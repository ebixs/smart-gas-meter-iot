#!/usr/bin/env python3
"""Compare a KiCad-exported modem netlist with design_modem_v01.py.

Same rules as the carrier check (hardware/kicad/check_netlist_matches_design.py): no
missing, extra, merged or split nets, every pin on its intended net, values and
footprints as designed. Also checks that the header pin-out equals carrier J6.

Usage: python3 hardware/kicad-modem/check_netlist_matches_design.py NETLIST.net
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "kicad"))
import check_netlist_matches_design as carrier_check  # noqa: E402
import design_modem_v01 as design  # noqa: E402
import design_v02 as carrier  # noqa: E402

carrier_check.design = design


def header_errors() -> list[str]:
    j6 = next(p for p in carrier.PARTS if p.ref == "J6").pins
    j1 = next(p for p in design.PARTS if p.ref == "J1").pins
    return [f"J1.{pin} is {j1.get(pin)} but carrier J6.{pin} is {net}" for pin, net in j6.items() if j1.get(pin) != net]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    errors = header_errors() + carrier_check.compare(path.read_text(encoding="utf-8"))
    if errors:
        print(f"Netlist does NOT match design_modem_v01.py ({len(errors)} finding(s)):")
        for item in errors:
            print(f"- {item}")
        return 1
    nets = design.expected_nets()
    print(f"Netlist matches design_modem_v01.py: {len(design.PARTS)} parts, {len(nets)} nets, "
          f"{sum(len(n) for n in nets.values())} pin connections; J1 pin-out = carrier J6 ({path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
