# Exploded board models · مدل‌های انفجاری بُردها

Three offline, bilingual (Persian + English) turnable 3D pages, built with the same kit as `../exploded/`:

| Page | What it shows | Source |
|---|---|---|
| `carrier.html` | Carrier board v0.2: its 6 layer slabs (top mask + silk, F.Cu, In1 GND plane, In2 3.3 V pour, B.Cu, bottom mask + silk) pull apart; every part sits at its pick-and-place position | `hardware/kicad/smart_gas_meter_iot.kicad_pcb` |
| `modem.html` | Modem daughterboard v0.1 (EC200U-EU), same treatment, socket J1 underneath. **EC200U footprint provisional** | `hardware/kicad-modem/sgm_modem.kicad_pcb` |
| `blocks.html` | Block diagram of both boards that separates by voltage domain (5 V input · 3.3 V logic · modem VBAT/1.8 V) | `models/blocks.mjs`, part names from both designs |

The layer artwork is the real routed copper, mask openings, silkscreen and drill holes, read directly from the
`.kicad_pcb` files by `tools/pcb_extract.py` (no KiCad needed). Part bodies come from each footprint's fabrication
outline; heights are typical package heights. Slabs are drawn thicker than real (0.3 mm each) so they can be seen.
Not-fitted (DNP) parts are left off. Every note (`parts-*.mjs`) is taken from the design files and datasheets.

```bash
python3 tools/pcb_extract.py ../../kicad/smart_gas_meter_iot.kicad_pcb data/carrier.json
python3 tools/pcb_extract.py ../../kicad-modem/sgm_modem.kicad_pcb data/modem.json
node page.mjs carrier && node page.mjs modem && node page.mjs blocks      # → <name>.html
node print.mjs                                                            # → ../media/sgm-boards-sheets-a4.pdf (16 A4 pages)
node capture.mjs carrier ../media/sgm-carrier-tour.video.mp4              # per-page tour; joined into ../media/sgm-boards-tour.mp4
```

**Audit status:** the pages build with the kit's strict painter-order proof. The slower turn audit (`node build.mjs modem --audit --quick`)
still reports order flips between a few small neighbouring parts at some angles when exploded (49 on the modem board),
which can show as a brief flicker of a resistor or capacitor while turning; the layers themselves are unaffected.
