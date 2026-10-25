# Telemetry Contract (Draft)

This contract defines the JSON record emitted by the software pulse simulator. It is a lab-only interface for development and tests, not a certified metrology format.

- Machine-readable schema: [`schemas/telemetry.schema.json`](../schemas/telemetry.schema.json)
- Producer: [`simulator/pulse_simulator.py`](../simulator/pulse_simulator.py)
- Input mode is explicitly `simulated`; do not use these records as real consumption measurements.
- `sequence` increases for each emitted record within one simulator run.
- `pulse_count_total` is cumulative in the generated sample stream.
- `timestamp` is ISO 8601 UTC (ending in `Z`) for simulator-generated records.
- `uptime_ms` is relative to the beginning of the generated stream.
- `schema_version` allows future contract changes to be introduced explicitly.

## Backend handling requirements

1. Validate each payload before persistence.
2. Treat the pair `(device_id, sequence)` as a candidate idempotency key for the prototype; confirm the final persistence strategy before implementation.
3. Detect duplicate or out-of-order sequence values instead of silently counting them as new consumption.
4. Never infer a meter reset or a real-world volume from this synthetic pulse count alone.
5. Record device time and server receipt time separately in a future ingestion implementation.
6. Define authentication, retention, and access controls before exposing an ingestion endpoint.

The schema and handling notes are a draft interface. They do not mean that an API or database ingestion path is implemented.

## Contract v2 (bench firmware)

- Machine-readable schema: [`schemas/telemetry-v2.schema.json`](../schemas/telemetry-v2.schema.json)
- Producer: the ESP32-S3 firmware in [`firmware/`](../firmware/README.md) and its host demo (`sgm_host demo`).
- Adds `record_type` (`interval`, `period_close`, `event`), `time_source`, `fw_version`, and optional
  `period`, `events`, `rssi_dbm`, `supply_mv`. `input_mode` may be `bench_pulse` for a lab signal on J2.
- `period_close` is the device's own billing reading: the cumulative count frozen at 00:00 Iran time on the
  first day of a Jalali month (monthly) or season (Farvardin, Tir, Mehr, Dey).
- `sequence` is persisted before a record is queued, so it increases across reboots. `uptime_ms` restarts at
  every boot, so the backend does not use it to order v2 records.
- Records are uploaded in batches to `POST /api/v1/readings/batch` (at most 64). The response reports each
  record as `stored`, `duplicate`, `invalid` or `conflict`, so one bad record cannot block the device queue.
- `simulator/validate_telemetry.py` validates both versions; v1 records keep their original rules.
