# Schematic explorer · کاوشگر شماتیک

`index.html` is one offline page holding both real KiCad schematics (carrier v0.2 and modem v0.1), exported to SVG by
`kicad-cli`. Click a wire, a label or a pin to light up the whole net and list every pin on it; click a part for its
value, exact part number, footprint, design note and a Persian/English description. The seven nets that cross the
carrier J6 ↔ modem J1 connector link to the same net on the other board.

```bash
kicad-cli sch export netlist -o /tmp/carrier.net ../../kicad/smart_gas_meter_iot.kicad_sch
kicad-cli sch export netlist -o /tmp/modem.net ../../kicad-modem/sgm_modem.kicad_sch
python3 tools/sch_extract.py ../../kicad/smart_gas_meter_iot.kicad_sch /tmp/carrier.net data/carrier.json
python3 tools/sch_extract.py ../../kicad-modem/sgm_modem.kicad_sch /tmp/modem.net data/modem.json
node build.mjs                     # → index.html (needs kicad-cli for the SVG export)
```

Net meanings are in `nets.mjs`; part descriptions are shared with the board pages (`../boards/parts-*.mjs`).
