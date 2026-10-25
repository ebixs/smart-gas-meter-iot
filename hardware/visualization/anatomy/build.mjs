// Fig 1 — one pulse is one hundredth of a cubic metre.
//
// A G4 diaphragm meter body on a bench (ports blanked: no gas), a clip-on reed
// pulser under its index, a cable, and the SGM enclosure. The last red index drum
// carries a magnet: one revolution = 0.01 m3 closes the reed once, one pulse runs
// down the cable and the enclosure's counter adds 0.01 m3. Every number shown
// comes from the model below (same constants as firmware/ and analytics/).
//
//   node hardware/visualization/anatomy/build.mjs [--light]
//
// Drawn with the anatomy kit (kit/iso-kit.mjs, MIT, github.com/wheresryan22/anatomy).
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "./kit/iso-kit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const theme = process.argv.includes("--light") ? "light" : "dark";
const kitScript = () => readFileSync(join(HERE, "kit/iso-kit.mjs"), "utf8").replace(/^export /gm, "");

// ---------------------------------------------------------------- model (truth)
const PULSE_M3 = 0.01;          // one revolution of the last red drum
const QMAX = 6;                 // m3/h, G4 meter
const START_M3 = 13505.287;     // sgm-0009's reading in the fleet console
const TIME_LAPSE = 60;          // simulated seconds per real second
const REED_SPAN = 0.22;         // share of a revolution the magnet holds the reed closed
const TOUR = [0.4, 1.6, 4.2, 1.6]; // m3/h: cooker, one heater, heater + boiler

// ---------------------------------------------------------------- world
const WIDTH = 640;
const HEIGHT = 372;
const PLATE = { x: -150, y: -62, w: 300, d: 124, r: 10 };
const PLATE_H = 10;
const FOOT_H = 5;

const CASE = { x: -128, y: -34, w: 116, d: 62, r: 6 };
const FRONT = CASE.y + CASE.d;          // 28
const CASE_Z0 = 4;
const SEAM_Z = 64;
const CASE_TOP = 124;
const INDEX = { x: -108, y: FRONT, w: 76, d: 7, r: 2 };
const INDEX_Z0 = 74;
const INDEX_Z1 = 106;
const INDEX_FRONT = FRONT + INDEX.d;    // 35
const WINDOW = { x0: -102, x1: -38, z0: 79, z1: 100, r: 2, depth: 3 };
const COLS = 8;                         // 5 black (m3) + 3 red (litres)
const COL_W = (WINDOW.x1 - WINDOW.x0 - 4) / COLS;
const DIGIT_H = 19;

const PULSER = { x: -92, y: FRONT, w: 30, d: 8, r: 2 };
const PULSER_Z0 = 50;
const PULSER_Z1 = 68;
const GLAND_A = { x: -62, y: FRONT + 2, w: 6, d: 4.4, r: 1 };
const PORTS = [[-100, -3], [-40, -3]];

const DEV = { x: 22, y: -26, w: 96, d: 52, r: 5 };
const DEV_FRONT = DEV.y + DEV.d;        // 26
const DEV_TOP = 64;
const LID_TOP = 70;
const LCD = { x0: 36, x1: 104, z0: 28, z1: 55, r: 2.5, depth: 2.4 };
const GLAND_B = { x: 30, y: DEV_FRONT, w: 7, d: 4.4, r: 1 };
const ANT = [100, -6];

const P = k.fitProjection(
  [...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), ...k.boxCorners(CASE, 0, 154), [ANT[0], ANT[1], 118]],
  WIDTH, HEIGHT, { pad: 20, azimuth: 52 },
);

const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const D = (pts, style) => k.dotsSvg(pts, style);
const byDepth = (pts) => [...pts].sort((a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P));
const planeOf = (y) => k.sideMatrix([0, y], 0, P, "left");
const flat = (x0, z0, x1, z1, r, steps = 6) =>
  k.pathOf(k.roundedPlan({ x: x0, y: z0, w: x1 - x0, d: z1 - z0, r }, steps).map(([u, z]) => [u, -z]), true);
