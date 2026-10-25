// Persian explainer: every frame is a pure function of t (render(t)). Inlined after the kit's TURN runtime.
// Injected: FIG (model), ITEMS (part notes), PLAN (scenes with timing and cues), FILM (analytics sample data), follow.
"use strict";
const FIG = __FIG__;
const ITEMS = __ITEMS__;
const PLAN = __PLAN__;
const FILM = __FILM__;
const follow = null;

const W = 1920;
const H = 1080;
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const sm = (x) => { x = clamp(x); return x * x * x * (x * (x * 6 - 15) + 10); };
const out3 = (x) => 1 - Math.pow(1 - clamp(x), 3);
const win = (t, a, b) => clamp((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
const $ = (id) => document.getElementById(id);
const NS = "http://www.w3.org/2000/svg";
const el = (tag, attrs = {}, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
const fa = (s) => String(s).replace(/[0-9]/g, (c) => "۰۱۲۳۴۵۶۷۸۹"[c]).replace(/\./g, "٫");
const faInt = (n) => fa(Math.round(n).toLocaleString("en-US")).replace(/,/g, "٬");
const show = (node, k, dy = 30) => { node.style.opacity = k.toFixed(3); node.style.transform = `translateY(${((1 - k) * dy).toFixed(1)}px)`; node.style.visibility = k > 0.001 ? "visible" : "hidden"; };

// ======================================================= the 3D model
const view = $("model");
const stage = view.querySelector(".sgm-stage");
const svgs = [...stage.querySelectorAll("svg")];
const live = stage.querySelector("svg[data-live]");
const back = svgs.find((svg) => !svg.hasAttribute("data-live"));
let vb = [0, 0, FIG.width, FIG.height];
for (const svg of svgs) { svg.setAttribute("preserveAspectRatio", "none"); svg.setAttribute("viewBox", vb.join(" ")); }
const controller = TURN.mount(stage, FIG.turn, { follow });
let shown = { spin: NaN, explode: NaN };
const pose = (spin, explode) => { if (spin === shown.spin && explode === shown.explode) return; controller.set({ spin, explode }); shown = { spin, explode }; };
const nodesByName = new Map([...live.querySelectorAll("[data-name]")].map((n) => [n.getAttribute("data-name"), n]));
const items = new Map(ITEMS.map((item) => [item.id, { ...item, nodes: [...nodesByName].filter(([name]) => item.match.some((m) => name.startsWith(m))).map(([, n]) => n) }]));
const VW = view.clientWidth;
const VH = view.clientHeight;
const unionBox = (nodes) => {
  const r = view.getBoundingClientRect();
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const node of nodes) { const b = node.getBoundingClientRect(); if (!b.width && !b.height) continue; x0 = Math.min(x0, b.left); y0 = Math.min(y0, b.top); x1 = Math.max(x1, b.right); y1 = Math.max(y1, b.bottom); }
  if (x0 === Infinity) return null;
  const sx = vb[2] / r.width;
  const sy = vb[3] / r.height;
  return [vb[0] + (x0 - r.left) * sx, vb[1] + (y0 - r.top) * sy, vb[0] + (x1 - r.left) * sx, vb[1] + (y1 - r.top) * sy];
};
const merge = (a, b) => (!a ? b : !b ? a : [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])]);
const allLive = [...nodesByName.values()];
const baseBox = unionBox([...back.querySelectorAll("path")]);
const FIT = [];
for (let i = 0; i <= 10; i++) { let box = baseBox; for (let a = 0; a < 360; a += 45) { pose(a, i / 10); box = merge(box, unionBox(allLive)); } FIT.push(box); }
const fitAt = (x) => { const f = clamp(x, 0, 1) * 10; const i = Math.min(9, Math.floor(f)); const k = f - i; return FIT[i].map((v, j) => v + (FIT[i + 1][j] - v) * k); };
const rectCache = new Map();
// a framing rectangle for some items at a pose; "fit" frames the whole model
function rectOf(ids, spin, explode, pad = { w: 76, h: 58 }) {
  if (!ids || ids === "fit") return fitAt(explode);
  const key = `${ids}|${spin.toFixed(1)}|${explode.toFixed(3)}`;
  if (rectCache.has(key)) return rectCache.get(key);
  const keep = { ...shown };
  pose(spin, explode);
  let box = unionBox(ids.flatMap((id) => items.get(id).nodes));
  pose(keep.spin, keep.explode);
  const cx = (box[0] + box[2]) / 2;
  const cy = (box[1] + box[3]) / 2;
  const w = Math.max(pad.w, box[2] - box[0]);
  const h = Math.max(pad.h, box[3] - box[1]);
  box = [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2];
  rectCache.set(key, box);
  return box;
}
function applyView(rect, fill) {
  const [x0, y0, x1, y1] = rect;
  const cx = (x0 + x1) / 2;
  const cy = (y0 + y1) / 2;
  let w = (x1 - x0) / fill;
  let h = (y1 - y0) / fill;
  if (w / h > VW / VH) h = (w * VH) / VW; else w = (h * VW) / VH;
  vb = [cx - w / 2, cy - h / 2, w, h];
  const text = vb.map((v) => v.toFixed(2)).join(" ");
  for (const svg of svgs) if (svg.getAttribute("viewBox") !== text) svg.setAttribute("viewBox", text);
}
let lit = "";
function highlight(ids, focus) {
  const key = (ids ?? []).join(",");
  if (key !== lit) {
    for (const n of live.querySelectorAll("[data-on]")) n.removeAttribute("data-on");
    for (const id of ids ?? []) for (const n of items.get(id).nodes) n.setAttribute("data-on", "");
    lit = key;
  }
  view.toggleAttribute("data-focus", Boolean(ids && ids.length) && focus > 0.001);
  view.style.setProperty("--focus", focus.toFixed(3));
}
const toScreen = ([x, y]) => [((x - vb[0]) / vb[2]) * VW, ((y - vb[1]) / vb[3]) * VH];

