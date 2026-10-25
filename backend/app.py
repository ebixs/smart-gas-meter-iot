"""Development API for synthetic lab telemetry; not production-hardened.

Data endpoints require a shared development bearer token. Per-device identity,
TLS deployment, rate limiting, and metrology certification are not provided.
Bind only to a trusted local lab environment until controls are reviewed.
"""
from __future__ import annotations

import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, Iterator, Literal, Union

from fastapi import Body, Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, StrictInt, TypeAdapter, ValidationError, field_validator, model_validator

DB_PATH = Path(os.environ.get("SGM_DATABASE_PATH", "data/telemetry.sqlite3"))
API_TOKEN = os.environ.get("SGM_API_TOKEN", "")
bearer_scheme = HTTPBearer(auto_error=False)
app = FastAPI(title="Smart Gas Meter IoT Lab API", version="0.2.0")
BATCH_MAX = 64


class TelemetryReading(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    device_id: str = Field(min_length=1, max_length=128)
    sequence: StrictInt = Field(ge=1)
    timestamp: datetime
    uptime_ms: StrictInt = Field(ge=0)
    pulse_count_total: StrictInt = Field(ge=1)
    input_mode: Literal["simulated"]

    @field_validator("device_id")
    @classmethod
    def device_id_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("device_id must not be blank")
        return value

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
            raise ValueError("timestamp must be UTC")
        return value.astimezone(timezone.utc)


class Period(BaseModel):
    model_config = ConfigDict(extra="forbid")

    calendar: Literal["jalali"]
    start: str = Field(pattern=r"^1[34][0-9]{2}/(0[1-9]|1[0-2])$")
    months: Literal[1, 3]


EventName = Literal[
    "tamper_open", "tamper_closed", "counter_restored", "store_empty", "queue_overflow",
    "implausible_rate", "late_close", "brownout_reset", "watchdog_reset",
]


class TelemetryReadingV2(BaseModel):
    """Bench-firmware contract (schemas/telemetry-v2.schema.json)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2]
    device_id: str = Field(pattern=r"^[A-Za-z0-9._-]{1,64}$")
    sequence: StrictInt = Field(ge=1)
    timestamp: datetime
    uptime_ms: StrictInt = Field(ge=0)
    pulse_count_total: StrictInt = Field(ge=0)
    input_mode: Literal["simulated", "bench_pulse"]
    record_type: Literal["interval", "period_close", "event"]
    time_source: Literal["network", "sntp", "backfilled"]
    fw_version: str = Field(min_length=1, max_length=32)
    period: Period | None = None
    events: list[EventName] | None = Field(default=None, min_length=1)
    rssi_dbm: StrictInt | None = Field(default=None, ge=-140, le=0)
    supply_mv: StrictInt | None = Field(default=None, ge=1, le=20000)

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
            raise ValueError("timestamp must be UTC")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def period_matches_type(self) -> "TelemetryReadingV2":
        if (self.record_type == "period_close") != (self.period is not None):
            raise ValueError("period is required on period_close records and only allowed there")
        if self.events is not None and len(set(self.events)) != len(self.events):
            raise ValueError("events must be unique")
        return self


AnyReading = Annotated[Union[TelemetryReading, TelemetryReadingV2], Field(discriminator="schema_version")]
READING_ADAPTER: TypeAdapter[Any] = TypeAdapter(AnyReading)


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    try:
        db.execute(
            """CREATE TABLE IF NOT EXISTS readings (
                device_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                uptime_ms INTEGER NOT NULL,
                pulse_count_total INTEGER NOT NULL,
                input_mode TEXT NOT NULL CHECK (input_mode IN ('simulated', 'bench_pulse')),
                payload_json TEXT NOT NULL,
                PRIMARY KEY (device_id, sequence)
            )"""
        )
        db.commit()
        yield db
    finally:
        db.close()


def row_to_dict(row: sqlite3.Row) -> dict[str, object]:
    return json.loads(row["payload_json"])


def require_api_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    if not API_TOKEN:
        raise HTTPException(status_code=503, detail="API token is not configured")
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Bearer token required")
    if not secrets.compare_digest(credentials.credentials, API_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid bearer token")


@app.get("/dashboard", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "synthetic-lab-only"}


def store_reading(reading: TelemetryReading | TelemetryReadingV2) -> dict[str, object]:
    """Idempotent insert with ordering checks. Raises HTTPException(409) on conflicts."""
    payload = reading.model_dump(mode="json", exclude_none=True)
    payload["timestamp"] = reading.timestamp.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    # uptime_ms restarts at every reboot of a v2 device, so it only orders v1 simulator streams.
    check_uptime = reading.schema_version == 1
    with connection() as db:
        existing = db.execute(
            "SELECT payload_json FROM readings WHERE device_id=? AND sequence=?",
            (reading.device_id, reading.sequence),
        ).fetchone()
        if existing:
            if existing["payload_json"] != payload_json:
                raise HTTPException(
                    status_code=409,
                    detail="sequence already exists with a different payload",
                )
            return {"accepted": True, "duplicate": True, "device_id": reading.device_id, "sequence": reading.sequence}
        previous = db.execute(
            """SELECT sequence, timestamp, uptime_ms, pulse_count_total FROM readings
               WHERE device_id=? AND sequence < ? ORDER BY sequence DESC LIMIT 1""",
            (reading.device_id, reading.sequence),
        ).fetchone()
        following = db.execute(
            """SELECT sequence, timestamp, uptime_ms, pulse_count_total FROM readings
               WHERE device_id=? AND sequence > ? ORDER BY sequence ASC LIMIT 1""",
            (reading.device_id, reading.sequence),
        ).fetchone()
        if previous and (
            payload["timestamp"] < previous["timestamp"]
            or (check_uptime and reading.uptime_ms < previous["uptime_ms"])
            or reading.pulse_count_total < previous["pulse_count_total"]
        ):
            raise HTTPException(
                status_code=409,
                detail="timestamp, uptime and cumulative pulse count must not decrease by sequence",
            )
        if following and (
            payload["timestamp"] > following["timestamp"]
            or (check_uptime and reading.uptime_ms > following["uptime_ms"])
            or reading.pulse_count_total > following["pulse_count_total"]
        ):
            raise HTTPException(
                status_code=409,
                detail="record conflicts with a later sequence's timestamp, uptime or pulse count",
            )
        db.execute(
            """INSERT INTO readings
            (device_id, sequence, timestamp, uptime_ms, pulse_count_total, input_mode, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                reading.device_id, reading.sequence, payload["timestamp"],
                reading.uptime_ms, reading.pulse_count_total, reading.input_mode, payload_json,
            ),
        )
        db.commit()
    return {"accepted": True, "duplicate": False, "device_id": reading.device_id, "sequence": reading.sequence}


