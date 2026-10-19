# AI Analytics, Billing, Energy, and Tamper Requirements — Draft 0.1

**Status:** Functional requirements for future implementation. Not evidence that the features already exist in software.

## Analytics
- AI-001: Ingest readings with device identity, monotonic sequence, timestamp/time quality, firmware version, and sensor/power quality state.
- AI-002: Detect missing, duplicate, out-of-order, reset, and implausible readings before analytics.
- AI-003: Flag unusual consumption against a per-device baseline; provide reason, time window, baseline, deviation, and data-quality indicator.
- AI-004: Forecast next-month consumption with uncertainty bounds and retain model version, training window, and evaluation metrics.
- AI-005: Compare seasonal and month-over-month usage only when comparable valid data exists.
- AI-006: An anomaly flag is decision support, not proof of a gas leak.
- AI-007: Measure false positives/negatives and monitor model drift before user-facing alert activation.
- AI-008: Apply documented privacy, retention, and access controls to customer data.

## Billing
- BILL-001: Use versioned tariff records with effective dates, currency, unit, rounding rule, and jurisdiction.
- BILL-002: Define billing periods as half-open intervals [start, end) with explicit timezone.
- BILL-003: Preserve raw readings and a reproducible calculation trace for each invoice.
- BILL-004: PDF/print invoice includes customer/subscription reference, device ID, previous/current reading, period consumption, tariff, amount/currency, issue date, and invoice ID.
- BILL-005: QR code opens an authenticated invoice view using an opaque or signed identifier; do not embed personal data directly.
- BILL-006: Mark estimated, missing, reset, or suspect data; never silently turn invalid telemetry into a final bill.
- BILL-007: Invoice corrections are auditable with reason, actor, timestamp, and original invoice reference.
- BILL-008: Official billing remains blocked until metrology, tariff, legal, and jurisdiction requirements are approved.

## Tamper and device health
- TAMP-001: Log boot/reset reason, brownout, clock changes, sensor disconnect, enclosure switch, storage fault, modem fault, and firmware update where hardware supports them.
- TAMP-002: Events include monotonic sequence, timestamp quality, firmware version, and device identity.
- TAMP-003: Protect transport with authenticated encryption and per-device credentials.
- TAMP-004: Provide server-side duplicate detection and an append-oriented audit trail.
- TAMP-005: Define failure behavior for RTC, battery, storage, and network faults.
- TAMP-006: Software logs cannot guarantee tamper proofing if an attacker can physically replace or reprogram the device.
- TAMP-007: Do not infer a gas leak from tamper switches or consumption anomalies.

## Energy
- EN-001: Measure current in sleep, sensing, modem attach, transmit, retry, and recovery states.
- EN-002: Report supply/battery state only when supported by suitable measurement circuitry.
- EN-003: Set low-battery thresholds and retention/retry policy from battery chemistry and required service interval.
- EN-004: Publish a battery-life estimate only after testing with declared signal strength, reporting interval, temperature, and capacity.