// ======================================================= timing
const SC = PLAN.scenes;
const sceneAt = (t) => { let i = 0; while (i + 1 < SC.length && t >= SC[i + 1].start) i++; return i; };
// time (absolute) at which a phrase is spoken inside a scene, from its character position in the narration
function cueTime(scene, phrase, after = 0) {
  const text = scene.text;
  const at = text.indexOf(phrase, after);
  const idx = at < 0 ? 0 : at;
  const chars = (s) => s.replace(/\s/g, "").length;
  return scene.narrStart + (chars(text.slice(0, idx)) / Math.max(1, chars(text))) * scene.narrDur;
}
for (const s of SC) s.cue = (phrase, after) => cueTime(s, phrase, after);

// ======================================================= subtitles
const sub = $("sub");
const subText = $("subtext");
function subtitleAt(t) {
  for (const s of SC) for (const seg of s.subs) if (t >= seg.a && t < seg.b) return { text: seg.text, k: Math.min(win(t, seg.a, seg.a + 0.18), 1 - win(t, seg.b - 0.12, seg.b)) };
  return null;
}

// ======================================================= scene modules
// Each module: { model?: (lt, s) => state, draw: (lt, s, k) => void }. lt is seconds into the scene, k the scene's opacity.
const MODEL_DEFAULT = { spin: -28, explode: 0, ids: null, focus: 0, frame: "fit", fill: 0.9 };
const modules = {};

// ---------- S01 hook
const i0 = (lt) => (lt < 0.001 ? 1 : out3(win(lt, -0.2, 0.6)));
{
  const big1 = $("s01n1"), big2 = $("s01n2"), bar = $("s01bar"), chip = $("s01chip"), kick = $("s01k");
  modules.s01 = {
    model: (lt, s) => ({ spin: lerp(-80, -26, sm(lt / s.dur)), explode: 0, ids: lt > s.cue("بیشترِ کنتورهای") - s.start ? ["drums"] : null, focus: 0.55 * win(lt, s.cue("بیشترِ کنتورهای") - s.start, s.cue("بیشترِ کنتورهای") - s.start + 1), frame: lt > s.cue("بیشترِ کنتورهای") - s.start ? ["index", "drums"] : "fit", fill: lt > s.cue("بیشترِ کنتورهای") - s.start ? 0.55 : 0.9, push: 0.04 }),
    draw(lt, s) {
      const t1 = s.cue("هشتصد") - s.start;
      const t2 = s.cue("ششصد") - s.start;
      const t3 = s.cue("نصب") - s.start;
      show(kick, i0(lt));
      show(big1, out3(win(lt, t1 - 0.4, t1 + 0.4)));
      big1.querySelector("b").textContent = faInt(860 * sm(win(lt, t1 - 0.3, t1 + 1.6)));
      show(big2, out3(win(lt, t2 - 0.4, t2 + 0.4)));
      big2.querySelector("b").textContent = faInt(660 * sm(win(lt, t2 - 0.3, t2 + 1.6)));
      bar.style.transform = `scaleX(${(0.767 * sm(win(lt, t2, t2 + 1.6))).toFixed(4)})`;
      show(chip, out3(win(lt, t3 - 0.3, t3 + 0.5)));
    },
  };
}

