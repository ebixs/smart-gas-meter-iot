// Bilingual A4 sheets for the boards: node print.mjs [--png]
// → ../media/sgm-boards-sheets-a4.pdf: for each board page (carrier, modem, block diagram) an exploded figure with
// numbered pins and a legend, then the parts table; then the two real schematics, full sheet.
// Each section is printed from its own live page (same model, same notes) and the sections are joined with pdfunite.
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = join(HERE, "..", "media", "sgm-boards-sheets-a4");
const argv = process.argv.slice(2);
const TMP = mkdtempSync(join(tmpdir(), "sgm-boards-print-"));
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
const num = (i) => String(i).padStart(2, "0");

const CSS = `
@page{size:A4 landscape;margin:0}
html,body{margin:0;background:#fff}
body{--ink:#15181b;--mute:#6b7177;--rule:#cfd2cb;--gas:#f2b200;color:var(--ink);font:9pt/1.45 "Plex Sans",sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.fa{font-family:"Vazir","Plex Sans",sans-serif;direction:rtl}
.sheet{width:297mm;height:210mm;box-sizing:border-box;padding:10mm 12mm 9mm;display:flex;flex-direction:column;gap:4mm;page-break-after:always;overflow:hidden;position:relative}
.hd{display:flex;align-items:center;gap:5mm;border-bottom:.3mm solid var(--ink);padding-bottom:3mm}
.mk{width:9mm;height:9mm;border-radius:2.4mm;background:var(--gas);flex:none}
.hd h1{margin:0;display:flex;gap:4mm;align-items:baseline;flex-wrap:wrap}
.hd h1 .fa{font:700 17pt/1.2 "Vazir","Plex Sans"}
.hd h1 .en{font:800 15pt/1.1 "Bricolage","Plex Sans";letter-spacing:-.01em}
.hd p{margin:1mm 0 0;color:var(--mute);font-size:8.5pt}
.hd .tag{margin-inline-start:auto;text-align:end;display:flex;flex-direction:column;font:600 7.5pt/1.4 "Plex Mono";color:var(--mute);text-transform:uppercase;letter-spacing:.05em;max-width:80mm}
.hd .tag .fa{text-transform:none;letter-spacing:0;font:700 8pt "Vazir","Plex Sans"}
.body{display:flex;gap:6mm;flex:1;min-height:0}
.fig{position:relative;flex:none}
.fig .sgm-view{position:absolute;inset:0;background:#fff;overflow:hidden}
.fig .sgm-stage{position:absolute;inset:0}
.fig .iso-svg{position:absolute;inset:0;width:100%;height:100%}
.pins{position:absolute;inset:0}
.pins .pin{fill:#15181b}
.pins .pn{fill:#fff;font:600 2.5px "Plex Mono";text-anchor:middle}
.pins .lead{stroke:#15181b;stroke-width:.18;fill:none}
.pins .tip{fill:#15181b}
.legend{flex:1;min-width:0;columns:2;column-gap:5mm;column-fill:auto;height:152mm;font-size:7.4pt}
.legend section{margin-bottom:2mm}
.legend h3{margin:0 0 1mm;display:flex;justify-content:space-between;gap:2mm;border-bottom:.2mm solid var(--rule);padding-bottom:.6mm;font:600 6.8pt/1.3 "Plex Mono";text-transform:uppercase;letter-spacing:.05em;color:var(--mute)}
.legend h3 .fa{font:700 7.6pt "Vazir","Plex Sans";color:var(--ink);text-transform:none;letter-spacing:0}
.legend ol{list-style:none;margin:0;padding:0}
.legend li{display:grid;grid-template-columns:6mm 1fr;column-gap:1.5mm;padding:.3mm 0;border-bottom:.1mm solid #eceee8;break-inside:avoid}
.legend li b{grid-row:span 2;font:600 6.6pt/1.55 "Plex Mono";background:#15181b;color:#fff;border-radius:1mm;text-align:center;height:3.6mm;align-self:center}
.legend li .fa{font:700 7.6pt/1.3 "Vazir","Plex Sans";text-align:start}
.legend li .en{color:var(--mute);font-size:6.6pt;line-height:1.2}
.ft{display:grid;grid-template-columns:1fr auto;gap:.5mm 6mm;border-top:.2mm solid var(--rule);padding-top:2mm;font-size:7pt;color:var(--mute)}
.ft .fa{font-family:"Vazir","Plex Sans";grid-column:1}
.ft .en{grid-column:1}
.ft .pg{grid-column:2;grid-row:1/3;align-self:center;font:600 7pt "Plex Mono"}
table{width:100%;border-collapse:collapse;font-size:8pt}
th{font:600 6.8pt "Plex Mono";text-transform:uppercase;letter-spacing:.05em;color:var(--mute);text-align:start;border-bottom:.3mm solid var(--ink);padding:1mm 2mm}
th.fa{font:700 8pt "Vazir","Plex Sans";text-align:right;text-transform:none;letter-spacing:0;color:var(--ink)}
td{vertical-align:top;padding:1.6mm 2mm;border-bottom:.15mm solid var(--rule)}
td.n{font:600 8pt "Plex Mono";width:8mm}
td b{display:block;font-weight:600;margin-bottom:.5mm}
td em{display:block;font-style:normal;margin-top:.8mm;color:var(--mute);font-size:7.2pt}
td.tfa{direction:rtl;font-family:"Vazir","Plex Sans";width:52%;line-height:1.65}
td.tfa b{font-weight:700;font-size:9pt}
td.ten{line-height:1.42;color:#2d3237}
.sch{flex:1;min-height:0;display:flex;align-items:center;justify-content:center}
.sch svg{width:273mm;height:auto;max-height:166mm}
`;
const head = (fa, en, sub, tagFa, tagEn) => `<header class="hd"><div class="mk"></div><div><h1><span class="fa">${fa}</span><span class="en">${en}</span></h1><p>${sub}</p></div><div class="tag"><span class="fa">${tagFa}</span><span class="en">${tagEn}</span></div></header>`;
const foot = (page) => `<footer class="ft"><span class="fa">فقط برای میز آزمایش؛ هرگز به کنتور، لولهٔ گاز یا برق شهرِ واقعی وصل نشود. هیچ‌کدام از این بُردها هنوز برای ساخت آزاد نشده است.</span><span class="en">Bench use only; never connect to a live gas meter, gas line or mains. Neither board is released for fabrication.</span><span class="pg">github.com/ebixs/smart-gas-meter-iot · ${page}</span></footer>`;

