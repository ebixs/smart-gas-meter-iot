# Board v0.2 — Production-Oriented Schematic Plan

**Status:** Electrical design plan only. This file is not a KiCad schematic, a routed PCB, or a fabrication release.  
**Revision intent:** Expand the v0.1 low-voltage lab board into a cellular-capable engineering prototype while keeping field-meter interfaces uncommitted until requirements are verified.

## Block-level design

1. USB-C service/programming input with ESD protection and correct CC sink resistors.
2. Input protection and a defined primary power input, to be selected after the deployment power source is decided.
3. Separate MCU 3.3 V rail and modem power rail. The modem rail must be designed against the selected module's transmit peak current and transient requirements.
4. ESP32-S3-WROOM-1-N8 controller with reset/boot, USB D+/D-, decoupling, debug/test points, and module antenna keep-out.
5. Replaceable cellular modem daughterboard interface: supply, GND, UART, enable, reset, status, SIM/eSIM approach, RF/antenna interface, and test pads.
6. Laboratory pulse input only for first bring-up; field interface to be designed only after the exact sensor/meter output and isolation needs are documented.
7. Enclosure tamper switch input, RTC option, and non-volatile event queue option.
8. Service/expansion header with explicitly labeled logic levels and power budget.
9. Optional battery monitor/fuel gauge only after battery chemistry and capacity are chosen.

## Proposed schematic sheets

- 00_System_Overview — power domains, board connectors, block interfaces.
- 01_USB_Service — USB-C connector, CC resistors, ESD, native USB routes.
- 02_MCU — ESP32-S3 module, reset/boot, decoupling, GPIO allocation.
- 03_Power — input protection and independent logic/modem supplies.
- 04_CellModem_Interface — replaceable modem interface, UART, control/status, SIM/RF boundaries.
- 05_Lab_Pulse_Tamper — lab pulse input, enclosure switch, test points.
- 06_Storage_Time — optional RTC and non-volatile storage.
- 07_Expansion_Test — headers and manufacturing/test points.

These are planned sheet names, not existing CAD sheets.

## Pin allocation changes required from v0.1

The old v0.1 assignment reserved GPIO17/18 for modem UART and GPIO4 for laboratory pulses. A final allocation must be reviewed against the chosen modem daughterboard, boot strapping, USB, optional RTC/storage, and any sensor interrupt requirements. Do not assume the old pin map is frozen.

## Power-design hold point

No power circuit can be finalized responsibly until the primary input is chosen. For a cellular product, the modem supply cannot be sized by MCU needs; transmit bursts can dominate peak current. The power budget must include:
- Input minimum/maximum and transients.
- Modem peak current, burst duration, and voltage droop limits.
- MCU and peripheral load.
- Optional battery chemistry, charge strategy, protection, and fuel gauge.
- Thermal performance and expected ambient temperature.
- Brownout, network outage, and low-battery recovery behavior.

## Cellular hold point

Do not select an exact modem part or RF footprint until deployment country, operator, supported bands, SIM/eSIM, coverage technology, and certification path are confirmed. The modular interface is a risk-reduction measure, not a substitute for that decision.

## CAD and manufacturing release gates

- [ ] Native KiCad schematic and project created with selected manufacturer symbols/footprints.
- [ ] Every symbol pin mapping verified against current manufacturer documents.
- [ ] ERC completed and all findings reviewed.
- [ ] PCB outline, component placement, antenna keep-outs, copper layers, differential USB routing, modem power loops, and ground return reviewed.
- [ ] DRC completed with no unexplained errors.
- [ ] 3D assembly checked against the selected footprints and actual 3D models.
- [ ] BOM contains exact orderable part numbers and alternates.
- [ ] Gerbers, drill, pick-and-place, and assembly outputs exported only after design review.
- [ ] Prototype tested on bench with current-limited power and synthetic pulse fixture only.
- [ ] No live gas meter, valve, pipe, or unknown field wiring connected during prototype testing.

## Current limitation

The current execution environment does not have KiCad CLI or its Python board library available, so it cannot validate native KiCad CAD here. This file intentionally records the required sheet structure and design gates instead of pretending an unvalidated CAD file exists.
