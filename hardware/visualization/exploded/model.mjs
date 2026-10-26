// Exploded 3D model of the SGM bench prototype on a generic G4 diaphragm gas meter.
// Every part is a convex solid built at its assembled position (world units ≈ 0.6 mm),
// grouped into slide groups that ride one turntable group, so the figure can turn and come apart.
// The G4 internals are a generic illustration of how diaphragm meters work, not one manufacturer's design.
import * as k from "./kit/iso-kit.mjs";
import * as G from "./kit/lathe.mjs";
import * as A from "./kit/audit.mjs";
import { turning } from "./kit/turn-build.mjs";

export const WIDTH = 760;
export const HEIGHT = 860;
export const AZIMUTH = 38;
export const ELEVATION = 28;
export const REACH = 136;
export const TOP = 345;

const ring = (r, z, n = 48) => Array.from({ length: n }, (_, i) => [r * Math.cos((i / n) * 2 * Math.PI), r * Math.sin((i / n) * 2 * Math.PI), z]);
export const P = k.fitProjection([...ring(REACH, -12), ...ring(REACH, TOP)], WIDTH, HEIGHT, { pad: 18, azimuth: AZIMUTH, elevation: ELEVATION });
export const R = A.recorder(P);
export const T = turning(P, { recorder: R });

const VERT = (x, y) => G.frameOf([x, y, 0], [0, 0, 1], [1, 0, 0], [0, 1, 0]);
const ALONG_X = (y, z) => G.frameOf([0, y, z], [1, 0, 0], [0, 1, 0], [0, 0, 1]);
const ALONG_Y = (x, z) => G.frameOf([x, 0, z], [0, 1, 0], [0, 0, 1], [1, 0, 0]);
const UP = { o: [0, 0, 0], a: [0, 0, 1], u: [1, 0, 0], v: [0, 1, 0] };

// ---------- groups ----------
export const spin = T.group("spin", { turn: { pivot: [0, 0] } });
const slide = (name, parent, direction, travel) => T.group(name, { parent, slide: { direction, travel } });
const g = {
  upper: slide("upper", spin, [0, 0, 1], 200),
  pulser: slide("pulser", spin, [0, 0, -1], 40),
  counter: slide("counter", spin, [0, 1, 0], 62),
  core: slide("core", spin, [0, 0, 1], 70),
  lid: slide("lid", spin, [0, 0, 1], 150),
  modem: slide("modem", spin, [0, 0, 1], 72),
  board: slide("board", spin, [0, 0, 1], 40),
  battLift: slide("battLift", spin, [0, 0, 1], 64),
};
g.coverF = slide("coverF", g.core, [0, 1, 0], 36);
g.coverB = slide("coverB", g.core, [0, -1, 0], 36);
g.diaF = slide("diaF", g.core, [0, 1, 0], 16);
g.diaB = slide("diaB", g.core, [0, -1, 0], 16);
g.mech = slide("mech", g.core, [0, 0, 1], 40);

// Staged explode: one value x in [0, 1] drives every group, so the order of separation is physical
// (covers lift before the parts inside them move sideways).
export const STAGES = {
  upper: [0.0, 0.34],
  lid: [0.0, 0.34],
  pulser: [0.02, 0.3],
  counter: [0.2, 0.55],
  core: [0.16, 0.5],
  modem: [0.22, 0.56],
  board: [0.3, 0.64],
  battLift: [0.34, 0.7],
  coverF: [0.52, 0.86],
  coverB: [0.52, 0.86],
  diaF: [0.56, 0.9],
  diaB: [0.56, 0.9],
  mech: [0.46, 0.8],
};
export const TRAVEL = Object.fromEntries(Object.entries(g).map(([name, group]) => [name, group.travel]));
export const follow = (values) => {
  const x = Math.min(1, Math.max(0, values.explode ?? 0));
  const out = { spin: values.spin ?? 0 };
  for (const [name, [a, b]] of Object.entries(STAGES)) {
    const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
    out[name] = TRAVEL[name] * t * t * (3 - 2 * t);
  }
  return out;
};
export const poses = () => {
  const out = [];
  for (let a = 0; a < 360; a += 4) for (let i = 0; i <= 25; i++) out.push(follow({ spin: a, explode: i / 25 }));
  return out;
};

export const layer = T.layer("model");
T.stack(["back", "model"]);