function pins(snap, listed, wmm, hmm) {
  const [vx, vy, vw, vh] = snap.vb;
  const sx = wmm / vw;
  const sy = hmm / vh;
  const ps = listed.filter((item) => snap.anchors[item.id]).map((item) => {
    const a = snap.anchors[item.id];
    const x = (a[0] - vx) * sx;
    const y = (a[1] - vy) * sy;
    return { item, ax: x, ay: y, x, y };
  });
  const R = 3.1;
  for (let it = 0; it < 400; it++) {
    let moved = false;
    for (let i = 0; i < ps.length; i++) for (let j = i + 1; j < ps.length; j++) {
      const a = ps[i];
      const b = ps[j];
      let dx = b.x - a.x;
      let dy = b.y - a.y;
      let d = Math.hypot(dx, dy);
      if (d < 2 * R + 0.6) {
        if (d < 1e-6) { dx = 1; dy = 0.3; d = 1; }
        const push = (2 * R + 0.6 - d) / 2;
        a.x -= (dx / d) * push; a.y -= (dy / d) * push;
        b.x += (dx / d) * push; b.y += (dy / d) * push;
        moved = true;
      }
    }
    for (const p of ps) { p.x = Math.min(wmm - R, Math.max(R, p.x)); p.y = Math.min(hmm - R, Math.max(R, p.y)); }
    if (!moved) break;
  }
  return `<svg class="pins" viewBox="0 0 ${wmm} ${hmm}" width="${wmm}mm" height="${hmm}mm">${ps.map((p) => {
    const lead = Math.hypot(p.x - p.ax, p.y - p.ay) > R ? `<path d="M${p.ax.toFixed(2)} ${p.ay.toFixed(2)}L${p.x.toFixed(2)} ${p.y.toFixed(2)}" class="lead"/><circle cx="${p.ax.toFixed(2)}" cy="${p.ay.toFixed(2)}" r="0.55" class="tip"/>` : "";
    return `${lead}<circle cx="${p.x.toFixed(2)}" cy="${p.y.toFixed(2)}" r="${R - 0.4}" class="pin"/><text x="${p.x.toFixed(2)}" y="${(p.y + 1.05).toFixed(2)}" class="pn">${num(listed.indexOf(p.item) + 1)}</text>`;
  }).join("")}</svg>`;
}
const figure = (snap, listed, wmm, hmm) => `<div class="fig" style="width:${wmm}mm;height:${hmm}mm"><div class="sgm-view iso" data-theme="light" style="width:${wmm}mm;height:${hmm}mm">${snap.html.replace(/viewBox="[^"]*"/g, `viewBox="${snap.vb.join(" ")}"`)}</div>${pins(snap, listed, wmm, hmm)}</div>`;

