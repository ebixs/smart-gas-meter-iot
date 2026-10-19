# Development API — synthetic telemetry only

The initial API uses FastAPI and SQLite to exercise the telemetry contract without hardware or an external database.

## Run locally

Use Python 3.12 or newer in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt "httpx>=0.27,<1"
export SGM_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uvicorn backend.app:app --reload
```

Open `http://127.0.0.1:8000/dashboard` for the lab dashboard or `http://127.0.0.1:8000/docs` for the interactive API documentation. In a second terminal, send a short synthetic test batch with `python simulator/push_to_api.py --device-id lab-run-001 --pulses 5`; it reads the bearer token from `SGM_API_TOKEN`. Use a new device ID for a fresh sequence-1 test run. The default database is `data/telemetry.sqlite3`; set `SGM_DATABASE_PATH` to change it.

## Endpoints

- `GET /health` — reports that this is a synthetic lab API.
- `POST /api/v1/readings` — validates and stores a synthetic telemetry record (requires `Authorization: Bearer $SGM_API_TOKEN`).
- `GET /api/v1/devices/{device_id}/latest` — returns the highest-sequence record for a device (requires the bearer token).
- `GET /api/v1/reports/consumption?device_id=lab-1&start=2026-01-01T00:00:00Z&end=2026-01-02T00:00:00Z` — returns pulse delta, not gas volume (requires the bearer token).

## Data integrity behavior

The unique key is `(device_id, sequence)`. Re-sending the same payload is idempotent; sending a different payload for an already-used sequence returns HTTP 409. This supports retry-safe delivery from an offline queue while preserving duplicate conflict detection. Delayed records may arrive out of order, but the API checks neighboring sequence numbers so timestamps, cumulative pulse count and uptime remain monotonic as sequence increases.

The report only calculates a pulse-counter delta. It returns `baseline_source` so consumers can tell whether the baseline came from the last reading before the range or the first reading inside it. When there is no pre-range reading, pulses before the first in-range sample cannot be counted. It deliberately returns `consumption_volume: null` because a verified meter-specific pulse constant has not been provided. Do not use the result as an invoice or as evidence of actual gas volume.

## Important security limitation

**Development-only, not production-ready.** This API currently uses one shared bearer token for development; it does not provide per-device identities or credential provisioning. It also lacks TLS configuration, rate limiting, retention controls, or an audited production database setup. Do not expose it to the public internet or connect it to an operational meter. Before deployment, implement and review device identity and credential provisioning, authenticated transport, authorization, input/rate limits, key rotation, database migrations/backups, observability, and threat modeling.

All records are restricted to `input_mode: simulated`. This API does not validate physical electronics, certify metrology, detect leaks, or establish regulatory compliance.
