import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

os.environ.setdefault("SGM_API_TOKEN", "test-only-token")

from backend import app as backend_app


class TelemetryApiTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        backend_app.DB_PATH = Path(self.tempdir.name) / "test.sqlite3"
        self.client = TestClient(backend_app.app)
        self.headers = {"Authorization": "Bearer test-only-token"}

    def tearDown(self):
        self.client.close()
        self.tempdir.cleanup()

    @staticmethod
    def reading(sequence=1, pulse_count=None, timestamp=None):
        return {
            "schema_version": 1,
            "device_id": "lab-1",
            "sequence": sequence,
            "timestamp": timestamp or f"2026-01-01T00:00:{sequence:02d}Z",
            "uptime_ms": sequence * 1000,
            "pulse_count_total": pulse_count if pulse_count is not None else sequence,
            "input_mode": "simulated",
        }

    def test_dashboard_is_served(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn("synthetic telemetry only", response.text)

    def test_health_is_explicitly_lab_only(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "synthetic-lab-only")

    def test_ingest_and_exact_duplicate_are_idempotent(self):
        payload = self.reading()
        first = self.client.post("/api/v1/readings", json=payload, headers=self.headers)
        second = self.client.post("/api/v1/readings", json=payload, headers=self.headers)
        self.assertEqual(first.status_code, 201)
        self.assertFalse(first.json()["duplicate"])
        self.assertEqual(second.status_code, 201)
        self.assertTrue(second.json()["duplicate"])

    def test_conflicting_duplicate_is_rejected(self):
        self.client.post("/api/v1/readings", json=self.reading(), headers=self.headers)
        conflict = self.client.post(
            "/api/v1/readings",
            json=self.reading(pulse_count=99),
            headers=self.headers,
        )
        self.assertEqual(conflict.status_code, 409)

    def test_latest_and_pulse_delta_report(self):
        self.client.post(
            "/api/v1/readings",
            json=self.reading(1, 10, "2026-01-01T00:00:00Z"),
            headers=self.headers,
        )
        self.client.post(
            "/api/v1/readings",
            json=self.reading(2, 14, "2026-01-01T00:00:01Z"),
            headers=self.headers,
        )
        latest = self.client.get("/api/v1/devices/lab-1/latest", headers=self.headers)
        self.assertEqual(latest.status_code, 200)
        self.assertEqual(latest.json()["pulse_count_total"], 14)

        report = self.client.get(
            "/api/v1/reports/consumption",
            headers=self.headers,
            params={
                "device_id": "lab-1",
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-01-01T00:00:03Z",
            },
        )
        self.assertEqual(report.status_code, 200)
        self.assertEqual(report.json()["pulse_delta"], 4)
        self.assertIsNone(report.json()["consumption_volume"])
        self.assertIn("not a bill", report.json()["note"])

    def test_report_discloses_missing_pre_range_baseline(self):
        self.client.post(
            "/api/v1/readings",
            json=self.reading(1, 10, "2026-01-01T00:00:01Z"),
            headers=self.headers,
        )
        self.client.post(
            "/api/v1/readings",
            json=self.reading(2, 15, "2026-01-01T00:00:02Z"),
            headers=self.headers,
        )
        response = self.client.get(
            "/api/v1/reports/consumption",
            headers=self.headers,
            params={
                "device_id": "lab-1",
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-01-01T00:00:03Z",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["baseline_source"], "first_reading_in_range")
        self.assertEqual(response.json()["pulse_delta"], 5)
        self.assertIn("not counted", response.json()["note"])

    def test_latest_endpoint_requires_bearer_token(self):
        response = self.client.get("/api/v1/devices/lab-1/latest")
        self.assertEqual(response.status_code, 401)

    def test_accepts_out_of_order_retry_when_counters_remain_monotonic(self):
        newer = self.reading(2, 20, "2026-01-01T00:00:02Z")
        older = self.reading(1, 10, "2026-01-01T00:00:01Z")
        self.assertEqual(
            self.client.post("/api/v1/readings", json=newer, headers=self.headers).status_code,
            201,
        )
        self.assertEqual(
            self.client.post("/api/v1/readings", json=older, headers=self.headers).status_code,
            201,
        )

    def test_rejects_decreasing_cumulative_pulse_count(self):
        self.client.post(
            "/api/v1/readings",
            json=self.reading(1, 10, "2026-01-01T00:00:01Z"),
            headers=self.headers,
        )
        response = self.client.post(
            "/api/v1/readings",
            json=self.reading(2, 9, "2026-01-01T00:00:02Z"),
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 409)

    def test_rejects_timestamp_that_conflicts_with_sequence_order(self):
        self.client.post(
            "/api/v1/readings",
            json=self.reading(2, 20, "2026-01-01T00:00:02Z"),
            headers=self.headers,
        )
        response = self.client.post(
            "/api/v1/readings",
            json=self.reading(1, 10, "2026-01-01T00:00:03Z"),
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 409)

    def test_ingestion_requires_bearer_token(self):
        response = self.client.post("/api/v1/readings", json=self.reading())
        self.assertEqual(response.status_code, 401)

    def test_rejects_non_simulated_input(self):
        payload = self.reading()
        payload["input_mode"] = "physical"
        response = self.client.post("/api/v1/readings", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 422)


    @staticmethod
    def reading_v2(sequence=1, pulses=0, timestamp=None, uptime=1000, **extra):
        record = {
            "schema_version": 2, "device_id": "sgm-bench-01", "sequence": sequence,
            "timestamp": timestamp or f"2026-09-22T20:{sequence:02d}:00.000Z", "uptime_ms": uptime,
            "pulse_count_total": pulses, "input_mode": "bench_pulse", "record_type": "interval",
            "time_source": "network", "fw_version": "0.3.0",
        }
        record.update(extra)
        return record

    def test_v2_period_close_round_trip(self):
        record = self.reading_v2(4, 44, "2026-09-22T20:30:00.000Z", record_type="period_close",
                                 period={"calendar": "jalali", "start": "1405/04", "months": 3},
                                 events=["counter_restored"], rssi_dbm=-79)
        response = self.client.post("/api/v1/readings", json=record, headers=self.headers)
        self.assertEqual(response.status_code, 201, response.text)
        latest = self.client.get("/api/v1/devices/sgm-bench-01/latest", headers=self.headers).json()
        self.assertEqual(latest["period"]["start"], "1405/04")
        self.assertEqual(latest["timestamp"], "2026-09-22T20:30:00.000000Z")

    def test_v2_rejects_period_on_interval_and_unknown_event(self):
        bad = self.reading_v2(period={"calendar": "jalali", "start": "1405/04", "months": 3})
        self.assertEqual(self.client.post("/api/v1/readings", json=bad, headers=self.headers).status_code, 422)
        bad = self.reading_v2(events=["gas_leak_confirmed"])
        self.assertEqual(self.client.post("/api/v1/readings", json=bad, headers=self.headers).status_code, 422)

    def test_v2_uptime_may_restart_after_reboot(self):
        before = self.reading_v2(1, 10, uptime=9_000_000)
        after = self.reading_v2(2, 10, uptime=50, events=["counter_restored", "brownout_reset"],
                                record_type="event")
        for record in (before, after):
            self.assertEqual(self.client.post("/api/v1/readings", json=record, headers=self.headers).status_code, 201)

    def test_batch_reports_each_record_and_never_blocks_on_one_bad_record(self):
        batch = [self.reading_v2(1, 5), {"schema_version": 2, "device_id": "x"}, self.reading_v2(3, 7),
                 self.reading_v2(4, 2)]  # 4 decreases the counter: conflict
        response = self.client.post("/api/v1/readings/batch", json=batch, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        statuses = [r["status"] for r in response.json()["results"]]
        self.assertEqual(statuses, ["stored", "invalid", "stored", "conflict"])
        again = self.client.post("/api/v1/readings/batch", json=batch[:1], headers=self.headers).json()
        self.assertEqual(again["results"][0]["status"], "duplicate")

    def test_batch_requires_token_and_bounds_size(self):
        self.assertEqual(self.client.post("/api/v1/readings/batch", json=[self.reading_v2()]).status_code, 401)
        too_many = [self.reading_v2(i, i) for i in range(1, 66)]
        self.assertEqual(
            self.client.post("/api/v1/readings/batch", json=too_many, headers=self.headers).status_code, 422)


if __name__ == "__main__":
    unittest.main()
