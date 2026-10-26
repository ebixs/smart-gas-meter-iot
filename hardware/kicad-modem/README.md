# Modem daughterboard v0.1 — Quectel EC200U-EU (KiCad)

**Status: v0.1-draft — engineering draft, NOT fabrication ready.** The schematic follows the Quectel EC200U Series
Hardware Design V1.0; the PCB is a 4-layer layout study. **The EC200U footprint is provisional**: its pad geometry and
the pad that carries each pin number are placeholders built from the partial dimensions in the hardware design guide.
It must be replaced by Quectel's *EC200U Series Footprint & Part* file, and the board re-placed and re-routed, before
any layout review or order. Bench-only: `MODEM_VIN` comes from a current-limited 3.8 V supply. Never connect any of
this to a live gas meter, gas line, valve, mains or field wiring.

The board plugs onto the carrier board's modem header **J6** (carrier v0.2, `hardware/kicad/`) with a socket **J1**
on its underside, pin for pin: `1 MODEM_VIN · 2 GND · 3 MODEM_TXD · 4 MODEM_RXD · 5 MODEM_EN · 6 MODEM_RESET ·
7 MODEM_STATUS · 8 GND` (3.3 V logic). It is the "replaceable modem board" of the hardware decisions.

## What is here

| Path | Purpose |
|---|---|
| `design_modem_v01.py` | **Single source of truth**: every part, value, footprint and pin → net assignment (same `Part` API as the carrier's `design_v02.py`) |
| `tools/generate_schematic.py` | Writes the schematic, project file and project-local libraries; reuses the carrier's sheet writer unchanged; generates the `EC200U` symbol and the **provisional** footprint |
| `sgm_modem.kicad_sch` / `.kicad_pro` | Native KiCad schematic (KiCad 7 format; opens in KiCad 7, 8, 9) |
| `lib/sgm_modem.kicad_sym`, `lib/SGMM.pretty/`, `lib/3d/` | Project-local symbols, footprints and STEP models (nickname `SGMM`) |
| `pcb_layout_modem_v01.py` | Placement table (75 × 50 mm, 4 layers) |
| `tools/build_pcb.py` | Builds the board with KiCad's `pcbnew` module, fans ground and VBAT pads out to their planes, autoroutes with Freerouting, stitches the ground pours and writes a DRC report |
| `sgm_modem.kicad_pcb` | The routed layout study |
| `check_netlist_matches_design.py` | Netlist vs. design, pin by pin, plus J1 pin-out = carrier J6 |
| `tests/` | Design invariants (no 3V3 on the modem, open-collector PWRKEY/RESET_N, every 1.8 V output shifted, …) |
| `exports/` | Schematic PDF, netlist, DRC report, layer artwork |

## Circuit (from the EC200U hardware design guide)

1. **VBAT** — `MODEM_VIN` (3.3–4.3 V, 3.8 V nominal, up to 2 A bursts) feeds VBAT_RF (57, 58) and VBAT_BB (59, 60).
   Two 100 µF low-ESR tantalum capacitors, a 100 nF / 33 pF / 10 pF MLCC set at each pin pair, and a TVS diode with
   ≥ 4.7 V stand-off (to be selected). On the PCB the whole inner layer In2 is the VBAT plane (the guide asks for
   ≥ 2–2.5 mm VBAT traces). J2 is an optional direct VBAT input, not fitted: never run it in parallel with carrier J7.
2. **PWRKEY / RESET_N** — open-collector MMBT3904 drivers (4.7 kΩ base resistor, 47 kΩ base pull-down) from
   `MODEM_EN` / `MODEM_RESET`. The carrier's 100 kΩ pull-downs keep the module off while the ESP32 boots.
   Switching on or off needs PWRKEY low for ≥ 2 s.
3. **Level shifting** — the module's UART and STATUS are 1.8 V. Three N-MOSFET shifters with their gates on
   `VDD_EXT` (the module's own 1.8 V output, 2.2 µF) and 10 kΩ pull-ups on the 1.8 V side. Candidate FET:
   Diodes DMG2302U (V<sub>GS(th)</sub> ≤ 1.0 V); a BSS138 is marginal with a 1.8 V gate.
4. **(U)SIM** — JAE SF53S006VCBR2000 micro-SIM, 0 Ω series resistors, 33 pF on each line, 10 kΩ pull-up on DATA,
   100 nF on USIM_VDD and a TI ESD224 array (0.5 pF; the guide's limit is 15 pF).
5. **Antenna** — ANT_MAIN on a short 50 Ω line (net class RF, 0.35 mm over the In1 ground plane — confirm with the
   fabricator's stack-up) to a Hirose u.FL, with a π network (0 Ω + two not-mounted shunts).
6. **Network LED** — NET_STATUS drives a green LED through a transistor, about 1.8 mA from VBAT.
7. **Bench access** — test pads for the module USB (VBUS, D+, D−) and the 1.8 V debug UART; solder jumper JP1 with
   4.7 kΩ to `VDD_EXT` forces USB download mode when closed before power-up (open by default).

## Review items (open)

- **Footprint**: replace the provisional EC200U footprint with Quectel's file; then re-place and re-route.
- **MCU-side pull-ups**: J6 carries no 3.3 V rail, so `MODEM_RXD` and `MODEM_STATUS` rely on the ESP32's internal
  pull-ups (firmware must enable them). Alternative: add 3V3 to the next carrier revision's modem header.
- **TVS selection** for VBAT, exact MPNs for the tantalum capacitors and the MOSFETs.
- **Header current**: one 2.54 mm pin carries `MODEM_VIN` bursts of up to 2 A; check the socket rating or use J2.
- **RF line width** against the real stack-up; tune the π network with the chosen antenna.

## Verification (2026-10-26, KiCad 7.0.11 here; CI repeats ERC/DRC with KiCad 9)

| Check | Result |
|---|---|
| Netlist vs. design (`check_netlist_matches_design.py`) | 55 parts, 35 nets, 190 pin connections match; J1 = carrier J6 |
| Schematic ↔ design sync (`generate_schematic.py --check`) | committed file matches a fresh generation |
| Design invariants (`python3 -m unittest discover -s hardware/kicad-modem/tests`) | pass |
| DRC (KiCad 7 `pcbnew`, `exports/drc-kicad-7.rpt`) | 0 violations, 0 unconnected pads |
| ERC + DRC with schematic parity, KiCad 9 (CI `hardware-cad-check.yml`, PR #8) | ERC pass; DRC 0 violations, 0 unconnected, 0 footprint errors |

A clean DRC here only proves the layout is consistent with the **provisional** footprint; it says nothing about the real module pads.

## Regenerate

```bash
python3 hardware/kicad-modem/tools/generate_schematic.py [--kicad-3d /path/to/kicad-packages3D]
python3 hardware/kicad-modem/tools/build_pcb.py --route          # needs Java 21 and freerouting.jar (v2.1)
kicad-cli sch export netlist -o /tmp/modem.net hardware/kicad-modem/sgm_modem.kicad_sch
python3 hardware/kicad-modem/check_netlist_matches_design.py /tmp/modem.net
python3 -m unittest discover -s hardware/kicad-modem/tests
```

The board's exploded 3D model is in `hardware/visualization/boards/modem.html`, and the schematic can be explored
net by net in `hardware/visualization/schematic/index.html`.
