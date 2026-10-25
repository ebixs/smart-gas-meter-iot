"""Bilingual (Persian/English) invoice PDF with a verification QR code.

The QR encodes only a verification URL with an opaque HMAC token (BILL-005):
no name, address or consumption is embedded. Every page carries an
"ILLUSTRATIVE - NOT A REAL BILL" marking (BILL-008).
"""
from __future__ import annotations

import io
from pathlib import Path

import arabic_reshaper
import qrcode
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .billing import Invoice
from .climate import CITIES
from .jalali import MONTHS_EN, MONTHS_FA

FONT_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"
VERIFY_BASE = "https://ebixs.github.io/smart-gas-meter-iot/verify/#"

INK = colors.HexColor("#0F172A")
MUTED = colors.HexColor("#64748B")
ACCENT = colors.HexColor("#0E7C66")
ACCENT_SOFT = colors.HexColor("#E6F4F0")
WARN = colors.HexColor("#B45309")
LINE = colors.HexColor("#E2E8F0")
# Ordinal one-hue ramp (light -> dark = tier 1 -> 4), validated with the dataviz
# palette checker (--ordinal): monotone lightness, single hue, light end >= 2:1.
TIER_COLORS = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]

_registered = False


def _fonts() -> None:
    global _registered
    if not _registered:
        pdfmetrics.registerFont(TTFont("Vazir", str(FONT_DIR / "Vazirmatn-Regular.ttf")))
        pdfmetrics.registerFont(TTFont("Vazir-Bold", str(FONT_DIR / "Vazirmatn-Bold.ttf")))
        _registered = True


def fa(text: str) -> str:
    """Shape and reorder Persian text for left-to-right PDF drawing."""
    return get_display(arabic_reshaper.reshape(text))


def fa_num(value: object) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def money(n: int) -> str:
    return f"{n:,}"


