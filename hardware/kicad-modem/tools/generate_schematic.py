#!/usr/bin/env python3
"""Generate the modem daughterboard v0.1 KiCad schematic and project-local libraries.

Inputs:  ``hardware/kicad-modem/design_modem_v01.py`` and the KiCad stock libraries
         (default /usr/share/kicad, tested with KiCad 7.0.11; output opens in 7, 8 and 9).
Outputs: ``sgm_modem.kicad_sch``, ``sgm_modem.kicad_pro``, ``sgm_modem.kicad_dru``,
         ``lib/sgm_modem.kicad_sym``, ``lib/SGMM.pretty/*``, ``sym-lib-table``, ``fp-lib-table``.

The sheet writer (pin stubs ending in labels or power symbols) is the carrier board's
``hardware/kicad/tools/generate_schematic.py``, reused unchanged by pointing it at this
design module. Two library items are generated here rather than copied from KiCad:

* ``EC200U`` symbol - pin numbers and names from the Quectel EC200U Series Hardware
  Design V1.0 pin table (only the pins this board uses, plus every GND pin, stacked).
* ``Quectel_EC200U_PROVISIONAL`` footprint - 80 LCC + 64 LGA pads on the 28.0 x 31.0 mm
  outline. PROVISIONAL: the pad geometry and which pad carries which number are
  placeholders; replace with Quectel's footprint file before any layout review.

Usage: python3 hardware/kicad-modem/tools/generate_schematic.py [--kicad-share DIR] [--check]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

MODEM_DIR = Path(__file__).resolve().parents[1]
CARRIER_TOOLS = MODEM_DIR.parent / "kicad" / "tools"
sys.path.insert(0, str(MODEM_DIR))
sys.path.insert(0, str(CARRIER_TOOLS))
import design_modem_v01 as design  # noqa: E402
import generate_schematic as gen  # noqa: E402  (carrier generator; imports design_v02 itself)

PROJECT = "sgm_modem"
SYMBOL_LIB = MODEM_DIR / "lib" / "sgm_modem.kicad_sym"
FP_NAME = "Quectel_EC200U_PROVISIONAL"

# Point the shared sheet writer at this board.
gen.design = design
gen.PROJECT = PROJECT
gen.KICAD_DIR = MODEM_DIR
gen.LOCAL_LIB = SYMBOL_LIB
gen.POWER_SYMBOLS = {"GND"}

SYMBOL_SOURCES = {
    "R": "Device", "C": "Device", "C_Polarized": "Device", "LED": "Device", "D_TVS": "Device",
    "Q_NMOS_GSD": "Device", "MMBT3904": "Transistor_BJT",
    "ESD224DQA": "Power_Protection", "SIM_Card": "Connector", "Conn_Coaxial": "Connector",
    "Conn_01x02": "Connector_Generic", "Conn_01x08": "Connector_Generic",
    "SolderJumper_2_Open": "Jumper", "TestPoint": "Connector",
    "GND": "power", "PWR_FLAG": "power",
}
FOOTPRINT_SOURCES = {
    "PinSocket_1x08_P2.54mm_Vertical": "Connector_PinSocket_2.54mm",
    "PinHeader_1x02_P2.54mm_Vertical": "Connector_PinHeader_2.54mm",
    "CP_EIA-3528-21_Kemet-B": "Capacitor_Tantalum_SMD",
    "C_0402_1005Metric": "Capacitor_SMD", "R_0402_1005Metric": "Resistor_SMD",
    "D_SMB": "Diode_SMD", "SOT-23": "Package_TO_SOT_SMD", "LED_0603_1608Metric": "LED_SMD",
    "USON-10_2.5x1.0mm_P0.5mm": "Package_SON",
    "microSIM_JAE_SF53S006VCBR2000": "Connector_Card",
    "U.FL_Hirose_U.FL-R-SMT-1_Vertical": "Connector_Coaxial",
    "SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm": "Jumper",
    "TestPoint_Pad_D1.0mm": "TestPoint",
    "MountingHole_2.7mm_M2.5": "MountingHole",
}

# --------------------------------------------------------------------------- EC200U symbol
# (pin number, name, electrical type, side, y) ; side L/R; y in symbol units (mm, up positive)
EC200U_PINS = [
    ("57", "VBAT_RF", "power_in", "L", 25.4), ("58", "VBAT_RF", "power_in", "L", 22.86),
    ("59", "VBAT_BB", "power_in", "L", 20.32), ("60", "VBAT_BB", "power_in", "L", 17.78),
    ("21", "PWRKEY", "input", "L", 12.7), ("20", "RESET_N", "input", "L", 10.16),
    ("68", "MAIN_RXD", "input", "L", 5.08), ("67", "MAIN_TXD", "output", "L", 2.54),
    ("61", "STATUS", "output", "L", 0.0), ("6", "NET_STATUS", "output", "L", -5.08),
    ("5", "NET_MODE", "output", "L", -7.62), ("11", "DBG_RXD", "input", "L", -12.7),
    ("12", "DBG_TXD", "output", "L", -15.24), ("115", "USB_BOOT", "input", "L", -20.32),
    ("7", "VDD_EXT", "power_out", "R", 25.4), ("14", "USIM_VDD", "power_out", "R", 20.32),
    ("17", "USIM_RST", "output", "R", 17.78), ("16", "USIM_CLK", "output", "R", 15.24),
    ("15", "USIM_DATA", "bidirectional", "R", 12.7), ("13", "USIM_DET", "input", "R", 10.16),
    ("10", "USIM_GND", "power_in", "R", 7.62), ("49", "ANT_MAIN", "bidirectional", "R", 0.0),
    ("71", "USB_VBUS", "input", "R", -10.16), ("69", "USB_DP", "bidirectional", "R", -12.7),
    ("70", "USB_DM", "bidirectional", "R", -15.24),
]
FONT = "(effects (font (size 1.27 1.27)))"


def ec200u_symbol() -> str:
    pins = []
    for number, name, etype, side, y in EC200U_PINS:
        x, angle = (-22.86, 0) if side == "L" else (22.86, 180)
        pins.append(f'      (pin {etype} line (at {x} {y} {angle}) (length 5.08)\n'
                    f'        (name "{name}" {FONT})\n        (number "{number}" {FONT})\n      )')
    for i, number in enumerate(design.EC200U_GND):
        hide = " hide" if i else ""
        pins.append(f'      (pin power_in line (at 0 -33.02 90) (length 5.08){hide}\n'
                    f'        (name "GND" {FONT})\n        (number "{number}" {FONT})\n      )')
    return (
        '(symbol "EC200U" (in_bom yes) (on_board yes)\n'
        f'    (property "Reference" "U" (at -17.78 29.21 0) (effects (font (size 1.27 1.27)) (justify left)))\n'
        f'    (property "Value" "EC200U" (at 2.54 29.21 0) (effects (font (size 1.27 1.27)) (justify left)))\n'
        f'    (property "Footprint" "{design.LIB}:{FP_NAME}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
        '    (property "Datasheet" "Quectel EC200U Series Hardware Design V1.0" (at 0 0 0) '
        '(effects (font (size 1.27 1.27)) hide))\n'
        '    (property "ki_description" "Quectel EC200U LTE Cat 1 module (subset of pins used by this board)" '
        '(at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
        '    (symbol "EC200U_0_1"\n'
        '      (rectangle (start -17.78 27.94) (end 17.78 -27.94) (stroke (width 0.254) (type default)) '
        '(fill (type background)))\n    )\n'
        '    (symbol "EC200U_1_1"\n' + "\n".join(pins) + "\n    )\n  )")


def sim_with_shield(stock: str) -> str:
    """Stock SIM_Card plus a shield pin 'SH' stacked on GND, so the holder's shell pads get GND."""
    body = stock.replace('(symbol "SIM_Card"', '(symbol "SIM_Card_SH"', 1)
    body = re.sub(r'\(symbol "SIM_Card_(\d+_\d+)"', r'(symbol "SIM_Card_SH_\1"', body)
    gnd = re.search(r'\(pin power_in line (\(at [^)]*\)) (\(length [^)]*\))[^\n]*\n?\s*\(name "GND"', body)
    if not gnd:
        raise SystemExit("SIM_Card: GND pin not found")
    shield = (f'(pin passive line {gnd.group(1)} {gnd.group(2)} hide\n'
              f'        (name "SH" {FONT})\n        (number "SH" {FONT})\n      )\n      ')
    return body[:gnd.start()] + shield + body[gnd.start():]


