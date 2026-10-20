import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hardware.kicad import check_schematic_structure as gate


class KiCadStructureGateTests(unittest.TestCase):
    def run_gate(self, source):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            (root / "test.kicad_sch").write_text(source, encoding="utf-8")
            output = io.StringIO()
            with patch.object(gate, "ROOT", root), contextlib.redirect_stdout(output):
                result = gate.main()
            return result, output.getvalue()

    def test_graphical_only_sheet_is_blocked(self):
        result, output = self.run_gate(
            '(kicad_sch (version 20250114) (lib_symbols) (text "block diagram"))'
        )
        self.assertEqual(result, 2)
        self.assertIn("not yet a pin-level electrical schematic", output)

    def test_library_symbol_without_placed_instance_is_blocked(self):
        source = (
            '(kicad_sch (version 20250114) '
            '(lib_symbols (symbol "Device:R" (pin_names (offset 0)))) )'
        )
        result, output = self.run_gate(source)
        self.assertEqual(result, 2)
        self.assertIn("placed symbol instances: 0", output)

    def test_matching_embedded_symbol_and_instance_passes_structure_gate(self):
        source = (
            '(kicad_sch (version 20250114) '
            '(lib_symbols (symbol "Device:R" (pin_names (offset 0)))) '
            '(symbol (lib_id "Device:R") (at 10 10 0) (unit 1) '
            '(uuid "00000000-0000-4000-8000-000000000001")))'
        )
        result, output = self.run_gate(source)
        self.assertEqual(result, 0, output)
        self.assertIn("STRUCTURE OK", output)

    def test_missing_symbol_definition_is_blocked(self):
        source = (
            '(kicad_sch (version 20250114) '
            '(lib_symbols (symbol "Device:R" (pin_names (offset 0)))) '
            '(symbol (lib_id "Device:C") (at 10 10 0) (unit 1)))'
        )
        result, output = self.run_gate(source)
        self.assertEqual(result, 2)
        self.assertIn("references missing embedded symbols", output)


if __name__ == "__main__":
    unittest.main()