// ---------- helpers ----------
const box = (name, group, plan, z0, z1, o = {}) => T.prism({ name, group, layer, plan, z: z0, h: z1 - z0, steps: o.steps ?? 3, bevel: o.bevel ?? 0, tone: o.tone ?? "hi", crease: o.crease ?? "faint", material: o.material, lit: o.lit, owner: o.owner, details: o.details ?? {} });
const bar = (name, group, a, b, half, z0, z1, o = {}) => {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const l = Math.hypot(dx, dy);
  const nx = (-dy / l) * half;
  const ny = (dx / l) * half;
  const polygon = [[a[0] + nx, a[1] + ny], [a[0] - nx, a[1] - ny], [b[0] - nx, b[1] - ny], [b[0] + nx, b[1] + ny]];
  return T.prism({ name, group, layer, F: UP, polygon, round: o.round ?? 0, s0: z0, s1: z1, tone: o.tone ?? "hi", material: o.material, bevel: o.bevel ?? 0 });
};
const polyZ = (name, group, polygon, z0, z1, o = {}) => T.prism({ name, group, layer, F: UP, polygon, s0: z0, s1: z1, tone: o.tone ?? "hi", material: o.material, bevel: o.bevel ?? 0, details: o.details ?? {} });
const cylZ = (name, group, x, y, r, z0, z1, o = {}) => T.round({ name, group, layer, F: VERT(x, y), s0: z0, s1: z1, r, ends: o.ends, tone: o.tone ?? "hi", crease: o.crease ?? "faint", material: o.material, lit: o.lit, owner: o.owner, details: o.details ?? {} });
const cylX = (name, group, y, z, r, x0, x1, o = {}) => T.round({ name, group, layer, F: ALONG_X(y, z), s0: x0, s1: x1, r, ends: o.ends, tone: o.tone ?? "hi", material: o.material, lit: o.lit, owner: o.owner, details: o.details ?? {} });
const cylY = (name, group, x, z, r, y0, y1, o = {}) => T.round({ name, group, layer, F: ALONG_Y(x, z), s0: y0, s1: y1, r, ends: o.ends, tone: o.tone ?? "hi", material: o.material, lit: o.lit, owner: o.owner, details: o.details ?? {} });
const hex = (r, x, y, phase = Math.PI / 6) => Array.from({ length: 6 }, (_, j) => [x + r * Math.cos(phase + (j * Math.PI) / 3), y + r * Math.sin(phase + (j * Math.PI) / 3)]);
const text = (str, size, { tone = "lo", anchor = "middle", weight = 600, cls = "" } = {}) => `<text class="iso-face-text sgm-t ${cls}" data-tone="${tone}" font-size="${size}" font-weight="${weight}" text-anchor="${anchor}">${str}</text>`;
const at = (x, y, inner) => `<g transform="translate(${x} ${y})">${inner}</g>`;
// planes: text on a face. o = top-left anchor, u = reading direction, v = down the text
const frontPlane = (part, x, y, z, svg) => T.plane({ part, o: [x, y, z], u: [1, 0, 0], v: [0, 0, -1], svg });
const rightPlane = (part, x, y, z, svg) => T.plane({ part, o: [x, y, z], u: [0, -1, 0], v: [0, 0, -1], svg });
const topPlane = (part, x, y, z, svg) => T.plane({ part, o: [x, y, z], u: [1, 0, 0], v: [0, 1, 0], svg });
const shell = (prefix, group, plan, z0, z1, t, o = {}) => {
  const { x, y, w, d } = plan;
  const parts = [];
  parts.push(box(`${prefix}.front`, group, { x, y: y + d - t, w, d: t, r: 0.6 }, z0, z1, o));
  parts.push(box(`${prefix}.back`, group, { x, y, w, d: t, r: 0.6 }, z0, z1, o));
  parts.push(box(`${prefix}.left`, group, { x, y: y + t, w: t, d: d - 2 * t, r: 0.4 }, z0, z1, o));
  parts.push(box(`${prefix}.right`, group, { x: x + w - t, y: y + t, w: t, d: d - 2 * t, r: 0.4 }, z0, z1, o));
  return parts;
};

