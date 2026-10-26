// Modem daughterboard v0.1 (4 layers, 75 x 50 mm): the KiCad layout extracted by tools/pcb_extract.py.
// The EC200U footprint is provisional, so its pad pattern is a placeholder.
import { readFileSync } from "node:fs";
import { boardModel } from "../board-kit.mjs";

const data = JSON.parse(readFileSync(new URL("../data/modem.json", import.meta.url), "utf8"));
export const STACK = [
  { id: "topmask", art: [["F.Mask", "art-pad"], ["F.Silk", "art-silk"]] },
  { id: "fcu", art: [["F.Cu", "art-cu"]] },
  { id: "in1", art: [["In1.Cu", "art-cu"]] },
  { id: "in2", art: [["In2.Cu", "art-cu"]] },
  { id: "bcu", art: [["B.Cu", "art-cu"]] },
  { id: "botmask", art: [["B.Mask", "art-pad"], ["B.Silk", "art-silk"]] },
];
export const model = boardModel({ data, stack: STACK, lift: -0.8, gap: 11, labels: { U1: "EC200U-EU" } });
export const LABEL = "An exploded, turnable model of the Smart Gas Meter EC200U modem daughterboard v0.1: its four copper layers, solder mask and silkscreen separated, with every part at its layout position and the carrier socket underneath.";
export const DATA = data;
