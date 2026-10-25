"""Publish reviewable analytics artefacts: figures, metrics, sample invoices, dashboard data.

Figures follow the repository's data-visualisation rules: validated categorical
slots in fixed order (blue, orange, aqua), one y-axis per panel (two measures
-> two panels, never a dual axis), recessive grid, direct labels, and status
colours only for alert state.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import billing, invoice_pdf  # noqa: E402
from .anomaly import LABEL_TO_DETECTOR, daily_shape  # noqa: E402
from .climate import CITIES  # noqa: E402

# Validated palette (dataviz reference instance, light mode).
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]  # slots 1-3: validated all-pairs
SEQ = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]  # ordinal blue ramp
STATUS = {"good": "#0ca30c", "warning": "#fab219", "serious": "#ec835a", "critical": "#d03b3b"}
LABEL_BAND = "#e1e0d9"


def _style() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": AXIS, "axes.labelcolor": INK_2, "axes.titlecolor": INK,
        "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.labelsize": 9, "xtick.color": MUTED, "ytick.color": MUTED,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.grid": True, "grid.color": GRID,
        "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
        "font.family": "DejaVu Sans", "legend.frameon": False, "legend.fontsize": 8,
        "lines.linewidth": 1.6, "figure.dpi": 150,
    })


def _save(fig: plt.Figure, path: Path) -> str:
    fig.savefig(path, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    return path.name


def fig_fleet(r, out: Path) -> str:
    """Two panels on a shared time axis: fleet gas use and temperature (no dual axis)."""
    d = r.daily.merge(r.fleet.devices[["device_id", "city"]], on="device_id")
    d = d[d["city"] == "shahrekord"]
    use = d.groupby("date")["volume_m3"].mean()
    w = r.fleet.weather["shahrekord"].set_index("date")
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 4.6), sharex=True, gridspec_kw={"height_ratios": [3, 2]})
    a1.plot(use.index, use.values, color=SERIES[0], lw=1.2)
    a1.set_title(f"Shahrekord households: average daily gas use (n={d['device_id'].nunique()})")
    a1.set_ylabel("m³ / household / day")
    a2.plot(w.index, w["t_mean_c"], color=SERIES[1], lw=1.0)
    a2.plot(w.index, w["t_clim_c"], color=MUTED, lw=1.0, ls="--")
    a2.text(w.index[-1], w["t_clim_c"].iloc[-1], " climate normal", color=INK_2, fontsize=8, va="center")
    a2.set_title("Daily mean temperature", fontsize=10)
    a2.set_ylabel("°C")
    a2.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.tight_layout()
    return _save(fig, out / "fig1_fleet_use_and_weather.png")


def fig_degree_day(r, out: Path) -> str:
    m = r.dd_models.sort_values("n_days", ascending=False)
    dev = m.iloc[len(m) // 3]
    e = r.expected[(r.expected["device_id"] == dev.device_id) & (r.expected["quality"] == "ok")]
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    ax.scatter(e["hdd_dev"], e["volume_m3"], s=10, color=SERIES[0], alpha=0.45, edgecolors="none")
    x = np.linspace(0, e["hdd_dev"].max(), 50)
    ax.plot(x, dev.base_m3_day + dev.heat_m3_per_hdd * x, color=INK, lw=2)
    ax.set_title(f"Degree-day model for {dev.device_id}")
    ax.set_xlabel(f"heating degree-days (balance temperature {dev.base_c} °C, from hourly data)")
    ax.set_ylabel("gas use, m³/day")
    ax.annotate(f"m³/day = {dev.base_m3_day:.2f} + {dev.heat_m3_per_hdd:.2f} × HDD\n"
                f"cooking & hot water ≈ {dev.base_m3_day:.1f} m³/day",
                xy=(0.03, 0.97), xycoords="axes fraction", va="top", fontsize=9, color=INK_2)
    fig.tight_layout()
    return _save(fig, out / "fig2_degree_day_model.png")


def fig_forecast(r, out: Path) -> str:
    met = r.forecast.metrics.sort_values("WAPE")
    bt = r.forecast.backtest
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.0), gridspec_kw={"width_ratios": [1.1, 1]})
    y = np.arange(len(met))
    colors_ = [SERIES[0] if "Gradient" in name else AXIS for name in met["method"]]
    a1.barh(y, met["WAPE"] * 100, color=colors_, height=0.6)
    a1.set_yticks(y, [name.replace(" (gbr-quantile-v1)", "") for name in met["method"]], fontsize=8)
    a1.invert_yaxis()
    for yi, v in zip(y, met["WAPE"] * 100):
        a1.text(v + 0.6, yi, f"{v:.1f}%", va="center", fontsize=8, color=INK_2)
    a1.set_xlabel("WAPE on held-out months (lower is better)")
    a1.set_title("Next-month forecast: rolling-origin backtest")
    a1.grid(axis="y", visible=False)
    # One household through the backtest months
    dev = bt.groupby("device_id")["m3"].mean().sort_values().index[len(bt["device_id"].unique()) // 2]
    b = bt[bt["device_id"] == dev].sort_values("t")
    labels, prev_year = [], None
    for t in b["t"]:
        year, month = int(t // 12), int(t % 12 + 1)
        labels.append(f"{month:02d}\n{year}" if year != prev_year else f"{month:02d}")
        prev_year = year
    xs = np.arange(len(b))
    lo, hi = ("p10_cal", "p90_cal") if "p10_cal" in b and b["p10_cal"].notna().any() else ("p10", "p90")
    a2.fill_between(xs, b[lo].fillna(b["p10"]), b[hi].fillna(b["p90"]), color=SEQ[0], alpha=0.55, lw=0,
                    label="P10-P90 interval (calibrated)")
    a2.plot(xs, b["p50"], color=SERIES[0], marker="o", ms=4, label="forecast P50")
    a2.plot(xs, b["m3"], color=INK, marker="o", ms=4, lw=1.2, label="actual")
    a2.set_xticks(xs, labels, fontsize=8)
    a2.set_title(f"{dev}: forecast vs actual (Jalali months)")
    a2.set_ylabel("m³ per month")
    a2.legend(loc="upper right")
    cov = r.forecast.metrics.attrs.get("p10_p90_coverage", float("nan"))
    a2.annotate(f"P10-P90 coverage on all held-out months: {cov:.0%} (target 80%)", xy=(0.0, -0.24),
                xycoords="axes fraction", fontsize=8, color=INK_2)
    fig.tight_layout()
    return _save(fig, out / "fig3_forecast_backtest.png")


def fig_anomalies(r, out: Path) -> str:
    """Small multiples: one labelled fault per panel, label band vs detector window."""
    kinds = ["leak_like_flow", "magnet_tamper", "stuck_meter", "usage_spike"]
    titles = {"leak_like_flow": "Leak-like continuous flow (night minimum)",
              "magnet_tamper": "Meter interference (sustained drop)",
              "stuck_meter": "Stuck / disconnected sensor",
              "usage_spike": "Usage spike"}
    shape = daily_shape(r.intervals) if "night_min_m3h" not in r.expected else None
    exp = r.expected if shape is None else r.expected.merge(shape, on=["device_id", "date"], how="left")
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.2))
    for ax, kind in zip(axes.ravel(), kinds):
        lab = r.fleet.labels[r.fleet.labels["anomaly"] == kind]
        det = LABEL_TO_DETECTOR[kind]
        chosen = None
        for _, row in lab.iterrows():
            a = r.alerts[(r.alerts["device_id"] == row.device_id) & (r.alerts["detector"] == det)]
            if len(a):
                chosen = (row, a.iloc[0])
                break
        if chosen is None:
            ax.set_visible(False)
            continue
        row, alert = chosen
        s, e = pd.Timestamp(row.start).normalize(), pd.Timestamp(row.end).normalize()
        g = exp[(exp["device_id"] == row.device_id) & (exp["date"] >= s - pd.Timedelta(days=30))
                & (exp["date"] <= e + pd.Timedelta(days=30))]
        if kind == "leak_like_flow":
            ax.plot(g["date"], g["night_min_m3h"], color=SERIES[0], label="night minimum flow")
            ax.set_ylabel("m³/h")
        else:
            ax.plot(g["date"], g["volume_m3"], color=SERIES[0], label="recorded")
            ax.plot(g["date"], g["expected_m3"], color=MUTED, ls="--", lw=1.2, label="weather-expected")
            ax.set_ylabel("m³/day")
        ax.axvspan(s, e, color=LABEL_BAND, zorder=0, label="injected fault (ground truth)")
        ax.axvspan(alert["start"], alert["end"], ymin=0.94, ymax=1.0, color=STATUS["critical"],
                   label="detector alert window")
        ax.set_title(titles[kind], fontsize=10)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b\n%Y"))
        ax.tick_params(axis="x", labelsize=7)
    handles, labels = [], []
    for ax in axes.ravel():
        for h_, l_ in zip(*ax.get_legend_handles_labels()):
            if l_ not in labels:
                handles.append(h_)
                labels.append(l_)
    fig.legend(handles, labels, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Detected faults against the simulator's ground truth", x=0.01, ha="left",
                 fontsize=12, fontweight="bold", color=INK)
    fig.tight_layout(rect=(0, 0.05, 1, 0.97))
    return _save(fig, out / "fig4_anomaly_gallery.png")


def fig_detection_quality(evaluations: dict[str, pd.DataFrame], out: Path) -> str:
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    for ax, metric in zip(axes, ["recall", "precision"]):
        for k, (name, ev) in enumerate(evaluations.items()):
            ev = ev.set_index("label")
            ys = np.arange(len(ev))
            ax.scatter(ev[metric] * 100, ys + (k - 0.5) * 0.18, color=SERIES[k], s=46, zorder=3,
                       edgecolors=SURFACE, linewidths=1.5, label=name)
        ax.set_yticks(np.arange(len(ev)), [lbl.replace("_", " ") for lbl in ev.index], fontsize=8)
        ax.set_xlim(0, 105)
        ax.set_title(metric.capitalize() + " by fault type")
        ax.set_xlabel("%")
        ax.grid(axis="y", visible=False)
    axes[0].invert_yaxis()
    axes[1].legend(loc="lower left")
    fig.tight_layout()
    return _save(fig, out / "fig5_detection_quality.png")


def dashboard_dataset(r, out: Path) -> Path:
    """Compact dataset for the static dashboard demo (GitHub Pages)."""
    devs = r.fleet.devices
    daily = r.daily.copy()
    daily["day"] = daily["date"].dt.strftime("%Y-%m-%d")
    last_day = daily["date"].max()
    recent = daily[daily["date"] > last_day - pd.Timedelta(days=400)]
    series = {d: [[day, round(v, 2), q] for day, v, q in zip(g["day"], g["volume_m3"], g["quality"])]
              for d, g in recent.groupby("device_id", observed=True)}
    last = r.fleet.readings.sort_values("ts_utc").groupby("device_id", observed=True).tail(1).set_index("device_id")
    nxt = r.forecast.next_month.set_index("device_id")
    alerts = r.alerts.copy()
    alerts["start"] = alerts["start"].dt.strftime("%Y-%m-%d")
    alerts["end"] = alerts["end"].dt.strftime("%Y-%m-%d")
    alerts = alerts[alerts["detector"] != "unusual_day"]
    inv = {i.device_id: i for i in r.invoices}
    device_rows = []
    for _, d in devs.iterrows():
        lr = last.loc[d.device_id] if d.device_id in last.index else None
        f = nxt.loc[d.device_id] if d.device_id in nxt.index else None
        i = inv.get(d.device_id)
        device_rows.append({
            "id": d.device_id, "city": d.city, "city_fa": CITIES[d.city].name_fa, "region": d.tariff_region,
            "area_m2": int(d.area_m2), "occupants": int(d.occupants),
            "last_reading": None if lr is None else {"ts": lr.ts_utc.isoformat(), "pulses": int(lr.pulse_count_total)},
            "forecast": None if f is None else {"jyear": int(f.jyear), "jmonth": int(f.jmonth),
                                                "p10": round(float(f.p10), 1), "p50": round(float(f.p50), 1),
                                                "p90": round(float(f.p90), 1)},
            "invoice": None if i is None else {"id": i.invoice_id, "period": i.period_jalali,
                                               "m3": i.consumption_m3, "total": i.total_payable,
                                               "status": i.status, "tiers": len(i.tier_lines)},
        })
    payload = {
        "generated_from": "sgm_analytics.pipeline (synthetic fleet, not field data)",
        "data_end": str(last_day.date()),
        "devices": device_rows,
        "daily": series,
        "alerts": alerts.drop(columns=["data_quality"]).to_dict(orient="records"),
        "forecast_metrics": r.forecast.metrics.to_dict(orient="records"),
        "forecast_coverage": r.forecast.metrics.attrs.get("p10_p90_coverage"),
        "detection": r.evaluation.to_dict(orient="records"),
        "tariff": billing.ILLUSTRATIVE_TARIFF.to_dict(),
    }
    path = out / "dashboard-data.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str), encoding="utf-8")
    return path


def _md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def publish(r, out: Path, holdout=None) -> None:
    _style()
    out = Path(out)
    fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    figs = [fig_fleet(r, fig_dir), fig_degree_day(r, fig_dir), fig_forecast(r, fig_dir), fig_anomalies(r, fig_dir)]
    evals = {"tuning fleet (seed 1405)": r.evaluation}
    if holdout is not None:
        evals["held-out fleet (seed 2026)"] = holdout.evaluation
    figs.append(fig_detection_quality(evals, fig_dir))

    inv_dir = out / "invoices"
    inv_dir.mkdir(exist_ok=True)
    for stale in inv_dir.glob("*"):
        stale.unlink()
    picks = {"high-tier": max(r.invoices, key=lambda i: (len(i.tier_lines), i.consumption_m3)),
             "typical": sorted(r.invoices, key=lambda i: i.consumption_m3)[len(r.invoices) // 2]}
    prov = [i for i in r.invoices if i.status.startswith("PROVISIONAL")]
    if prov:
        picks["provisional"] = prov[0]
    for name, inv in picks.items():
        invoice_pdf.render_invoice(inv, inv_dir / f"sample-invoice-{name}.pdf")
        (inv_dir / f"sample-invoice-{name}.json").write_text(billing.invoice_json(inv), encoding="utf-8")
    dashboard_dataset(r, out)

    def fmt(ev: pd.DataFrame) -> pd.DataFrame:
        e = ev.copy()
        for c in ("recall", "precision"):
            e[c] = e[c].map(lambda v: "-" if pd.isna(v) else f"{v:.0%}")
        return e[["label", "detector", "labelled_events", "detected", "recall", "alerts", "precision"]]

    met = r.forecast.metrics.copy()
    met["WAPE"] = met["WAPE"].map(lambda v: f"{v:.1%}")
    met["median APE"] = met["median APE"].map(lambda v: f"{v:.1%}")
    cov = r.forecast.metrics.attrs.get("p10_p90_coverage", float("nan"))
    hold_txt = ""
    if holdout is not None:
        hmet = holdout.forecast.metrics.copy()
        hmet["WAPE"] = hmet["WAPE"].map(lambda v: f"{v:.1%}")
        hmet["median APE"] = hmet["median APE"].map(lambda v: f"{v:.1%}")
        hold_txt = (f"\n\n**Held-out fleet (seed 2026, never used for tuning):**\n\n{_md_table(fmt(holdout.evaluation))}\n\n"
                    f"Forecast on the held-out fleet:\n\n{_md_table(hmet)}\n\n"
                    f"P10-P90 coverage: {holdout.forecast.metrics.attrs.get('p10_p90_coverage', float('nan')):.0%}")
    n = len(r.fleet.devices)
    text = f"""# Analytics report: synthetic smart-gas-meter fleet