// ---------- the turntable ----------
const PLATTER_R = 122;
cylZ("stand.platter", spin, 0, 0, PLATTER_R, 0, 6, { tone: "mid", crease: "lo", material: "gunmetal", details: { seams: [1.4], bolts: [{ s: 6, r: PLATTER_R - 6, count: 24, size: 0.5, tone: "mid" }] } });

// ---------- G4 meter: cases ----------
export const M = { x: -86, y: -40, w: 104, d: 80, r: 6 };
const T_WALL = 2.4;
const SEAM = 72;
const CASE_TOP = 120;
const LOWER = { tone: "hi", crease: "lo", material: "steel" };
box("case.lower.floor", spin, M, 6, 8.4, { ...LOWER, steps: 4 });
shell("case.lower", spin, M, 8.4, SEAM, T_WALL, LOWER);
const upperWalls = shell("case.upper", g.upper, M, SEAM, CASE_TOP - T_WALL, T_WALL, LOWER);
const upperTop = box("case.upper.top", g.upper, M, CASE_TOP - T_WALL, CASE_TOP, { ...LOWER, steps: 4, bevel: 0.8 });
topPlane(upperTop, M.x + 52, M.y + 66, CASE_TOP, at(0, 0, text("G4 · Qmax 6 m³/h · Pmax 0.5 bar", 4.2, { tone: "mid" }) + `<g transform="translate(0 8.5)">${text("illustrative diaphragm meter", 3.2, { tone: "faint", weight: 500 })}</g>`));
topPlane(upperTop, -66, -14, CASE_TOP, text("IN", 4.6, { tone: "mid", weight: 700 }));
topPlane(upperTop, -2, -14, CASE_TOP, text("OUT", 4.6, { tone: "mid", weight: 700 }));
frontPlane(upperWalls[0], -24, M.y + M.d, 116, text("m³", 4, { tone: "mid", weight: 700 }));

// ports: the gas connections on top, painted gas-pipe yellow
for (const [name, x] of [["in", -66], ["out", -2]]) {
  cylZ(`port.${name}.neck`, g.upper, x, 0, 9, CASE_TOP, 134, { tone: "hi", material: "brass", details: { seams: [CASE_TOP + 2] } });
  polyZ(`port.${name}.nut`, g.upper, hex(12.2, x, 0), 134, 142, { tone: "hi", material: "brass", bevel: 0.4 });
  cylZ(`port.${name}.cap`, g.upper, x, 0, 7, 142, 144, { tone: "mid", material: "gunmetal" });
}

// ---------- measuring unit (core) ----------
const BLOCK = { x: -66, y: -14, w: 68, d: 28, r: 3 };
const BLOCK_TOP = 66;
box("unit.block", g.core, BLOCK, 8.4, BLOCK_TOP, { tone: "mid", crease: "lo", steps: 4, bevel: 0.6, material: "gunmetal", details: { seams: [36] } });
const CH = { x: -32, z: 37, r: 24 };
cylY("unit.diaphragm.front", g.diaF, CH.x, CH.z, CH.r, 14, 15.4, { material: "rubber", tone: "hi" });
cylY("unit.diaphragm.back", g.diaB, CH.x, CH.z, CH.r, -15.4, -14, { material: "rubber", tone: "hi" });
cylY("unit.cover.front", g.coverF, CH.x, CH.z, [CH.r + 1, CH.r - 3], 16.6, 26.6, { material: "steel", tone: "hi", details: { seams: [18.2] } });
cylY("unit.cover.back", g.coverB, CH.x, CH.z, [CH.r - 3, CH.r + 1], -26.6, -16.6, { material: "steel", tone: "hi", details: { seams: [-18.2] } });
// diaphragm discs: the flexing middle (a plate the flag rod is pinned to)
cylY("unit.plate.front", g.diaF, CH.x, CH.z, 10, 15.4, 16.6, { material: "chrome", tone: "mid" });
cylY("unit.plate.back", g.diaB, CH.x, CH.z, 10, -16.6, -15.4, { material: "chrome", tone: "mid" });

