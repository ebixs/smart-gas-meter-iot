// Builds the offline, bilingual schematic explorer: node build.mjs  (→ index.html, one self-contained file)
// Inputs: the real KiCad schematics exported to SVG (kicad-cli sch export svg), the net geometry from
// tools/sch_extract.py (data/*.json), net meanings (nets.mjs) and the part notes of the board pages.
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { NETS, CROSS, BLOCKS } from "./nets.mjs";
import * as carrierNotes from "../boards/parts-carrier.mjs";
import * as modemNotes from "../boards/parts-modem.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..", "..", "..");
const SHEETS = [
  { id: "carrier", sch: join(ROOT, "hardware/kicad/smart_gas_meter_iot.kicad_sch"), notes: carrierNotes, en: "Carrier board v0.2", fa: "بُرد حامل نسخهٔ ۰٫۲", rev: "v0.2-rc1 · schematic freeze candidate", revFa: "نسخهٔ 0.2-rc1 · نامزد انجماد شماتیک" },
  { id: "modem", sch: join(ROOT, "hardware/kicad-modem/sgm_modem.kicad_sch"), notes: modemNotes, en: "Modem board v0.1", fa: "بُرد مودم نسخهٔ ۰٫۱", rev: "v0.1-draft · EC200U footprint provisional", revFa: "نسخهٔ 0.1-draft · ردپای EC200U موقت" },
];

// KiCad SVG → compact markup: 2-decimal coordinates, no title/desc/doctype, empty groups dropped
const compact = (svg) => svg
  .replace(/<\?xml[^>]*>|<!DOCTYPE[^>]*>|<title>[\s\S]*?<\/title>|<desc>[\s\S]*?<\/desc>/g, "")
  .replace(/(\d+\.\d{2})\d+/g, "$1")
  .replace(/\.00(?=\D)/g, "")
  .replace(/<g[^>]*>\s*<\/g>/g, "")
  .replace(/\n\s*/g, "\n")
  .replace(/^[\s\S]*?<svg[^>]*>/, "")
  .replace(/<\/svg>\s*$/, "");

const tmp = mkdtempSync(join(tmpdir(), "sgm-sch-"));
const sheets = SHEETS.map((s) => {
  execFileSync("kicad-cli", ["sch", "export", "svg", "-o", tmp, s.sch], { stdio: "ignore" });
  const file = readdirSync(tmp).find((f) => f.startsWith(s.sch.split("/").pop().replace(".kicad_sch", "")) && f.endsWith(".svg"));
  const svg = compact(readFileSync(join(tmp, file), "utf8"));
  const data = JSON.parse(readFileSync(join(HERE, "data", `${s.id}.json`), "utf8"));
  // part notes: the board page item that names this reference
  const items = {};
  for (const item of s.notes.ITEMS) for (const m of item.match) {
    const ref = m.match(/^cmp\.([A-Z]+\d+)\.$/)?.[1];
    if (ref) items[ref] = { en: item.en, fa: item.fa, facts: item.facts };
  }
  return { id: s.id, en: s.en, fa: s.fa, rev: s.rev, revFa: s.revFa, svg, nets: data.nets, parts: data.parts, items, meanings: NETS[s.id] };
});

const FONTS = join(ROOT, "media", "film", "fonts");
const font = (family, file, weight) => `@font-face{font-family:"${family}";src:url(data:font/woff2;base64,${readFileSync(join(FONTS, file)).toString("base64")}) format("woff2");font-weight:${weight};font-display:swap}`;
const FONT_CSS = [
  font("Vazir", "vazirmatn-arabic-400-normal.woff2", 400), font("Vazir", "vazirmatn-arabic-700-normal.woff2", 700),
  font("Plex Sans", "ibm-plex-sans-latin-400-normal.woff2", 400), font("Plex Sans", "ibm-plex-sans-latin-600-normal.woff2", 600),
  font("Plex Mono", "ibm-plex-mono-latin-400-normal.woff2", 400), font("Plex Mono", "ibm-plex-mono-latin-600-normal.woff2", 600),
].join("\n");

