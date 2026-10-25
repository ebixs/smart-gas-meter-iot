"""Billing engine: versioned tiered/seasonal tariffs and reproducible invoices.

Implements the repository's billing requirements:
  BILL-001 versioned tariff records (effective date, currency, unit, rounding, jurisdiction)
  BILL-002 billing periods are half-open [start, end) intervals in an explicit timezone
  BILL-003 every invoice carries a reproducible calculation trace
  BILL-005 the QR code carries an opaque signed token, never personal data
  BILL-006 estimated/reset/suspect data marks the invoice PROVISIONAL, never silently final
  BILL-008 the tariff is ILLUSTRATIVE: no official billing until metrology/legal approval

Tariff structure modelled on Iran's 2025 residential reform (four standard tiers
measured against a consumption pattern derived from multi-year history and
climate region). Prices below are placeholders for demonstration only.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime

import pandas as pd

from .jalali import JDate, month_length, month_start, next_month, to_jalali

TZ = "Asia/Tehran"


@dataclass(frozen=True)
class Tier:
    upto_pattern_multiple: float | None  # upper bound as multiple of the pattern; None = no limit
    price_cold: int  # IRR per m3
    price_warm: int


@dataclass(frozen=True)
class TariffVersion:
    version_id: str
    jurisdiction: str
    effective_from: JDate
    status: str
    currency: str
    unit: str
    cold_months: tuple[int, ...]  # Jalali months billed at cold-season prices
    tiers: tuple[Tier, ...]
    fixed_charge: int  # per bill, IRR
    tax_rate: float
    rounding: int  # round the payable amount down to this many IRR

    def to_dict(self) -> dict:
        d = asdict(self)
        d["effective_from"] = str(self.effective_from)
        return d


ILLUSTRATIVE_TARIFF = TariffVersion(
    version_id="IR-RES-ILLUSTRATIVE-1404.08",
    jurisdiction="IR residential natural gas (structure only)",
    effective_from=JDate(1404, 8, 1),
    status="ILLUSTRATIVE - prices are placeholders, not an official tariff",
    currency="IRR",
    unit="m3",
    cold_months=(8, 9, 10, 11, 12, 1),  # Aban .. Farvardin
    tiers=(
        Tier(1.0, 2_500, 3_000),
        Tier(1.5, 6_000, 7_500),
        Tier(2.0, 15_000, 19_000),
        Tier(None, 40_000, 50_000),
    ),
    fixed_charge=50_000,
    tax_rate=0.10,
    rounding=1_000,
)


@dataclass
class Invoice:
    invoice_id: str
    device_id: str
    subscriber_ref: str
    city: str
    tariff_region: str
    period_jalali: str
    period_start: str
    period_end: str
    previous_reading_pulses: int | None
    current_reading_pulses: int | None
    consumption_m3: float
    pattern_m3: float
    tier_lines: list[dict]
    energy_charge: int
    fixed_charge: int
    tax: int
    total_payable: int
    currency: str
    tariff_version: str
    status: str
    quality_notes: list[str]
    verify_token: str
    trace: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def billing_period(jy: int, jm: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Half-open [start, end) for a Jalali month in Asia/Tehran (BILL-002)."""
    ny, nm = next_month(jy, jm)
    return (pd.Timestamp(month_start(jy, jm), tz=TZ), pd.Timestamp(month_start(ny, nm), tz=TZ))


def consumption_pattern(daily: pd.DataFrame, devices: pd.DataFrame, before: pd.Timestamp,
                        years: int = 5) -> pd.DataFrame:
    """Region x Jalali-month pattern: median household m3/day over up to ``years`` prior years.

    Only quality-OK days are used, so faults do not inflate or deflate the pattern.
    """
    d = daily[(daily["quality"] == "ok") & (daily["date"] < before)
              & (daily["date"] >= before - pd.DateOffset(years=years))]
    d = d.merge(devices[["device_id", "tariff_region"]], on="device_id")
    d["jmonth"] = [to_jalali(x.date()).month for x in d["date"]]
    per_household = d.groupby(["tariff_region", "jmonth", "device_id"], observed=True)["volume_m3"].mean()
    return per_household.groupby(["tariff_region", "jmonth"]).median().rename("pattern_m3_per_day").reset_index()


def sign_token(invoice_id: str, total: int, period: str, secret: bytes) -> str:
    msg = f"{invoice_id}|{total}|{period}".encode()
    digest = hmac.new(secret, msg, hashlib.sha256).digest()[:15]
    return base64.b32encode(digest).decode().rstrip("=")


def verify_token(invoice_id: str, total: int, period: str, token: str, secret: bytes) -> bool:
    return hmac.compare_digest(sign_token(invoice_id, total, period, secret), token)


def _tier_breakdown(consumption: float, pattern: float, tariff: TariffVersion, cold: bool) -> list[dict]:
    lines, lower = [], 0.0
    for n, tier in enumerate(tariff.tiers, start=1):
        upper = math.inf if tier.upto_pattern_multiple is None else tier.upto_pattern_multiple * pattern
        qty = max(0.0, min(consumption, upper) - lower)
        if qty > 0:
            price = tier.price_cold if cold else tier.price_warm
            lines.append({"tier": n, "from_m3": round(lower, 2),
                          "to_m3": None if math.isinf(upper) else round(upper, 2),
                          "quantity_m3": round(qty, 2), "price_per_m3": price, "amount": round(qty * price)})
        lower = upper
        if consumption <= upper:
            break
    return lines