// valve grid, slide valves, flag rods, link arms, crank, gear, drive spindle, magnetic coupling (mech)
const GRID = { x: -48, y: -12, w: 44, d: 24, r: 2 };
box("mech.grid", g.mech, GRID, BLOCK_TOP, 69, { tone: "mid", material: "gunmetal", bevel: 0.3 });
box("mech.valve.a", g.mech, { x: -44, y: -10, w: 14, d: 8.6, r: 1.6 }, 69, 74, { tone: "hi", material: "brass", bevel: 0.4 });
box("mech.valve.b", g.mech, { x: -44, y: 1.4, w: 14, d: 8.6, r: 1.6 }, 69, 74, { tone: "hi", material: "brass", bevel: 0.4 });
for (const [i, y] of [[0, 7], [1, -7]]) cylZ(`mech.flag.${i}`, g.mech, -56, y, 2, BLOCK_TOP, 80, { material: "steel", tone: "mid" });
const CRANK = [-14, 0];
const PIN = [-24, 0];
bar("mech.link.0", g.mech, [-56, 7], [PIN[0], PIN[1] + 1.2], 1.8, 80, 82, { material: "chrome", round: 1.2 });
bar("mech.link.1", g.mech, [-56, -7], [PIN[0], PIN[1] - 1.2], 1.8, 82, 84, { material: "chrome", round: 1.2 });
cylZ("mech.crank.pin", g.mech, PIN[0], PIN[1], 1.3, 84, 92, { material: "steel", tone: "mid" });
cylZ("mech.crank.shaft.lo", g.mech, CRANK[0], CRANK[1], 2.4, 69, 84, { material: "steel", tone: "mid" });
cylZ("mech.gear", g.mech, CRANK[0], CRANK[1], 7, 84, 87, { material: "brass", tone: "hi", details: { ribs: { s0: 84.3, s1: 86.7, count: 48, seams: true, tone: "lo" } } });
cylZ("mech.crank.shaft.hi", g.mech, CRANK[0], CRANK[1], 2.4, 87, 92, { material: "steel", tone: "mid" });
bar("mech.crank.arm", g.mech, [CRANK[0] + 2, 0], [PIN[0] - 2, 0], 2.6, 92, 94.5, { material: "brass", round: 2.4 });
cylY("mech.spindle", g.mech, CRANK[0], 85.5, 1.3, 7, 35.2, { material: "steel", tone: "mid" });
cylY("mech.coupling", g.mech, CRANK[0], 85.5, 5.5, 35.2, 37.6, { material: "gunmetal", tone: "mid", details: { bolts: [{ s: 37.6, r: 3.2, count: 4, size: 0.45 }] } });

// ---------- index (counter) on the front ----------
const FRONT = M.y + M.d;
const BODY = { x: -60, y: FRONT, w: 70, d: 6, r: 1.4 };
const DRUM = { y: FRONT + 11.6, z: 92, r: 5.6, w: 6.4, gap: 0.6, x0: -55 };
box("index.body", g.counter, BODY, 78, 106, { tone: "lo", material: "gunmetal", bevel: 0.4 });
const BEZEL_Y = FRONT + 6;
const BEZEL_D = 12.4;
box("index.bezel.top", g.counter, { x: -60, y: BEZEL_Y, w: 70, d: BEZEL_D, r: 1 }, 97.8, 102, { tone: "mid", material: "gunmetal", bevel: 0.4 });
box("index.bezel.bottom", g.counter, { x: -60, y: BEZEL_Y, w: 70, d: BEZEL_D, r: 1 }, 82.4, 86.2, { tone: "mid", material: "gunmetal" });
box("index.bezel.left", g.counter, { x: -60, y: BEZEL_Y, w: 4.4, d: BEZEL_D, r: 0.6 }, 86.2, 97.8, { tone: "mid", material: "gunmetal" });
const digits = ["0", "0", "5", "1", "2", "3", "4", "7"];
let drumX = DRUM.x0;
const drums = [];
cylX("index.axle.0", g.counter, DRUM.y, DRUM.z, 1.5, -55.6, drumX, { material: "steel", tone: "mid" });
for (let i = 0; i < 8; i++) {
  const x0 = drumX;
  const x1 = x0 + DRUM.w;
  const red = i >= 5;
  const drum = cylX(`index.drum.${i}`, g.counter, DRUM.y, DRUM.z, DRUM.r, x0, x1, { tone: "hi", crease: "lo", lit: false, details: { seams: [x0 + 0.5, x1 - 0.5] } });
  drum.red = red;
  drums.push(drum);
  frontPlane(drum, (x0 + x1) / 2, DRUM.y + DRUM.r, DRUM.z - 2.3, text(digits[i], 6.4, { tone: red ? "hi" : "hi", weight: 700, cls: red ? "sgm-red-digit" : "sgm-digit" }));
  drumX = x1 + DRUM.gap;
  if (i < 7) cylX(`index.axle.${i + 1}`, g.counter, DRUM.y, DRUM.z, 1.5, x1, drumX, { material: "steel", tone: "mid" });
}
// the magnet sits in the last (0.001 m³) drum's end and closes the reed once per turn
const MAG_X0 = drumX - DRUM.gap;
cylX("index.magnet", g.counter, DRUM.y, DRUM.z, 3.2, MAG_X0, MAG_X0 + 2, { tone: "hi", lit: true, material: "chrome" });
box("index.bezel.right", g.counter, { x: MAG_X0 + 2, y: BEZEL_Y, w: 10 - (MAG_X0 + 2), d: BEZEL_D, r: 0.6 }, 86.2, 97.8, { tone: "mid", material: "gunmetal" });
const bezelTop = drums[0];
void bezelTop;

