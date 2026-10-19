# MCU pinout and test points — v0.2 proposal

This is a provisional allocation, not a verified electrical schematic. Confirm every assignment against the exact ESP32-S3 module, boot-strapping constraints, USB routing, and the final modem/interface circuit before layout.

| Signal | Proposed MCU signal | Test / connector point | Notes |
|---|---|---|---|
| Native USB D- | GPIO19 | USB-C D- | Route as controlled differential pair per Espressif guidance; ESD protection at connector |
| Native USB D+ | GPIO20 | USB-C D+ | Route as controlled differential pair per Espressif guidance; ESD protection at connector |
| Simulated pulse input | GPIO4 | TP_PULSE / J_PULSE | Low-voltage simulator only; external input conditioning/isolation not frozen |
| Status LED | GPIO5 | TP_LED | Series resistor and LED polarity to be defined in schematic |
| I2C SDA | GPIO6 | TP_SDA / expansion header | Pull-ups and bus voltage to be defined |
| I2C SCL | GPIO7 | TP_SCL / expansion header | Pull-ups and bus voltage to be defined |
| Modem UART TX/RX | GPIO17 / GPIO18 candidate | TP_MODEM_TX/RX | Verify modem I/O voltage, UART direction and flow control; add level translation if required |
| Modem enable/reset/status | TBD | TP_MODEM_EN/RST/STAT | Reserve dedicated GPIOs only after exact modem selection |
| Enclosure tamper | TBD | TP_TAMPER | Debounce/filter and fail-state to be specified |
| Debug UART | UART pins TBD | TP_TX/TP_RX/GND | Keep accessible without interfering with modem UART |
| 3.3 V rail | — | TP_3V3 | Measure at MCU/module supply, not only at regulator |
| Modem rail | — | TP_VMODEM | Separate rail; peak-current sizing and transient response depend on modem SKU |
| Ground | — | Multiple GND pads | Add return points near power and RF-related circuitry |

## Layout/testability rules

- Place test pads where a probe can touch without shorting adjacent pads.
- Label test points in silkscreen and in the test procedure.
- Keep USB, modem UART, simulated pulse, and debug interfaces identifiable.
- Reserve mounting holes and a repeatable fixture datum.
- Add accessible current-measurement provision for the modem rail and MCU rail.
- Do not connect the pulse input to a real meter until a qualified interface design is reviewed.
