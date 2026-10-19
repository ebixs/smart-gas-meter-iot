# Board v0.1 — PCB Layout and Release Checklist

**Status:** Design-review checklist; not evidence that a PCB layout exists or passed checks.

## Schematic / library
- [ ] Select exact ESP32-S3-WROOM-1-N8 module variant and verify symbol/footprint pad numbering against Espressif's current drawing.
- [ ] Select exact AP63203 package/orderable suffix and verify pin numbering, recommended circuit, inductor, and capacitors against the current Diodes Incorporated datasheet.
- [ ] Verify the module's EN and GPIO0/strapping circuits against Espressif reference design.
- [ ] Add USB-C CC1/CC2 Rd resistors (5.1 kΩ each for a USB-C sink/device implementation); verify connector pin mapping.
- [ ] Select low-capacitance USB ESD protection and confirm orientation/line mapping.
- [ ] Calculate LED resistor for selected LED and GPIO current limits.
- [ ] Confirm pulse-input resistor placement and decide whether filtering is needed only after pulse waveform/rate is characterized.
- [ ] Run ERC and resolve or document every finding.

## Placement / routing
- [ ] Place USB-C connector at a board edge; keep ESD protection close to connector.
- [ ] Keep USB D+/D- short and routed as a differential pair using board-house stack-up guidance; avoid stubs.
- [ ] Follow ESP32-S3 module antenna keep-out and edge-placement guidance exactly; keep copper/components out of the required zone.
- [ ] Keep the regulator's high-di/dt loop compact and follow the datasheet's recommended layout; do not route sensitive pulse input under the switching node/inductor.
- [ ] Use a continuous ground reference where practical; avoid splitting the return path beneath USB.
- [ ] Add labeled test points for VBUS_5V, 3V3, GND, EN, and PULSE_IN.
- [ ] Mark the board “LAB PROTOTYPE — NO GAS-LINE CONNECTION” on silkscreen.
- [ ] Run DRC and review board outline, clearances, drill sizes, solder-mask, silkscreen, and manufacturing constraints.

## Release package gate
- [ ] Schematic source and project files committed.
- [ ] PCB source and project files committed.
- [ ] ERC/DRC reports reviewed and archived.
- [ ] 3D assembly checked for connector, module, and component collisions.
- [ ] Gerbers, drill files, and BOM/CPL exported only after review.
- [ ] No fabrication release until all items above are completed.
