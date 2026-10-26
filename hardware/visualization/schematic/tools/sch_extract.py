#!/usr/bin/env python3
"""Extract a generated KiCad schematic into JSON for the interactive schematic explorer.

Inputs: the .kicad_sch file and the netlist KiCad exports from it (kicad-cli sch export netlist).
Output: every net with its geometry in sheet millimetres (the same units as KiCad's SVG export):
pin tips, the wire stubs touching them and the labels / power symbols at their far ends; and every
part with its bounding box, value, footprint, MPN and design note.

Usage: python3 sch_extract.py SHEET.kicad_sch NETLIST.net OUT.json
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "boards" / "tools"))
from pcb_extract import kid, kids, num, parse  # noqa: E402

NET_START = re.compile(r'\(net\s+\(code\s+"?[^")\s]+"?\)\s+\(name\s+"([^"]*)"\)')
NODE_RE = re.compile(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)(?:\s+\(pinfunction\s+"([^"]*)"\))?')


def netlist(text: str) -> dict[str, list[tuple[str, str, str]]]:
    nets: dict[str, list[tuple[str, str, str]]] = {}
    starts = list(NET_START.finditer(text))
    for i, m in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        nets[m.group(1).lstrip("/")] = [(r, p, f or "") for r, p, f in NODE_RE.findall(text[m.end():end])]
    return nets


def rot(px: float, py: float, a: float) -> tuple[float, float]:
    r = math.radians(a)
    return px * math.cos(r) - py * math.sin(r), px * math.sin(r) + py * math.cos(r)


def lib_geometry(sym: list) -> tuple[dict[str, tuple[float, float]], list[tuple[float, float]]]:
    """Pins (number -> lib coords of the tip) and outline points of a lib symbol (all units)."""
    pins: dict[str, tuple[float, float]] = {}
    pts: list[tuple[float, float]] = []
    add = pts.extend

    def walk(node: list) -> None:
        for c in node[1:]:
            if not isinstance(c, list) or not c:
                continue
            if c[0] == "pin":
                at = kid(c, "at")
                number = kid(c, "number")
                pins.setdefault(str(number[1]), (num(at), num(at, 2)))
                add([(num(at), num(at, 2))])
            elif c[0] == "rectangle":
                add([(num(kid(c, "start")), num(kid(c, "start"), 2)), (num(kid(c, "end")), num(kid(c, "end"), 2))])
            elif c[0] in ("polyline", "bezier"):
                add([(num(p), num(p, 2)) for p in (kid(c, "pts") or [])[1:] if isinstance(p, list)])
            elif c[0] == "circle":
                cx, cy, r = num(kid(c, "center")), num(kid(c, "center"), 2), num(kid(c, "radius"))
                add([(cx - r, cy - r), (cx + r, cy + r)])
            elif c[0] == "arc":
                add([(num(kid(c, k)), num(kid(c, k), 2)) for k in ("start", "mid", "end") if kid(c, k)])
            elif c[0] == "symbol":
                walk(c)
    walk(sym)
    return pins, pts


def r2(v: float) -> float:
    return round(v, 2)


def extract(sch_path: Path, net_path: Path) -> dict:
    root = parse(sch_path.read_text(encoding="utf-8"))
    libs = {str(s[1]): lib_geometry(s) for s in kids(kid(root, "lib_symbols"), "symbol")}
    nets = netlist(net_path.read_text(encoding="utf-8"))
    node_net = {(r, p): n for n, nodes in nets.items() for r, p, _ in nodes}
    pinfunc = {(r, p): f for nodes in nets.values() for r, p, f in nodes}

    tips: dict[tuple[float, float], str] = {}  # pin tip -> net
    out_nets: dict[str, dict] = {n: {"pins": [], "wires": [], "labels": []} for n in nets}
    parts = {}
    power_at: list[tuple[float, float, str]] = []
    for s in kids(root, "symbol"):
        lib_id = str(kid(s, "lib_id")[1])
        at = kid(s, "at")
        x, y, a = num(at), num(at, 2), num(at, 3)
        mirror = kid(s, "mirror")
        props = {str(p[1]): str(p[2]) for p in kids(s, "property")}
        ref = props.get("Reference", "")
        pins, pts = libs[lib_id]
        def place(px: float, py: float) -> tuple[float, float]:
            if mirror and mirror[1] == "y":
                px = -px
            if mirror and mirror[1] == "x":
                py = -py
            rx, ry = rot(px, py, a)
            return r2(x + rx), r2(y - ry)
        if ref.startswith("#"):
            value = props.get("Value", "")
            for number, (px, py) in pins.items():
                tip = place(px, py)
                net = value if not ref.startswith("#FLG") else node_net.get((ref, number), "")
                if net:
                    tips[tip] = net
                    power_at.append((tip[0], tip[1], net))
            continue
        world = [place(px, py) for px, py in pts]
        xs, ys = [p[0] for p in world], [p[1] for p in world]
        parts[ref] = {"box": [min(xs), min(ys), max(xs), max(ys)], "value": props.get("Value", ""),
                      "footprint": props.get("Footprint", "").split(":")[-1], "mpn": props.get("MPN", ""),
                      "note": props.get("Design_Note", ""), "block": props.get("Block", ""),
                      "maker": props.get("Manufacturer", ""), "lcsc": props.get("LCSC", "")}
        for number, (px, py) in pins.items():
            tip = place(px, py)
            net = node_net.get((ref, number))
            if net:
                tips[tip] = net
                out_nets[net]["pins"].append([ref, number, pinfunc.get((ref, number), ""), tip[0], tip[1]])
            elif tip not in tips:
                tips.setdefault(tip, "")
    # wires: each touches a pin tip (stub) or a power-flag tip
    wire_net: list[tuple[list[float], str]] = []
    for w in kids(root, "wire"):
        pts = [(r2(num(p)), r2(num(p, 2))) for p in (kid(w, "pts") or [])[1:] if isinstance(p, list)]
        net = next((tips[p] for p in pts if tips.get(p)), "")
        if net:
            out_nets[net]["wires"].append([pts[0][0], pts[0][1], pts[-1][0], pts[-1][1]])
            wire_net.append(([pts[0][0], pts[0][1], pts[-1][0], pts[-1][1]], net))
    for lab in kids(root, "label") + kids(root, "global_label"):
        at = kid(lab, "at")
        name = str(lab[1])
        if name in out_nets:
            out_nets[name]["labels"].append([r2(num(at)), r2(num(at, 2)), num(at, 3)])
    for x, y, net in power_at:
        if net in out_nets:
            out_nets[net]["labels"].append([x, y, -1])
    texts = [[str(t[1]), r2(num(kid(t, "at"))), r2(num(kid(t, "at"), 2))] for t in kids(root, "text")]
    return {"source": sch_path.name, "nets": out_nets, "parts": parts, "notes": texts}


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    data = extract(Path(sys.argv[1]), Path(sys.argv[2]))
    Path(sys.argv[3]).write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    lone = [n for n, d in data["nets"].items() if not n.startswith("unconnected") and not d["wires"]]
    print(f"{Path(sys.argv[3]).name}: {len(data['parts'])} parts, {len(data['nets'])} nets"
          + (f"; nets without wires: {lone}" if lone else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