def _qr(data: str) -> ImageReader:
    img = qrcode.make(data, box_size=6, border=1)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def render_invoice(inv: Invoice, path: Path) -> Path:
    _fonts()
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    m = 16 * mm
    jy, jm = (int(x) for x in inv.period_jalali.split("/"))
    city = CITIES[inv.city]

    # Header band
    c.setFillColor(INK)
    c.rect(0, h - 34 * mm, w, 34 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Vazir-Bold", 17)
    c.drawString(m, h - 15 * mm, "Smart Gas Meter IoT")
    c.setFont("Vazir", 9.5)
    c.drawString(m, h - 21 * mm, "Gas consumption invoice  |  Lab prototype data platform")
    c.setFont("Vazir-Bold", 15)
    c.drawRightString(w - m, h - 15 * mm, fa("صورتحساب مصرف گاز"))
    c.setFont("Vazir", 9.5)
    c.drawRightString(w - m, h - 21 * mm, fa("کنتور هوشمند گاز — نمونه آزمایشگاهی"))
    c.setFillColor(WARN)
    c.roundRect(m, h - 31 * mm, w - 2 * m, 6.5 * mm, 2 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Vazir-Bold", 8.5)
    c.drawString(m + 3 * mm, h - 29 * mm, "ILLUSTRATIVE - NOT A REAL BILL - synthetic data, placeholder tariff")
    c.drawRightString(w - m - 3 * mm, h - 29 * mm, fa("نمایشی — قبض واقعی نیست"))

    # Identity block
    y = h - 46 * mm
    rows = [
        ("Invoice ID", inv.invoice_id, "شناسه صورتحساب"),
        ("Subscriber ref.", inv.subscriber_ref, "شماره اشتراک"),
        ("Device / meter", inv.device_id, "شناسه کنتور"),
        ("City / region", f"{city.name_en} / {inv.tariff_region}", f"شهر: {city.name_fa}"),
        ("Billing period", f"{MONTHS_EN[jm - 1]} {jy}  ({inv.period_start[:10]} to {inv.period_end[:10]}, end excl.)",
         f"دوره: {MONTHS_FA[jm - 1]} {fa_num(jy)}"),
        ("Status", inv.status, "وضعیت"),
    ]
    for label, value, label_fa in rows:
        c.setFillColor(MUTED)
        c.setFont("Vazir", 8.5)
        c.drawString(m, y, label)
        c.drawRightString(w - m, y, fa(label_fa))
        c.setFillColor(WARN if label == "Status" and "PROVISIONAL" in value else INK)
        c.setFont("Vazir-Bold", 10)
        c.drawString(m + 34 * mm, y, value)
        y -= 6.4 * mm

    # Consumption vs pattern card
    y -= 3 * mm
    card_h = 34 * mm
    c.setFillColor(ACCENT_SOFT)
    c.roundRect(m, y - card_h, w - 2 * m, card_h, 3 * mm, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont("Vazir-Bold", 22)
    c.drawString(m + 5 * mm, y - 12 * mm, f"{inv.consumption_m3:,.1f} m³")
    c.setFont("Vazir", 8.5)
    c.setFillColor(MUTED)
    c.drawString(m + 5 * mm, y - 17 * mm, "consumption this period")
    prev = "-" if inv.previous_reading_pulses is None else f"{inv.previous_reading_pulses:,}"
    cur = "-" if inv.current_reading_pulses is None else f"{inv.current_reading_pulses:,}"
    c.drawString(m + 5 * mm, y - 23 * mm, f"Meter reading (pulses, 0.01 m³/pulse): {prev}  ->  {cur}")
    c.drawRightString(w - m - 5 * mm, y - 12 * mm, fa(f"مصرف دوره: {fa_num(f'{inv.consumption_m3:.1f}')} مترمکعب"))
    c.drawRightString(w - m - 5 * mm, y - 17 * mm, fa(f"الگوی مصرف منطقه: {fa_num(f'{inv.pattern_m3:.0f}')} مترمکعب"))
    # bar: consumption against pattern multiples
    bx, by, bw, bh = m + 5 * mm, y - 30 * mm, w - 2 * m - 10 * mm, 3.2 * mm
    scale_max = max(inv.consumption_m3, inv.pattern_m3 * 2.2, 1)
    edges = [0, 1.0, 1.5, 2.0, scale_max / max(inv.pattern_m3, 1e-9)]
    for i in range(4):
        x0 = bx + bw * min(1, edges[i] * inv.pattern_m3 / scale_max)
        x1 = bx + bw * min(1, edges[i + 1] * inv.pattern_m3 / scale_max)
        c.setFillColor(colors.HexColor(TIER_COLORS[i]))
        c.setFillAlpha(0.25)
        c.rect(x0, by, max(0, x1 - x0), bh, fill=1, stroke=0)
    c.setFillAlpha(1)
    c.setFillColor(INK)
    used = bw * min(1, inv.consumption_m3 / scale_max)
    c.rect(bx, by + 0.9 * mm, used, bh - 1.8 * mm, fill=1, stroke=0)
    c.setFont("Vazir", 7)
    c.setFillColor(MUTED)
    for mult in (1.0, 1.5, 2.0):
        x = bx + bw * min(1, mult * inv.pattern_m3 / scale_max)
        c.drawCentredString(x, by - 3 * mm, f"{mult:g}x pattern")

    # Tier table
    y = y - card_h - 9 * mm
    c.setFont("Vazir-Bold", 10.5)
    c.setFillColor(INK)
    c.drawString(m, y, "Charges by tier")
    c.drawRightString(w - m, y, fa("محاسبه پلکانی"))
    y -= 6 * mm
    cols = [m, m + 22 * mm, m + 70 * mm, m + 105 * mm, w - m]
    c.setFont("Vazir", 8)
    c.setFillColor(MUTED)
    for x, t in zip(cols[:4], ["Tier", "Range (m³)", "Quantity (m³)", "Price (IRR/m³)"]):
        c.drawString(x, y, t)
    c.drawRightString(cols[4], y, "Amount (IRR)")
    y -= 2.5 * mm
    c.setStrokeColor(LINE)
    c.line(m, y, w - m, y)
    for line in inv.tier_lines:
        y -= 6 * mm
        c.setFillColor(colors.HexColor(TIER_COLORS[line["tier"] - 1]))
        c.circle(m + 1.5 * mm, y + 1.1 * mm, 1.4 * mm, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont("Vazir", 9)
        c.drawString(m + 5 * mm, y, str(line["tier"]))
        rng = f"{line['from_m3']:,.0f} - " + ("..." if line["to_m3"] is None else f"{line['to_m3']:,.0f}")
        c.drawString(cols[1], y, rng)
        c.drawString(cols[2], y, f"{line['quantity_m3']:,.2f}")
        c.drawString(cols[3], y, money(line["price_per_m3"]))
        c.drawRightString(cols[4], y, money(line["amount"]))
    y -= 3 * mm
    c.line(m, y, w - m, y)
    for label, value, bold in (("Energy charge", inv.energy_charge, False), ("Fixed charge", inv.fixed_charge, False),
                               ("Tax", inv.tax, False), ("Total payable (IRR)", inv.total_payable, True)):
        y -= 6 * mm
        c.setFont("Vazir-Bold" if bold else "Vazir", 11 if bold else 9)
        c.setFillColor(ACCENT if bold else INK)
        c.drawString(cols[2], y, label)
        c.drawRightString(cols[4], y, money(value))
    y -= 7 * mm
    c.setFont("Vazir-Bold", 12)
    c.setFillColor(ACCENT)
    c.drawRightString(w - m, y, fa(f"مبلغ قابل پرداخت: {fa_num(money(inv.total_payable))} ریال"))

    # Quality notes
    y -= 10 * mm
    c.setFont("Vazir-Bold", 9.5)
    c.setFillColor(INK)
    c.drawString(m, y, "Data quality")
    c.setFont("Vazir", 8.5)
    notes = inv.quality_notes or ["All readings in this period passed quality checks."]
    for note in notes[:4]:
        y -= 5 * mm
        c.setFillColor(WARN if inv.quality_notes else MUTED)
        c.drawString(m + 3 * mm, y, f"- {note[:110]}")

    # QR + verification footer
    qr_size = 30 * mm
    url = VERIFY_BASE + inv.verify_token
    c.drawImage(_qr(url), w - m - qr_size, 18 * mm, qr_size, qr_size)
    c.setFillColor(MUTED)
    c.setFont("Vazir", 7.5)
    c.drawString(m, 40 * mm, f"Verify: scan the QR code. Token {inv.verify_token[:12]}... (opaque, signed; no personal data).")
    c.drawString(m, 35 * mm, f"Tariff version {inv.tariff_version}. Calculation trace is stored with the invoice.")
    c.drawString(m, 30 * mm, "Consumption anomaly flags are decision support only; they do not prove a gas leak.")
    c.drawRightString(w - m - qr_size - 4 * mm, 24 * mm, fa("برای استعلام، کد QR را اسکن کنید"))
    c.setStrokeColor(LINE)
    c.line(m, 14 * mm, w - m, 14 * mm)
    c.drawString(m, 10 * mm, "github.com/ebixs/smart-gas-meter-iot  |  synthetic demonstration")
    c.showPage()
    c.save()
    return path
