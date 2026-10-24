"""Tests for the v0.2 design table, schematic generator and netlist comparison."""
import importlib.util
import re
import subprocess
import sys
import unittest
from pathlib import Path

KICAD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KICAD))

import design_v02 as design  # noqa: E402

SPEC = importlib.util.spec_from_file_location("match", KICAD / "check_netlist_matches_design.py")
MATCH = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MATCH)


def synthetic_netlist(nets=None, nc_pins=None):
    """Build a KiCad-style netlist text from net -> {(ref, pin)}."""
    nets = design.expected_nets() if nets is None else nets
    if nc_pins is None:
        nc_pins = [(p.ref, pin) for p in design.PARTS for pin, n in p.pins.items() if n == design.NC]
    comps = "\n".join(
        f'    (comp (ref "{p.ref}") (value "{p.value}") (footprint "{design.LIB}:{p.footprint}"))'
        for p in design.PARTS)
    out, code = [], 1
    for name, nodes in sorted(nets.items()):
        body = "\n".join(f'      (node (ref "{r}") (pin "{pin}") (pintype "passive"))' for r, pin in sorted(nodes))
        out.append(f'    (net (code "{code}") (name "/{name}")\n{body})')
        code += 1
    for ref, pin in nc_pins:
        out.append(f'    (net (code "{code}") (name "unconnected-({ref}-Pad{pin})")\n'
                   f'      (node (ref "{ref}") (pin "{pin}") (pintype "passive")))')
        code += 1
    return f"(export (version \"E\")\n  (components\n{comps})\n  (nets\n" + "\n".join(out) + "))\n"


class DesignTableTests(unittest.TestCase):
    def test_reference_designators_are_unique(self):
        refs = [p.ref for p in design.PARTS]
        self.assertEqual(len(refs), len(set(refs)))

    def test_required_rails_are_distinct_nets(self):
        nets = design.expected_nets()
        for rail in design.POWER_NETS:
            self.assertIn(rail, nets)

    def test_modem_supply_never_shares_mcu_rail(self):
        nets = design.expected_nets()
        self.assertFalse(nets["MODEM_VIN"] & nets["+3V3"])
        regulator = next(p for p in design.PARTS if p.ref == "U3")
        self.assertNotIn("MODEM_VIN", regulator.pins.values())

    def test_no_capacitor_shorted(self):
        for part in design.PARTS:
            if part.symbol == "C":
                self.assertNotEqual(part.pins["1"], part.pins["2"], part.ref)

    def test_pulse_input_reaches_gpio4_only_through_series_resistor(self):
        nets = design.expected_nets()
        self.assertIn(("U1", "4"), nets["PULSE_IN"])
        self.assertIn(("J2", "1"), nets["PULSE_EXT"])
        self.assertNotIn(("J2", "1"), nets["PULSE_IN"])
        self.assertEqual({("R6", "1"), ("R6", "2")} & (nets["PULSE_EXT"] | nets["PULSE_IN"]),
                         {("R6", "1"), ("R6", "2")})

    def test_usb_cc_pins_each_have_own_pull_down(self):
        nets = design.expected_nets()
        self.assertEqual(nets["USB_CC1"], {("J1", "A5"), ("R1", "1")})
        self.assertEqual(nets["USB_CC2"], {("J1", "B5"), ("R2", "1")})


class NetlistComparisonTests(unittest.TestCase):
    def test_design_netlist_matches(self):
        self.assertEqual(MATCH.compare(synthetic_netlist()), [])

    def test_detects_pin_on_wrong_net(self):
        nets = {k: set(v) for k, v in design.expected_nets().items()}
        nets["PULSE_IN"].discard(("U1", "4"))
        nets["LED_DRV"].add(("U1", "4"))
        errors = MATCH.compare(synthetic_netlist(nets))
        self.assertTrue(any("PULSE_IN: missing pins" in e for e in errors), errors)
        self.assertTrue(any("LED_DRV: unexpected pins" in e for e in errors), errors)

    def test_detects_merged_rails(self):
        nets = {k: set(v) for k, v in design.expected_nets().items()}
        nets["+5V"] |= nets.pop("GND")
        errors = MATCH.compare(synthetic_netlist(nets))
        self.assertTrue(any("missing net GND" in e for e in errors), errors)

    def test_detects_floating_pin_that_should_be_connected(self):
        nets = {k: set(v) for k, v in design.expected_nets().items()}
        nets["MCU_EN"].discard(("R3", "2"))
        nc = [(p.ref, pin) for p in design.PARTS for pin, n in p.pins.items() if n == design.NC]
        errors = MATCH.compare(synthetic_netlist(nets, nc + [("R3", "2")]))
        self.assertTrue(any("R3.2 is unconnected" in e for e in errors), errors)


class SchematicSyncTests(unittest.TestCase):
    def test_committed_schematic_is_generated_from_design(self):
        result = subprocess.run(
            [sys.executable, str(KICAD / "tools" / "generate_schematic.py"), "--check",
             "--kicad-share", str(KICAD / "no-stock-libraries")],
            capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_every_footprint_is_vendored(self):
        pretty = KICAD / "lib" / f"{design.LIB}.pretty"
        for part in design.PARTS:
            self.assertTrue((pretty / f"{part.footprint}.kicad_mod").exists(), part.footprint)

    def test_frozen_draft_is_archived_not_active(self):
        active = sorted(p.name for p in KICAD.glob("*.kicad_sch"))
        self.assertEqual(active, ["smart_gas_meter_iot.kicad_sch"])
        frozen = KICAD / "archive" / "v0.2-frozen-2026-10-23" / "smart_gas_meter_iot.kicad_sch"
        self.assertTrue(frozen.exists())
        self.assertIn("esp32-dev-boards", frozen.read_text(encoding="utf-8"))
        text = (KICAD / "smart_gas_meter_iot.kicad_sch").read_text(encoding="utf-8")
        self.assertFalse(re.search(r'lib_id "esp32-dev-boards', text))


if __name__ == "__main__":
    unittest.main()
