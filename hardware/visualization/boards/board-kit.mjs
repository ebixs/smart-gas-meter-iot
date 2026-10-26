// Builds an exploded, turnable model of a real KiCad board from its extracted JSON (tools/pcb_extract.py).
// The board's layer stack becomes thin slabs that separate on explode, each carrying that layer's real artwork
// (copper, solder-mask openings, silkscreen, drill holes) as a plane on its top face; parts sit at their real
// CPL positions with body sizes from their footprints' fabrication outlines. World units are millimetres.
import * as k from "../exploded/kit/iso-kit.mjs";
import * as A from "../exploded/kit/audit.mjs";
import { turning } from "../exploded/kit/turn-build.mjs";

// body height (mm) and look per footprint family; first match wins
const LOOKS = [
  [/^R_0402/, { h: 0.35, kind: "res" }], [/^R_0603/, { h: 0.45, kind: "res" }],
  [/^C_0402/, { h: 0.5, kind: "cap" }], [/^C_0603/, { h: 0.8, kind: "cap" }], [/^C_0805/, { h: 1.25, kind: "cap" }],
  [/^C_1206/, { h: 1.6, kind: "cap" }], [/^CP_EIA/, { h: 2.1, kind: "tant" }], [/^Fuse_1206/, { h: 0.85, kind: "fuse" }],
  [/^D_SM[AB]/, { h: 2.3, kind: "ic" }], [/^LED_0603/, { h: 0.6, kind: "led" }],
  [/^SOT-23/, { h: 1.1, kind: "ic" }], [/^TSOT-23/, { h: 0.9, kind: "ic" }], [/^USON/, { h: 0.55, kind: "ic" }],
  [/^L_Sunlord/, { h: 3.0, kind: "ind" }], [/^ESP32-S3-WROOM/, { h: 3.1, kind: "esp" }],
  [/^USB_C_Receptacle/, { h: 3.2, kind: "usb" }], [/^SW_SPST_TL3342/, { h: 1.5, kind: "sw" }],
  [/^PinHeader/, { h: 2.5, kind: "header" }], [/^PinSocket/, { h: 8.5, kind: "socket" }],
  [/^U\.FL/, { h: 1.25, kind: "ufl" }], [/^microSIM/, { h: 1.4, kind: "sim" }], [/^Quectel_EC200U/, { h: 2.4, kind: "module" }],
];
const SKIP = /^(TestPoint|MountingHole|SolderJumper)/;