def library_symbols(share: Path) -> dict[str, str]:
    stock = {}
    for name, lib in SYMBOL_SOURCES.items():
        if name == "SIM_Card":
            continue
        stock[name] = gen.read_symbol(share, lib, name)
    stock["SIM_Card_SH"] = sim_with_shield(gen.read_symbol(share, "Connector", "SIM_Card")) \
        if (share / "symbols" / "Connector.kicad_sym").exists() else gen.read_symbol(share, "Connector", "SIM_Card_SH")
    stock["EC200U"] = ec200u_symbol()
    return stock


# --------------------------------------------------------------------------- provisional footprint
def lcc_pad(n: int) -> tuple[float, float, float, float]:
    """Pad n (1..80) centre and size. Pin 1 top-left, counter-clockwise (Quectel convention).
    31 mm sides (top/bottom) carry 20 pads; 28 mm sides carry 13 + 7 pads, all at 1.3 mm pitch."""
    ys = [-12.35 + 1.3 * i for i in range(13)] + [4.55 + 1.3 * i for i in range(7)]
    xs = [-12.35 + 1.3 * i for i in range(20)]
    i, side = (n - 1) % 20, (n - 1) // 20
    if side == 0:
        return -15.5, ys[i], 2.0, 0.8
    if side == 1:
        return xs[i], 14.15, 0.8, 2.0
    if side == 2:
        return 15.5, ys[::-1][i], 2.0, 0.8
    return xs[::-1][i], -14.15, 0.8, 2.0


