#!/usr/bin/env python3
"""Generate the v0.2 native KiCad schematic and project-local libraries.

Inputs:  ``hardware/kicad/design_v02.py`` (parts, values, pin -> net map) and
         the KiCad stock symbol/footprint libraries (default: /usr/share/kicad,
         tested with KiCad 7.0.11; output opens in KiCad 7, 8 and 9).
Outputs: ``smart_gas_meter_iot.kicad_sch``, ``smart_gas_meter_iot.kicad_pro``,
         ``lib/smart_gas_meter.kicad_sym``, ``lib/SGM.pretty/*``,
         ``sym-lib-table`` and ``fp-lib-table``.

Connectivity is expressed with a short wire stub on every pin that ends in a
net label or power symbol, so every connection is explicit and reviewable and
the exported netlist can be compared one-to-one with ``design_v02.py``.

Usage: python3 hardware/kicad/tools/generate_schematic.py [--kicad-share DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import uuid
from pathlib import Path

KICAD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KICAD_DIR))
import design_v02 as design  # noqa: E402

PROJECT = "smart_gas_meter_iot"
GRID = 1.27
STUB = 2.54

# Stock library that provides each symbol / footprint used by the design.
SYMBOL_SOURCES = {
    "USB_C_Receptacle_USB2.0_16P": "Connector",
    "R": "Device", "C": "Device", "L": "Device", "LED": "Device",
    "Polyfuse": "Device", "D_TVS": "Device",
    "USBLC6-2SC6": "Power_Protection",
    "AP63203WU": "Regulator_Switching",
    "ESP32-S3-WROOM-1": "RF_Module",
    "SW_Push": "Switch",
    "Conn_01x02": "Connector_Generic", "Conn_01x03": "Connector_Generic",
    "Conn_01x04": "Connector_Generic", "Conn_01x08": "Connector_Generic",
    "TestPoint": "Connector",
    "GND": "power", "+3V3": "power", "+5V": "power", "PWR_FLAG": "power",
}
FOOTPRINT_SOURCES = {
    "USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal": "Connector_USB",
    "R_0603_1608Metric": "Resistor_SMD",
    "C_0603_1608Metric": "Capacitor_SMD", "C_0805_2012Metric": "Capacitor_SMD",
    "C_1206_3216Metric": "Capacitor_SMD",
    "Fuse_1206_3216Metric": "Fuse",
    "D_SMA": "Diode_SMD",
    "SOT-23-6": "Package_TO_SOT_SMD", "TSOT-23-6": "Package_TO_SOT_SMD",
    "L_Sunlord_SWPA4030S": "Inductor_SMD",
    "ESP32-S3-WROOM-1": "RF_Module",
    "SW_SPST_TL3342": "Button_Switch_SMD",
    "LED_0603_1608Metric": "LED_SMD",
    "PinHeader_1x02_P2.54mm_Vertical": "Connector_PinHeader_2.54mm",
    "PinHeader_1x03_P2.54mm_Vertical": "Connector_PinHeader_2.54mm",
    "PinHeader_1x04_P2.54mm_Vertical": "Connector_PinHeader_2.54mm",
    "PinHeader_1x08_P2.54mm_Vertical": "Connector_PinHeader_2.54mm",
    "TestPoint_Pad_D1.5mm": "TestPoint",
    "MountingHole_3.2mm_M3": "MountingHole",
}
POWER_SYMBOLS = {"GND", "+3V3", "+5V"}

_ns = uuid.UUID("6f1d6a52-9d0e-4c43-9a51-5a9b0c8e2f10")


def uid(*parts: object) -> str:
    """Deterministic UUID so regenerating produces a stable, diffable file."""
    return str(uuid.uuid5(_ns, "/".join(map(str, parts))))


# --------------------------------------------------------------------------- S-expression helpers
def balanced(text: str, start: int) -> str:
    depth, quoted, escaped = 0, False, False
    for i in range(start, len(text)):
        ch = text[i]
        if quoted:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
            continue
        if ch == '"':
            quoted = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise ValueError("unbalanced S-expression")


LOCAL_LIB = KICAD_DIR / "lib" / "smart_gas_meter.kicad_sym"


def read_symbol(share: Path, lib: str, name: str) -> str:
    source = share / "symbols" / f"{lib}.kicad_sym"
    if not source.exists():
        # No stock libraries (e.g. CI without KiCad): use the committed, already
        # flattened project-local copies so regeneration stays reproducible.
        source = LOCAL_LIB
    text = source.read_text(encoding="utf-8")
    match = re.search(r'\(symbol "%s"' % re.escape(name), text)
    if not match:
        raise KeyError(f"{lib}:{name} not found")
    body = balanced(text, match.start())
    parent = re.search(r'\(extends "([^"]+)"\)', body)
    if not parent:
        return body
    # Flatten: take the parent's graphics/pins, keep the child's properties.
    base = read_symbol(share, lib, parent.group(1))
    base = base.replace(f'(symbol "{parent.group(1)}"', f'(symbol "{name}"', 1)
    base = re.sub(r'\(symbol "%s_(\d+_\d+)"' % re.escape(parent.group(1)),
                  lambda m: f'(symbol "{name}_{m.group(1)}"', base)
    for key, value in re.findall(r'\(property "([^"]+)" "((?:[^"\\]|\\.)*)"', body):
        base = re.sub(r'(\(property "%s" )"(?:[^"\\]|\\.)*"' % re.escape(key),
                      lambda m: m.group(1) + '"' + value.replace("\\", "\\\\") + '"', base, count=1)
    return base


PIN_RE = re.compile(r'\(pin (\w+) (\w+) \(at ([-\d.]+) ([-\d.]+) (\d+)\).*?\(number "([^"]+)"', re.S)


def pin_table(symbol: str) -> dict[str, tuple[float, float, int, str]]:
    return {m.group(6): (float(m.group(3)), float(m.group(4)), int(m.group(5)), m.group(1))
            for m in PIN_RE.finditer(symbol)}


# --------------------------------------------------------------------------- geometry
OUTWARD = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}  # screen direction away from the body


def snap(v: float) -> float:
    return round(round(v / GRID) * GRID, 2)


def fmt(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def text_position(symbol: str, x: float, y: float, i: int) -> tuple[float, float]:
    """Reference (i=0) / Value (i=1) placement that avoids pins, stubs and labels."""
    if symbol == "ESP32-S3-WROOM-1":
        return x + 5.08, y - 35.56 + 2.54 * i  # beside the +3V3 symbol above the module
    if symbol == "USB_C_Receptacle_USB2.0_16P":
        return x - 15.24, y - 26.67 + 2.54 * i
    if symbol in ("AP63203WU", "USBLC6-2SC6"):
        return x + 3.81, y + 10.16 + 2.54 * i  # below the right-hand pin labels
    if symbol in ("D_TVS", "LED", "SW_Push"):
        return x - 3.81, y - 7.62 + 2.54 * i  # horizontal parts: above the body
    return x + 3.81, y - 1.27 + 2.54 * i


EFFECTS = "(effects (font (size 1.27 1.27)))"
EFFECTS_HIDE = "(effects (font (size 1.27 1.27)) hide)"


class Sheet:
    def __init__(self, root: str) -> None:
        self.root = root
        self.items: list[str] = []
        self.pwr = 0

    def wire(self, a: tuple[float, float], b: tuple[float, float], key: str) -> None:
        self.items.append(
            f"  (wire (pts (xy {fmt(a[0])} {fmt(a[1])}) (xy {fmt(b[0])} {fmt(b[1])}))\n"
            f"    (stroke (width 0) (type default))\n    (uuid {uid('wire', key)})\n  )")

    def label(self, net: str, at: tuple[float, float], direction: tuple[int, int], key: str) -> None:
        angle, justify = {(1, 0): (0, "left"), (-1, 0): (180, "right"),
                          (0, -1): (90, "left"), (0, 1): (270, "right")}[direction]
        self.items.append(
            f'  (label "{net}" (at {fmt(at[0])} {fmt(at[1])} {angle}) (fields_autoplaced)\n'
            f"    (effects (font (size 1.27 1.27)) (justify {justify} bottom))\n"
            f"    (uuid {uid('label', key)})\n  )")

    def no_connect(self, at: tuple[float, float], key: str) -> None:
        self.items.append(f"  (no_connect (at {fmt(at[0])} {fmt(at[1])}) (uuid {uid('nc', key)}))")

    def power(self, net: str, at: tuple[float, float], direction: tuple[int, int], key: str,
              lib_name: str | None = None) -> None:
        name = lib_name or net
        if name == "GND":
            rot = {(0, 1): 0, (0, -1): 180, (1, 0): 90, (-1, 0): 270}[direction]
        else:  # +3V3/+5V/PWR_FLAG are drawn above their pin
            rot = {(0, -1): 0, (0, 1): 180, (-1, 0): 90, (1, 0): 270}[direction]
        self.pwr += 1
        ref = f"#{'FLG' if name == 'PWR_FLAG' else 'PWR'}{self.pwr:03d}"
        value = net if name != "PWR_FLAG" else "PWR_FLAG"
        x, y = at
        self.items.append(
            f'  (symbol (lib_id "{design.LIB}:{name}") (at {fmt(x)} {fmt(y)} {rot}) (unit 1)\n'
            f"    (in_bom no) (on_board yes) (dnp no) (fields_autoplaced)\n"
            f"    (uuid {uid('pwr', key)})\n"
            f'    (property "Reference" "{ref}" (at {fmt(x)} {fmt(y + 6.35)} 0)\n      {EFFECTS_HIDE}\n    )\n'
            f'    (property "Value" "{value}" (at {fmt(x)} {fmt(y - 3.81 if name != "GND" else y + 3.81)} 0)\n      {EFFECTS}\n    )\n'
            f'    (property "Footprint" "" (at {fmt(x)} {fmt(y)} 0)\n      {EFFECTS_HIDE}\n    )\n'
            f'    (property "Datasheet" "" (at {fmt(x)} {fmt(y)} 0)\n      {EFFECTS_HIDE}\n    )\n'
            f'    (pin "1" (uuid {uid("pwrpin", key)}))\n'
            f'    (instances\n      (project "{PROJECT}"\n        (path "/{self.root}" (reference "{ref}") (unit 1))\n      )\n    )\n  )')

    def endpoint(self, net: str, at: tuple[float, float], direction: tuple[int, int], key: str) -> None:
        if net in POWER_SYMBOLS:
            self.power(net, at, direction, key)
        else:
            self.label(net, at, direction, key)

    def part(self, part: design.Part, pins: dict[str, tuple[float, float, int, str]]) -> None:
        x, y = part.at
        props = {
            "Reference": part.ref, "Value": part.value,
            "Footprint": f"{design.LIB}:{part.footprint}", "Datasheet": "~",
            "MPN": part.mpn, "Design_Note": part.note or "-", "Block": part.block,
            **part.fields,
        }
        lines = [f'  (symbol (lib_id "{design.LIB}:{part.symbol}") (at {fmt(x)} {fmt(y)} 0) (unit 1)',
                 f"    (in_bom yes) (on_board yes) (dnp {'yes' if part.dnp else 'no'})",
                 f"    (uuid {uid('sym', part.ref)})"]
        for i, (key, value) in enumerate(props.items()):
            hidden = key not in ("Reference", "Value")
            px, py = text_position(part.symbol, x, y, i) if not hidden else (x, y)
            value = value.replace('"', "'")
            lines.append(f'    (property "{key}" "{value}" (at {fmt(px)} {fmt(py)} 0)\n'
                         f"      {EFFECTS_HIDE if hidden else '(effects (font (size 1.27 1.27)) (justify left))'}\n    )")
        for number in pins:
            lines.append(f'    (pin "{number}" (uuid {uid("pin", part.ref, number)}))')
        lines.append(f'    (instances\n      (project "{PROJECT}"\n'
                     f'        (path "/{self.root}" (reference "{part.ref}") (unit 1))\n      )\n    )\n  )')
        self.items.append("\n".join(lines))

        # Connections: one stub per distinct pin location (stacked pins share one).
        done: dict[tuple[float, float], str] = {}
        power_ends: list[tuple[float, float]] = []
        for number, (px, py, angle, _etype) in pins.items():
            net = part.pins.get(number)
            if net is None:
                raise SystemExit(f"{part.ref} pin {number} has no entry in design_v02.py")
            tip = (snap(x + px), snap(y - py))
            if tip in done:
                if done[tip] != net:
                    raise SystemExit(f"{part.ref}: stacked pins at {tip} assigned to {done[tip]} and {net}")
                continue
            done[tip] = net
            key = f"{part.ref}.{number}"
            if net == design.NC:
                self.no_connect(tip, key)
                continue
            dx, dy = OUTWARD[angle]
            length = STUB
            if net in POWER_SYMBOLS and part.symbol in ("Conn_01x03", "Conn_01x04", "Conn_01x08"):
                length = 17.78  # keep rail symbols clear of neighbouring pin labels
            end = (snap(tip[0] + dx * length), snap(tip[1] + dy * length))
            if net in POWER_SYMBOLS:
                # Stagger neighbouring power symbols on one part so their text does not overlap.
                while any(abs(end[0] - a) + abs(end[1] - b) < 6.0 for a, b in power_ends):
                    length += 5.08
                    end = (snap(tip[0] + dx * length), snap(tip[1] + dy * length))
                power_ends.append(end)
            self.wire(tip, end, key)
            self.endpoint(net, end, (dx, dy), key)

    def flag(self, net: str, at: tuple[float, float]) -> None:
        x, y = at
        self.power(net, (x, y), (0, -1), f"flag.{net}", lib_name="PWR_FLAG")
        self.wire((x, y), (x, snap(y + STUB)), f"flag.{net}")
        self.endpoint(net, (x, snap(y + STUB)), (0, 1), f"flagend.{net}")

    def text(self, body: str, at: tuple[float, float], key: str, size: float = 1.27) -> None:
        body = body.replace('"', "'").replace("\n", "\\n")
        self.items.append(f'  (text "{body}" (at {fmt(at[0])} {fmt(at[1])} 0)\n'
                          f"    (effects (font (size {size} {size})) (justify left bottom))\n"
                          f"    (uuid {uid('text', key)})\n  )")


BLOCK_TITLES = {
    "usb": ("1. USB-C input, PTC fuse, TVS, USB ESD", (25.4, 20.32)),
    "power": ("2. 3V3 buck regulator (AP63203)", (119.38, 20.32)),
    "mcu": ("3. ESP32-S3-WROOM-1-N8, EN RC, RESET/BOOT", (101.6, 106.68)),
    "pulse": ("4. Synthetic pulse input - 3.3V LAB SIGNAL ONLY", (271.78, 20.32)),
    "status": ("5. Status LED", (271.78, 101.6)),
    "tamper": ("6. Enclosure tamper switch (advisory only)", (271.78, 147.32)),
    "io": ("7. I2C expansion and debug UART", (157.48, 233.68)),
    "modem": ("8. Modem daughterboard - MODEM_VIN separate, never +3V3", (25.4, 210.82)),
    "test": ("9. Test points", (25.4, 144.78)),
}
NOTES = [
    ("Power path: USB_VBUS -> F1 (PTC) -> +5V -> U3 AP63203 -> L1 -> +3V3. "
     "PWR_FLAGs mark rails fed through passives for ERC.", (119.38, 88.9)),
]


def build_schematic(share: Path) -> tuple[str, dict[str, str]]:
    root = uid("root")
    sheet = Sheet(root)
    needed = {p.symbol for p in design.PARTS} | POWER_SYMBOLS | {"PWR_FLAG"}
    symbols = {name: read_symbol(share, SYMBOL_SOURCES[name], name) for name in sorted(needed)}

    for part in design.PARTS:
        pins = pin_table(symbols[part.symbol])
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

    lib_section = "\n".join(
        "    " + body.replace('(symbol "%s"' % name, '(symbol "%s:%s"' % (design.LIB, name), 1).replace("\n", "\n    ")
        for name, body in symbols.items())
    # KiCad draws comment 4 at the top of the title block; keep reading order top-down.
    n = len(design.COMMENTS)
    comments = "\n".join(f'    (comment {n - i} "{c}")' for i, c in enumerate(design.COMMENTS))
    text = (
        f"(kicad_sch (version 20230121) (generator eeschema)\n\n  (uuid {root})\n\n  (paper \"A3\")\n\n"
        f"  (title_block\n    (title \"{design.TITLE}\")\n    (date \"2026-10-24\")\n"
        f"    (rev \"{design.REVISION}\")\n    (company \"Smart Gas Meter IoT - lab prototype\")\n{comments}\n  )\n\n"
        f"  (lib_symbols\n{lib_section}\n  )\n\n" + "\n\n".join(sheet.items) +
        f"\n\n  (sheet_instances\n    (path \"/\" (page \"1\"))\n  )\n)\n")
    return text, symbols


MODEL_RE = re.compile(r'\(model\s+"?\$\{[A-Z0-9_]+\}/([^/"]+)\.3dshapes/([^"\s]+)\.(?:wrl|step)"?')


def vendor_3d_model(footprint: Path, models_3d: Path | None) -> None:
    """Point a footprint at a project-local STEP model, copying it in when available."""
    text = footprint.read_text(encoding="utf-8")
    match = MODEL_RE.search(text)
    if not match:
        return
    lib, name = match.groups()
    local = KICAD_DIR / "lib" / "3d" / f"{name}.step"
    local.parent.mkdir(exist_ok=True)
    if models_3d is not None:
        source = models_3d / f"{lib}.3dshapes" / f"{name}.step"
        if source.exists():
            shutil.copyfile(source, local)
    if not local.exists():
        raise SystemExit(f"3D model {name}.step not found; pass --kicad-3d with the KiCad 3dmodels dir")
    text = MODEL_RE.sub(f'(model "${{KIPRJMOD}}/lib/3d/{name}.step"', text, count=1)
    footprint.write_text(text, encoding="utf-8")


def write_libraries(share: Path, symbols: dict[str, str], models_3d: Path | None = None) -> None:
    lib_dir = KICAD_DIR / "lib"
    lib_dir.mkdir(exist_ok=True)
    body = "\n".join(symbols.values())  # verbatim, so regeneration from this file is byte-identical
    (lib_dir / "smart_gas_meter.kicad_sym").write_text(
        f"(kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor)\n{body}\n)\n", encoding="utf-8")
    pretty = lib_dir / f"{design.LIB}.pretty"
    pretty.mkdir(exist_ok=True)
    used = {p.footprint for p in design.PARTS} | set(design.BOARD_ONLY_FOOTPRINTS)
    for stale in pretty.glob("*.kicad_mod"):
        if stale.stem not in used:
            stale.unlink()
    for fp in sorted(used):
        src = share / "footprints" / f"{FOOTPRINT_SOURCES[fp]}.pretty" / f"{fp}.kicad_mod"
        if src.exists():
            shutil.copyfile(src, pretty / src.name)
        elif not (pretty / src.name).exists():
            raise SystemExit(f"footprint {fp} not found in {src.parent} or {pretty}")
        vendor_3d_model(pretty / src.name, models_3d)
        if fp == "ESP32-S3-WROOM-1":
            # Stock antenna keep-out omits In2.Cu; extend it to every copper layer of the 4-layer board.
            mod = pretty / src.name
            text = mod.read_text(encoding="utf-8")
            text = re.sub(r'\(zone \(net 0\) \(net_name ""\) \(layers [^)]*\)',
                          '(zone (net 0) (net_name "") (layers "*.Cu")', text)
            mod.write_text(text, encoding="utf-8")
    (KICAD_DIR / "sym-lib-table").write_text(
        '(sym_lib_table\n  (version 7)\n  (lib (name "SGM")(type "KiCad")(uri "${KIPRJMOD}/lib/smart_gas_meter.kicad_sym")'
        '(options "")(descr "Project-local copies of KiCad 7.0.11 stock symbols used by v0.2"))\n)\n', encoding="utf-8")
    (KICAD_DIR / "fp-lib-table").write_text(
        '(fp_lib_table\n  (version 7)\n  (lib (name "SGM")(type "KiCad")(uri "${KIPRJMOD}/lib/SGM.pretty")'
        '(options "")(descr "Project-local copies of KiCad 7.0.11 stock footprints used by v0.2"))\n)\n', encoding="utf-8")


def _netclass(name: str, track: float, clearance: float, via: float, drill: float,
              priority: int, dp_width: float = 0.2, dp_gap: float = 0.25) -> dict:
    return {"bus_width": 12, "clearance": clearance, "diff_pair_gap": dp_gap, "diff_pair_via_gap": 0.25,
            "diff_pair_width": dp_width, "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
            "name": name, "pcb_color": "rgba(0, 0, 0, 0.000)", "priority": priority,
            "schematic_color": "rgba(0, 0, 0, 0.000)", "track_width": track, "via_diameter": via,
            "via_drill": drill, "wire_width": 6}


DESIGN_RULES = """(version 1)
# Project design rules for carrier board v0.2 (generated by tools/generate_schematic.py).
# Hand-soldered 2.54 mm headers sit between neighbouring pads and tracks, so one
# resolved thermal spoke is accepted for through-hole pads; SMD pads connect solid.
(rule "THT header thermal spokes"
  (condition "A.Type == 'Pad' && A.Pad_Type == 'Through-hole'")
  (constraint min_resolved_spokes (min 1)))
