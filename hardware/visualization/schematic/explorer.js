// Schematic explorer runtime. DATA (per sheet: nets with geometry, parts, notes), CROSS, BLOCKS and UI are injected.
const DATA = __DATA__;
const CROSS = __CROSS__;
const BLOCKS = __BLOCKS__;
const UI = __UI__;

const root = document.documentElement;
const view = document.querySelector(".view");
const card = document.querySelector(".card");
const list = document.querySelector(".list");
const search = document.querySelector(".search input");
const badge = document.querySelector(".badge");
const store = {
  get: (k) => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch { /* private window */ } },
};
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const bi = (en, fa, tag = "span") => `<${tag} class="en" lang="en" dir="ltr">${en}</${tag}><${tag} class="fa" lang="fa" dir="rtl">${fa}</${tag}>`;
const stack = (en, fa, tag = "p", cls = "") => `<div class="stack ${cls}">${bi(en, fa, tag)}</div>`;
const T = (key) => UI[key];
const named = (s) => Object.keys(s.nets).filter((n) => !n.startsWith("unconnected")).sort((a, b) => a.localeCompare(b, "en", { numeric: true }));
const natural = (a, b) => a.localeCompare(b, "en", { numeric: true });

const S = { sheet: null, sel: null, vb: {} };
const sheetOf = (id) => DATA.find((s) => s.id === id);
const svgOf = (id) => view.querySelector(`svg.sheet[data-for="${id}"]`);

// ---------- language and theme ----------
let lang = store.get("sgm-sch-lang") || "both";
const setLang = (l) => {
  lang = l;
  root.setAttribute("data-lang", l);
  root.setAttribute("dir", l === "fa" ? "rtl" : "ltr");
  for (const b of document.querySelectorAll("[data-set-lang]")) b.setAttribute("aria-pressed", String(b.dataset.setLang === l));
  store.set("sgm-sch-lang", l);
};
document.querySelectorAll("[data-set-lang]").forEach((b) => b.addEventListener("click", () => setLang(b.dataset.setLang)));
setLang(lang);
const themeBtn = document.querySelector("[data-toggle-theme]");
const dark = () => root.getAttribute("data-theme") === "dark" || (!root.hasAttribute("data-theme") && matchMedia("(prefers-color-scheme: dark)").matches);
themeBtn.addEventListener("click", () => { root.setAttribute("data-theme", dark() ? "light" : "dark"); themeBtn.setAttribute("aria-pressed", String(dark())); store.set("sgm-sch-theme", root.getAttribute("data-theme")); });
const savedTheme = store.get("sgm-sch-theme");
if (savedTheme) root.setAttribute("data-theme", savedTheme);

// ---------- geometry ----------
const segDist = (px, py, x1, y1, x2, y2) => {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const l2 = dx * dx + dy * dy || 1e-9;
  const t = Math.max(0, Math.min(1, ((px - x1) * dx + (py - y1) * dy) / l2));
  return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy));
};
// a label's text runs from its anchor along its angle; KiCad text ≈ 1.1 mm per character at 1.27 mm size
const labelSeg = (name, [x, y, a]) => {
  if (a === -1) return [x, y - 2.5, x, y + 2.5];
  const len = name.length * 1.1;
  const r = (a * Math.PI) / 180;
  return [x, y, x + Math.cos(r) * len, y - Math.sin(r) * len];
};
const netBox = (s, name) => {
  const n = s.nets[name];
  const xs = [];
  const ys = [];
  for (const w of n.wires) { xs.push(w[0], w[2]); ys.push(w[1], w[3]); }
  for (const p of n.pins) { xs.push(p[3]); ys.push(p[4]); }
  for (const l of n.labels) { const g = labelSeg(name, l); xs.push(g[0], g[2]); ys.push(g[1], g[3]); }
  return xs.length ? [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)] : null;
};
const hit = (s, x, y) => {
  let best = null;
  for (const name of named(s)) {
    const n = s.nets[name];
    let d = Infinity;
    for (const w of n.wires) d = Math.min(d, segDist(x, y, ...w));
    for (const p of n.pins) d = Math.min(d, Math.hypot(x - p[3], y - p[4]));
    for (const l of n.labels) { const g = labelSeg(name, l); d = Math.min(d, segDist(x, y, ...g) - 0.4); }
    if (d < 1.3 && (!best || d < best.d)) best = { type: "net", id: name, d };
  }
  if (best) return best;
  let part = null;
  for (const [ref, p] of Object.entries(s.parts)) {
    const [x0, y0, x1, y1] = p.box;
    if (x >= x0 - 1 && x <= x1 + 1 && y >= y0 - 1 && y <= y1 + 1) {
      const area = (x1 - x0) * (y1 - y0);
      if (!part || area < part.area) part = { type: "part", id: ref, area };
    }
  }
  return part;
};