def lga_pads() -> list[tuple[int, float, float]]:
    """64 LGA pads, 8 x 8 grid at 2.4 mm pitch, numbered 81..144 row by row (placeholder grid)."""
    return [(81 + 8 * r + c, -8.4 + 2.4 * c, -8.4 + 2.4 * r) for r in range(8) for c in range(8)]


def ec200u_footprint() -> str:
    lines = [f'(footprint "{FP_NAME}" (version 20221018) (generator pcbnew)',
             '  (layer "F.Cu")',
             '  (descr "PROVISIONAL Quectel EC200U LCC+LGA footprint built from partial dimensions in the '
             'Hardware Design V1.0. Pad geometry and pad numbering are placeholders - replace with the '
             'Quectel EC200U Series Footprint & Part file before layout review or fabrication.")',
             '  (tags "Quectel EC200U LTE PROVISIONAL")',
             '  (attr smd)',
             '  (fp_text reference "REF**" (at 0 -16.6) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
             f'  (fp_text value "{FP_NAME}" (at 0 16.8) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
             '  (fp_text user "PROVISIONAL FOOTPRINT" (at 0 -2) (layer "F.Fab") (effects (font (size 1.5 1.5) (thickness 0.2))))',
             '  (fp_text user "replace with Quectel file" (at 0 1) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))']
    w, h = 15.5, 14.0
    for (x1, y1, x2, y2) in ((-w, -h, w, -h), (w, -h, w, h), (w, h, -w, h), (-w, h, -w, -h)):
        lines.append(f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0.1) (type solid)) (layer "F.Fab"))')
    sw, sh = 16.7, 15.35
    for (x1, y1, x2, y2) in ((-sw + 1.5, -sh, sw, -sh), (sw, -sh, sw, sh), (sw, sh, -sw, sh), (-sw, sh, -sw, -sh + 1.5)):
        lines.append(f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))')
    lines.append(f'  (fp_circle (center {-sw - 0.8} {-sh - 0.8}) (end {-sw - 0.4} {-sh - 0.8}) '
                 '(stroke (width 0.2) (type solid)) (fill solid) (layer "F.SilkS"))')
    cw, ch = 17.0, 15.65
    lines.append(f'  (fp_rect (start {-cw} {-ch}) (end {cw} {ch}) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))')
    for n in range(1, 81):
        x, y, sx, sy = lcc_pad(n)
        lines.append(f'  (pad "{n}" smd roundrect (at {x:.2f} {y:.2f}) (size {sx} {sy}) '
                     '(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.15))')
    for n, x, y in lga_pads():
        lines.append(f'  (pad "{n}" smd rect (at {x:.2f} {y:.2f}) (size 1.0 1.0) (layers "F.Cu" "F.Paste" "F.Mask"))')
    lines.append(")")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- schematic