const browser = await chromium.launch();
const sections = [];
let pageNo = 1;
const MODELS = [
  { name: "carrier", spin: -28, sub: "100 × 70 mm · 4 layers · KiCad v0.2-rc1", tagFa: "طرح واقعی KiCad · هر لایه جدا", tagEn: "Real KiCad layout · every layer apart" },
  { name: "modem", spin: -28, sub: "75 × 50 mm · 4 layers · KiCad v0.1-draft · EC200U footprint provisional", tagFa: "طراحی تازه · ردپای EC200U موقت", tagEn: "New design · EC200U footprint provisional" },
  { name: "blocks", spin: 0, sub: "Carrier v0.2 + modem v0.1 · three voltage domains", tagFa: "جدا شده بر اساس حوزهٔ ولتاژ", tagEn: "Exploded by voltage domain" },
];
for (const m of MODELS) {
  const { ITEMS, SECTIONS, META } = await import(`./parts-${m.name}.mjs`);
  const file = join(HERE, `${m.name}.html`);
  const index = readFileSync(file, "utf8");
  const pageCss = index.slice(index.indexOf("<style>") + 7, index.indexOf("</style>"));
  const live = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
  await live.goto(pathToFileURL(file).href);
  await live.evaluate(() => { __sgm.setTheme("light"); __sgm.setLang("both"); document.querySelector(".sgm-badge").remove(); });
  await live.evaluate(() => { const v = document.querySelector(".sgm-view"); v.style.position = "fixed"; v.style.left = "0"; v.style.top = "0"; v.style.width = "1092px"; v.style.height = "900px"; });
  await live.waitForTimeout(400);
  const apart = await live.evaluate((spin) => __sgm.snapshot(spin, 1, 0.97), m.spin);
  await live.close();
  const listed = ITEMS;
  const legend = SECTIONS.map((sec) => {
    const rows = listed.filter((i) => i.sec === sec.id).map((item) => `<li><b>${num(listed.indexOf(item) + 1)}</b><span class="fa">${item.fa.name}</span><span class="en">${esc(item.en.name)}</span></li>`).join("");
    return rows ? `<section><h3><span class="fa">${sec.fa}</span><span class="en">${sec.en}</span></h3><ol>${rows}</ol></section>` : "";
  }).join("");
  const pages = [`<div class="sheet">${head(META.title.fa, META.title.en, m.sub, m.tagFa, m.tagEn)}<div class="body">${figure(apart, listed, 168, 152)}<div class="legend">${legend}</div></div>${foot(pageNo++)}</div>`];
  const rows = listed.map((item) => `<tr><td class="n">${num(listed.indexOf(item) + 1)}</td><td class="tfa"><b>${item.fa.name}</b><span>${item.fa.does}</span>${item.facts?.length ? `<em>${item.facts.map((f) => f.fa).join(" · ")}</em>` : ""}</td><td class="ten"><b>${esc(item.en.name)}</b><span>${esc(item.en.does)}</span>${item.facts?.length ? `<em>${item.facts.map((f) => esc(f.en)).join(" · ")}</em>` : ""}</td></tr>`);
  const per = 5;
  for (let i = 0; i < rows.length; i += per) pages.push(`<div class="sheet">${head(`${META.title.fa} — قطعه‌ها`, `${META.title.en.split(" — ")[0]} — parts`, `${Math.floor(i / per) + 1} / ${Math.ceil(rows.length / per)}`, m.tagFa, m.tagEn)}<table><thead><tr><th>#</th><th class="fa">فارسی</th><th>English</th></tr></thead><tbody>${rows.slice(i, i + per).join("")}</tbody></table><div style="flex:1"></div>${foot(pageNo++)}</div>`);
  sections.push({ name: m.name, html: `<!doctype html><html lang="fa"><head><meta charset="utf-8"><style>${pageCss}\n${CSS}</style></head><body>${pages.join("")}</body></html>` });
}

