"""End-to-end pipeline: simulate -> quality -> models -> forecasts -> anomalies -> invoices.

Usage (from the ``analytics`` directory):
    python -m sgm_analytics.pipeline --devices 240 --out output
    python -m sgm_analytics.pipeline --devices 240 --out output --publish ../docs/analytics
        (also simulates a second, held-out fleet with --holdout-seed, default 2026)

``--out`` receives the full working data (large, git-ignored). ``--publish``
writes the small, reviewable artefacts that live in the repository: report
figures, metrics tables, sample invoices and the dataset behind the static
dashboard demo.
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import anomaly, billing, fleet, models, quality

DEFAULT_SEED = 1405


@dataclass
class Run:
    fleet: fleet.Fleet
    intervals: pd.DataFrame
    daily: pd.DataFrame
    degree_days: pd.DataFrame
    daily_weather: pd.DataFrame
    dd_models: pd.DataFrame
    expected: pd.DataFrame
    forecast: models.ForecastResult
    alerts: pd.DataFrame
    evaluation: pd.DataFrame
    pattern: pd.DataFrame
    invoices: list[billing.Invoice]
    bill_month: tuple[int, int]
    timings: dict[str, float]


def last_complete_month(daily: pd.DataFrame) -> tuple[int, int]:
    """Latest Jalali month fully covered by the data."""
    from .jalali import next_month, to_jalali

    last_day = daily["date"].max()
    j = to_jalali((last_day + pd.Timedelta(days=1)).date())
    jy, jm = j.year, j.month
    # step back one month: the month containing the day after the data ends is incomplete
    jy, jm = (jy, jm - 1) if jm > 1 else (jy - 1, 12)
    start, end = billing.billing_period(jy, jm)
    if end > last_day + pd.Timedelta(days=1):
        jy, jm = (jy, jm - 1) if jm > 1 else (jy - 1, 12)
    assert next_month(jy, jm)  # sanity: valid month
    return jy, jm


def review_flags_for(alerts: pd.DataFrame, device_id: str, start: pd.Timestamp, end: pd.Timestamp) -> list[str]:
    """Alerts that overlap the billing period and should hold the invoice for review (BILL-006)."""
    if alerts.empty:
        return []
    hold = {"zero_while_expected", "sustained_drop", "counter_reset", "data_gap"}
    a = alerts[(alerts["device_id"] == device_id) & alerts["detector"].isin(hold)
               & (alerts["start"] < end.tz_localize(None) if alerts["start"].dt.tz is None else alerts["start"] < end)
               & (alerts["end"] > start.tz_localize(None) if alerts["end"].dt.tz is None else alerts["end"] > start)]
    return [f"analytics alert in period: {d} ({r})" for d, r in zip(a["detector"], a["reason"])]


def run(n_devices: int = 240, seed: int = DEFAULT_SEED, start: str = "2023-09-23", end: str = "2026-09-23",
        anomaly_share: float = 0.2) -> Run:
    timings: dict[str, float] = {}
    t = time.perf_counter()

    def lap(name: str) -> None:
        nonlocal t
        now = time.perf_counter()
        timings[name] = round(now - t, 2)
        t = now

    f = fleet.simulate_fleet(n_devices=n_devices, start=start, end=end, seed=seed, anomaly_share=anomaly_share)
    lap("simulate")
    iv = quality.interval_consumption(f.readings)
    daily = quality.daily_consumption(iv)
    lap("quality")
    dd = models.degree_days(f.weather)
    dw = models.with_weather(daily, f.devices, dd)
    ddm = models.fit_degree_day_models(dw)
    exp = models.expected_daily(dw, ddm)
    lap("degree_day_models")
    fc = models.forecast(dw, ddm)
    lap("forecast")
    alerts = anomaly.detect(exp, iv, f.events, ddm)
    evaluation = anomaly.evaluate(alerts, f.labels)
    lap("anomaly")
    jy, jm = last_complete_month(daily)
    pstart, pend = billing.billing_period(jy, jm)
    pattern = billing.consumption_pattern(daily, f.devices, before=pstart)
    invoices = [billing.bill_device_month(dev, iv, pattern, jy, jm,
                                          review_flags=review_flags_for(alerts, dev.device_id, pstart, pend))
                for _, dev in f.devices.iterrows()]
    lap("billing")
    return Run(f, iv, daily, dd, dw, ddm, exp, fc, alerts, evaluation, pattern, invoices, (jy, jm), timings)


def write_outputs(r: Run, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    r.fleet.devices.to_csv(out / "devices.csv", index=False)
    r.fleet.labels.to_csv(out / "labels.csv", index=False)
    r.fleet.events.to_csv(out / "events.csv", index=False)
    r.fleet.readings.to_parquet(out / "readings.parquet", index=False)
    r.daily.to_csv(out / "daily.csv.gz", index=False)
    r.dd_models.to_csv(out / "degree_day_models.csv", index=False)
    r.alerts.to_csv(out / "alerts.csv", index=False)
    r.evaluation.to_csv(out / "anomaly_evaluation.csv", index=False)
    r.forecast.metrics.to_csv(out / "forecast_metrics.csv", index=False)
    r.forecast.backtest.to_csv(out / "forecast_backtest.csv.gz", index=False)
    r.forecast.next_month.to_csv(out / "forecast_next_month.csv", index=False)
    inv_dir = out / "invoices"
    inv_dir.mkdir(exist_ok=True)
    for inv in r.invoices:
        (inv_dir / f"{inv.invoice_id}.json").write_text(billing.invoice_json(inv), encoding="utf-8")
    (out / "run.json").write_text(json.dumps({"timings_s": r.timings, "bill_month": r.bill_month,
                                              "devices": len(r.fleet.devices),
                                              "readings": len(r.fleet.readings)}, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--devices", type=int, default=240)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, default=Path("output"))
    parser.add_argument("--publish", type=Path, default=None, help="write report/dashboard artefacts here")
    parser.add_argument("--holdout-seed", type=int, default=2026,
                        help="second, untouched fleet used only to report how detectors generalise (0 = skip)")
    args = parser.parse_args()
    r = run(args.devices, args.seed)
    write_outputs(r, args.out)
    print(f"{len(r.fleet.devices)} devices, {len(r.fleet.readings):,} readings; timings {r.timings}")
    print(r.forecast.metrics.round(3).to_string(index=False))
    print(r.evaluation.round(2).to_string(index=False))
    if args.publish:
        from .report import publish

        holdout = run(args.devices, args.holdout_seed) if args.holdout_seed else None
        if holdout is not None:
            print("held-out fleet:")
            print(holdout.evaluation.round(2).to_string(index=False))
        publish(r, args.publish, holdout=holdout)
        print(f"published artefacts to {args.publish}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