// ---------- reed pulser and its cable ----------
const PULSER = { x: -12, y: BEZEL_Y, w: 22, d: 11, r: 2 };
const pulser = box("pulser.body", g.pulser, PULSER, 72, 82.4, { tone: "hi", crease: "lo", bevel: 0.5, details: { seams: [74] } });
frontPlane(pulser, -1, PULSER.y + PULSER.d, 78.2, text("PULSE", 3.2, { tone: "lo", weight: 700 }));
cylX("pulser.reed", g.pulser, PULSER.y + PULSER.d + 1.4, 75, 1.4, -8, 6, { tone: "hi", lit: true, ends: ["dome", "dome"] });
const CABLE_Y = PULSER.y + PULSER.d / 2;
const CABLE_Z = 77;
const CABLE_R = 1.3;
const DY = -40;
const EL = { x: 32, y: -6, w: 60, d: 62, r: 4 };
export const E = { ...EL, y: EL.y + DY };
const GLAND_X = 44;
cylX("pulser.boot", g.pulser, CABLE_Y, CABLE_Z, 2.4, PULSER.x + PULSER.w, PULSER.x + PULSER.w + 3, { tone: "mid", material: "rubber" });
const CABLE_ROUTE = G.fillet([[PULSER.x + PULSER.w + 3, CABLE_Y, CABLE_Z], [GLAND_X, CABLE_Y, CABLE_Z], [GLAND_X, EL.y + EL.d + 6 + DY, CABLE_Z]], 14, 12);
T.tube({ name: "pulser.cable", group: g.pulser, layer, route: CABLE_ROUTE, r: CABLE_R, chunk: 6, tone: "hi", material: "rubber", hue: "blue" });

// ---------- SGM enclosure ----------
// The device is drawn in its own coordinates and shifted back by DY so it sits beside the meter, clear of the index.
const dbox = (n, gr, plan, z0, z1, o) => box(n, gr, { ...plan, y: plan.y + DY }, z0, z1, o);
const dcylZ = (n, gr, x, y, ...rest) => cylZ(n, gr, x, y + DY, ...rest);
const dcylY = (n, gr, x, z, r, y0, y1, o) => cylY(n, gr, x, z, r, y0 + DY, y1 + DY, o);
const dTop = (part, x, y, z, svg) => topPlane(part, x, y + DY, z, svg);
dbox("device.mount", spin, { x: 46, y: 12, w: 28, d: 28, r: 3 }, 6, 60, { tone: "mid", material: "gunmetal", bevel: 0.4 });
const BASE_Z = 60;
const FLOOR_TOP = 62.4;
const WALL_TOP = 96;
dbox("device.base.floor", spin, EL, BASE_Z, FLOOR_TOP, { tone: "hi", crease: "lo", steps: 4 });
const baseWalls = shell("device.base", spin, E, FLOOR_TOP, WALL_TOP, 2.4, { tone: "hi", crease: "lo" });
rightPlane(baseWalls[3], E.x + E.w, E.y + E.d - 8, 86, text("SGM · bench prototype", 3.4, { tone: "mid", anchor: "start", weight: 700 }) + `<g transform="translate(0 5)">${text("not for live gas", 3, { tone: "lo", anchor: "start", weight: 500 })}</g>`);
dcylY("device.gland", spin, GLAND_X, CABLE_Z, 3.4, EL.y + EL.d, EL.y + EL.d + 6, { tone: "mid", material: "gunmetal", details: { seams: [EL.y + EL.d + 3.8 + DY] } });

