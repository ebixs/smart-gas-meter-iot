#!/usr/bin/env python3
"""Build the modem daughterboard v0.1 PCB from design_modem_v01.py + pcb_layout_modem_v01.py.

Places every part, sets nets (including KiCad's per-pin names for intentional no-connects so
schematic-parity DRC is exact), drops GND and MODEM_VIN SMD pads to their planes with short
fan-out vias, adds the 4-layer pours, optionally autoroutes with Freerouting, refills zones
and writes a DRC report. Runs on KiCad 7.0.11's pcbnew Python module (also KiCad 8/9).

The EC200U footprint is PROVISIONAL, so the result is a layout study, not a release.

Usage: python3 hardware/kicad-modem/tools/build_pcb.py [--route] [--freerouting JAR] [--passes N]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import pcbnew

MODEM_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODEM_DIR))
sys.path.insert(0, str(MODEM_DIR.parent / "kicad" / "tools"))
import design_modem_v01 as design  # noqa: E402
import pcb_layout_modem_v01 as layout  # noqa: E402
from generate_schematic import uid  # noqa: E402  (carrier generator's deterministic UUIDs)

PCB = MODEM_DIR / "sgm_modem.kicad_pcb"
PRETTY = str(MODEM_DIR / "lib" / f"{design.LIB}.pretty")
MM = pcbnew.FromMM
PLANE_NETS = {"GND": pcbnew.In1_Cu, "MODEM_VIN": pcbnew.In2_Cu}


def pos(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(MM(layout.ORIGIN[0] + x), MM(layout.ORIGIN[1] + y))


def net_name(net: str) -> str:
    return net if net == "GND" else f"/{net}"


def load_footprint(name: str) -> pcbnew.FOOTPRINT:
    fp = pcbnew.FootprintLoad(PRETTY, name)
    if fp is None:
        raise SystemExit(f"footprint {name} not found in {PRETTY}")
    fp.SetFPID(pcbnew.LIB_ID(design.LIB, name))
    return fp


def outline(board: pcbnew.BOARD) -> None:
    w, h, r = layout.BOARD_W, layout.BOARD_H, layout.CORNER_R
    for a, b in (((r, 0), (w - r, 0)), ((w, r), (w, h - r)), ((w - r, h), (r, h)), ((0, h - r), (0, r))):
        line = pcbnew.PCB_SHAPE(board)
        line.SetShape(pcbnew.SHAPE_T_SEGMENT)
        line.SetStart(pos(*a))
        line.SetEnd(pos(*b))
        line.SetLayer(pcbnew.Edge_Cuts)
        line.SetWidth(MM(0.1))
        board.Add(line)
    for cx, cy, sx, sy in ((r, r, 0, r), (w - r, r, w - r, 0), (w - r, h - r, w, h - r), (r, h - r, r, h)):
        arc = pcbnew.PCB_SHAPE(board)
        arc.SetShape(pcbnew.SHAPE_T_ARC)
        arc.SetCenter(pos(cx, cy))
        arc.SetStart(pos(sx, sy))
        arc.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
        arc.SetLayer(pcbnew.Edge_Cuts)
        arc.SetWidth(MM(0.1))
        board.Add(arc)


def zone(board: pcbnew.BOARD, layer: int, net: pcbnew.NETINFO_ITEM, name: str, priority: int = 0) -> None:
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net)
    z.SetZoneName(name)
    z.SetAssignedPriority(priority)
    z.SetLocalClearance(MM(0.25))
    z.SetMinThickness(MM(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetThermalReliefGap(MM(0.3))
    z.SetThermalReliefSpokeWidth(MM(0.4))
    poly = z.Outline()
    poly.NewOutline()
    inset = 0.4
    for x, y in ((inset, inset), (layout.BOARD_W - inset, inset),
                 (layout.BOARD_W - inset, layout.BOARD_H - inset), (inset, layout.BOARD_H - inset)):
        poly.Append(pos(x, y))
    board.Add(z)


def pin_names() -> dict[tuple[str, str], str]:
    text = (MODEM_DIR / "lib" / "sgm_modem.kicad_sym").read_text(encoding="utf-8")
    names: dict[tuple[str, str], str] = {}
    for symbol in re.finditer(r'^\(symbol "([^"]+)"', text, re.M):
        end = text.find("\n(symbol ", symbol.start() + 1)
        body = text[symbol.start():end if end > 0 else None]
        for pin in re.finditer(r'\(name "([^"]*)".*?\(number "([^"]+)"', body, re.S):
            names.setdefault((symbol.group(1), pin.group(2)), pin.group(1))
    return names


def assign_nc_nets(board: pcbnew.BOARD) -> int:
    names = pin_names()
    by_ref = {p.ref: p for p in design.PARTS}
    count = 0
    for fp in board.GetFootprints():
        part = by_ref.get(fp.GetReference())
        if part is None:
            continue
        for pad in fp.Pads():
            if part.pins.get(pad.GetNumber()) == design.NC:
                pin = names.get((part.symbol, pad.GetNumber()), "")
                net = pcbnew.NETINFO_ITEM(board, f"unconnected-({part.ref}-{pin}-Pad{pad.GetNumber()})")
                board.Add(net)
                pad.SetNet(net)
                count += 1
    return count


def build() -> pcbnew.BOARD:
    board = pcbnew.NewBoard(str(PCB))
    board.SetCopperLayerCount(layout.LAYERS)
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(layout.LAYERS)
    rules = layout.BOARD_RULES
    ds.m_MinClearance = MM(rules["min_clearance"])
    ds.m_TrackMinWidth = MM(rules["min_track_width"])
    ds.m_ViasMinSize = MM(rules["min_via_diameter"])
    ds.m_MinThroughDrill = MM(rules["min_through_hole_diameter"])
    ds.m_HoleClearance = MM(rules["min_hole_clearance"])
    ds.m_HoleToHoleMin = MM(rules["min_hole_to_hole"])
    ds.m_CopperEdgeClearance = MM(rules["min_copper_edge_clearance"])

    title = board.GetTitleBlock()
    title.SetTitle(design.TITLE)
    title.SetRevision(design.REVISION)
    title.SetDate("2026-10-26")
    title.SetCompany("Smart Gas Meter IoT - lab prototype")
    for i, comment in enumerate(design.COMMENTS):
        title.SetComment(i, comment)

    nets: dict[str, pcbnew.NETINFO_ITEM] = {}
    for net in design.expected_nets():
        info = pcbnew.NETINFO_ITEM(board, net_name(net))
        board.Add(info)
        nets[net] = info

    missing = {p.ref for p in design.PARTS} - set(layout.PLACEMENT)
    if missing:
        raise SystemExit(f"parts without placement: {sorted(missing)}")
    root = uid("modem-root")
    for part in design.PARTS:
        x, y, rot, side = layout.PLACEMENT[part.ref]
        fp = load_footprint(part.footprint)
        fp.SetReference(part.ref)
        fp.SetValue(part.value)
        fp.SetPosition(pos(x, y))
        fp.SetOrientationDegrees(rot)
        fp.SetPath(pcbnew.KIID_PATH(f"/{root}/{uid('sym', part.ref)}"))
        for key, value in (("MPN", part.mpn), ("Block", part.block)):
            fp.SetProperty(key, value)
        for pad in fp.Pads():
            net = part.pins.get(pad.GetNumber())
            if net and net != design.NC:
                pad.SetNet(nets[net])
        board.Add(fp)
        if side == "B":
            fp.Flip(fp.GetPosition(), False)
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8)))
        fp.Reference().SetTextThickness(MM(0.12))
        if part.ref in layout.FAB_ONLY_REFERENCES:
            fp.Reference().SetLayer(pcbnew.F_Fab)

    for ref, name, x, y in layout.MOUNTING_HOLES:
        fp = load_footprint(name)
        fp.SetReference(ref)
        fp.SetValue("M2.5")
        fp.SetPosition(pos(x, y))
        fp.SetExcludedFromBOM(True)
        fp.SetExcludedFromPosFiles(True)
        fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_BOARD_ONLY)
        fp.Reference().SetVisible(False)
        board.Add(fp)

    outline(board)
    for text, x, y, size, layer_name in layout.SILKSCREEN:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetPosition(pos(x, y))
        layer = {"F.SilkS": pcbnew.F_SilkS, "B.SilkS": pcbnew.B_SilkS}[layer_name]
        t.SetLayer(layer)
        t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
        t.SetTextThickness(MM(max(0.12, size * 0.15)))
        if layer == pcbnew.B_SilkS:
            t.SetMirrored(True)
        board.Add(t)

    vias = {net: fanout(board, net) for net in PLANE_NETS}
    print(f"Plane fan-out vias: {vias}; NC pins: {assign_nc_nets(board)}")
    zone(board, pcbnew.In1_Cu, nets["GND"], "GND plane")
    zone(board, pcbnew.In2_Cu, nets["MODEM_VIN"], "VBAT plane")
    zone(board, pcbnew.B_Cu, nets["GND"], "GND pour bottom")
    zone(board, pcbnew.F_Cu, nets["GND"], "GND pour top")
    return board


def fanout(board: pcbnew.BOARD, net_name_: str) -> int:
    """Drop every top-side SMD pad of a plane net to its plane with a short track and a via.

    Candidate via positions are tried around each pad (outward from the part first) and
    accepted only if they keep clear of other-net pads, holes, the board edge and earlier vias.
    """
    via_d, drill, clear = MM(0.5), MM(0.25), MM(0.2)
    net = board.FindNet(net_name(net_name_))
    blockers = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            blockers.append((pad.GetBoundingBox(), pad.GetNetCode(), pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH))
    for item in board.GetTracks():
        blockers.append((item.GetBoundingBox(), item.GetNetCode(), False))
    edge = board.GetBoardEdgesBoundingBox()
    edge.Inflate(-MM(0.8))
    placed = [t.GetPosition() for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]

    size_t = getattr(pcbnew, "VECTOR2L", pcbnew.VECTOR2I)

    def clear_at(pt: pcbnew.VECTOR2I, radius: int) -> bool:
        probe = pcbnew.BOX2I(pcbnew.VECTOR2I(pt.x - radius, pt.y - radius), size_t(2 * radius, 2 * radius))
        for box, code, hole in blockers:
            if (code != net.GetNetCode() or hole) and box.Intersects(probe):
                return False
        return True

    def free(start: pcbnew.VECTOR2I, pt: pcbnew.VECTOR2I, width: int) -> bool:
        if not edge.Contains(pt) or not clear_at(pt, via_d // 2 + clear):
            return False
        # the fan-out track itself must also stay clear of other-net copper
        for k in range(1, 8):
            f = k / 8
            mid = pcbnew.VECTOR2I(int(start.x + (pt.x - start.x) * f), int(start.y + (pt.y - start.y) * f))
            if not clear_at(mid, width // 2 + MM(0.16)):
                return False
        return all((pt - other).EuclideanNorm() > via_d + clear for other in placed)

    count = 0
    for fp in board.GetFootprints():
        center = fp.GetPosition()
        for pad in fp.Pads():
            if pad.GetNetCode() != net.GetNetCode() or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            if not pad.IsOnLayer(pcbnew.F_Cu):
                continue
            p = pad.GetPosition()
            out = p - center
            norm = max(out.EuclideanNorm(), 1)
            ux, uy = out.x / norm, out.y / norm
            half = max(pad.GetSize().x, pad.GetSize().y) // 2
            width = min(MM(0.3 if net_name_ == "GND" else 0.5), min(pad.GetSize().x, pad.GetSize().y))
            # LGA pads under the module: put the via in the gap beside the pad (no via-in-pad).
            if fp.GetReference() == "U1" and int(pad.GetNumber()) > 80:
                directions = [(0.7071, 0.7071), (-0.7071, 0.7071), (0.7071, -0.7071), (-0.7071, -0.7071)]
                extras = (0.35, 0.5)
            else:
                directions = [(ux, uy), (-uy, ux), (uy, -ux), (-ux, -uy)]
                extras = (0.45, 0.7, 1.0, 1.4)
            target = None
            for dx, dy in directions:
                for extra in extras:
                    dist = half + MM(extra)
                    pt = pcbnew.VECTOR2I(int(p.x + dx * dist), int(p.y + dy * dist))
                    if free(p, pt, width):
                        target = pt
                        break
                if target:
                    break
            if target is None:
                print(f"fanout {net_name_}: no free via site for {fp.GetReference()}.{pad.GetNumber()}")
                continue
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(target)
            via.SetWidth(via_d)
            via.SetDrill(drill)
            via.SetNet(net)
            board.Add(via)
            track = pcbnew.PCB_TRACK(board)
            track.SetStart(p)
            track.SetEnd(target)
            track.SetWidth(width)
            track.SetLayer(pcbnew.F_Cu)
            track.SetNet(net)
            board.Add(track)
            placed.append(target)
            blockers.append((via.GetBoundingBox(), net.GetNetCode(), False))
            blockers.append((track.GetBoundingBox(), net.GetNetCode(), False))
            count += 1
    return count


def fill_and_save(board: pcbnew.BOARD) -> pcbnew.BOARD:
    pcbnew.SaveBoard(str(PCB), board)
    board = pcbnew.LoadBoard(str(PCB))
    board.BuildConnectivity()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(PCB), board)
    return board


def route(jar: Path, passes: int, java: str, timeout: str = "00:04:00") -> None:
    board = pcbnew.LoadBoard(str(PCB))
    dsn, ses = PCB.with_suffix(".dsn"), PCB.with_suffix(".ses")
    if not pcbnew.ExportSpecctraDSN(board, str(dsn)):
        raise SystemExit("DSN export failed")
    text = dsn.read_text(encoding="utf-8")
    # In1 (GND) and In2 (MODEM_VIN) are planes reached by the fan-out vias: no tracks there.
    text = re.sub(r"(\(layer In1\.Cu\s*\(type )signal", r"\1power", text)
    text = re.sub(r"(\(layer In2\.Cu\s*\(type )signal", r"\1power", text)
    # The outer GND pours are filled after routing; they are not routing targets.
    text = re.sub(r"\s*\(plane GND \(polygon (?:F|B)\.Cu[^)]*\)\)", "", text)
    dsn.write_text(text, encoding="utf-8")
    cmd = [java, "-jar", str(jar), "-de", str(dsn), "-do", str(ses), "-mp", str(passes), f"--router.job_timeout={timeout}",
           "--gui.enabled=false"]
    print("Running:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)
    import_ses(board, ses)
    print(f"Dangling track stubs removed: {prune_dangling(board)}")
    board = fill_and_save(board)
    print(f"GND stitching vias: {stitch(board)}")
    board = fill_and_save(board)
    print(f"Vias added to tie isolated pour pieces: {tie_islands(board)}")
    board = fill_and_save(board)
    print(f"Dangling track stubs removed after fill: {prune_dangling(board)}")
    fill_and_save(board)
    dsn.unlink(missing_ok=True)
    ses.unlink(missing_ok=True)


def stitch(board: pcbnew.BOARD, pitch: float = 2.5) -> int:
    """GND vias wherever both outer GND pours are filled, so every piece of the top and bottom pour
    is tied to the In1 plane (and RF/SIM areas get a dense ground fence)."""
    gnd = board.FindNet("GND")
    pours = [z for z in board.Zones() if z.GetNetCode() == gnd.GetNetCode() and z.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu)]
    via_d, drill, keep = MM(0.5), MM(0.25), MM(0.35)
    others = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():  # never put a via in or beside any pad (no via-in-pad, no hole near a hole)
            box = pad.GetBoundingBox()
            box.Inflate(keep + via_d // 2)
            others.append(box)
    for t in board.GetTracks():
        if t.GetNetCode() != gnd.GetNetCode() or isinstance(t, pcbnew.PCB_VIA):
            box = t.GetBoundingBox()
            box.Inflate(keep + via_d // 2)
            others.append(box)
    count = 0
    y = 1.6
    while y < layout.BOARD_H - 1.5:
        x = 1.6
        while x < layout.BOARD_W - 1.5:
            pt = pos(x, y)
            inside = all(z.GetFilledPolysList(z.GetLayer()).Contains(pt, -1, via_d // 2 + MM(0.2)) for z in pours)
            if inside and not any(b.Contains(pt) for b in others):
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pt)
                v.SetWidth(via_d)
                v.SetDrill(drill)
                v.SetNet(gnd)
                board.Add(v)
                box = v.GetBoundingBox()
                box.Inflate(keep)
                others.append(box)
                count += 1
            x += pitch
        y += pitch
    return count


def prune_dangling(board: pcbnew.BOARD) -> int:
    """Remove track segments with a free end (autorouter leftovers), repeating until none remain."""
    removed = 0
    while True:
        board.BuildConnectivity()
        conn = board.GetConnectivity()
        dead = [t for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA) and conn.TestTrackEndpointDangling(t, False)]
        if not dead:
            return removed
        for t in dead:
            board.Remove(t)
        removed += len(dead)


def tie_islands(board: pcbnew.BOARD) -> int:
    """Add a GND via inside any piece of an outer GND pour that has no via of its own."""
    gnd = board.FindNet("GND")
    vias = [t for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA) and t.GetNetCode() == gnd.GetNetCode()]
    added = 0
    for z in board.Zones():
        if z.GetNetCode() != gnd.GetNetCode() or z.GetLayer() not in (pcbnew.F_Cu, pcbnew.B_Cu):
            continue
        polys = z.GetFilledPolysList(z.GetLayer())
        for i in range(polys.OutlineCount()):
            piece = pcbnew.SHAPE_POLY_SET()
            piece.AddOutline(polys.Outline(i))
            if any(piece.Contains(v.GetPosition()) for v in vias):
                continue
            box = piece.BBox()
            step = MM(0.5)
            done = False
            y = box.GetTop() + step
            while y < box.GetBottom() and not done:
                x = box.GetLeft() + step
                while x < box.GetRight() and not done:
                    pt = pcbnew.VECTOR2I(x, y)
                    if piece.Contains(pt, -1, MM(0.45)):
                        v = pcbnew.PCB_VIA(board)
                        v.SetPosition(pt)
                        v.SetWidth(MM(0.5))
                        v.SetDrill(MM(0.25))
                        v.SetNet(gnd)
                        board.Add(v)
                        vias.append(v)
                        added += 1
                        done = True
                    x += step
                y += step
    return added


def import_ses(board: pcbnew.BOARD, ses: Path) -> None:
    """Replace the board's tracks and vias with a Specctra session (KiCad 7's ImportSpecctraSES
    only works inside the editor, so the session is applied here directly)."""
    sys.path.insert(0, str(MODEM_DIR.parent / "visualization" / "boards" / "tools"))
    from pcb_extract import parse, kids, kid  # small S-expression reader
    tree = parse(ses.read_text(encoding="utf-8"))
    routes = kid(tree, "routes")
    res = kid(routes, "resolution")
    scale = 1000.0 / float(res[2]) if res else 1000.0  # session units -> nanometres
    to_nm = lambda v: int(round(float(v) * scale))  # noqa: E731
    stacks = {}
    for ps in kids(kid(routes, "library_out") or ["library_out"], "padstack"):
        m = re.search(r"_(\d+):(\d+)_um", ps[1])
        if m:
            stacks[ps[1]] = (int(m.group(1)) * 1000, int(m.group(2)) * 1000)
    for item in list(board.GetTracks()):
        board.Remove(item)
    layers = {board.GetLayerName(i): i for i in range(pcbnew.PCB_LAYER_ID_COUNT)}
    count = [0, 0]
    for net_node in kids(kid(routes, "network_out"), "net"):
        net = board.FindNet(net_node[1])
        if net is None:
            raise SystemExit(f"SES net {net_node[1]} not on the board")
        for wire in kids(net_node, "wire"):
            path = kid(wire, "path")
            layer, width = layers[path[1]], to_nm(path[2])
            pts = [pcbnew.VECTOR2I(to_nm(path[i]), -to_nm(path[i + 1])) for i in range(3, len(path) - 1, 2)]
            for a, b in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(a)
                t.SetEnd(b)
                t.SetWidth(width)
                t.SetLayer(layer)
                t.SetNet(net)
                board.Add(t)
                count[0] += 1
        for via_node in kids(net_node, "via"):
            size, drill = stacks.get(via_node[1], (500000, 250000))
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(to_nm(via_node[2]), -to_nm(via_node[3])))
            v.SetWidth(size)
            v.SetDrill(drill)
            v.SetNet(net)
            board.Add(v)
            count[1] += 1
    print(f"Imported session: {count[0]} track segments, {count[1]} vias")


def drc(report: Path) -> None:
    board = pcbnew.LoadBoard(str(PCB))
    pcbnew.WriteDRCReport(board, str(report), pcbnew.EDA_UNITS_MILLIMETRES, True)
    text = report.read_text(encoding="utf-8")
    counts = re.findall(r"\*\* Found (\d+) ([^*]+?) \*\*", text)
    print("DRC (KiCad 7):", "; ".join(f"{n} {what.strip()}" for n, what in counts), f"-> {report.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--route", action="store_true", help="autoroute with Freerouting")
    parser.add_argument("--freerouting", type=Path, default=Path("/opt/fr/freerouting.jar"))
    parser.add_argument("--passes", type=int, default=200)
    parser.add_argument("--java", default="java")
    parser.add_argument("--drc", type=Path, default=MODEM_DIR / "exports" / "drc-kicad-7.rpt")
    args = parser.parse_args()
    board = build()
    fill_and_save(board)
    print(f"Placed {len(design.PARTS)} parts + {len(layout.MOUNTING_HOLES)} holes on "
          f"{layout.BOARD_W:g} x {layout.BOARD_H:g} mm, {layout.LAYERS} layers -> {PCB.name}")
    if args.route:
        route(args.freerouting, args.passes, args.java)
        print("Routed and zones filled.")
    args.drc.parent.mkdir(exist_ok=True)
    drc(args.drc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