const onFront = (pts, y) => k.pathOf(pts.map(([x, z]) => at([x, y, z])));
const onSide = (pts, x, closed = true) => k.pathOf(pts.map(([y, z]) => at([x, y, z])), closed);
const sideRect = (x, y0, z0, y1, z1, r) =>
  onSide(k.roundedPlan({ x: y0, y: z0, w: y1 - y0, d: z1 - z0, r }, 4), x);

let clips = 0;
// A window cut into a vertical face at y, with shaded inner walls (desk-computer recipe).
function recess({ x0, x1, z0, z1, r, depth }, y, back = "", backClass = "sgm-well") {
  const id = `sgm-clip-${clips++}`;
  const ring = k.roundedPlan({ x: x0, y: z0, w: x1 - x0, d: z1 - z0, r }, 6);
  const cx = (x0 + x1) / 2, cz = (z0 + z1) / 2;
  const { sinA } = k.cameraOf(P);
  const tops = [], sides = [[], [], [], []];
  ring.forEach(([ax, az], i) => {
    const [bx, bz] = ring[(i + 1) % ring.length];
    const len = Math.hypot(bx - ax, bz - az) || 1;
    let [nx, nz] = [(bz - az) / len, -(bx - ax) / len];
    if (nx * (cx - (ax + bx) / 2) + nz * (cz - (az + bz) / 2) < 0) [nx, nz] = [-nx, -nz];
    if (nx <= 0 && nz <= 0) return;
    const quad = k.pathOf([at([ax, y, az]), at([bx, y, bz]), at([bx, y - depth, bz]), at([ax, y - depth, az])], true);
    if (nz >= nx) tops.push(quad);
    else sides[Math.min(3, Math.max(0, Math.floor(((nx * -sinA + 1) / 2) * 4)))].push(quad);
  });
  const shape = flat(x0, z0, x1, z1, r);
  return [
    `<clipPath id="${id}"><path transform="${planeOf(y)}" d="${shape}"/></clipPath>`,
    `<g clip-path="url(#${id})">`,
    `<path class="iso-top" d="${tops.join("")}"/>`,
    ...sides.map((d, s) => (d.length ? `<path class="iso-shade" data-shade="${s}" d="${d.join("")}"/>` : "")),
    `<g transform="${planeOf(y - depth)}"><path class="${backClass}" d="${shape}"/>${back}<path class="iso-line" data-tone="faint" d="${shape}"/></g>`,
    `</g>`,
    `<g transform="${planeOf(y)}"><path class="iso-line" data-tone="lo" d="${shape}"/></g>`,
  ].join("");
}

// ---------------------------------------------------------------- bench
function bench() {
  const out = [`<path class="iso-halo" d="${k.haloOf(PLATE, -PLATE_H - FOOT_H, PLATE_H, P)}"/>`];
  for (const [x, y] of byDepth(k.corners(PLATE, 22))) {
    out.push(S(k.cylinder(x, y, 7, -PLATE_H - FOOT_H, 1.6, P, 28), { tone: "lo" }));
    out.push(S(k.cylinder(x, y, 5.4, -PLATE_H - FOOT_H + 1.6, FOOT_H - 1.6, P, 28), { tone: "mid" }));
  }
  out.push(S(k.slabOf(PLATE, -PLATE_H, PLATE_H, P, 8, 1.6), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(PLATE, 5), 0, P), { tone: "lo" }));
  const screws = k.corners(PLATE, 10);
  out.push(L(screws.map(([x, y]) => k.ring(x, y, 2.2, 0, P, 16)).join(""), { tone: "lo" }));
  out.push(D(screws.map(([x, y]) => at([x, y, 0])), { size: 0.5 }));
  // ruler strip along the front edge
  const strip = { x: -132, y: PLATE.y + PLATE.d - 14, w: 200, d: 7, r: 1 };
  out.push(S(k.slabOf(strip, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  const t = k.topTicks(strip.x + 4, strip.x + strip.w - 4, 4, 5, strip.y + 0.8, 0.6, [2, 3.6], P);
  out.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }));
  out.push(D([at([strip.x + 2, strip.y + 3.5, 0.6]), at([strip.x + strip.w - 2, strip.y + 3.5, 0.6])], { size: 0.45 }));
  // label plate: bench-only rig
  const label = { x: 84, y: PLATE.y + PLATE.d - 18, w: 46, d: 10, r: 1.2 };
  out.push(S(k.slabOf(label, 0, 0.8, P, 3), { tone: "lo", crease: "none" }));
  out.push(L(k.planOutline(k.insetPlan(label, 1.6), 0.8, P), { tone: "faint" }));
  out.push(L([32, 24, 28].map((w, i) => k.lineOnTop([label.x + 4, label.y + 2.6 + i * 2.4], [label.x + 4 + w, label.y + 2.6 + i * 2.4], 0.8, P)).join(""), { tone: "lo", free: true }));
  out.push(D([at([label.x + label.w - 3, label.y + label.d / 2, 0.8])], { size: 0.45 }));
  return out.join("");
}