// ---------- S02 problem (2D)
{
  const svg = $("s02svg");
  const TL = { x: 120, y: 290, w: 1080, h: 270 };
  el("line", { x1: TL.x, y1: TL.y + TL.h, x2: TL.x + TL.w, y2: TL.y + TL.h, stroke: "var(--ink)", "stroke-width": 3 }, svg);
  // true daily use over 60 winter days (shape only): hidden between two readings
  const days = 60;
  const use = Array.from({ length: days }, (_, i) => 0.45 + 0.25 * Math.sin(i / 6.5) + 0.22 * Math.max(0, Math.sin(i / 3.1 + 1)) ** 3 + 0.08 * Math.sin(i * 1.7));
  const pts = use.map((u, i) => [TL.x + (i / (days - 1)) * TL.w, TL.y + TL.h - u * TL.h]);
  const ghost = el("path", { d: "M" + pts.map((p) => p.map((v) => v.toFixed(1)).join(" ")).join("L"), fill: "none", stroke: "var(--blue)", "stroke-width": 4, "stroke-linejoin": "round", "stroke-dasharray": "6 10", opacity: 0 }, svg);
  const fogs = el("rect", { x: TL.x + 40, y: TL.y - 20, width: TL.w - 80, height: TL.h + 20, fill: "url(#fog)", opacity: 0 }, svg);
  const g = el("linearGradient", { id: "fog", x1: 0, x2: 1 }, svg);
  [[0, 0], [0.08, 0.85], [0.92, 0.85], [1, 0]].forEach(([o, a]) => el("stop", { offset: o, "stop-color": "var(--bg)", "stop-opacity": a }, g));
  const readers = [0, 1].map((i) => {
    const x = TL.x + i * TL.w;
    const grp = el("g", { opacity: 0 }, svg);
    el("line", { x1: x, y1: TL.y - 40, x2: x, y2: TL.y + TL.h, stroke: "var(--ink)", "stroke-width": 4 }, grp);
    el("circle", { cx: x, cy: TL.y - 64, r: 24, fill: "var(--pipe)", stroke: "var(--ink)", "stroke-width": 4 }, grp);
    const tx = el("text", { x, y: TL.y + TL.h + 54, "text-anchor": "middle", class: "fa-svg", "font-size": 30, fill: "var(--ink2)" }, grp);
    tx.textContent = "قرائت";
    return grp;
  });
  const q = el("text", { x: TL.x + TL.w / 2, y: TL.y + TL.h / 2 + 40, "text-anchor": "middle", "font-family": "Bricolage", "font-weight": 800, "font-size": 200, fill: "var(--ink)", opacity: 0 }, svg);
  q.textContent = "?";
  // 27 million dots: a 30 × 9 grid, each dot ~100,000 subscribers
  const dots = [];
  for (let r = 0; r < 9; r++) for (let c = 0; c < 30; c++) dots.push(el("circle", { cx: 160 + c * 34, cy: 680 + r * 24, r: 7, fill: "var(--ink)", opacity: 0 }, svg));
  const n27 = $("s02n"), cost = $("s02cost"), head = $("s02h");
  modules.s02 = {
    draw(lt, s) {
      show(head, out3(win(lt, 0.1, 0.9)));
      readers.forEach((r, i) => r.setAttribute("opacity", out3(win(lt, 0.4 + i * 0.5, 1 + i * 0.5)).toFixed(3)));
      const tLeak = s.cue("نشتی") - s.start;
      const reveal = win(lt, 1.4, tLeak + 1.5);
      ghost.setAttribute("opacity", (0.25 + 0.75 * reveal).toFixed(3));
      ghost.setAttribute("stroke-dashoffset", (-lt * 30).toFixed(1));
      fogs.setAttribute("opacity", (0.95 * (1 - win(lt, tLeak, tLeak + 2.5))).toFixed(3));
      q.setAttribute("opacity", (out3(win(lt, 1.2, 2)) * (1 - win(lt, tLeak, tLeak + 1.5))).toFixed(3));
      const t27 = s.cue("بیست و هفت") - s.start;
      const shown27 = win(lt, t27 - 0.5, t27 + 2.2);
      dots.forEach((d, i) => d.setAttribute("opacity", (clamp(shown27 * dots.length - i) * 0.9).toFixed(3)));
      show(n27, out3(win(lt, t27 - 0.4, t27 + 0.4)));
      n27.querySelector("b").textContent = faInt(27 * sm(win(lt, t27 - 0.3, t27 + 1.6)));
      const t4 = s.cue("چهار میلیارد") - s.start;
      show(cost, out3(win(lt, t4 - 0.5, t4 + 0.3)));
    },
  };
}

// ---------- S03 idea (model)
{
  const head = $("s03h"), chips = [...document.querySelectorAll("#s03 .chip")];
  const CUES = ["بشمارد", "در پایانِ هر فصل", "با سیم‌کارت", "فاکتوری"];
  modules.s03 = {
    model(lt, s) {
      const a = s.cue("یک دستگاه کوچک") - s.start;
      const b = s.cue("هر ده لیتر") - s.start;
      const ids = lt > b ? ["pulser", "reed", "cable"] : lt > a ? ["enclosure", "lid", "antenna", "gland"] : null;
      return { spin: lerp(-26, 10, sm(lt / s.dur)), explode: 0, ids, focus: ids ? 0.6 : 0, frame: "fit", fill: 0.92, push: 0.05 };
    },
    draw(lt, s) {
      show(head, out3(win(lt, 0.2, 1)));
      chips.forEach((c, i) => { const tc = s.cue(CUES[i]) - s.start; show(c, out3(win(lt, tc - 0.3, tc + 0.4)), 20); });
    },
  };
}

