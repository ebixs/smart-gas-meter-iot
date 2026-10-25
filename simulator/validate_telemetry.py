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


V2_REQUIRED = REQUIRED_FIELDS | {"record_type", "time_source", "fw_version"}
V2_OPTIONAL = {"period", "events", "rssi_dbm", "supply_mv"}
V2_EVENTS = {
    "tamper_open", "tamper_closed", "counter_restored", "store_empty", "queue_overflow",
    "implausible_rate", "late_close", "brownout_reset", "watchdog_reset",
}
DEVICE_ID_V2 = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
PERIOD_START = re.compile(r"^1[34][0-9]{2}/(0[1-9]|1[0-2])$")


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _common_checks(record: dict, prefix: str, min_pulses: int) -> list[str]:
    errors: list[str] = []

    def integer(name: str, minimum: int) -> None:
        value = record.get(name)
        if not _is_int(value) or value < minimum:
            errors.append(prefix + f"{name} must be an integer >= {minimum}")

    integer("sequence", 1)
    integer("uptime_ms", 0)
    integer("pulse_count_total", min_pulses)
    timestamp = record.get("timestamp")
    if not isinstance(timestamp, str) or not UTC_TIMESTAMP.fullmatch(timestamp):
        errors.append(prefix + "timestamp must be an ISO 8601 UTC timestamp ending in Z")
    else:
        try:
            datetime.fromisoformat(timestamp[:-1] + "+00:00")
        except ValueError:
            errors.append(prefix + "timestamp is not a valid date-time")
    return errors


def _validate_v1(record: dict, prefix: str) -> list[str]:
    errors: list[str] = []
    keys = set(record)
    missing = REQUIRED_FIELDS - keys
    extra = keys - REQUIRED_FIELDS
    if missing:
        errors.append(prefix + "missing fields: " + ", ".join(sorted(missing)))
    if extra:
        errors.append(prefix + "unexpected fields: " + ", ".join(sorted(extra)))
    device_id = record.get("device_id")
    if not isinstance(device_id, str) or not device_id.strip() or len(device_id) > 128:
        errors.append(prefix + "device_id must be a non-empty string of at most 128 characters")
    errors.extend(_common_checks(record, prefix, 1))
    if record.get("input_mode") != "simulated":
        errors.append(prefix + "input_mode must be 'simulated'")
    return errors


def _validate_v2(record: dict, prefix: str) -> list[str]:
    """Contract v2 (schemas/telemetry-v2.schema.json), produced by the bench firmware."""
    errors: list[str] = []
    keys = set(record)
    missing = V2_REQUIRED - keys
    extra = keys - V2_REQUIRED - V2_OPTIONAL
    if missing:
        errors.append(prefix + "missing fields: " + ", ".join(sorted(missing)))
    if extra:
        errors.append(prefix + "unexpected fields: " + ", ".join(sorted(extra)))
    device_id = record.get("device_id")
    if not isinstance(device_id, str) or not DEVICE_ID_V2.fullmatch(device_id):
        errors.append(prefix + "device_id must be 1-64 characters of A-Z a-z 0-9 . _ -")
    errors.extend(_common_checks(record, prefix, 0))
    if record.get("input_mode") not in ("simulated", "bench_pulse"):
        errors.append(prefix + "input_mode must be 'simulated' or 'bench_pulse'")
    record_type = record.get("record_type")
    if record_type not in ("interval", "period_close", "event"):
        errors.append(prefix + "record_type must be interval, period_close or event")
    if record.get("time_source") not in ("network", "sntp", "backfilled"):
        errors.append(prefix + "time_source must be network, sntp or backfilled")
    fw = record.get("fw_version")
    if not isinstance(fw, str) or not 1 <= len(fw) <= 32:
        errors.append(prefix + "fw_version must be a string of 1-32 characters")
    period = record.get("period")
    if record_type == "period_close":
        if (not isinstance(period, dict) or set(period) != {"calendar", "start", "months"}
                or period.get("calendar") != "jalali" or not isinstance(period.get("start"), str)
                or not PERIOD_START.fullmatch(period["start"]) or period.get("months") not in (1, 3)
                or isinstance(period.get("months"), bool)):
            errors.append(prefix + "period_close needs period {calendar: jalali, start: YYYY/MM, months: 1|3}")
    elif period is not None:
        errors.append(prefix + "period is only allowed on period_close records")
    if "events" in record:
        events = record["events"]
        if (not isinstance(events, list) or not events or len(set(map(str, events))) != len(events)
                or not all(isinstance(e, str) and e in V2_EVENTS for e in events)):
            errors.append(prefix + "events must be a non-empty list of unique known event names")
    if "rssi_dbm" in record and (not _is_int(record["rssi_dbm"]) or not -140 <= record["rssi_dbm"] <= 0):
        errors.append(prefix + "rssi_dbm must be an integer between -140 and 0")
    if "supply_mv" in record and (not _is_int(record["supply_mv"]) or not 1 <= record["supply_mv"] <= 20000):
        errors.append(prefix + "supply_mv must be an integer between 1 and 20000")
    return errors


def validate_record(record: object, line_number: int = 1) -> list[str]:
    """Return validation errors for one record; an empty list means valid.

    schema_version 1 is the simulator contract; 2 is the bench-firmware contract.
    """
    prefix = f"line {line_number}: "
    if not isinstance(record, dict):
        return [prefix + "record must be a JSON object"]
    version = record.get("schema_version")
    if _is_int(version) and version == 2:
        return _validate_v2(record, prefix)
    errors = _validate_v1(record, prefix)
    if version != 1 or isinstance(version, bool):
        errors.insert(0, prefix + "schema_version must equal integer 1 or 2")
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
