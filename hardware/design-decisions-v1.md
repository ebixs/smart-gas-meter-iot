# Smart Gas Meter IoT — Design Decisions v1

**Status:** provisional engineering baseline; not a manufacturing release  
**Scope:** low-voltage laboratory prototype evolving toward a regulated product

## Selected baseline

| Area | Decision | Reason / condition |
|---|---|---|
| Controller | ESP32-S3-WROOM-1-N8 candidate | Mature development ecosystem, USB debugging, sufficient processing for local buffering and telemetry |
| Cellular | Separate modem daughterboard / dedicated footprint-and-interface zone | Keeps the main PCB reusable while country, operator, bands, SIM form factor and certification path are verified |
| Cellular capability | Prefer LTE Cat 1 bis or LTE-M/NB-IoT only after coverage and operator support are verified | Do not assume a radio technology is available or suitable in the deployment region |
| Power | External certified low-voltage DC adapter for the lab prototype; reserve a separately engineered backup-battery option | Simplifies safe bench testing. Battery chemistry, charging and protection must be designed only after operating-time and environment targets are known |
| PCB | Larger 4-layer board, subject to layout and cost review | Easier routing, ground return, RF/power separation, test access and future service |
| Testability | Labeled test points for input power, 3V3, ground, reset, boot, UART, pulse simulator input, modem control/status and debug | Enables repeatable bring-up without connecting to a live meter |
| Meter interface | Isolated/protected, configurable low-voltage input; lab pulse simulator is the only input source for initial tests | Actual sensor type, pulse constant, voltage/current, isolation and legal metrology requirements are not yet known |
| Data continuity | Local timestamped queue, sequence IDs, retry/backoff, duplicate-safe server ingestion | Supports outages without silently losing or double-counting readings |
| Tamper/fault | Enclosure switch input, sensor-disconnect diagnostics where electrically supportable, reset reason and event log | Detection is diagnostic only; it does not itself establish a safety event |
| Analytics | Server-side baseline, anomaly flags, next-period forecast and seasonal comparison | Results are advisory; consumption anomalies alone cannot prove a gas leak |
| Billing | Reproducible invoice records with device/subscription IDs, prior/current readings, consumption, tariff version, totals, timestamps and QR verification | Must remain a draft/non-regulatory bill until metrology and jurisdictional requirements are validated |
| Security | Unique device identity, authenticated transport, protected credentials, signed/versioned firmware update strategy, least-privilege API | Exact secure provisioning and hardware root-of-trust choices remain to be validated |

## Explicitly not frozen yet

1. Exact cellular modem SKU, RF design, antenna and SIM/eSIM depend on target country, operator, supported bands, coverage, certifications and availability.
2. Power input range, connector and protection ratings require an agreed installation environment.
3. The real meter/sensor interface cannot be frozen without the sensor output specification and pulse constant.
4. Enclosure, tamper switch mechanics and antenna keep-out depend on physical packaging and RF validation.
5. Battery capacity and charging topology require an autonomy target and environmental profile.
6. PCB stack-up, trace widths, RF matching and manufacturing files require actual CAD layout, design-rule checks and manufacturer capability review.

## Release gates

- **Gate A — CAD:** native schematic and PCB files created; ERC/DRC results reviewed; footprint assignments and 3D models checked.
- **Gate B — bench:** power, reset/boot, USB/UART, pulse simulator, storage and modem tests recorded on low-voltage bench hardware.
- **Gate C — radio:** modem registration, antenna/RF, SIM, reconnect and data-loss/replay tests verified for the intended operator and region.
- **Gate D — product:** enclosure, environmental, EMC, radio, cybersecurity, metrology, gas-safety and local regulatory assessments completed by qualified parties.
- **Gate E — manufacturing:** BOM availability, approved alternates, Gerbers/drill, assembly drawings, pick-and-place, test fixture and production test records reviewed.

## Safety and approval boundary

This repository baseline is not a certified gas meter, leak detector, or production-ready device. Initial validation must use synthetic pulse signals and isolated low-voltage bench equipment only. Do not connect the prototype to a live gas pipe, operational meter, mains wiring, or an unknown field signal. No valve-control output is part of this design. No component order or fabrication is authorized by this document.