// ---------- S04 inside the meter (model), S05 pulse, S06 device: cue-driven part tours
function partTour(s, list, base) {
  // list: [phrase, ids, frameIds?, extra?]; the camera eases from the previous framing to the new one over 1.1 s
  const times = list.map(([phrase]) => s.cue(phrase) - s.start);
  return (lt) => {
    let i = -1;
    for (let j = 0; j < times.length; j++) if (lt >= times[j] - 0.25) i = j;
    const b = base(lt);
    if (i < 0) return { ...b, ids: null, focus: 0, current: null, since: 0 };
    const [, ids, frameIds, extra] = list[i];
    const since = lt - (times[i] - 0.25);
    const prev = i > 0 ? list[i - 1] : null;
    return { ...b, ids, focus: 1, frame: frameIds ?? ids, prevFrame: prev ? prev[2] ?? prev[1] : b.frame, prevFill: prev ? 0.6 : b.fill, blend: sm(since / 1.1), fill: 0.6, current: ids[0], since, ...(extra ?? {}) };
  };
}
const card = $("partcard");
function drawPartCard(state, k) {
  if (!state || !state.current) { show(card, 0); return; }
  const item = items.get(state.current);
  if (card.dataset.id !== item.id) { card.dataset.id = item.id; card.querySelector("h3").textContent = item.fa.name; card.querySelector("small").textContent = item.en.name; card.querySelector("p").textContent = item.fa.does; }
  show(card, k * out3(state.since / 0.5), 16);
}
{
  const head = $("s04h");
  let tour = null;
  modules.s04 = {
    model(lt, s) {
      tour ??= partTour(s, [
        ["اتصالِ ورودی", ["ports"], ["case-upper", "ports"]],
        ["دو محفظهٔ اندازه‌گیری", ["block"]],
        ["دیافراگم‌های", ["diaphragm"], ["diaphragm", "covers"]],
        ["میله‌ها و بازوها", ["flags"]],
        ["میل‌لنگ می‌رسانند", ["crank"], ["crank", "flags"]],
        ["سوپاپ‌های کشویی", ["valves"]],
        ["چرخ‌دنده‌ها", ["gear"]],
        ["کوپلینگ", ["coupling"]],
        ["غلتک‌های شمارنده", ["drums"], ["drums", "index"]],
      ], (lt) => ({ spin: lerp(10, -24, sm(win(lt, 0, Math.max(1.5, s.cue("اتصالِ ورودی") - s.start)))), explode: sm(win(lt, 0.3, Math.max(2.5, s.cue("دو محفظهٔ") - s.start))), frame: "fit", fill: 0.9 }));
      return tour(lt);
    },
    draw(lt, s, k, st) { show(head, out3(win(lt, 0.2, 1)) * (1 - win(lt, 3, 3.8))); drawPartCard(st, k); },
  };
}
{
  const trace = $("s05trace"), eq = $("s05eq"), deb = $("s05deb");
  let tour = null;
  modules.s05 = {
    model(lt, s) {
      tour ??= partTour(s, [
        ["آخرین غلتکِ قرمز", ["drums"], ["drums", "magnet"]],
        ["آهنربای کوچک", ["magnet"], ["magnet", "drums"]],
        ["پالسرِ رید", ["pulser", "reed"], ["pulser", "magnet"]],
        ["فِرم‌ور", ["reed"], ["pulser", "reed"]],
      ], (lt) => ({ spin: lerp(-24, -12, sm(win(lt, 0, 2.5))), explode: lerp(1, 0, sm(win(lt, 0, 2.5))), frame: ["index", "pulser"], fill: 0.7 }));
      return tour(lt);
    },
    draw(lt, s, k, st) {
      drawPartCard(st, k);
      const tPulse = s.cue("یک پالس") - s.start;
      show(eq, out3(win(lt, s.cue("ده لیتر") - s.start - 0.3, s.cue("ده لیتر") - s.start + 0.5)));
      // live pulse trace: one clean pulse per drum turn, drawn as time scrolls
      const tDeb = s.cue("سی میلی‌ثانیه") - s.start;
      show(trace, out3(win(lt, tPulse - 0.6, tPulse)) * (1 - win(lt, tDeb - 0.8, tDeb - 0.2)));
      const pts = [];
      const span = 4;
      for (let i = 0; i <= 200; i++) {
        const x = i / 200;
        const tt = lt - span * (1 - x);
        const ph = (((tt - tPulse) % 1.6) + 1.6) % 1.6;
        const high = tt >= tPulse && ph < 0.35;
        pts.push(`${(20 + x * 560).toFixed(1)} ${(high ? 30 : 120).toFixed(1)}`);
      }
      trace.querySelector("path").setAttribute("d", "M" + pts.join("L"));
      show(deb, out3(win(lt, tDeb - 0.4, tDeb + 0.2)));
    },
  };
}
{
  const ab = $("s06ab"), batt = $("s06batt");
  let tour = null;
  modules.s06 = {
    model(lt, s) {
      tour ??= partTour(s, [
        ["بُردِ اصلی", ["pcb"], ["pcb"], { explode: 0.72 }],
        ["ESP32-S3", ["esp32"], ["esp32", "pcb"], { explode: 0.72 }],
        ["حافظهٔ فلش", ["esp32"], ["esp32", "pcb"], { explode: 0.72 }],
        ["بُردِ مودمِ", ["modem", "sim"], ["modem", "pcb"], { explode: 0.72 }],
        ["باتریِ", ["battery", "hlc"], ["battery", "hlc"], { explode: 0.8 }],
      ], (lt) => { const c = Math.max(2, s.cue("بُردِ اصلی") - s.start); return { spin: lerp(-12, 36, sm(win(lt, 0, c))), explode: lerp(0, 0.72, sm(win(lt, 0.2, c))), frame: "fit", fill: 0.9 }; });
      return tour(lt);
    },
    draw(lt, s, k, st) {
      drawPartCard(st, k);
      const tf = s.cue("حافظهٔ فلش") - s.start;
      show(ab, out3(win(lt, tf - 0.3, tf + 0.5)) * (1 - win(lt, s.cue("بُردِ مودمِ") - s.start - 0.3, s.cue("بُردِ مودمِ") - s.start + 0.2)));
      const flip = Math.floor(lt * 1.6) % 2;
      ab.querySelectorAll(".slot").forEach((n, i) => n.classList.toggle("on", i === flip));
      const tb = s.cue("بودجهٔ انرژیِ") - s.start;
      show(batt, out3(win(lt, tb - 0.3, tb + 0.5)));
    },
  };
}

