# Smart Gas Meter IoT — Anatomy-inspired 3D visual design

This project adopts the open-source **Anatomy** skill's visual principles (MIT): depict the system as a recognisable physical instrument, build layered parts with deliberate depth, use restrained motion, and make the illustration explain the mechanism rather than relying on abstract boxes.

Reference: https://github.com/wheresryan22/anatomy

## Deliverables in this folder

- `smart-gas-meter-exploded.html`: standalone interactive isometric concept illustration. Open locally in a browser; no build step, framework, or network connection required.
- The drawing is an **illustrative concept model**, not a mechanical CAD model, KiCad 3D render, enclosure drawing, or fabrication reference.
- Controls let the viewer rotate the presentation slightly, toggle the exploded view, and pause motion. Respect for reduced-motion preferences is built in.

## Visual mapping

- The carrier PCB and standoffs form the base.
- ESP32-S3 module is the processing core.
- Protected pulse input, power conversion, USB-C, debug/test pads, and a reserved cellular daughterboard are shown as physically separate regions.
- A dashed signal path illustrates the intended *simulated pulse → MCU → radio/backend* flow; it does not imply a validated electrical design.
- The modem is intentionally labelled as a reserved interface: final SKU depends on deployment region, operator bands, certification, antenna, and power budget.

## Safety and maturity

This illustration is for design communication only. It does not replace the pin-level schematic, routed PCB, 3D mechanical CAD, electrical/ERC/DRC validation, or a field safety assessment. Bench testing must use synthetic pulse inputs at low voltage only. Do not connect to a live gas line or an operational meter. No valve actuation is implemented.

## Source skill licence

Anatomy is MIT-licensed. This project's illustration is an independent implementation inspired by its documented approach; it does not copy Anatomy example artwork or source files.
