# BOM — carrier board v0.2-draft2 (generated from `design_v02.py`)

**Candidate BOM — not approved for purchase.** `TBD` / `candidate` entries must be selected and checked against datasheets before freeze.

| Ref | Value | Footprint (SGM lib) | MPN / status | DNP | Note |
|---|---|---|---|---|---|
| J1 | USB-C receptacle (USB 2.0, sink) | `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` | GCT USB4105-GF-A (candidate) |  | Footprint/pin map must be checked against the selected connector drawing |
| R1 | 5.1k 1% | `R_0603_1608Metric` | TBD |  | USB-C sink Rd on CC1 |
| R2 | 5.1k 1% | `R_0603_1608Metric` | TBD |  | USB-C sink Rd on CC2 |
| F1 | PTC 0.75A hold, >=6V | `Fuse_1206_3216Metric` | TBD |  | Resettable input protection; size after load budget |
| D1 | TVS 5V standoff (candidate SMAJ5.0CA) | `D_SMA` | SMAJ5.0CA (candidate) |  | VBUS surge clamp after the fuse |
| U2 | USBLC6-2SC6 | `SOT-23-6` | STMicroelectronics USBLC6-2SC6 |  | Low-capacitance USB ESD array; place at the connector |
| U3 | AP63203WU-7 (3.3V buck) | `TSOT-23-6` | Diodes Inc. AP63203WU-7 |  | Fixed 3.3V: FB senses the output; EN tied to VIN (datasheet: auto start-up) |
| C1 | 10uF 25V X7R | `C_1206_3216Metric` | TBD |  | Buck input capacitor (datasheet CIN) |
| C2 | 100nF 50V | `C_0603_1608Metric` | TBD |  | High-frequency input bypass, close to VIN |
| C3 | 100nF 25V | `C_0603_1608Metric` | TBD |  | Bootstrap capacitor between BST and SW (datasheet CBST) |
| L1 | 3.9uH, Isat>=3A (candidate) | `L_Taiyo-Yuden_NR-40xx` | TBD |  | Datasheet table value for 3.3V output |
| C4 | 22uF 10V X7R | `C_0805_2012Metric` | TBD |  | Buck output capacitor 1/2 (datasheet 2x22uF) |
| C5 | 22uF 10V X7R | `C_0805_2012Metric` | TBD |  | Buck output capacitor 2/2 |
| U1 | ESP32-S3-WROOM-1-N8 | `ESP32-S3-WROOM-1` | Espressif ESP32-S3-WROOM-1-N8 |  | Pin numbers per KiCad RF_Module symbol = Espressif datasheet pin table |
| C6 | 10uF 10V X7R | `C_0805_2012Metric` | TBD |  | Module bulk decoupling at the 3V3 pin |
| C7 | 100nF 16V | `C_0603_1608Metric` | TBD |  | Module HF decoupling at the 3V3 pin |
| R3 | 10k | `R_0603_1608Metric` | TBD |  | EN pull-up (Espressif RC delay R=10k) |
| C8 | 1uF 16V | `C_0603_1608Metric` | TBD |  | EN delay capacitor (Espressif RC delay C=1uF) |
| SW1 | RESET | `SW_SPST_TL3342` | TBD |  | Pulls EN low to reset |
| R4 | 10k | `R_0603_1608Metric` | TBD |  | GPIO0 strapping pull-up (run from flash by default) |
| SW2 | BOOT | `SW_SPST_TL3342` | TBD |  | Hold during reset for USB download mode |
| J2 | PULSE_IN (synthetic 3.3V lab signal only) | `PinHeader_1x02_P2.54mm_Vertical` | TBD |  | Max 3.3V logic or dry contact to GND. Never connect a live meter or field wiring |
| R5 | 10k | `R_0603_1608Metric` | TBD |  | Defined idle-high state / dry-contact pull-up |
| R6 | 1k | `R_0603_1608Metric` | TBD |  | Series current limit; place near the MCU pin |
| C9 | 100nF (DNP) | `C_0603_1608Metric` | TBD | yes | Optional RC filter footprint, not fitted by default |
| R7 | 1k | `R_0603_1608Metric` | TBD |  | ~1.3mA with a 2V LED; adjust after LED selection |
| D2 | Green LED | `LED_0603_1608Metric` | TBD |  | Active-high status LED (pin 2 = anode) |
| J3 | TAMPER switch | `PinHeader_1x02_P2.54mm_Vertical` | TBD |  | Enclosure switch closed to GND when lid is closed; open = tamper (advisory only) |
| R8 | 10k | `R_0603_1608Metric` | TBD |  | Pull-up: wire break or lid open reads high |
| R9 | 1k | `R_0603_1608Metric` | TBD |  | Series resistor |
| C10 | 100nF | `C_0603_1608Metric` | TBD |  | Debounce (~1ms with R9) |
| J4 | I2C expansion (3.3V) | `PinHeader_1x04_P2.54mm_Vertical` | TBD |  | Optional 3.3V I2C sensors |
| R10 | 4.7k | `R_0603_1608Metric` | TBD |  | I2C pull-up |
| R11 | 4.7k | `R_0603_1608Metric` | TBD |  | I2C pull-up |
| J5 | Debug UART0 (3.3V) | `PinHeader_1x03_P2.54mm_Vertical` | TBD |  | Pin 1 = module TXD0 output; no power pin to avoid back-feeding |
| J6 | Modem daughterboard interface | `PinHeader_1x08_P2.54mm_Vertical` | TBD |  | 3.3V logic interface; daughterboard provides level translation and modem power design |
| J7 | MODEM_VIN bench supply input | `PinHeader_1x02_P2.54mm_Vertical` | TBD |  | Separate current-limited supply sized to the selected modem; never from +3V3 |
| R12 | 100k | `R_0603_1608Metric` | TBD |  | Modem held disabled while MCU boots |
| R13 | 100k | `R_0603_1608Metric` | TBD |  | Reset de-asserted by default (polarity per modem) |
| TP1 | TP_5V | `TestPoint_Pad_D1.5mm` | TBD |  |  |
| TP2 | TP_3V3 | `TestPoint_Pad_D1.5mm` | TBD |  |  |
| TP3 | TP_GND | `TestPoint_Pad_D1.5mm` | TBD |  |  |
| TP4 | TP_PULSE | `TestPoint_Pad_D1.5mm` | TBD |  |  |
| TP5 | TP_EN | `TestPoint_Pad_D1.5mm` | TBD |  |  |
| TP6 | TP_BOOT | `TestPoint_Pad_D1.5mm` | TBD |  |  |
| TP7 | TP_VMODEM | `TestPoint_Pad_D1.5mm` | TBD |  |  |
| TP8 | TP_GND2 | `TestPoint_Pad_D1.5mm` | TBD |  |  |
| TP9 | TP_VBUS | `TestPoint_Pad_D1.5mm` | TBD |  |  |
