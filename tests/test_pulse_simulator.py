import unittest
from datetime import datetime, timezone

from simulator.pulse_simulator import generate_readings


class GenerateReadingsTests(unittest.TestCase):
    def test_emits_cumulative_counts_and_sequences(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        readings = list(generate_readings("lab-1", 3, 250, start))

        self.assertEqual([r["sequence"] for r in readings], [1, 2, 3])
        self.assertEqual([r["pulse_count_total"] for r in readings], [1, 2, 3])
        self.assertEqual([r["uptime_ms"] for r in readings], [250, 500, 750])
        self.assertTrue(all(r["input_mode"] == "simulated" for r in readings))

    def test_records_match_telemetry_contract_fields(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        readings = list(generate_readings("lab-1", 1, 250, start))
        self.assertEqual(
            set(readings[0]),
            {
                "schema_version",
                "device_id",
                "sequence",
                "timestamp",
                "uptime_ms",
                "pulse_count_total",
                "input_mode",
            },
        )
        self.assertEqual(readings[0]["schema_version"], 1)
        self.assertEqual(readings[0]["timestamp"], "2026-01-01T00:00:00.250Z")

    def test_zero_pulses_emits_no_readings(self):
        self.assertEqual(list(generate_readings("lab-1", 0)), [])

    def test_rejects_invalid_parameters(self):
        with self.assertRaises(ValueError):
            list(generate_readings(" ", 1))
        with self.assertRaises(ValueError):
            list(generate_readings("lab-1", -1))
        with self.assertRaises(ValueError):
            list(generate_readings("lab-1", 1, -10))

    def test_requires_timezone_aware_start_time(self):
        with self.assertRaises(ValueError):
            list(generate_readings("lab-1", 1, start_time=datetime(2026, 1, 1)))


if __name__ == "__main__":
    unittest.main()
