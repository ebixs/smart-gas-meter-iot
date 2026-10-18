"""Generate deterministic synthetic telemetry for backend and billing tests.

This is a software fixture. It does not generate electrical pulses and must not
be treated as validation of physical meter hardware.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from typing import Iterator


def generate_readings(
    device_id: str,
    pulses: int,
    interval_ms: int = 1000,
    start_time: datetime | None = None,
) -> Iterator[dict[str, object]]:
    """Yield one cumulative telemetry reading per simulated pulse."""
    if not device_id.strip():
        raise ValueError("device_id must not be empty")
    if pulses < 0:
        raise ValueError("pulses must be >= 0")
    if interval_ms < 0:
        raise ValueError("interval_ms must be >= 0")

    start = start_time or datetime.now(timezone.utc)
    if start.tzinfo is None:
        raise ValueError("start_time must be timezone-aware")

    start = start.astimezone(timezone.utc)
    for count in range(1, pulses + 1):
        timestamp = start + timedelta(milliseconds=count * interval_ms)
        yield {
            "schema_version": 1,
            "device_id": device_id,
            "sequence": count,
            "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
            "uptime_ms": count * interval_ms,
            "pulse_count_total": count,
            "input_mode": "simulated",
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Emit synthetic Smart Gas Meter IoT telemetry as JSON Lines."
    )
    parser.add_argument("--device-id", default="sgm-lab-001")
    parser.add_argument("--pulses", type=int, default=10)
    parser.add_argument("--interval-ms", type=int, default=1000)
    args = parser.parse_args()

    for reading in generate_readings(args.device_id, args.pulses, args.interval_ms):
        print(json.dumps(reading, separators=(",", ":")))


if __name__ == "__main__":
    main()
