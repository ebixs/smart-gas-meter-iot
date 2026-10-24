# Part selection and datasheet checks — v0.2-rc1

**Status:** exact parts selected for the schematic freeze candidate (2026-10-24). This is still a bench-only, low-voltage prototype and is **not fabrication-ready** until the PCB passes DRC and the freeze review below is signed off.

All selections are recorded in `design_v02.py` (`PART_SELECTION`). From there they flow into the schematic fields (`MPN`, `Manufacturer`, `LCSC`), the [review BOM](exports/BOM-v0.2-rc1.md) and the [JLCPCB assembly BOM](exports/BOM-v0.2-rc1-jlcpcb.csv). Ratings come from the manufacturer datasheets and LCSC/JLCPCB parametric data as of 2026-10-24. Stock levels change daily.

## Load and power budget (5 V USB input)

| Consumer | Worst case |
|---|---|
| ESP32-S3-WROOM-1-N8, Wi-Fi TX peak (module data: 355 mA @ 3.3 V) | 355 mA |
| Status LED (~1.3 mA), pull-ups, EN RC | < 5 mA |
| I2C expansion allowance | 50 mA |
| **3V3 rail total** | **≈ 410 mA** (AP63203 rated 2 A) |
| Reflected to 5 V at ~85 % buck efficiency | ≈ 320 mA |

The modem is **not** on this path. It is powered from its own `MODEM_VIN` bench supply through J7.

## Selections

| Ref | Part | Key ratings checked | Why |
|---|---|---|---|
| J1 | GCT **USB4105-GF-A** | 5 A VBUS, 48 V, USB 2.0 16-pin; datasheet pin table A1/A12/B1/B12 GND, A4/A9/B4/B9 VBUS, A5 CC1, B5 CC2, A6/B6 D+, A7/B7 D−, A8/B8 SBU, shell GND | Matches the KiCad `USB4105-xx-A` footprint and the symbol pin numbers exactly. **JLCPCB stock was 0** at selection time; order it from DigiKey/Mouser or hand-fit it. |
| F1 | Littelfuse **1206L075/13.2WR** | Ihold 0.75 A, Itrip 1.5 A, Vmax 13.2 V, R1max 0.35 Ω | ~2.3× margin over the 320 mA input. ⚠ The similarly named *1206L075THYR* is rated for a lower maximum voltage. Do not substitute it. |
| D1 | **SMAJ6.5CA** (bidirectional, SMA) | Vrwm 6.5 V, Vbr 7.98 V, Vc 11.2 V, 400 W | 6.5 V stand-off keeps leakage negligible at 5–5.5 V (a 5.0 V-rated TVS sits at its stand-off on a USB rail). The 11.2 V clamp stays far below the AP63203's 32 V input limit. |
| U2 | ST **USBLC6-2SC6** | Vrwm 5.25 V, 3.5 pF, IEC 61000-4-2 | Standard USB 2.0 ESD array. SOT-23-6 pinout: 1/6 I/O1, 3/4 I/O2, 2 GND, 5 VBUS, matching the symbol. |
| U3 | Diodes **AP63203WU-7** | 3.8–32 V in, 3.3 V fixed, 2 A, 1.1 MHz | TSOT-26 pinout 1 FB, 2 EN, 3 VIN, 4 GND, 5 SW, 6 BST. Fixed-output FB connects to the output rail, and EN may be tied to VIN (datasheet). |
| L1 | Sunlord **SWPA4030S3R9MT** | 3.9 µH (datasheet table value for 3.3 V out), Isat 3 A, Irms 2.1 A, DCR 74 mΩ | Saturation margin is well above the 2 A regulator rating. KiCad has a dedicated `L_Sunlord_SWPA4030S` footprint. |
| C1 | Murata **GRM31CR71E106KA12L** | 10 µF 25 V X7R 1206 | Datasheet CIN, with voltage margin at 5 V. |
| C4, C5 | Murata **GRM21BR61C226ME44L** | 22 µF 16 V X5R 0805 | Datasheet 2 × 22 µF COUT. The 16 V rating keeps more capacitance under DC bias than the 10 V part. |
| C2, C3, C7, C10 (C9 DNP) | YAGEO **CC0603KRX7R9BB104** | 100 nF 50 V X7R | HF input bypass, bootstrap (CBST), module decoupling, tamper debounce. |
| C6 | Samsung **CL21A106KAYNNNE** | 10 µF 25 V X5R 0805 | Module bulk decoupling (Espressif: 10 µF + 0.1 µF). |
| C8 | Samsung **CL10A105KB8NNNC** | 1 µF 50 V | EN RC delay (Espressif: 10 kΩ / 1 µF). |
| U1 | Espressif **ESP32-S3-WROOM-1-N8** | 3.0–3.6 V, 8 MB flash, no PSRAM, PCB antenna | Symbol pin numbers match the Espressif pin table. GPIO35–37 stay unused anyway. |
| R* | UNI-ROYAL 0603WAF series, 1 % | 5.1 k / 10 k / 1 k / 4.7 k / 100 k | JLCPCB basic parts. |
| SW1, SW2 | E-Switch **TL3342F160QG** | 50 mA 12 V, 5.2 × 5.2 mm | Matches the KiCad `SW_SPST_TL3342` footprint. |
| D2 | Everlight **19-213SURC/S530-A3/5T** (red) | Vf 2.0–2.4 V | ⚠ The first candidate, a green 0603 LED, had Vf ≈ 3.3 V and would barely light from a 3.3 V GPIO. Red gives ≈ 1.3 mA through 1 kΩ. |
| J2–J7, TP1–TP9 | Generic 2.54 mm headers / bare test pads | — | Hand-fitted; test points are copper pads only. |

## Footprint ↔ symbol check

An automated check confirmed that every symbol pin number of all 48 parts exists as a pad on its assigned footprint. The package pinouts above were compared with the manufacturer pin tables. **Still to do at PCB stage:** overlay each footprint on the manufacturer's recommended land pattern (USB4105 drawing, AP63203 TSOT-26, SWPA4030, ESP32-S3-WROOM-1 antenna keep-out) and inspect the 3D fit.

## Freeze review — remaining human sign-off

- [ ] Independent review of this file and the schematic PDF by a second engineer.
- [ ] Confirm USB4105-GF-A sourcing (or approve an equivalent with an identical land pattern).
- [ ] Modem SKU still open. J6 remains an interface placeholder; its EN/RESET polarity and I/O level must be confirmed against the chosen modem.
