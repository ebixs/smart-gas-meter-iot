"""Board-level placement for the modem daughterboard v0.1 (single source for the PCB).

Coordinates are millimetres from the board's top-left corner (x right, y down); rotation
is in degrees counter-clockwise as KiCad shows it. ``side`` "B" flips the part to the
bottom layer. Every part in design_modem_v01.PARTS must appear here.

Placement logic (75 x 50 mm, 4 layers):
* EC200U turned 180 degrees so its UART/STATUS pads face the carrier header along the
  bottom edge, its VBAT pads face the reservoir capacitors on the left, its antenna pad
  faces the u.FL on the left edge and its (U)SIM pads face the SIM holder on the right.
* J1 (socket) sits on the bottom side so the board stacks over carrier header J6.
* PWRKEY / RESET_N drivers top-right next to those pads; LED lower right.
* The EC200U footprint is PROVISIONAL, so this placement is a layout study only.
"""

BOARD_W = 75.0
BOARD_H = 50.0
ORIGIN = (100.0, 50.0)
CORNER_R = 2.0
LAYERS = 4  # F.Cu signal + GND pour / In1 solid GND / In2 MODEM_VIN (VBAT) plane / B.Cu signal + GND pour

BOARD_RULES = {
    "min_clearance": 0.15,
    "min_track_width": 0.15,
    "min_via_diameter": 0.45,
    "min_via_annular_width": 0.1,
    "min_through_hole_diameter": 0.25,
    "min_hole_clearance": 0.2,
    "min_hole_to_hole": 0.4,
    "min_copper_edge_clearance": 0.3,
    "min_text_height": 0.8,
    "min_text_thickness": 0.08,
    "min_resolved_spokes": 2,
}

# ref: (x, y, rotation, side)
PLACEMENT: dict[str, tuple[float, float, float, str]] = {
    "U1": (38.0, 24.0, 180, "F"),
    # VBAT reservoir: left of the VBAT pads (x 22.5, y 32.4-36.4 after rotation)
    "C3": (19.6, 32.4, 0, "F"), "C4": (19.6, 33.7, 0, "F"), "C5": (19.6, 35.0, 0, "F"),
    "C6": (19.6, 36.3, 0, "F"), "C7": (19.6, 37.6, 0, "F"), "C8": (19.6, 38.9, 0, "F"),
    "C1": (14.0, 31.5, 90, "F"), "C2": (14.0, 37.8, 90, "F"),
    "D1": (7.5, 33.5, 90, "F"),
    "J2": (3.5, 40.0, 90, "F"),
    # Antenna (ANT pad at x 22.5, y 22.05)
    "R15": (17.6, 22.05, 0, "F"),
    "C14": (19.6, 24.0, 90, "F"),
    "C15": (12.6, 24.0, 90, "F"),
    "J4": (8.0, 22.05, 0, "F"),
    # Carrier header along the bottom edge (bottom side)
    "J1": (4.0, 46.5, 90, "B"),
    # Level shifters below the UART/STATUS pads (y 38.15)
    "Q5": (26.0, 44.0, 0, "F"), "R7": (29.2, 44.0, 90, "F"),
    "Q4": (33.0, 44.0, 0, "F"), "R6": (36.2, 44.0, 90, "F"),
    "Q3": (40.0, 44.0, 0, "F"), "R5": (43.2, 44.0, 90, "F"),
    # USB download / test pads
    "TP1": (47.0, 42.0, 0, "F"), "TP2": (49.5, 42.0, 0, "F"), "TP3": (52.0, 42.0, 0, "F"),
    "R16": (47.5, 46.5, 0, "F"), "JP1": (51.0, 46.5, 0, "F"),
    "TP4": (55.0, 46.5, 0, "F"), "TP5": (57.5, 46.5, 0, "F"), "TP6": (60.0, 46.5, 0, "F"),
    "TP7": (62.5, 46.5, 0, "F"), "TP8": (65.0, 46.5, 0, "F"),
    # VDD_EXT decoupling (pad x 53.5, y 28.55)
    "C9": (56.2, 28.6, 90, "F"),
    # Network LED (NET_STATUS pad x 53.5, y 29.85)
    "R8": (59.0, 31.5, 0, "F"), "R9": (59.0, 33.2, 0, "F"), "Q6": (62.5, 32.5, 0, "F"),
    "R10": (67.0, 30.5, 0, "F"), "D2": (67.0, 33.5, 180, "F"),
    # SIM holder (contacts face the module)
    "J3": (66.5, 14.0, 90, "F"),
    "R11": (56.6, 15.6, 0, "F"), "R12": (56.6, 16.9, 0, "F"), "R13": (56.6, 18.2, 0, "F"),
    "C10": (58.6, 23.6, 90, "F"), "C11": (59.9, 23.6, 90, "F"), "C12": (61.2, 23.6, 90, "F"),
    "R14": (56.6, 20.5, 0, "F"), "C13": (56.6, 22.0, 0, "F"),
    "U2": (65.0, 26.6, 0, "F"),
    # PWRKEY / RESET_N drivers (PWRKEY pad x 50.35, y 9.85; RESET_N pad x 53.5, y 11.65)
    "Q1": (47.0, 5.0, 0, "F"), "R1": (43.5, 4.3, 90, "F"), "R2": (43.5, 7.0, 90, "F"), "C16": (41.5, 5.6, 90, "F"),
    "Q2": (55.0, 5.0, 0, "F"), "R3": (51.5, 4.3, 90, "F"), "R4": (51.5, 7.0, 90, "F"),
}

FAB_ONLY_REFERENCES = {"C3", "C4", "C5", "C6", "C7", "C8", "R11", "R12", "R13", "R14", "C10", "C11", "C12", "C13",
                       "C14", "R15", "R5", "R6", "R7", "R1", "R2", "R3", "R4", "C16", "R8", "R9", "C9", "R16"}

MOUNTING_HOLES = [
    ("H1", "MountingHole_2.7mm_M2.5", 3.5, 3.5),
    ("H2", "MountingHole_2.7mm_M2.5", 71.5, 46.5),
]

SILKSCREEN = [
    ("SGM MODEM v0.1  EC200U", 22.0, 4.0, 1.2, "F.SilkS"),
    ("FOOTPRINT PROVISIONAL", 22.0, 6.2, 1.0, "F.SilkS"),
    ("ANT", 8.0, 26.0, 0.9, "F.SilkS"),
    ("SIM", 72.6, 22.6, 0.9, "F.SilkS"),
    ("NET", 67.0, 36.2, 0.9, "F.SilkS"),
    ("BOOT", 51.0, 48.6, 0.8, "F.SilkS"),
    ("J1 = carrier J6  (pin 1 MODEM_VIN)", 37.0, 49.0, 0.8, "B.SilkS"),
    ("Smart Gas Meter IoT modem v0.1 - bench use only", 37.0, 3.5, 1.0, "B.SilkS"),
]
