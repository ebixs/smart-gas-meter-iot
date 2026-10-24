# BOM — carrier board v0.2-rc1 (generated from `design_v02.py`)

Exact parts selected for schematic freeze; see [PART_SELECTION.md](../PART_SELECTION.md) for ratings and reasoning. Prices and stock change daily — re-check before ordering. **Not approved for purchase until the PCB and freeze review are signed off.**

`hand-fit` = generic 2.54 mm headers fitted by hand; test points are bare pads and are not purchased.

| Qty | Refs | Value | Manufacturer | MPN | LCSC | Footprint (SGM) | Fit |
|---:|---|---|---|---|---|---|---|
| 1 | J1 | USB4105-GF-A (USB-C) | GCT | USB4105-GF-A | C3020560 | `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` | SMT |
| 2 | R1, R2 | 5.1k 1% | UNI-ROYAL | 0603WAF5101T5E | C23186 | `R_0603_1608Metric` | SMT |
| 1 | F1 | PTC 0.75A/13.2V | Littelfuse | 1206L075/13.2WR | C207036 | `Fuse_1206_3216Metric` | SMT |
| 1 | D1 | SMAJ6.5CA | ZHIDE | SMAJ6.5CA | C5161320 | `D_SMA` | SMT |
| 1 | U2 | USBLC6-2SC6 | STMicroelectronics | USBLC6-2SC6 | C7519 | `SOT-23-6` | SMT |
| 1 | U3 | AP63203WU-7 | Diodes Inc. | AP63203WU-7 | C780769 | `TSOT-23-6` | SMT |
| 1 | C1 | 10uF 25V X7R | Murata | GRM31CR71E106KA12L | C77093 | `C_1206_3216Metric` | SMT |
| 4 | C2, C3, C7, C10 | 100nF 50V | YAGEO | CC0603KRX7R9BB104 | C14663 | `C_0603_1608Metric` | SMT |
| 1 | L1 | 3.9uH Isat 3A | Sunlord | SWPA4030S3R9MT | C96899 | `L_Sunlord_SWPA4030S` | SMT |
| 2 | C4, C5 | 22uF 16V | Murata | GRM21BR61C226ME44L | C86817 | `C_0805_2012Metric` | SMT |
| 1 | U1 | ESP32-S3-WROOM-1-N8 | Espressif | ESP32-S3-WROOM-1-N8 | C2913198 | `ESP32-S3-WROOM-1` | SMT |
| 1 | C6 | 10uF 25V | Samsung | CL21A106KAYNNNE | C15850 | `C_0805_2012Metric` | SMT |
| 4 | R3, R4, R5, R8 | 10k 1% | UNI-ROYAL | 0603WAF1002T5E | C25804 | `R_0603_1608Metric` | SMT |
| 1 | C8 | 1uF 50V | Samsung | CL10A105KB8NNNC | C15849 | `C_0603_1608Metric` | SMT |
| 2 | SW1, SW2 | TL3342 | E-Switch | TL3342F160QG | C2886898 | `SW_SPST_TL3342` | SMT |
| 1 | J2 | PULSE_IN (synthetic 3.3V lab signal only) | - | generic | - | `PinHeader_1x02_P2.54mm_Vertical` | hand-fit |
| 3 | R6, R7, R9 | 1k 1% | UNI-ROYAL | 0603WAF1001T5E | C21190 | `R_0603_1608Metric` | SMT |
| 1 | C9 | 100nF 50V (DNP) | YAGEO | CC0603KRX7R9BB104 | C14663 | `C_0603_1608Metric` | DNP |
| 1 | D2 | Red LED | Everlight | 19-213SURC/S530-A3/5T | C2986056 | `LED_0603_1608Metric` | SMT |
| 1 | J3 | TAMPER switch | - | generic | - | `PinHeader_1x02_P2.54mm_Vertical` | hand-fit |
| 1 | J4 | I2C expansion (3.3V) | - | generic | - | `PinHeader_1x04_P2.54mm_Vertical` | hand-fit |
| 2 | R10, R11 | 4.7k 1% | UNI-ROYAL | 0603WAF4701T5E | C23162 | `R_0603_1608Metric` | SMT |
| 1 | J5 | Debug UART0 (3.3V) | - | generic | - | `PinHeader_1x03_P2.54mm_Vertical` | hand-fit |
| 1 | J6 | Modem daughterboard interface | - | generic | - | `PinHeader_1x08_P2.54mm_Vertical` | hand-fit |
| 1 | J7 | MODEM_VIN bench supply input | - | generic | - | `PinHeader_1x02_P2.54mm_Vertical` | hand-fit |
| 2 | R12, R13 | 100k 1% | UNI-ROYAL | 0603WAF1003T5E | C25803 | `R_0603_1608Metric` | SMT |
| 1 | TP1 | TP_5V | - | generic | - | `TestPoint_Pad_D1.5mm` | hand-fit |
| 1 | TP2 | TP_3V3 | - | generic | - | `TestPoint_Pad_D1.5mm` | hand-fit |
| 1 | TP3 | TP_GND | - | generic | - | `TestPoint_Pad_D1.5mm` | hand-fit |
| 1 | TP4 | TP_PULSE | - | generic | - | `TestPoint_Pad_D1.5mm` | hand-fit |
| 1 | TP5 | TP_EN | - | generic | - | `TestPoint_Pad_D1.5mm` | hand-fit |
| 1 | TP6 | TP_BOOT | - | generic | - | `TestPoint_Pad_D1.5mm` | hand-fit |
| 1 | TP7 | TP_VMODEM | - | generic | - | `TestPoint_Pad_D1.5mm` | hand-fit |
| 1 | TP8 | TP_GND2 | - | generic | - | `TestPoint_Pad_D1.5mm` | hand-fit |
| 1 | TP9 | TP_VBUS | - | generic | - | `TestPoint_Pad_D1.5mm` | hand-fit |