BLOCK_TITLES = {
    "carrier": ("1. Carrier interface J1 (= carrier J6) and VBAT reservoir", (25.4, 30.48)),
    "module": ("2. Quectel EC200U-EU LTE Cat 1 module (footprint PROVISIONAL)", (203.2, 76.2)),
    "control": ("3. PWRKEY / RESET_N open-collector drivers (VBAT domain)", (60.96, 99.06)),
    "shift": ("4. 3.3 V <-> 1.8 V level shifting (UART + STATUS)", (60.96, 147.32)),
    "led": ("5. Network status LED (NET_STATUS)", (60.96, 198.12)),
    "sim": ("6. micro-SIM: 0R series, 33 pF, pull-up, low-capacitance ESD", (309.88, 30.48)),
    "rf": ("7. LTE main antenna: pi network + u.FL (50 ohm)", (304.8, 134.62)),
    "test": ("8. USB download jumper and test pads (1.8 V debug UART)", (233.68, 200.66)),
}
NOTES = [
    ("Power: MODEM_VIN (3.8 V nom, 3.3-4.3 V, up to 2 A bursts) comes from carrier J7 through J6 pin 1 "
     "(or J2 if fitted). Never from +3V3.", (25.4, 88.9)),
    ("Level shifting: MCU-side pins 3, 4 and 7 have no pull-up on this board (J6 carries no 3V3); "
     "firmware enables the ESP32 internal pull-ups on MODEM_RXD and MODEM_STATUS.", (60.96, 190.5)),
]


def text_position(symbol: str, x: float, y: float, i: int) -> tuple[float, float]:
    if symbol == "EC200U":
        return x - 17.78, y - 33.02 + 2.54 * i
    if symbol == "SolderJumper_2_Open":
        return x - 3.81, y - 5.08 + 2.54 * i
    if symbol in ("Conn_Coaxial", "SIM_Card_SH", "ESD224DQA"):
        return x + 5.08, y - 12.7 + 2.54 * i
    return _carrier_text_position(symbol, x, y, i)


_carrier_text_position = gen.text_position
gen.text_position = text_position


def build_schematic(share: Path) -> tuple[str, dict[str, str]]:
    root = gen.uid("modem-root")
    sheet = gen.Sheet(root)
    symbols = library_symbols(share)
    for part in design.PARTS:
        pins = gen.pin_table(symbols[part.symbol])
        extra = set(part.pins) - set(pins)
        if extra:
            raise SystemExit(f"{part.ref}: design lists pins not on symbol {part.symbol}: {sorted(extra)}")
        sheet.part(part, pins)
    for net, at in design.PWR_FLAGS.items():
        sheet.flag(net, at)
    for block, (title, at) in BLOCK_TITLES.items():
        sheet.text(title, at, block, 1.778)
    for i, (body, at) in enumerate(NOTES):
        sheet.text(body, at, f"note{i}")
    used = {p.symbol for p in design.PARTS} | {"GND", "PWR_FLAG"}
    symbols = {k: v for k, v in sorted(symbols.items()) if k in used}
    lib_section = "\n".join(
        "    " + body.replace('(symbol "%s"' % name, '(symbol "%s:%s"' % (design.LIB, name), 1).replace("\n", "\n    ")
        for name, body in symbols.items())
    n = len(design.COMMENTS)
    comments = "\n".join(f'    (comment {n - i} "{c}")' for i, c in enumerate(design.COMMENTS))
    text = (
        f"(kicad_sch (version 20230121) (generator eeschema)\n\n  (uuid {root})\n\n  (paper \"A3\")\n\n"
        f"  (title_block\n    (title \"{design.TITLE}\")\n    (date \"2026-10-26\")\n"
        f"    (rev \"{design.REVISION}\")\n    (company \"Smart Gas Meter IoT - lab prototype\")\n{comments}\n  )\n\n"
        f"  (lib_symbols\n{lib_section}\n  )\n\n" + "\n\n".join(sheet.items) +
        "\n\n  (sheet_instances\n    (path \"/\" (page \"1\"))\n  )\n)\n")
    # the shared writer stamps instances with the root uuid passed in; keep project name consistent
    return text, symbols


