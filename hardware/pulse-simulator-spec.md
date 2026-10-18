# Low-Voltage Pulse Simulator Specification

**Revision:** Draft 0.1  
**Purpose:** Reproducible bench testing with synthetic pulses only

## 1. Purpose and boundary

The simulator creates known electrical transitions for validating the counter input and firmware. It must remain a low-voltage test fixture and must not connect to a gas pipe, live utility meter, or safety-critical equipment.

## 2. Initial operating modes

1. **Manual:** push-button input for basic bring-up.
2. **Generated:** configurable pulse train from a microcontroller test output or laboratory function generator.
3. **Software:** deterministic synthetic telemetry for backend and billing tests.

Hardware and software simulation are separate test tools. Software-generated records do not prove the physical circuit is correct.

## 3. Parameters to define before schematic freeze

| Parameter | Initial decision |
|---|---|
| Logic voltage | Match selected MCU input; verify from its datasheet |
| Pulse shape | Clean digital high/low transition |
| Minimum high/low time | To be set after MCU and test-rate requirements are selected |
| Maximum pulse frequency | To be defined and measured in tests |
| Input conditioning | Pull resistor and optional Schmitt-trigger stage, values calculated from selected components |
| Test access | GND, input signal, supply, and MCU debug interface |
| Event identity | Device ID plus increasing sequence number |
| Counter behavior | Cumulative count; reset behavior explicitly reported |

Do not copy resistor values or pulse limits from an unrelated board design. Select them from the chosen component datasheets and the required test frequency.

## 4. Acceptance tests

- **T-01 Count accuracy:** generate 1,000 pulses at a documented rate; expected cumulative count is 1,000.
- **T-02 Repeatability:** repeat T-01 at least three times and record results.
- **T-03 Bounce/noise:** test the button input and confirm one intentional press yields one accepted event under the selected debounce strategy.
- **T-04 Rate limits:** test at low, nominal, and maximum declared test rates.
- **T-05 Reset:** reboot the MCU and verify whether the cumulative count is persisted or reset according to the documented design.
- **T-06 Offline backend:** disconnect network transport and verify queue/retry behavior if buffering is implemented.
- **T-07 Duplicate delivery:** replay one telemetry record and confirm the backend does not double-count it.
- **T-08 Counter regression:** submit a lower cumulative count and verify it is flagged as reset/rollover or invalid.
- **T-09 Invalid input:** test malformed payloads and out-of-range values at the API boundary.
- **T-10 Evidence:** save firmware version, test setup, pulse rate, expected count, observed count, and pass/fail result.

## 5. Test record template

| Field | Value |
|---|---|
| Test ID | |
| Date / operator | |
| Firmware revision | |
| Simulator mode | |
| Pulse rate / timing | |
| Expected count | |
| Observed count | |
| Result | PASS / FAIL |
| Notes / evidence | |

## 6. Completion criteria

The simulator is ready for schematic integration when pulse timing, logic level, input conditioning, test access, and maximum test rate are explicitly defined and reviewed. Hardware validation remains incomplete until bench results are recorded.