// ---------------------------------------------------------------- meter body
function meterBack() {
  const out = [];
  // skids the casing stands on
  for (const y of [CASE.y + 4, FRONT - 10]) {
    out.push(S(k.slabOf({ x: CASE.x + 4, y, w: CASE.w - 8, d: 6, r: 1.2 }, 0, CASE_Z0, P, 3, 0.4), { tone: "lo" }));
  }
  out.push(`<path class="iso-halo" d="${k.haloOf(k.insetPlan(CASE, 2), CASE_Z0, 0.1, P)}" style="filter:blur(3px)"/>`);
  // lower and upper pressed-steel shells with the crimped seam band between them
  out.push(S(k.slabOf(CASE, CASE_Z0, SEAM_Z - 2 - CASE_Z0, P, 8, 1), { tone: "mid" }));
  const band = k.insetPlan(CASE, -1.4);
  out.push(S(k.slabOf(band, SEAM_Z - 2, 4, P, 8, 0.6), { tone: "mid", inner: L(k.sideSeam(band, SEAM_Z, P, 8), { tone: "faint" }) }));
  out.push(S(k.slabOf(CASE, SEAM_Z + 2, CASE_TOP - SEAM_Z - 2, P, 8, 1.4), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(CASE, 5), CASE_TOP, P), { tone: "faint" }));
  // flow arrow embossed on the top, between the ports
  const ay = 12;
  const arrow = [[-86, ay - 1.2], [-62, ay - 1.2], [-62, ay - 3.6], [-53, ay], [-62, ay + 3.6], [-62, ay + 1.2], [-86, ay + 1.2]];
  out.push(L(k.onTop(arrow, CASE_TOP, P, true), { tone: "lo" }));
  // rating plate above the index
  out.push(`<g transform="${planeOf(FRONT)}"><path class="iso-line" data-tone="lo" d="${flat(-108, 109, -40, 120, 1.4)}"/>` +
    [40, 28, 34].map((w, i) => `<path class="iso-line" data-tone="lo" data-free="" d="M${-103} ${-(117 - i * 3)}H${-103 + w}"/>`).join("") + `</g>`);
  out.push(D([at([-105, FRONT, 114.5]), at([-43, FRONT, 114.5])], { size: 0.45 }));
  return out.join("");
}

function ports() {
  const out = [];
  for (const [x, y] of byDepth(PORTS)) {
    out.push(S(k.cylinder(x, y, 11, CASE_TOP, 3, P, 40, 0.5), { tone: "mid" }));          // boss
    out.push(S(k.cylinder(x, y, 7, CASE_TOP + 3, 14, P, 36), { tone: "mid", crease: "none" })); // spigot
    out.push(L([CASE_TOP + 8, CASE_TOP + 12].map((z) => k.sideArc(x, y, 7, z, P, 20)).join(""), { tone: "faint" })); // thread
    out.push(S(k.cylinder(x, y, 9.6, CASE_TOP + 17, 8, P, 6, 0.4), { tone: "mid" }));      // hex union nut
    out.push(S(k.cylinder(x, y, 8, CASE_TOP + 25, 3.4, P, 36, 0.6), { tone: "hi", crease: "lo" })); // blanking cap
    out.push(L(k.ring(x, y, 4.2, CASE_TOP + 28.4, P, 28), { tone: "faint" }));
    out.push(D([at([x, y, CASE_TOP + 28.4])], { size: 0.5 }));
  }
  return out.join("");
}

