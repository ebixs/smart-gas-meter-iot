#!/usr/bin/env python3
"""Fail closed when a graphical KiCad concept sheet is mistaken for electrical CAD."""
from pathlib import Path
import re
import sys

ROOT = Path("hardware/kicad")


def extract_balanced_form(source: str, start: int) -> str:
    """Return one balanced S-expression, respecting quoted strings."""
    depth = 0
    quoted = False
    escaped = False
    for index in range(start, len(source)):
        char = source[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
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


def main() -> int:
    schematics = sorted(ROOT.glob("*.kicad_sch"))
    if not schematics:
        print("ERROR: no KiCad schematic files found.")
        return 1

    failed = False
    for path in schematics:
        text = path.read_text(encoding="utf-8")
        match = re.search(r"\(lib_symbols(?:\s|$)", text)
        if not match:
            print(f"BLOCKED: {path} has no embedded lib_symbols section.")
            failed = True
            continue
        try:
            library = extract_balanced_form(text, match.start())
        except ValueError:
            print(f"ERROR: unbalanced library section in {path}")
            failed = True
            continue

        definitions = len(re.findall(r'\(symbol\s+"[^"]+"', library))
        placed_ids = re.findall(r'\(lib_id\s+"([^"]+)"', text)
        # Only count IDs occurring after the end of the embedded library section.
        tail = text[match.start() + len(library):]
        placed_ids = re.findall(r'\(lib_id\s+"([^"]+)"', tail)
        if definitions == 0 or not placed_ids:
            print(f"BLOCKED: {path} is not yet a pin-level electrical schematic.")
            print(f"  embedded library symbol definitions: {definitions}")
            print(f"  placed symbol instances: {len(placed_ids)}")
            failed = True
            continue

        missing = sorted(set(placed_ids) - set(re.findall(r'\(symbol\s+"([^"]+)"', library)))
        if missing:
            print(f"BLOCKED: {path} references missing embedded symbols: {', '.join(missing)}")
            failed = True
        else:
            print(f"STRUCTURE OK: {path} ({definitions} definitions; {len(placed_ids)} placed instances).")

    if failed:
        print("Structural gate failed. Graphical blocks are not electrical CAD.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