// main board and its parts (v0.2 board: U1 ESP32-S3, U3 AP63203 buck + L1, J1 USB-C, U2 USBLC6 ESD, J2 pulse, J3-J5 lab headers, SW1/SW2, D2 LED)
const PCB = { x: 36, y: -2, w: 30, d: 54, r: 1.5 };
const PCB_Z = 68;
const PCB_TOP = 69.6;
for (const [i, [x, y]] of k.corners(PCB, 3).entries()) dcylZ(`board.standoff.${i}`, g.board, x, y, 1.6, FLOOR_TOP, PCB_Z, { material: "brass", tone: "mid" });
dbox("board.pcb", g.board, PCB, PCB_Z, PCB_TOP, { tone: "hi", crease: "lo", steps: 2 });
dbox("board.esp32.pcb", g.board, { x: 46, y: 26, w: 18, d: 24, r: 0.4 }, PCB_TOP, 70.4, { tone: "mid" });
const can = dbox("board.esp32.can", g.board, { x: 46.5, y: 26.5, w: 17, d: 17, r: 0.6 }, 70.4, 72.8, { tone: "hi", material: "chrome", bevel: 0.3 });
dTop(can, 55, 33, 72.8, text("ESP32-S3", 2.4, { tone: "lo", weight: 700 }) + `<g transform="translate(0 3)">${text("WROOM-1", 1.9, { tone: "faint", weight: 600 })}</g>`);
dbox("board.usb", g.board, { x: 46, y: -2, w: 9, d: 7, r: 1 }, PCB_TOP, 72.8, { tone: "hi", material: "chrome", bevel: 0.3 });
dbox("board.esd", g.board, { x: 47, y: 6, w: 3, d: 2, r: 0.2 }, PCB_TOP, 70.5, { tone: "lo", material: "gunmetal" });
dbox("board.buck.ic", g.board, { x: 56, y: 2, w: 4, d: 3, r: 0.3 }, PCB_TOP, 70.8, { tone: "lo", material: "gunmetal" });
dbox("board.buck.inductor", g.board, { x: 57, y: 6, w: 7, d: 7, r: 1.2 }, PCB_TOP, 73.2, { tone: "mid", material: "gunmetal", bevel: 0.3 });
dbox("board.j3", g.board, { x: 37, y: 28, w: 3, d: 12, r: 0.3 }, PCB_TOP, 74.4, { tone: "lo", material: "gunmetal" });
dbox("board.j2", g.board, { x: 37, y: 44, w: 7, d: 5, r: 0.5 }, PCB_TOP, 74, { tone: "hi", bevel: 0.2 });
for (const [i, y] of [30.5, 35].entries()) {
  dbox(`board.sw${i + 1}`, g.board, { x: 41, y, w: 4, d: 3.4, r: 0.4 }, PCB_TOP, 71.2, { tone: "mid", material: "gunmetal" });
  dcylZ(`board.sw${i + 1}.key`, g.board, 43, y + 1.7, 1, 71.2, 72.2, { tone: "hi" });
}
dcylZ("board.led", g.board, 41.5, 50.8, 1.1, PCB_TOP, 71.4, { tone: "hi", lit: true });
for (const [i, [x, y]] of [[38.6, 1], [64.4, 1], [38.6, 21.6], [64.4, 21.6]].entries()) dcylZ(`board.modem.post.${i}`, g.board, x, y, 1.3, PCB_TOP, 80, { material: "brass", tone: "mid" });
// tamper switch on the base floor, held closed by the lid (GPIO15)
dbox("device.tamper", spin, { x: 80, y: -3, w: 6, d: 5, r: 0.6 }, FLOOR_TOP, 68, { tone: "mid", material: "gunmetal" });
dcylZ("device.tamper.plunger", spin, 83, -0.5, 1.2, 68, WALL_TOP, { tone: "hi", material: "steel" });

