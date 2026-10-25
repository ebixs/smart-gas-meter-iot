// Bilingual A4 sheets from the same model and notes as the live page: node print.mjs [--png]
// → sgm-exploded-sheets-a4.pdf (+ .html, and page PNGs with --png)
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { ITEMS, SECTIONS } from "./parts.mjs";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = join(HERE, "..", "media", "sgm-exploded-sheets-a4");
const argv = process.argv.slice(2);
const index = readFileSync(join(HERE, "index.html"), "utf8");
const pageCss = index.slice(index.indexOf("<style>") + 7, index.indexOf("</style>"));

const browser = await chromium.launch();
const live = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
await live.goto(pathToFileURL(join(HERE, "index.html")).href);
await live.evaluate(() => { __sgm.setTheme("light"); __sgm.setLang("both"); document.querySelector(".sgm-badge").remove(); });
// the figure box on the sheet is 182 × 150 mm; size the live view to that aspect before freezing
await live.evaluate(() => { const v = document.querySelector(".sgm-view"); v.style.position = "fixed"; v.style.left = "0"; v.style.top = "0"; v.style.width = "1092px"; v.style.height = "900px"; });
await live.waitForTimeout(400);
const apart = await live.evaluate(() => __sgm.snapshot(-28, 1, 0.97));
await live.evaluate(() => { const v = document.querySelector(".sgm-view"); v.style.width = "760px"; v.style.height = "760px"; });
await live.waitForTimeout(300);
const rest = await live.evaluate(() => __sgm.snapshot(-28, 0, 0.94));

const listed = ITEMS.filter((item) => item.id !== "platter");
const num = (i) => String(i).padStart(2, "0");
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");

