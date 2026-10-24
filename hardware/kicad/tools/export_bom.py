#!/usr/bin/env python3
"""Export the BOM from design_v02.py as Markdown (review) and CSV (JLCPCB assembly format).

Usage: python3 hardware/kicad/tools/export_bom.py
Writes hardware/kicad/exports/BOM-v<rev>.md and BOM-v<rev>-jlcpcb.csv.
"""
from __future__ import annotations

import csv
import sys
from collections import OrderedDict
from pathlib import Path

KICAD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KICAD_DIR))
import design_v02 as design  # noqa: E402


def grouped():
    groups: OrderedDict[tuple, list[str]] = OrderedDict()
    for part in design.PARTS:
        if part.symbol == "TestPoint":
            continue  # bare copper pads, nothing to buy or place
        key = (part.value, part.footprint, part.mpn, part.fields.get("Manufacturer", ""),
               part.fields.get("LCSC", ""), part.dnp)
        groups.setdefault(key, []).append(part.ref)
    return groups


def main() -> int:
    out = KICAD_DIR / "exports"
    out.mkdir(exist_ok=True)
    rev = design.REVISION
    for stale in out.glob("BOM-v*"):
        stale.unlink()
    rows = ["| Qty | Refs | Value | Manufacturer | MPN | LCSC | Footprint (SGM) | Fit |",
            "|---:|---|---|---|---|---|---|---|"]
    with (out / f"BOM-v{rev}-jlcpcb.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (value, fp, mpn, maker, lcsc, dnp), refs in grouped().items():
            fit = "DNP" if dnp else ("hand-fit" if mpn == "generic" else "SMT")
            rows.append(f"| {len(refs)} | {', '.join(refs)} | {value} | {maker or '-'} | {mpn} | "
                        f"{lcsc or '-'} | `{fp}` | {fit} |")
            if lcsc and not dnp:
                writer.writerow([value, ",".join(refs), fp, lcsc])
    (out / f"BOM-v{rev}.md").write_text(
        f"# BOM — carrier board v{rev} (generated from `design_v02.py`)\n\n"
        "Exact parts selected for schematic freeze; see [PART_SELECTION.md](../PART_SELECTION.md) for ratings and reasoning. "
        "Prices and stock change daily — re-check before ordering. **Not approved for purchase until the PCB and freeze review are signed off.**\n\n"
        "`hand-fit` = generic 2.54 mm headers fitted by hand. Test points TP1–TP9 are bare copper pads and are not listed.\n\n"
        + "\n".join(rows) + "\n", encoding="utf-8")
    print(f"Wrote BOM-v{rev}.md and BOM-v{rev}-jlcpcb.csv ({len(design.PARTS)} parts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
