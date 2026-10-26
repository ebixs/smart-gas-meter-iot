#!/usr/bin/env python3
"""Extract a KiCad board into JSON for the exploded board models.

Reads a .kicad_pcb file directly (KiCad 7, 8 or 9 format; no KiCad install needed) and
writes, in board-local millimetres (origin = board top-left, x right, y down):

* the outline size and corner radius,
* every footprint: reference, value, footprint name, position, rotation, side, and its body
  rectangle (from the F.Fab/B.Fab drawing, else the courtyard),
* per-layer artwork as compact SVG markup: copper (tracks, arcs, pads, vias, filled zones,
  drill holes) for each copper layer, and silkscreen (lines, arcs, circles, polygons, text)
  plus solder-mask openings for the top and bottom.

Usage: python3 pcb_extract.py BOARD.kicad_pcb OUT.json
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

TOKEN = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')


def parse(text: str) -> list:
    stack: list[list] = [[]]
    for tok in TOKEN.findall(text):
        if tok == "(":
            stack.append([])
        elif tok == ")":
            node = stack.pop()
            stack[-1].append(node)
        elif tok.startswith('"'):
            stack[-1].append(tok[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
        else:
            stack[-1].append(tok)
    return stack[0][0]


def kids(node: list, name: str) -> list[list]:
    return [c for c in node[1:] if isinstance(c, list) and c and c[0] == name]


def kid(node: list, name: str) -> list | None:
    for c in node[1:]:
        if isinstance(c, list) and c and c[0] == name:
            return c
    return None


def num(node: list | None, i: int = 1, default: float = 0.0) -> float:
    try:
        return float(node[i])  # type: ignore[index]
    except (TypeError, IndexError, ValueError):
        return default


def layers_of(node: list) -> list[str]:
    lay = kid(node, "layers") or kid(node, "layer")
    return [str(x) for x in lay[1:]] if lay else []


def f(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Board:
    def __init__(self, path: Path) -> None:
        self.root = parse(path.read_text(encoding="utf-8"))
        xs, ys = [], []
        for item in self.edges():
            for x, y in item:
                xs.append(x)
                ys.append(y)
        self.x0, self.y0, self.x1, self.y1 = min(xs), min(ys), max(xs), max(ys)
        self.art: dict[str, list[str]] = {}

    def edges(self):
        for kind in ("gr_line", "gr_arc", "gr_rect"):
            for node in kids(self.root, kind):
                if "Edge.Cuts" in layers_of(node):
                    pts = [(num(kid(node, k)), num(kid(node, k), 2)) for k in ("start", "mid", "end") if kid(node, k)]
                    yield pts

    def local(self, x: float, y: float) -> tuple[float, float]:
        return x - self.x0, y - self.y0

    def add(self, layer: str, markup: str) -> None:
        self.art.setdefault(layer, []).append(markup)


def rot(px: float, py: float, deg: float) -> tuple[float, float]:
    """KiCad footprint-local -> board offset: rotation is counter-clockwise on screen (y down)."""
    a = math.radians(deg)
    return px * math.cos(a) + py * math.sin(a), -px * math.sin(a) + py * math.cos(a)


def arc_path(start, mid, end) -> str:
    (x1, y1), (x2, y2), (x3, y3) = start, mid, end
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-9:
        return f"M{f(x1)} {f(y1)}L{f(x3)} {f(y3)}"
    ux = ((x1 ** 2 + y1 ** 2) * (y2 - y3) + (x2 ** 2 + y2 ** 2) * (y3 - y1) + (x3 ** 2 + y3 ** 2) * (y1 - y2)) / d
    uy = ((x1 ** 2 + y1 ** 2) * (x3 - x2) + (x2 ** 2 + y2 ** 2) * (x1 - x3) + (x3 ** 2 + y3 ** 2) * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    cross = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)
    sweep = 1 if cross > 0 else 0
    a1 = math.atan2(y1 - uy, x1 - ux)
    a3 = math.atan2(y3 - uy, x3 - ux)
    span = (a3 - a1) % (2 * math.pi) if sweep else (a1 - a3) % (2 * math.pi)
    large = 1 if span > math.pi else 0
    return f"M{f(x1)} {f(y1)}A{f(r)} {f(r)} 0 {large} {sweep} {f(x3)} {f(y3)}"


def pad_markup(cx: float, cy: float, angle: float, pad: list, cls: str = "") -> str:
    shape = pad[3] if len(pad) > 3 else "rect"
    size = kid(pad, "size")
    w, h = num(size), num(size, 2)
    c = f' class="{cls}"' if cls else ""
    tr = f' transform="rotate({f(-angle)} {f(cx)} {f(cy)})"' if abs(angle) % 360 > 0.01 else ""
    if shape == "circle":
        return f'<circle{c} cx="{f(cx)}" cy="{f(cy)}" r="{f(w / 2)}"/>'
    if shape == "oval":
        r = min(w, h) / 2
    elif shape == "roundrect":
        r = min(w, h) * num(kid(pad, "roundrect_rratio"), 1, 0.25)
    else:
        r = 0
    rx = f' rx="{f(r)}"' if r > 0 else ""
    return f'<rect{c} x="{f(cx - w / 2)}" y="{f(cy - h / 2)}" width="{f(w)}" height="{f(h)}"{rx}{tr}/>'


COPPER = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")


def extract(path: Path) -> dict:
    b = Board(path)
    footprints = []
    holes: list[str] = []
    for fp in kids(b.root, "footprint"):
        at = kid(fp, "at")
        fx, fy, frot = num(at), num(at, 2), num(at, 3)
        side = "B" if (kid(fp, "layer") or [None, "F.Cu"])[1] == "B.Cu" else "F"
        props = {p[1]: p[2] for p in kids(fp, "property") if len(p) > 2}
        for t in kids(fp, "fp_text"):  # KiCad 7 stores reference/value as fp_text
            if len(t) > 2 and t[1] in ("reference", "value"):
                props.setdefault(t[1].capitalize(), t[2])
        ref = props.get("Reference", "")
        name = str(fp[1]).split(":")[-1]
        fab, crt = [], []
        for kind in ("fp_line", "fp_rect", "fp_circle", "fp_poly", "fp_arc"):
            for g in kids(fp, kind):
                lay = layers_of(g)
                pts = [(num(p, 1), num(p, 2)) for p in (kid(g, "pts") or [])[1:] if isinstance(p, list)]
                pts += [(num(kid(g, k)), num(kid(g, k), 2)) for k in ("start", "end", "mid", "center") if kid(g, k)]
                if kind == "fp_circle" and kid(g, "center"):
                    cx, cy = num(kid(g, "center")), num(kid(g, "center"), 2)
                    r = math.hypot(num(kid(g, "end")) - cx, num(kid(g, "end"), 2) - cy)
                    pts += [(cx - r, cy - r), (cx + r, cy + r)]
                if any(l.endswith(".Fab") for l in lay):
                    fab += pts
                elif any(l.endswith(".CrtYd") for l in lay):
                    crt += pts
                # silkscreen artwork of the footprint
                for l in lay:
                    if l.endswith(".SilkS") or l.endswith(".Silkscreen"):
                        b.add(("F" if l.startswith("F") else "B") + ".Silk", silk_shape(kind, g, fx, fy, frot, b))
        for t in kids(fp, "fp_text") + kids(fp, "property"):
            lay = layers_of(t)
            hidden = "hide" in t or (kid(t, "hide") and kid(t, "hide")[1:] != ["no"]) or \
                (kid(t, "effects") and "hide" in kid(t, "effects"))
            if hidden or len(t) < 3:
                continue
            for l in lay:
                if l.endswith(".SilkS") or l.endswith(".Silkscreen"):
                    b.add(("F" if l.startswith("F") else "B") + ".Silk", silk_shape("fp_text", t, fx, fy, frot, b))
        src = fab or crt
        body = None
        if src:
            corners = [rot(x, y, frot) for x, y in src]
            xs = [fx + dx for dx, _ in corners]
            ys = [fy + dy for _, dy in corners]
            lx0, ly0 = b.local(min(xs), min(ys))
            lx1, ly1 = b.local(max(xs), max(ys))
            if not fab:  # courtyard is ~0.25 mm outside the body
                lx0, ly0, lx1, ly1 = lx0 + 0.25, ly0 + 0.25, lx1 - 0.25, ly1 - 0.25
            body = [round(lx0, 2), round(ly0, 2), round(lx1, 2), round(ly1, 2)]
        pads = []
        for pad in kids(fp, "pad"):
            pat = kid(pad, "at")
            px, py, pr = num(pat), num(pat, 2), num(pat, 3)
            dx, dy = rot(px, py, frot)
            cx, cy = b.local(fx + dx, fy + dy)
            lays = layers_of(pad)
            net = kid(pad, "net")
            netname = str(net[2]) if net and len(net) > 2 else (str(net[1]) if net and len(net) > 1 and not str(net[1]).isdigit() else "")
            ptype = pad[2] if len(pad) > 2 else "smd"
            copper = [l for l in COPPER if l in lays or "*.Cu" in lays or ("F&B.Cu" in lays and l in ("F.Cu", "B.Cu"))]
            if ptype in ("thru_hole", "np_thru_hole") and "*.Cu" in lays:
                copper = list(COPPER)
            mark = pad_markup(cx, cy, pr, pad)
            for l in copper:
                b.add(l, mark)
            for l in lays:
                if l in ("F.Mask", "B.Mask", "*.Mask"):
                    for m in (("F.Mask", "B.Mask") if l == "*.Mask" else (l,)):
                        b.add(m, mark)
            drill = kid(pad, "drill")
            if drill:
                d = num(drill)
                holes.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(d / 2)}"/>')
            pads.append({"n": str(pad[1]), "net": netname.lstrip("/"), "x": round(cx, 3), "y": round(cy, 3)})
        footprints.append({"ref": ref, "value": props.get("Value", ""), "fp": name, "x": round(b.local(fx, fy)[0], 3),
                           "y": round(b.local(fx, fy)[1], 3), "rot": frot, "side": side, "body": body,
                           "mpn": props.get("MPN", ""), "pads": pads})

    for seg in kids(b.root, "segment"):
        lay = layers_of(seg)[0]
        (x1, y1), (x2, y2) = b.local(num(kid(seg, "start")), num(kid(seg, "start"), 2)), b.local(num(kid(seg, "end")), num(kid(seg, "end"), 2))
        b.add(lay, f'<path class="t" d="M{f(x1)} {f(y1)}L{f(x2)} {f(y2)}" stroke-width="{f(num(kid(seg, "width")))}"/>')
    for arc in kids(b.root, "arc"):
        lay = layers_of(arc)[0]
        pts = [b.local(num(kid(arc, k)), num(kid(arc, k), 2)) for k in ("start", "mid", "end")]
        b.add(lay, f'<path class="t" d="{arc_path(*pts)}" stroke-width="{f(num(kid(arc, "width")))}"/>')
    for via in kids(b.root, "via"):
        x, y = b.local(num(kid(via, "at")), num(kid(via, "at"), 2))
        for l in COPPER:
            b.add(l, f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(num(kid(via, "size")) / 2)}"/>')
        holes.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(num(kid(via, "drill")) / 2)}"/>')
    for z in kids(b.root, "zone"):
        for fpoly in kids(z, "filled_polygon"):
            lay = layers_of(fpoly)[0]
            pts = [b.local(num(p, 1), num(p, 2)) for p in (kid(fpoly, "pts") or [])[1:] if isinstance(p, list) and p[0] == "xy"]
            if pts:
                d = "M" + "L".join(f"{f(x)} {f(y)}" for x, y in pts) + "Z"
                b.add(lay + "#zone", f'<path class="z" d="{d}"/>')
    for kind in ("gr_line", "gr_arc", "gr_circle", "gr_poly", "gr_rect", "gr_text"):
        for g in kids(b.root, kind):
            for l in layers_of(g):
                if l.endswith(".SilkS") or l.endswith(".Silkscreen"):
                    b.add(("F" if l.startswith("F") else "B") + ".Silk", silk_shape(kind.replace("gr_", "fp_"), g, 0, 0, 0, b))

    w, h = b.x1 - b.x0, b.y1 - b.y0
    return {
        "source": path.name,
        "w": round(w, 3), "h": round(h, 3),
        # zone fills first, so tracks and pads are drawn over the pour
        "layers": {k: "".join(b.art.get(k + "#zone", []) + v) for k, v in sorted(b.art.items()) if k in COPPER + ("F.Silk", "B.Silk", "F.Mask", "B.Mask")},
        "holes": "".join(holes),
        "footprints": footprints,
    }


def silk_shape(kind: str, g: list, fx: float, fy: float, frot: float, b: Board) -> str:
    def P(node_name: str) -> tuple[float, float]:
        n = kid(g, node_name)
        dx, dy = rot(num(n), num(n, 2), frot)
        return b.local(fx + dx, fy + dy)
    stroke = kid(g, "stroke")
    width = num(kid(stroke, "width")) if stroke else num(kid(g, "width"), 1, 0.12)
    sw = f' stroke-width="{f(max(width, 0.1))}"'
    if kind == "fp_line":
        (x1, y1), (x2, y2) = P("start"), P("end")
        return f'<path d="M{f(x1)} {f(y1)}L{f(x2)} {f(y2)}"{sw}/>'
    if kind == "fp_arc":
        return f'<path d="{arc_path(P("start"), P("mid"), P("end"))}"{sw}/>'
    if kind == "fp_circle":
        (cx, cy), (ex, ey) = P("center"), P("end")
        fill = kid(g, "fill")
        filled = fill and len(fill) > 1 and fill[1] in ("solid", "yes")
        return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(math.hypot(ex - cx, ey - cy))}"{sw}{" class=\"s\"" if filled else ""}/>'
    if kind == "fp_rect":
        (x1, y1), (x2, y2) = P("start"), P("end")
        return f'<path d="M{f(x1)} {f(y1)}L{f(x2)} {f(y1)}L{f(x2)} {f(y2)}L{f(x1)} {f(y2)}Z"{sw}/>'
    if kind == "fp_poly":
        pts = []
        for p in (kid(g, "pts") or [])[1:]:
            if isinstance(p, list) and p[0] == "xy":
                dx, dy = rot(num(p, 1), num(p, 2), frot)
                pts.append(b.local(fx + dx, fy + dy))
        if not pts:
            return ""
        fill = kid(g, "fill")
        filled = fill and len(fill) > 1 and fill[1] in ("solid", "yes")
        return f'<path{" class=\"s\"" if filled else ""} d="M' + "L".join(f"{f(x)} {f(y)}" for x, y in pts) + f'Z"{sw}/>'
    if kind in ("fp_text", "fp_text_gr") or g[0] in ("fp_text", "gr_text"):
        if kid(g, "hide") or (len(g) > 3 and "hide" in g):
            return ""
        txt = g[2] if g[0] in ("fp_text", "property") else g[1]
        at = kid(g, "at")
        dx, dy = rot(num(at), num(at, 2), frot)
        x, y = b.local(fx + dx, fy + dy)
        eff = kid(g, "effects")
        font = kid(eff, "font") if eff else None
        size = num(kid(font, "size"), 1, 1.0) if font else 1.0
        angle = num(at, 3)
        mirrored = bool(eff and kid(eff, "justify") and "mirror" in kid(eff, "justify"))
        tr = f' transform="rotate({f(-angle)} {f(x)} {f(y)})"' if angle else ""
        if mirrored:
            tr = f' transform="translate({f(2 * x)} 0) scale(-1 1){" rotate(" + f(angle) + f" {f(x)} {f(y)})" if angle else ""}"'
        txt = str(txt).replace("&", "&amp;").replace("<", "&lt;")
        if txt.startswith("${"):
            return ""
        return f'<text x="{f(x)}" y="{f(y + size * 0.36)}" font-size="{f(size * 1.05)}"{tr}>{txt}</text>'
    return ""


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    data = extract(Path(sys.argv[1]))
    out = Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    sizes = ", ".join(f"{k} {len(v) // 1024} KB" for k, v in data["layers"].items())
    print(f"{out.name}: {data['w']} x {data['h']} mm, {len(data['footprints'])} footprints; {sizes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