// ---------- drawing ----------
const NS = "http://www.w3.org/2000/svg";
const drawNet = (g, s, name, strong) => {
  if (!name) { g.innerHTML = ""; return; }
  const n = s.nets[name];
  let out = "";
  for (const w of n.wires) out += `<line x1="${w[0]}" y1="${w[1]}" x2="${w[2]}" y2="${w[3]}"/>`;
  if (strong) {
    for (const p of n.pins) out += `<circle cx="${p[3]}" cy="${p[4]}" r="0.75"/>`;
    for (const l of n.labels) { const [x1, y1, x2, y2] = labelSeg(name, l); out += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" style="stroke-width:2.2;opacity:.28"/>`; }
  } else {
    for (const l of n.labels) { const [x1, y1, x2, y2] = labelSeg(name, l); out += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" style="stroke-width:2;opacity:.18"/>`; }
  }
  g.innerHTML = out;
};
const drawPart = (g, s, ref) => {
  if (!ref) { g.innerHTML = ""; return; }
  const [x0, y0, x1, y1] = s.parts[ref].box;
  g.innerHTML = `<rect x="${x0 - 1.2}" y="${y0 - 1.2}" width="${x1 - x0 + 2.4}" height="${y1 - y0 + 2.4}" rx="1"/>`;
};

// ---------- view box: pan and zoom ----------
const FULL = [0, 0, 420, 297];
const applyVb = () => { svgOf(S.sheet).setAttribute("viewBox", S.vb[S.sheet].join(" ")); };
const toSheet = (ev) => {
  const svg = svgOf(S.sheet);
  const pt = svg.createSVGPoint();
  pt.x = ev.clientX;
  pt.y = ev.clientY;
  return pt.matrixTransform(svg.getScreenCTM().inverse());
};
const zoomAt = (factor, cx, cy) => {
  const [x, y, w, h] = S.vb[S.sheet];
  const nw = Math.min(FULL[2] * 1.4, Math.max(18, w / factor));
  const nh = (nw * h) / w;
  S.vb[S.sheet] = [cx - ((cx - x) * nw) / w, cy - ((cy - y) * nh) / h, nw, nh];
  applyVb();
};
const fitTo = (box, minW = 70) => {
  if (!box) { S.vb[S.sheet] = FULL.slice(); applyVb(); return; }
  const r = view.getBoundingClientRect();
  let [x0, y0, x1, y1] = box;
  let w = Math.max(minW, (x1 - x0) * 1.35);
  let h = Math.max(minW * 0.6, (y1 - y0) * 1.35);
  if (w / h > r.width / r.height) h = (w * r.height) / r.width;
  else w = (h * r.width) / r.height;
  S.vb[S.sheet] = [(x0 + x1) / 2 - w / 2, (y0 + y1) / 2 - h / 2, w, h];
  applyVb();
};
view.addEventListener("wheel", (ev) => { ev.preventDefault(); const p = toSheet(ev); zoomAt(ev.deltaY < 0 ? 1.18 : 1 / 1.18, p.x, p.y); }, { passive: false });
const pointers = new Map();
let drag = null;
let moved = false;
view.addEventListener("pointerdown", (ev) => {
  if (ev.target.closest(".zoom")) return;
  view.setPointerCapture(ev.pointerId);
  pointers.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
  drag = { x: ev.clientX, y: ev.clientY, vb: S.vb[S.sheet].slice() };
  moved = false;
});
view.addEventListener("pointermove", (ev) => {
  if (pointers.has(ev.pointerId)) {
    const prev = pointers.get(ev.pointerId);
    pointers.set(ev.pointerId, { x: ev.clientX, y: ev.clientY });
    if (pointers.size === 2) {
      const [a, b] = [...pointers.values()];
      const other = [...pointers.entries()].find(([id]) => id !== ev.pointerId)[1];
      const d0 = Math.hypot(prev.x - other.x, prev.y - other.y);
      const d1 = Math.hypot(a.x - b.x, a.y - b.y);
      const mid = toSheet({ clientX: (a.x + b.x) / 2, clientY: (a.y + b.y) / 2 });
      if (d0 > 0) zoomAt(d1 / d0, mid.x, mid.y);
      moved = true;
      return;
    }
    if (drag) {
      const r = view.getBoundingClientRect();
      const [x, y, w, h] = drag.vb;
      const scale = Math.max(w / r.width, h / r.height);
      const dx = (ev.clientX - drag.x) * scale;
      const dy = (ev.clientY - drag.y) * scale;
      if (Math.abs(ev.clientX - drag.x) + Math.abs(ev.clientY - drag.y) > 4) { moved = true; view.classList.add("drag"); }
      if (moved) { S.vb[S.sheet] = [x - dx, y - dy, w, h]; applyVb(); }
    }
    return;
  }
  const p = toSheet(ev);
  const h = hit(sheetOf(S.sheet), p.x, p.y);
  const g = svgOf(S.sheet).querySelector(".hl-hover");
  drawNet(g, sheetOf(S.sheet), h && h.type === "net" && !(S.sel && S.sel.id === h.id) ? h.id : null, false);
  view.style.cursor = h ? "pointer" : "";
});
const end = (ev) => {
  pointers.delete(ev.pointerId);
  view.classList.remove("drag");
  if (drag && !moved && pointers.size === 0) {
    const p = toSheet(ev);
    const h = hit(sheetOf(S.sheet), p.x, p.y);
    select(h ? { type: h.type, id: h.id } : null, { fit: false });
  }
  if (pointers.size === 0) drag = null;
};
view.addEventListener("pointerup", end);
view.addEventListener("pointercancel", end);
document.querySelectorAll("[data-zoom]").forEach((b) => b.addEventListener("click", () => { const [x, y, w, h] = S.vb[S.sheet]; zoomAt(Number(b.dataset.zoom), x + w / 2, y + h / 2); }));
document.querySelector("[data-fit]").addEventListener("click", () => fitTo(null));

// ---------- cards and list ----------
const pinsOfPart = (s, ref) => {
  const out = [];
  for (const [name, n] of Object.entries(s.nets)) for (const p of n.pins) if (p[0] === ref) out.push({ pin: p[1], fn: p[2], net: name });
  return out.sort((a, b) => natural(a.pin, b.pin));
};
const renderCard = () => {
  const s = sheetOf(S.sheet);
  if (!S.sel) {
    card.innerHTML = `<p class="kicker">${bi(s.en, s.fa)}</p><h2 class="stack">${bi(T("introTitle")[0], T("introTitle")[1])}</h2>${stack(T("introBody")[0], T("introBody")[1])}`;
    return;
  }
  if (S.sel.type === "net") {
    const name = S.sel.id;
    const n = s.nets[name];
    const m = s.meanings[name];
    const chips = n.pins.slice().sort((a, b) => natural(a[0], b[0]) || natural(a[1], b[1])).map((p) => `<button type="button" class="chip" data-part="${esc(p[0])}">${esc(p[0])}·${esc(p[1])}${p[2] && p[2] !== p[1] ? `<small>${esc(p[2].replace(/^Pin_\d+$/, ""))}</small>` : ""}</button>`).join("");
    const other = DATA.find((o) => o.id !== s.id);
    const cross = CROSS.includes(name) && other.nets[name] ? `<div class="cross">${stack(T("cross")[0], T("cross")[1], "span")}<div class="chips"><button type="button" class="chip" data-go="${other.id}" data-net="${esc(name)}">${bi(`${T("show")[0]} → ${other.en}`, `${T("show")[1]} ← ${other.fa}`)}</button></div></div>` : "";
    card.innerHTML = `<p class="kicker">${bi(T("net")[0], T("net")[1])} · ${bi(s.en, s.fa)}</p><h2>${esc(name)}</h2>${m ? stack(m.en, m.fa) : ""}<p class="kicker" style="margin-top:12px">${bi(`${T("pins")[0]} (${n.pins.length})`, `${T("pins")[1]} (${n.pins.length})`)}</p><div class="chips">${chips}</div>${cross}`;
  } else {
    const ref = S.sel.id;
    const p = s.parts[ref];
    const item = s.items[ref];
    const blk = BLOCKS[p.block];
    const tp = ref.startsWith("TP");
    const pins = pinsOfPart(s, ref);
    const chips = pins.map((q) => `<button type="button" class="chip" data-net="${esc(q.net)}">${esc(q.pin)}${q.fn && q.fn !== q.pin && !/^Pin_\d+$/.test(q.fn) ? `<small>${esc(q.fn)}</small>` : ""} → ${esc(q.net.startsWith("unconnected") ? "NC" : q.net)}</button>`).join("");
    const mpn = [p.maker, p.mpn, p.lcsc && `LCSC ${p.lcsc}`].filter((v) => v && v !== "TBD" && v !== "generic").join(" · ") || (p.mpn === "generic" ? "generic" : "to select");
    card.innerHTML = `<p class="kicker">${bi(T("part")[0], T("part")[1])}${blk ? ` · ${bi(blk[0], blk[1])}` : ""}</p>
      <h2>${esc(ref)} · ${esc(p.value)}</h2>
      ${item ? stack(item.en.does, item.fa.does) : tp ? stack(`${T("tp")[0]} (${esc(p.value)})`, `${T("tp")[1]} (${esc(p.value)})`) : ""}
      ${item ? `<p class="kicker" style="margin-top:6px">${bi(item.en.name, item.fa.name)}</p>` : ""}
      <dl class="meta"><dt><span class="inline">${bi(T("mpn")[0], T("mpn")[1])}</span></dt><dd>${esc(mpn)}</dd><dt><span class="inline">${bi(T("fp")[0], T("fp")[1])}</span></dt><dd>${esc(p.footprint)}</dd></dl>
      ${p.note && p.note !== "-" ? `<div class="note"><b class="inline">${bi(T("design")[0], T("design")[1])}</b> <span lang="en" dir="ltr">${esc(p.note)}</span></div>` : ""}
      <div class="chips">${chips}</div>`;
  }
};
const renderList = () => {
  const s = sheetOf(S.sheet);
  const q = search.value.trim().toUpperCase();
  const nets = named(s).filter((n) => !q || n.toUpperCase().includes(q) || (s.meanings[n] && (s.meanings[n].en.toUpperCase().includes(q) || s.meanings[n].fa.includes(search.value.trim()))));
  const parts = Object.keys(s.parts).sort(natural).filter((r) => !q || r.toUpperCase().includes(q) || s.parts[r].value.toUpperCase().includes(q));
  const cur = (type, id) => (S.sel && S.sel.type === type && S.sel.id === id ? ' aria-current="true"' : "");
  list.innerHTML = `<h3 class="inline">${bi(`${T("nets")[0]} (${nets.length})`, `${T("nets")[1]} (${nets.length})`)}</h3>${nets.map((n) => `<button type="button" class="row" data-net="${esc(n)}"${cur("net", n)}><b>${esc(n)}</b><span>${s.nets[n].pins.length} ${lang === "fa" ? "پایه" : "pins"}</span></button>`).join("")}
    <h3 class="inline">${bi(`${T("parts")[0]} (${parts.length})`, `${T("parts")[1]} (${parts.length})`)}</h3>${parts.map((r) => `<button type="button" class="row" data-part="${esc(r)}"${cur("part", r)}><b>${esc(r)}</b><span>${esc(s.parts[r].value)}</span></button>`).join("")}`;
};
const select = (sel, { fit = true } = {}) => {
  S.sel = sel;
  const s = sheetOf(S.sheet);
  const svg = svgOf(S.sheet);
  drawNet(svg.querySelector(".hl-net"), s, sel && sel.type === "net" ? sel.id : null, true);
  drawPart(svg.querySelector(".hl-part"), s, sel && sel.type === "part" ? sel.id : null);
  svg.querySelector(".hl-hover").innerHTML = "";
  if (fit && sel) fitTo(sel.type === "net" ? netBox(s, sel.id) : s.parts[sel.id].box, sel.type === "net" ? 90 : 95);
  renderCard();
  renderList();
};
const showSheet = (id, sel = null) => {
  S.sheet = id;
  for (const svg of view.querySelectorAll("svg.sheet")) svg.toggleAttribute("hidden", svg.dataset.for !== id);
  for (const b of document.querySelectorAll("[data-sheet]")) b.setAttribute("aria-pressed", String(b.dataset.sheet === id));
  S.vb[id] = S.vb[id] ?? FULL.slice();
  applyVb();
  const s = sheetOf(id);
  badge.innerHTML = `${bi(s.rev, s.revFa)}${bi(T("badge")[0], T("badge")[1])}`;
  select(sel, { fit: Boolean(sel) });
  try { history.replaceState(null, "", `#${id}`); } catch { /* sandboxed */ }
};
document.querySelectorAll("[data-sheet]").forEach((b) => b.addEventListener("click", () => showSheet(b.dataset.sheet)));
document.addEventListener("click", (ev) => {
  const t = ev.target.closest("[data-net],[data-part]");
  if (!t || t.closest(".view")) return;
  if (t.dataset.go) { showSheet(t.dataset.go, { type: "net", id: t.dataset.net }); return; }
  if (t.dataset.net) select({ type: "net", id: t.dataset.net });
  else select({ type: "part", id: t.dataset.part });
});
search.addEventListener("input", renderList);
search.addEventListener("keydown", (ev) => {
  if (ev.key !== "Enter") return;
  const first = list.querySelector("[data-net],[data-part]");
  if (first) first.click();
});
document.addEventListener("keydown", (ev) => {
  if (ev.target.closest("input")) return;
  if (ev.key === "Escape") select(null, { fit: false });
  if (ev.key === "l" || ev.key === "L") setLang(lang === "both" ? "fa" : lang === "fa" ? "en" : "both");
});

const start = (location.hash || "").slice(1);
showSheet(DATA.some((s) => s.id === start) ? start : DATA[0].id);
window.__sch = { show: (sheet, type, id, fit = true) => { if (S.sheet !== sheet) showSheet(sheet); select(type ? { type, id } : null, { fit }); }, setLang, fitTo };