// pins: start on each item's largest shape, push apart until none crowd, keep a hairline back to the point
function pins(snap, wmm, hmm) {
  const [vx, vy, vw, vh] = snap.vb;
  const sx = wmm / vw;
  const sy = hmm / vh;
  const ps = listed.map((item) => {
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
  const n = (item) => listed.indexOf(item) + 1;
  return `<svg class="pins" viewBox="0 0 ${wmm} ${hmm}" width="${wmm}mm" height="${hmm}mm">${ps.map((p) => {
    const lead = Math.hypot(p.x - p.ax, p.y - p.ay) > R ? `<path d="M${p.ax.toFixed(2)} ${p.ay.toFixed(2)}L${p.x.toFixed(2)} ${p.y.toFixed(2)}" class="lead"/><circle cx="${p.ax.toFixed(2)}" cy="${p.ay.toFixed(2)}" r="0.55" class="tip"/>` : "";
    return `${lead}<circle cx="${p.x.toFixed(2)}" cy="${p.y.toFixed(2)}" r="${R - 0.4}" class="pin"/><text x="${p.x.toFixed(2)}" y="${(p.y + 1.05).toFixed(2)}" class="pn">${num(n(p.item))}</text>`;
  }).join("")}</svg>`;
}
const figure = (snap, wmm, hmm, withPins) => `<div class="fig" style="width:${wmm}mm;height:${hmm}mm"><div class="sgm-view iso" data-theme="light" style="width:${wmm}mm;height:${hmm}mm">${snap.html.replace(/viewBox="[^"]*"/g, `viewBox="${snap.vb.join(" ")}"`)}</div>${withPins ? pins(snap, wmm, hmm) : ""}</div>`;

const head = (fa, en, sub) => `<header class="hd"><div class="mk"></div><div><h1><span class="fa">${fa}</span><span class="en">${en}</span></h1><p>${sub}</p></div><div class="tag"><span class="fa">نمونهٔ آزمایشگاهی · فقط پالس شبیه‌سازی‌شده</span><span class="en">Bench prototype · synthetic pulses only</span></div></header>`;
const foot = (page) => `<footer class="ft"><span class="fa">هرگز به کنتور، لولهٔ گاز یا برق شهرِ واقعی وصل نشود. سازوکار G4 عمومی و نمایشی است؛ محفظه مفهومی است.</span><span class="en">Never connect to a live gas meter, gas line or mains. G4 internals are generic; the enclosure is a concept.</span><span class="pg">github.com/ebixs/smart-gas-meter-iot · ${page}</span></footer>`;

const legend = SECTIONS.map((sec) => {
  const rows = listed.filter((i) => i.sec === sec.id).map((item) => `<li><b>${num(listed.indexOf(item) + 1)}</b><span class="fa">${item.fa.name}</span><span class="en">${esc(item.en.name)}</span></li>`).join("");
  return `<section><h3><span class="fa">${sec.fa}</span><span class="en">${sec.en}</span></h3><ol>${rows}</ol></section>`;
}).join("");

const STEPS = [
  { fa: "گاز دو محفظه را به نوبت پر و خالی می‌کند و دیافراگم‌ها با هر رفت‌وبرگشت، حجمی ثابت جابه‌جا می‌کنند.", en: "Gas fills and empties two chambers in turn; each diaphragm stroke moves a fixed volume." },
  { fa: "میله‌ها، بازوها و میل‌لنگ این حرکت را به چرخش تبدیل می‌کنند؛ میل‌لنگ سوپاپ‌ها و غلتک‌های شمارنده را با هم می‌چرخاند.", en: "Flag rods, links and the crank turn it into rotation that drives the valves and the index together." },
  { fa: "هر دور غلتک قرمز آخر ۰٫۰۱ مترمکعب است؛ آهنربای آن یک بار کلید رید را می‌بندد: یک پالس.", en: "One turn of the last red drum is 0.01 m³; its magnet closes the reed once: one pulse." },
  { fa: "فِرم‌ور بسته‌شدن‌های کوتاه‌تر از ۳۰ میلی‌ثانیه را نمی‌شمارد و شمارنده را در دو بخش فلش با CRC-32 نگه می‌دارد.", en: "Firmware ignores closures under 30 ms and keeps the count in two flash slots with CRC-32." },
  { fa: "ساعت ۰۰:۰۰ اولین روز هر فصل شمسی به وقت تهران، رکورد «بستن دوره» ساخته و ارسال می‌شود؛ پس از ۲۴ ساعت، پیامک پشتیبان.", en: "At 00:00 Tehran on the first day of each Jalali season a period-close record is sent; an SMS backs it up after 24 h." },
  { fa: "سرور مصرف را پیش‌بینی می‌کند، الگوهای غیرعادی را برای بررسی علامت می‌زند و فاکتور پلکانی با QR صادر می‌کند.", en: "The server forecasts use, flags unusual patterns for a look, and issues a tiered invoice with a QR check." },
];
const NUMBERS = [
  ["۰٫۰۱", "0.01 m³", "مترمکعب در هر پالس", "per pulse"],
  ["۳۰", "30 ms", "میلی‌ثانیه حذف لرزش", "debounce"],
  ["۰۰:۰۰", "00:00", "بستن فصل به وقت تهران", "season close, Tehran"],
  ["۲۴", "24 h", "ساعت تا پیامک پشتیبان", "to the SMS fallback"],
  ["۱۰+", "10+ yr", "سال عمر باتری (تخمین)", "battery, estimate"],
];

const tableRows = listed.map((item) => `<tr><td class="n">${num(listed.indexOf(item) + 1)}</td><td class="tfa"><b>${item.fa.name}</b><span>${item.fa.does}</span>${item.facts.length ? `<em>${item.facts.map((f) => f.fa).join(" · ")}</em>` : ""}</td><td class="ten"><b>${esc(item.en.name)}</b><span>${esc(item.en.does)}</span>${item.facts.length ? `<em>${item.facts.map((f) => esc(f.en)).join(" · ")}</em>` : ""}</td></tr>`);
const per = 6;
const tables = [];
for (let i = 0; i < tableRows.length; i += per) tables.push(tableRows.slice(i, i + per).join(""));

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
.hd .tag{margin-inline-start:auto;text-align:end;display:flex;flex-direction:column;font:600 7.5pt/1.4 "Plex Mono";color:var(--mute);text-transform:uppercase;letter-spacing:.05em}
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
.how{display:grid;grid-template-columns:118mm 1fr;gap:7mm;flex:1;min-height:0}
.steps{display:grid;grid-template-columns:1fr 1fr;gap:3mm 5mm;align-content:start}
.step{border-top:.3mm solid var(--ink);padding-top:1.6mm}
.step i{font:700 8pt "Plex Mono";font-style:normal;color:var(--mute)}
.step .fa{display:block;font:400 9pt/1.7 "Vazir","Plex Sans";margin:.6mm 0}
.step .en{display:block;font-size:8pt;color:var(--mute)}
.nums{display:grid;grid-template-columns:repeat(5,1fr);gap:3mm;margin-top:3mm}
.nums div{border-top:.6mm solid var(--gas);padding-top:1.5mm}
.nums b{display:block;font:800 15pt/1.1 "Bricolage","Plex Sans"}
.nums .fa{display:block;font:700 7.6pt/1.4 "Vazir","Plex Sans"}
.nums .en{display:block;font-size:7pt;color:var(--mute)}
.lede{display:grid;gap:1.5mm;margin-bottom:3mm}
.lede .fa{font:400 10pt/1.8 "Vazir","Plex Sans"}
.lede .en{font-size:8.6pt;color:var(--mute)}
table{width:100%;border-collapse:collapse;font-size:8pt}
th{font:600 6.8pt "Plex Mono";text-transform:uppercase;letter-spacing:.05em;color:var(--mute);text-align:start;border-bottom:.3mm solid var(--ink);padding:1mm 2mm}
th.fa{font:700 8pt "Vazir","Plex Sans";text-align:right;text-transform:none;letter-spacing:0;color:var(--ink)}
td{vertical-align:top;padding:1.8mm 2mm;border-bottom:.15mm solid var(--rule)}
td.n{font:600 8pt "Plex Mono";width:8mm}
td b{display:block;font-weight:600;margin-bottom:.5mm}
td em{display:block;font-style:normal;margin-top:.8mm;color:var(--mute);font-size:7.2pt}
td.tfa{direction:rtl;font-family:"Vazir","Plex Sans";width:52%;line-height:1.7}
td.tfa b{font-weight:700;font-size:9pt}
td.ten{line-height:1.45;color:#2d3237}
.inset-label{font:600 6.8pt "Plex Mono";color:var(--mute);text-transform:uppercase;letter-spacing:.05em;margin-top:1mm;display:flex;justify-content:space-between}
.inset-label .fa{font:700 7.6pt "Vazir","Plex Sans";text-transform:none}
`;

const pages = [];
pages.push(`<div class="sheet">${head("کنتور هوشمند گاز — نمای انفجاری", "Smart Gas Meter — exploded", "همهٔ قطعه‌ها و نامشان · Every part and its name")}<div class="body">${figure(apart, 168, 152, true)}<div class="legend">${legend}</div></div>${foot("1")}</div>`);
pages.push(`<div class="sheet">${head("چگونه کار می‌کند", "How it works", "از گاز درون لوله تا عدد روی سرور · From gas in the pipe to a reading on the server")}<div class="how"><div>${figure(rest, 118, 118, false)}<div class="inset-label"><span>Assembled · bench prototype</span><span class="fa">سرهم‌شده · نمونهٔ آزمایشگاهی</span></div><div class="nums">${NUMBERS.map(([nfa, nen, lfa, len]) => `<div><b>${nen}</b><span class="fa">${lfa}</span><span class="en">${len}</span></div>`).join("")}</div></div><div><div class="lede"><span class="fa">کنتور دیافراگمی گاز را با پر و خالی کردن محفظه‌هایی با حجم ثابت می‌شمارد. دستگاه SGM کنار همان کنتور نصب می‌شود، هر ۱۰ لیتر را می‌شمارد، هر فصل را خودش می‌بندد و عدد را از طریق شبکهٔ موبایل می‌فرستد.</span><span class="en">A diaphragm meter counts gas by filling and emptying chambers of a fixed size. The SGM device sits beside that same meter, counts every 10 litres, closes each season on its own and sends the reading over the mobile network.</span></div><div class="steps">${STEPS.map((s, i) => `<div class="step"><i>0${i + 1}</i><span class="fa">${s.fa}</span><span class="en">${s.en}</span></div>`).join("")}</div></div></div>${foot("2")}</div>`);
tables.forEach((rows, i) => pages.push(`<div class="sheet">${head("قطعه‌ها و کارکردشان", "Parts and what they do", `${i + 1} / ${tables.length}`)}<table><thead><tr><th>#</th><th class="fa">فارسی</th><th>English</th></tr></thead><tbody>${rows}</tbody></table><div style="flex:1"></div>${foot(String(i + 3))}</div>`));

const html = `<!doctype html><html lang="fa"><head><meta charset="utf-8"><title>SGM exploded sheets</title><style>${pageCss}\n${CSS}</style></head><body>${pages.join("")}</body></html>`;
writeFileSync(`${OUT}.html`, html);
const sheet = await browser.newPage({ viewport: { width: 1123, height: 794 } });
await sheet.goto(pathToFileURL(`${OUT}.html`).href);
await sheet.evaluate(() => document.fonts.ready);
const overflow = await sheet.evaluate(() => [...document.querySelectorAll(".sheet")].map((s, i) => (s.scrollHeight > s.clientHeight + 1 ? i + 1 : 0)).filter(Boolean));
await sheet.pdf({ path: `${OUT}.pdf`, width: "297mm", height: "210mm", printBackground: true, preferCSSPageSize: true });
if (argv.includes("--png")) {
  const n = await sheet.evaluate(() => document.querySelectorAll(".sheet").length);
  await sheet.setViewportSize({ width: 1123, height: 794 });
  for (let i = 0; i < n; i++) {
    const el = (await sheet.$$(".sheet"))[i];
    await el.screenshot({ path: `${OUT}-p${i + 1}.png` });
  }
}
await browser.close();
console.log(`wrote ${OUT}.pdf · ${pages.length} pages${overflow.length ? ` · OVERFLOW on pages ${overflow.join(", ")}` : ""}`);
if (overflow.length) process.exitCode = 1;
