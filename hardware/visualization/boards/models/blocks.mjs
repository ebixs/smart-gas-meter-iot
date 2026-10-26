// 3D exploded block diagram of the whole electronics: assembled it is one flat block diagram; exploded,
// it separates into its three voltage domains (5 V input, 3.3 V carrier logic, modem VBAT/1.8 V), with
// matching pegs showing where a signal or rail crosses from one domain to the next. Blocks name real parts.
import * as k from "../../exploded/kit/iso-kit.mjs";
import * as A from "../../exploded/kit/audit.mjs";
import { turning } from "../../exploded/kit/turn-build.mjs";

const WIDTH = 900;
const HEIGHT = 680;
const PLATE = { x: -140, y: -76, w: 280, d: 152, r: 8 };
const TH = 2.4; // plate thickness
const BH = 7; // block height
const GAP = 46; // tier separation when exploded
const reach = Math.hypot(PLATE.w, PLATE.d) / 2 + 2;
const ring = (r, z, m = 48) => Array.from({ length: m }, (_, i) => [r * Math.cos((i / m) * 2 * Math.PI), r * Math.sin((i / m) * 2 * Math.PI), z]);
const P = k.fitProjection([...ring(reach, 0), ...ring(reach * 0.8, 2 * GAP + TH + BH + 4)], WIDTH, HEIGHT, { pad: 18, azimuth: 90, elevation: 38 });
const R = A.recorder(P);
const T = turning(P, { recorder: R });
const spin = T.group("spin", { turn: { pivot: [0, 0] } });
const layer = T.layer("model");
T.stack(["back", "model"]);
// Assembled, every block sits on the one plate: an ordinary block diagram with three coloured regions.
// Exploded, the 3.3 V logic and the modem domain rise to their own levels; arrows that cross a domain
// boundary break exactly at that boundary.
const GROUP = {
  power: spin,
  logic: T.group("logic", { parent: spin, slide: { direction: [0, 0, 1], travel: GAP } }),
  modem: T.group("modem", { parent: spin, slide: { direction: [0, 0, 1], travel: 2 * GAP } }),
};
const STAGES = { logic: [0.1, 0.75], modem: [0.25, 0.95] };
const TRAVEL = { logic: GAP, modem: 2 * GAP };
const TOP = TH;

const text = (str, size, { tone = "lo", weight = 700, cls = "", dy = 0 } = {}) => `<text class="iso-face-text sgm-t ${cls}" data-tone="${tone}" font-size="${size}" font-weight="${weight}" text-anchor="middle" dy="${dy}">${str}</text>`;
const topPlane = (part, x, y, z, svg) => T.plane({ part, o: [x, y, z + 0.02], u: [1, 0, 0], v: [0, 1, 0], svg });
const UP = { o: [0, 0, 0], a: [0, 0, 1], u: [1, 0, 0], v: [0, 1, 0] };

T.prism({ name: "plate", group: spin, layer, plan: PLATE, z: 0, h: TH, steps: 4, tone: "hi", crease: "lo" });

const block = (tier, id, x, y, w, d, en, fa, refs, o = {}) => {
  const h = o.h ?? BH;
  const part = T.prism({ name: `block.${tier}.${id}`, group: GROUP[tier], layer, plan: { x: x - w / 2, y: y - d / 2, w, d, r: 2.4 }, z: TOP, h, steps: 3, tone: "hi", crease: "faint", material: o.material, bevel: 0.6 });
  const s = o.size ?? 4.4;
  const lines = text(en, s) + (fa ? `<g transform="translate(0 ${s * 1.35})">${text(fa, s * 1.05, { cls: "sgm-fa" })}</g>` : "") + (refs ? `<g transform="translate(0 ${s * 2.55})">${text(refs, 3.1, { tone: "mid", weight: 600 })}</g>` : "");
  topPlane(part, x, y - (fa ? s * 0.9 : 0), TOP + h, lines);
  return part;
};
const arrow = (tier, id, a, b, { head = true, material = "copper" } = {}) => {
  const z0 = TOP;
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const l = Math.hypot(dx, dy);
  const ux = dx / l;
  const uy = dy / l;
  const half = 1.1;
  const hl = head ? Math.min(4.2, l * 0.6) : 0;
  const end = [b[0] - ux * hl, b[1] - uy * hl];
  const nx = -uy * half;
  const ny = ux * half;
  T.prism({ name: `link.${tier}.${id}`, group: GROUP[tier], layer, F: UP, polygon: [[a[0] + nx, a[1] + ny], [a[0] - nx, a[1] - ny], [end[0] - nx, end[1] - ny], [end[0] + nx, end[1] + ny]], s0: z0, s1: z0 + 1, tone: "mid", material });
  if (head) T.prism({ name: `link.${tier}.${id}.head`, group: GROUP[tier], layer, F: UP, polygon: [[end[0] - uy * 2.8, end[1] + ux * 2.8], [end[0] + uy * 2.8, end[1] - ux * 2.8], [b[0], b[1]]], s0: z0, s1: z0 + 1, tone: "mid", material });
};

// region tabs
block("power", "tab", -107, -68, 58, 10, "5 V INPUT · ورودی ۵ ولت", "", "", { h: 1.4, size: 3.8 });
block("logic", "tab", -14, -68, 104, 10, "3.3 V CARRIER LOGIC · منطق ۳٫۳ ولت بُرد حامل", "", "", { h: 1.4, size: 3.8 });
block("modem", "tab", 94, -68, 84, 10, "MODEM BOARD · VBAT / 1.8 V · بُرد مودم", "", "", { h: 1.4, size: 3.8 });

