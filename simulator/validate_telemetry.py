"""Validate JSON Lines telemetry against the versioned lab contract.

This intentionally uses the Python standard library only. It validates synthetic
records; it does not certify physical meter measurements or electrical hardware.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import TextIO

REQUIRED_FIELDS = {
    "schema_version",
    "device_id",
    "sequence",
    "timestamp",
    "uptime_ms",
    "pulse_count_total",
    "input_mode",
}
UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


def validate_record(record: object, line_number: int = 1) -> list[str]:
    """Return validation errors for one record; an empty list means valid."""
    errors: list[str] = []
    prefix = f"line {line_number}: "
    if not isinstance(record, dict):
        return [prefix + "record must be a JSON object"]

    keys = set(record)
    missing = REQUIRED_FIELDS - keys
    extra = keys - REQUIRED_FIELDS
    if missing:
        errors.append(prefix + "missing fields: " + ", ".join(sorted(missing)))
    if extra:
        errors.append(prefix + "unexpected fields: " + ", ".join(sorted(extra)))

    def integer(name: str, minimum: int) -> None:
        value = record.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            errors.append(prefix + f"{name} must be an integer >= {minimum}")

    if record.get("schema_version") != 1 or isinstance(record.get("schema_version"), bool):
        errors.append(prefix + "schema_version must equal integer 1")
    device_id = record.get("device_id")
    if not isinstance(device_id, str) or not device_id.strip() or len(device_id) > 128:
        errors.append(prefix + "device_id must be a non-empty string of at most 128 characters")
    integer("sequence", 1)
    integer("uptime_ms", 0)
    integer("pulse_count_total", 1)

    timestamp = record.get("timestamp")
    if not isinstance(timestamp, str) or not UTC_TIMESTAMP.fullmatch(timestamp):
        errors.append(prefix + "timestamp must be an ISO 8601 UTC timestamp ending in Z")
    else:
        try:
            datetime.fromisoformat(timestamp[:-1] + "+00:00")
        except ValueError:
            errors.append(prefix + "timestamp is not a valid date-time")

    if record.get("input_mode") != "simulated":
        errors.append(prefix + "input_mode must be 'simulated'")
    return errors


def validate_stream(stream: TextIO) -> list[str]:
    """Validate each JSONL record and basic sequence monotonicity per device."""
    errors: list[str] = []
    last_sequence: dict[str, int] = {}
    for line_number, line in enumerate(stream, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: invalid JSON ({exc.msg})")
            continue
        record_errors = validate_record(record, line_number)
        errors.extend(record_errors)
        if record_errors or not isinstance(record, dict):
            continue
        device_id = record["device_id"]
        sequence = record["sequence"]
        previous = last_sequence.get(device_id)
        if previous is not None and sequence <= previous:
            errors.append(
                f"line {line_number}: sequence for {device_id!r} must increase "
                f"(previous {previous}, current {sequence})"
            )
        last_sequence[device_id] = sequence
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate synthetic telemetry JSON Lines against the repository contract."
    )
    parser.add_argument("path", nargs="?", default="-", help="JSONL file path, or - for stdin")
    args = parser.parse_args()
    if args.path == "-":
        errors = validate_stream(sys.stdin)
    else:
        try:
            with Path(args.path).open(encoding="utf-8") as stream:
                errors = validate_stream(stream)
        except OSError as exc:
            print(f"Cannot read {args.path}: {exc}", file=sys.stderr)
            return 2
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Telemetry validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