export function boardModel({ data, stack, width = 860, height = 820, azimuth = 34, elevation = 30, gap = 13, lift = 0.0, labels = {}, onTop = () => {} }) {
  const W = data.w;
  const D = data.h;
  const X0 = -W / 2;
  const Y0 = -D / 2;
  const wx = (x) => X0 + x;
  const wy = (y) => Y0 + y;
  const TH = 0.3; // slab thickness: copper layer and the dielectric under it, 6 slabs = 1.8 mm
  const n = stack.length;
  const top = n * TH; // board top surface (assembled)
  // explode offsets: layer i (0 = top) moves by (i0 - i) * gap; parts follow their side
  const i0 = (n - 1) / 2;
  const off = (i) => (i0 - i) * gap;
  const fitted = (f) => f.body && !SKIP.test(f.fp) && !/\(DNP\)/.test(f.value); // not-fitted parts are left off, as on a real board
  const tops = data.footprints.filter((f) => f.side === "F" && fitted(f));
  const bottoms = data.footprints.filter((f) => f.side === "B" && fitted(f));
  const partLift = off(0) + gap * 1.15;
  const zMax = top + partLift + 12;
  const zMin = -(gap * (n - 1 - i0)) - (bottoms.length ? gap * 1.15 + 10 : 2);
  const reach = Math.hypot(W, D) / 2 + 1 + Math.abs(lift) * Math.max(zMax, -zMin);
  const ring = (r, z, m = 48) => Array.from({ length: m }, (_, i) => [r * Math.cos((i / m) * 2 * Math.PI), r * Math.sin((i / m) * 2 * Math.PI), z]);
  const P = k.fitProjection([...ring(reach, zMin), ...ring(reach, zMax)], width, height, { pad: 18, azimuth, elevation });
  const R = A.recorder(P);
  const T = turning(P, { recorder: R });
  const spin = T.group("spin", { turn: { pivot: [0, 0] } });
  const layer = T.layer("model");
  T.stack(["back", "model"]);
  const lean = [0, lift, 1];
  const slide = (name, z) => T.group(name, { parent: spin, slide: { direction: z >= 0 ? lean : [0, -lift, -1], travel: Math.abs(z) * Math.hypot(lift, 1) } });

  const groups = {};
  const STAGES = {};
  const TRAVEL = {};
  // top parts lift first, then the stack opens from the outside in
  groups.top = slide("top", partLift);
  STAGES.top = [0, 0.45];
  stack.forEach((s, i) => {
    const z = off(i);
    if (Math.abs(z) < 1e-6) return;
    groups[s.id] = slide(s.id, z);
    const order = Math.abs(i - i0) / Math.max(1, i0);
    STAGES[s.id] = [0.18 + 0.3 * (1 - order), 0.62 + 0.3 * (1 - order)];
  });
  if (bottoms.length) {
    groups.bottom = slide("bottom", -(gap * (n - 1 - i0) + gap * 1.15));
    STAGES.bottom = [0, 0.45];
  }
  for (const [name, gr] of Object.entries(groups)) TRAVEL[name] = gr.travel;

  // ---------- the layer slabs, top first ----------
  const plan = { x: X0, y: Y0, w: W, d: D, r: data.r ?? 2 };
  stack.forEach((s, i) => {
    const z0 = top - (i + 1) * TH;
    const group = groups[s.id] ?? spin;
    const slab = T.prism({ name: `layer.${s.id}`, group, layer, plan, z: z0, h: TH, steps: 3, tone: "hi", crease: "lo" });
    const art = s.art.map(([key, cls]) => (data.layers[key] ? `<g class="${cls}">${data.layers[key]}</g>` : "")).join("") + `<g class="art-hole">${data.holes}</g>`;
    T.plane({ part: slab, o: [X0, Y0, z0 + TH + 0.01], u: [1, 0, 0], v: [0, 1, 0], svg: `<g class="art">${art}</g>`, fade: [0.02, 0.12] });
  });

  // ---------- parts ----------
  const rect = ([x0, y0, x1, y1], inset = 0) => ({ x: wx(x0) + inset, y: wy(y0) + inset, w: x1 - x0 - 2 * inset, d: y1 - y0 - 2 * inset, r: Math.min(0.3, (x1 - x0) / 6) });
  const label = (part, f, z, str, size) => T.plane({ part, o: [wx((f.body[0] + f.body[2]) / 2), wy((f.body[1] + f.body[3]) / 2), z + 0.01], u: [1, 0, 0], v: [0, 1, 0], svg: `<text class="iso-face-text sgm-t" data-tone="lo" font-size="${size}" font-weight="700" text-anchor="middle" dy="${size * 0.35}">${str}</text>` });
  const box = (name, group, p, z0, z1, o = {}) => T.prism({ name, group, layer, plan: p, z: z0, h: z1 - z0, steps: 2, tone: o.tone ?? "hi", crease: o.crease ?? "faint", material: o.material, lit: o.lit, bevel: o.bevel ?? 0 });
  const cyl = (name, group, x, y, r, z0, z1, o = {}) => T.round({ name, group, layer, F: { o: [x, y, 0], a: [0, 0, 1], u: [1, 0, 0], v: [0, 1, 0] }, s0: z0, s1: z1, r, tone: o.tone ?? "hi", crease: "faint", material: o.material, lit: o.lit });

  const place = (f, group, up) => {
    const look = LOOKS.find(([re]) => re.test(f.fp))?.[1] ?? { h: 1, kind: "ic" };
    const name = `cmp.${f.ref}`;
    const base = up ? top : 0;
    const z = (h) => (up ? [base, base + h] : [base - h, base]);
    const b = f.body;
    const shortSide = Math.min(b[2] - b[0], b[3] - b[1]);
    switch (look.kind) {
      case "esp": {
        const [z0, z1] = z(0.8);
        box(`${name}.pcb`, group, rect(b), z0, z1, { tone: "mid" });
        // the metal can covers the lower 17.6 mm of the 25.5 mm module; the antenna end stays bare
        const can = box(`${name}.can`, group, rect([b[0] + 1.1, b[3] - 18.4, b[2] - 1.1, b[3] - 0.8]), z1, z1 + 2.3, { material: "chrome", bevel: 0.2 });
        label(can, { body: [b[0], b[3] - 18.4, b[2], b[3] - 0.8] }, z1 + 2.3, "ESP32-S3", 2.2);
        break;
      }
      case "module": {
        const [z0, z1] = z(look.h);
        const can = box(`${name}.can`, group, rect(b, 0.4), z0, z1, { material: "chrome", bevel: 0.25 });
        label(can, f, z1, labels[f.ref] ?? f.value, 2.4);
        break;
      }
      case "header": {
        const [z0, z1] = z(look.h);
        box(`${name}.body`, group, rect(b, 0.05), z0, z1, { material: "rubber" });
        for (const p of f.pads) box(`${name}.pin.${p.n}`, group, { x: wx(p.x) - 0.32, y: wy(p.y) - 0.32, w: 0.64, d: 0.64, r: 0.08 }, z1, z1 + 6, { material: "gold" });
        break;
      }
      case "socket": {
        const [z0, z1] = z(look.h);
        box(`${name}.body`, group, rect(b, 0.05), z0, z1, { material: "rubber" });
        break;
      }
      case "sw": {
        const [z0, z1] = z(look.h);
        box(`${name}.body`, group, rect(b, 0.6), z0, z1, { material: "steel", bevel: 0.2 });
        cyl(`${name}.key`, group, wx((b[0] + b[2]) / 2), wy((b[1] + b[3]) / 2), 1.2, z1, z1 + 1, { material: "rubber" });
        break;
      }
      case "usb": {
        const [z0, z1] = z(look.h);
        box(`${name}.shell`, group, rect(b, 0.1), z0, z1, { material: "chrome", bevel: 0.3 });
        break;
      }
      case "ufl":
        cyl(`${name}.body`, group, wx((b[0] + b[2]) / 2), wy((b[1] + b[3]) / 2), 1.0, ...z(look.h), { material: "gold" });
        break;
      case "sim": {
        const [z0, z1] = z(look.h);
        box(`${name}.shell`, group, rect(b, 0.3), z0, z1, { material: "steel", bevel: 0.2 });
        break;
      }
      default: {
        const [z0, z1] = z(look.h);
        const inset = shortSide > 1.5 ? 0.05 : 0;
        const material = { res: "rubber", ic: "rubber", ind: "gunmetal", tant: undefined, fuse: undefined, cap: undefined, led: undefined }[look.kind];
        const part = box(`${name}.body`, group, rect(b, inset), z0, z1, { material, lit: look.kind === "led" });
        if (look.kind === "ind") label(part, f, z1, f.value.split(" ")[0], 1.1);
      }
    }
  };
  for (const f of tops) place(f, groups.top, true);
  for (const f of bottoms) place(f, groups.bottom, false);
  onTop({ T, groups, layer, wx, wy, top, box, cyl });

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
  return { P, R, T, WIDTH: width, HEIGHT: height, follow, poses, STAGES, TRAVEL };
}
