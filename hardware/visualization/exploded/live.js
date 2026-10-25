// Live page for the exploded SGM model. Inlined after the kit's TURN runtime; DATA, ITEMS, SECTIONS, follow are injected.
const FIG = __FIG__;
const ITEMS = __ITEMS__;
const SECTIONS = __SECTIONS__;
const UI = __UI__;
const follow = null;

const W = FIG.width;
const H = FIG.height;
const root = document.documentElement;
const view = document.querySelector(".sgm-view");
const stage = document.querySelector(".sgm-stage");
const svgs = [...stage.querySelectorAll("svg")];
const live = stage.querySelector("svg[data-live]");
const back = svgs.find((svg) => !svg.hasAttribute("data-live"));
const overlay = document.querySelector(".sgm-overlay");
const callout = document.querySelector(".sgm-callout");
const card = document.querySelector(".sgm-card");
const list = document.querySelector(".sgm-list");
const slider = document.querySelector("#sgm-explode");
const announce = document.querySelector(".sgm-live");
const still = matchMedia("(prefers-reduced-motion: reduce)");

const store = {
  get: (key) => { try { return localStorage.getItem(key); } catch { return null; } },
  set: (key, value) => { try { localStorage.setItem(key, value); } catch { /* private window */ } },
};

// ---------- parts and items ----------
const nodesByName = new Map([...live.querySelectorAll("[data-name]")].map((node) => [node.getAttribute("data-name"), node]));
const itemOfName = new Map();
for (const item of ITEMS) {
  item.nodes = [];
  for (const [name, node] of nodesByName) if (item.match.some((m) => name.startsWith(m))) { item.nodes.push(node); if (!itemOfName.has(name)) itemOfName.set(name, item); }
  for (const node of item.nodes) node.setAttribute("data-item", item.id);
}
const itemById = new Map(ITEMS.map((item, i) => [item.id, Object.assign(item, { n: i + 1 })]));
const faDigits = (s) => String(s).replace(/[0-9]/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[d]);
const two = (n) => String(n).padStart(2, "0");

let vb = [0, 0, W, H];
// the viewBox is always set to the view's aspect, so "none" never distorts; it keeps the client-rect mapping exact
for (const svg of svgs) { svg.setAttribute("preserveAspectRatio", "none"); svg.setAttribute("viewBox", vb.join(" ")); }
// ---------- the turn controller ----------
const controller = TURN.mount(stage, FIG.turn, { follow });
let shown = { spin: NaN, explode: NaN };
const pose = (spin, explode) => {
  if (spin === shown.spin && explode === shown.explode) return;
  controller.set({ spin, explode });
  shown = { spin, explode };
};

// bounding boxes in viewBox units
// boxes come from client rects, so every transform the runtime writes (translate on fixed parts) is included
let viewRect = null;
const unionBox = (nodes) => {
  const r = viewRect ?? view.getBoundingClientRect();
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const node of nodes) {
    const b = node.getBoundingClientRect();
    if (!b.width && !b.height) continue;
    x0 = Math.min(x0, b.left); y0 = Math.min(y0, b.top); x1 = Math.max(x1, b.right); y1 = Math.max(y1, b.bottom);
  }
  if (x0 === Infinity) return null;
  const sx = vb[2] / r.width;
  const sy = vb[3] / r.height;
  return [vb[0] + (x0 - r.left) * sx, vb[1] + (y0 - r.top) * sy, vb[0] + (x1 - r.left) * sx, vb[1] + (y1 - r.top) * sy];
};
const merge = (a, b) => (!a ? b : !b ? a : [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])]);
const allLive = [...nodesByName.values()];
const baseBox = back ? unionBox([...back.querySelectorAll("path")]) : null;
const FIT = [];
for (let i = 0; i <= 10; i++) {
  let box = baseBox;
  for (let a = 0; a < 360; a += 45) { pose(a, i / 10); box = merge(box, unionBox(allLive)); }
  FIT.push(box);
}
const fitAt = (x) => {
  const f = Math.min(10, Math.max(0, x * 10));
  const i = Math.min(9, Math.floor(f));
  const t = f - i;
  return FIT[i].map((v, j) => v + (FIT[i + 1][j] - v) * t);
};
const itemRect = (item, spin, explode) => {
  const keep = { ...shown };
  pose(spin, explode);
  let box = unionBox(item.nodes);
  pose(keep.spin, keep.explode);
  if (!box) return fitAt(explode);
  const minW = 70;
  const minH = 56;
  const cx = (box[0] + box[2]) / 2;
  const cy = (box[1] + box[3]) / 2;
  const w = Math.max(minW, box[2] - box[0]);
  const h = Math.max(minH, box[3] - box[1]);
  box = [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2];
  return box;
};

