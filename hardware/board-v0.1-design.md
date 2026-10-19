# Board v0.1 — Engineering Design Baseline

**Project:** Smart Gas Meter IoT  
**Revision:** 0.1 — schematic-planning baseline  
**Status:** Proposed design; not yet a validated schematic or PCB  
**Use:** Low-voltage laboratory prototype only

## 1. Design decision

Use an **ESP32-S3-WROOM-1-N8** module as the controller and a USB-C connector for 5 V power, programming, and USB serial/JTAG. A dedicated 3.3 V buck supply is planned using **AP63203WU-7** (fixed 3.3 V, 2 A class) based on the manufacturer's application circuit. The exact orderable package, footprint, inductor, capacitor ratings, USB protection, and layout must be checked against current manufacturer documents before schematic/PCB release.

This is a custom carrier PCB around a certified radio module, not a custom RF design. The module antenna area must follow Espressif's keep-out and placement guidance.

Primary reference documents:
- [ESP32-S3-WROOM-1 / WROOM-1U datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)
- [AP63200/AP63201/AP63203/AP63205 datasheet](https://www.diodes.com/datasheet/download/AP63200-AP63201-AP63203-AP63205.pdf)

## 2. v0.1 scope

Included:
- ESP32-S3 module, USB-C 5 V input and native USB data lines
- 3.3 V regulator and local decoupling
- Reset and boot buttons
- One protected **dry-contact / 3.3 V logic** pulse input for lab testing
- Status LED, debug/test points, and expansion header
- Optional I2C footprint/header for later RTC or peripheral module

Explicitly not included in v0.1:
- Any connection to a live gas meter, gas line, valve, or utility wiring
- Any input accepting 5 V, 12 V, 24 V, mains, or unknown field wiring
- Cellular modem and its power subsystem (separate later design after module/band/current review)
- Certified metrology, safety functions, or billing-grade accuracy claims

## 3. Proposed net and pin assignment

| Signal / net | ESP32-S3 connection | Purpose / constraint |
|---|---|---|
| USB_D- | GPIO19 | Native USB; route as a differential pair |
| USB_D+ | GPIO20 | Native USB; route as a differential pair |
| PULSE_IN | GPIO4 | Lab-only dry-contact / 3.3 V logic input |
| STATUS_LED | GPIO5 through a current-limiting resistor | Firmware status indication |
| I2C_SDA | GPIO6 | Optional expansion; 3.3 V only |
| I2C_SCL | GPIO7 | Optional expansion; 3.3 V only |
| MODEM_UART_TX | GPIO17, reserved | Future modem interface; not populated in v0.1 |
| MODEM_UART_RX | GPIO18, reserved | Future modem interface; not populated in v0.1 |
| BOOT | GPIO0 / strapping pin | Button to GND; verify startup behavior |
| RESET_EN | EN | Reset button and datasheet-recommended enable network |
| 3V3 | Module 3V3 | Regulated rail; verify current/transient budget |
| GND | Module GND | Continuous reference plane |

The GPIO assignment is provisional and must be cross-checked against the exact module variant, strapping requirements, and all selected peripherals before schematic freeze.

## 4. Circuit blocks

### J1 — USB-C power and programming
- USB-C receptacle, USB 2.0 device wiring.
- CC1 and CC2 each use the required sink/device pull-down resistor selected per the USB Type-C specification.
- Route D+/D- to GPIO20/GPIO19 with short, matched, controlled-impedance routing as practical for the board stack-up.
- Add low-capacitance USB ESD protection close to the connector.
- VBUS is the 5 V input rail. Do not connect VBUS directly to 3V3.
- Confirm whether a VBUS sense circuit is needed by the chosen firmware/programming mode.

### U1 — 3.3 V buck supply
- Candidate: AP63203WU-7, fixed 3.3 V output.
- Use the manufacturer-recommended application circuit and component calculations, including input/output capacitors, bootstrap capacitor, and inductor.
- Select the inductor for saturation current, RMS current, DCR, and the datasheet's recommended inductance.
- Place the input capacitor, IC, bootstrap capacitor, inductor, and output capacitor tightly to minimize the high-di/dt loop and switching-node copper.
- Verify startup, ripple, thermal behavior, and ESP32-S3 radio current transients on the assembled board.
- The 2 A IC rating does not guarantee 2 A continuous output on every PCB; thermal/layout conditions must be checked.

### U2 — ESP32-S3-WROOM-1-N8
- Power from 3V3 with local decoupling placed close to the module supply pins.
- Follow Espressif's recommended module footprint, ground stitching, antenna clearance, and placement rules.
- Keep copper, components, enclosure metal, and cables out of the module antenna keep-out area as specified by Espressif.
- Use native USB on GPIO19/GPIO20; avoid assigning those pins to other functions.

### J2 — pulse test input (lab only)
- Connector pins: PULSE_IN and GND; no external supply pin.
- Use a normally-open button to short PULSE_IN to GND for a manual test.
- Provide a 10 kΩ pull-up from PULSE_IN to 3V3 and a 1 kΩ series resistor close to the MCU pin.
- A small capacitor footprint to GND may be fitted only after bounce/rise-time measurements; do not choose the final value without verifying the intended maximum pulse rate.
- Configure firmware for edge counting and software debounce/qualification, with the minimum pulse width and maximum rate documented by tests.
- This input is not electrically isolated and is not suitable for field wiring.

### SW1 / SW2 — BOOT and RESET
- BOOT pulls GPIO0 low only while pressed.
- RESET pulls EN low momentarily; use the module datasheet's recommended EN pull-up and capacitor arrangement.
- Check boot behavior and startup timing during bring-up.

### D1 — status LED
- LED plus series resistor from a GPIO to GND (or reverse polarity if the chosen footprint/circuit requires it).
- Select resistor based on LED forward voltage and a conservative GPIO current; verify brightness and current during prototype testing.

### J3 — expansion/debug
- Expose GND, 3V3, PULSE_IN, I2C_SDA, I2C_SCL, and reserved UART signals.
- Mark test points clearly on silkscreen. Do not expose unprotected signals as field connectors.

## 5. Layout constraints

1. Use a continuous ground plane on the primary reference layer where possible.
2. Keep the buck converter's switching loop compact; keep SW copper small and away from PULSE_IN and USB.
3. Route USB D+/D- as a differential pair using the actual PCB stack-up/board house impedance guidance.
4. Place USB ESD parts adjacent to the connector, with a short return to ground.
5. Place module antenna at the board edge and obey the exact Espressif keep-out guidance.
6. Keep the pulse input away from the switching node and add a nearby ground reference.
7. Add test points for VBUS, 3V3, GND, EN, PULSE_IN, and (if accessible) UART/debug.
8. Add clear connector pin-1 marks, polarity labels, board revision, and “LAB PROTOTYPE — NOT FOR GAS FIELD USE” on silkscreen.

## 6. Bring-up and acceptance gates

Do not release manufacturing files until these checks are complete:

- [ ] Verify all footprints and pin numbers against manufacturer datasheets.
- [ ] Run ERC with no unexplained power/pin errors.
- [ ] Run PCB DRC with no unexplained clearance, mask, courtyard, or unconnected-net errors.
- [ ] Review 3D assembly and antenna keep-out.
- [ ] Power the unpopulated board from a current-limited bench supply and verify no shorts.
- [ ] Verify 5 V input and 3.3 V rail before installing/connecting the MCU module.
- [ ] Check 3.3 V rail under startup and wireless activity; inspect ripple and temperature.
- [ ] Test USB enumeration, flashing, reset, and boot mode.
- [ ] Apply a known number of dry-contact pulses and compare MCU counts with the source.
- [ ] Test bounce, slow edges, minimum pulse width, and maximum intended rate.
- [ ] Record board revision, component substitutions, test setup, and results.

## 7. Companion engineering drafts

- [Preliminary pin/net connection table](board-v0.1-netlist-draft.csv) — planning aid, not a native CAD netlist.
- [PCB layout and release checklist](board-v0.1-layout-checklist.md).
- [Bring-up and acceptance test plan](board-v0.1-bringup-test-plan.md).
- [Preliminary BOM](BOM-board-v0.1.md).

## 8. What is still open

This document is a circuit-design baseline, not a completed CAD design. The next engineering deliverable is the actual KiCad schematic and footprints, followed by PCB placement/routing, ERC/DRC, and manufacturing outputs. Do not order boards from this document alone.