// modem daughterboard (common footprint: BG95-M3 or EC200U-EU), its antenna connector
dbox("modem.pcb", g.modem, { x: 37, y: -0.6, w: 29, d: 33, r: 1.2 }, 80, 81.6, { tone: "hi", crease: "lo", steps: 2 });
const mod = dbox("modem.module", g.modem, { x: 40, y: 1, w: 22, d: 18, r: 0.6 }, 81.6, 84.2, { tone: "hi", material: "chrome", bevel: 0.3 });
dTop(mod, 51, 13, 84.2, text("BG95 / EC200U", 2.2, { tone: "lo", weight: 700 }) + `<g transform="translate(0 3)">${text("LTE-M · Cat-1", 1.8, { tone: "faint", weight: 600 })}</g>`);
dcylZ("modem.ufl", g.modem, 62.6, 22, 1.1, 81.6, 82.8, { tone: "hi", material: "brass" });
dbox("modem.sim", g.modem, { x: 42, y: 21.6, w: 12, d: 9.6, r: 0.6 }, 81.6, 83.2, { tone: "hi", material: "chrome", bevel: 0.2 });

// battery (v0.3 recommendation): Li-SOCl2 D cell + hybrid layer capacitor on cradles
const BATT = { x: 79, z: 73, r: 9 };
for (const [i, y] of [[0, 8], [1, 36]]) dbox(`battery.cradle.${i}`, g.battLift, { x: 71, y, w: 16, d: 4, r: 0.6 }, FLOOR_TOP, 64, { tone: "mid", material: "gunmetal" });
dbox("battery.cradle.2", g.battLift, { x: 75, y: 47, w: 8, d: 4, r: 0.6 }, FLOOR_TOP, 64.4, { tone: "mid", material: "gunmetal" });
const cell = dcylY("battery.cell", g.battLift, BATT.x, BATT.z, BATT.r, 4, 44, { tone: "hi", crease: "lo", material: "gold", details: { seams: [6, 42] } });
dcylY("battery.terminal", g.battLift, BATT.x, BATT.z, 2.6, 44, 45.4, { tone: "mid", material: "steel" });
dcylY("battery.hlc", g.battLift, BATT.x, 68.4, 4, 45.8, 53.4, { tone: "hi", material: "gunmetal", details: { seams: [47] } });
T.plane({ part: cell, o: [BATT.x + 0.0, 24 + DY, BATT.z + BATT.r + 0.01], u: [0, 1, 0], v: [-1, 0, 0], svg: text("Li-SOCl₂ · D · 3.6 V", 2.6, { tone: "lo", weight: 700 }) });
void cell;

// lid, light pipe for D1, antenna
const lid = dbox("lid.plate", g.lid, EL, WALL_TOP, WALL_TOP + 2.6, { tone: "hi", crease: "lo", steps: 4, bevel: 0.8, details: { dots: k.corners(E, 4).map(([x, y]) => ({ at: [WALL_TOP + 2.6, x, y], normal: [0, 0, 1], size: 0.55, tone: "mid" })) } });
dTop(lid, EL.x + 26, EL.y + 36, WALL_TOP + 2.6, text("SGM", 9, { tone: "mid", weight: 800 }) + `<g transform="translate(0 7)">${text("کنتور هوشمند گاز", 4.4, { tone: "lo", weight: 700, cls: "sgm-fa" })}</g>`);
dcylZ("lid.lightpipe", g.lid, 41.5, 50.8, 1.4, WALL_TOP + 2.6, WALL_TOP + 3.6, { tone: "hi", lit: true });
dcylZ("lid.antenna.nut", g.lid, 84, 4, 4.4, WALL_TOP + 2.6, WALL_TOP + 6, { tone: "mid", material: "gunmetal" });
dcylZ("lid.antenna.whip", g.lid, 84, 4, 2, WALL_TOP + 6, WALL_TOP + 40, { tone: "hi", material: "rubber", ends: ["flat", "dome"] });

// ---------- the static display base under the turntable ----------
const baseSolid = k.cylinder(0, 0, PLATTER_R + 6, -12, 12, P, 120);
R.put({ name: "stand.base", layer: "back", at: [0, 0, -12], svg: `<path class="iso-halo" d="${k.haloOf({ x: -PLATTER_R, y: -PLATTER_R, w: 2 * PLATTER_R, d: 2 * PLATTER_R, r: PLATTER_R }, -12, 12, P)}"/>` + k.solidSvg(baseSolid, { tone: "lo", crease: "faint" }), shapes: [R.solid(A.cylinder(0, 0, PLATTER_R + 6, -12, 12, { name: "stand.base", ground: true }))] });
