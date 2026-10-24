"""Static checks on the PCB placement table and the committed board file."""
import re
import sys
import unittest
from pathlib import Path

KICAD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KICAD))

import design_v02 as design  # noqa: E402
import pcb_layout_v02 as layout  # noqa: E402

PCB = KICAD / "smart_gas_meter_iot.kicad_pcb"


class PlacementTableTests(unittest.TestCase):
    def test_every_schematic_part_is_placed_exactly_once(self):
        self.assertEqual(set(layout.PLACEMENT), {p.ref for p in design.PARTS})

    def test_placements_are_inside_the_board(self):
        for ref, (x, y, _rot) in layout.PLACEMENT.items():
            self.assertTrue(0 <= x <= layout.BOARD_W and 0 <= y <= layout.BOARD_H, ref)

    def test_esp32_antenna_sits_at_the_top_edge(self):
        # Module body is 25.5 mm long; its antenna end must be within 1 mm of the board edge.
        _x, y, rot = layout.PLACEMENT["U1"]
        self.assertEqual(rot, 0)
        self.assertLessEqual(y - 25.5 / 2, 1.0)

    def test_usb_connector_on_left_edge(self):
        x, _y, _rot = layout.PLACEMENT["J1"]
        self.assertLess(x, 5.0)

    def test_pulse_input_far_from_switch_node(self):
        jx, jy, _ = layout.PLACEMENT["J2"]
        lx, ly, _ = layout.PLACEMENT["L1"]
        self.assertGreater(((jx - lx) ** 2 + (jy - ly) ** 2) ** 0.5, 40.0)


@unittest.skipUnless(PCB.exists(), "board not generated yet")
class BoardFileTests(unittest.TestCase):
    def setUp(self):
        self.text = PCB.read_text(encoding="utf-8")

    def test_four_copper_layers(self):
        for layer in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu"):
            self.assertIn(f'"{layer}"', self.text)

    def test_every_part_on_board(self):
        refs = set(re.findall(r'\(property "Reference" "([^"]+)"', self.text))
        self.assertTrue({p.ref for p in design.PARTS} <= refs)

    def test_no_tracks_on_solid_ground_plane(self):
        tracks_in1 = re.findall(r'\(segment\s+\(start[^)]*\)\s+\(end[^)]*\)\s+\(width [\d.]+\)\s+\(layer "In1\.Cu"\)',
                                self.text)
        self.assertEqual(tracks_in1, [])

    def test_project_carries_board_rules(self):
        import json
        project = json.loads((KICAD / "smart_gas_meter_iot.kicad_pro").read_text(encoding="utf-8"))
        self.assertEqual(project["board"]["design_settings"]["rules"], layout.BOARD_RULES)

    def test_antenna_keepout_covers_all_copper(self):
        footprint = (KICAD / "lib" / f"{design.LIB}.pretty" / "ESP32-S3-WROOM-1.kicad_mod").read_text()
        self.assertIn('(layers "*.Cu")', footprint)


if __name__ == "__main__":
    unittest.main()