const bi = (en, fa, tag = "span") => `<${tag} class="en" lang="en" dir="ltr">${en}</${tag}><${tag} class="fa" lang="fa" dir="rtl">${fa}</${tag}>`;
const CSS = `${FONT_CSS}
:root{--bg:#eceee8;--panel:#f7f8f4;--card:#ffffff;--ink:#15181b;--ink2:#454b52;--muted:#6f757c;--line:#d9dcd4;--line2:#c3c7be;
  --accent:#2a78d6;--accent-ink:#fff;--hl:#e8590c;--hl2:#2a78d6;--sheet:#f5f4ef;
  --sans:"Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--fa:"Vazir","Plex Sans",Tahoma,sans-serif;--mono:"Plex Mono",ui-monospace,Menlo,Consolas,monospace;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0e1012;--panel:#14171a;--card:#1a1e22;--ink:#eceee9;--ink2:#c2c7cc;--muted:#8a9096;--line:#272b30;--line2:#363b41;--accent:#5b9cf0;--accent-ink:#0b1320;--hl:#ff8a3d;--hl2:#6aa8ff;--sheet:#16191c;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0e1012;--panel:#14171a;--card:#1a1e22;--ink:#eceee9;--ink2:#c2c7cc;--muted:#8a9096;--line:#272b30;--line2:#363b41;--accent:#5b9cf0;--accent-ink:#0b1320;--hl:#ff8a3d;--hl2:#6aa8ff;--sheet:#16191c;color-scheme:dark}
*{box-sizing:border-box}[hidden]{display:none!important}
html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--ink);font:15px/1.55 var(--sans);-webkit-font-smoothing:antialiased}
.fa,[lang="fa"]{font-family:var(--fa)}
button,input{font:inherit;color:inherit}
[data-lang="en"] .fa{display:none!important}[data-lang="fa"] .en{display:none!important}
[data-lang="both"] .stack{display:flex;flex-direction:column;gap:.15em}
[data-lang="both"] .stack>.fa{order:-1}
[data-lang="both"] .stack>.en{font-size:.84em;color:var(--muted)}
[data-lang="both"] .inline>.en{margin-inline-start:.5em;color:var(--muted);font-size:.88em}
[data-lang="both"] .inline>.fa{order:-1}
.inline{display:inline-flex;flex-wrap:wrap;align-items:baseline}
.app{display:grid;grid-template-columns:minmax(0,1fr) minmax(320px,440px);grid-template-rows:auto minmax(0,1fr);height:100vh;height:100dvh}
.bar{grid-column:1/-1;display:flex;align-items:center;gap:14px;flex-wrap:wrap;padding-block:12px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));border-bottom:1px solid var(--line);background:var(--panel)}
.mark{width:34px;height:34px;flex:none}
.title{min-width:0;flex:1 1 260px}
.title h1{margin:0;font:700 19px/1.2 var(--sans);display:flex;flex-wrap:wrap;gap:.1em .6em;align-items:baseline}
.title h1 .fa{font:700 19px/1.3 var(--fa)}
.pages{display:flex;flex-wrap:wrap;gap:4px 14px;margin-top:4px;font-size:12.5px}
.pages a{color:var(--accent);text-decoration:none;display:inline-flex;gap:.4em}
.pages a[aria-current]{color:var(--ink);font-weight:600;text-decoration:underline;text-underline-offset:3px}
.tools{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.seg{display:inline-flex;border:1px solid var(--line2);border-radius:999px;padding:2px;background:var(--card)}
.seg button,.btn{border:0;background:none;padding:6px 12px;border-radius:999px;cursor:pointer;font-size:13px;white-space:nowrap}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--bg)}
.btn{border:1px solid var(--line2);background:var(--card);display:inline-flex;align-items:center;gap:6px}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.view{position:relative;min-width:0;min-height:0;overflow:hidden;background:var(--sheet);border-inline-end:1px solid var(--line);touch-action:none;cursor:grab}
.view.drag{cursor:grabbing}
.view svg.sheet{position:absolute;inset:0;width:100%;height:100%;display:block}
:root[data-theme="dark"] .paper{filter:invert(.9) hue-rotate(180deg)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .paper{filter:invert(.9) hue-rotate(180deg)}}
.hl-net line,.hl-net polyline{stroke:var(--hl);stroke-width:.9;stroke-linecap:round;fill:none;opacity:.85}
.hl-net circle{fill:var(--hl);opacity:.9}
.hl-net .lab{fill:none;stroke:var(--hl);stroke-width:.45}
.hl-hover line{stroke:var(--hl2);stroke-width:.7;stroke-linecap:round;opacity:.6}
.hl-part rect{fill:color-mix(in srgb,var(--hl2) 10%,transparent);stroke:var(--hl2);stroke-width:.45;stroke-dasharray:1.2 .8}
.zoom{position:absolute;inset-inline-end:12px;bottom:12px;display:flex;gap:6px}
.zoom .btn{padding:6px 10px;font-weight:600}
.badge{position:absolute;inset-inline-start:12px;bottom:12px;font:500 11.5px/1.35 var(--mono);color:var(--muted);background:color-mix(in srgb,var(--card) 88%,transparent);border:1px solid var(--line);padding:5px 9px;border-radius:8px;max-width:calc(100% - 140px);display:flex;flex-direction:column;gap:2px;pointer-events:none}
.badge .fa{font-family:var(--fa);font-size:12px}
.panel{display:grid;grid-template-rows:auto auto minmax(0,1fr);min-height:0;background:var(--panel)}
.search{padding:14px 16px 10px;border-bottom:1px solid var(--line)}
.search input{width:100%;padding:9px 12px;border:1px solid var(--line2);border-radius:10px;background:var(--card)}
.card{padding:16px 18px 14px;border-bottom:1px solid var(--line);max-height:58vh;overflow:auto}
.card .kicker{margin:0 0 8px;font:600 12px/1.3 var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.06em;display:flex;gap:8px;flex-wrap:wrap}
.card .kicker .fa{text-transform:none;letter-spacing:0;font-size:13px}
.card h2{margin:0 0 8px;font:700 22px/1.25 var(--sans);word-break:break-word}
.card h2 .fa{font:700 22px/1.4 var(--fa)}
.card p{margin:0 0 8px}
.card .meta{font:500 12.5px/1.5 var(--mono);color:var(--ink2);margin:0 0 10px;display:grid;grid-template-columns:auto 1fr;gap:2px 10px}
.card .meta dt{color:var(--muted)}.card .meta dd{margin:0;word-break:break-word}
.card .note{font-size:13px;color:var(--ink2);border-inline-start:3px solid var(--line2);padding-inline-start:10px;margin:8px 0}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 4px}
.chip{border:1px solid var(--line2);background:var(--card);border-radius:999px;padding:3px 10px;font:500 12.5px/1.4 var(--mono);cursor:pointer}
.chip:hover{border-color:var(--accent)}
.chip small{color:var(--muted);margin-inline-start:4px}
.cross{margin-top:10px;padding:9px 11px;border-radius:10px;background:color-mix(in srgb,var(--accent) 10%,var(--card));border:1px solid color-mix(in srgb,var(--accent) 40%,var(--line))}
.list{overflow:auto;padding:6px 8px 20px}
.list h3{margin:12px 10px 6px;font:600 12px/1.3 var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.row{display:flex;gap:10px;align-items:baseline;width:100%;text-align:start;border:0;background:none;padding:6px 10px;border-radius:8px;cursor:pointer}
.row:hover,.row[aria-current]{background:var(--card)}
.row b{font:600 13px/1.3 var(--mono);min-width:7.5em}
.row span{color:var(--ink2);font-size:13px;min-width:0}
@media (max-width:980px){.app{grid-template-columns:minmax(0,1fr);grid-template-rows:auto 62vh auto;height:auto}.view{border-inline-end:0;border-bottom:1px solid var(--line)}.card{max-height:none}.list{max-height:60vh}}
`;

