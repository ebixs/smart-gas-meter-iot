# Controlled schematic reconstruction — v0.2

> **Progress 2026-10-24 (v0.2-draft2):** steps 1–5 are done. The frozen draft is archived under `archive/v0.2-frozen-2026-10-23/`. A clean sheet is generated from `design_v02.py` using project-local copies of stock KiCad symbols/footprints. KiCad 9.0.3 ERC reports 0 errors and 0 warnings, and the exported netlist passes `check_netlist_invariants.py` and a pin-by-pin comparison with the design (`check_netlist_matches_design.py`). All required rails (`USB_VBUS`, `+5V`, `+3V3`, `GND`, `MODEM_VIN`) are distinct. The schematic-stage "definition of done" is still open on the exact-part selection and independent datasheet review listed in `README.md`. Step 6 (PCB) has not started.

**Status: implementation contract; not a released schematic.**  
**Safety boundary:** bench-only, current-limited low-voltage supply and synthetic 3.3 V pulse source. Never connect to a live gas meter, gas line, valve, utility wiring, or an unknown field signal.

## Why the existing sheet is frozen

The 2026-10-23 KiCad 9.0.9 export found 5 ERC errors and 60 warnings. The exported netlist also merged intended +5V and GND connectivity and placed both pins of C4/C5 on the same net. This is a real electrical fault. Do not create a PCB from the frozen sheet and do not suppress ERC to make CI green.

## Target architecture

Use one ESP32-S3-WROOM-1-N8 module on a carrier PCB. Remove all legacy ESP32 development-board headers from the production-intent sheet. Keep programming through native USB only after the USB-C pin map is verified against the selected connector datasheet.

Functional blocks, in order:
1. USB-C receptacle and VBUS input protection.
2. USB-C CC1 and CC2 each connected to its own 5.1 kΩ Rd resistor to GND; duplicate USB data pins joined only as required by the exact receptacle symbol/datasheet.
3. USB D− to GPIO19 and D+ to GPIO20, with a suitable low-capacitance ESD protector near the connector. Confirm ESP32-S3 native USB pin mapping against the module datasheet.
4. One regulator topology only. Do not mix the legacy AMS1117 circuit with the proposed AP63203 buck. Select a topology after input range, load, thermal constraints, inductor, and datasheet application circuit are checked. Label the regulator and its input/output nets clearly.
5. ESP32-S3 module power and local decoupling. Every capacitor must connect between its intended rail and GND; no capacitor pins may share the same rail unless that is explicitly its component function.
6. Synthetic pulse fixture: connector signal and GND only; 3.3 V logic/dry-contact source; defined pull-up, MCU-side series resistor, optional filter footprint. No direct mains, meter, valve, or field wiring.
7. Status LED with series resistor; BOOT/RESET circuits; labelled test points.
8. Cellular daughterboard connector only as an interface placeholder until a modem SKU is chosen. Keep MODEM_VIN separate from 3V3 and do not assume the MCU regulator can supply modem burst current.
9. Optional enclosure tamper switch to a GPIO with defined bias/debounce; no safety-critical actuation.

## Required net naming and invariants

The following must remain distinct in the exported netlist:
- `USB_VBUS`: connector VBUS before the chosen input protection.
- `+5V` (or a more appropriate protected input name): protected power rail after protection.
- `+3V3`: regulator output and module/peripheral logic supply.
- `GND`: common return.

Electrical invariants:
- No net contains both `+5V` and GND pins or labels.
- No capacitor's two terminals appear on the same net unless the datasheet explicitly defines a shorted component.
- The regulator output connects only to the intended 3V3 load rail; no second power-output source is present.
- The ESP32 module is the sole MCU symbol; no duplicate dev-board power headers remain.
- USB connector power pins and GND pins use correct symbol pin electrical types and physical pin numbers.
- Every connector footprint and symbol pin map is cross-checked against a manufacturer drawing.
- No modem supply pin is silently tied to 3V3.
- Pulse input has a documented maximum of 3.3 V and is marked synthetic bench signal only.

## Rebuild sequence and evidence required

1. Archive the frozen draft and its ERC/netlist artifacts; do not overwrite the evidence.
2. Build a clean native KiCad sheet from project-local or verified standard symbols. Record symbol library IDs and footprints.
3. Generate a fresh netlist and inspect every power net and all connector pin numbers before running ERC.
4. Run ERC; fix root causes rather than changing pin types or adding no-connect flags to hide faults. Any intentional exception must be explained in a reviewed note.
5. Export the netlist again and run automated checks for the invariants above.
6. Only after the sheet is electrically coherent, create the PCB from that exact schematic revision.
7. Run DRC and manually review antenna keep-out, USB differential pair routing, regulator hot loop, connector access, creepage/clearance as applicable, and test-point accessibility.
8. Generate 3D views from actual PCB footprints/models. Do not present illustrative concept renders as CAD-derived assembly evidence.
9. Release Gerbers/drills/assembly outputs only after ERC, netlist checks, DRC, BOM/footprint review, and bench bring-up are documented.

## Definition of done for schematic stage

- Native schematic opens in the declared KiCad version.
- ERC has no unresolved electrical errors; remaining warnings are reviewed individually and documented.
- Exported netlist passes the invariants above.
- BOM and footprint assignments match the schematic revision.
- A reviewer can trace USB input → protection → regulator → module and synthetic pulse connector → GPIO without ambiguity.
- The status is still **not fabrication-ready** until a native PCB passes DRC and manufacturing review.

## Not yet selected

- Exact USB-C connector, fuse/protection and ESD SKUs.
- Final regulator and supporting component values.
- Exact modem SKU, radio bands, peak current, supply rail, and antenna.
- PCB stack-up, copper weight, dimensions, and manufacturer constraints.

These are deliberate open engineering decisions, not permission to guess parts or fabricate a board.
