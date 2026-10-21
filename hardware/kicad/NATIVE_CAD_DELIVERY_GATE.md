# Native KiCad delivery gate

The current `smart_gas_meter_iot.kicad_sch` is a graphical block concept, not a native electrical schematic. The existing CI intentionally rejects it. This hold point remains until the native schematic has embedded symbol definitions, placed pin-level symbols, explicit wires/labels and an ERC review.

## Current deliverables
- `SCHEMATIC_IMPLEMENTATION_PLAN.md`: design scope and proposed signal map.
- `board-v0.2-netlist-draft.csv`: proposed pin/net mapping for a low-voltage lab prototype.
- `board-v0.2-layout-plan.md`: PCB placement and routing constraints.
- `../BOM-board-v0.1.md`: candidate-only BOM.

## Outstanding technical decisions
1. Final power stage and exact regulator BOM/footprints, validated against current datasheet.
2. Exact USB-C connector and ESD protector.
3. Verify module pin numbers and symbol against the selected ESP32-S3-WROOM-1-N8 datasheet.
4. Freeze board outline and mounting holes.
5. Choose cellular modem only after deployment country/operator/bands and peak-current budget are known.

## Release criteria
A deliverable may be called a native schematic only after KiCad opens it as an electrical schematic and ERC has been run. A deliverable may be called a routed PCB only after the board file exists and DRC is run. Gerbers must not be described as manufacturing-ready before review.
