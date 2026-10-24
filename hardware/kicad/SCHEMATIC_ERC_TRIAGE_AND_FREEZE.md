# v0.2 schematic ERC triage and freeze checklist

> **Update 2026-10-24:** the findings below refer to the **archived** frozen draft (`archive/v0.2-frozen-2026-10-23/`). The active schematic is the controlled rebuild v0.2-draft2: KiCad 9.0.3 ERC 0 errors / 0 warnings ([report](exports/erc-kicad-9.0.3.rpt)), no exclusions. Its netlist passes the invariant guardrail and matches `design_v02.py` pin by pin. The freeze checklist at the end of this file remains open until the exact-part and datasheet review is done.

**Status: schematic freeze candidate v0.2-rc1. Board gate OPEN, not approved for fabrication.** This file tracks real electrical review items. It does not waive KiCad ERC/DRC.

## Current CI evidence
- Native schematic parses and netlist export is attempted by KiCad CLI.
- Latest hardware-CAD run on 2026-10-23: [run 39962389116](https://github.com/ebixs/smart-gas-meter-iot/actions/runs/39962389116). Its diagnostic artifact is [kicad-validation-39962389116](https://github.com/ebixs/smart-gas-meter-iot/actions/runs/39962389116/artifacts/12505237688).
- KiCad 9.0.9 reported **65 ERC messages: 5 errors and 60 warnings** and returned exit code 5.
- The workflow now continues after ERC/DRC errors and uploads diagnostic artifacts. The 2026-10-23 run confirms schematic structure check passed and the artifact upload succeeded; the overall CAD job still fails because ERC reports violations. Python simulator/API tests passed in [run 39962389242](https://github.com/ebixs/smart-gas-meter-iot/actions/runs/39962389242).
- No DRC result is evidence of a valid board unless a native `.kicad_pcb` file exists and the DRC step runs.


## Findings from the 2026-10-23 ERC artifact

The downloaded report confirms these are electrical design issues, not just library warnings:

- **Power-output conflicts:** the ESP32 dev-board connector symbols J1/J2 and programmer/USB connector symbols J3/J4 use pin electrical types that KiCad interprets as power outputs. Several are connected together, producing explicit pin-to-pin errors.
- **Power-net short:** the report says **both +5V and GND are attached to the same items** and +5V wins in the generated netlist. Treat this as a blocking short until the connector symbols and wiring are rebuilt and verified.
- **Regulator conflict:** U2 (AMS1117-3.3) output is tied to another power-output pin on the 3V3 rail. The proposed architecture previously called for a buck regulator, so the schematic and BOM are not yet aligned.
- **Legacy footprint/symbol libraries:** the report references missing `Espressif`, `esp32-dev-boards`, `$74th`, and standard-library tables. Resolve these with a project-local KiCad library table or standard symbols/footprints before layout.
- **Generated netlist exists** in the run artifact, but it is not acceptable for PCB work while the power-net conflict remains.

### Corrective action order

1. Remove the legacy dev-board connector symbols from the intended module-based circuit, or replace them with verified connector symbols whose pin numbers and electrical types match their datasheets.
2. Rebuild USB-C and programming headers from exact, reviewed pin maps; do not preserve the current J3/J4 symbols by merely silencing ERC.
3. Remove the +5V/GND net collision and inspect the exported netlist to confirm those nets are separate.
4. Decide and document one regulator topology; update schematic, footprints, BOM and layout plan together.
5. Add/resolve library tables, rerun ERC, then manually inspect the report and netlist before starting PCB placement.


## Netlist-level blocking findings (artifact inspected)

The exported `smart_gas_meter_iot.net` was inspected in addition to the ERC summary. It confirms that the current draft must not be used to generate a PCB:

- Net `+5V` contains **both pins of C4 and both pins of C5**, meaning these capacitors are shorted by the current connectivity; it also contains U1 GND pins and U2 GND/VI, and J2/J3/J4 pins marked GND. The netlist's `+5V` name is therefore misleading because distinct intended nets have merged.
- Net `+3V3` contains both the intended module supply and regulator output, plus the old dev-board connector J1 pin 2. That duplicates the module power interface and causes a power-output conflict with U2.
- The schematic currently includes both the module U1 (ESP32-S3-WROOM-1) and legacy dev-board header symbols J1/J2. Those should not coexist as if they were separate board-level supply sources in the carrier design.
- The legacy USB/programming symbols have incorrect electrical pin classifications for connectors (GND/VCC marked power-output), and their current connectivity joins +5V and GND.

**Decision:** do not patch this by changing ERC pin types alone. The schematic connectivity needs a controlled rebuild around one architecture: module-only carrier board, one documented power path, separate USB VBUS / +5V / 3V3 / GND nets, correctly mapped USB-C connector and CC resistors, and a low-voltage synthetic pulse input. Keep the existing draft as historical evidence until the rebuilt sheet passes ERC and its netlist is reviewed.

## Required review sequence

1. Open the generated ERC report and group all findings by rule and reference designator.
2. Correct electrical causes in the schematic; do not globally disable ERC rules or use blanket exclusions.
3. Check all symbol pin numbers and functions against the selected ESP32-S3-WROOM-1-N8 datasheet, including strapping pins, EN, USB, power and ground.
4. Confirm that the actual schematic implements the proposed signal table; remove legacy/dev-board symbols that conflict with the module-based design.
5. Resolve all footprint library references to standard KiCad libraries or checked-in, versioned project libraries.
6. Re-run KiCad ERC; only after a clean reviewed report should PCB layout begin.

## Electrical freeze items
Status for v0.2-rc1 (2026-10-24). Evidence: [PART_SELECTION.md](PART_SELECTION.md), [ERC report](exports/erc-kicad-9.0.3.rpt), `check_netlist_matches_design.py`.
- [x] ESP32-S3-WROOM-1-N8 pin-number mapping verified against the manufacturer pin table (1 GND, 2 3V3, 3 EN, 13/14 IO19/IO20, 27 IO0, 36/37 RXD0/TXD0, 40/41 GND). Second-engineer review pending.
- [x] USB-C connector selected (GCT USB4105-GF-A); CC1/CC2 each with its own 5.1 kΩ Rd; D+/D− pin map checked against the GCT pin table.
- [x] USB ESD (USBLC6-2SC6) and VBUS protection (1206L075/13.2WR PTC + SMAJ6.5CA TVS) selected from datasheets.
- [x] 3.3 V regulator AP63203WU-7 with datasheet-table passives (3.9 µH Isat 3 A, 10 µF in, 2 × 22 µF 16 V out, 100 nF BST); 2 A rating vs ≈ 0.41 A load. **Thermal layout remains a PCB-stage item.**
- [x] Module power pin and local decoupling (10 µF + 100 nF) per Espressif guidance.
- [x] BOOT/EN: 10 kΩ / 1 µF EN RC per Espressif guidelines, RESET to GND, GPIO0 10 kΩ pull-up with BOOT button.
- [x] Synthetic pulse input: 3.3 V lab logic only, 10 kΩ pull-up default-high, 1 kΩ series, optional DNP filter.
- [x] All unconnected pins carry explicit no-connect flags and are listed as `NC` in `design_v02.py`; the netlist check proves the NC set is exact.
- [ ] Footprints match manufacturer package drawings. Symbol pin ↔ pad numbers are verified for all 48 parts; **land-pattern overlay against the drawings is a PCB-stage item.**
- [x] ERC reviewed with zero violations (KiCad 9.0.3: 0 errors, 0 warnings, no exclusions).

## Board gate (stage 3)
Do not route or release a board until the schematic netlist and footprints pass review. Board acceptance requires:
- [ ] Board outline and mounting-hole coordinates frozen.
- [ ] ESP32 antenna keep-out maintained per module datasheet.
- [ ] USB differential pair routed to the chosen stack-up/impedance guidance.
- [ ] Regulator switching loop and return paths minimized.
- [ ] Connector accessibility and test-point spacing checked.
- [ ] DRC report reviewed; zero unintended violations.
- [ ] 3D model positions and clearances reviewed against actual parts.

## Safety and use boundary
Bench prototype only. Use a current-limited low-voltage supply and a synthetic 3.3 V pulse source. Never connect to a live gas meter, gas line, valve, utility wiring, or unknown field signal. No valve actuation is included. Anomalous pulse patterns are not proof of a gas leak.
