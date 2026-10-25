"""Unit tests for the analytics, billing and simulation layers (fast, synthetic)."""
import sys
import unittest
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sgm_analytics import anomaly, billing, fleet, models, quality  # noqa: E402
from sgm_analytics.jalali import JDate, month_length, to_gregorian, to_jalali  # noqa: E402


class JalaliTests(unittest.TestCase):
    def test_known_nowruz_dates(self):
        self.assertEqual(to_gregorian(1403, 1, 1), date(2024, 3, 20))
        self.assertEqual(to_gregorian(1404, 1, 1), date(2025, 3, 21))
        self.assertEqual(to_jalali(date(2025, 3, 21)), JDate(1404, 1, 1))

    def test_round_trip_every_day_for_three_years(self):
        d = date(2023, 3, 1)
        while d < date(2026, 3, 1):
            j = to_jalali(d)
            self.assertEqual(to_gregorian(j.year, j.month, j.day), d)
            d = d.fromordinal(d.toordinal() + 1)

    def test_month_lengths(self):
        self.assertEqual(month_length(1404, 1), 31)
        self.assertEqual(month_length(1404, 7), 30)
        self.assertEqual(month_length(1403, 12), 30)  # 1403 is a leap year
        self.assertEqual(month_length(1404, 12), 29)


def _readings(pulses, device="d1", start="2025-01-01", seqs=None):
    n = len(pulses)
    ts = pd.date_range(start, periods=n, freq="h", tz="UTC")
    return pd.DataFrame({"device_id": device, "ts_utc": ts,
                         "sequence": seqs if seqs is not None else np.arange(1, n + 1),
                         "pulse_count_total": pulses})


class QualityTests(unittest.TestCase):
    def test_interval_volume_from_cumulative_pulses(self):
        iv = quality.interval_consumption(_readings([100, 110, 135]))
        self.assertEqual(list(iv["volume_m3"].round(2).fillna(-1)), [-1, 0.10, 0.25])

    def test_gap_reset_and_duplicate_are_flagged_not_fixed(self):
        r = _readings([100, 110, 120, 5, 15], seqs=[1, 2, 5, 6, 7])
        r = pd.concat([r, r.iloc[[1]]])  # duplicate sequence 2
        iv = quality.interval_consumption(r)
        self.assertTrue(iv.loc[iv["sequence"] == 5, "flag_gap"].item())
        self.assertTrue(iv.loc[iv["sequence"] == 6, "flag_reset"].item())
        self.assertEqual(int(iv["duplicates_dropped"].max()), 1)
        # after a reset only the pulses counted since reboot are known
        self.assertAlmostEqual(iv.loc[iv["sequence"] == 6, "volume_m3"].item(), 0.04)

    def test_implausible_flow(self):
        iv = quality.interval_consumption(_readings([1, 1001]))  # 10 m3 in one hour > G4 Qmax 6 m3/h
        self.assertTrue(iv["flag_implausible"].iloc[1])


class BillingTests(unittest.TestCase):
    def test_tiers_follow_pattern_multiples(self):
        lines = billing._tier_breakdown(250.0, 100.0, billing.ILLUSTRATIVE_TARIFF, cold=True)
        self.assertEqual([line["quantity_m3"] for line in lines], [100.0, 50.0, 50.0, 50.0])
        prices = [t.price_cold for t in billing.ILLUSTRATIVE_TARIFF.tiers]
        self.assertEqual([line["price_per_m3"] for line in lines], prices)

    def test_consumption_inside_first_tier(self):
        lines = billing._tier_breakdown(40.0, 100.0, billing.ILLUSTRATIVE_TARIFF, cold=False)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["amount"], 40 * billing.ILLUSTRATIVE_TARIFF.tiers[0].price_warm)

    def test_billing_period_is_half_open_tehran_month(self):
        start, end = billing.billing_period(1404, 12)
        self.assertEqual(str(start.date()), "2026-02-20")
        self.assertEqual(str(end.date()), "2026-03-21")
        self.assertEqual(str(start.tz), "Asia/Tehran")

    def test_verification_token_is_signed_and_opaque(self):
        tok = billing.sign_token("INV-1", 123000, "1404/08", b"k")
        self.assertTrue(billing.verify_token("INV-1", 123000, "1404/08", tok, b"k"))
        self.assertFalse(billing.verify_token("INV-1", 124000, "1404/08", tok, b"k"))
        self.assertNotIn("INV", tok)


