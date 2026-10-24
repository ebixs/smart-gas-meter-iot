#!/usr/bin/env python3
"""Compare a KiCad-exported netlist with the intended design in design_v02.py.

Fails if any net is missing, extra, merged or split, if any pin sits on the
wrong net, or if part values/footprints differ from the design table. This
catches accidental connections (overlapping labels/wires) that ERC may not.

Usage: python3 hardware/kicad/check_netlist_matches_design.py NETLIST.net
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_v02 as design  # noqa: E402

NET_START = re.compile(r'\(net\s+\(code\s+"?[^")\s]+"?\)\s+\(name\s+"([^"]*)"\)')
NODE_RE = re.compile(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)')
COMP_RE = re.compile(r'\(comp\s+\(ref\s+"([^"]+)"\)\s+\(value\s+"([^"]*)"\)\s+\(footprint\s+"([^"]*)"\)')


def parse(text: str) -> tuple[dict[str, set[tuple[str, str]]], dict[str, tuple[str, str]]]:
    nets: dict[str, set[tuple[str, str]]] = {}
    starts = list(NET_START.finditer(text))
    for i, match in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        name = match.group(1).lstrip("/")
        nodes = {(r, p) for r, p in NODE_RE.findall(text[match.end():end]) if not r.startswith("#")}
        if nodes:
            nets[name] = nodes
    comps = {ref: (value, fp) for ref, value, fp in COMP_RE.findall(text)}
    return nets, comps


def compare(text: str) -> list[str]:
    actual, comps = parse(text)
    expected = design.expected_nets()
    errors: list[str] = []
    # KiCad exports each no-connect pin as a single-pin "unconnected-(...)" net.
    # Those must be exactly the pins the design marks NC; nothing else may float.
    design_nc = {(p.ref, pin) for p in design.PARTS for pin, net in p.pins.items() if net == design.NC}
    floating: set[tuple[str, str]] = set()
    for name in sorted(set(actual) - set(expected)):
        if name.startswith("unconnected-") and len(actual[name]) == 1:
            floating |= actual[name]
        else:
            errors.append(f"unexpected net {name}: {sorted(actual[name])}")
    for ref, pin in sorted(floating - design_nc):
        errors.append(f"{ref}.{pin} is unconnected but the design assigns it a net")
    for ref, pin in sorted(design_nc - floating):
        errors.append(f"{ref}.{pin} is marked NC in the design but is connected")
    for name in sorted(expected):
        if name not in actual:
            errors.append(f"missing net {name}: expected {sorted(expected[name])}")
            continue
        missing = expected[name] - actual[name]
        extra = actual[name] - expected[name]
        if missing:
            errors.append(f"{name}: missing pins {sorted(missing)}")
        if extra:
            errors.append(f"{name}: unexpected pins {sorted(extra)}")
    for part in design.PARTS:
        if part.ref not in comps:
            errors.append(f"component {part.ref} missing from netlist")
            continue
        value, footprint = comps[part.ref]
        if value != part.value.replace('"', "'"):
            errors.append(f"{part.ref}: value {value!r} != design {part.value!r}")
        if footprint != f"{design.LIB}:{part.footprint}":
            errors.append(f"{part.ref}: footprint {footprint!r} != design {design.LIB}:{part.footprint}")
    extra_refs = set(comps) - {p.ref for p in design.PARTS}
    if extra_refs:
        errors.append(f"components not in design: {sorted(extra_refs)}")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    errors = compare(path.read_text(encoding="utf-8"))
    if errors:
        print(f"Netlist does NOT match design_v02.py ({len(errors)} finding(s)):")
        for item in errors:
            print(f"- {item}")
        return 1
    nets = design.expected_nets()
    print(f"Netlist matches design_v02.py: {len(design.PARTS)} parts, {len(nets)} nets, "
          f"{sum(len(n) for n in nets.values())} pin connections ({path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