function indexHousing() {
  const out = [];
  out.push(S(k.slabOf(INDEX, INDEX_Z0, INDEX_Z1 - INDEX_Z0, P, 4, 0.6), { tone: "mid" }));
  out.push(D([at([INDEX.x + 3, INDEX_FRONT, INDEX_Z1 - 3]), at([INDEX.x + INDEX.w - 3, INDEX_FRONT, INDEX_Z1 - 3]),
    at([INDEX.x + 3, INDEX_FRONT, INDEX_Z0 + 3]), at([INDEX.x + INDEX.w - 3, INDEX_FRONT, INDEX_Z0 + 3])], { size: 0.45 }));
  // drums seen through the window
  const cols = [];
  for (let c = 0; c < COLS; c++) {
    const x0 = WINDOW.x0 + 2 + c * COL_W;
    const red = c >= 5;
    const mid = x0 + COL_W / 2;
    const digits = [];
    for (let n = -1; n <= 10; n++) {
      digits.push(`<text x="${mid.toFixed(2)}" y="${(-(WINDOW.z0 + WINDOW.z1) / 2 + 3.4 + n * DIGIT_H).toFixed(2)}" class="sgm-digit${red ? " red" : ""}">${(n + 10) % 10}</text>`);
    }
    cols.push(`<path class="sgm-drum${red ? " red" : ""}" d="${flat(x0 + 0.4, WINDOW.z0 - 2, x0 + COL_W - 0.4, WINDOW.z1 + 2, 0, 1)}"/>`);
    cols.push(`<g data-drum="${c}">${digits.join("")}</g>`);
  }
  // drum shading: the drums are cylinders, darker toward top and bottom of the window
  cols.push(`<path class="sgm-drum-shade" d="${flat(WINDOW.x0, WINDOW.z1 - 4, WINDOW.x1, WINDOW.z1, 0, 1)}"/>`);
  cols.push(`<path class="sgm-drum-shade" d="${flat(WINDOW.x0, WINDOW.z0, WINDOW.x1, WINDOW.z0 + 4, 0, 1)}"/>`);
  // divider between the cubic-metre drums and the red litre drums
  cols.push(`<path class="iso-line" data-tone="lo" d="M${WINDOW.x0 + 2 + 5 * COL_W} ${-WINDOW.z0}V${-WINDOW.z1}"/>`);
  out.push(recess(WINDOW, INDEX_FRONT, cols.join("")));
  // decimal comma between m3 and litres, and the one engraved label
  out.push(`<g transform="${planeOf(INDEX_FRONT)}"><text class="iso-face-text" data-tone="mid" x="${WINDOW.x1 - 1}" y="${-(INDEX_Z0 + 1.6)}" font-size="3.6" text-anchor="end">m³</text>` + `</g>`);
  return out.join("");
}

