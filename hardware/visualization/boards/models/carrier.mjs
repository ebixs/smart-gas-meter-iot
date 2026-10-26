// Carrier board v0.2 (4 layers, 100 x 70 mm): the real KiCad board, extracted by tools/pcb_extract.py.
import { readFileSync } from "node:fs";
import { boardModel } from "../board-kit.mjs";

const data = JSON.parse(readFileSync(new URL("../data/carrier.json", import.meta.url), "utf8"));
export const STACK = [
  { id: "topmask", art: [["F.Mask", "art-pad"], ["F.Silk", "art-silk"]] },
  { id: "fcu", art: [["F.Cu", "art-cu"]] },
  { id: "in1", art: [["In1.Cu", "art-cu"]] },
  { id: "in2", art: [["In2.Cu", "art-cu"]] },
  { id: "bcu", art: [["B.Cu", "art-cu"]] },
  { id: "botmask", art: [["B.Mask", "art-pad"], ["B.Silk", "art-silk"]] },
];
export const model = boardModel({ data, stack: STACK, lift: -0.8, gap: 14 });
export const LABEL = "An exploded, turnable model of the Smart Gas Meter carrier board v0.2: its four copper layers, solder mask and silkscreen separated, with every part at its real position.";
export const DATA = data;
