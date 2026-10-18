# Board v0.1 — Preliminary BOM

**Status:** Candidate BOM for schematic development only. Not purchase-ready until all manufacturer part numbers, footprints, tolerances, ratings, and availability are verified.

| Ref. | Qty. | Candidate / requirement | Notes |
|---|---:|---|---|
| U1 | 1 | ESP32-S3-WROOM-1-N8 | Module; verify exact module and footprint revision |
| U2 | 1 | AP63203WU-7 | Fixed 3.3 V synchronous buck; implement per current manufacturer datasheet |
| L1 | 1 | Buck inductor selected from AP63203 datasheet design guidance | Confirm inductance, saturation current, RMS rating, DCR, footprint |
| C1 | 1 | 10 µF input capacitor, ceramic, voltage rating appropriate for 5 V rail | Verify effective capacitance under DC bias |
| C2, C3 | 2 | 22 µF output capacitors, ceramic, suitable voltage rating | Datasheet application circuit candidate; verify effective capacitance and stability |
| C4 | 1 | 100 nF bootstrap capacitor | Place between BST and SW as specified by regulator datasheet |
| C5+ | As required | Local 100 nF and bulk decoupling capacitors | Confirm against Espressif module recommendations and rail transient tests |
| J1 | 1 | USB-C receptacle, USB 2.0 device | Exact footprint TBD |
| RCC1, RCC2 | 2 | USB-C CC pull-down resistors | Select according to USB Type-C device/sink requirements |
| U3 | 1 | Low-capacitance USB 2.0 ESD protector | Select package/capacitance and confirm line mapping |
| J2 | 1 | 2-pin test connector | PULSE_IN and GND only; lab use |
| SW1 | 1 | Momentary normally-open push button | BOOT to GND |
| SW2 | 1 | Momentary normally-open push button | EN/RESET per module reference design |
| RPU1 | 1 | 10 kΩ | PULSE_IN pull-up to 3V3 |
| RS1 | 1 | 1 kΩ | Series resistor on PULSE_IN |
| C_PULSE | 1 footprint | DNP initially; optional debounce/filter capacitor | Value only after pulse-rate and edge testing |
| D1 | 1 | Low-current status LED | Color and package TBD |
| RLED1 | 1 | LED series resistor | Calculate for chosen LED and GPIO current |
| TP1–TP6 | 6 | Test points | VBUS, 3V3, GND, EN, PULSE_IN, spare/debug |
| J3 | 1 | Expansion header | GND, 3V3, I2C, reserved UART |
| PCB | 1 | 2-layer FR-4 candidate | Stack-up and impedance guidance from board house; copper/widths to be calculated |

## Exclusions for v0.1

- Cellular modem and SIM holder
- RTC and microSD (expansion header reserved)
- Any field pulse interface or connection to live gas equipment
- Battery/charger and mains supply
- Certified measurement, safety, or billing components

## Purchasing gate

Before ordering, attach exact manufacturer part numbers and datasheet revisions, verify every footprint and pinout, calculate the power stage from the regulator datasheet, and complete KiCad ERC/DRC. This BOM is not an instruction to order parts yet.