function pulser() {
  const out = [];
  // clip bracket from the index housing down to the pulser
  out.push(S(k.slabOf({ x: -84, y: FRONT, w: 14, d: 3, r: 0.8 }, PULSER_Z1, INDEX_Z0 - PULSER_Z1, P, 3, 0.3), { tone: "lo" }));
  out.push(S(k.slabOf(PULSER, PULSER_Z0, PULSER_Z1 - PULSER_Z0, P, 4, 0.6), { tone: "hi", crease: "lo" }));
  const f = PULSER.y + PULSER.d;
  out.push(`<g transform="${planeOf(f)}"><path class="iso-line" data-tone="faint" d="${flat(PULSER.x + 3, PULSER_Z0 + 3, PULSER.x + PULSER.w - 3, PULSER_Z1 - 3, 1.4)}"/></g>`);
  out.push(D([at([PULSER.x + 5.5, f, PULSER_Z1 - 5.5]), at([PULSER.x + PULSER.w - 5.5, f, PULSER_Z0 + 5.5])], { size: 0.5 }));
  // reed window: the glass capsule seen through a slot, lights when the contact is closed
  out.push(`<g transform="${planeOf(f)}"><path class="sgm-slot" d="${flat(PULSER.x + 8, 57.5, PULSER.x + 22, 60.5, 1.5)}"/>` +
    `<path class="sgm-reed" data-part="reed" d="${flat(PULSER.x + 9, 58.3, PULSER.x + 21, 59.7, 0.7)}"/>` +
    `<path class="iso-line" data-tone="lo" d="${flat(PULSER.x + 8, 57.5, PULSER.x + 22, 60.5, 1.5)}"/></g>`);
  // cable gland on the +x side
  out.push(S(k.slabOf(GLAND_A, 52, 5, P, 3, 0.4), { tone: "mid" }));
  out.push(S(k.slabOf({ x: GLAND_A.x + GLAND_A.w, y: GLAND_A.y + 0.7, w: 2.2, d: 3, r: 0.8 }, 52.8, 3.4, P, 3), { tone: "mid" }));
  return out.join("");
}

// ---------------------------------------------------------------- SGM enclosure
function enclosure() {
  const out = [];
  for (const x of [DEV.x - 7, DEV.x + DEV.w - 1]) {
    out.push(S(k.slabOf({ x, y: -8, w: 8, d: 16, r: 2 }, 0, 2, P, 3, 0.4), { tone: "lo" }));
    out.push(L(k.ring(x + 3.5, 0, 1.6, 2, P, 14), { tone: "lo" }));
    out.push(D([at([x + 3.5, 0, 2])], { size: 0.45 }));
  }
  out.push(`<path class="iso-halo" d="${k.haloOf(k.insetPlan(DEV, 2), 0.2, 0.1, P)}" style="filter:blur(3px)"/>`);
  out.push(S(k.slabOf(DEV, 0, DEV_TOP, P, 6, 1.2), { tone: "mid", inner: L(k.sideSeam(DEV, 8, P, 6), { tone: "faint" }) }));
  const lid = k.insetPlan(DEV, -0.8);
  out.push(S(k.slabOf(lid, DEV_TOP, LID_TOP - DEV_TOP, P, 6, 0.8), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(DEV, 4), LID_TOP, P), { tone: "faint" }));
  const lidScrews = k.corners(DEV, 6);
  out.push(L(lidScrews.map(([x, y]) => k.ring(x, y, 1.8, LID_TOP, P, 14)).join(""), { tone: "lo" }));
  out.push(D(lidScrews.map(([x, y]) => at([x, y, LID_TOP])), { size: 0.5 }));
  // display window with the counter
  const lcd = [
    `<text class="sgm-lcd" data-part="lcd" x="${LCD.x1 - 6}" y="${-(LCD.z0 + 6)}" text-anchor="end">13505.28</text>`,
    `<text class="sgm-lcd-small" data-part="lcd-flow" x="${LCD.x0 + 5}" y="${-(LCD.z1 - 7)}">1.6 m³/h</text>`,
    `<text class="sgm-lcd-small" data-part="lcd-p" x="${LCD.x1 - 6}" y="${-(LCD.z1 - 7)}" text-anchor="end">P 1405/07</text>`,
  ].join("");
  out.push(recess(LCD, DEV_FRONT, lcd, "sgm-lcd-well"));
  // status LED and the two buttons
  out.push(`<g transform="${planeOf(DEV_FRONT)}"><circle class="sgm-led" data-part="led" cx="${LCD.x1 - 2}" cy="${-(LCD.z1 + 5)}" r="1.5"/>` +
    `<circle class="iso-line" data-tone="lo" cx="${LCD.x1 - 2}" cy="${-(LCD.z1 + 5)}" r="2.3" fill="none"/>` +
    `<path class="iso-line" data-tone="lo" d="${flat(LCD.x0 + 18, LCD.z0 - 9, LCD.x0 + 30, LCD.z0 - 4, 2.4)}${flat(LCD.x0 + 34, LCD.z0 - 9, LCD.x0 + 46, LCD.z0 - 4, 2.4)}"/>` +
    `</g>`);
  // right side: battery hatch with two screws and the SIM tray slot
  const side = DEV.x + DEV.w;
  out.push(L(sideRect(side, -18, 12, 14, 38, 2), { tone: "lo" }));
  out.push(D([at([side, -15, 35]), at([side, 11, 15])], { size: 0.45 }));
  out.push(L(sideRect(side, -16, 47, -2, 50, 1.4), { tone: "lo" }));
  out.push(D([at([side, -18.6, 48.5])], { size: 0.35 }));
  // cable gland on the front, lower left
  out.push(S(k.slabOf(GLAND_B, 8, 6, P, 3, 0.4), { tone: "mid" }));
  out.push(S(k.slabOf({ x: GLAND_B.x + 1.5, y: GLAND_B.y + GLAND_B.d, w: 4, d: 2, r: 0.8 }, 9.2, 3.6, P, 3), { tone: "mid" }));
  // antenna on the lid
  const [ax, ay] = ANT;
  out.push(S(k.cylinder(ax, ay, 5, LID_TOP, 4, P, 28, 0.4), { tone: "mid" }));
  out.push(L(k.knurl(ax, ay, 5, LID_TOP, LID_TOP + 4, 28, P), { tone: "lo" }));
  out.push(S(k.cylinder(ax, ay, 1.8, LID_TOP + 4, 38, P, 16), { tone: "mid", crease: "none" }));
  out.push(L([LID_TOP + 16, LID_TOP + 28].map((z) => k.sideArc(ax, ay, 1.8, z, P, 10)).join(""), { tone: "faint" }));
  out.push(S(k.cylinder(ax, ay, 2.6, LID_TOP + 42, 3, P, 20, 0.5), { tone: "mid" }));
  return out.join("");
}

