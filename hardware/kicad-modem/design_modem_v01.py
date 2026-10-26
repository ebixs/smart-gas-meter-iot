"""Single source of truth for the cellular modem daughterboard v0.1 schematic.

The daughterboard plugs into carrier-board header J6 (1x08, 2.54 mm) and carries a
Quectel EC200U-EU LTE Cat 1 module, its VBAT reservoir, open-collector PWRKEY / RESET_N
drivers, 1.8 V <-> 3.3 V UART/STATUS level shifting, a micro-SIM holder with ESD
protection, a u.FL antenna connector with a pi matching network, a network-status LED
and test pads for the module's USB (firmware update) and debug UART.

Every part, value, footprint and pin-to-net connection of ``sgm_modem.kicad_sch`` is
defined here; ``tools/generate_schematic.py`` writes the schematic and
``check_netlist_matches_design.py`` checks the KiCad netlist back against this table.

Status: engineering draft, bench-only. The EC200U symbol pin numbers follow the Quectel
EC200U Series Hardware Design V1.0 pin table, but the FOOTPRINT IS PROVISIONAL: pad
geometry and pad-number positions were built from the partial dimensions in that
document and must be replaced by Quectel's "EC200U Series Footprint & Part" file
before any layout review or fabrication. Nothing here authorises connection to a live
gas meter, gas line, valve, mains or field wiring.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "kicad"))
from design_v02 import NC, Part  # noqa: E402  (same Part API as the carrier board)

LIB = "SGMM"  # project-local symbol and footprint library nickname

# Carrier-board nets that cross header J6 keep the carrier's names so the two
# netlists can be joined (MODEM_VIN is the module's VBAT on this board).
CARRIER_NETS = ("MODEM_VIN", "GND", "MODEM_TXD", "MODEM_RXD", "MODEM_EN", "MODEM_RESET", "MODEM_STATUS")
POWER_NETS = ("MODEM_VIN", "VDD_EXT", "USIM_VDD", "GND")

EC200U_GND = ["8", "9", "19", "22", "36", "46", "48", "50", "51", "52", "53", "54", "56", "72", "76"] + \
    [str(n) for n in range(85, 113)]

PARTS: list[Part] = [
    # ------------------------------------------------------------------ 1. Carrier interface + VBAT reservoir
    Part("J1", "Conn_01x08", "Carrier interface (mates carrier J6)", "PinSocket_1x08_P2.54mm_Vertical", (38.1, 63.5),
         {"1": "MODEM_VIN", "2": "GND", "3": "MODEM_TXD", "4": "MODEM_RXD",
          "5": "MODEM_EN", "6": "MODEM_RESET", "7": "MODEM_STATUS", "8": "GND"}, "carrier",
         "Socket on the bottom side; pin order identical to carrier J6. 3.3 V logic on pins 3-7"),
    Part("J2", "Conn_01x02", "Direct VBAT bench input (DNP)", "PinHeader_1x02_P2.54mm_Vertical", (38.1, 106.68),
         {"1": "MODEM_VIN", "2": "GND"}, "carrier",
         "Alternative short, heavy feed for 2 A bursts; fit only if carrier J7 is NOT used", dnp=True),
    Part("C1", "C_Polarized", "100uF 6.3V Ta", "CP_EIA-3528-21_Kemet-B", (66.04, 58.42),
         {"1": "MODEM_VIN", "2": "GND"}, "power", "Bulk reservoir at VBAT_RF (datasheet: ~100 uF, ESR ~0.7 ohm)"),
    Part("C2", "C_Polarized", "100uF 6.3V Ta", "CP_EIA-3528-21_Kemet-B", (86.36, 58.42),
         {"1": "MODEM_VIN", "2": "GND"}, "power", "Bulk reservoir at VBAT_BB"),
    Part("C3", "C", "100nF", "C_0402_1005Metric", (106.68, 58.42), {"1": "MODEM_VIN", "2": "GND"}, "power",
         "VBAT_RF MLCC array 1/3, at the pins"),
    Part("C4", "C", "33pF", "C_0402_1005Metric", (119.38, 58.42), {"1": "MODEM_VIN", "2": "GND"}, "power",
         "VBAT_RF MLCC array 2/3"),
    Part("C5", "C", "10pF", "C_0402_1005Metric", (132.08, 58.42), {"1": "MODEM_VIN", "2": "GND"}, "power",
         "VBAT_RF MLCC array 3/3"),
    Part("C6", "C", "100nF", "C_0402_1005Metric", (144.78, 58.42), {"1": "MODEM_VIN", "2": "GND"}, "power",
         "VBAT_BB MLCC array 1/3"),
    Part("C7", "C", "33pF", "C_0402_1005Metric", (157.48, 58.42), {"1": "MODEM_VIN", "2": "GND"}, "power",
         "VBAT_BB MLCC array 2/3"),
    Part("C8", "C", "10pF", "C_0402_1005Metric", (170.18, 58.42), {"1": "MODEM_VIN", "2": "GND"}, "power",
         "VBAT_BB MLCC array 3/3"),
    Part("D1", "D_TVS", "TVS 4.7V standoff (to select)", "D_SMB", (200.66, 58.42),
         {"1": "MODEM_VIN", "2": "GND"}, "power",
         "Datasheet asks for >=4.7 V reverse stand-off, high peak pulse power; select before freeze"),

    # ------------------------------------------------------------------ 2. EC200U module
    Part("U1", "EC200U", "EC200U-EU (LTE Cat 1)", "Quectel_EC200U_PROVISIONAL", (254.0, 139.7),
         {"57": "MODEM_VIN", "58": "MODEM_VIN", "59": "MODEM_VIN", "60": "MODEM_VIN",
          "21": "PWRKEY_N", "20": "RESET_N",
          "68": "M_RXD", "67": "M_TXD", "61": "M_STATUS", "6": "NET_STATUS", "5": NC,
          "11": "DBG_RXD", "12": "DBG_TXD", "115": "USB_BOOT",
          "7": "VDD_EXT", "14": "USIM_VDD", "17": "USIM_RST", "16": "USIM_CLK", "15": "USIM_DATA",
          "13": NC, "10": "GND", "49": "RF_MAIN",
          "71": "USB_VBUS", "69": "USB_DP", "70": "USB_DM",
          **{pin: "GND" for pin in EC200U_GND}},
         "module", "Pin numbers per Quectel EC200U HW Design V1.0 table; footprint PROVISIONAL",
         mpn="Quectel EC200U-EU (candidate)"),
    Part("C9", "C", "2.2uF", "C_0402_1005Metric", (200.66, 210.82), {"1": "VDD_EXT", "2": "GND"}, "module",
         "VDD_EXT (1.8 V, 50 mA max) decoupling, per datasheet"),

    # ------------------------------------------------------------------ 3. PWRKEY / RESET_N open-collector drivers
    Part("R1", "R", "4.7k", "R_0402_1005Metric", (73.66, 119.38), {"1": "MODEM_EN", "2": "Q1_B"}, "control",
         "MODEM_EN high (>= 2 s pulse) pulls PWRKEY low; carrier R12 holds it low at boot"),
    Part("R2", "R", "47k", "R_0402_1005Metric", (86.36, 119.38), {"1": "Q1_B", "2": "GND"}, "control",
         "Base pull-down: transistor off while MODEM_EN floats"),
    Part("Q1", "MMBT3904", "MMBT3904", "SOT-23", (109.22, 119.38),
         {"1": "Q1_B", "2": "GND", "3": "PWRKEY_N"}, "control",
         "Open-collector PWRKEY driver (datasheet Fig. 10); module pulls PWRKEY up internally"),
    Part("C16", "C", "10nF", "C_0402_1005Metric", (124.46, 119.38), {"1": "Q1_B", "2": "GND"}, "control",
         "Base filter against glitches on MODEM_EN (datasheet Fig. 10 shows 10 nF; position to confirm)"),
    Part("R3", "R", "4.7k", "R_0402_1005Metric", (142.24, 119.38), {"1": "MODEM_RESET", "2": "Q2_B"}, "control",
         "MODEM_RESET high pulls RESET_N low (active-low reset)"),
    Part("R4", "R", "47k", "R_0402_1005Metric", (154.94, 119.38), {"1": "Q2_B", "2": "GND"}, "control",
         "Base pull-down"),
    Part("Q2", "MMBT3904", "MMBT3904", "SOT-23", (177.8, 119.38),
         {"1": "Q2_B", "2": "GND", "3": "RESET_N"}, "control", "Open-collector RESET_N driver (datasheet Fig. 14)"),

    # ------------------------------------------------------------------ 4. 1.8 V <-> 3.3 V level shifting
    Part("Q3", "Q_NMOS_GSD", "DMG2302U", "SOT-23", (76.2, 170.18),
         {"1": "VDD_EXT", "2": "M_RXD", "3": "MODEM_TXD"}, "shift",
         "MCU TXD -> module MAIN_RXD. Gate at 1.8 V: needs Vgs(th) <= 1.0 V (BSS138 is marginal)"),
    Part("R5", "R", "10k", "R_0402_1005Metric", (91.44, 165.1), {"1": "VDD_EXT", "2": "M_RXD"}, "shift",
         "Module-side pull-up to VDD_EXT"),
    Part("Q4", "Q_NMOS_GSD", "DMG2302U", "SOT-23", (124.46, 170.18),
         {"1": "VDD_EXT", "2": "M_TXD", "3": "MODEM_RXD"}, "shift",
         "Module MAIN_TXD -> MCU RXD. 3.3 V side has no pull-up here: the carrier has no 3V3 on J6, "
         "so the ESP32 internal pull-up on MODEM_RXD must be enabled (review item)"),
    Part("R6", "R", "10k", "R_0402_1005Metric", (139.7, 165.1), {"1": "VDD_EXT", "2": "M_TXD"}, "shift",
         "Module-side pull-up to VDD_EXT"),
    Part("Q5", "Q_NMOS_GSD", "DMG2302U", "SOT-23", (172.72, 170.18),
         {"1": "VDD_EXT", "2": "M_STATUS", "3": "MODEM_STATUS"}, "shift",
         "Module STATUS -> MCU; same MCU-side pull-up requirement as Q4"),
    Part("R7", "R", "10k", "R_0402_1005Metric", (187.96, 165.1), {"1": "VDD_EXT", "2": "M_STATUS"}, "shift",
         "Module-side pull-up to VDD_EXT"),

    # ------------------------------------------------------------------ 5. Network status LED
    Part("R8", "R", "4.7k", "R_0402_1005Metric", (73.66, 220.98), {"1": "NET_STATUS", "2": "Q6_B"}, "led",
         "NET_STATUS is a 1.8 V output: it drives the LED through a transistor (datasheet 3.20)"),
    Part("R9", "R", "47k", "R_0402_1005Metric", (86.36, 220.98), {"1": "Q6_B", "2": "GND"}, "led", "Base pull-down"),
    Part("Q6", "MMBT3904", "MMBT3904", "SOT-23", (109.22, 220.98), {"1": "Q6_B", "2": "GND", "3": "LED_K"}, "led",
         "Low-side LED switch"),
    Part("R10", "R", "1k", "R_0402_1005Metric", (127.0, 213.36), {"1": "MODEM_VIN", "2": "LED_A"}, "led",
         "About 1.8 mA from a 3.8 V VBAT"),
    Part("D2", "LED", "Green LED", "LED_0603_1608Metric", (144.78, 226.06), {"1": "LED_K", "2": "LED_A"}, "led",
         "Network status: blink pattern per datasheet Table 27"),

    # ------------------------------------------------------------------ 6. (U)SIM
    Part("R11", "R", "0R", "R_0402_1005Metric", (322.58, 50.8), {"1": "USIM_RST", "2": "SIM_RST"}, "sim",
         "Series 0 ohm for debugging (datasheet 3.8)"),
    Part("R12", "R", "0R", "R_0402_1005Metric", (335.28, 50.8), {"1": "USIM_CLK", "2": "SIM_CLK"}, "sim",
         "Series 0 ohm"),
    Part("R13", "R", "0R", "R_0402_1005Metric", (347.98, 50.8), {"1": "USIM_DATA", "2": "SIM_DATA"}, "sim",
         "Series 0 ohm"),
    Part("C10", "C", "33pF", "C_0402_1005Metric", (322.58, 88.9), {"1": "SIM_RST", "2": "GND"}, "sim",
         "EGSM900 interference filter"),
    Part("C11", "C", "33pF", "C_0402_1005Metric", (335.28, 88.9), {"1": "SIM_CLK", "2": "GND"}, "sim",
         "EGSM900 interference filter"),
    Part("C12", "C", "33pF", "C_0402_1005Metric", (347.98, 88.9), {"1": "SIM_DATA", "2": "GND"}, "sim",
         "EGSM900 interference filter"),
    Part("R14", "R", "10k", "R_0402_1005Metric", (360.68, 50.8), {"1": "USIM_VDD", "2": "SIM_DATA"}, "sim",
         "USIM_DATA pull-up, close to the holder"),
    Part("C13", "C", "100nF", "C_0402_1005Metric", (373.38, 50.8), {"1": "USIM_VDD", "2": "GND"}, "sim",
         "USIM_VDD decoupling at the holder"),
    Part("U2", "ESD224DQA", "ESD224DQAR", "USON-10_2.5x1.0mm_P0.5mm", (330.2, 111.76),
         {"1": "SIM_RST", "10": "SIM_RST", "2": "SIM_CLK", "9": "SIM_CLK",
          "4": "SIM_DATA", "7": "SIM_DATA", "5": "USIM_VDD", "6": "USIM_VDD", "3": "GND", "8": "GND"}, "sim",
         "4-channel TVS array, 0.5 pF typ (datasheet asks for <= 15 pF); flow-through pins",
         mpn="Texas Instruments ESD224DQAR (candidate)"),
    Part("J3", "SIM_Card_SH", "micro-SIM holder", "microSIM_JAE_SF53S006VCBR2000", (393.7, 111.76),
         {"1": "USIM_VDD", "2": "SIM_RST", "3": "SIM_CLK", "5": "GND", "6": NC, "7": "SIM_DATA", "SH": "GND"},
         "sim", "Push-push micro-SIM (3FF); VPP unused", mpn="JAE SF53S006VCBR2000"),

    # ------------------------------------------------------------------ 7. Antenna
    Part("R15", "R", "0R", "R_0402_1005Metric", (322.58, 152.4), {"1": "RF_MAIN", "2": "RF_ANT"}, "rf",
         "Pi network series element; 50 ohm coplanar line to the u.FL"),
    Part("C14", "C", "NM", "C_0402_1005Metric", (309.88, 167.64), {"1": "RF_MAIN", "2": "GND"}, "rf",
         "Pi network shunt, not mounted by default (tune with the antenna)", dnp=True),
    Part("C15", "C", "NM", "C_0402_1005Metric", (335.28, 167.64), {"1": "RF_ANT", "2": "GND"}, "rf",
         "Pi network shunt, not mounted by default", dnp=True),
    Part("J4", "Conn_Coaxial", "u.FL antenna (LTE main)", "U.FL_Hirose_U.FL-R-SMT-1_Vertical", (360.68, 152.4),
         {"1": "RF_ANT", "2": "GND"}, "rf", "External LTE antenna on a u.FL pigtail", mpn="Hirose U.FL-R-SMT-1"),

    # ------------------------------------------------------------------ 8. USB download + debug test pads
    Part("R16", "R", "4.7k", "R_0402_1005Metric", (322.58, 213.36), {"1": "VDD_EXT", "2": "BOOT_PU"}, "test",
         "USB_BOOT pull-up source; must not be connected at normal start-up"),
    Part("JP1", "SolderJumper_2_Open", "USB_BOOT (open)", "SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
         (340.36, 220.98), {"1": "BOOT_PU", "2": "USB_BOOT"}, "test",
         "Close only to force USB download mode (datasheet 3.23)"),
    Part("TP1", "TestPoint", "VBUS", "TestPoint_Pad_D1.0mm", (236.22, 236.22), {"1": "USB_VBUS"}, "test"),
    Part("TP2", "TestPoint", "D+", "TestPoint_Pad_D1.0mm", (251.46, 236.22), {"1": "USB_DP"}, "test"),
    Part("TP3", "TestPoint", "D-", "TestPoint_Pad_D1.0mm", (266.7, 236.22), {"1": "USB_DM"}, "test"),
    Part("TP4", "TestPoint", "VDD_EXT", "TestPoint_Pad_D1.0mm", (281.94, 236.22), {"1": "VDD_EXT"}, "test"),
    Part("TP5", "TestPoint", "DBG_TX", "TestPoint_Pad_D1.0mm", (236.22, 259.08), {"1": "DBG_TXD"}, "test"),
    Part("TP6", "TestPoint", "DBG_RX", "TestPoint_Pad_D1.0mm", (251.46, 259.08), {"1": "DBG_RXD"}, "test"),
    Part("TP7", "TestPoint", "VBAT", "TestPoint_Pad_D1.0mm", (266.7, 259.08), {"1": "MODEM_VIN"}, "test"),
    Part("TP8", "TestPoint", "GND", "TestPoint_Pad_D1.0mm", (281.94, 259.08), {"1": "GND"}, "test"),
]

GENERIC_PARTS = {"J1", "J2", "TP1", "TP2", "TP3", "TP4", "TP5", "TP6", "TP7", "TP8", "JP1"}
for _p in PARTS:
    if _p.ref in GENERIC_PARTS:
        _p.mpn = "generic"
    if _p.dnp and "(DNP)" not in _p.value:
        _p.value += " (DNP)"

PWR_FLAGS = {"MODEM_VIN": (215.9, 33.02), "GND": (231.14, 33.02)}
BOARD_ONLY_FOOTPRINTS = ("MountingHole_2.7mm_M2.5",)

TITLE = "Smart Gas Meter IoT - cellular modem daughterboard v0.1 (EC200U)"
REVISION = "0.1-draft"
COMMENTS = (
    "ENGINEERING DRAFT - NOT FABRICATION READY. Generated from design_modem_v01.py.",
    "EC200U FOOTPRINT IS PROVISIONAL: replace with the Quectel footprint file before layout review.",
    "Bench-only: MODEM_VIN 3.8 V from a current-limited supply. Never on a live gas meter or gas line.",
    "Mates carrier v0.2 J6 (1x08). 3.3 V logic at the header, 1.8 V at the module.",
)


def expected_nets() -> dict[str, set[tuple[str, str]]]:
    """Return net name -> {(ref, pin)} for every non-NC connection."""
    nets: dict[str, set[tuple[str, str]]] = {}
    for part in PARTS:
        for pin, net in part.pins.items():
            if net != NC:
                nets.setdefault(net, set()).add((part.ref, pin))
    return nets
