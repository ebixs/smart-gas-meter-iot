"""Single source of truth for the v0.2 controlled-rebuild schematic.

Every part, value, footprint and pin-to-net connection of
``smart_gas_meter_iot.kicad_sch`` is defined here. The schematic is generated
from this table by ``tools/generate_schematic.py`` and the KiCad-exported
netlist is checked back against it by ``check_netlist_matches_design.py``.

Status: engineering draft for a bench-only, low-voltage prototype. Values
marked "candidate" are taken from datasheet typical-application circuits and
must be re-verified before the schematic is frozen. Nothing here authorises
fabrication or connection to a live gas meter, gas line or utility wiring.
"""
from __future__ import annotations

from dataclasses import dataclass, field

LIB = "SGM"  # project-local symbol and footprint library nickname

# Nets that are intentionally distinct (CONTROLLED_REBUILD_SPEC.md).
POWER_NETS = ("USB_VBUS", "+5V", "+3V3", "GND", "MODEM_VIN")


@dataclass
class Part:
    ref: str
    symbol: str  # symbol name in the project library (copied from KiCad 7.0.11 stock libraries)
    value: str
    footprint: str  # footprint name in lib/SGM.pretty
    at: tuple[float, float]  # placement on the A3 sheet, mm
    pins: dict[str, str]  # pin number -> net name; "NC" = intentional no-connect
    block: str
    note: str = ""
    mpn: str = "TBD"
    dnp: bool = False
    fields: dict[str, str] = field(default_factory=dict)


NC = "NC"