// ---------- S07 seasonal self-reading (2D)
{
  const date = $("s07date"), clock = $("s07clock"), recd = $("s07rec"), json = $("s07json"), queue = $("s07q"), timer = $("s07timer"), sms = $("s07sms"), head = $("s07h");
  const LINES = ["{", '  "device_id": "sgm-bench-01",', '  "timestamp": "2026-09-22T20:30:00Z",', '  "pulse_count_total": 44,', '  "record_type": "period_close",', '  "period": { "calendar": "jalali",', '              "start": "1405/04", "months": 3 }', "}"];
  const SMS = "SGM1 sgm-bench-01 P=1405/04x3 C=44 S=4 T=20260922T2030Z";
  modules.s07 = {
    draw(lt, s) {
      show(head, out3(win(lt, 0.1, 0.8)));
      const t0 = s.cue("ساعتِ صفرِ") - s.start;
      // the clock runs 4 s into the boundary: 23:59:56 → 00:00:00 exactly at the cue "ثابت"
      const tb = s.cue("ثابت می‌کند") - s.start;
      const secs = Math.floor(clamp(lt - tb, -4, 60));
      const before = secs < 0;
      const hh = before ? 23 : 0, mm = before ? 59 : 0, ss = before ? 60 + secs : secs;
      date.textContent = before ? "۱۴۰۵/۰۶/۳۱ · شهریور" : "۱۴۰۵/۰۷/۰۱ · مهر";
      clock.textContent = fa(`${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}`);
      show($("s07clockwrap"), out3(win(lt, 0, 0.6)));
      void t0;
      $("s07clockwrap").classList.toggle("hit", lt >= tb && lt < tb + 1.2);
      const tr = s.cue("بستنِ دوره") - s.start;
      show(recd, out3(win(lt, tr - 0.4, tr + 0.3)));
      const n = Math.floor(clamp((lt - tr) / 1.4) * LINES.length);
      json.innerHTML = LINES.slice(0, n).map((l) => (/period_close|1405\/04/.test(l) ? `<mark>${l}</mark>` : l)).join("\n");
      const tq = s.cue("در صف") - s.start;
      show(queue, out3(win(lt, tq - 0.3, tq + 0.4)));
      const t24 = s.cue("بیست و چهار") - s.start;
      show(timer, out3(win(lt, t24 - 0.3, t24 + 0.3)));
      const hours = 24 * sm(win(lt, t24, t24 + 2.2));
      timer.querySelector("b").textContent = fa(Math.floor(hours)) + " ساعت";
      timer.querySelector("circle.fg").setAttribute("stroke-dashoffset", (264 * (1 - hours / 24)).toFixed(1));
      const ts = s.cue("پیامک") - s.start;
      show(sms, out3(win(lt, ts - 0.3, ts + 0.4)));
      sms.querySelector(".mono").textContent = SMS.slice(0, Math.floor(clamp((lt - ts) / 1.6) * SMS.length));
    },
  };
}

