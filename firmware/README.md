# Firmware — ESP32-S3 bench prototype

> **Bench use only.** J2 takes a synthetic 3.3 V pulse (signal generator) or a dry
> contact to GND. Never connect a live gas meter, gas line, valve, mains or field
> wiring. Readings are not certified metrology, and an analytics alert is not proof
> of a gas leak.

The firmware counts meter pulses, keeps the counter safe across power cuts,
freezes its own reading at every Jalali billing-period boundary (the
*self-reading*, «خودخوان»), and forwards records to the backend over Wi-Fi
(bench) or a cellular modem, with an SMS fallback for the billing reading.

```
GPIO4 edge ─▶ ISR ─▶ edge queue ─▶ pulse task ── debounce ──▶ meter core ──▶ NVS (A/B + CRC)
                                                                │
                           report task ◀── record queue ◀───────┘
                           │  interval snapshot (1 h), tamper events
                           ▼
                uplink: Wi-Fi + HTTP  │  modem (Quectel AT) + HTTP, SMS fallback
                           ▼
                POST /api/v1/readings/batch  (telemetry contract v2)
```

## Layout

| Path | What it is |
|---|---|
| `components/sgm_core/` | Portable C11 core, no ESP-IDF headers. Builds for the ESP32-S3 and the host. |
| `main/` | ESP-IDF application: GPIO/ISR, NVS, tasks, Wi-Fi and cellular uplinks, `Kconfig`. |
| `main/board.h` | GPIO map of the v0.2 board; a test checks it against `hardware/kicad/design_v02.py`. |
| `test/host/` | Host unit tests (ASan + UBSan) and `sgm_host`, a CLI used by Python cross-checks. |

### Core modules

| Module | Responsibility |
|---|---|
| `debounce` | Edge-driven reed-contact qualifier: min closure 30 ms, bounce merged, closure already active at boot never counted, pulses faster than the G4 Qmax flagged. |
| `meter` | Counter, persistence policy, wall clock, period tracking and record creation. Sequence numbers are saved before a record is queued, so a reset never reuses one. |
| `period` + `jalali` | Jalali calendar (integer port of jalaali-js) and period boundaries at 00:00 Iran time (UTC+03:30, no DST since 1402). Monthly or seasonal (Farvardin, Tir, Mehr, Dey). |
| `store` | 40-byte counter image in two slots with CRC-32 and a generation number; a torn write can only damage the older copy. |
| `queue` | Bounded store-and-forward queue. When full it drops the oldest *interval* record and keeps period-close records. Acknowledge by sequence. |
| `telemetry` | Heap-free JSON encoder for contract v2 (`schemas/telemetry-v2.schema.json`). |
| `at`, `sms` | AT response parser (CEREG, CSQ, CCLK with quarter-hour zones, QHTTPPOST, CMGS) and the period-close SMS text. |
| `backoff` | Exponential retry with equal jitter, so a fleet does not retry in lockstep after an outage. |

## Self-reading at the period boundary

Every path that creates a record, and every pulse, first asks the period tracker
whether a boundary has passed. If it has, the counter value *before* the new
pulse is frozen into a `period_close` record stamped with the boundary instant:

```json
{"schema_version":2,"device_id":"sgm-bench-01","sequence":4,
 "timestamp":"2026-09-22T20:30:00.000Z","pulse_count_total":44,
 "record_type":"period_close","period":{"calendar":"jalali","start":"1405/04","months":3}, ...}
```

`2026-09-22T20:30Z` is 00:00 on 1 Mehr 1405 in Tehran. If the device was off or
had no clock at the boundary, the close is stamped when it is observed and carries
`late_close`. A test compares the C boundaries with the Python billing calendar
for 40 consecutive periods, and the C Jalali dates with the Python ones for every
day from 1990 to 2060.

If a period-close record is still unsent after 24 h on the cellular build and an
SMS gateway number is configured, the device also sends it as one SMS:

```
SGM1 sgm-bench-01 P=1405/04x3 C=123456 S=812 T=20260922T2030Z
```

The SMS duplicates the record and never replaces it: the record stays queued until
the backend acknowledges it.

## Flash wear budget

Each counter save writes a 40-byte NVS blob (~4 of the 126 entries in a 4 KiB
page). The custom partition table gives NVS 24 KiB (6 pages). Using the simulated
fleet's annual consumption at 0.01 m³/pulse and 100,000 erase cycles per sector:

| Household (simulated fleet) | m³/year | Save every pulse | Save every 4 pulses |
|---|---:|---:|---:|
| Median | 2,250 | ~84 years | ~330 years |
| 90th percentile | 4,500 | ~42 years | ~170 years |
| 99th percentile | 8,000 | ~24 years | ~94 years |

Default is every pulse (`SGM_COMMIT_EVERY_PULSES=1`): a power cut loses nothing
that was already counted. Raising it trades up to N−1 pulses (N−1 × 0.01 m³) on a
power cut for flash life.

## Build

Host tests (any machine with CMake and gcc/clang):

```bash
cmake -S firmware/test/host -B build/host && cmake --build build/host -j
ctest --test-dir build/host --output-on-failure
build/host/sgm_host demo | python3 simulator/validate_telemetry.py -
```

ESP32-S3 (ESP-IDF v5.3):

```bash
cd firmware
idf.py set-target esp32s3
idf.py menuconfig        # Smart Gas Meter: Wi-Fi, API URL, token, period, uplink
idf.py build flash monitor
# cellular variant
idf.py -B build-cell -DSDKCONFIG=build-cell/sdkconfig \
       -DSDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.cell" build
```

CI (`.github/workflows/firmware.yml`) runs the host tests under sanitizers and
builds both variants with ESP-IDF v5.3.2. Current image sizes: Wi-Fi 535 KiB,
cellular 275 KiB, against a 3 MiB OTA slot.

## Bench test with the lab backend

```bash
SGM_API_TOKEN=dev-token uvicorn backend.app:app --host 0.0.0.0
# menuconfig: API URL http://<pc-ip>:8000/api/v1/readings/batch, token dev-token
```

Feed J2 from a signal generator (3.3 V, idle high, ≥30 ms low) or a push button to
GND. The status LED blinks once per qualified pulse.

## Status and open items

- Built and unit-tested; **not yet flashed on assembled hardware** (the v0.2 board
  has not been fabricated).
- The cellular driver follows the Quectel AT manuals for BG95/EC200U but has not run
  against a modem. HTTPS on the modem needs a CA loaded with `AT+QSSLCFG`.
- Low-power operation (light sleep with GPIO wake, modem PSM/eDRX) depends on the
  power decision in [`docs/hardware-decisions.md`](../docs/hardware-decisions.md).
- No OTA update flow yet, though the partition table reserves two OTA slots.