def bill_device_month(device: pd.Series, intervals: pd.DataFrame, pattern: pd.DataFrame, jy: int, jm: int,
                      tariff: TariffVersion = ILLUSTRATIVE_TARIFF, secret: bytes = b"demo-secret",
                      review_flags: list[str] | None = None) -> Invoice:
    """Compute one illustrative invoice for a device and Jalali month from interval data."""
    start, end = billing_period(jy, jm)
    trace: list[dict] = [{"step": "period", "start": start.isoformat(), "end": end.isoformat(),
                          "rule": "half-open [start, end), Asia/Tehran"}]
    dev = intervals[intervals["device_id"] == device.device_id]
    local = dev["ts_utc"].dt.tz_convert(TZ)
    inside = dev[(local >= start) & (local < end)]
    before = dev[local < start]
    notes: list[str] = []

    prev_pulses = int(before["pulse_count_total"].iloc[-1]) if len(before) else None
    cur_pulses = int(inside["pulse_count_total"].iloc[-1]) if len(inside) else None
    usable = inside[~inside["first_reading"]] if prev_pulses is None else inside
    consumption = float(usable["volume_m3"].sum())
    if prev_pulses is None:
        notes.append("no reading before period start: consumption counted from first reading in period")
    if inside["flag_reset"].any():
        notes.append("counter reset inside period: consumption around the reset is incomplete")
    if inside["flag_implausible"].any():
        notes.append("implausible flow value inside period")
    hours_expected = (end - start) / pd.Timedelta(hours=1)
    last_gap_h = ((end - local[(local >= start) & (local < end)].max()) / pd.Timedelta(hours=1)) if len(inside) else hours_expected
    if len(inside) == 0:
        notes.append("no readings in period")
    elif last_gap_h > 24:
        rate = consumption / max(1.0, hours_expected - last_gap_h)
        estimate = rate * last_gap_h
        notes.append(f"no reading for the last {last_gap_h:.0f} h: {estimate:.1f} m3 estimated from period average")
        consumption += estimate
    trace.append({"step": "readings", "previous_pulses": prev_pulses, "current_pulses": cur_pulses,
                  "intervals_used": int(len(usable)), "consumption_m3": round(consumption, 3),
                  "rule": "sum of quality-checked interval volumes (handles counter resets and gaps)"})

    row = pattern[(pattern["tariff_region"] == device.tariff_region) & (pattern["jmonth"] == jm)]
    per_day = float(row["pattern_m3_per_day"].iloc[0]) if len(row) else 0.0
    days = month_length(jy, jm)
    pattern_m3 = per_day * days
    trace.append({"step": "pattern", "region": device.tariff_region, "jalali_month": jm,
                  "median_m3_per_day": round(per_day, 3), "days": days, "pattern_m3": round(pattern_m3, 2),
                  "rule": "median household m3/day for region and month over up to 5 prior years (quality-OK days)"})

    cold = jm in tariff.cold_months
    lines = _tier_breakdown(consumption, pattern_m3, tariff, cold)
    energy = int(sum(line["amount"] for line in lines))
    tax = round((energy + tariff.fixed_charge) * tariff.tax_rate)
    total = int((energy + tariff.fixed_charge + tax) // tariff.rounding * tariff.rounding)
    trace.append({"step": "tiers", "season": "cold" if cold else "warm", "lines": lines})
    trace.append({"step": "amount", "energy": energy, "fixed": tariff.fixed_charge, "tax_rate": tariff.tax_rate,
                  "tax": tax, "rounded_down_to": tariff.rounding, "total": total})

    if review_flags:
        notes.extend(review_flags)
    status = "PROVISIONAL - needs review" if notes else "ILLUSTRATIVE FINAL"
    invoice_id = f"INV-{jy}{jm:02d}-{device.device_id}"
    period = f"{jy:04d}/{jm:02d}"
    return Invoice(
        invoice_id=invoice_id, device_id=device.device_id, subscriber_ref=device.subscriber_ref,
        city=device.city, tariff_region=device.tariff_region, period_jalali=period,
        period_start=start.isoformat(), period_end=end.isoformat(),
        previous_reading_pulses=prev_pulses, current_reading_pulses=cur_pulses,
        consumption_m3=round(consumption, 2), pattern_m3=round(pattern_m3, 2), tier_lines=lines,
        energy_charge=energy, fixed_charge=tariff.fixed_charge, tax=tax, total_payable=total,
        currency=tariff.currency, tariff_version=tariff.version_id, status=status, quality_notes=notes,
        verify_token=sign_token(invoice_id, total, period, secret), trace=trace,
    )


def invoice_json(inv: Invoice) -> str:
    return json.dumps(inv.to_dict(), ensure_ascii=False, indent=2, default=str)


def now_jalali() -> JDate:
    return to_jalali(datetime.now().date())
