#!/usr/bin/env python3
"""Fail on known blocking electrical mistakes in a KiCad S-expression netlist.

This is a guardrail, not a replacement for KiCad ERC, DRC, or engineering review.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

NET_START_RE = re.compile(r'\(net\s+\(code\s+"?[^")\s]+"?\)\s+\(name\s+"([^"]*)"\)')
NODE_START_RE = re.compile(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)')


def balanced(text: str, start: int) -> str:
    """Return the S-expression starting at ``start``, respecting quoted strings.

    Works for KiCad's multi-line export and for one-line fixtures alike.
    """
    depth, quoted, escaped = 0, False, False
    for index in range(start, len(text)):
        char = text[index]
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
                return text[start:index + 1]
    return text[start:]


def parse_nets(text: str) -> dict[str, list[tuple[str, str, str]]]:
    nets: dict[str, list[tuple[str, str, str]]] = {}
    for match in NET_START_RE.finditer(text):
        form = balanced(text, match.start())
        nodes = []
        for node in NODE_START_RE.finditer(form):
            body = balanced(form, node.start())
            fn = re.search(r'\(pinfunction\s+"([^"]*)"\)', body)
            nodes.append((node.group(1), node.group(2), fn.group(1) if fn else ""))
        # KiCad prefixes local labels with the sheet path ("/USB_VBUS");
        # normalise so the rail checks below also cover label-named nets.
        nets.setdefault(match.group(1).lstrip("/"), []).extend(nodes)
    return nets


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("hardware/kicad/netlist.net")
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    nets = parse_nets(text)

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
    # Identify legacy headers by their source library/part, not by reference
    # designator: the v0.2 carrier legitimately uses J1 (USB-C) and J2 (pulse).
    comps = {}
    for comp in re.finditer(r'\(comp\s+\(ref\s+"([^"]+)"\)(.*?)(?=\(comp\s+\(ref|\Z)', text, re.S):
        lib = re.search(r'\(libsource\s+\(lib\s+"([^"]*)"\)\s+\(part\s+"([^"]*)"', comp.group(2))
        comps[comp.group(1)] = (lib.group(1), lib.group(2)) if lib else ("", "")
    legacy = sorted(ref for ref, (lib, part) in comps.items()
                    if lib == "esp32-dev-boards" or "DEVKIT" in part.upper())
    modules = sorted(ref for ref, (_, part) in comps.items() if part.upper().startswith("ESP32-S3-WROOM"))
    if legacy and modules:
        errors.append(f"Legacy dev-board headers {', '.join(legacy)} coexist with module "
                      f"{', '.join(modules)}; review architecture")

    # The modem must never be powered from the MCU 3V3 rail.
    for ref, pin, function in nets.get("+3V3", []):
        if "MODEM" in function.upper():
            errors.append(f"+3V3: modem supply pin {ref}.{pin} ({function}) is tied to the MCU rail")
    if "MODEM_VIN" in nets and "+3V3" in nets:
        shared = {(r, p) for r, p, _ in nets["MODEM_VIN"]} & {(r, p) for r, p, _ in nets["+3V3"]}
        if shared:
            errors.append(f"MODEM_VIN and +3V3 share pins {sorted(shared)}")

    if errors:
        print(f"Netlist guardrail FAILED ({len(errors)} finding(s)):")
        for item in errors:
            print(f"- {item}")
        return 1
    print(f"Netlist guardrail passed: {len(nets)} nets inspected in {path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