const MARK = `<svg class="mark" viewBox="0 0 34 34" aria-hidden="true"><rect x="1" y="1" width="32" height="32" rx="9" fill="#f2b200"/><path d="M9 23V14a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v9" fill="none" stroke="#15181b" stroke-width="2.6" stroke-linecap="round"/><circle cx="17" cy="19" r="3.4" fill="#c9352f"/><path d="M6 23h22" stroke="#15181b" stroke-width="2.6" stroke-linecap="round"/></svg>`;
const PAGES = [["../boards/carrier.html", "Carrier board", "بُرد حامل"], ["../boards/modem.html", "Modem board", "بُرد مودم"], ["../boards/blocks.html", "Block diagram", "نمودار بلوکی"], ["index.html", "Schematics", "شماتیک‌ها"], ["../exploded/index.html", "Whole device", "کل دستگاه"]];

const body = `<div class="app">
<header class="bar">${MARK}
  <div class="title"><h1>${bi("Schematic explorer", "کاوشگر شماتیک")}</h1>
    <nav class="pages" aria-label="Pages / صفحه‌ها">${PAGES.map(([f, en, fa]) => `<a href="${f}"${f === "index.html" ? ' aria-current="page"' : ""}>${bi(en, fa)}</a>`).join("")}</nav></div>
  <div class="tools">
    <div class="seg" role="group" aria-label="Sheet / برگه">${sheets.map((s) => `<button type="button" data-sheet="${s.id}" aria-pressed="false">${bi(s.en, s.fa)}</button>`).join("")}</div>
    <div class="seg" role="group" aria-label="Language / زبان"><button type="button" data-set-lang="both" aria-pressed="false">EN + فا</button><button type="button" data-set-lang="fa" aria-pressed="false">فارسی</button><button type="button" data-set-lang="en" aria-pressed="false">English</button></div>
    <button type="button" class="btn" data-toggle-theme aria-label="Dark theme"><svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path d="M13 9.5A5.5 5.5 0 0 1 6.5 3a5.5 5.5 0 1 0 6.5 6.5z" fill="currentColor"/></svg></button>
  </div>
</header>
<section class="view" aria-label="Schematic. Drag to pan, scroll or pinch to zoom, click a wire, label or part.">
  ${sheets.map((s) => `<svg class="sheet" data-for="${s.id}" viewBox="0 0 420 297" preserveAspectRatio="xMidYMid meet" hidden><g class="paper">${s.svg}</g><g class="hl-part"></g><g class="hl-hover"></g><g class="hl-net"></g></svg>`).join("")}
  <div class="badge"></div>
  <div class="zoom"><button type="button" class="btn" data-zoom="1.4" aria-label="Zoom in">+</button><button type="button" class="btn" data-zoom="0.7" aria-label="Zoom out">−</button><button type="button" class="btn" data-fit aria-label="Fit">⤢</button></div>
</section>
<aside class="panel">
  <div class="search"><input type="search" placeholder="Net or part: GND, U1, MODEM_TXD… · جست‌وجوی نت یا قطعه" aria-label="Search nets and parts / جست‌وجو"></div>
  <div class="card" aria-live="polite"></div>
  <nav class="list" aria-label="Nets and parts / نت‌ها و قطعه‌ها"></nav>
</aside>
</div>`;

