#!/usr/bin/env python3
"""Fail on known blocking electrical mistakes in a KiCad S-expression netlist.

This is a guardrail, not a replacement for KiCad ERC, DRC, or engineering review.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

NET_RE = re.compile(r'\(net\s+\(code\s+"[^"]+"\)\s+\(name\s+"([^"]+)"\).*?(?=\n\s*\(net\s+\(code|\n\s*\)\s*\)\s*\Z)', re.S)
NODE_RE = re.compile(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)(.*?)\)', re.S)

def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("hardware/kicad/netlist.net")
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    nets: dict[str, list[tuple[str, str, str]]] = {}
    for match in NET_RE.finditer(text):
        name = match.group(1)
        nodes = []
        for node in NODE_RE.finditer(match.group(0)):
            ref, pin, rest = node.groups()
            fn = re.search(r'\(pinfunction\s+"([^"]+)"\)', rest)
            nodes.append((ref, pin, fn.group(1) if fn else ""))
        nets[name] = nodes

    if not nets:
        print(f"ERROR: no nets parsed from {path}")
        return 2

    # A ground-labelled pin must never be present on a positive supply net.
    for supply in ("+5V", "USB_VBUS", "+3V3"):
        for ref, pin, function in nets.get(supply, []):
            if function.upper() in {"GND", "GROUND"}:
                errors.append(f"{supply}: {ref}.{pin} is labelled {function}")

    # Passive capacitors must not have both terminals on the same net.
    capacitor_nets: dict[str, set[str]] = defaultdict(set)
    for net_name, nodes in nets.items():
        for ref, pin, _ in nodes:
            if re.fullmatch(r"C\d+", ref):
                capacitor_nets[ref].add(net_name)
    for ref, names in capacitor_nets.items():
        if len(names) == 1:
            errors.append(f"{ref}: both terminals appear on one net ({next(iter(names))})")

    # Production-intent carrier uses a module, not parallel legacy dev-board headers.
    refs = set(re.findall(r'\(comp\s+\(ref\s+"([^"]+)"\)', text))
    if "U1" in refs and ({"J1", "J2"} <= refs):
        errors.append("Legacy dev-board headers J1/J2 coexist with module U1; review architecture")

    if errors:
        print(f"Netlist guardrail FAILED ({len(errors)} finding(s)):")
        for item in errors:
            print(f"- {item}")
        return 1
    print(f"Netlist guardrail passed: {len(nets)} nets inspected in {path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