// ---------------------------------------------------------------- cable
const CABLE = [
  [GLAND_A.x + GLAND_A.w + 2.2, GLAND_A.y + 2.2, 54.5],
  [4, GLAND_A.y + 2.2, 54.5],
  [4, 38, 50],
  [4, 38, 1.6],
  [GLAND_B.x + 3.5, 38, 1.6],
  [GLAND_B.x + 3.5, GLAND_B.y + GLAND_B.d + 2, 11],
];
const cablePts = CABLE.map(at);
const cableD = k.pathOf(cablePts);
function cable() {
  return `<path class="sgm-cable-jacket" d="${cableD}"/><path class="sgm-cable-core" d="${cableD}"/><path class="sgm-cable" d="${cableD}"/>` +
    D([cablePts[0], cablePts[cablePts.length - 1]], { size: 0.5 }) +
    `<circle class="sgm-pulse" data-part="pulse" r="2" cx="${cablePts[0][0]}" cy="${cablePts[0][1]}" opacity="0"/>`;
}

const svg = k.figureSvg({
  width: WIDTH, height: HEIGHT,
  label: "A G4 diaphragm gas meter body on a bench with its ports blanked, a reed pulser clipped under its index drums, a cable, and the Smart Gas Meter enclosure with a display and antenna. Each turn of the last red drum closes the reed once and sends one pulse to the enclosure.",
  body: [bench(), meterBack(), ports(), indexHousing(), pulser(), enclosure(), cable()],
});