// ---------- S08 server: fleet → forecast → flag → invoice (2D)
{
  const svg = $("s08svg");
  const C = { x: 110, y: 330, w: 1060, h: 430 };
  const fleet = FILM.fleet;
  const fmax = Math.max(...fleet) * 1.08;
  const fx = (i) => C.x + (i / (fleet.length - 1)) * C.w;
  const fy = (v) => C.y + C.h - (v / fmax) * C.h;
  el("line", { x1: C.x, y1: C.y + C.h, x2: C.x + C.w, y2: C.y + C.h, stroke: "var(--line2)", "stroke-width": 2 }, svg);
  const area = el("path", { d: "M" + fleet.map((v, i) => `${fx(i).toFixed(1)} ${fy(v).toFixed(1)}`).join("L") + `L${C.x + C.w} ${C.y + C.h}L${C.x} ${C.y + C.h}Z`, fill: "var(--blue)", opacity: 0.12 }, svg);
  const line = el("path", { d: "M" + fleet.map((v, i) => `${fx(i).toFixed(1)} ${fy(v).toFixed(1)}`).join("L"), fill: "none", stroke: "var(--blue)", "stroke-width": 4, "stroke-linejoin": "round", pathLength: 1, "stroke-dasharray": "1 1" }, svg);
  const dotsG = el("g", {}, svg);
  const dots = Array.from({ length: 240 }, (_, i) => el("circle", { r: 6, fill: "var(--ink)" }, dotsG));
  const flag = $("s08flag"), inv = $("s08inv"), head = $("s08h"), lab = $("s08lab"), ok = $("s08ok");
  // the invoice card is filled once from the sample invoice
  const I = FILM.invoice;
  inv.querySelector(".lines").innerHTML = I.lines.map((l) => `<div><span>پله ${fa(l.tier)}</span><span>${fa(l.quantity_m3.toFixed(2))} مترمکعب</span><span>${faInt(l.amount)} ریال</span></div>`).join("");
  inv.querySelector(".id").textContent = I.id;
  inv.querySelector(".period").textContent = `دورهٔ ${fa(I.period)} · ${fa(I.m3.toFixed(2))} مترمکعب`;
  const qr = inv.querySelector("svg.qr");
  qr.setAttribute("viewBox", `0 0 ${FILM.qr.n} ${FILM.qr.n}`);
  el("path", { d: FILM.qr.d, fill: "var(--ink)" }, qr);
  modules.s08 = {
    draw(lt, s) {
      show(head, out3(win(lt, 0.1, 0.8)));
      const tf = s.cue("دویست و چهل") - s.start;
      const gather = sm(win(lt, tf, tf + 2.4));
      dots.forEach((d, i) => {
        const r = (i * 7919) % 240;
        const sx = C.x + (r % 24) * 44 + 20;
        const sy = C.y + 40 + Math.floor(r / 24) * 36;
        const tx = fx((i / 239) * (fleet.length - 1));
        const ty = fy(fleet[Math.round((i / 239) * (fleet.length - 1))]);
        d.setAttribute("cx", lerp(sx, tx, gather).toFixed(1));
        d.setAttribute("cy", lerp(sy, ty, gather).toFixed(1));
        d.setAttribute("opacity", (out3(win(lt, 0.1 + (i % 24) * 0.02, 0.8 + (i % 24) * 0.02)) * (1 - win(lt, tf + 2.2, tf + 2.8))).toFixed(3));
      });
      line.setAttribute("stroke-dashoffset", (1 - sm(win(lt, tf + 1.8, tf + 3.4))).toFixed(4));
      area.setAttribute("opacity", (0.12 * win(lt, tf + 2.6, tf + 3.6)).toFixed(3));
      show(lab, out3(win(lt, tf + 1.6, tf + 2.4)));
      const ta = s.cue("الگوهای غیرعادی") - s.start;
      show(flag, out3(win(lt, ta - 0.3, ta + 0.4)));
      const ti = s.cue("فاکتورِ پلکانی") - s.start;
      show(inv, out3(win(lt, ti - 0.5, ti + 0.4)), 40);
      const tok = s.cue("اصالتش") - s.start;
      show(ok, out3(win(lt, tok - 0.2, tok + 0.4)));
      const th = s.cue("علامتِ ناهنجاری") - s.start;
      flag.classList.toggle("hot", lt > th - 0.2);
    },
  };
}

// ---------- S09 everyday life (2D)
{
  const rows = [...document.querySelectorAll("#s09 .benefit")], phone = $("s09phone"), head = $("s09h");
  const CUES = ["عددِ واقعیِ", "منتظرِ", "غیرعادی"];
  modules.s09 = {
    draw(lt, s) {
      show(head, out3(win(lt, 0.1, 0.8)));
      show(phone, out3(win(lt, 0.3, 1.2)), 50);
      rows.forEach((r, i) => { const tc = s.cue(CUES[i]) - s.start; show(r, out3(win(lt, tc - 0.6, tc + 0.1)), 24); r.classList.toggle("on", lt >= tc - 0.2); });
      phone.querySelector(".alert").style.opacity = out3(win(lt, s.cue("غیرعادی") - s.start - 0.2, s.cue("غیرعادی") - s.start + 0.5)).toFixed(3);
    },
  };
}

