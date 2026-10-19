# Cellular Modem Daughterboard Interface — Draft 0.1

**Status:** Interface proposal only. No modem SKU is selected and no RF design is released.

## Why modular?
Country, operator, supported bands, SIM options, and deployed radio technology are not confirmed. A replaceable modem board reduces the risk of locking the main PCB to an unsupported regional variant.

## Proposed logical interface
| Interface | Requirement |
|---|---|
| Supply | Dedicated modem rail sized from the exact module peak-current specification; separate from MCU 3V3 |
| Ground | Low-impedance return and RF grounding per module reference design |
| UART TX/RX | Voltage levels matched to the modem; translate if required |
| Enable/reset | MCU-controlled lines with safe default states |
| Status | Modem status/network indication if supported |
| SIM | SIM or eSIM selected with carrier and module SKU |
| RF | 50-ohm path and antenna arrangement per exact module reference design |
| Debug | Test pads for modem supply, GND, UART, reset and enable |
| ESD | Protection appropriate to accessible SIM/service/RF interfaces |

## Candidate radio classes
| Class | Potential fit | Must resolve |
|---|---|---|
| LTE Cat 1 / Cat 1 bis | Conventional LTE service and moderate data | Regional bands, availability, peak current |
| LTE-M / Cat M1 | Low-power telemetry where deployed | Operator support, roaming, provisioning |
| NB-IoT / Cat NB2 | Small periodic payloads where deployed | Latency, mobility, coverage, operator provisioning |

No technology is selected responsibly without target operator and location information.

## Electrical gates
- Never power the modem from the MCU 3.3 V regulator.
- Follow the exact module supply ripple, peak current, decoupling, UART level, SIM, reset, and RF reference design.
- Place bulk/high-frequency decoupling at the modem supply pins and verify regulator transient response.
- Reserve antenna connector and keep-out; use matching components only as recommended by the module manufacturer.
- Test the actual antenna with the enclosure.
- Module approvals do not automatically certify the complete end product.

## Open items
- [ ] Country and operator
- [ ] Supported bands and network deployment
- [ ] Exact orderable modem SKU
- [ ] SIM or eSIM
- [ ] Antenna, connector, placement, and enclosure
- [ ] Peak-current budget and power rail
- [ ] Certification and product lifecycle