// schematics: the real KiCad sheets, one per page
const schIndex = readFileSync(join(HERE, "..", "schematic", "index.html"), "utf8");
const schCss = schIndex.slice(schIndex.indexOf("<style>") + 7, schIndex.indexOf("</style>"));
const sheetSvgs = [...schIndex.matchAll(/<svg class="sheet" data-for="(\w+)"[^>]*>([\s\S]*?)<g class="hl-part">/g)].map((m) => ({ id: m[1], paper: m[2] }));
const SCH = { carrier: ["شماتیک بُرد حامل نسخهٔ ۰٫۲", "Carrier board v0.2 — schematic", "KiCad 7 file · ERC-clean in CI with KiCad 9"], modem: ["شماتیک بُرد مودم نسخهٔ ۰٫۱", "Modem board v0.1 — schematic", "KiCad 7 file · EC200U footprint provisional"] };
const schPages = sheetSvgs.map((s) => `<div class="sheet">${head(SCH[s.id][0], SCH[s.id][1], SCH[s.id][2], "شماتیک واقعی KiCad", "Real KiCad schematic")}<div class="sch"><svg viewBox="0 0 420 297">${s.paper}</svg></div>${foot(pageNo++)}</div>`);
sections.push({ name: "schematics", html: `<!doctype html><html lang="fa"><head><meta charset="utf-8"><style>${schCss}\n${CSS}\nbody{height:auto;overflow:visible}</style></head><body>${schPages.join("")}</body></html>` });

const parts = [];
const overflow = [];
const sheet = await browser.newPage({ viewport: { width: 1123, height: 794 } });
let pngIndex = 1;
for (const s of sections) {
  const html = join(TMP, `${s.name}.html`);
  writeFileSync(html, s.html);
  await sheet.goto(pathToFileURL(html).href);
  await sheet.evaluate(() => document.fonts.ready);
  const over = await sheet.evaluate(() => [...document.querySelectorAll(".sheet")].map((x, i) => (x.scrollHeight > x.clientHeight + 1 ? i + 1 : 0)).filter(Boolean));
  if (over.length) overflow.push(`${s.name}: ${over.join(", ")}`);
  const pdf = join(TMP, `${s.name}.pdf`);
  await sheet.pdf({ path: pdf, width: "297mm", height: "210mm", printBackground: true, preferCSSPageSize: true });
  parts.push(pdf);
  if (argv.includes("--png")) {
    for (const el of await sheet.$$(".sheet")) await el.screenshot({ path: `${OUT}-p${pngIndex++}.png` });
  }
}
await browser.close();
execFileSync("pdfunite", [...parts, `${OUT}.pdf`]);
console.log(`wrote ${OUT}.pdf · ${pageNo - 1} pages${overflow.length ? ` · OVERFLOW ${overflow.join("; ")}` : ""}`);
if (overflow.length) process.exitCode = 1;
