"""Cross-checks between the C firmware core and the rest of the repository.

- firmware/main/board.h must match the ESP32-S3 pin assignment in the KiCad design source;
- the C Jalali calendar and billing-period boundaries must agree with the Python
  analytics package that issues the invoices;
- records produced by the firmware core must pass the v2 telemetry contract.

The C parts are built with CMake on the host (gcc/clang with sanitizers). They are
skipped when no compiler toolchain is available.
"""
from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analytics"))

from sgm_analytics.jalali import to_gregorian, to_jalali  # noqa: E402
from simulator.validate_telemetry import validate_record, validate_stream  # noqa: E402

# ESP32-S3-WROOM-1 module pin -> GPIO (Espressif datasheet, pin definitions table).
WROOM1_PIN_TO_GPIO = {
    4: 4, 5: 5, 6: 6, 7: 7, 8: 15, 9: 16, 10: 17, 11: 18, 12: 8, 13: 19, 14: 20, 15: 3,
    16: 46, 17: 9, 18: 10, 19: 11, 20: 12, 21: 13, 22: 14, 23: 21, 24: 47, 25: 48, 26: 45,
    27: 0, 28: 35, 29: 36, 30: 37, 31: 38, 32: 39, 33: 40, 34: 41, 35: 42, 38: 2, 39: 1,
}
BOARD_MACRO_TO_NET = {
    "SGM_GPIO_PULSE_IN": "PULSE_IN", "SGM_GPIO_LED": "LED_DRV", "SGM_GPIO_I2C_SDA": "I2C_SDA",
    "SGM_GPIO_I2C_SCL": "I2C_SCL", "SGM_GPIO_TAMPER_IN": "TAMPER_IN", "SGM_GPIO_MODEM_TXD": "MODEM_TXD",
    "SGM_GPIO_MODEM_RXD": "MODEM_RXD", "SGM_GPIO_MODEM_EN": "MODEM_EN", "SGM_GPIO_MODEM_RESET": "MODEM_RESET",
    "SGM_GPIO_MODEM_STATUS": "MODEM_STATUS",
}
IRAN = timezone(timedelta(hours=3, minutes=30))


def u1_pin_nets() -> dict[str, int]:
    """Net -> module pin for U1, read from design_v02.py without importing KiCad tooling."""
    source = (ROOT / "hardware/kicad/design_v02.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and getattr(node.func, "id", "") == "Part" and node.args
                and isinstance(node.args[0], ast.Constant) and node.args[0].value == "U1"):
            pins = node.args[5]
            out = {}
            for k, v in zip(pins.keys, pins.values):
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    out[v.value] = int(k.value)
            return out
    raise AssertionError("U1 not found in design_v02.py")


class BoardPinMapTests(unittest.TestCase):
    def test_board_header_matches_schematic(self):
        header = (ROOT / "firmware/main/board.h").read_text(encoding="utf-8")
        defined = {m: int(g) for m, g in re.findall(r"#define\s+(SGM_GPIO_\w+)\s+GPIO_NUM_(\d+)", header)}
        nets = u1_pin_nets()
        self.assertEqual(set(defined), set(BOARD_MACRO_TO_NET))
        for macro, net in BOARD_MACRO_TO_NET.items():
            with self.subTest(macro=macro):
                self.assertIn(net, nets, f"{net} is not on U1 in the schematic")
                self.assertEqual(defined[macro], WROOM1_PIN_TO_GPIO[nets[net]])


@unittest.skipUnless(shutil.which("cmake") and (shutil.which("cc") or shutil.which("gcc")), "no host C toolchain")
class FirmwareCoreHostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = Path(tempfile.mkdtemp(prefix="sgm-host-"))
        subprocess.run(["cmake", "-S", str(ROOT / "firmware/test/host"), "-B", str(cls.build),
                        "-DCMAKE_BUILD_TYPE=Debug"], check=True, capture_output=True)
        subprocess.run(["cmake", "--build", str(cls.build), "-j"], check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.build, ignore_errors=True)

    def tool(self, *args: str) -> str:
        return subprocess.run([str(self.build / "sgm_host"), *args], check=True, capture_output=True,
                              text=True).stdout

    def test_c_unit_tests_pass(self):
        result = subprocess.run([str(self.build / "test_core")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_jalali_matches_python_for_every_day_1990_2060(self):
        start = (date(1990, 1, 1) - date(1970, 1, 1)).days
        end = (date(2060, 1, 1) - date(1970, 1, 1)).days
        mismatches = []
        for line in self.tool("jalali", str(start), str(end)).splitlines():
            days, jy, jm, jd = map(int, line.split())
            j = to_jalali(date(1970, 1, 1) + timedelta(days=days))
            if (j.year, j.month, j.day) != (jy, jm, jd):
                mismatches.append((days, (jy, jm, jd), j))
        self.assertEqual(mismatches[:5], [])

    def test_period_boundaries_match_python_billing_calendar(self):
        start = int(datetime(2023, 3, 1, tzinfo=timezone.utc).timestamp())
        for months in (1, 3):
            got = [int(x) for x in self.tool("boundaries", str(start), "40", str(months)).split()]
            first = to_jalali(datetime.fromtimestamp(start, IRAN).date())
            jy, jm = first.year, ((first.month - 1) // months) * months + 1
            want = []
            for _ in range(40):
                jm += months
                if jm > 12:
                    jy, jm = jy + 1, jm - 12
                local_midnight = datetime.combine(to_gregorian(jy, jm, 1), datetime.min.time(), IRAN)
                want.append(int(local_midnight.timestamp()))
            with self.subTest(months=months):
                self.assertEqual(got, want)

    def test_demo_records_pass_contract_v2(self):
        lines = self.tool("demo").splitlines()
        self.assertGreater(len(lines), 5)
        import io
        import json

        self.assertEqual(validate_stream(io.StringIO("\n".join(lines))), [])
        records = [json.loads(line) for line in lines]
        closes = [r for r in records if r["record_type"] == "period_close"]
        self.assertEqual(len(closes), 1)
        self.assertEqual(closes[0]["period"], {"calendar": "jalali", "start": "1405/04", "months": 3})
        self.assertEqual(closes[0]["timestamp"], "2026-09-22T20:30:00.000Z")  # 00:00 Mehr 1, Tehran
        self.assertTrue(all(validate_record(r) == [] for r in records))
        totals = [r["pulse_count_total"] for r in records]
        self.assertEqual(totals, sorted(totals))


if __name__ == "__main__":
    unittest.main()
