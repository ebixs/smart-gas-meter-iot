#!/usr/bin/env python3
"""Fail closed when a graphical KiCad concept sheet is mistaken for electrical CAD.

This is a structural preflight, not a replacement for kicad-cli ERC/DRC.
It detects embedded library symbol definitions and placed symbol instances.
"""
from pathlib import Path
import re
import sys

ROOT = Path("hardware/kicad")


def extract_balanced_form(source: str, start: int) -> str:
    """Return one balanced S-expression starting at an opening parenthesis."""
    depth = 0
    quoted = False
    escaped = False
    for index in range(start, len(source)):
        char = source[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise ValueError("Unbalanced S-expression")


schematics = sorted(ROOT.glob("*.kicad_sch"))
if not schematics:
    print("ERROR: no KiCad schematic files found.")
    sys.exit(1)

failed = False
for path in schematics:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"\(lib_symbols(?:\s|$)", text)
    lib_block = ""
    if match:
        try:
            lib_block = extract_balanced_form(text, match.start())
        except ValueError:
            print(f"ERROR: unbalanced library block in {path}")
            failed = True
            continue

    definitions = len(re.findall(r'\(symbol\s+"[^"]+"', lib_block))
    placed_block_count = len(re.findall(r'\\(lib_id\\s+"[^"]+"', text))
    if definitions == 0 or placed_block_count == 0:
        print(f"BLOCKED: {path} is not yet a pin-level electrical schematic.")
        print(f"  embedded library symbol definitions: {definitions}")
        print(f"  placed symbol instances: {placed_block_count}")
        failed = True
    else:
        print(f"STRUCTURE OK: {path} ({definitions} definitions; {placed_block_count} instances).")

if failed:
    print("Structural gate failed. Do not treat graphical blocks as electrical CAD.")
    sys.exit(2)
