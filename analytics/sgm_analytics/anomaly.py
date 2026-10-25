"""Anomaly and fault detection with measured precision/recall (AI-003, AI-006, AI-007).

Each alert carries what AI-003 asks for: reason, time window, baseline, deviation
and a data-quality indicator. Detectors are deliberately explainable:

  continuous_flow    CUSUM detects a persistent upward shift of the night-time minimum flow
                     (a leak-LIKE pattern; decision support only, never proof of a leak)
  zero_while_expected no pulses for >= 2 days while the weather model expects real use
                     (stuck/disconnected sensor)
  sustained_drop     several days at a steady 10-45 % of the weather-expected level
                     (possible meter interference; travel drops to ~0 instead);
                     confidence boosted by enclosure-open events
  usage_spike        a day far above the weather-expected level
  data_gap           readings missing (communications outage)
  counter_reset      cumulative counter went backwards
  unusual_day        Isolation Forest on daily residual features (generic, lower confidence)

``evaluate`` matches alerts to the simulator's ground-truth labels and reports
event-level precision and recall per category, so false positives/negatives are
measured before any alert would be shown to a user (AI-007).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import HuberRegressor

TZ = "Asia/Tehran"
LABEL_TO_DETECTOR = {
    "leak_like_flow": "continuous_flow",
    "stuck_meter": "zero_while_expected",
    "comms_outage": "data_gap",
    "magnet_tamper": "sustained_drop",
    "usage_spike": "usage_spike",
    "counter_reset": "counter_reset",
}


def _runs(flags: pd.Series, min_len: int) -> list[tuple[int, int]]:
    """Index ranges [i, j) of consecutive True values with length >= min_len."""
    out, start = [], None
    values = flags.to_numpy()
    for i, v in enumerate(values):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start >= min_len:
                out.append((start, i))
            start = None
    if start is not None and len(values) - start >= min_len:
        out.append((start, len(values)))
    return out


def daily_shape(intervals: pd.DataFrame) -> pd.DataFrame:
    """Per device-day: minimum flow between 01:00 and 05:00 local, and the coefficient of
    variation of hourly flow (scale-invariant: interference scales a day down but keeps
    its cooking/hot-water peaks; an empty home loses them)."""
    iv = intervals[~intervals["first_reading"] & ~intervals["flag_gap"] & ~intervals["flag_reset"]].copy()
    local = iv["ts_utc"].dt.tz_convert(TZ)
    iv["date"] = local.dt.normalize()
    iv["night"] = (local.dt.hour >= 1) & (local.dt.hour <= 5)
    hour = local.dt.hour
    iv["peak"] = hour.between(6, 8) | hour.between(18, 21)
    g = iv.groupby(["device_id", "date"], observed=True)["volume_m3"]
    shape = pd.DataFrame({"cv_day": g.std() / g.mean().clip(lower=1e-6)})
    night = iv[iv["night"]].groupby(["device_id", "date"], observed=True)["volume_m3"]
    peak = iv[iv["peak"]].groupby(["device_id", "date"], observed=True)["volume_m3"].mean()
    shape["night_min_m3h"] = night.min()
    # Cooking/hot-water peaks relative to the night level. Interference scales the whole
    # day (ratio kept); an empty home loses its peaks (ratio collapses towards ~1).
    shape["peak_to_night"] = peak / night.mean().clip(lower=0.005)
    return shape.reset_index()


def _hetero_scale(resid: pd.Series, level: pd.Series, ok: pd.Series, floor: float) -> pd.Series:
    """Residual scale that grows with the expected level (winter days are noisier).

    Fits |resid| ~ c0 + c1 * level robustly on OK days and converts mean absolute
    deviation to a standard-deviation-like scale (x 1.25 for a normal distribution).
    """
    use = ok & resid.notna() & level.notna()
    if use.sum() < 60:
        return pd.Series(max(floor, float(resid[use].abs().median() or floor) * 1.25), index=resid.index)
    x = level[use].to_numpy().reshape(-1, 1)
    model = HuberRegressor(epsilon=1.35, max_iter=300).fit(x, resid[use].abs())
    scale = model.predict(level.fillna(level.median()).to_numpy().reshape(-1, 1)) * 1.25
    return pd.Series(np.clip(scale, floor, None), index=resid.index)


def _cusum_runs(z: pd.Series, k: float, h: float, min_len: int) -> list[tuple[int, int]]:
    """One-sided CUSUM for a persistent upward shift in standardized residuals ``z``.

    Returns index ranges [start, end) where the statistic exceeded ``h``; ``start`` is
    the day the statistic last left zero (estimated onset) and ``end`` is one past the
    last day that still pushed the statistic up. The statistic itself decays slowly
    after a large shift ends, so its reset day would overstate how long the fault lasted.
    """
    out, s, onset, last_up, alarm = [], 0.0, None, None, False
    values = z.fillna(0.0).to_numpy()

    def close() -> None:
        if alarm and onset is not None and last_up is not None and last_up + 1 - onset >= min_len:
            out.append((onset, last_up + 1))

    for i, v in enumerate(values):
        s = max(0.0, s + v - k)
        if s == 0.0:
            close()
            onset, last_up, alarm = None, None, False
        else:
            if onset is None:
                onset = i
            if v > k:
                last_up = i
            if s > h:
                alarm = True
    close()
    return out


def _night_baseline(g: pd.DataFrame) -> pd.Series:
    """Expected night minimum from night temperature (heating keeps a floor in winter)."""
    ok = g["quality"].eq("ok") & g["night_min_m3h"].notna()
    x = np.clip(g["base_c"] - g["t_night_c"], 0, None).to_numpy().reshape(-1, 1)
    if ok.sum() < 60:
        return pd.Series(0.01, index=g.index)
    model = HuberRegressor(epsilon=1.35, max_iter=300).fit(x[ok.to_numpy()], g.loc[ok, "night_min_m3h"])
    return pd.Series(np.clip(model.predict(x), 0, None), index=g.index)


def detect(expected: pd.DataFrame, intervals: pd.DataFrame, events: pd.DataFrame,
           dd_models: pd.DataFrame) -> pd.DataFrame:
    """Run all detectors. ``expected`` = output of models.expected_daily."""
    alerts: list[dict] = []
    shape = daily_shape(intervals)
    exp = expected.merge(shape, on=["device_id", "date"], how="left").sort_values(["device_id", "date"])
    tamper_days = set()
    if len(events):
        ev = events[events["event"] == "enclosure_open"]
        tamper_days = {(d, pd.Timestamp(t).normalize()) for d, t in zip(ev["device_id"], ev["ts_local"])}

    for dev, g in exp.groupby("device_id", observed=True):
        g = g.reset_index(drop=True)
        ok = g["quality"] == "ok"
        mad = float(g["resid_mad"].iloc[0]) if g["resid_mad"].notna().any() else 0.5

        def add(kind, i, j, reason, baseline, deviation, confidence):
            alerts.append({"device_id": dev, "detector": kind, "start": g["date"].iloc[i],
                           "end": g["date"].iloc[j - 1] + pd.Timedelta(days=1), "reason": reason,
                           "baseline": round(float(baseline), 3), "deviation": round(float(deviation), 3),
                           "data_quality": "ok" if ok.iloc[i:j].all() else "mixed", "confidence": confidence})

        # Continuous flow: night minimum above what night-time heating explains.
        night_exp = _night_baseline(g)
        night_resid = g["night_min_m3h"] - night_exp
        night_scale = _hetero_scale(night_resid, night_exp, ok, floor=0.008)
        z_night = (night_resid / night_scale).where(ok)
        for i, j in _cusum_runs(z_night, k=1.0, h=10.0, min_len=4):
            add("continuous_flow", i, j,
                "night-time minimum flow shifted up and stayed above what night heating explains (CUSUM)",
                night_exp.iloc[i:j].mean(), g["night_min_m3h"].iloc[i:j].mean(), "medium")

        # Zero pulses while the weather model expects clear consumption.
        zero = (g["volume_m3"] <= 0.0) & (g["expected_m3"] > 1.5) & ok
        for i, j in _runs(zero, 2):
            add("zero_while_expected", i, j, "no pulses although weather-expected use is high",
                g["expected_m3"].iloc[i:j].mean(), 0.0, "high")

        # Sustained drop that keeps the day's shape (interference), unlike an empty home.
        # Interference removes a share of the pulses but gas keeps flowing, so the counted
        # level settles at a steady fraction of normal. An empty home (travel) drops to
        # almost nothing and a dead sensor to exactly zero (handled above), so the band
        # 10-45 % of the weather-expected level separates the three.
        drop = g["ratio"].between(0.10, 0.45) & (g["expected_m3"] > 3) & ok
        typical_cv = g.loc[ok & g["ratio"].between(0.7, 1.4), "cv_day"].median()
        for i, j in _runs(drop, 5):
            # Interference scales the whole hourly profile, so its variability (CV) over the
            # window stays near the household's normal; an empty home leaves erratic,
            # spiky use (CV ~2x normal). Backtested on the simulator's labels.
            run_cv = g["cv_day"].iloc[i:j].median()
            if pd.notna(typical_cv) and pd.notna(run_cv) and run_cv > 1.5 * typical_cv:
                continue
            boosted = any((dev, g["date"].iloc[k]) in tamper_days for k in range(max(0, i - 2), min(len(g), i + 3)))
            add("sustained_drop", i, j,
                "consumption far below weather-expected level while the daily usage pattern persists"
                + ("; enclosure opened" if boosted else ""),
                g["expected_m3"].iloc[i:j].mean(), g["ratio"].iloc[i:j].mean(), "high" if boosted else "medium")

        # Spike relative to expected, scaled by the device's own variability.
        day_resid = g["volume_m3"] - g["expected_m3"]
        day_scale = _hetero_scale(day_resid, g["expected_m3"], ok, floor=max(0.2, 0.5 * mad))
        # Spikes are sudden: also require a jump against the median of the previous week,
        # so a household whose model under-fits a whole season is not flagged day after day.
        prior_week = g["volume_m3"].where(ok).shift(1).rolling(7, min_periods=4).median()
        spike = (g["ratio"] > 2.0) & (day_resid / day_scale > 6.0) & (g["volume_m3"] > 1.8 * prior_week) & ok
        for i, j in _runs(spike, 1):
            add("usage_spike", i, j, "daily use far above weather-expected level",
                g["expected_m3"].iloc[i:j].mean(), g["ratio"].iloc[i:j].mean(), "medium")

    # Data-quality alerts straight from the quality layer.
    iv = intervals.copy()
    iv["local"] = iv["ts_utc"].dt.tz_convert(TZ)
    for _, r in iv[iv["flag_gap"]].iterrows():
        missing_h = float(r["hours"]) - 1
        alerts.append({"device_id": r["device_id"], "detector": "data_gap",
                       "start": (r["local"] - pd.Timedelta(hours=missing_h)).normalize(), "end": r["local"].normalize() + pd.Timedelta(days=1),
                       "reason": f"{missing_h:.0f} h of readings missing", "baseline": 1.0,
                       "deviation": missing_h, "data_quality": "gap", "confidence": "high"})
    for _, r in iv[iv["flag_reset"]].iterrows():
        alerts.append({"device_id": r["device_id"], "detector": "counter_reset", "start": r["local"].normalize(),
                       "end": r["local"].normalize() + pd.Timedelta(days=1), "reason": "cumulative counter went backwards",
                       "baseline": 0, "deviation": 0, "data_quality": "reset", "confidence": "high"})

    # Generic unusual days (Isolation Forest on residual features, OK days only).
    feats = exp[exp["quality"] == "ok"].copy()
    feats["log_ratio"] = np.log(feats["ratio"].clip(0.01, 50))
    feats["night"] = feats["night_min_m3h"].fillna(0)
    feats["cv"] = feats["cv_day"].fillna(0)
    feats["dow"] = feats["date"].dt.dayofweek
    x = feats[["log_ratio", "night", "cv", "hdd_dev"]].fillna(0).to_numpy()
    iso = IsolationForest(n_estimators=200, contamination=0.0005, random_state=0).fit(x)
    feats["iso"] = iso.predict(x)
    for _, r in feats[feats["iso"] == -1].iterrows():
        alerts.append({"device_id": r["device_id"], "detector": "unusual_day", "start": r["date"],
                       "end": r["date"] + pd.Timedelta(days=1), "reason": "isolation-forest outlier on residual features",
                       "baseline": round(float(r["expected_m3"]), 3), "deviation": round(float(r["ratio"]), 3),
                       "data_quality": "ok", "confidence": "low"})

    out = pd.DataFrame(alerts)
    if len(out):
        out = out.sort_values(["device_id", "start"]).reset_index(drop=True)
    return out


def evaluate(alerts: pd.DataFrame, labels: pd.DataFrame, slack_days: int = 2) -> pd.DataFrame:
    """Event-level precision/recall per detector against simulator ground truth."""
    lab = labels.copy()
    lab["start"] = pd.to_datetime(lab["start"]).dt.normalize()
    lab["end"] = pd.to_datetime(lab["end"]).dt.normalize() + pd.Timedelta(days=1)
    slack = pd.Timedelta(days=slack_days)
    rows = []
    for label, det in LABEL_TO_DETECTOR.items():
        a = alerts[alerts["detector"] == det] if len(alerts) else alerts
        lt = lab[lab["anomaly"] == label]
        detected = 0
        for _, l in lt.iterrows():
            hit = a[(a["device_id"] == l["device_id"]) & (a["start"] <= l["end"] + slack) & (a["end"] >= l["start"] - slack)]
            detected += int(len(hit) > 0)
        true_alerts = 0
        for _, al in a.iterrows():
            hit = lt[(lt["device_id"] == al["device_id"]) & (al["start"] <= lt["end"] + slack) & (al["end"] >= lt["start"] - slack)]
            true_alerts += int(len(hit) > 0)
        rows.append({"label": label, "detector": det, "labelled_events": len(lt), "detected": detected,
                     "recall": detected / len(lt) if len(lt) else np.nan,
                     "alerts": len(a), "precision": true_alerts / len(a) if len(a) else np.nan})
    return pd.DataFrame(rows)