// ---------------------------------------------------------------- live
const live = `
const PULSE_M3 = ${PULSE_M3}, QMAX = ${QMAX}, LAPSE = ${TIME_LAPSE}, REED_SPAN = ${REED_SPAN}, DIGIT_H = ${DIGIT_H}, COLS = ${COLS};
const TOUR = ${JSON.stringify(TOUR)};
const stage = document.querySelector(".iso-stage");
const svg = stage.querySelector("svg");
const drums = [...svg.querySelectorAll("[data-drum]")];
const reed = svg.querySelector('[data-part="reed"]');
const pulse = svg.querySelector('[data-part="pulse"]');
const wire = svg.querySelector(".sgm-cable");
const lcd = svg.querySelector('[data-part="lcd"]');
const lcdFlow = svg.querySelector('[data-part="lcd-flow"]');
const led = svg.querySelector('[data-part="led"]');
const readout = document.querySelector("[data-readout]");
const still = matchMedia("(prefers-reduced-motion: reduce)");
const wireLen = wire.getTotalLength();
let litres = Math.round(${START_M3} * 1000);   // integer litres, exact arithmetic
let frac = 0;                                   // sub-litre progress
let pulses = Math.floor(litres / 10);
let counted = pulses;                           // what the enclosure has received
let flow = TOUR[1], target = flow, touring = true, clock = 0, last = 0, frame = 0, visible = false, idle = 0;
const inflight = [];                            // pulse positions along the cable, 0..1
let ledT = 0;
function drumValues(totalLitres) {
  // odometer carry: a drum only turns while every drum to its right is on 9
  const vals = [];
  let carry = frac;                             // continuous part of the last drum
  let rest = totalLitres;
  for (let c = COLS - 1; c >= 0; c--) {
    const d = rest % 10;
    vals[c] = d + carry;
    carry = d === 9 ? carry : 0;
    rest = Math.floor(rest / 10);
  }
  return vals;
}
function draw() {
  const vals = drumValues(litres);
  drums.forEach((g, c) => g.setAttribute("transform", "translate(0 " + (-vals[c] * DIGIT_H).toFixed(2) + ")"));
  const turn = ((litres % 10) + frac) / 10;     // position of the last red drum's magnet in its revolution
  const closed = turn < REED_SPAN;
  reed.toggleAttribute("data-closed", closed);
  if (inflight.length) {
    const p = wire.getPointAtLength(inflight[0] * wireLen);
    pulse.setAttribute("cx", p.x.toFixed(1)); pulse.setAttribute("cy", p.y.toFixed(1)); pulse.setAttribute("opacity", "1");
  } else pulse.setAttribute("opacity", "0");
  const m3 = (counted * PULSE_M3).toFixed(2);
  if (lcd.textContent !== m3) lcd.textContent = m3;
  const f = flow.toFixed(1) + " m³/h";
  if (lcdFlow.textContent !== f) lcdFlow.textContent = f;
  led.toggleAttribute("data-on", ledT > 0);
  const text = flow.toFixed(1) + " m³/h · " + counted.toLocaleString("en-US") + " pulses · ×" + LAPSE;
  if (readout.textContent !== text) readout.textContent = text;
  stage.setAttribute("aria-valuenow", flow.toFixed(1));
  stage.setAttribute("aria-valuetext", text);
}
function tick(now) {
  const dt = last ? Math.min((now - last) / 1000, 1 / 20) : 1 / 60;
  last = now;
  if (touring) { clock += dt; target = TOUR[Math.floor(clock / 6) % TOUR.length]; }
  flow += (target - flow) * (1 - Math.exp(-dt / 0.6));
  // flow (m3/h) -> litres advanced in this frame of simulated time
  frac += flow * 1000 / 3600 * dt * LAPSE;
  while (frac >= 1) {
    frac -= 1; litres += 1;
    if (litres % 10 === 0) { pulses += 1; inflight.push(0); }   // the magnet arrives at the reed
  }
  for (let i = 0; i < inflight.length; i++) inflight[i] += dt / 0.55;
  while (inflight.length && inflight[0] >= 1) { inflight.shift(); counted += 1; ledT = 0.12; }
  ledT = Math.max(0, ledT - dt);
  draw();
  frame = visible && !still.matches ? requestAnimationFrame(tick) : 0;
}
const run = () => { if (!frame && visible && !still.matches) { last = 0; frame = requestAnimationFrame(tick); } };
const steer = (q) => { touring = false; target = Math.max(0, Math.min(QMAX, q)); clearTimeout(idle); idle = setTimeout(() => { touring = true; clock = 0; }, 4000); run(); };
new IntersectionObserver((e) => { visible = e[e.length - 1].isIntersecting; if (visible) run(); }, { rootMargin: "120px 0px" }).observe(stage);
stage.addEventListener("pointermove", (ev) => {
  const b = svg.getBoundingClientRect();
  steer(Math.max(0, Math.min(1, (ev.clientX - b.left) / b.width)) * QMAX);
});
stage.addEventListener("keydown", (ev) => {
  const step = ev.key === "ArrowRight" || ev.key === "ArrowUp" ? 0.5 : ev.key === "ArrowLeft" || ev.key === "ArrowDown" ? -0.5 : 0;
  if (!step) return;
  ev.preventDefault(); steer(target + step);
});
draw();
`;