PARTS: list[Part] = [
    # ------------------------------------------------------------------ 1. USB-C input
    Part("J1", "USB_C_Receptacle_USB2.0_16P", "USB-C receptacle (USB 2.0, sink)",
         "USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal", (38.1, 66.04),
         {"A4": "USB_VBUS", "A9": "USB_VBUS", "B4": "USB_VBUS", "B9": "USB_VBUS",
          "A5": "USB_CC1", "B5": "USB_CC2",
          "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DN", "B7": "USB_DN",
          "A8": NC, "B8": NC,
          "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "S1": "GND"},
         "usb", "Footprint/pin map must be checked against the selected connector drawing",
         mpn="GCT USB4105-GF-A (candidate)"),
    Part("R1", "R", "5.1k 1%", "R_0603_1608Metric", (68.58, 99.06),
         {"1": "USB_CC1", "2": "GND"}, "usb", "USB-C sink Rd on CC1"),
    Part("R2", "R", "5.1k 1%", "R_0603_1608Metric", (81.28, 99.06),
         {"1": "USB_CC2", "2": "GND"}, "usb", "USB-C sink Rd on CC2"),
    Part("F1", "Polyfuse", "PTC 0.75A hold, >=6V", "Fuse_1206_3216Metric", (68.58, 40.64),
         {"1": "USB_VBUS", "2": "+5V"}, "usb", "Resettable input protection; size after load budget"),
    Part("D1", "D_TVS", "TVS 5V standoff (candidate SMAJ5.0CA)", "D_SMA", (88.9, 53.34),
         {"1": "+5V", "2": "GND"}, "usb", "VBUS surge clamp after the fuse", mpn="SMAJ5.0CA (candidate)"),
    Part("U2", "USBLC6-2SC6", "USBLC6-2SC6", "SOT-23-6", (99.06, 81.28),
         {"1": "USB_DN", "6": "USB_DN", "3": "USB_DP", "4": "USB_DP", "5": "+5V", "2": "GND"},
         "usb", "Low-capacitance USB ESD array; place at the connector", mpn="STMicroelectronics USBLC6-2SC6"),

    # ------------------------------------------------------------------ 2. 3V3 buck regulator
    Part("U3", "AP63203WU", "AP63203WU-7 (3.3V buck)", "TSOT-23-6", (160.02, 50.8),
         {"3": "+5V", "2": "+5V", "4": "GND", "5": "REG_SW", "6": "REG_BST", "1": "+3V3"},
         "power", "Fixed 3.3V: FB senses the output; EN tied to VIN (datasheet: auto start-up)",
         mpn="Diodes Inc. AP63203WU-7"),
    Part("C1", "C", "10uF 25V X7R", "C_1206_3216Metric", (127.0, 66.04),
         {"1": "+5V", "2": "GND"}, "power", "Buck input capacitor (datasheet CIN)"),
    Part("C2", "C", "100nF 50V", "C_0603_1608Metric", (142.24, 66.04),
         {"1": "+5V", "2": "GND"}, "power", "High-frequency input bypass, close to VIN"),
    Part("C3", "C", "100nF 25V", "C_0603_1608Metric", (185.42, 33.02),
         {"1": "REG_BST", "2": "REG_SW"}, "power", "Bootstrap capacitor between BST and SW (datasheet CBST)"),
    Part("L1", "L", "3.9uH, Isat>=3A (candidate)", "L_Taiyo-Yuden_NR-40xx", (195.58, 50.8),
         {"1": "REG_SW", "2": "+3V3"}, "power", "Datasheet table value for 3.3V output"),
    Part("C4", "C", "22uF 10V X7R", "C_0805_2012Metric", (205.74, 66.04),
         {"1": "+3V3", "2": "GND"}, "power", "Buck output capacitor 1/2 (datasheet 2x22uF)"),
    Part("C5", "C", "22uF 10V X7R", "C_0805_2012Metric", (220.98, 66.04),
         {"1": "+3V3", "2": "GND"}, "power", "Buck output capacitor 2/2"),

    # ------------------------------------------------------------------ 3. ESP32-S3 module
    Part("U1", "ESP32-S3-WROOM-1", "ESP32-S3-WROOM-1-N8", "ESP32-S3-WROOM-1", (213.36, 165.1),
         {"2": "+3V3", "1": "GND", "40": "GND", "41": "GND",
          "3": "MCU_EN", "27": "BOOT_N",
          "13": "USB_DN", "14": "USB_DP",
          "4": "PULSE_IN", "5": "LED_DRV", "6": "I2C_SDA", "7": "I2C_SCL",
          "8": "TAMPER_IN",
          "10": "MODEM_TXD", "11": "MODEM_RXD",
          "17": "MODEM_EN", "18": "MODEM_RESET", "19": "MODEM_STATUS",
          "37": "DBG_TXD", "36": "DBG_RXD",
          # Unused GPIOs, intentionally unconnected. IO3/IO45/IO46 are strapping
          # pins left at their datasheet default state.
          "12": NC, "15": NC, "16": NC, "9": NC, "20": NC, "21": NC, "22": NC,
          "23": NC, "24": NC, "25": NC, "26": NC, "28": NC, "29": NC, "30": NC,
          "31": NC, "32": NC, "33": NC, "34": NC, "35": NC, "38": NC, "39": NC},
         "mcu", "Pin numbers per KiCad RF_Module symbol = Espressif datasheet pin table",
         mpn="Espressif ESP32-S3-WROOM-1-N8"),
    Part("C6", "C", "10uF 10V X7R", "C_0805_2012Metric", (165.1, 124.46),
         {"1": "+3V3", "2": "GND"}, "mcu", "Module bulk decoupling at the 3V3 pin"),
    Part("C7", "C", "100nF 16V", "C_0603_1608Metric", (180.34, 124.46),
         {"1": "+3V3", "2": "GND"}, "mcu", "Module HF decoupling at the 3V3 pin"),
    Part("R3", "R", "10k", "R_0603_1608Metric", (149.86, 129.54),
         {"1": "+3V3", "2": "MCU_EN"}, "mcu", "EN pull-up (Espressif RC delay R=10k)"),
    Part("C8", "C", "1uF 16V", "C_0603_1608Metric", (149.86, 167.64),
         {"1": "MCU_EN", "2": "GND"}, "mcu", "EN delay capacitor (Espressif RC delay C=1uF)"),
    Part("SW1", "SW_Push", "RESET", "SW_SPST_TL3342", (134.62, 162.56),
         {"1": "MCU_EN", "2": "GND"}, "mcu", "Pulls EN low to reset"),
    Part("R4", "R", "10k", "R_0603_1608Metric", (119.38, 129.54),
         {"1": "+3V3", "2": "BOOT_N"}, "mcu", "GPIO0 strapping pull-up (run from flash by default)"),
    Part("SW2", "SW_Push", "BOOT", "SW_SPST_TL3342", (106.68, 175.26),
         {"1": "BOOT_N", "2": "GND"}, "mcu", "Hold during reset for USB download mode"),

    # ------------------------------------------------------------------ 4. Synthetic pulse input
    Part("J2", "Conn_01x02", "PULSE_IN (synthetic 3.3V lab signal only)", "PinHeader_1x02_P2.54mm_Vertical",
         (279.4, 50.8), {"1": "PULSE_EXT", "2": "GND"}, "pulse",
         "Max 3.3V logic or dry contact to GND. Never connect a live meter or field wiring"),
    Part("R5", "R", "10k", "R_0603_1608Metric", (330.2, 43.18),
         {"1": "+3V3", "2": "PULSE_EXT"}, "pulse", "Defined idle-high state / dry-contact pull-up"),
    Part("R6", "R", "1k", "R_0603_1608Metric", (345.44, 63.5),
         {"1": "PULSE_EXT", "2": "PULSE_IN"}, "pulse", "Series current limit; place near the MCU pin"),
    Part("C9", "C", "100nF (DNP)", "C_0603_1608Metric", (360.68, 76.2),
         {"1": "PULSE_IN", "2": "GND"}, "pulse", "Optional RC filter footprint, not fitted by default", dnp=True),

    # ------------------------------------------------------------------ 5. Status LED
    Part("R7", "R", "1k", "R_0603_1608Metric", (279.4, 121.92),
         {"1": "LED_DRV", "2": "LED_A"}, "status", "~1.3mA with a 2V LED; adjust after LED selection"),
    Part("D2", "LED", "Green LED", "LED_0603_1608Metric", (302.26, 134.62),
         {"2": "LED_A", "1": "GND"}, "status", "Active-high status LED (pin 2 = anode)"),

    # ------------------------------------------------------------------ 6. Tamper input
    Part("J3", "Conn_01x02", "TAMPER switch", "PinHeader_1x02_P2.54mm_Vertical", (279.4, 172.72),
         {"1": "TAMPER_EXT", "2": "GND"}, "tamper",
         "Enclosure switch closed to GND when lid is closed; open = tamper (advisory only)"),
    Part("R8", "R", "10k", "R_0603_1608Metric", (330.2, 165.1),
         {"1": "+3V3", "2": "TAMPER_EXT"}, "tamper", "Pull-up: wire break or lid open reads high"),
    Part("R9", "R", "1k", "R_0603_1608Metric", (345.44, 185.42),
         {"1": "TAMPER_EXT", "2": "TAMPER_IN"}, "tamper", "Series resistor"),
    Part("C10", "C", "100nF", "C_0603_1608Metric", (360.68, 198.12),
         {"1": "TAMPER_IN", "2": "GND"}, "tamper", "Debounce (~1ms with R9)"),

    # ------------------------------------------------------------------ 7. Expansion / debug
    Part("J4", "Conn_01x04", "I2C expansion (3.3V)", "PinHeader_1x04_P2.54mm_Vertical", (165.1, 251.46),
         {"1": "+3V3", "2": "I2C_SDA", "3": "I2C_SCL", "4": "GND"}, "io", "Optional 3.3V I2C sensors"),
    Part("R10", "R", "4.7k", "R_0603_1608Metric", (190.5, 251.46),
         {"1": "+3V3", "2": "I2C_SDA"}, "io", "I2C pull-up"),
    Part("R11", "R", "4.7k", "R_0603_1608Metric", (203.2, 251.46),
         {"1": "+3V3", "2": "I2C_SCL"}, "io", "I2C pull-up"),
    Part("J5", "Conn_01x03", "Debug UART0 (3.3V)", "PinHeader_1x03_P2.54mm_Vertical", (238.76, 251.46),
         {"1": "DBG_TXD", "2": "DBG_RXD", "3": "GND"}, "io",
         "Pin 1 = module TXD0 output; no power pin to avoid back-feeding"),

    # ------------------------------------------------------------------ 8. Cellular daughterboard interface
    Part("J6", "Conn_01x08", "Modem daughterboard interface", "PinHeader_1x08_P2.54mm_Vertical", (88.9, 228.6),
         {"1": "MODEM_VIN", "2": "GND", "3": "MODEM_TXD", "4": "MODEM_RXD",
          "5": "MODEM_EN", "6": "MODEM_RESET", "7": "MODEM_STATUS", "8": "GND"}, "modem",
         "3.3V logic interface; daughterboard provides level translation and modem power design"),
    Part("J7", "Conn_01x02", "MODEM_VIN bench supply input", "PinHeader_1x02_P2.54mm_Vertical", (30.48, 220.98),
         {"1": "MODEM_VIN", "2": "GND"}, "modem",
         "Separate current-limited supply sized to the selected modem; never from +3V3"),
    Part("R12", "R", "100k", "R_0603_1608Metric", (129.54, 220.98),
         {"1": "MODEM_EN", "2": "GND"}, "modem", "Modem held disabled while MCU boots"),
    Part("R13", "R", "100k", "R_0603_1608Metric", (142.24, 220.98),
         {"1": "MODEM_RESET", "2": "GND"}, "modem", "Reset de-asserted by default (polarity per modem)"),

    # ------------------------------------------------------------------ 9. Test points
    Part("TP1", "TestPoint", "TP_5V", "TestPoint_Pad_D1.5mm", (30.48, 149.86), {"1": "+5V"}, "test"),
    Part("TP2", "TestPoint", "TP_3V3", "TestPoint_Pad_D1.5mm", (43.18, 149.86), {"1": "+3V3"}, "test"),
    Part("TP3", "TestPoint", "TP_GND", "TestPoint_Pad_D1.5mm", (55.88, 149.86), {"1": "GND"}, "test"),
    Part("TP4", "TestPoint", "TP_PULSE", "TestPoint_Pad_D1.5mm", (30.48, 170.18), {"1": "PULSE_IN"}, "test"),
    Part("TP5", "TestPoint", "TP_EN", "TestPoint_Pad_D1.5mm", (43.18, 170.18), {"1": "MCU_EN"}, "test"),
    Part("TP6", "TestPoint", "TP_BOOT", "TestPoint_Pad_D1.5mm", (55.88, 170.18), {"1": "BOOT_N"}, "test"),
    Part("TP7", "TestPoint", "TP_VMODEM", "TestPoint_Pad_D1.5mm", (30.48, 190.5), {"1": "MODEM_VIN"}, "test"),
    Part("TP8", "TestPoint", "TP_GND2", "TestPoint_Pad_D1.5mm", (43.18, 190.5), {"1": "GND"}, "test"),
    Part("TP9", "TestPoint", "TP_VBUS", "TestPoint_Pad_D1.5mm", (55.88, 190.5), {"1": "USB_VBUS"}, "test"),
]

# Power-flag locations (mm). A PWR_FLAG marks the net as driven for ERC because
# these rails are fed through passive parts (fuse, inductor) or the connector.
PWR_FLAGS = {"+5V": (226.06, 33.02), "+3V3": (241.3, 33.02), "GND": (256.54, 33.02)}

TITLE = "Smart Gas Meter IoT - carrier board v0.2 (controlled rebuild)"
REVISION = "0.2-draft2"
COMMENTS = (
    "ENGINEERING DRAFT - NOT FABRICATION READY. Generated from design_v02.py.",
    "Bench-only: current-limited low-voltage supply + synthetic 3.3V pulse source.",
    "Never connect to a live gas meter, gas line, valve, mains or field wiring.",
    "Candidate values from datasheet typical applications; verify before freeze.",
)


def expected_nets() -> dict[str, set[tuple[str, str]]]:
    """Return net name -> {(ref, pin)} for every non-NC connection."""
    nets: dict[str, set[tuple[str, str]]] = {}
    for part in PARTS:
        for pin, net in part.pins.items():
            if net != NC:
                nets.setdefault(net, set()).add((part.ref, pin))
    return nets
