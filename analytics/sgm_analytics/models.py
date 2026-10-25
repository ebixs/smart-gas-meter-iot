"""Consumption modelling: degree-day baselines and next-month forecasting (AI-004, AI-005).

1. Per-device degree-day model  daily_m3 = a + b * HDD  fitted with a robust
   (Huber) regression on quality-OK days only. ``a`` is cooking/hot-water load,
   ``b`` the household's heating sensitivity. This is the "expected" consumption
   the anomaly detectors compare against.
2. Global gradient-boosting forecaster for next Jalali-month consumption with
   P10/P50/P90 quantiles. Weather for the target month is unknown at forecast
   time, so it uses climatological HDD. The P10-P90 interval is calibrated with
   conformalised quantile regression using only earlier backtest months. Evaluated by a rolling-origin backtest
   against naive baselines (last year's same month; last month).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import HuberRegressor

from .climate import CITIES
from .jalali import to_jalali

HDD_BASE_C = 16.0
MODEL_VERSION = "gbr-quantile-v1"


BASES_C = tuple(range(12, 21))


def degree_days(weather: dict[str, pd.DataFrame], base: float = HDD_BASE_C) -> pd.DataFrame:
    """Daily weather plus heating degree-days computed from HOURLY temperatures.

    Hourly degree-hours/24 capture shoulder-season nights that dip below the balance
    temperature even when the daily mean does not. Columns hdd_bXX / hddc_bXX hold
    actual and climatological values for each candidate balance temperature XX.
    """
    from .climate import hourly_temperature

    rows = []
    for key, w in weather.items():
        city = CITIES[key]
        t_h = hourly_temperature(w, city).to_numpy().reshape(-1, 24)
        clim_w = w.assign(t_mean_c=w["t_clim_c"])
        tc_h = hourly_temperature(clim_w, city).to_numpy().reshape(-1, 24)
        frame = {"city": key, "date": w["date"], "t_mean_c": w["t_mean_c"], "t_clim_c": w["t_clim_c"],
                 "t_night_c": t_h[:, 1:6].mean(axis=1)}
        for b in BASES_C:
            frame[f"hdd_b{b}"] = np.clip(b - t_h, 0, None).mean(axis=1)
            frame[f"hddc_b{b}"] = np.clip(b - tc_h, 0, None).mean(axis=1)
        frame["hdd"] = frame[f"hdd_b{int(base)}"]
        frame["hdd_clim"] = frame[f"hddc_b{int(base)}"]
        rows.append(pd.DataFrame(frame))
    return pd.concat(rows, ignore_index=True)


def with_weather(daily: pd.DataFrame, devices: pd.DataFrame, dd: pd.DataFrame) -> pd.DataFrame:
    d = daily.merge(devices[["device_id", "city", "tariff_region"]], on="device_id")
    return d.merge(dd, on=["city", "date"], how="left")


def fit_degree_day_models(daily_w: pd.DataFrame, bases: tuple[int, ...] = BASES_C) -> pd.DataFrame:
    """Robust per-device change-point fit: daily m3 = a + b * HDD(T_base).

    The balance temperature T_base differs by household (thermostat, insulation), so it
    is chosen per device from ``bases`` by the smallest robust residual spread
    (PRISM-style variable-base degree-day model). Only quality-OK days are used.
    """
    out = []
    for dev, g in daily_w[daily_w["quality"] == "ok"].groupby("device_id", observed=True):
        if len(g) < 60:
            continue
        y = g["volume_m3"].to_numpy()
        best = None
        for base in bases:
            x = g[[f"hdd_b{base}"]].to_numpy()
            model = HuberRegressor(epsilon=1.5, max_iter=300).fit(x, y)
            resid = y - model.predict(x)
            mad = float(np.median(np.abs(resid - np.median(resid)))) * 1.4826
            if best is None or mad < best[0]:
                best = (mad, base, model)
        mad, base, model = best
        out.append({"device_id": dev, "base_c": int(base), "base_m3_day": float(model.intercept_),
                    "heat_m3_per_hdd": float(model.coef_[0]), "resid_mad": mad, "n_days": len(g)})
    return pd.DataFrame(out)


def add_device_hdd(daily_w: pd.DataFrame, dd_models: pd.DataFrame) -> pd.DataFrame:
    d = daily_w.merge(dd_models[["device_id", "base_c", "base_m3_day", "heat_m3_per_hdd"]], on="device_id", how="left")
    base = d["base_c"].fillna(HDD_BASE_C).astype(int).to_numpy()
    d["hdd_dev"] = np.choose(np.searchsorted(BASES_C, base), [d[f"hdd_b{b}"].to_numpy() for b in BASES_C])
    d["hdd_clim_dev"] = np.choose(np.searchsorted(BASES_C, base), [d[f"hddc_b{b}"].to_numpy() for b in BASES_C])
    return d


def expected_daily(daily_w: pd.DataFrame, dd_models: pd.DataFrame) -> pd.DataFrame:
    d = add_device_hdd(daily_w, dd_models)
    d = d.merge(dd_models[["device_id", "resid_mad"]], on="device_id", how="left")
    d["expected_m3"] = (d["base_m3_day"] + d["heat_m3_per_hdd"] * d["hdd_dev"]).clip(lower=0.05)
    d["ratio"] = d["volume_m3"] / d["expected_m3"]
    return d


# ---------------------------------------------------------------- monthly forecasting
def monthly_table(daily_w: pd.DataFrame, dd_models: pd.DataFrame) -> pd.DataFrame:
    d = add_device_hdd(daily_w, dd_models)
    j = [to_jalali(x.date()) for x in d["date"]]
    d["jyear"] = [x.year for x in j]
    d["jmonth"] = [x.month for x in j]
    d["ok"] = d["quality"] == "ok"
    m = d.groupby(["device_id", "city", "jyear", "jmonth"], observed=True).agg(
        m3=("volume_m3", "sum"), days=("date", "nunique"), ok_share=("ok", "mean"),
        hdd=("hdd_dev", "sum"), hdd_clim=("hdd_clim_dev", "sum")).reset_index()
    m["t"] = m["jyear"] * 12 + m["jmonth"] - 1
    return m[m["days"] >= 28]


def _features(m: pd.DataFrame, dd_models: pd.DataFrame) -> pd.DataFrame:
    m = m.sort_values(["device_id", "t"]).copy()
    by = m.groupby("device_id", observed=True)
    for k in (1, 12):
        m[f"lag{k}"] = by["m3"].shift(k)
        m[f"hdd_lag{k}"] = by["hdd"].shift(k)
        m[f"days_lag{k}"] = by["days"].shift(k)
        stale = by["t"].shift(k) != m["t"] - k
        m.loc[stale, [f"lag{k}", f"hdd_lag{k}", f"days_lag{k}"]] = np.nan
    m = m.merge(dd_models[["device_id", "base_m3_day", "heat_m3_per_hdd"]], on="device_id", how="left")
    m["hdd_clim_month"] = m["hdd_clim"]  # climatology for the target month (known in advance)
    m["dd_estimate"] = m["base_m3_day"] * m["days"] + m["heat_m3_per_hdd"] * m["hdd_clim_month"]
    # Last year's same month, re-scaled from last year's actual weather to normal weather.
    base12 = m["base_m3_day"] * m["days_lag12"]
    m["wn_lag12"] = base12 + (m["lag12"] - base12).clip(lower=0) * (m["hdd_clim_month"] + 1) / (m["hdd_lag12"] + 1)
    # Recent behaviour: last month relative to what the degree-day model expected for it.
    exp1 = m["base_m3_day"] * m["days_lag1"] + m["heat_m3_per_hdd"] * m["hdd_lag1"]
    m["trend1"] = (m["lag1"] / exp1.clip(lower=1)).clip(0.2, 5)
    m["trend_estimate"] = m["dd_estimate"] * m["trend1"]
    m["city_code"] = m["city"].map({k: i for i, k in enumerate(CITIES)})
    return m


FEATURES = ["lag1", "lag12", "wn_lag12", "dd_estimate", "trend_estimate", "trend1", "hdd_clim_month",
            "jmonth", "city_code", "heat_m3_per_hdd", "base_m3_day"]


@dataclass
class ForecastResult:
    backtest: pd.DataFrame  # per (device, month) predictions on held-out months
    metrics: pd.DataFrame  # WAPE/MAPE per method
    next_month: pd.DataFrame  # forecasts for the month after the data ends
    model_version: str
    train_window: str


def _fit_quantiles(train: pd.DataFrame) -> dict[float, GradientBoostingRegressor]:
    models = {}
    for q in (0.1, 0.5, 0.9):
        gbr = GradientBoostingRegressor(loss="quantile", alpha=q, n_estimators=250, max_depth=3,
                                        learning_rate=0.05, subsample=0.8, random_state=0)
        gbr.fit(train[FEATURES].fillna(-1), train["m3"])
        models[q] = gbr
    return models


def forecast(daily_w: pd.DataFrame, dd_models: pd.DataFrame, holdout_months: int = 9) -> ForecastResult:
    base = monthly_table(daily_w, dd_models)
    # One future row per device for the month after the data ends: target unknown,
    # climatological HDD taken from the same Jalali month in earlier years.
    last = base.sort_values("t").groupby("device_id", observed=True).tail(1)
    future = last[["device_id", "city", "t"]].copy()
    future["t"] += 1
    future["jyear"], future["jmonth"] = future["t"] // 12, future["t"] % 12 + 1
    future["days"] = np.where(future["jmonth"] <= 6, 31, 30)
    clim = base.groupby(["device_id", "jmonth"], observed=True)["hdd_clim"].mean()
    future["hdd_clim"] = [clim.get((d, jm), np.nan) for d, jm in zip(future["device_id"], future["jmonth"])]
    future["m3"], future["hdd"], future["ok_share"], future["is_future"] = np.nan, np.nan, 1.0, True
    allm = _features(pd.concat([base.assign(is_future=False), future], ignore_index=True), dd_models)
    m = allm[~allm["is_future"].astype(bool) & (allm["ok_share"] >= 0.8)]  # AI-005: comparable, valid data only
    months = sorted(m["t"].unique())
    test_months = months[-holdout_months:]
    preds = []
    scores: list[np.ndarray] = []  # conformity scores from EARLIER test months only
    for t in test_months:  # rolling origin: train strictly on earlier months
        train = m[(m["t"] < t) & m["lag1"].notna()]
        test = m[(m["t"] == t) & m["lag1"].notna()].copy()
        if len(train) < 200 or test.empty:
            continue
        models = _fit_quantiles(train)
        for q, gbr in models.items():
            test[f"p{int(q * 100)}"] = gbr.predict(test[FEATURES].fillna(-1))
        # Conformalised quantile regression (CQR), relative to the median so the correction
        # scales with household size. Calibrated only from months before ``t`` (no leakage).
        past = np.concatenate(scores) if scores else np.array([])
        q_adj = float(np.quantile(past, 0.8)) if len(past) >= 100 else np.nan
        scale = test["p50"].clip(lower=1.0)
        test["cqr_q"] = q_adj
        test["p10_cal"] = (test["p10"] - np.nan_to_num(q_adj) * scale).clip(lower=0)
        test["p90_cal"] = test["p90"] + np.nan_to_num(q_adj) * scale
        scores.append(np.maximum((test["p10"] - test["m3"]) / scale, (test["m3"] - test["p90"]) / scale).to_numpy())
        test["naive_last_year"] = test["lag12"]
        test["naive_last_month"] = test["lag1"]
        preds.append(test)
    bt = pd.concat(preds, ignore_index=True)

    def wape(pred: pd.Series) -> float:
        ok = pred.notna()
        return float(np.abs(bt.loc[ok, "m3"] - pred[ok]).sum() / bt.loc[ok, "m3"].sum())

    def mape(pred: pd.Series) -> float:
        ok = pred.notna() & (bt["m3"] > 5)
        return float((np.abs(bt.loc[ok, "m3"] - pred[ok]) / bt.loc[ok, "m3"]).median())

    coverage = float(((bt["m3"] >= bt["p10"]) & (bt["m3"] <= bt["p90"])).mean())
    cal = bt[bt["cqr_q"].notna()]
    coverage_cal = float(((cal["m3"] >= cal["p10_cal"]) & (cal["m3"] <= cal["p90_cal"])).mean()) if len(cal) else np.nan
    raw_on_cal = float(((cal["m3"] >= cal["p10"]) & (cal["m3"] <= cal["p90"])).mean()) if len(cal) else np.nan
    metrics = pd.DataFrame([
        {"method": "Gradient boosting P50 (" + MODEL_VERSION + ")", "WAPE": wape(bt["p50"]), "median APE": mape(bt["p50"])},
        {"method": "Change-point degree-day model x climatology", "WAPE": wape(bt["dd_estimate"]), "median APE": mape(bt["dd_estimate"])},
        {"method": "Weather-normalised last year", "WAPE": wape(bt["wn_lag12"]), "median APE": mape(bt["wn_lag12"])},
        {"method": "Naive: same month last year", "WAPE": wape(bt["naive_last_year"]), "median APE": mape(bt["naive_last_year"])},
        {"method": "Naive: last month", "WAPE": wape(bt["naive_last_month"]), "median APE": mape(bt["naive_last_month"])},
    ])
    metrics.attrs["p10_p90_coverage_raw"] = coverage
    metrics.attrs["p10_p90_coverage_raw_on_calibrated_months"] = raw_on_cal
    metrics.attrs["p10_p90_coverage"] = coverage_cal  # reported: calibrated intervals
    metrics.attrs["calibrated_rows"] = int(len(cal))

    models = _fit_quantiles(m[m["lag1"].notna()])  # final model on all valid history
    nxt = allm[allm["is_future"].astype(bool)].copy()
    for q, gbr in models.items():
        nxt[f"p{int(q * 100)}"] = gbr.predict(nxt[FEATURES].fillna(-1))
    q_all = float(np.quantile(np.concatenate(scores), 0.8)) if scores else 0.0
    scale = nxt["p50"].clip(lower=1.0)
    nxt["p10"] = (nxt["p10"] - q_all * scale).clip(lower=0)  # CQR-calibrated interval
    nxt["p90"] = nxt["p90"] + q_all * scale
    window = f"{int(months[0] // 12)}/{int(months[0] % 12 + 1):02d} - {int(months[-1] // 12)}/{int(months[-1] % 12 + 1):02d}"
    return ForecastResult(bt, metrics, nxt[["device_id", "city", "jyear", "jmonth", "p10", "p50", "p90", "lag1", "lag12"]],
                          MODEL_VERSION, window)
