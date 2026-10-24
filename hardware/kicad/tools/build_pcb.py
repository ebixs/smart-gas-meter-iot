#!/usr/bin/env python3
"""Build the v0.2 PCB from design_v02.py (nets) and pcb_layout_v02.py (placement).

Runs inside KiCad 9's Python (``import pcbnew``). Steps:
  1. place footprints from the project-local SGM library, link them to the
     schematic symbols (same UUIDs as the generated schematic) and assign nets;
  2. draw the board outline, mounting holes, silkscreen and copper zones
     (In1 = solid GND plane, In2 = signals + 3V3 pour, B.Cu = signals + GND pour;
     every top-side GND pad reaches the In1 plane through its own via);
  3. optionally autoroute with Freerouting (Specctra DSN/SES round trip);
  4. fill zones and save ``smart_gas_meter_iot.kicad_pcb``.

Usage (KiCad 9 python):
  python3 hardware/kicad/tools/build_pcb.py [--route --freerouting /path/freerouting.jar]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import pcbnew

KICAD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KICAD_DIR))
sys.path.insert(0, str(KICAD_DIR / "tools"))
import design_v02 as design  # noqa: E402
import pcb_layout_v02 as layout  # noqa: E402
from generate_schematic import POWER_SYMBOLS, uid  # noqa: E402

PCB = KICAD_DIR / "smart_gas_meter_iot.kicad_pcb"
PRETTY = str(KICAD_DIR / "lib" / f"{design.LIB}.pretty")
MM = pcbnew.FromMM


def pos(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(MM(layout.ORIGIN[0] + x), MM(layout.ORIGIN[1] + y))


def net_name(net: str) -> str:
    return net if net in POWER_SYMBOLS else f"/{net}"


def load_footprint(name: str) -> pcbnew.FOOTPRINT:
    fp = pcbnew.FootprintLoad(PRETTY, name)
    if fp is None:
        raise SystemExit(f"footprint {name} not found in {PRETTY}")
    fp.SetFPID(pcbnew.LIB_ID(design.LIB, name))
    return fp


def outline(board: pcbnew.BOARD) -> None:
    w, h, r = layout.BOARD_W, layout.BOARD_H, layout.CORNER_R
    segments = [((r, 0), (w - r, 0)), ((w, r), (w, h - r)), ((w - r, h), (r, h)), ((0, h - r), (0, r))]
    for a, b in segments:
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
    z.SetLocalClearance(MM(0.3))
    z.SetMinThickness(MM(0.25))
    # Solid connections for SMD pads (fine-pitch USB-C pads cannot fit thermal spokes);
    # thermal reliefs only for hand-soldered through-hole headers.
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


def build() -> pcbnew.BOARD:
    board = pcbnew.NewBoard(str(PCB))
    board.SetCopperLayerCount(layout.LAYERS)
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(layout.LAYERS)
    ds.m_MinClearance = MM(0.15)
    ds.m_TrackMinWidth = MM(0.15)
    ds.m_ViasMinSize = MM(0.5)
    # JLCPCB 4-layer capability: 0.2 mm min drill (the ESP32 module's thermal vias use 0.2 mm).
    ds.m_MinThroughDrill = MM(0.2)
    # GCT's USB4105 land pattern puts its locating holes 0.19 mm from the GND pads.
    ds.m_HoleClearance = MM(0.15)
    ds.m_HoleToHoleMin = MM(0.5)
    ds.m_CopperEdgeClearance = MM(0.3)

    title = board.GetTitleBlock()
    title.SetTitle(design.TITLE)
    title.SetRevision(design.REVISION)
    title.SetDate("2026-10-24")
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
    root = uid("root")
    for part in design.PARTS:
        x, y, rot = layout.PLACEMENT[part.ref]
        fp = load_footprint(part.footprint)
        fp.SetReference(part.ref)
        fp.SetValue(part.value)
        fp.SetPosition(pos(x, y))
        fp.SetOrientationDegrees(rot)
        fp.SetPath(pcbnew.KIID_PATH(f"/{root}/{uid('sym', part.ref)}"))
        for key in ("MPN", "LCSC", "Manufacturer"):
            value = part.mpn if key == "MPN" else part.fields.get(key, "")
            if value:
                field = pcbnew.PCB_FIELD(fp, fp.GetNextFieldId(), key)
                field.SetText(value)
                field.SetVisible(False)
                field.SetLayer(pcbnew.F_Fab)
                fp.AddField(field)
        if part.dnp:
            fp.SetDNP(True)
        for pad in fp.Pads():
            net = part.pins.get(pad.GetNumber())
            if net and net != design.NC:
                pad.SetNet(nets[net])
        board.Add(fp)
        # Keep reference designators readable and off pads.
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8)))
        fp.Reference().SetTextThickness(MM(0.12))

    for ref, name, x, y in layout.MOUNTING_HOLES:
        fp = load_footprint(name)
        fp.SetReference(ref)
        fp.SetValue("M3")
        fp.SetPosition(pos(x, y))
        fp.SetBoardOnly(True)
        fp.SetExcludedFromBOM(True)
        fp.SetExcludedFromPosFiles(True)
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

    zone(board, pcbnew.In1_Cu, nets["GND"], "GND plane")
    zone(board, pcbnew.In2_Cu, nets["+3V3"], "+3V3 pour")
    zone(board, pcbnew.B_Cu, nets["GND"], "GND pour bottom")
    return board


def fill_and_save(board: pcbnew.BOARD) -> pcbnew.BOARD:
    """Save, reload and fill. Filling a board built in memory misses NPTH hole
    knock-outs in KiCad 9.0.3, so zones are always filled on a reloaded board."""
    pcbnew.SaveBoard(str(PCB), board)
    board = pcbnew.LoadBoard(str(PCB))
    board.BuildConnectivity()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(PCB), board)
    return board


def route(jar: Path, passes: int, java: str) -> None:
    board = pcbnew.LoadBoard(str(PCB))  # reload so project net classes apply
    dsn = PCB.with_suffix(".dsn")
    ses = PCB.with_suffix(".ses")
    if not pcbnew.ExportSpecctraDSN(board, str(dsn)):
        raise SystemExit("DSN export failed")
    # In1 is a solid GND plane (reference for the top layer and the USB pair): no tracks.
    text = dsn.read_text(encoding="utf-8")
    text = re.sub(r"(\(layer In1\.Cu\s*\(type )signal", r"\1power", text)
    # In2 carries signals plus a +3V3 pour, and B.Cu carries signals plus a GND pour. Neither pour
    # is a routing target, so +3V3 is routed as 0.4 mm tracks and GND drops to In1 through vias.
    text = re.sub(r"\s*\(plane GND \(polygon B\.Cu[^)]*\)\)", "", text)
    text = re.sub(r"\s*\(plane \+3V3 \(polygon In2\.Cu[^)]*\)\)", "", text)
    dsn.write_text(text, encoding="utf-8")
    cmd = [java, "-jar", str(jar), "-de", str(dsn), "-do", str(ses), f"--router.max_passes={passes}",
           "--gui.enabled=false"]
    print("Running:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)
    if not pcbnew.ImportSpecctraSES(board, str(ses)):
        raise SystemExit("SES import failed")
    fill_and_save(board)
    dsn.unlink(missing_ok=True)
    ses.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--route", action="store_true", help="autoroute with Freerouting")
    parser.add_argument("--freerouting", type=Path, default=Path("/opt/fr/freerouting.jar"))
    parser.add_argument("--passes", type=int, default=300)
    parser.add_argument("--java", default="java", help="java executable (Freerouting needs Java 21+)")
    args = parser.parse_args()
    board = build()
    fill_and_save(board)
    print(f"Placed {len(design.PARTS)} parts + {len(layout.MOUNTING_HOLES)} holes on "
          f"{layout.BOARD_W:g} x {layout.BOARD_H:g} mm, {layout.LAYERS} layers -> {PCB.name}")
    if args.route:
        route(args.freerouting, args.passes, args.java)
        print("Routed and zones filled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