const UI = {
  introTitle: ["Click a wire, a label or a part", "روی یک سیم، برچسب یا قطعه کلیک کنید"],
  introBody: ["These are the real KiCad schematics of both boards. Every connection is a short wire ending in a net label, so clicking any of them lights up the whole net across the sheet and lists every pin it reaches. Click a part to see its value, its exact part number and what it does. The modem's J1 and the carrier's J6 carry the same seven nets: follow them from one board to the other.",
    "این‌ها شماتیک‌های واقعی KiCad هر دو بُرد هستند. هر اتصال یک سیم کوتاه است که به برچسب نت می‌رسد؛ پس کلیک روی هر کدام کل آن نت را در برگه روشن می‌کند و همهٔ پایه‌هایی را که به آن وصل‌اند فهرست می‌کند. روی هر قطعه کلیک کنید تا مقدار، شمارهٔ دقیق قطعه و کارش را ببینید. J1 بُرد مودم و J6 بُرد حامل هفت نت یکسان دارند: آن‌ها را از یک بُرد تا بُرد دیگر دنبال کنید."],
  nets: ["Nets", "نت‌ها"], parts: ["Parts", "قطعه‌ها"], net: ["Net", "نت"], part: ["Part", "قطعه"],
  pins: ["Connects", "وصل است به"], cross: ["Continues on the other board through the J6 ↔ J1 connector", "از طریق اتصال J6 ↔ J1 در بُرد دیگر ادامه دارد"], show: ["Show it there", "آنجا نشانم بده"],
  value: ["Value", "مقدار"], mpn: ["Part number", "شمارهٔ قطعه"], fp: ["Footprint", "ردپا"], block: ["Block", "بخش"], design: ["Design note", "یادداشت طراحی"],
  badge: ["Bench use only — never connect to a live gas meter, gas line or mains", "فقط برای میز آزمایش — هرگز به کنتور، لولهٔ گاز یا برق شهر وصل نشود"],
  tp: ["Test point: a bare copper pad for a probe.", "نقطهٔ آزمون: یک پد مسی برهنه برای پروب."],
};

const script = readFileSync(join(HERE, "explorer.js"), "utf8")
  .replace("__DATA__", JSON.stringify(sheets.map(({ svg, ...rest }) => rest)))
  .replace("__CROSS__", JSON.stringify(CROSS))
  .replace("__BLOCKS__", JSON.stringify(BLOCKS))
  .replace("__UI__", JSON.stringify(UI));
const html = `<!doctype html>
<html lang="fa" dir="ltr" data-lang="both">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>SGM Schematic Explorer</title>
<meta name="description" content="Interactive bilingual explorer for the real KiCad schematics of the Smart Gas Meter carrier board and EC200U modem board, with net tracing.">
<style>${CSS}</style>
</head>
<body>${body}
<script>${script.replace(/<\/(script)/gi, "<\\/$1")}</script>
</body>
</html>`;
writeFileSync(join(HERE, "index.html"), html);
console.log(`wrote schematic/index.html · ${(html.length / 1024).toFixed(0)} KB · ${sheets.map((s) => `${s.id}: ${Object.keys(s.parts).length} parts, ${Object.keys(s.nets).length} nets, svg ${(s.svg.length / 1024).toFixed(0)} KB`).join(" · ")}`);
