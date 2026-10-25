# SGM launch film — brief and storyboard

**What it is.** A 30-second, 1080p60 intro film for the Smart Gas Meter IoT project
(`ebixs/smart-gas-meter-iot`): an open bench prototype, not a commercial product.
**Viewer.** Engineers, data people and recruiters landing on the GitHub page or the project site.
**Single action.** Open the repository: `github.com/ebixs/smart-gas-meter-iot`.
**Label on screen.** "Bench prototype · synthetic fleet · illustrative prices".

## What is provably true (and shown)
- One revolution of the last red index drum is 0.01 m³ and closes the reed once (firmware model, anatomy figure).
- The ESP32-S3 firmware debounces the reed, saves the counter to flash in A/B slots with CRC-32, and freezes a
  `period_close` record at 00:00 Tehran on the first day of each Jalali season. The JSON shown is real output of
  `sgm_host demo` (firmware core).
- Records are stored and forwarded over the uplink; an unsent period-close record also goes out as one SMS after 24 h.
- 240 *simulated* meters in six cities; fleet daily totals, the forecast backtest of `sgm-0101`, the alert on
  `sgm-0239` and invoice `INV-140506-sgm-0058` come from `docs/analytics` / `analytics/output`.
- Forecast WAPE 9.5 %, 79 % of actuals inside the calibrated P10–P90 band (tuning fleet).
- The QR code encodes the real verification URL for that invoice.

## Never claimed
No real households, no certified metrology, no official tariff, no leak detection ("an alert asks for a look"),
no field deployment, no live gas connection.

## Brand
Site identity: paper `#f2f3ef`, ink `#15181b`, gas-pipe yellow `#f2b200` (Iranian gas pipes are painted yellow),
data blue `#2a78d6`, red decimal drums `#c9352f`. Bricolage Grotesque (display), IBM Plex Sans/Mono, Vazirmatn.
Every frame is code (HTML/SVG); no AI imagery, no footage.

## Storyboard (cuts on a 0.5 s grid so a 120 BPM track can be back-timed later)

| Time | The viewer sees | Business job | Out / carried object |
|---|---|---|---|
| 0.0–3.0 | Giant index drums rolling; "Every 0.01 m³ counts." | Hook: what is measured | Push into the last red drum |
| 3.0–6.0 | Red drum wheel with its magnet; the reed blades close; a yellow pulse leaves on a yellow pipe | Mechanism: one turn = one pulse | The yellow pulse and pipe carry across |
| 6.0–9.0 | Camera pans along the pipe into the SGM enclosure; the display counts each arriving pulse | Edge device: counts, survives power cuts | Push into the display |
| 9.0–12.5 | The display becomes a Jalali clock: 31 Shahrivar 23:59:58 → 1 Mehr 00:00; a `period_close` record prints | Signature: self-reading at the period boundary | The record card |
| 12.5–15.0 | The record leaves as a packet; signal drops; the SMS fallback types | Delivery: store-and-forward, SMS fallback | The packet |
| 15.0–18.5 | The packet lands in a field of 240 dots that fly into a 400-day fleet curve | Scale: one console for the fleet | The chart frame |
| 18.5–21.5 | One meter's forecast band and actuals; 9.5 % WAPE | Analytics: forecasting | Chart frame |
| 21.5–24.5 | A winter series flatlines; a scan flags it; "asks for a look, never proof of a leak" | Analytics: anomaly detection, honestly | The flagged meter |
| 24.5–27.5 | An invoice builds tier by tier; QR; "Issued by the meter operator ✓" | Billing: verifiable invoice | The pipe glyph |
| 27.5–30.0 | End card: Smart Gas Meter · کنتور هوشمند گاز · repo URL · honesty label | CTA | — |

## Audio
Delivered silent on purpose for now: this environment cannot reach a licensed music library, and generated or
synthesised scores were rejected in every case study this playbook records. The cut is on a 0.5 s grid, ready
for a back-timed 120 BPM library track (`scripts/backtime-music.py` in the playbook).

## Review ledger

| Round | Artifact | Independent critic's top findings | Changed | Measured |
|---|---|---|---|---|
| self-check | v1 | — | — | frozen time 11.9 s of 30 |
| — | v2 | — | slow camera push on every scene | frozen 0.0 s, 0 near-black frames |
| critic 1 | v2 | carried object breaks at 12.5/15.0; charts open empty; WAPE counted down (misleading); leak hedge small and late; empty halves; weak end card | record card becomes the packet; data on screen at each cut; fixed 9.5 %; hedge in the flag chip; layouts filled; composed end card with URL underline | ONE MORE PASS |
| critic 2 | v3 | 15.0 cut still unbridged; empty corners; small footer and coverage line | SMS card survives the cut and collapses into the dot burst; earlier SMS and verification chip; larger type | frozen 0.0 s |
| final | v4 | (not re-reviewed) | — | 1080p60, 8.6 MB |

Limits: silent; a music bed needs a licensed track. Review was sampled (contact sheets every 0.25 s, dense windows at each cut), not exhaustive. Rebuild: `node media/film/capture.mjs out.mp4`.