"""


def project_file() -> str:
    """KiCad 9 project with net classes used by the PCB (single source of truth)."""
    data = {
        "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 3},
        "net_settings": {
            "classes": [
                _netclass("Default", 0.25, 0.2, 0.6, 0.3, 2147483647),
                # 0.4 mm on 1 oz outer copper carries > 1 A; narrow enough for the USB4105 pads.
                _netclass("Power", 0.4, 0.2, 0.8, 0.4, 0),
                # Native USB 2.0 full-speed pair; 0.2/0.2 mm on the outer layer of a JLC 4-layer stack.
                _netclass("USB", 0.2, 0.2, 0.6, 0.3, 1, dp_width=0.2, dp_gap=0.2),
            ],
            "meta": {"version": 4},
            "net_colors": None,
            "netclass_assignments": None,
            "netclass_patterns": [
                {"netclass": "Power", "pattern": pattern}
                for pattern in ("GND", "+5V", "+3V3", "/USB_VBUS", "/MODEM_VIN", "/REG_SW")
            ] + [{"netclass": "USB", "pattern": "/USB_D*"}],
        },
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [[uid("root"), ""]],
        "text_variables": {},
    }
    return json.dumps(data, indent=2) + "\n"




def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--kicad-share", type=Path, default=Path("/usr/share/kicad"))
    parser.add_argument("--kicad-3d", type=Path, default=None,
                        help="KiCad 3dmodels directory to vendor STEP models from (default: <share>/3dmodels)")
    parser.add_argument("--check", action="store_true",
                        help="do not write; fail if the committed schematic differs from design_v02.py")
    args = parser.parse_args()
    text, symbols = build_schematic(args.kicad_share)
    if args.check:
        committed = (KICAD_DIR / f"{PROJECT}.kicad_sch").read_text(encoding="utf-8")
        if committed != text:
            print("Committed schematic is out of date with design_v02.py; rerun the generator.")
            return 1
        print("Committed schematic matches design_v02.py.")
        return 0
    (KICAD_DIR / f"{PROJECT}.kicad_sch").write_text(text, encoding="utf-8")
    models_3d = args.kicad_3d or args.kicad_share / "3dmodels"
    write_libraries(args.kicad_share, symbols, models_3d if models_3d.exists() else None)
    (KICAD_DIR / f"{PROJECT}.kicad_pro").write_text(project_file(), encoding="utf-8")
    (KICAD_DIR / f"{PROJECT}.kicad_dru").write_text(DESIGN_RULES, encoding="utf-8")
    print(f"Wrote {PROJECT}.kicad_sch with {len(design.PARTS)} parts and "
          f"{len(design.expected_nets())} nets; {len(symbols)} library symbols.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
