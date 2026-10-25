"""Synthetic but climatologically plausible weather for Iranian cities.

Monthly mean temperatures are rounded approximations of long-term climate
normals, good enough to drive a heating-demand simulation. They are NOT an
authoritative climate dataset. Daily weather adds persistent (AR(1)) anomalies
and a diurnal cycle, so cold spells last several days as they do in reality.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class City:
    key: str
    name_en: str
    name_fa: str
    monthly_mean_c: tuple[float, ...]  # Jan..Dec
    diurnal_range_c: float  # typical daily max-min
    anomaly_sd_c: float  # day-to-day weather variability
    tariff_region: str  # illustrative climate/tariff region label


CITIES: dict[str, City] = {
    c.key: c
    for c in (
        City("tehran", "Tehran", "تهران",
             (4.0, 6.5, 11.5, 17.5, 23.0, 28.5, 31.5, 30.5, 26.0, 19.5, 11.5, 6.0), 11.0, 2.8, "temperate"),
        City("shahrekord", "Shahrekord", "شهرکرد",
             (-3.0, -0.5, 4.5, 10.5, 15.5, 21.0, 24.5, 23.5, 18.5, 12.0, 5.0, -0.5), 15.0, 3.5, "cold"),
        City("tabriz", "Tabriz", "تبریز",
             (-1.5, 1.0, 6.5, 12.5, 17.5, 23.0, 27.0, 26.5, 21.5, 14.5, 7.0, 1.0), 12.0, 3.3, "cold"),
        City("mashhad", "Mashhad", "مشهد",
             (2.5, 4.5, 9.5, 15.5, 20.5, 25.5, 27.5, 25.5, 21.0, 15.0, 8.5, 3.5), 13.0, 3.0, "temperate"),
        City("rasht", "Rasht", "رشت",
             (7.0, 7.5, 10.0, 14.5, 19.5, 23.5, 25.5, 25.5, 22.5, 18.0, 13.0, 9.0), 7.0, 2.2, "mild-humid"),
        City("ahvaz", "Ahvaz", "اهواز",
             (12.5, 15.0, 19.5, 26.0, 32.5, 37.0, 38.5, 38.0, 34.5, 28.0, 20.0, 14.0), 13.0, 2.0, "hot"),
    )
}


def _seasonal_curve(city: City, days: pd.DatetimeIndex) -> np.ndarray:
    """Smooth daily climatology by interpolating monthly means placed mid-month."""
    doy = days.dayofyear.to_numpy() - 1
    anchors = np.array([15, 45, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349], dtype=float)
    means = np.array(city.monthly_mean_c)
    x = np.concatenate([anchors - 365, anchors, anchors + 365])
    y = np.concatenate([means, means, means])
    return np.interp(doy, x, y)


def daily_weather(city: City, start: str, end: str, seed: int) -> pd.DataFrame:
    """Daily mean temperature with AR(1) anomalies (phi=0.75, ~4-day persistence)."""
    days = pd.date_range(start, end, freq="D", tz="Asia/Tehran", inclusive="left")
    rng = np.random.default_rng(seed)
    clim = _seasonal_curve(city, days)
    phi = 0.75
    noise = rng.normal(0.0, city.anomaly_sd_c * np.sqrt(1 - phi**2), len(days))
    anomaly = np.zeros(len(days))
    for i in range(1, len(days)):
        anomaly[i] = phi * anomaly[i - 1] + noise[i]
    return pd.DataFrame({"date": days, "t_mean_c": clim + anomaly, "t_clim_c": clim})


def hourly_temperature(daily: pd.DataFrame, city: City) -> pd.Series:
    """Expand to hourly with a diurnal cycle (minimum ~05:00, maximum ~15:00)."""
    idx = pd.date_range(daily["date"].iloc[0], periods=len(daily) * 24, freq="h")
    t_mean = np.repeat(daily["t_mean_c"].to_numpy(), 24)
    hour = idx.hour.to_numpy()
    diurnal = 0.5 * city.diurnal_range_c * np.cos(2 * np.pi * (hour - 15) / 24)
    return pd.Series(t_mean + diurnal, index=idx, name="t_c")
