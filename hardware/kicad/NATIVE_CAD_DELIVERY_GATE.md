# Native KiCad delivery gate

**Current status: engineering draft; not fabrication-ready.**

The repository contains a native KiCad S-expression schematic at `smart_gas_meter_iot.kicad_sch`. It has embedded symbol definitions and placed symbol instances, but the last recorded ERC run reported 65 violations. The presence of a native file does not establish electrical correctness.

## Current deliverables
- `SCHEMATIC_IMPLEMENTATION_PLAN.md`: design scope and proposed signal map.
- `SCHEMATIC_ERC_TRIAGE_AND_FREEZE.md`: required ERC and design freeze review.
- `board-v0.2-netlist-draft.csv`: proposed pin/net mapping; it is not a netlist exported from a verified design.
- `board-v0.2-layout-plan.md`: placement and routing constraints.
- `../BOM-board-v0.1.md`: candidate-only BOM.

## Outstanding technical decisions
1. Correct all unintended ERC findings and verify the module symbol pin mapping against the ESP32-S3-WROOM-1-N8 datasheet.
2. Select exact USB-C connector, ESD and VBUS protection parts.
3. Verify regulator, inductor, capacitor ratings, thermal limits and footprints against datasheets.
4. Freeze board outline, mounting holes, stack-up and fabrication constraints.
5. Select cellular modem only after target country/operator/bands and peak-current budget are known.
6. Validate every footprint pad mapping and 3D model against manufacturer drawings.

## Release criteria
- A native schematic opens in KiCad and its exported netlist is reviewed.
- ERC has zero unintended violations; no blanket exclusions or disabled checks.
- A native PCB is built from the reviewed netlist, not manually guessed from the draft CSV.
- DRC has zero unintended violations and antenna keep-out, USB routing, power loops and clearances are reviewed.
- Gerbers are generated only as review artifacts until all electrical, mechanical and bench checks pass.

## Safety boundary
Bench prototype only. Use a current-limited low-voltage supply and synthetic 3.3 V pulse source. Never connect to a live gas meter, gas line, valve, utility wiring, or unknown field signal. No valve actuation is included. Anomalous pulse patterns are not proof of a gas leak.
