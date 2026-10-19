"""Minimal development API for synthetic lab telemetry.

Not production-secure: no device authentication, TLS termination, rate limiting,
or metrology certification is provided here. Bind only to a trusted local lab
environment until those controls are implemented and reviewed.
"""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

DB_PATH = Path(os.environ.get("SGM_DATABASE_PATH", "data/telemetry.sqlite3"))
app = FastAPI(title="Smart Gas Meter IoT Lab API", version="0.1.0")


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
                input_mode TEXT NOT NULL CHECK (input_mode = 'simulated'),
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "synthetic-lab-only"}


@app.post("/api/v1/readings", status_code=201)
def ingest_reading(reading: TelemetryReading) -> dict[str, object]:
    payload = reading.model_dump(mode="json")
    payload["timestamp"] = reading.timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
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


@app.get("/api/v1/devices/{device_id}/latest")
def latest_reading(device_id: str) -> dict[str, object]:
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
) -> dict[str, object]:
    if start.tzinfo is None or end.tzinfo is None:
        raise HTTPException(status_code=422, detail="start and end must include a timezone")
    start_utc = start.astimezone(timezone.utc)
    end_utc = end.astimezone(timezone.utc)
    if end_utc <= start_utc:
        raise HTTPException(status_code=422, detail="end must be after start")
    start_text = start_utc.isoformat().replace("+00:00", "Z")
    end_text = end_utc.isoformat().replace("+00:00", "Z")
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
        "final_pulse_count": final,
        "pulse_delta": delta,
        "consumption_volume": None,
        "note": "Pulse delta only. Volume requires a verified meter-specific pulse constant; this report is not a bill.",
    }
