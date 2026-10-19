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
            json=self.reading(1, 10, "2026-01-01T00:00:01Z"),
            headers=self.headers,
        )
        self.client.post(
            "/api/v1/readings",
            json=self.reading(2, 14, "2026-01-01T00:00:02Z"),
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

    def test_ingestion_requires_bearer_token(self):
        response = self.client.post("/api/v1/readings", json=self.reading())
        self.assertEqual(response.status_code, 401)

    def test_rejects_non_simulated_input(self):
        payload = self.reading()
        payload["input_mode"] = "physical"
        response = self.client.post("/api/v1/readings", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