> **Everything here is synthetic.** A simulated fleet exercises the software end to end. These are not field
> measurements, the tariff is illustrative, and an anomaly flag is never proof of a gas leak.

Generated by `python -m sgm_analytics.pipeline --publish ../docs/analytics` from `analytics/`. The fleet has {n} households in 6
Iranian cities, simulated hour by hour from {r.fleet.start.date()} to {r.fleet.end.date()}, producing {len(r.fleet.readings):,} meter readings.

## 1. Fleet and weather

![fleet](figures/{figs[0]})

Hourly gas use comes from a building-physics model. Space heating is driven by heating degree-hours, scaled by floor area,
insulation, thermostat set-point, night set-back and weekday absence. Cooking and hot water follow a daily profile and
grow with occupants and cold inlet water. Households travel during Nowruz and occasionally during the year. Weather is a
city climatology with persistent day-to-day anomalies (AR(1)), so cold spells last several days.

## 2. Data quality before anything else (AI-002)

Cumulative pulse counts are turned into interval volumes, with flags for duplicates, gaps, counter resets and physically
implausible flow (above the G4 meter's 6 m³/h Qmax). Flags travel with the numbers. Billing and analytics read the flags;
they never "fix" data silently.

## 3. Per-household degree-day model (expected consumption)

![degree-day](figures/{figs[1]})

Each household gets a robust (Huber) change-point model, `m³/day = a + b × HDD(T_base)`. The balance temperature `T_base`
is chosen per household (PRISM-style). The model gives the *weather-expected* consumption that the forecasts and the
anomaly detectors compare against.

## 4. Next-month forecast with uncertainty (AI-004)

![forecast](figures/{figs[2]})

A global gradient-boosting model predicts P10/P50/P90 consumption for the next Jalali month from lags, the household's
degree-day parameters and climatological HDD (the target month's weather is unknown at forecast time). Evaluation is a
rolling-origin backtest that trains strictly on earlier months, compared with honest baselines:

{_md_table(met)}

P10-P90 interval coverage on held-out months: **{cov:.0%}** (target 80%). Weather-normalised last-year consumption is a
strong baseline. The boosted model matches its median error and adds calibrated intervals.

## 5. Fault and anomaly detection (AI-003, AI-006, AI-007)

![anomalies](figures/{figs[3]})

Each detector is explainable, and every alert carries its reason, time window, baseline, deviation and data quality.

| Detector | Logic |
|---|---|
| continuous_flow | CUSUM on the night-time minimum flow, standardised by a level-dependent (heteroscedastic) scale |
| zero_while_expected | no pulses for ≥2 days while the weather model expects clear use |
| sustained_drop | ≥5 days at a steady 10-45 % of the expected level with normal hourly variability. Travel drops to ~0 % with erratic use; interference scales the whole profile |
| usage_spike | ratio > 2, robust z > 6 and a jump against the previous week's median |
| data_gap / counter_reset | straight from the data-quality layer |
| unusual_day | Isolation Forest on residual features (low confidence, not scored) |

Event-level precision and recall against the simulator's ground-truth labels (±2 days):

**Tuning fleet (seed 1405):**

{_md_table(fmt(r.evaluation))}{hold_txt}

![quality](figures/{figs[4]})

The detector thresholds were tuned on the seed-1405 fleet only. The seed-2026 fleet is a held-out check of how well they
generalise. Diagnosis drove each change, and the false alarms were inspected rather than tuned away: the first
interference detector fired on Nowruz travel (3 % precision). It now separates travel from interference by the level band
and the hourly variability.

## 6. Billing (BILL-001 … BILL-008)

Each invoice uses a versioned **illustrative** tariff. It has four standard tiers measured against a regional, monthly
consumption pattern (the median household m³/day over prior years, quality-OK days only), cold- and warm-season prices, a
fixed charge, tax and rounding. Billing periods are half-open Jalali months in Asia/Tehran. Each invoice stores its
calculation trace, is marked *PROVISIONAL* when data is missing, reset or under an open fault alert, and carries an
HMAC-signed QR verification token with no personal data.

Sample invoices (bilingual PDF + JSON with trace): [`invoices/`](invoices/).

## Limitations

- The simulator's physics and fault models are plausible, not calibrated against field data. Detector performance on real
  meters will differ and must be re-measured before any alert is shown to a customer (AI-007).
- Labels are synthetic and evaluation is event-level with ±2 days of slack.
- Monthly city temperatures are rounded climate approximations, not an authoritative climate dataset.
- Tariff numbers are placeholders. Official billing stays blocked until metrology, tariff and legal approval (BILL-008).
"""
    (out / "REPORT.md").write_text(text, encoding="utf-8")
    pd.DataFrame(r.evaluation).to_csv(out / "anomaly_evaluation.csv", index=False)
    r.forecast.metrics.to_csv(out / "forecast_metrics.csv", index=False)