// ---------- S10 NIGC (2D)
{
  const svg = $("s10svg"), head = $("s10h"), cards = [...document.querySelectorAll("#s10 .gain")], two = $("s10two"), note = $("s10note");
  const C = { x: 120, y: 330, w: 1000, h: 330 };
  // an illustrative winter demand curve (shape only) with a cold-day peak
  const n = 90;
  const ys = Array.from({ length: n }, (_, i) => 0.35 + 0.35 * Math.sin((i / n) * Math.PI) + 0.25 * Math.exp(-(((i - 52) / 5) ** 2)));
  const p = ys.map((y, i) => [C.x + (i / (n - 1)) * C.w, C.y + C.h - y * C.h]);
  el("line", { x1: C.x, y1: C.y + C.h, x2: C.x + C.w, y2: C.y + C.h, stroke: "var(--line2)", "stroke-width": 2 }, svg);
  const curve = el("path", { d: "M" + p.map((q) => q.map((v) => v.toFixed(1)).join(" ")).join("L"), fill: "none", stroke: "var(--serious)", "stroke-width": 5, pathLength: 1, "stroke-dasharray": "1 1" }, svg);
  const lower = el("path", { d: "M" + p.map(([x, y], i) => `${x.toFixed(1)} ${(y + 0.11 * C.h * Math.exp(-(((i - 52) / 9) ** 2))).toFixed(1)}`).join("L"), fill: "none", stroke: "var(--blue)", "stroke-width": 5, "stroke-dasharray": "10 8", opacity: 0 }, svg);
  const peakLab = el("text", { x: p[52][0], y: p[52][1] - 26, "text-anchor": "middle", class: "fa-svg", "font-size": 30, fill: "var(--ink)", opacity: 0 }, svg);
  peakLab.textContent = "روز اوج";
  const axisLab = el("text", { x: C.x + C.w, y: C.y + C.h + 44, "text-anchor": "end", class: "fa-svg", "font-size": 24, fill: "var(--muted)", opacity: 0 }, svg);
  axisLab.textContent = "تقاضای گاز در زمستان · شکل نمایشی";
  const CUES = ["قرائتِ خودکار", "تصویری نزدیک", "کشفِ زودترِ", "هوشمند کردنِ"];
  modules.s10 = {
    draw(lt, s) {
      show(head, out3(win(lt, 0.1, 0.8)));
      cards.forEach((c, i) => { const tc = s.cue(CUES[i]) - s.start; show(c, out3(win(lt, tc - 0.4, tc + 0.3)), 20); c.classList.toggle("on", lt >= tc - 0.2 && (i === CUES.length - 1 || lt < s.cue(CUES[i + 1]) - s.start - 0.2)); });
      const tc = s.cue("تصویری نزدیک") - s.start;
      curve.setAttribute("stroke-dashoffset", (1 - sm(win(lt, 0.3, Math.max(2.5, tc + 1)))).toFixed(4));
      axisLab.setAttribute("opacity", out3(win(lt, 0.2, 0.9)).toFixed(3));
      peakLab.setAttribute("opacity", out3(win(lt, tc + 1.4, tc + 2)).toFixed(3));
      const t2 = s.cue("دو درجه") - s.start;
      lower.setAttribute("opacity", out3(win(lt, t2 - 0.2, t2 + 0.8)).toFixed(3));
      show(two, out3(win(lt, t2 - 0.3, t2 + 0.5)));
      const tn = s.cue("هزینه و دقتِ") - s.start;
      show(note, out3(win(lt, tn - 0.3, tn + 0.5)));
    },
  };
}

// ---------- S11 honesty (2D) and S12 end (model)
{
  const rows = [...document.querySelectorAll("#s11 .tag")], steps = [...document.querySelectorAll("#s11 .next li")], head = $("s11h"), plate = $("s11plate");
  const CUES = ["پالس‌ها", "تعرفه", "هرگز نباید"];
  const STEP_CUES = ["آزمونِ میدانی", "گواهی‌های", "محفظهٔ نهایی"];
  modules.s11 = {
    draw(lt, s) {
      show(head, out3(win(lt, 0.1, 0.8)));
      show(plate, out3(win(lt, 0, 0.7)), 0);
      plate.style.transform = `rotate(${(-2 + 1.2 * sm(lt / s.dur)).toFixed(2)}deg) scale(${(1 + 0.03 * sm(lt / s.dur)).toFixed(4)})`;
      rows.forEach((r, i) => { const tc = s.cue(CUES[i]) - s.start; show(r, out3(win(lt, tc - 0.4, tc + 0.2)), 16); });
      steps.forEach((r, i) => { const tc = s.cue(STEP_CUES[i]) - s.start; show(r, out3(win(lt, tc - 0.4, tc + 0.2)), 16); });
    },
  };
}
{
  const parts = [...document.querySelectorAll("#s12 .end")];
  modules.s12 = {
    model: (lt, s) => ({ spin: lerp(40, -20, sm(lt / s.dur)), explode: lerp(0.35, 0, sm(win(lt, 0, 2.5))), ids: null, focus: 0, frame: "fit", fill: 0.86 }),
    draw(lt) { parts.forEach((p, i) => show(p, out3(win(lt, 0.6 + i * 0.35, 1.3 + i * 0.35)), 24)); },
  };
}