// ---------- view (zoom by viewBox, so lines stay crisp) ----------
let VW = 1;
let VH = 1;
const measure = () => {
  const r = view.getBoundingClientRect();
  VW = Math.max(1, r.width);
  VH = Math.max(1, r.height);
  overlay.setAttribute("viewBox", `0 0 ${VW} ${VH}`);
};
new ResizeObserver(() => { measure(); kick(); }).observe(view);
measure();
const viewBoxFor = (rect, fill) => {
  const [x0, y0, x1, y1] = rect;
  const cx = (x0 + x1) / 2;
  const cy = (y0 + y1) / 2;
  let w = (x1 - x0) / fill;
  let h = (y1 - y0) / fill;
  if (w / h > VW / VH) h = (w * VH) / VW;
  else w = (h * VW) / VH;
  return [cx - w / 2, cy - h / 2, w, h];
};
const applyView = (rect, fill) => {
  vb = viewBoxFor(rect, fill);
  const text = vb.map((v) => v.toFixed(2)).join(" ");
  for (const svg of svgs) if (svg.getAttribute("viewBox") !== text) svg.setAttribute("viewBox", text);
};
const toScreen = ([x, y]) => [((x - vb[0]) / vb[2]) * VW, ((y - vb[1]) / vb[3]) * VH];

