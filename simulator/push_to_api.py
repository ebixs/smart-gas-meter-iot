"""Send synthetic pulse telemetry to a running local Smart Gas Meter IoT API."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from simulator.pulse_simulator import generate_readings


def send_readings(base_url: str, token: str, device_id: str, pulses: int, interval_ms: int) -> int:
    if not token:
        raise ValueError("provide --token or set SGM_API_TOKEN")
    sent = 0
    for reading in generate_readings(
        device_id=device_id,
        pulses=pulses,
        interval_ms=interval_ms,
        start_time=datetime.now(timezone.utc),
    ):
        body = json.dumps(reading, separators=(",", ":")).encode("utf-8")
        request = Request(
            base_url.rstrip("/") + "/api/v1/readings",
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                if not result.get("accepted"):
                    raise RuntimeError("API did not confirm record acceptance")
                sent += 1
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"API returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Could not reach API: {exc.reason}") from exc
    return sent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--token", default=os.environ.get("SGM_API_TOKEN", ""))
    parser.add_argument("--device-id", default="sgm-lab-001")
    parser.add_argument("--pulses", type=int, default=5)
    parser.add_argument("--interval-ms", type=int, default=1000)
    args = parser.parse_args()
    try:
        sent = send_readings(args.base_url, args.token, args.device_id, args.pulses, args.interval_ms)
    except (ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Accepted {sent} synthetic readings for {args.device_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
