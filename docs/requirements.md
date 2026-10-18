# System Requirements and Acceptance Criteria

**Project:** Smart Gas Meter IoT  
**Status:** Draft v0.1  
**Scope:** Laboratory prototype using synthetic pulse data only

## 1. Purpose

Define a testable baseline for a portfolio-grade prototype demonstrating embedded event counting, reliable telemetry, consumption calculations, and reporting. This document does not define a certified gas meter.

## 2. Scope

### Included
- Generate synthetic meter pulses using a button or configurable low-voltage test generator.
- Count pulses on a microcontroller and maintain a cumulative count.
- Timestamp and buffer readings locally where practical.
- Transfer prototype readings to a Python API.
- Validate and store readings, calculate simulated consumption, and produce six-month reports.
- Provide automated tests, design documentation, and a reproducible development setup.

### Excluded
- Connection to a live gas pipe, valve, or utility meter.
- Modification of a certified meter or use as a billing authority.
- Safety-critical gas detection or shutoff functions.
- Claims of metrological accuracy, regulatory approval, or production readiness.

## 3. Functional requirements

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---:|---|
| REQ-001 | Synthetic pulse input | Must | Tests run without connecting to gas equipment. |
| REQ-002 | Reliable pulse counting | Must | A documented test of 1,000 generated pulses records the expected total under stated conditions. |
| REQ-003 | Input conditioning | Must | Mechanical switch bounce does not create unintended counts in the defined test. |
| REQ-004 | Cumulative counter | Must | Counter is monotonic during normal operation; reset behavior is explicit. |
| REQ-005 | Timestamped readings | Must | Each reading includes device ID, sequence, timestamp or uptime, and cumulative count. |
| REQ-006 | Local buffering | Should | Network interruption triggers queue/retry behavior without duplicate ingestion. |
| REQ-007 | Backend validation | Must | API rejects malformed payloads, negative counters, and invalid sequence regressions. |
| REQ-008 | Idempotent ingestion | Must | Replaying the same event does not duplicate consumption. |
| REQ-009 | Configurable conversion | Must | Pulse-to-volume conversion is configurable and labelled as a simulation parameter. |
| REQ-010 | Six-month report | Must | A test dataset produces a report for a selected six-month interval with defined boundaries. |
| REQ-011 | Dashboard | Should | User can inspect readings, simulated consumption, connection status, and reports. |
| REQ-012 | Security basics | Must | Secrets are not committed; remote transport and authentication are documented before deployment. |
| REQ-013 | Automated tests | Must | Conversion, duplicate handling, and period aggregation have tests. |
| REQ-014 | Documentation | Must | Setup, interfaces, BOM, limitations, and test procedures are documented. |

## 4. Non-functional targets

These are prototype targets to revise after bench testing:
- **Integrity:** readings must not silently reduce the cumulative count.
- **Traceability:** each reading is attributable to a device and unique event/sequence.
- **Recoverability:** network loss must not silently reset the local counter.
- **Maintainability:** firmware, API, and dashboard responsibilities remain separate.
- **Privacy:** use synthetic identifiers and sample data in the public repository.
- **Safety:** low-voltage bench circuits only; no live-gas testing.

## 5. Draft telemetry contract

```json
{
  "schema_version": 1,
  "device_id": "sgm-lab-001",
  "sequence": 42,
  "timestamp": "2026-01-15T12:30:00Z",
  "uptime_ms": 840000,
  "pulse_count_total": 1200,
  "input_mode": "simulated"
}
```

Rules:
- `pulse_count_total` is a cumulative integer, not a per-message delta.
- `sequence` increases for each emitted reading; retries reuse the same event identity.
- If the clock is not synchronized, preserve uptime and mark timestamp quality explicitly.
- Conversion from pulses to volume belongs in versioned configuration, not an undocumented firmware constant.

## 6. Six-month reporting rules

- Period start is inclusive and period end exclusive: `[start, end)`.
- The reporting timezone must be explicit.
- Calculate consumption from valid counter differences, not by summing cumulative readings.
- Flag counter resets, rollovers, gaps, and out-of-order readings.
- Tariff and currency are configuration inputs; no real tariff is assumed in sample data.

## 7. Milestones

1. Requirements and system interfaces.
2. Preliminary component shortlist and BOM.
3. Low-voltage pulse simulator specification and test plan.
4. Schematic and PCB design.
5. Firmware and API implementation.
6. Billing, dashboard, and analytics.
7. Validation, security review, and release documentation.

## 8. Open decisions

- MCU board and GPIO allocation.
- Cellular modem and SIM/provider compatibility for the intended test location.
- Power supply, enclosure, and environmental constraints.
- RTC and non-volatile storage strategy.
- Transport protocol and device authentication.
- Report export format.

Resolve these decisions after interface requirements and component availability are reviewed.
