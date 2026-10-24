#!/usr/bin/env bash
# Export review artefacts for the v0.2 PCB with KiCad 9's CLI.
#   DRC report (with schematic parity), Gerbers, Excellon drill, pick-and-place,
#   board-layer PDF, and CAD-derived 3D renders (top, bottom, isometric).
# These are REVIEW artefacts: the board is not released for fabrication.
# Usage: hardware/kicad/tools/export_pcb.sh [output-dir]
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
pcb="$here/smart_gas_meter_iot.kicad_pcb"
out="${1:-$here/exports/pcb}"
mkdir -p "$out/gerbers" "$out/render"

kicad-cli pcb drc --schematic-parity --severity-all --exit-code-violations \
  --output "$out/drc-kicad-9.rpt" "$pcb"
kicad-cli pcb export gerbers --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts \
  --output "$out/gerbers/" "$pcb" >/dev/null
kicad-cli pcb export drill --format excellon --generate-map --map-format pdf \
  --output "$out/gerbers/" "$pcb" >/dev/null
kicad-cli pcb export pos --side front --format csv --units mm --exclude-dnp \
  --output "$out/smart_gas_meter_iot-cpl.csv" "$pcb" >/dev/null
kicad-cli pcb export pdf --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Silkscreen,Edge.Cuts --mode-separate \
  --output "$out/layers/" "$pcb" >/dev/null 2>&1 || \
  kicad-cli pcb export pdf --layers F.Cu,F.Silkscreen,Edge.Cuts --output "$out/layers-top.pdf" "$pcb" >/dev/null
for view in top bottom; do
  kicad-cli pcb render --side "$view" --quality high --width 2000 --height 1400 --background opaque \
    --output "$out/render/board-$view.png" "$pcb" >/dev/null
done
kicad-cli pcb render --side top --rotate "-35,0,25" --perspective --quality high --floor \
  --width 2000 --height 1400 --zoom 0.9 --output "$out/render/board-iso.png" "$pcb" >/dev/null
echo "Exported review artefacts to $out"