class DetectorTests(unittest.TestCase):
    def test_cusum_finds_small_persistent_shift_and_onset(self):
        rng = np.random.default_rng(0)
        z = pd.Series(np.concatenate([rng.normal(0, 1, 60), rng.normal(3, 1, 20), rng.normal(0, 1, 40)]))
        runs = anomaly._cusum_runs(z, k=1.0, h=10.0, min_len=4)
        self.assertEqual(len(runs), 1)
        start, end = runs[0]
        self.assertLessEqual(abs(start - 60), 3)
        self.assertGreaterEqual(end, 78)

    def test_cusum_quiet_on_noise(self):
        z = pd.Series(np.random.default_rng(1).normal(0, 1, 2000))
        self.assertEqual(anomaly._cusum_runs(z, k=1.0, h=10.0, min_len=4), [])

    def test_evaluate_counts_hits_with_slack(self):
        alerts = pd.DataFrame({"device_id": ["a", "b"], "detector": ["data_gap", "data_gap"],
                               "start": pd.to_datetime(["2025-01-03", "2025-02-01"]),
                               "end": pd.to_datetime(["2025-01-05", "2025-02-02"])})
        labels = pd.DataFrame({"device_id": ["a"], "anomaly": ["comms_outage"],
                               "start": ["2025-01-02"], "end": ["2025-01-04"], "detail": [""]})
        ev = anomaly.evaluate(alerts, labels).set_index("label")
        self.assertEqual(ev.loc["comms_outage", "recall"], 1.0)
        self.assertEqual(ev.loc["comms_outage", "precision"], 0.5)


class ModelTests(unittest.TestCase):
    def test_degree_day_fit_recovers_parameters(self):
        rng = np.random.default_rng(3)
        temp = rng.uniform(-5, 25, 300)  # daily mean temperature
        hdd16 = np.clip(16 - temp, 0, None)
        frame = {"device_id": "x", "quality": "ok", "volume_m3": 2.0 + 0.5 * hdd16 + rng.normal(0, 0.2, 300)}
        for b in models.BASES_C:  # degree-days for every candidate balance temperature
            frame[f"hdd_b{b}"] = np.clip(b - temp, 0, None)
        fit = models.fit_degree_day_models(pd.DataFrame(frame)).iloc[0]
        self.assertEqual(fit.base_c, 16)
        self.assertAlmostEqual(fit.base_m3_day, 2.0, delta=0.15)
        self.assertAlmostEqual(fit.heat_m3_per_hdd, 0.5, delta=0.02)


class SimulatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = fleet.simulate_fleet(n_devices=12, start="2024-10-01", end="2025-04-01", seed=7, anomaly_share=0.5)

    def test_deterministic_for_a_seed(self):
        again = fleet.simulate_fleet(n_devices=12, start="2024-10-01", end="2025-04-01", seed=7, anomaly_share=0.5)
        pd.testing.assert_frame_equal(self.f.readings, again.readings)

    def test_cumulative_counter_monotone_except_labelled_resets(self):
        resets = set(self.f.labels.loc[self.f.labels["anomaly"] == "counter_reset", "device_id"])
        for dev, g in self.f.readings.groupby("device_id", observed=True):
            if dev not in resets:
                self.assertTrue((g["pulse_count_total"].diff().dropna() >= 0).all(), dev)

    def test_winter_uses_more_gas_than_autumn(self):
        d = self.f.true_daily.copy()
        d["month"] = d["date"].dt.month
        self.assertGreater(d[d["month"] == 1]["true_m3"].mean(), 2 * d[d["month"] == 10]["true_m3"].mean())

    def test_labels_use_known_fault_types(self):
        self.assertTrue(set(self.f.labels["anomaly"]) <= set(fleet.ANOMALY_TYPES))
        self.assertGreater(len(self.f.labels), 0)


if __name__ == "__main__":
    unittest.main()
