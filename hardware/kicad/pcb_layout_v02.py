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
PLACEMENT: dict[str, tuple[float, float, float]] = {
    # USB-C input (left edge). The footprint's "PCB Edge" line sits 3.1 mm from its origin.
    "J1": (3.1, 24.0, 270),
    "R1": (11.0, 17.0, 90),
    "R2": (11.0, 31.0, 90),
    "U2": (17.0, 24.0, 0),
    "F1": (12.0, 38.0, 0),
    "D1": (19.0, 38.0, 0),
    "TP9": (5.0, 36.0, 0),
    "TP1": (25.0, 38.0, 0),
    # 3V3 buck (lower left)
    "C1": (6.0, 50.0, 90),
    "C2": (9.5, 50.0, 90),
    "U3": (15.0, 51.0, 0),
    "C3": (15.0, 46.5, 0),
    "L1": (22.0, 51.0, 0),
    "C4": (28.0, 50.0, 90),
    "C5": (31.5, 50.0, 90),
    "TP2": (30.0, 56.0, 0),
    "TP3": (12.0, 60.0, 0),
    # ESP32-S3 module (top edge, centred) and its support parts
    "U1": (50.0, 13.25, 0),
    "C6": (35.0, 9.0, 90),
    "C7": (37.8, 9.0, 90),
    "R3": (34.0, 16.0, 90),
    "C8": (37.0, 16.0, 90),
    "TP5": (34.0, 21.5, 0),
    "R4": (64.0, 22.0, 90),
    "SW1": (30.0, 63.5, 0),
    "SW2": (42.0, 63.5, 0),
    "TP6": (49.0, 60.0, 0),
    # Synthetic pulse input (right edge, top)
    "J2": (94.0, 12.0, 0),
    "R5": (86.0, 10.0, 0),
    "R6": (82.0, 14.0, 0),
    "C9": (78.0, 14.0, 90),
    "TP4": (78.0, 8.0, 0),
    # Tamper input
    "J3": (94.0, 22.0, 0),
    "R8": (86.0, 21.0, 0),
    "R9": (82.0, 25.0, 0),
    "C10": (78.0, 25.0, 90),
    # I2C expansion and debug UART
    "J4": (94.0, 32.0, 0),
    "R10": (86.0, 32.0, 0),
    "R11": (86.0, 35.0, 0),
    "J5": (94.0, 46.0, 0),
    # Status LED
    "R7": (74.0, 56.0, 0),
    "D2": (79.0, 56.0, 0),
    # Modem daughterboard interface (bottom edge)
    "J6": (54.0, 66.0, 90),
    "J7": (76.0, 66.0, 90),
    "R12": (56.0, 60.0, 0),
    "R13": (60.0, 60.0, 0),
    "TP7": (82.0, 62.0, 0),
    "TP8": (88.0, 62.0, 0),
}

# Board-only footprints: (reference, footprint, x, y)
MOUNTING_HOLES = [
    ("H1", "MountingHole_3.2mm_M3", 4.0, 4.0),
    ("H2", "MountingHole_3.2mm_M3", 96.0, 4.0),
    ("H3", "MountingHole_3.2mm_M3", 4.0, 66.0),
    ("H4", "MountingHole_3.2mm_M3", 96.0, 66.0),
]

SILKSCREEN = [
    # (text, x, y, size_mm, layer)
    ("SMART GAS METER IoT  v0.2", 50.0, 34.0, 1.5, "F.SilkS"),
    ("LAB PROTOTYPE - NO GAS-LINE CONNECTION", 50.0, 37.0, 1.2, "F.SilkS"),
    ("PULSE", 90.0, 15.8, 0.9, "F.SilkS"),
    ("TAMPER", 90.0, 25.8, 0.9, "F.SilkS"),
    ("I2C", 90.0, 41.2, 0.9, "F.SilkS"),
    ("UART", 90.0, 52.5, 0.9, "F.SilkS"),
    ("MODEM IF", 63.0, 69.0, 0.9, "F.SilkS"),
    ("VMODEM", 77.3, 69.0, 0.9, "F.SilkS"),
    ("RESET", 30.0, 68.3, 0.9, "F.SilkS"),
    ("BOOT", 42.0, 68.3, 0.9, "F.SilkS"),
    ("USB-C", 9.5, 20.0, 0.9, "F.SilkS"),
    ("Smart Gas Meter IoT carrier v0.2 - bench use only", 50.0, 50.0, 1.2, "B.SilkS"),
]
