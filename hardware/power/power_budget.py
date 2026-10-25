"""Battery-life model for the v0.3 power decision (docs/hardware-decisions.md).

Every number is an explicit assumption with its source; change one and rerun:
    python hardware/power/power_budget.py            # table to stdout
    python hardware/power/power_budget.py --plot out.png

The model is deliberately simple (average current = sleep floor + per-event charge
spread over a day). It is meant to rank options and show which term dominates,
not to replace a measured profile with a current analyser on the real board.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field

# ---------------------------------------------------------------- sources
# [S3]  Espressif low-power guide: ESP32-S3 light-sleep 240 uA, deep-sleep 7 uA.
# [BG95] Quectel BG95 Series Specification V1.7: PSM 3.9 uA; Cat-M1 sleep 1.89 mA (DRX 1.28 s);
#        TX 193 mA at 21 dBm.
# [EC200U] Quectel EC200U Series Specification V1.4: LTE sleep 1.4-1.5 mA; no PSM listed.
# [INZ]  Elster IN-Z61 pulse transmitter: reed contact, min closing time 0.25 s.
# Session charge (attach + TLS-less HTTP POST + RRC release) is an engineering estimate,
# to be replaced by a measurement; see SESSION_* below.

PULSE_M3 = 0.01           # m3 per pulse, typical G4 index drum; verify per meter model
FLEET_M3_PER_YEAR = {"median": 2250, "p90": 4500, "p99": 8000}  # simulated fleet (analytics)


@dataclass
class Battery:
    name: str
    capacity_mah: float
    usable_fraction: float  # derating for passivation, temperature and 10-year self-discharge


LI_SOCL2_D = Battery("Li-SOCl2 D-cell 3.6 V 19 Ah + hybrid layer capacitor", 19000, 0.70)
LI_SOCL2_2D = Battery("2 x Li-SOCl2 D-cell in parallel (38 Ah)", 38000, 0.70)


@dataclass
class Scenario:
    key: str
    label: str
    mcu_sleep_ua: float           # MCU floor while waiting for pulses
    wake_per_pulse_mas: float     # charge per pulse wake-up (mA*s)
    pullup_ua_avg: float          # pull-up current averaged over time (contact may rest closed)
    regulator_iq_ua: float
    modem_floor_ua: float         # modem between sessions (PSM, sleep or switched off)
    sessions_per_day: float
    session_mas: float            # charge per upload session (mA*s)
    notes: str = ""
    battery: Battery = field(default_factory=lambda: LI_SOCL2_D)

    def avg_ua(self, m3_per_year: float) -> dict[str, float]:
        pulses_per_day = m3_per_year / PULSE_M3 / 365
        parts = {
            "MCU sleep": self.mcu_sleep_ua,
            "pulse wake-ups": pulses_per_day * self.wake_per_pulse_mas / 86400 * 1000,
            "pull-up": self.pullup_ua_avg,
            "regulator": self.regulator_iq_ua,
            "modem idle": self.modem_floor_ua,
            "uploads": self.sessions_per_day * self.session_mas / 86400 * 1000,
        }
        parts["total"] = sum(parts.values())
        return parts

    def years(self, m3_per_year: float) -> float:
        b = self.battery
        return b.capacity_mah * b.usable_fraction / (self.avg_ua(m3_per_year)["total"] / 1000) / 8760


# Wake-up on a pulse from deep sleep: ROM + 2nd-stage boot ~40 ms at ~35 mA (estimate).
WAKE_DEEP_MAS = 0.040 * 35
# Handling a pulse while in automatic light sleep: ~3 ms at ~25 mA (estimate).
WAKE_LIGHT_MAS = 0.003 * 25
# A 10 kOhm pull-up that rests closed (magnet parked on the reed) draws 330 uA forever.
PULLUP_10K_WORST_UA = 3.3 / 10_000 * 1e6
# Edge-armed 1 MOhm pull-up plus input leakage.
PULLUP_1M_UA = 3.3 / 1_000_000 * 1e6
# LTE-M from PSM: wake, RRC connect, POST, release: ~12 s at ~80 mA average (estimate).
SESSION_LTEM_MAS = 12 * 80
# Cat-1 from power-off: boot + attach + POST + orderly power-down: ~35 s at ~110 mA (estimate).
SESSION_CAT1_COLD_MAS = 35 * 110

SCENARIOS = [
    Scenario("v02-as-is", "v0.2 board as drawn on a battery (light sleep, 10k pull-up resting closed, "
             "modem kept registered, hourly upload)", 240, WAKE_LIGHT_MAS, PULLUP_10K_WORST_UA, 22,
             1890, 24, SESSION_LTEM_MAS / 3,
             "What happens without power design: the radio's idle floor dominates."),
    Scenario("ltem-daily", "Deep sleep + pulse wake, 1 MOhm pull-up, BG95-M3 LTE-M in PSM, one upload per day",
             7, WAKE_DEEP_MAS, PULLUP_1M_UA, 1, 3.9, 1, SESSION_LTEM_MAS,
             "Recommended battery architecture if the operator offers LTE-M with PSM."),
    Scenario("ltem-4x", "Same, four uploads per day", 7, WAKE_DEEP_MAS, PULLUP_1M_UA, 1, 3.9, 4, SESSION_LTEM_MAS),
    Scenario("cat1-daily", "Deep sleep, EC200U Cat-1 switched off between daily uploads", 7, WAKE_DEEP_MAS,
             PULLUP_1M_UA, 1, 1.0, 1, SESSION_CAT1_COLD_MAS,
             "Works on today's Iranian LTE bands (B1/B3/B7/B8) without LTE-M support."),
    Scenario("cat1-daily-2d", "Cat-1 daily, two D-cells", 7, WAKE_DEEP_MAS, PULLUP_1M_UA, 1, 1.0, 1,
             SESSION_CAT1_COLD_MAS, battery=LI_SOCL2_2D),
    Scenario("cat1-sleep", "Cat-1 left registered in sleep (no PSM), daily upload", 7, WAKE_DEEP_MAS,
             PULLUP_1M_UA, 1, 1400, 1, SESSION_LTEM_MAS),
]


def table(m3: float) -> str:
    head = "| Scenario | Avg current | Uploads | Pulse wakes | Modem idle | Life (years) |\n|---|---:|---:|---:|---:|---:|"
    rows = []
    for s in SCENARIOS:
        a = s.avg_ua(m3)
        rows.append(f"| {s.label} | {a['total']:.0f} uA | {a['uploads']:.1f} uA | {a['pulse wake-ups']:.1f} uA "
                    f"| {a['modem idle']:.1f} uA | {s.years(m3):.1f} |")
    return head + "\n" + "\n".join(rows)


def plot(path: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, ink2, muted, grid = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
    colors = {"median": "#86b6ef", "p90": "#3987e5", "p99": "#0d366b"}  # ordinal ramp: more gas, darker
    short = {"v02-as-is": "v0.2 as drawn", "ltem-daily": "LTE-M PSM, daily", "ltem-4x": "LTE-M PSM, 4x/day",
             "cat1-daily": "Cat-1 off between, daily", "cat1-daily-2d": "Cat-1 daily, 2 cells",
             "cat1-sleep": "Cat-1 kept in sleep"}
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=150)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    keys = [s.key for s in SCENARIOS]
    y = range(len(keys))
    h = 0.26
    for k, (name, m3) in enumerate(FLEET_M3_PER_YEAR.items()):
        vals = [min(s.years(m3), 20) for s in SCENARIOS]
        ax.barh([i + (k - 1) * h for i in y], vals, height=h - 0.03, color=colors[name],
                label=f"{name} household ({m3:,} m3/yr)")
        if name == "median":
            for i, v in zip(y, vals):
                ax.text(v + 0.3, i - h, ("20+ y" if v >= 20 else f"{v:.1f} y"), va="center", fontsize=8, color=ink2)
    ax.axvline(10, color=muted, lw=1, ls="--")
    ax.text(10.2, len(keys) - 0.45, "10-year target", fontsize=8, color=muted)
    ax.set_yticks(list(y), [short[k] for k in keys], fontsize=9, color=ink2)
    ax.invert_yaxis()
    ax.set_xlabel("battery life, years (19 Ah Li-SOCl2, 70% usable; capped at 20 = cell shelf life)", fontsize=9, color=ink2)
    ax.set_title("Battery life by power architecture", loc="left", fontsize=12, fontweight="bold", color=ink)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color("#c3c2b7")
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.tick_params(colors=muted, labelsize=8)
    ax.grid(axis="x", color=grid, lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(path, facecolor=fig.get_facecolor())


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--plot", help="write a PNG chart")
    args = p.parse_args()
    for name, m3 in FLEET_M3_PER_YEAR.items():
        print(f"\n### {name} household, {m3:,} m3/year ({m3 / PULSE_M3 / 365:.0f} pulses/day)\n")
        print(table(m3))
    if args.plot:
        plot(args.plot)


if __name__ == "__main__":
    main()