// 5 V input (carrier, left)
block("power", "usb", -107, -44, 50, 24, "USB-C 5 V", "ورودی USB-C", "J1 · R1 R2");
block("power", "protect", -107, -12, 50, 24, "Protection", "حفاظت", "F1 · D1 · U2");
block("power", "buck", -107, 20, 50, 24, "Buck 3.3 V", "مبدل باک", "U3 AP63203 · L1");
arrow("power", "usb-protect", [-107, -31.5], [-107, -24.5]);
arrow("power", "protect-buck", [-107, 0.5], [-107, 7.5]);
arrow("power", "3v3", [-81.5, 20], [-73, 20], { head: false });
arrow("power", "usbdata", [-81.5, -44], [-73, -44], { head: false });

// 3.3 V carrier logic (middle)
block("logic", "esp32", -24, 0, 56, 40, "ESP32-S3", "میکروکنترلر", "U1 WROOM-1-N8", { size: 5.2, material: "chrome" });
block("logic", "header", 28, 0, 24, 40, "J6", "اتصال مودم", "1×08", { size: 4.6 });
block("logic", "pulse", -38, -48, 30, 20, "Pulse in", "ورودی پالس", "J2 · GPIO4", { size: 3.9 });
block("logic", "tamper", -4, -48, 30, 20, "Tamper", "ضددستکاری", "J3 · GPIO15", { size: 3.9 });
block("logic", "keys", 28, -48, 24, 20, "RST · BOOT", "ریست", "SW1 SW2", { size: 3.6 });
block("logic", "led", -38, 48, 30, 20, "Status LED", "چراغ وضعیت", "D2 · GPIO5", { size: 3.9 });
block("logic", "io", -4, 48, 30, 20, "I²C · UART", "توسعه و سریال", "J4 · J5", { size: 3.9 });
arrow("logic", "3v3", [-70, 20], [-52.5, 14]);
arrow("logic", "usbdata", [-70, -44], [-53, -16]);
arrow("logic", "pulse", [-38, -37.5], [-38, -20.5]);
arrow("logic", "tamper", [-4, -37.5], [-8, -20.5]);
arrow("logic", "keys", [24, -36], [2, -20.5]);
arrow("logic", "led", [-38, 20.5], [-38, 37.5]);
arrow("logic", "io", [-4, 20.5], [-4, 37.5]);
arrow("logic", "j6", [4.5, 0], [15.5, 0]);
arrow("logic", "uart-out", [40.5, 0], [47, 0], { head: false });
arrow("logic", "en-out", [40.5, -12], [47, -12], { head: false });

// modem board (right)
block("modem", "shift", 70, 0, 24, 22, "Shift", "تبدیل سطح", "Q3–Q5", { size: 3.8 });
block("modem", "drivers", 70, -34, 24, 22, "PWRKEY", "روشن/ریست", "Q1 · Q2", { size: 3.8 });
block("modem", "ec200u", 113, 0, 46, 36, "EC200U-EU", "ماژول LTE", "LTE Cat 1 · NET LED", { size: 5, material: "chrome" });
block("modem", "sim", 113, -44, 40, 20, "micro-SIM", "سیم‌کارت", "J3 · U2 ESD224", { size: 3.9 });
block("modem", "ant", 113, 44, 40, 20, "Antenna", "آنتن", "J4 u.FL · π", { size: 3.9 });
block("modem", "vbat", 70, 34, 24, 22, "VBAT", "مخزن VBAT", "2×100 µF", { size: 3.8 });
block("modem", "bench", 70, 63, 24, 14, "J7 3.8 V", "", "bench supply", { size: 3.6 });
arrow("modem", "uart-in", [50, 0], [57.5, 0]);
arrow("modem", "en-in", [50, -12], [60, -22.5]);
arrow("modem", "shift-ec", [82.5, 0], [89.5, 0]);
arrow("modem", "drivers-ec", [84, -28], [94, -18.5]);
arrow("modem", "sim", [113, -18.5], [113, -33.5]);
arrow("modem", "ant", [113, 18.5], [113, 33.5]);
arrow("modem", "vbat", [84, 28], [94, 18.5]);
arrow("modem", "bench", [70, 55.5], [70, 45.5]);

const follow = (values) => {
  const x = Math.min(1, Math.max(0, values.explode ?? 0));
  const out = { spin: values.spin ?? 0 };
  for (const [name, [a, b]] of Object.entries(STAGES)) {
    const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
    out[name] = TRAVEL[name] * t * t * (3 - 2 * t);
  }
  return out;
};
const poses = () => {
  const out = [];
  for (let a = 0; a < 360; a += 6) for (let i = 0; i <= 20; i++) out.push(follow({ spin: a, explode: i / 20 }));
  return out;
};

export const model = { P, R, T, WIDTH, HEIGHT, follow, poses, STAGES, TRAVEL };
export const LABEL = "An exploded 3D block diagram of the Smart Gas Meter electronics: assembled it is one block diagram; exploded it separates into the 5 V input, the 3.3 V carrier logic and the modem's VBAT and 1.8 V domain.";
