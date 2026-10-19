# Production-Oriented Product Architecture — Draft 0.1

**Status:** Architecture requirements, not a released product design. The target is engineering prototype → verified pilot → compliance review → deployment.
**Safety boundary:** Prototype only; no live gas wiring, gas-line connection, or gas-valve control.

## Product scope
- Embedded controller plus independently powered cellular modem.
- Sensor interface chosen only after the actual meter output, pulse constant, isolation needs, and tamper policy are documented.
- Local non-volatile buffering, monotonic sequence numbers, clock-quality tracking, secure transport, and retry after outages.
- Server-side consumption analytics, anomaly flags, forecasts, invoice generation, and audit history.
- Tamper/event logging and device-health telemetry.
- Serviceable PCB with test points, programming/debug interface, replaceable cellular antenna, and test-friendly component placement.

“Operational product” is a target, not a readiness claim. Metering accuracy, installation safety, radio approval, cybersecurity, environmental qualification, and billing/legal acceptance require separate verification.

## Hardware partition
### Main controller board
- MCU candidate: ESP32-S3-WROOM-1-N8, pending lifecycle, temperature-grade, and antenna review.
- Cellular modem: a replaceable modem daughterboard for the first spin until country/operator/bands and exact modem SKU are confirmed.
- USB-C for programming/service and bench power in the prototype.
- Protected low-voltage laboratory pulse input. The actual field sensor interface remains undefined until meter output and isolation requirements are known.
- Non-volatile event/data storage footprint, subject to retention and endurance requirements.
- Optional RTC/backup supply if time accuracy requirements cannot be met by the system time strategy.
- Separate logic, modem, and optional battery power domains with test points.
- Enclosure tamper-switch input and sensor-disconnect detection, subject to final sensor design.
- Status indicators and expansion/debug header.

### Cellular technology decision
Evaluate LTE Cat 1/Cat 1 bis, LTE-M (Cat M1), and NB-IoT/Cat NB2 against the target operator, country, bands, SIM/eSIM, module lifecycle, antenna, latency, and peak current. A module supporting a radio standard does not prove the target carrier deploys it.

**No modem SKU is frozen yet.** Do not freeze the RF footprint until the deployment operator and exact modem SKU are known. See the [modem daughterboard interface](../hardware/modem-daughterboard-interface.md).

## Power strategy
The power source is an open product requirement; do not assume mains or battery-only operation without deployment evidence.
- Define input source and allowed voltage range before selecting input protection and regulators.
- Size the modem supply for the selected module’s transmit-current peaks; never power the modem from the MCU 3.3 V rail.
- Measure idle, sensing, modem attach, transmit, retry, and fault-state current.
- Include battery fuel gauge/voltage sensing only after battery chemistry is selected.
- Add reverse-polarity, transient, ESD, and brownout protection for the declared input and environment.
- Queue readings locally during network outages and retry with backoff.
- Define low-battery behavior and data retention before field testing.
- Do not claim energy optimization until power profiles are measured.

## Data and security
- Unique per-device identity and credentials; no shared global device secret.
- Authenticated encrypted transport, credential rotation/revocation, and signed firmware update with recovery/rollback plan.
- Every reading includes schema version, device ID, monotonic sequence, timestamp and time quality, uptime, cumulative count, sensor/power state, and firmware version.
- Store readings durably before confirming local capture; deduplicate server-side by device ID and sequence.
- Log boot/reset reason, clock adjustment, sensor disconnect, enclosure switch, storage errors, modem faults, and firmware updates.
- Tamper logs should be append-oriented and cryptographically protected where feasible; firmware logs alone cannot guarantee tamper resistance against physical access.

## AI, billing, and alerts
- Run consumption analytics on the server, not as the sole safety mechanism on the meter.
- Flag unusual consumption against per-device baselines and seasonality; show reason, time window, comparison baseline, and data quality.
- Forecast next-month consumption with uncertainty intervals and backtesting; store model version and evaluation metrics.
- Compare seasonal periods only when valid comparable data exists.
- A high-consumption anomaly is not proof of a gas leak. Leak detection requires an appropriate independent sensor and safety system.
- Use versioned tariff records, explicit timezone and billing period, documented rounding, raw-reading traceability, and auditable invoice corrections.
- PDF/print invoices should include customer/subscription reference, device ID, previous/current readings, usage, tariff, amount/currency, issue date, and invoice ID.
- QR code should point to an authenticated invoice page using an opaque or signed identifier, not expose personal data directly.

## Decisions required before schematic freeze
- [ ] Deployment country and target cellular operator(s).
- [ ] Supported network technology, bands, exact modem SKU, and SIM/eSIM.
- [ ] Power source, input voltage, battery chemistry/capacity if any, and service interval.
- [ ] Actual meter/sensor output, pulse constant, isolation/protection requirements, pulse width and maximum rate.
- [ ] Installation temperature, humidity, ingress protection, vibration, enclosure, and service access.
- [ ] Time accuracy, outage buffering duration, and acceptable data loss.
- [ ] Applicable metrology, radio, EMC, electrical safety, cybersecurity, and gas-installation standards identified by qualified specialists.
- [ ] Tariff jurisdiction and official billing rules.
- [ ] Tamper threat model and retention policy.

## Verification gates
1. Review schematic against exact manufacturer datasheets.
2. Run ERC/DRC and verify every footprint/pin map.
3. Calculate modem peak-current margin and thermal performance.
4. Review RF layout and antenna placement for the exact module.
5. Bench bring-up with current-limited supply and synthetic pulse fixture only.
6. Measure power profile and test outage/retry behavior.
7. Test secure update, credential handling, storage failures, and event logging.
8. Complete applicable environmental, EMC, radio, metrology, and installation validation before deployment.

## References
- [Espressif ESP32-S3 hardware design guidelines](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/index.html)
- [Espressif ESP32-S3-WROOM-1 documentation](https://www.espressif.com/en/products/modules/esp32/esp32-s3-wroom-1)
- [Quectel BG95 series specification](https://www.quectel.com/content/uploads/2024/03/Quectel_BG95_Series_LPWA_Specification_V2.0-4-1.pdf)

References are component research only; they do not establish local network coverage or certify the end product.
