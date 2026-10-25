"""Simulate a fleet of residential gas meters with realistic behaviour and labelled faults.

Each household has a city (climate), floor area, occupants, insulation, thermostat
habits and travel behaviour. Hourly gas use = space heating driven by heating
degree-hours + cooking/hot-water with a daily profile + noise. The meter emits
pulses (default 0.01 m3/pulse, a common G4 diaphragm-meter constant; assumption)
and reports its cumulative pulse count every hour.

Injected, labelled anomalies (ground truth for evaluating analytics):
  leak_like_flow   continuous extra flow, also at night (decision support only:
                   an anomaly is NEVER proof of a gas leak)
  stuck_meter      pulses stop although gas is consumed (sensor fault)
  comms_outage     readings missing; counter keeps counting (no gas lost)
  magnet_tamper    counted pulses reduced (meter interference); some cases
                   also log an enclosure-open event
  usage_spike      a few days of unusually high use
  counter_reset    device reboots and its cumulative counter restarts at 0

Everything here is synthetic. It exercises software; it is not field data.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .climate import CITIES, daily_weather, hourly_temperature
from .jalali import to_gregorian

PULSE_M3 = 0.01
CITY_WEIGHTS = {"tehran": 0.34, "mashhad": 0.15, "tabriz": 0.14, "shahrekord": 0.10,
                "rasht": 0.13, "ahvaz": 0.14}
ANOMALY_TYPES = ("leak_like_flow", "stuck_meter", "comms_outage", "magnet_tamper",
                 "usage_spike", "counter_reset")

# Share of the day's cooking + hot-water use in each local hour.
_BASE_PROFILE = np.array([0.6, 0.4, 0.3, 0.3, 0.4, 0.8, 2.2, 3.0, 2.4, 1.4, 1.2, 1.6,
                          2.4, 2.0, 1.3, 1.0, 1.0, 1.3, 2.2, 3.0, 3.2, 2.6, 1.7, 1.0])
_BASE_PROFILE = _BASE_PROFILE / _BASE_PROFILE.sum()


@dataclass
class Fleet:
    devices: pd.DataFrame
    weather: dict[str, pd.DataFrame]
    readings: pd.DataFrame  # device_id, ts_utc, sequence, pulse_count_total
    events: pd.DataFrame  # device_id, ts_utc, event
    labels: pd.DataFrame  # device_id, anomaly, start, end, detail
    true_daily: pd.DataFrame  # device_id, date (local), true_m3, recorded_m3
    start: pd.Timestamp = field(default=None)
    end: pd.Timestamp = field(default=None)


def _households(n: int, rng: np.random.Generator) -> pd.DataFrame:
    cities = rng.choice(list(CITY_WEIGHTS), size=n, p=list(CITY_WEIGHTS.values()))
    area = np.clip(rng.lognormal(np.log(95), 0.32, n), 45, 260).round()
    occupants = rng.choice([1, 2, 3, 4, 5, 6], size=n, p=[0.10, 0.20, 0.27, 0.27, 0.11, 0.05])
    return pd.DataFrame({
        "device_id": [f"sgm-{i:04d}" for i in range(1, n + 1)],
        "subscriber_ref": [f"SUB-{rng.integers(10**7, 10**8)}" for _ in range(n)],
        "city": cities,
        "tariff_region": [CITIES[c].tariff_region for c in cities],
        "area_m2": area,
        "occupants": occupants,
        "insulation": rng.uniform(0.7, 1.4, n).round(2),  # >1 = leakier building
        "setpoint_c": rng.choice([19, 20, 21, 22, 23], size=n, p=[0.1, 0.2, 0.3, 0.25, 0.15]),
        "night_setback": rng.random(n) < 0.6,
        "away_weekdays": rng.random(n) < 0.5,
        "nowruz_travel": rng.random(n) < 0.45,
    })


def _consumption(h: pd.Series, temps: pd.Series, rng: np.random.Generator,
                 nowruz: list[tuple[pd.Timestamp, pd.Timestamp]]) -> np.ndarray:
    idx = temps.index
    hour = idx.hour.to_numpy()
    dow = idx.dayofweek.to_numpy()  # Mon=0 .. Sun=6; Iranian weekend Thu(3)/Fri(4)
    setpoint = np.full(len(idx), float(h.setpoint_c))
    if h.night_setback:
        setpoint[(hour >= 23) | (hour < 6)] -= 2.0
    if h.away_weekdays:
        working = ~np.isin(dow, [3, 4]) & (hour >= 8) & (hour < 16)
        setpoint[working] -= 1.5
    away = np.zeros(len(idx), dtype=bool)
    if h.nowruz_travel:
        for start, _ in nowruz:
            depart = start + pd.Timedelta(days=int(rng.integers(-2, 5)))
            away |= (idx >= depart) & (idx < depart + pd.Timedelta(days=int(rng.integers(4, 13))))
    for _ in range(int(rng.poisson(2.0 * len(idx) / 8760))):  # occasional short trips
        depart = idx[int(rng.integers(0, len(idx) - 72))]
        away |= (idx >= depart) & (idx < depart + pd.Timedelta(days=int(rng.integers(2, 5))))
    setpoint[away] = 10.0  # frost protection while away

    balance = setpoint - 3.0  # internal and solar gains cover ~3 K
    hdd = np.clip(balance - temps.to_numpy(), 0, None)
    heating = 0.00045 * h.area_m2 * h.insulation * hdd

    daily_base = 0.35 + 0.28 * h.occupants  # m3/day cooking + hot water
    cold_inlet = 1.0 + 0.35 * np.clip((15.0 - temps.to_numpy()) / 15.0, 0, 1)
    base = daily_base * _BASE_PROFILE[hour] * cold_inlet
    base[away] *= 0.05
    noise = rng.lognormal(0.0, 0.18, len(idx))
    return (heating + base) * noise


def simulate_fleet(n_devices: int = 240, start: str = "2023-09-23", end: str = "2026-09-23",
                   seed: int = 1405, anomaly_share: float = 0.2) -> Fleet:
    """Simulate hourly meter readings for ``n_devices`` households between start and end (local)."""
    rng = np.random.default_rng(seed)
    devices = _households(n_devices, rng)
    weather = {key: daily_weather(city, start, end, seed=seed + i) for i, (key, city) in enumerate(CITIES.items())}
    hourly_t = {key: hourly_temperature(weather[key], CITIES[key]) for key in CITIES}
    first_year = pd.Timestamp(start).year
    nowruz = [(pd.Timestamp(to_gregorian(jy, 1, 1), tz="Asia/Tehran"), None)
              for jy in range(first_year - 621, first_year - 621 + 5)]

    readings, events, labels, daily = [], [], [], []
    anomalous = set(rng.choice(devices.index, size=int(anomaly_share * n_devices), replace=False))
    for i, h in devices.iterrows():
        temps = hourly_t[h.city]
        idx = temps.index
        n = len(idx)
        true_m3 = _consumption(h, temps, rng, nowruz)
        counted_m3 = true_m3.copy()
        present = np.ones(n, dtype=bool)
        reset_at = None
        if i in anomalous:
            kinds = rng.choice(ANOMALY_TYPES, size=int(rng.integers(1, 3)), replace=False,
                               p=[0.2, 0.16, 0.2, 0.16, 0.16, 0.12])
            for kind in kinds:
                s = int(rng.integers(24 * 30, n - 24 * 40))
                if kind == "leak_like_flow":
                    dur = int(rng.integers(20, 70)) * 24
                    rate = float(rng.uniform(0.03, 0.07))
                    true_m3[s:s + dur] += rate
                    counted_m3[s:s + dur] += rate
                    detail = f"{rate:.3f} m3/h continuous"
                elif kind == "stuck_meter":
                    dur = int(rng.integers(5, 26)) * 24
                    counted_m3[s:s + dur] = 0.0
                    detail = "pulses stop; gas still used"
                elif kind == "comms_outage":
                    dur = int(rng.integers(2, 11)) * 24
                    present[s:s + dur] = False
                    detail = "no readings; counter continues"
                elif kind == "magnet_tamper":
                    dur = int(rng.integers(7, 31)) * 24
                    counted_m3[s:s + dur] *= 0.25
                    logged = bool(rng.random() < 0.5)
                    if logged:
                        events.append((h.device_id, idx[s], "enclosure_open"))
                        events.append((h.device_id, idx[min(s + dur, n - 1)], "enclosure_closed"))
                    detail = "75% of pulses lost" + ("; enclosure event logged" if logged else "; no event")
                elif kind == "usage_spike":
                    dur = int(rng.integers(1, 5)) * 24
                    factor = float(rng.uniform(2.5, 4.0))
                    true_m3[s:s + dur] *= factor
                    counted_m3[s:s + dur] *= factor
                    detail = f"x{factor:.1f} for {dur // 24} day(s)"
                else:  # counter_reset
                    dur = 1
                    reset_at = s
                    events.append((h.device_id, idx[s], "reboot_counter_lost"))
                    detail = "cumulative counter restarts at 0"
                labels.append((h.device_id, kind, idx[s], idx[min(s + dur, n - 1)], detail))

        pulses = np.floor(np.cumsum(counted_m3) / PULSE_M3).astype(np.int64) + int(rng.integers(1000, 500000))
        if reset_at is not None:
            pulses[reset_at:] = pulses[reset_at:] - pulses[reset_at] + 1
        keep = present & (pulses >= 1)
        ts_utc = idx.tz_convert("UTC")
        readings.append(pd.DataFrame({
            "device_id": h.device_id,
            "ts_utc": ts_utc[keep],
            "sequence": np.arange(1, n + 1, dtype=np.int64)[keep],
            "pulse_count_total": pulses[keep],
        }))
        day = idx.normalize()
        daily.append(pd.DataFrame({"device_id": h.device_id, "date": day, "true_m3": true_m3,
                                   "recorded_m3": counted_m3}).groupby(["device_id", "date"], as_index=False).sum())

    readings_df = pd.concat(readings, ignore_index=True)
    readings_df["device_id"] = readings_df["device_id"].astype("category")
    return Fleet(
        devices=devices,
        weather=weather,
        readings=readings_df,
        events=pd.DataFrame(events, columns=["device_id", "ts_local", "event"]),
        labels=pd.DataFrame(labels, columns=["device_id", "anomaly", "start", "end", "detail"]),
        true_daily=pd.concat(daily, ignore_index=True),
        start=pd.Timestamp(start, tz="Asia/Tehran"),
        end=pd.Timestamp(end, tz="Asia/Tehran"),
    )
