import io
import json
import unittest

from simulator.validate_telemetry import validate_record, validate_stream


VALID = {
    "schema_version": 1,
    "device_id": "lab-1",
    "sequence": 1,
    "timestamp": "2026-01-01T00:00:00.250000Z",
    "uptime_ms": 250,
    "pulse_count_total": 1,
    "input_mode": "simulated",
}

VALID_V2 = {
    "schema_version": 2, "device_id": "sgm-bench-01", "sequence": 4,
    "timestamp": "2026-09-22T20:30:00.000Z", "uptime_ms": 10805000, "pulse_count_total": 44,
    "input_mode": "bench_pulse", "record_type": "period_close", "time_source": "network",
    "fw_version": "0.3.0", "period": {"calendar": "jalali", "start": "1405/04", "months": 3},
    "events": ["late_close"], "rssi_dbm": -79,
}


class TelemetryV2ValidatorTests(unittest.TestCase):
    def test_accepts_firmware_period_close(self):
        self.assertEqual(validate_record(VALID_V2), [])

    def test_period_only_on_period_close(self):
        record = dict(VALID_V2, record_type="interval")
        self.assertTrue(any("period is only allowed" in e for e in validate_record(record)))
        record = dict(VALID_V2)
        del record["period"]
        self.assertTrue(any("period_close needs period" in e for e in validate_record(record)))

    def test_rejects_unknown_event_and_bad_rssi(self):
        errors = validate_record(dict(VALID_V2, events=["leak"], rssi_dbm=12))
        self.assertTrue(any("events" in e for e in errors))
        self.assertTrue(any("rssi_dbm" in e for e in errors))

    def test_zero_pulses_allowed_in_v2_only(self):
        self.assertEqual(validate_record(dict(VALID_V2, pulse_count_total=0)), [])


class TelemetryValidatorTests(unittest.TestCase):
    def test_accepts_valid_record(self):
        self.assertEqual(validate_record(VALID), [])

    def test_rejects_extra_or_missing_fields(self):
        record = dict(VALID)
        record.pop("device_id")
        record["unexpected"] = True
        errors = validate_record(record)
        self.assertTrue(any("missing fields: device_id" in error for error in errors))
        self.assertTrue(any("unexpected fields: unexpected" in error for error in errors))

    def test_rejects_bool_as_integer(self):
        record = dict(VALID, sequence=True)
        self.assertTrue(any("sequence must be an integer" in error for error in validate_record(record)))

    def test_rejects_non_utc_timestamp_and_real_input_mode(self):
        record = dict(VALID, timestamp="2026-01-01T00:00:00+03:30", input_mode="physical")
        errors = validate_record(record)
        self.assertTrue(any("ending in Z" in error for error in errors))
        self.assertTrue(any("input_mode" in error for error in errors))

    def test_stream_rejects_invalid_json_and_non_increasing_sequence(self):
        rows = [
            json.dumps(VALID),
            json.dumps(dict(VALID, sequence=1, pulse_count_total=2)),
            "{not json}",
        ]
        errors = validate_stream(io.StringIO("\n".join(rows)))
        self.assertTrue(any("must increase" in error for error in errors))
        self.assertTrue(any("invalid JSON" in error for error in errors))

    def test_stream_tracks_devices_independently(self):
        other = dict(VALID, device_id="lab-2", sequence=1)
        rows = [json.dumps(VALID), json.dumps(other), json.dumps(dict(VALID, sequence=2, pulse_count_total=2))]
        self.assertEqual(validate_stream(io.StringIO("\n".join(rows))), [])


if __name__ == "__main__":
    unittest.main()
