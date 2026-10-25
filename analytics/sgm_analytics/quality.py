"""Data-quality layer (requirement AI-002) between raw readings and billing/analytics.

Turns cumulative pulse counts into interval consumption and flags:
  duplicate     same (device, sequence) seen more than once
  gap           readings missing between two consecutive sequences
  reset         cumulative counter went backwards (device lost its counter)
  implausible   interval flow above the meter's physical maximum
Nothing here silently "fixes" data: flags travel with the numbers so billing can
mark periods as estimated/suspect (BILL-006) and analytics can exclude them.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .fleet import PULSE_M3

G4_QMAX_M3H = 6.0  # maximum flow of a G4 household meter


def interval_consumption(readings: pd.DataFrame, pulse_m3: float = PULSE_M3,
                         expected_interval: pd.Timedelta = pd.Timedelta(hours=1)) -> pd.DataFrame:
    """Per-reading interval volume with quality flags, sorted by device and sequence."""
    # Positional index: input may come from concatenated batches with repeated labels.
    ordered = readings.sort_values(["device_id", "sequence"], kind="stable").reset_index(drop=True)
    dup = ordered.duplicated(["device_id", "sequence"], keep="first")
    df = ordered[~dup].copy()
    g = df.groupby("device_id", observed=True)
    d_pulse = g["pulse_count_total"].diff()
    d_seq = g["sequence"].diff()
    d_time = g["ts_utc"].diff()
    df["hours"] = d_time / pd.Timedelta(hours=1)
    df["flag_gap"] = d_seq > 1
    df["flag_reset"] = d_pulse < 0
    vol = d_pulse * pulse_m3
    # After a reset the new counter started at 1, so this interval only holds what
    # was counted since the reboot; the pre-reset remainder is unknown.
    vol = vol.where(~df["flag_reset"], (df["pulse_count_total"] - 1) * pulse_m3)
    hours = df["hours"].fillna(expected_interval / pd.Timedelta(hours=1)).clip(lower=1 / 60)
    df["flag_implausible"] = (vol / hours) > G4_QMAX_M3H
    df["volume_m3"] = vol
    df["first_reading"] = d_pulse.isna()
    df["duplicates_dropped"] = 0
    if dup.any():
        counts = ordered[dup].groupby("device_id", observed=True).size()
        df["duplicates_dropped"] = df["device_id"].map(counts).fillna(0).astype(int)
    return df


def daily_consumption(intervals: pd.DataFrame, tz: str = "Asia/Tehran") -> pd.DataFrame:
    """Daily volumes per device with a quality status column."""
    df = intervals[~intervals["first_reading"]].copy()
    df["date"] = df["ts_utc"].dt.tz_convert(tz).dt.normalize()
    agg = df.groupby(["device_id", "date"], observed=True).agg(
        volume_m3=("volume_m3", "sum"),
        readings=("sequence", "size"),
        gap=("flag_gap", "any"),
        reset=("flag_reset", "any"),
        implausible=("flag_implausible", "any"),
    ).reset_index()
    status = np.select([agg["reset"], agg["implausible"], agg["gap"] | (agg["readings"] < 20)],
                       ["reset", "implausible", "gap"], default="ok")
    agg["quality"] = status
    return agg


def quality_summary(intervals: pd.DataFrame) -> pd.DataFrame:
    g = intervals.groupby("device_id", observed=True)
    return pd.DataFrame({
        "readings": g.size(),
        "gaps": g["flag_gap"].sum(),
        "missing_readings": g.apply(lambda x: int((x["sequence"].diff().fillna(1) - 1).clip(lower=0).sum()),
                                    include_groups=False),
        "resets": g["flag_reset"].sum(),
        "implausible": g["flag_implausible"].sum(),
    }).reset_index()
