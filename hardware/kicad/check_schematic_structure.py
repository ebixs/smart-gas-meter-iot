#!/usr/bin/env python3
"""Fail closed when a graphical KiCad concept sheet is mistaken for electrical CAD.

This is deliberately a structural gate, not a replacement for kicad-cli ERC/DRC.
A schematic must contain embedded library definitions and placed symbol instances
before the KiCad CLI checks are treated as meaningful.
"""
from pathlib import Path
import re
import sys

ROOT = Path("hardware/kicad")
schematics = sorted(ROOT.glob("*.kicad_sch"))
if not schematics:
    print("No KiCad schematic files found.")
    sys.exit(1)

failed = False
for path in schematics:
    text = path.read_text(encoding="utf-8")
    lib_match = re.search(r"\(lib_symbols\s*(.*?)\n\s*\)", text, re.S)
    # Count actual placed symbol forms, not the library definition section.
    placed = len(re.findall(r"\n\s{2,}\(symbol\s*\n\s*\(lib_id\s+", text))
    has_libs = bool(lib_match and re.search(r"\(symbol\s+\(", lib_match.group(1)))
    if not has_libs or placed == 0:
        print(f"BLOCKED: {path} is a graphical/concept sheet, not pin-level electrical CAD.")
        print("Required: embedded symbol definitions and placed symbol instances with real pins.")
        failed = True
    else:
        print(f"STRUCTURE OK: {path} ({placed} placed symbol instances).")
if failed:
    sys.exit(2)