def write_libraries(share: Path, symbols: dict[str, str], models_3d: Path | None) -> None:
    lib_dir = MODEM_DIR / "lib"
    lib_dir.mkdir(exist_ok=True)
    SYMBOL_LIB.write_text("(kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor)\n"
                          + "\n".join(symbols.values()) + "\n)\n", encoding="utf-8")
    pretty = lib_dir / f"{design.LIB}.pretty"
    pretty.mkdir(exist_ok=True)
    used = {p.footprint for p in design.PARTS} | set(design.BOARD_ONLY_FOOTPRINTS)
    for stale in pretty.glob("*.kicad_mod"):
        if stale.stem not in used:
            stale.unlink()
    for fp in sorted(used - {FP_NAME}):
        src = share / "footprints" / f"{FOOTPRINT_SOURCES[fp]}.pretty" / f"{fp}.kicad_mod"
        if src.exists():
            shutil.copyfile(src, pretty / src.name)
        elif not (pretty / src.name).exists():
            raise SystemExit(f"footprint {fp} not found in {src.parent} or {pretty}")
        try:
            gen.vendor_3d_model(pretty / src.name, models_3d)
        except SystemExit:
            # No STEP model available (e.g. the JAE micro-SIM): keep the footprint without a 3D model.
            mod = pretty / src.name
            text = mod.read_text(encoding="utf-8")
            start = text.find("(model ")
            mod.write_text(text[:start].rstrip() + "\n)\n" if start > 0 else text, encoding="utf-8")
    (pretty / f"{FP_NAME}.kicad_mod").write_text(ec200u_footprint(), encoding="utf-8")
    (MODEM_DIR / "sym-lib-table").write_text(
        f'(sym_lib_table\n  (version 7)\n  (lib (name "{design.LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/lib/sgm_modem.kicad_sym")'
        '(options "")(descr "Modem daughterboard symbols: KiCad 7.0.11 stock copies + generated EC200U"))\n)\n',
        encoding="utf-8")
    (MODEM_DIR / "fp-lib-table").write_text(
        f'(fp_lib_table\n  (version 7)\n  (lib (name "{design.LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/lib/{design.LIB}.pretty")'
        '(options "")(descr "Modem daughterboard footprints: KiCad 7.0.11 stock copies + PROVISIONAL EC200U"))\n)\n',
        encoding="utf-8")


def project_file() -> str:
    import pcb_layout_modem_v01 as layout
    nc = gen._netclass
    data = {
        "board": {"design_settings": {"rules": dict(layout.BOARD_RULES)}},
        "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 3},
        "net_settings": {
            "classes": [
                nc("Default", 0.2, 0.15, 0.5, 0.25, 2147483647),
                nc("Power", 0.5, 0.2, 0.8, 0.4, 0),
                # 50 ohm grounded coplanar line on F.Cu over the In1 GND plane (JLC 4-layer, 0.2 mm prepreg):
                # width / gap to be confirmed with the fabricator's impedance calculator.
                nc("RF", 0.35, 0.25, 0.6, 0.3, 1),
                nc("USB", 0.2, 0.15, 0.5, 0.25, 2, dp_width=0.2, dp_gap=0.15),
            ],
            "meta": {"version": 4},
            "net_colors": None,
            "netclass_assignments": None,
            "netclass_patterns": [{"netclass": "Power", "pattern": p} for p in ("GND", "/MODEM_VIN")]
            + [{"netclass": "RF", "pattern": "/RF_*"}, {"netclass": "USB", "pattern": "/USB_D*"}],
        },
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [[gen.uid("modem-root"), ""]],
        "text_variables": {},
    }
    return json.dumps(data, indent=2) + "\n"


DESIGN_RULES = """(version 1)
# Project design rules for the modem daughterboard v0.1 (generated by tools/generate_schematic.py).
# Board-setup constraints in the .kicad_pcb apply; no custom rules yet.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--kicad-share", type=Path, default=Path("/usr/share/kicad"))
    parser.add_argument("--kicad-3d", type=Path, default=None,
                        help="KiCad 3dmodels directory (kicad-packages3D) to vendor STEP models from")
    parser.add_argument("--check", action="store_true", help="fail if the committed schematic is out of date")
    args = parser.parse_args()
    text, symbols = build_schematic(args.kicad_share)
    sch = MODEM_DIR / f"{PROJECT}.kicad_sch"
    if args.check:
        if sch.read_text(encoding="utf-8") != text:
            print("Committed modem schematic is out of date with design_modem_v01.py; rerun the generator.")
            return 1
        print("Committed modem schematic matches design_modem_v01.py.")
        return 0
    sch.write_text(text, encoding="utf-8")
    models = args.kicad_3d or args.kicad_share / "3dmodels"
    write_libraries(args.kicad_share, symbols, models if models.exists() else None)
    (MODEM_DIR / f"{PROJECT}.kicad_pro").write_text(project_file(), encoding="utf-8")
    (MODEM_DIR / f"{PROJECT}.kicad_dru").write_text(DESIGN_RULES, encoding="utf-8")
    print(f"Wrote {sch.name}: {len(design.PARTS)} parts, {len(design.expected_nets())} nets, "
          f"{len(symbols)} library symbols; provisional EC200U footprint with 144 pads.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