@app.post("/api/v1/readings", status_code=201)
def ingest_reading(
    reading: AnyReading, _: None = Depends(require_api_token)
) -> dict[str, object]:
    return store_reading(reading)


@app.post("/api/v1/readings/batch")
def ingest_batch(
    records: list[dict[str, Any]] = Body(..., min_length=1, max_length=BATCH_MAX),
    _: None = Depends(require_api_token),
) -> dict[str, object]:
    """Store-and-forward upload from the firmware: each record is validated and stored
    on its own, so one bad record is reported instead of blocking the device queue."""
    results: list[dict[str, object]] = []
    for index, raw in enumerate(records):
        try:
            reading = READING_ADAPTER.validate_python(raw)
        except ValidationError as exc:
            results.append({"index": index, "status": "invalid",
                            "detail": [e["msg"] for e in exc.errors()][:3]})
            continue
        try:
            outcome = store_reading(reading)
            results.append({"index": index, "sequence": reading.sequence,
                            "status": "duplicate" if outcome["duplicate"] else "stored"})
        except HTTPException as exc:
            results.append({"index": index, "sequence": reading.sequence, "status": "conflict",
                            "detail": exc.detail})
    stored = sum(r["status"] in ("stored", "duplicate") for r in results)
    return {"received": len(records), "stored": stored, "results": results}


@app.get("/api/v1/devices/{device_id}/latest")
def latest_reading(device_id: str, _: None = Depends(require_api_token)) -> dict[str, object]:
    with connection() as db:
        row = db.execute(
            "SELECT payload_json FROM readings WHERE device_id=? ORDER BY sequence DESC LIMIT 1",
            (device_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="device has no readings")
    return row_to_dict(row)


@app.get("/api/v1/reports/consumption")
def consumption_report(
    device_id: str = Query(min_length=1, max_length=128),
    start: datetime = Query(),
    end: datetime = Query(),
    _: None = Depends(require_api_token),
) -> dict[str, object]:
    if start.tzinfo is None or end.tzinfo is None:
        raise HTTPException(status_code=422, detail="start and end must include a timezone")
    start_utc = start.astimezone(timezone.utc)
    end_utc = end.astimezone(timezone.utc)
    if end_utc <= start_utc:
        raise HTTPException(status_code=422, detail="end must be after start")
    start_text = start_utc.isoformat(timespec="microseconds").replace("+00:00", "Z")
    end_text = end_utc.isoformat(timespec="microseconds").replace("+00:00", "Z")
    with connection() as db:
        baseline = db.execute(
            """SELECT pulse_count_total FROM readings
               WHERE device_id=? AND timestamp < ?
               ORDER BY timestamp DESC, sequence DESC LIMIT 1""",
            (device_id, start_text),
        ).fetchone()
        rows = db.execute(
            """SELECT payload_json FROM readings
               WHERE device_id=? AND timestamp >= ? AND timestamp <= ?
               ORDER BY timestamp, sequence""",
            (device_id, start_text, end_text),
        ).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="no readings in requested time range")
    records = [row_to_dict(row) for row in rows]
    initial = baseline["pulse_count_total"] if baseline else records[0]["pulse_count_total"]
    final = records[-1]["pulse_count_total"]
    delta = max(0, int(final) - int(initial))
    return {
        "device_id": device_id,
        "start": start_text,
        "end": end_text,
        "reading_count": len(records),
        "initial_pulse_count": initial,
        "baseline_source": "last_reading_before_start" if baseline else "first_reading_in_range",
        "final_pulse_count": final,
        "pulse_delta": delta,
        "consumption_volume": None,
        "note": "Pulse delta only. If baseline_source is first_reading_in_range, pulses before the first in-range reading are not counted. Volume requires a verified meter-specific pulse constant; this report is not a bill.",
    }
