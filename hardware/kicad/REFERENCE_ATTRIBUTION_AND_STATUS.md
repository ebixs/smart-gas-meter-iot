# Reference attribution and design status

The current native KiCad schematic is adapted from the ESP32-S3-WROOM-1 example in **74th/esp32-dev-boards**.

- Upstream repository: https://github.com/74th/esp32-dev-boards
- Reference file: `ESP32-S3-WROOM-1/ESP32-S3-WROOM-1.kicad_sch`
- Reference revision: `3ebaa91177bfecc0c8f40ec1124f9d84ab0b988b`
- License reported by upstream repository: MIT
- License text: https://github.com/74th/esp32-dev-boards/blob/main/LICENSE

The upstream reference is credited here; the project-specific file is a starting point for adaptation, not a claim of original authorship or electrical approval. Preserve upstream copyright/license notices where required when redistributing adapted material.

## What this file currently is

A native KiCad schematic document with embedded symbol definitions and placed symbol instances, adapted from an ESP32-S3 dev-board reference. It still contains reference circuitry and requires project-specific review and modification before it can be treated as the smart gas meter prototype schematic.

## Required before electrical release

- Verify all connector and module pin numbers against the exact manufacturer documents and footprints.
- Confirm the USB-C connector, CC resistors, ESD protection and input protection are appropriate for the selected parts.
- Confirm the regulator, inductor, capacitors, current capacity, thermal behavior and power-up behavior.
- Replace any reference-only programming/development-board circuitry not needed by this carrier.
- Add the project's synthetic pulse input, protection, test points and modem daughterboard interface as actual wired schematic elements.
- Run ERC with KiCad and resolve errors; review warnings individually.
- Generate the PCB from the reviewed schematic, then run DRC and inspect the 3D assembly.
- Do not connect to a live gas line, production meter, valve or unknown field signal. The prototype is for isolated low-voltage bench testing with synthetic pulses only.