// ======================================================= render(t)
const sceneEls = SC.map((s) => $(s.id));
const MODEL_SCENES = new Set(SC.filter((s) => modules[s.id]?.model).map((s) => s.id));
const modelBox = $("modelbox");
function modelStateAt(i, t) {
  const s = SC[i];
  const m = modules[s.id];
  if (!m?.model) return null;
  const st = { ...MODEL_DEFAULT, ...m.model(clamp(t - s.start, 0, s.dur), s) };
  return st;
}
const blendState = (a, b, k) => ({ spin: lerp(a.spin, b.spin, k), explode: lerp(a.explode, b.explode, k), rect: a.rect.map((v, j) => lerp(v, b.rect[j], k)), fill: lerp(a.fill, b.fill, k) });
function resolve(st) {
  const rect = rectOf(st.frame === "fit" ? "fit" : st.frame, st.spin, st.explode);
  if (st.prevFrame !== undefined && st.blend < 1) {
    const from = rectOf(st.prevFrame === "fit" ? "fit" : st.prevFrame, st.spin, st.explode);
    return { spin: st.spin, explode: st.explode, rect: from.map((v, i) => lerp(v, rect[i], st.blend)), fill: lerp(st.prevFill, st.fill, st.blend) };
  }
  return { spin: st.spin, explode: st.explode, rect, fill: st.fill };
}
// smoothing in time without state: average the resolved camera over the last 0.6 s (fixed taps → deterministic)
function cameraAt(i, t) {
  const taps = [0, 0.1, 0.2, 0.32, 0.45, 0.6];
  const wts = [0.24, 0.2, 0.17, 0.15, 0.13, 0.11];
  let acc = null;
  let wsum = 0;
  for (let j = 0; j < taps.length; j++) {
    const tt = t - taps[j];
    let ii = sceneAt(Math.max(0, tt));
    let st = modelStateAt(ii, tt);
    if (!st) st = modelStateAt(i, t);
    const r = resolve(st);
    if (!acc) acc = { spin: 0, explode: 0, rect: [0, 0, 0, 0], fill: 0 };
    acc.spin += r.spin * wts[j]; acc.explode += r.explode * wts[j]; acc.fill += r.fill * wts[j];
    r.rect.forEach((v, q) => (acc.rect[q] += v * wts[j]));
    wsum += wts[j];
  }
  return { spin: acc.spin / wsum, explode: acc.explode / wsum, fill: acc.fill / wsum, rect: acc.rect.map((v) => v / wsum) };
}
function render(t) {
  const i = sceneAt(t);
  const s = SC[i];
  const lt = t - s.start;
  // scene opacity: crossfade 0.5 s at each cut
  SC.forEach((sc, j) => {
    const k = j === i ? Math.min(1, win(t, sc.start - 0.001, sc.start + 0.5)) : j === i - 1 ? 1 - win(t, s.start, s.start + 0.5) : 0;
    const node = sceneEls[j];
    node.style.opacity = (j === 0 && i === 0 ? 1 : k).toFixed(3);
    node.style.visibility = k > 0.001 || (j === 0 && i === 0) ? "visible" : "hidden";
    if (k > 0.001 || (j === 0 && i === 0)) modules[sc.id]?.draw?.(t - sc.start, sc, k || 1, j === i ? modelStateAt(j, t) : null);
  });
  if (!["s04", "s05", "s06"].includes(s.id)) show(card, i > 0 && ["s04", "s05", "s06"].includes(SC[i - 1].id) ? 1 - win(t, s.start, s.start + 0.4) : 0);
  // the model: shown in model scenes, faded through 2D scenes
  const inModel = MODEL_SCENES.has(s.id);
  const prevModel = i > 0 && MODEL_SCENES.has(SC[i - 1].id);
  const mk = inModel ? (prevModel || i === 0 ? 1 : win(t, s.start, s.start + 0.6)) : prevModel ? 1 - win(t, s.start, s.start + 0.5) : 0;
  modelBox.style.opacity = mk.toFixed(3);
  modelBox.style.visibility = mk > 0.001 ? "visible" : "hidden";
  if (mk > 0.001) {
    const mi = inModel ? i : i - 1;
    const mt = inModel ? t : SC[i - 1].start + SC[i - 1].dur - 0.001;
    const cam = cameraAt(mi, mt);
    const st = modelStateAt(mi, mt);
    // a slow push keeps every held frame alive
    const push = 1 + 0.035 * Math.sin(((mt - SC[mi].start) / SC[mi].dur) * Math.PI);
    pose(cam.spin, cam.explode);
    applyView(cam.rect, cam.fill * push);
    highlight(st.ids, st.focus ?? 0);
  }
  // subtitles
  const st = subtitleAt(t);
  if (st) { if (subText.textContent !== st.text) subText.textContent = st.text; sub.style.opacity = st.k.toFixed(3); } else sub.style.opacity = "0";
  // progress hairline
  $("progress").style.transform = `scaleX(${(t / PLAN.length).toFixed(5)})`;
  $("chapter").textContent = `${fa(i + 1)} / ${fa(SC.length)} · ${s.name}`;
}
window.__render = render;
window.__plan = PLAN;
render(Number(new URLSearchParams(location.search).get("t") ?? 0));