const css = `<style>
.sgm-well{fill:var(--anatomy-shade-0)}
.sgm-lcd-well{fill:var(--sgm-lcd-bg)}
.sgm-drum{fill:var(--sgm-drum)}
.sgm-drum.red{fill:var(--sgm-drum-red)}
.sgm-drum-shade{fill:#000;opacity:.28}
.sgm-digit{fill:var(--sgm-digit);font:600 10.5px var(--anatomy-mono);text-anchor:middle}
.sgm-digit.red{fill:#fff}
.sgm-lcd{fill:var(--sgm-lcd-ink);font:600 11px var(--anatomy-mono);letter-spacing:.04em}
.sgm-lcd-small{fill:var(--sgm-lcd-ink);font:500 4.6px var(--anatomy-mono);opacity:.75}
.sgm-slot{fill:var(--anatomy-shade-0)}
.sgm-reed{fill:var(--anatomy-faint);transition:fill .08s}
.sgm-reed[data-closed]{fill:var(--anatomy-lit)}
.sgm-cable{fill:none;stroke:none}
.sgm-cable-jacket{fill:none;stroke:var(--anatomy-mid);stroke-width:3.2px;stroke-linejoin:round;stroke-linecap:round}
.sgm-cable-core{fill:none;stroke:var(--anatomy-face);stroke-width:1.9px;stroke-linejoin:round;stroke-linecap:round}
.sgm-pulse{fill:var(--anatomy-lit);stroke:var(--anatomy-paper);stroke-width:1px}
.sgm-led{fill:var(--anatomy-faint)}
.sgm-led[data-on]{fill:var(--anatomy-green)}
.iso{--sgm-drum:#0d0d0d;--sgm-drum-red:#8f1f1b;--sgm-digit:#e9e9e4;--sgm-lcd-bg:#1d2a22;--sgm-lcd-ink:#b9f2c9}
.iso[data-theme="light"]{--sgm-drum:#1b1b1d;--sgm-drum-red:#b3302b;--sgm-digit:#f4f4ef;--sgm-lcd-bg:#c9d6c4;--sgm-lcd-ink:#1d2b1f}
</style>`;

const body = k.plateHtml({
  fig: "Fig 1",
  title: "One pulse = 0.01 m³",
  hint: "Move to set the flow",
  readout: "1.6 m³/h · 1,350,528 pulses · ×60",
  keys: [
    { mark: "lit", label: "Reed contact and the pulse it sends: one per turn of the last red drum (0.01 m³)" },
    { mark: "raised", label: "Clip-on reed pulser under the index; meter ports blanked, bench only" },
    { mark: "line", label: "Cable to the SGM enclosure, which counts pulses and freezes the reading at each period" },
  ],
  caption:
    "The meter's index turns as gas flows; the last red drum moves one litre per digit, so one revolution is 0.01 m³. A magnet on that drum closes the reed once per turn and the enclosure adds 0.01 m³ per pulse. It never reads the drums, only counts pulses, which is why the pulse constant must be verified per meter model. Time runs 60× faster than real; a G4 meter tops out at 6 m³/h, one pulse every 6 s.",
  body: `${css}<div class="iso-stage" tabindex="0" role="slider" aria-label="Gas flow: arrow keys change it in 0.5 m³/h steps" aria-valuemin="0" aria-valuemax="${QMAX}" aria-valuenow="1.6">${svg}</div>`,
});

const out = join(HERE, theme === "light" ? "pulse-anatomy-light.html" : "pulse-anatomy.html");
writeFileSync(out, k.pageHtml({ title: "SGM pulse anatomy", theme, body, script: kitScript() + live, width: 720 }));
console.log("wrote", out);
