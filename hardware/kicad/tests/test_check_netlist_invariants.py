import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "check_netlist_invariants.py"
SPEC = importlib.util.spec_from_file_location("check_netlist_invariants", SCRIPT)
CHECKER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(CHECKER)


class NetlistInvariantTests(unittest.TestCase):
    def run_checker(self, text):
        with tempfile.TemporaryDirectory() as directory:
            netlist = Path(directory) / "fixture.net"
            netlist.write_text(text, encoding="utf-8")
            with patch("sys.argv", ["check_netlist_invariants.py", str(netlist)]):
                return CHECKER.main()

    def test_rejects_ground_on_positive_rail(self):
        fixture = '''(export (components (comp (ref "U1")))
          (nets (net (code "1") (name "+5V")
            (node (ref "U1") (pin "1") (pinfunction "GND")))))'''
        self.assertEqual(self.run_checker(fixture), 1)

    def test_rejects_capacitor_with_both_ends_on_same_net(self):
        fixture = '''(export (components (comp (ref "C1")))
          (nets (net (code "1") (name "GND")
            (node (ref "C1") (pin "1") (pinfunction "A"))
            (node (ref "C1") (pin "2") (pinfunction "B")))))'''
        self.assertEqual(self.run_checker(fixture), 1)

    def test_rejects_legacy_devboard_headers_with_module(self):
        fixture = '''(export
          (components
            (comp (ref "U1") (value "ESP32-S3-WROOM-1")
              (libsource (lib "Espressif") (part "ESP32-S3-WROOM-1") (description "")))
            (comp (ref "J1") (value "J1")
              (libsource (lib "esp32-dev-boards") (part "ESP32-S3-DEVKITC-1-J1-mini") (description "")))
            (comp (ref "J2") (value "J2")
              (libsource (lib "esp32-dev-boards") (part "ESP32-S3-DEVKITC-1-J2-mini") (description "")))
          )
          (nets (net (code "1") (name "PULSE_IN")
            (node (ref "U1") (pin "1") (pinfunction "GPIO4")))))'''
        self.assertEqual(self.run_checker(fixture), 1)

    def test_accepts_module_with_ordinary_connectors_j1_j2(self):
        fixture = '''(export
          (components
            (comp (ref "U1") (value "ESP32-S3-WROOM-1-N8")
              (libsource (lib "SGM") (part "ESP32-S3-WROOM-1") (description "")))
            (comp (ref "J1") (value "USB-C")
              (libsource (lib "SGM") (part "USB_C_Receptacle_USB2.0_16P") (description "")))
            (comp (ref "J2") (value "PULSE_IN")
              (libsource (lib "SGM") (part "Conn_01x02") (description "")))
          )
          (nets (net (code "1") (name "PULSE_IN")
            (node (ref "U1") (pin "4") (pinfunction "IO4"))
            (node (ref "J2") (pin "1") (pinfunction "Pin_1")))))'''
        self.assertEqual(self.run_checker(fixture), 0)

    def test_rejects_modem_supply_on_3v3(self):
        fixture = '''(export (components (comp (ref "J6")))
          (nets (net (code "1") (name "+3V3")
            (node (ref "J6") (pin "1") (pinfunction "MODEM_VIN")))))'''
        self.assertEqual(self.run_checker(fixture), 1)


if __name__ == "__main__":
    unittest.main()