// ---------- language and theme ----------
const LANGS = ["both", "fa", "en"];
let lang = LANGS.includes(store.get("sgm-lang")) ? store.get("sgm-lang") : "both";
const setLang = (next) => {
  lang = next;
  root.dataset.lang = lang;
  root.setAttribute("dir", lang === "fa" ? "rtl" : "ltr");
  root.setAttribute("lang", lang === "en" ? "en" : "fa");
  document.querySelectorAll("[data-set-lang]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.setLang === lang)));
  store.set("sgm-lang", lang);
  renderCard();
  kick();
};
const themeOf = () => store.get("sgm-theme") ?? (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
const setTheme = (theme) => {
  root.dataset.theme = theme;
  view.dataset.theme = theme;
  document.querySelector("[data-toggle-theme]")?.setAttribute("aria-pressed", String(theme === "dark"));
};
setTheme(themeOf());

// ---------- the part list ----------
const bi = (en, fa, tag = "span") => `<${tag} class="en" lang="en" dir="ltr">${en}</${tag}><${tag} class="fa" lang="fa" dir="rtl">${fa}</${tag}>`;
list.innerHTML = SECTIONS.map((sec) => {
  const items = ITEMS.filter((item) => item.sec === sec.id);
  return `<section class="sgm-sec" data-sec="${sec.id}"><h3>${bi(sec.en, sec.fa)}</h3><ol>${items.map((item) => `<li><button type="button" data-pick="${item.id}"><span class="num">${two(item.n)}</span><span class="nm">${bi(item.en.name, item.fa.name)}</span></button></li>`).join("")}</ol></section>`;
}).join("");

// ---------- state ----------
const S = {
  spin: -28, explode: 0, rect: fitAt(0), fill: 0.9, focus: 0, // shown values
  tSpin: -28, tExplode: 0, tRect: fitAt(0), tFill: 0.9, tFocus: 0, // targets
  sel: null, auto: !still.matches, timeline: null, clock: 0,
};
let idleTimer = 0;
const hold = () => {
  S.auto = false;
  clearTimeout(idleTimer);
  if (!S.timeline) idleTimer = setTimeout(() => { if (!S.sel) { S.auto = !still.matches; kick(); } }, 6000);
};

const select = (id, { fromTour = false } = {}) => {
  const item = id ? itemById.get(id) : null;
  S.sel = item ? item.id : null;
  for (const node of live.querySelectorAll("[data-on]")) node.removeAttribute("data-on");
  if (item) for (const node of item.nodes) node.setAttribute("data-on", "");
  view.toggleAttribute("data-focus", Boolean(item));
  list.querySelectorAll("[data-pick]").forEach((b) => b.setAttribute("aria-current", String(b.dataset.pick === S.sel)));
  if (item && !fromTour) {
    S.tExplode = Math.max(item.x, Math.min(S.tExplode, 1));
    if (item.x >= 0.99) S.tExplode = 1;
    S.tSpin = nearestAngle(S.spin, item.spin);
    S.tRect = itemRect(item, S.tSpin, S.tExplode);
    S.tFill = 0.62;
    S.tFocus = 1;
    slider.value = String(Math.round(S.tExplode * 100));
    // scroll the list itself, never the page (on a phone the list is part of the page and the figure must stay in view)
    const li = list.querySelector(`[data-pick="${item.id}"]`);
    if (li && list.scrollHeight > list.clientHeight + 4) list.scrollTo({ top: li.offsetTop - list.clientHeight / 2, behavior: still.matches ? "auto" : "smooth" });
  }
  if (!item && !fromTour) { S.tRect = fitAt(S.tExplode); S.tFill = 0.9; S.tFocus = 0; }
  renderCard();
  if (item) announce.textContent = lang === "en" ? item.en.name : item.fa.name;
  kick();
};
const nearestAngle = (from, to) => from + ((((to - from) % 360) + 540) % 360) - 180;
const step = (d) => {
  const i = S.sel ? ITEMS.findIndex((item) => item.id === S.sel) : -1;
  const next = ITEMS[(i + d + ITEMS.length) % ITEMS.length];
  select(next.id);
};

function renderCard() {
  const item = S.sel ? itemById.get(S.sel) : null;
  const stack = (en, fa, tag = "span", cls = "") => `<div class="stack ${cls}">${bi(en, fa, tag)}</div>`;
  if (!item) {
    card.innerHTML = `<p class="kicker">${bi(UI.overviewKicker.en, UI.overviewKicker.fa)}</p><h2 class="stack">${bi(UI.overviewTitle.en, UI.overviewTitle.fa)}</h2>${stack(UI.overviewBody.en, UI.overviewBody.fa, "p", "body")}${stack(UI.hint.en, UI.hint.fa, "span", "hint")}`;
    return;
  }
  const sec = SECTIONS.find((s) => s.id === item.sec);
  const facts = item.facts.map((f) => `<li class="stack">${bi(f.en, f.fa)}</li>`).join("");
  card.innerHTML = `<p class="kicker"><span class="badge">${two(item.n)} / ${ITEMS.length}</span>${bi(sec.en, sec.fa)}</p><h2 class="stack">${bi(item.en.name, item.fa.name)}</h2>${stack(item.en.does, item.fa.does, "p", "body")}${facts ? `<ul class="facts">${facts}</ul>` : ""}${item.sec === "meter" ? stack(sec.noteEn, sec.noteFa, "span", "note") : ""}`;
}

// ---------- tour timeline (also drives the video capture) ----------
const ease = (t) => (t <= 0 ? 0 : t >= 1 ? 1 : t * t * (3 - 2 * t));
const lerp = (a, b, t) => a + (b - a) * t;
const lerpRect = (a, b, t) => a.map((v, i) => lerp(v, b[i], t));
function buildTimeline(order = ITEMS.filter((i) => i.id !== "platter")) {
  const keys = [];
  let t = 0;
  const push = (dur, state) => { keys.push({ t, dur, ...state }); t += dur; };
  push(0, { spin: -60, explode: 0, rect: fitAt(0), fill: 0.9, focus: 0, sel: null, move: 0 });
  push(7, { spin: -24, explode: 0, rect: fitAt(0), fill: 0.9, focus: 0, sel: null, move: 7 });
  push(6.5, { spin: 10, explode: 1, rect: fitAt(1), fill: 0.9, focus: 0, sel: null, move: 5.5 });
  let spin = 10;
  for (const item of order) {
    const target = nearestAngle(spin, item.spin);
    spin = target;
    push(5.5, { spin: target, explode: 1, rect: itemRect(item, target, 1), fill: 0.62, focus: 1, sel: item.id, move: 1.4 });
  }
  push(5, { spin: spin + 40, explode: 1, rect: fitAt(1), fill: 0.9, focus: 0, sel: null, move: 2.2 });
  push(7, { spin: spin + 100, explode: 0, rect: fitAt(0), fill: 0.9, focus: 0, sel: null, move: 5.5 });
  return { keys, length: t };
}
// state at time t: each key moves from the previous key's values over `move` seconds, then holds
function timelineAt(tl, time) {
  const keys = tl.keys;
  let k = 0;
  while (k + 1 < keys.length && keys[k + 1].t <= time) k++;
  const cur = keys[k];
  const prev = keys[Math.max(0, k - 1)];
  const p = cur.move ? ease((time - cur.t) / cur.move) : 1;
  const linearSpin = k === 1 || k === keys.length - 1;
  const ps = linearSpin ? Math.min(1, Math.max(0, (time - cur.t) / cur.move)) : p;
  return {
    spin: lerp(prev.spin, cur.spin, ps),
    explode: lerp(prev.explode, cur.explode, p),
    rect: lerpRect(prev.rect, cur.rect, p),
    fill: lerp(prev.fill, cur.fill, p),
    focus: lerp(prev.focus, cur.focus, p),
    sel: cur.sel ?? (p < 0.5 ? prev.sel : null),
    selAge: time - cur.t,
  };
}

// ---------- frame ----------
let frame = 0;
let last = 0;
const drawFrame = () => {
  pose(S.spin, S.explode);
  applyView(S.rect, S.fill);
  view.style.setProperty("--focus", S.focus.toFixed(3));
  drawCallout();
  if (document.activeElement !== slider && !S.timeline) slider.value = String(Math.round(S.tExplode * 100));
};
function drawCallout() {
  const item = S.sel ? itemById.get(S.sel) : null;
  if (!item || S.focus < 0.4) { callout.hidden = true; overlay.innerHTML = ""; return; }
  const box = unionBox(item.nodes);
  if (!box) { callout.hidden = true; return; }
  const [ax, ay] = toScreen([box[2], box[1]]);
  const [bx, by] = toScreen([box[0], box[3]]);
  const pad = 10;
  const rightSpace = VW - ax;
  const cw = callout.offsetWidth || 220;
  const ch = callout.offsetHeight || 60;
  let lx = rightSpace > cw + 40 ? ax + 28 : Math.max(8, bx - cw - 28);
  let ly = Math.min(VH - ch - 8, Math.max(8, ay - ch - 18));
  callout.hidden = false;
  callout.style.transform = `translate(${lx.toFixed(1)}px, ${ly.toFixed(1)}px)`;
  callout.style.opacity = String(Math.min(1, (S.focus - 0.4) / 0.4));
  const anchorX = lx > ax ? lx : lx + cw;
  const anchorY = ly + ch / 2;
  const tx = lx > ax ? ax : bx;
  const ty = Math.min(Math.max(anchorY, ay), by);
  overlay.innerHTML = `<rect class="ring" x="${(Math.min(ax, bx) - pad).toFixed(1)}" y="${(ay - pad).toFixed(1)}" width="${(Math.abs(ax - bx) + 2 * pad).toFixed(1)}" height="${(by - ay + 2 * pad).toFixed(1)}" rx="8" opacity="${Math.min(1, (S.focus - 0.4) / 0.4).toFixed(2)}"/><path class="lead" d="M${anchorX.toFixed(1)} ${anchorY.toFixed(1)}L${tx.toFixed(1)} ${ty.toFixed(1)}" opacity="${Math.min(1, (S.focus - 0.4) / 0.4).toFixed(2)}"/><circle class="dot" cx="${tx.toFixed(1)}" cy="${ty.toFixed(1)}" r="3.2"/>`;
  if (callout.dataset.item !== item.id) {
    callout.dataset.item = item.id;
    callout.innerHTML = `<b>${two(item.n)}</b><span class="cn">${bi(item.en.name, item.fa.name)}</span>`;
  }
}

const follows = (cur, target, dt, tau) => (still.matches ? target : cur + (target - cur) * (1 - Math.exp(-dt / tau)));
function tick(now) {
  const dt = last ? Math.min((now - last) / 1000, 1 / 20) : 1 / 60;
  last = now;
  let moving = false;
  if (S.timeline) {
    S.clock += dt;
    if (S.clock > S.timeline.length) S.clock = 0;
    const st = timelineAt(S.timeline, S.clock);
    Object.assign(S, { spin: st.spin, explode: st.explode, rect: st.rect, fill: st.fill, focus: st.focus });
    if (st.sel !== S.sel) select(st.sel, { fromTour: true });
    moving = true;
  } else {
    if (S.auto && !S.sel) S.tSpin += dt * 7;
    const before = [S.spin, S.explode, S.fill, S.focus, ...S.rect];
    S.spin = follows(S.spin, S.tSpin, dt, 0.22);
    S.explode = follows(S.explode, S.tExplode, dt, 0.38);
    S.fill = follows(S.fill, S.tFill, dt, 0.4);
    S.focus = follows(S.focus, S.tFocus, dt, 0.3);
    if (!S.sel) S.tRect = fitAt(S.tExplode);
    S.rect = S.rect.map((v, i) => follows(v, S.tRect[i], dt, 0.42));
    const after = [S.spin, S.explode, S.fill, S.focus, ...S.rect];
    moving = S.auto || after.some((v, i) => Math.abs(v - before[i]) > 1e-3);
    if (!moving) { S.spin = S.tSpin; S.explode = S.tExplode; }
  }
  drawFrame();
  frame = moving && visible ? requestAnimationFrame(tick) : 0;
}
let visible = true;
function kick() { if (!frame) { last = 0; frame = requestAnimationFrame(tick); } }
new IntersectionObserver((entries) => { visible = entries[entries.length - 1].isIntersecting; if (visible) kick(); }, { rootMargin: "120px 0px" }).observe(view);

// ---------- input ----------
let drag = null;
view.addEventListener("pointerdown", (e) => {
  if (S.timeline) stopTour();
  drag = { x: e.clientX, y: e.clientY, spin: S.tSpin, moved: false, id: e.pointerId };
  hold();
});
view.addEventListener("pointermove", (e) => {
  if (drag && e.pointerId === drag.id) {
    const dx = e.clientX - drag.x;
    if (!drag.moved && Math.abs(dx) > 4) { drag.moved = true; view.setPointerCapture(e.pointerId); }
    if (drag.moved) { S.tSpin = drag.spin - dx * 0.45; kick(); }
    return;
  }
  const name = e.target.closest?.("[data-name]")?.getAttribute("data-name");
  const item = name ? itemOfName.get(name) : null;
  view.style.cursor = item ? "pointer" : "grab";
  const hover = view.querySelector("[data-hover]");
  if (hover && hover.dataset.item !== item?.id) for (const n of live.querySelectorAll("[data-hover]")) n.removeAttribute("data-hover");
  if (item && !item.nodes[0].hasAttribute("data-hover")) for (const n of item.nodes) n.setAttribute("data-hover", "");
});
view.addEventListener("pointerleave", () => { for (const n of live.querySelectorAll("[data-hover]")) n.removeAttribute("data-hover"); });
const endDrag = (e) => {
  if (!drag || e.pointerId !== drag.id) return;
  if (!drag.moved) {
    const name = e.target.closest?.("[data-name]")?.getAttribute("data-name");
    const item = name ? itemOfName.get(name) : null;
    select(item && item.id !== S.sel ? item.id : null);
  }
  drag = null;
};
view.addEventListener("pointerup", endDrag);
view.addEventListener("pointercancel", () => (drag = null));
view.addEventListener("wheel", (e) => {
  e.preventDefault();
  hold();
  const k = Math.exp(Math.sign(e.deltaY) * 0.12);
  const r = view.getBoundingClientRect();
  const px = vb[0] + ((e.clientX - r.left) / VW) * vb[2];
  const py = vb[1] + ((e.clientY - r.top) / VH) * vb[3];
  const base = S.tRect;
  S.tRect = base.map((v, i) => (i % 2 === 0 ? px + (v - px) * k : py + (v - py) * k));
  if (!S.sel) S.auto = false;
  pinned = true;
  kick();
}, { passive: false });
let pinned = false;
view.addEventListener("dblclick", () => { select(null); pinned = false; S.tRect = fitAt(S.tExplode); });

slider.addEventListener("input", () => { if (S.timeline) stopTour(); hold(); S.tExplode = Number(slider.value) / 100; if (!S.sel) S.tRect = fitAt(S.tExplode); kick(); });
document.querySelectorAll("[data-spin]").forEach((b) => b.addEventListener("click", () => { if (S.timeline) stopTour(); hold(); S.tSpin += Number(b.dataset.spin); kick(); }));
document.querySelectorAll("[data-explode]").forEach((b) => b.addEventListener("click", () => { if (S.timeline) stopTour(); hold(); S.tExplode = Number(b.dataset.explode); if (!S.sel) S.tRect = fitAt(S.tExplode); kick(); }));
document.querySelector("[data-reset]")?.addEventListener("click", () => { stopTour(); select(null); S.tExplode = 0; S.tSpin = nearestAngle(S.spin, -28); S.tRect = fitAt(0); S.auto = !still.matches; kick(); });
document.querySelector("[data-prev]")?.addEventListener("click", () => { stopTour(); step(-1); });
document.querySelector("[data-next]")?.addEventListener("click", () => { stopTour(); step(1); });
document.querySelectorAll("[data-set-lang]").forEach((b) => b.addEventListener("click", () => setLang(b.dataset.setLang)));
document.querySelector("[data-toggle-theme]")?.addEventListener("click", () => { const next = root.dataset.theme === "dark" ? "light" : "dark"; store.set("sgm-theme", next); setTheme(next); });
list.addEventListener("click", (e) => { const b = e.target.closest("[data-pick]"); if (b) { stopTour(); select(b.dataset.pick === S.sel ? null : b.dataset.pick); } });
const tourButton = document.querySelector("[data-tour]");
function startTour() { select(null, { fromTour: true }); S.timeline = buildTimeline(); S.clock = 0; tourButton?.setAttribute("aria-pressed", "true"); kick(); }
function stopTour() {
  if (!S.timeline) return;
  S.timeline = null;
  tourButton?.setAttribute("aria-pressed", "false");
  Object.assign(S, { tSpin: S.spin, tExplode: S.explode, tRect: S.rect.slice(), tFill: S.fill, tFocus: S.focus });
  if (S.sel) select(S.sel);
}
tourButton?.addEventListener("click", () => (S.timeline ? stopTour() : startTour()));
document.addEventListener("keydown", (e) => {
  if (e.target.closest("input, textarea")) return;
  const k = e.key;
  if (k === "ArrowLeft" || k === "ArrowRight") { stopTour(); hold(); S.tSpin += (k === "ArrowLeft" ? 15 : -15) * (e.shiftKey ? 3 : 1); kick(); e.preventDefault(); }
  else if (k === "ArrowUp" || k === "ArrowDown") { stopTour(); hold(); S.tExplode = Math.min(1, Math.max(0, S.tExplode + (k === "ArrowUp" ? 0.1 : -0.1))); if (!S.sel) S.tRect = fitAt(S.tExplode); kick(); e.preventDefault(); }
  else if (k === "]" || k === "n") { stopTour(); step(1); }
  else if (k === "[" || k === "p") { stopTour(); step(-1); }
  else if (k === "Escape") { stopTour(); select(null); }
  else if (k === "l" || k === "L") setLang(LANGS[(LANGS.indexOf(lang) + 1) % LANGS.length]);
  else if (k === "t" || k === "T") (S.timeline ? stopTour() : startTour());
  else if (k === "f" || k === "F") document.fullscreenElement ? document.exitFullscreen?.() : document.documentElement.requestFullscreen?.().catch(() => {});
});

// ---------- capture hook: a deterministic frame at time t ----------
window.__sgm = {
  timeline: (order) => buildTimeline(order ? order.map((id) => itemById.get(id)) : undefined),
  render(tl, t, opts = {}) {
    S.timeline = null;
    S.auto = false;
    const st = timelineAt(tl, t);
    Object.assign(S, { spin: st.spin, explode: st.explode, rect: st.rect, fill: st.fill, focus: st.focus });
    if (st.sel !== S.sel) select(st.sel, { fromTour: true });
    if (opts.lang && opts.lang !== lang) setLang(opts.lang);
    drawFrame();
    return { sel: S.sel, selAge: st.selAge };
  },
  // a frozen pose for the printed sheets: the stage markup plus where every item sits (viewBox units)
  snapshot(spin, explode, fill = 0.96) {
    S.timeline = null;
    S.auto = false;
    select(null, { fromTour: true });
    view.style.setProperty("--focus", "0");
    pose(spin, explode);
    applyView(fitAt(explode), fill);
    callout.hidden = true;
    overlay.innerHTML = "";
    const boxes = {};
    const anchors = {};
    for (const item of ITEMS) {
      boxes[item.id] = unionBox(item.nodes);
      let best = null;
      let area = -1;
      for (const node of item.nodes) {
        const b = unionBox([node]);
        if (!b) continue;
        const a = (b[2] - b[0]) * (b[3] - b[1]);
        if (a > area) { area = a; best = b; }
      }
      anchors[item.id] = best ? [(best[0] + best[2]) / 2, (best[1] + best[3]) / 2] : null;
    }
    return { vb: vb.slice(), boxes, anchors, html: stage.innerHTML, w: VW, h: VH };
  },
  select, setLang, setTheme, items: ITEMS.map((i) => i.id), pose,
  state: () => ({ spin: S.spin, explode: S.explode, sel: S.sel }),
};

setLang(lang);
select(null);
drawFrame();
kick();
