# v0.2 schematic ERC triage and freeze checklist

**Status: OPEN — not approved for fabrication.** This file tracks real electrical review items. It does not waive KiCad ERC/DRC.

## Current CI evidence
- Native schematic parses and netlist export is attempted by KiCad CLI.
- Latest recorded hardware-CAD run on 2026-10-22: [run 39855322995](https://github.com/ebixs/smart-gas-meter-iot/actions/runs/39855322995).
- KiCad 9.0.9 reported **65 ERC violations** and returned exit code 5.
- The workflow was updated to continue exporting SVG/netlist/DRC/Gerber outputs even if ERC/DRC fails, so diagnostic artifacts remain available.
- No DRC result is evidence of a valid board unless a native `.kicad_pcb` file exists and the DRC step runs.

## Required review sequence

1. Open the generated ERC report and group all findings by rule and reference designator.
2. Correct electrical causes in the schematic; do not globally disable ERC rules or use blanket exclusions.
3. Check all symbol pin numbers and functions against the selected ESP32-S3-WROOM-1-N8 datasheet, including strapping pins, EN, USB, power and ground.
4. Confirm that the actual schematic implements the proposed signal table; remove legacy/dev-board symbols that conflict with the module-based design.
5. Resolve all footprint library references to standard KiCad libraries or checked-in, versioned project libraries.
6. Re-run KiCad ERC; only after a clean reviewed report should PCB layout begin.

## Electrical freeze items
- [ ] ESP32-S3-WROOM-1-N8 pin-number mapping verified against manufacturer datasheet.
- [ ] USB-C connector exact manufacturer part number selected; CC1/CC2 Rd and D+/D− pin mapping reviewed.
- [ ] USB ESD/protection part and VBUS protection selected from datasheets.
- [ ] 3.3 V regulator selected with verified inductor, input/output capacitor values, current capability and thermal layout.
- [ ] All module power pins and local decoupling reviewed.
- [ ] BOOT/EN reset network follows Espressif reference design and startup requirements.
- [ ] Synthetic pulse input is limited to 3.3 V lab logic, has a defined default state and series protection.
- [ ] All unconnected pins are either intentionally documented or connected as required.
- [ ] Footprints match manufacturer package drawings and KiCad pad numbers.
- [ ] ERC reviewed with zero unintended violations.

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
