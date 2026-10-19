# Board v0.1 — Bring-up and Acceptance Test Plan

**Status:** Test plan only. No physical board has been built or tested.  
**Scope:** Low-voltage laboratory prototype; synthetic pulses only.

## Preconditions
- [ ] Schematic is captured in the selected CAD tool and reviewed against exact manufacturer datasheets.
- [ ] ERC has no unexplained errors; all warnings are reviewed.
- [ ] PCB DRC has no unexplained errors; footprints and pin numbers are checked against manufacturer drawings.
- [ ] BOM contains exact orderable manufacturer part numbers, ratings, tolerances, and footprints.
- [ ] Antenna keep-out and USB routing/layout constraints are checked.
- [ ] First power-up uses a current-limited 5 V bench supply or a known-good USB source, with no peripherals attached.

## First-power sequence
1. Inspect board under magnification for shorts, solder bridges, polarity, and orientation.
2. With power disconnected, measure resistance between VBUS_5V/GND and 3V3/GND; investigate unexpectedly low resistance.
3. Power from a current-limited 5 V source. Stop immediately for heating, odor, smoke, or unexpected current.
4. Measure VBUS_5V and 3V3 at test points; verify regulator output against the selected regulator tolerance.
5. Verify EN reset behavior and BOOT entry behavior.
6. Connect USB to a host and verify enumeration/programming without attaching any field wiring.
7. Run a firmware GPIO test with a known 3.3 V logic source or a dry-contact fixture.
8. Verify pulse count for slow synthetic test sequences, including idle, bounce/noise simulation, rapid transitions, and reboot/reset.
9. Record supply current, regulator temperature, USB behavior, and pulse-count results with firmware version and board revision.

## Acceptance criteria
- [ ] No short circuit, abnormal heating, smoke, or unstable supply behavior.
- [ ] 3V3 remains within the regulator and module datasheet limits at idle and during Wi-Fi/CPU activity.
- [ ] USB programming/serial behavior is repeatable on more than one connection cycle.
- [ ] BOOT and RESET controls work reliably.
- [ ] Synthetic pulse fixture produces the expected count without phantom counts in the agreed test sequence.
- [ ] Test results, failures, and corrective actions are recorded; no certification or billing-accuracy claim is inferred.

## Explicit exclusions
- Never connect the prototype to a live gas meter, gas line, valve, utility wiring, mains, or unknown field signal.
- Do not apply 5 V, 12 V, or 24 V to J2.
- This checklist does not replace electrical safety review, design verification, or regulatory testing.
