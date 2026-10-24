"""Board-level placement for carrier board v0.2 (single source for the PCB).

Coordinates are millimetres from the board's top-left corner (x right, y down);
rotation is in degrees counter-clockwise as KiCad shows it. Every schematic part
in design_v02.PARTS must appear here; the build script fails otherwise.

Placement follows board-v0.2-layout-plan.md:
* ESP32-S3 module on the top edge so its antenna keep-out lies at/over the edge.
* USB-C on the left edge with CC resistors and the ESD array next to it.
* Compact AP63203 power loop in the lower-left corner, away from the pulse input.
* Lab interfaces (pulse, tamper, I2C, UART) as headers on the right edge.
* Modem daughterboard header and its separate supply input on the bottom edge.
* BOOT/RESET buttons and labelled test points reachable from the top side.
"""

BOARD_W = 100.0
BOARD_H = 70.0
ORIGIN = (100.0, 50.0)  # board top-left in KiCad page coordinates
CORNER_R = 2.0
LAYERS = 4  # F.Cu signal / In1 solid GND / In2 signal + 3V3 pour / B.Cu signal + GND pour

# ref: (x, y, rotation)
# The ESP32-S3 module sits right of centre: its left-hand pins (EN, IO4-IO7, IO15, IO17/18,
# USB D-/D+) face the lab-interface cluster and USB/power on the left, its bottom-row pins
# (IO9-IO11) face the modem header, and its right-hand pins (IO0, UART0) face BOOT/UART.
PLACEMENT: dict[str, tuple[float, float, float]] = {
    # ESP32-S3 module: antenna end flush with the top edge (keep-out spans x 44..92, y < 6.5)
    "U1": (68.0, 13.25, 0),
    "C7": (56.5, 8.2, 0),
    "C6": (56.5, 10.8, 0),
    "R3": (52.5, 8.2, 0),
    "C8": (52.5, 10.8, 0),
    "TP5": (48.5, 8.2, 0),
    "SW1": (40.0, 30.0, 0),
    # Synthetic pulse input (next to IO4)
    "R6": (56.5, 13.6, 0),
    "R5": (52.5, 13.6, 0),
    "C9": (52.5, 16.0, 0),
    "J2": (34.0, 9.0, 90),
    "TP4": (42.0, 9.0, 0),
    # Status LED (IO5)
    "R7": (56.5, 16.2, 0),
    "D2": (56.5, 18.6, 0),
    # I2C expansion (IO6/IO7)
    "R10": (48.5, 14.4, 90),
    "R11": (46.0, 14.4, 90),
    "J4": (34.0, 19.0, 90),
    # Tamper input (IO15)
    "R9": (56.5, 21.0, 0),
    "R8": (52.5, 21.0, 0),
    "C10": (52.5, 18.6, 0),
    "J3": (34.0, 14.0, 90),
    # USB-C input (left edge). The footprint's "PCB Edge" line sits 3.1 mm from its origin.
    "J1": (3.1, 30.0, 270),
    "R1": (11.0, 23.0, 90),
    "R2": (11.0, 37.0, 90),
    "U2": (17.0, 30.0, 0),
    "TP9": (5.0, 40.0, 0),
    "F1": (12.0, 44.0, 0),
    "D1": (19.0, 44.0, 0),
    "TP1": (26.0, 44.0, 0),
    # 3V3 buck (lower left), far from the pulse input
    "C1": (6.0, 54.0, 90),
    "C2": (9.5, 54.0, 90),
    "U3": (15.0, 55.0, 0),
    "C3": (15.0, 50.5, 0),
    "L1": (22.0, 55.0, 0),
    "C4": (28.0, 54.0, 90),
    "C5": (31.5, 54.0, 90),
    "TP2": (30.0, 60.0, 0),
    "TP3": (12.0, 62.0, 0),
    # Modem daughterboard interface (bottom edge, below IO9-IO11)
    "J6": (46.0, 66.0, 90),
    "J7": (70.0, 66.0, 90),
    "R12": (60.0, 31.0, 90),
    "R13": (64.0, 31.0, 90),
    "TP7": (76.0, 62.0, 0),
    "TP8": (82.0, 62.0, 0),
    # Right side: debug UART0 and BOOT (IO0)
    "J5": (92.0, 12.0, 0),
    "R4": (80.0, 29.0, 90),
    "SW2": (88.0, 40.0, 0),
    "TP6": (80.0, 36.0, 0),
}

# Dense cluster beside the module: reference designators go on the F.Fab (assembly) layer
# instead of silkscreen so they do not overlap; the assembly PDF still shows them.
FAB_ONLY_REFERENCES = {"C6", "C7", "R3", "C8", "R5", "R6", "C9", "R7", "D2", "R8", "R9", "C10", "R10", "R11"}

# Board-only footprints: (reference, footprint, x, y)
MOUNTING_HOLES = [
    ("H1", "MountingHole_3.2mm_M3", 4.0, 4.0),
    ("H2", "MountingHole_3.2mm_M3", 96.0, 4.0),
    ("H3", "MountingHole_3.2mm_M3", 4.0, 66.0),
    ("H4", "MountingHole_3.2mm_M3", 96.0, 66.0),
]

SILKSCREEN = [
    # (text, x, y, size_mm, layer)
    ("SMART GAS METER IoT  v0.2", 62.0, 46.0, 1.5, "F.SilkS"),
    ("LAB PROTOTYPE - NO GAS-LINE CONNECTION", 62.0, 49.0, 1.2, "F.SilkS"),
    ("PULSE", 29.0, 9.0, 0.9, "F.SilkS"),
    ("TAMPER", 28.5, 14.0, 0.9, "F.SilkS"),
    ("I2C", 29.5, 19.0, 0.9, "F.SilkS"),
    ("UART", 92.0, 19.2, 0.9, "F.SilkS"),
    ("MODEM IF", 55.0, 69.0, 0.9, "F.SilkS"),
    ("VMODEM", 71.3, 69.0, 0.9, "F.SilkS"),
    ("RESET", 40.0, 34.6, 0.9, "F.SilkS"),
    ("BOOT", 88.0, 44.6, 0.9, "F.SilkS"),
    ("USB-C", 9.5, 26.0, 0.9, "F.SilkS"),
    ("Smart Gas Meter IoT carrier v0.2 - bench use only", 50.0, 50.0, 1.2, "B.SilkS"),
]
