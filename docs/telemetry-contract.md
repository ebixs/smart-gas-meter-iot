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
