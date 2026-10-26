"""Design invariants for the modem daughterboard v0.1 (no KiCad needed)."""
import re
import sys
import unittest
from pathlib import Path

MODEM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODEM))
sys.path.insert(0, str(MODEM.parent / "kicad"))

import design_modem_v01 as design  # noqa: E402
import design_v02 as carrier  # noqa: E402
import pcb_layout_modem_v01 as layout  # noqa: E402

BY_REF = {p.ref: p for p in design.PARTS}
PCB = MODEM / "sgm_modem.kicad_pcb"


class InterfaceTests(unittest.TestCase):
    def test_socket_pinout_equals_carrier_j6(self):
        j6 = next(p for p in carrier.PARTS if p.ref == "J6").pins
        self.assertEqual(BY_REF["J1"].pins, j6)

    def test_module_never_touches_a_3v3_rail(self):
        nets = design.expected_nets()
        self.assertNotIn("+3V3", nets)
        self.assertNotIn("+5V", nets)

    def test_vbat_pins_on_modem_vin(self):
        for pin in ("57", "58", "59", "60"):
            self.assertEqual(BY_REF["U1"].pins[pin], "MODEM_VIN", pin)

    def test_every_module_ground_pin_grounded(self):
        for pin in design.EC200U_GND + ["10"]:
            self.assertEqual(BY_REF["U1"].pins[pin], "GND", pin)

    def test_pwrkey_and_reset_are_open_collector(self):
        # Only a transistor collector may drive PWRKEY_N / RESET_N (module pulls them up to VBAT).
        nets = design.expected_nets()
        self.assertEqual(nets["PWRKEY_N"], {("U1", "21"), ("Q1", "3")})
        self.assertEqual(nets["RESET_N"], {("U1", "20"), ("Q2", "3")})

    def test_every_1v8_module_output_is_shifted_before_the_header(self):
        nets = design.expected_nets()
        for net in ("M_TXD", "M_RXD", "M_STATUS"):
            refs = {ref for ref, _ in nets[net]}
            self.assertFalse(refs & {"J1"}, net)
            self.assertTrue(refs & {"Q3", "Q4", "Q5"}, net)

    def test_shifter_gates_on_vdd_ext(self):
        for q in ("Q3", "Q4", "Q5"):
            self.assertEqual(BY_REF[q].pins["1"], "VDD_EXT", q)

    def test_usb_boot_jumper_is_open_by_default(self):
        self.assertIn("open", BY_REF["JP1"].value.lower())

    def test_direct_vbat_input_not_fitted(self):
        self.assertTrue(BY_REF["J2"].dnp)


class LayoutTests(unittest.TestCase):
    def test_every_part_placed(self):
        self.assertEqual(set(layout.PLACEMENT), set(BY_REF))

    def test_inside_the_board(self):
        for ref, (x, y, _r, side) in layout.PLACEMENT.items():
            self.assertTrue(0 <= x <= layout.BOARD_W and 0 <= y <= layout.BOARD_H, ref)
            self.assertIn(side, ("F", "B"))

    def test_socket_on_bottom(self):
        self.assertEqual(layout.PLACEMENT["J1"][3], "B")

    def test_antenna_connector_on_an_edge(self):
        x, y, _r, _s = layout.PLACEMENT["J4"]
        self.assertLess(min(x, y, layout.BOARD_W - x, layout.BOARD_H - y), 10.0)


@unittest.skipUnless(PCB.exists(), "board not built")
class BoardFileTests(unittest.TestCase):
    def test_footprint_marked_provisional(self):
        text = PCB.read_text(encoding="utf-8")
        self.assertIn("Quectel_EC200U_PROVISIONAL", text)
        self.assertIn("FOOTPRINT PROVISIONAL", text)

    def test_four_copper_layers(self):
        text = PCB.read_text(encoding="utf-8")
        for layer in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu"):
            self.assertRegex(text, rf'\(\d+ "{re.escape(layer)}" (signal|power)')


if __name__ == "__main__":
    unittest.main()
