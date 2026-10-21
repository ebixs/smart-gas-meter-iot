# PCB Layout Plan — v0.2

**Status:** placement and routing plan only. This is not a routed PCB or a fabrication release.

## Placement
1. Reserve the ESP32-S3 module antenna clearance at a board edge according to the exact Espressif datasheet.
2. Place USB-C at an accessible edge; keep the CC resistors and low-capacitance ESD protector close to the connector.
3. Place the regulator, inductor and input/output capacitors as a compact reference-design power loop. The exact regulator and values remain unverified.
4. Keep MCU decoupling close to module supply pins.
5. Place BOOT/RESET switches and labeled test points where accessible.
6. Keep the synthetic pulse input and its series resistor away from the switching node and USB pair.
7. Defer the cellular module and its power circuit until the modem SKU, supply range and transmit peak current are known.

## Routing constraints
- USB D+/D-: matched differential routing; determine geometry from the selected stack-up and board-house impedance guidance.
- Power converter: minimize the high-current loop and switch-node copper; keep it away from the pulse input.
- Ground: preserve a continuous reference plane wherever possible.
- Pulse input: short route; do not finalize optional filtering until pulse width and maximum rate are specified.
- Antenna keep-out: follow the exact module manufacturer's instructions; do not route copper or place components in the prohibited area.
- Do not add RF routing until the cellular module and antenna topology are selected.

## Release gates
- Verify every symbol, pin number, footprint and orderable part against current manufacturer documents.
- Run KiCad ERC and review every finding.
- Run PCB DRC and resolve or document every finding.
- Inspect 3D mechanical clearance and antenna keep-out.
- Export manufacturing outputs only from the reviewed PCB.

This document is not a PCB file, copper routing, Gerber set or proof of electrical correctness. Do not fabricate from this plan.
