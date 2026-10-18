# Preliminary Hardware Bill of Materials (BOM)

**Revision:** Draft 0.1  
**Purpose:** Laboratory prototype planning  
**Note:** This is a candidate list, not a purchase-ready or production-approved BOM. Confirm exact variants, pinouts, electrical limits, availability, and local sourcing before ordering.

## 1. Design approach

Begin with a low-voltage bench prototype. Validate pulse counting and the telemetry contract over USB serial first. Add cellular communication only after firmware and backend behavior are stable. Do not connect this design to a live gas meter or gas line.

## 2. Candidate BOM

| Ref. | Block | Candidate / specification | Qty. | Rationale | Status |
|---|---|---|---:|---|---|
| U1 | MCU | ESP32-S3 development board, exact board TBD | 1 | USB debugging, GPIO, mature development ecosystem | Candidate |
| J1 | Test input | Momentary push-button or function-generator input | 1 | Repeatable synthetic pulses | Required |
| R1 | Input network | Series resistor and pull-up/down values selected for chosen logic voltage | 1 set | Defines input state and limits current | To calculate |
| U2 | Input conditioning | Schmitt-trigger buffer compatible with selected logic level | 1 | Helps reject slow/noisy edges if testing shows it is needed | Optional |
| U3 | RTC | DS3231-class RTC module if independent wall-clock time is required | 1 | Timekeeping during short network interruptions | Candidate |
| U4 | Non-volatile storage | MCU flash initially; external FRAM or other storage if endurance tests justify it | 1 | Persist counter and queue state | Decision pending |
| U5 | Cellular modem | LTE Cat-1 bis / LTE-M / NB-IoT module selected after carrier review | 1 | Remote telemetry in later milestone | Deferred |
| ANT1 | Antenna | Antenna matched to selected modem and supported bands | 1 | Required for cellular milestone | Deferred |
| P1 | Power | Regulated supply for dev board; modem rail sized to vendor peak-current guidance | 1 | Avoid brownouts during transmit bursts | To design |
| J2 | Debug | USB data cable / UART access | 1 | Flashing and serial logs | Required |
| PCB1 | PCB | Custom low-voltage prototype PCB, fabrication spec TBD | 1 | Integrates validated circuit | Later milestone |
| MECH1 | Enclosure | Non-certified project enclosure with strain relief | 1 | Protects lab prototype during handling | Later milestone |
| TP1 | Test points | GND, input, supply and status test points | 1 set | Bench debugging and verification | Recommended |

## 3. Design cautions

- **Modem choice:** verify regional band support, operator compatibility, SIM/data plan, antenna matching, peak current, and module availability before selection.
- **Power budget:** cellular modules can draw high transient current; do not power a modem from an undersized MCU regulator.
- **Logic levels:** verify UART/GPIO voltage compatibility from datasheets; do not assume levels match.
- **Synthetic input only:** this revision is a test fixture, not a field-meter interface. A future utility interface requires a separate safety and compliance review.
- **Low-voltage lab only:** live gas systems and mains wiring are outside this project's scope.
- **No production claims:** this BOM does not establish EMC, environmental, metrology, or hazardous-area compliance.

## 4. Selection checklist

- [ ] Confirm exact MCU board and pinout.
- [ ] Confirm development environment and USB/UART access.
- [ ] Define pulse amplitude, minimum high/low time, and maximum test frequency.
- [ ] Calculate input resistor and protection values from selected datasheets.
- [ ] Decide whether a Schmitt trigger is needed after measuring the waveform.
- [ ] Set persistence requirements before choosing external memory.
- [ ] Verify carrier and band support before selecting a modem.
- [ ] Calculate supply current with modem peak-current margin.
- [ ] Verify component footprints against manufacturer datasheets.
- [ ] Record manufacturer part numbers, supplier, price, and source date before ordering.

## 5. Next hardware deliverable

After the MCU board and test-pulse limits are fixed, produce:
1. A reviewed input-conditioning schematic.
2. A pin-assignment table.
3. A BOM with manufacturer part numbers.
4. A test procedure for 1,000 pulses, bounce rejection, reset behavior, and network-offline simulation.

Component values and modem model remain intentionally unspecified until those checks are complete.
