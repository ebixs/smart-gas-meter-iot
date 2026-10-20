# KiCad v0.2 — pin-level implementation plan

**Status:** Engineering definition for the first native schematic; not a released schematic, PCB, or fabrication package.  
**Use:** low-voltage bench prototype only. Never connect this board to a live gas meter, gas line, valve, utility wiring, or unknown field signal.

## Design boundary

The first sheet is a carrier board for an ESP32-S3-WROOM-1-N8 and a low-voltage synthetic pulse fixture. Cellular connectivity is provided through a replaceable modem daughterboard interface, but the modem supply cannot be finalized until a specific modem SKU, regional bands, operator, SIM/eSIM arrangement, and peak-current profile are confirmed.

## Proposed sheet breakdown

1. **USB-C and input protection** — USB-C receptacle, CC1/CC2 sink resistors, VBUS fuse/protection, low-capacitance USB ESD protection, D+/D− to ESP32-S3 GPIO20/GPIO19.
2. **3V3 supply** — AP63203WU-7 candidate, manufacturer-recommended inductor and capacitors, input/output test points. Component values and footprints must be checked against the current datasheet and thermal/layout constraints before release.
3. **ESP32-S3 module** — U1 ESP32-S3-WROOM-1-N8; local decoupling; EN pull-up/reset circuit; GPIO0 boot switch; USB native data pins reserved.
4. **Synthetic pulse input** — J2 two-pin signal/GND only; PULSE_IN pulled up to 3V3 through 10 kΩ; 1 kΩ series resistor at MCU pin; optional unpopulated filter footprint; input explicitly restricted to 3.3 V lab logic/dry contact.
5. **Status and debug** — status LED with series resistor; UART/test header; test points for 5V, 3V3, GND, PULSE_IN, EN and BOOT.
6. **Cellular daughterboard interface** — UART_TX/RX, modem_EN, modem_RESET, modem_STATUS, GND, and separately supplied MODEM_VIN. No direct connection from the MCU 3V3 rail to modem power. Pinout and voltage levels must be reviewed against the selected modem's hardware design guide.
7. **Tamper switch** — enclosure microswitch to a GPIO with a defined pull-up/down and debounce strategy; no safety-critical action attached to this signal.

## Provisional signal map

| Signal | ESP32-S3 pin | Notes |
|---|---:|---|
| USB_D− | GPIO19 | Native USB; differential routing required |
| USB_D+ | GPIO20 | Native USB; differential routing required |
| PULSE_IN | GPIO4 | Synthetic 3.3 V lab signal only |
| STATUS_LED | GPIO5 | Through series resistor |
| I2C_SDA | GPIO6 | Optional peripheral expansion |
| I2C_SCL | GPIO7 | Optional peripheral expansion |
| MODEM_UART_TX | GPIO17 | Provisional; confirm module/peripheral conflicts |
| MODEM_UART_RX | GPIO18 | Provisional; confirm module/peripheral conflicts |
| BOOT | GPIO0 | Strapping pin; validate startup behavior |
| RESET_EN | EN | Datasheet-recommended enable circuit |
| TAMPER_SW | GPIO15 | Provisional; check pin constraints before freeze |

## Release gates

- Replace the existing graphical-only draft with a true KiCad native schematic containing embedded library symbols, real symbol pins, wires, labels, power symbols, and footprints.
- Run KiCad ERC and resolve all unintended violations; document every intentional exception.
- Build a PCB only from the validated schematic; assign footprints from manufacturer package drawings.
- Run DRC, inspect antenna keep-out and USB routing, check power/thermal loops, and review manufacturing outputs.
- Confirm the exact modem, power profile, regional radio support and certifications before approving the cellular daughterboard.
- Bench-test using a current-limited low-voltage supply and synthetic pulses only.
- Do not publish Gerbers as manufacturing-ready until ERC/DRC, BOM, footprint and physical bring-up checks are complete.

## Known limitations

This is not yet a complete electrical design. In particular, the regulator passives, USB protection parts, exact connector SKUs, modem module/power rail, footprints, and board stack-up require datasheet-backed engineering review. The design is not certified metrology and must not be used for billing-grade measurements without a validated meter pulse constant and a traceable calibration process.
