// Writes one offline, bilingual exploded board page: node page.mjs <carrier|modem|blocks>  (→ <name>.html, self-contained)
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { out, stage, FIG, FOLLOW, k, strip, HERE, NAME, mod, ART_CSS } from "./build.mjs";

const { T } = mod.model;
const { ITEMS, SECTIONS, UI, META } = await import(`./parts-${NAME}.mjs`);

const FONTS = join(HERE, "..", "..", "..", "media", "film", "fonts");
const font = (family, file, weight) => `@font-face{font-family:"${family}";src:url(data:font/woff2;base64,${readFileSync(join(FONTS, file)).toString("base64")}) format("woff2");font-weight:${weight};font-display:block}`;
const FONT_CSS = [
  font("Vazir", "vazirmatn-arabic-400-normal.woff2", 400),
  font("Vazir", "vazirmatn-arabic-700-normal.woff2", 700),
  font("Plex Sans", "ibm-plex-sans-latin-400-normal.woff2", 400),
  font("Plex Sans", "ibm-plex-sans-latin-600-normal.woff2", 600),
  font("Plex Mono", "ibm-plex-mono-latin-400-normal.woff2", 400),
  font("Plex Mono", "ibm-plex-mono-latin-600-normal.woff2", 600),
  font("Bricolage", "bricolage-grotesque-latin-800-normal.woff2", 800),
].join("\n");

// every drawn part must belong to an item, so a click always explains something
const unmatched = T.parts.map((p) => p.name).filter((name) => !ITEMS.some((item) => item.match.some((m) => name.startsWith(m))));
if (unmatched.length) {
  console.error(`parts without an item: ${unmatched.join(", ")}`);
  process.exitCode = 1;
}

const bi = (en, fa, tag = "span") => `<${tag} class="en" lang="en" dir="ltr">${en}</${tag}><${tag} class="fa" lang="fa" dir="rtl">${fa}</${tag}>`;

const CSS = `
${FONT_CSS}
:root{--bg:#eceee8;--panel:#f7f8f4;--card:#ffffff;--ink:#15181b;--ink2:#454b52;--muted:#767c83;--line:#d9dcd4;--line2:#c3c7be;
  --accent:#2a78d6;--accent-ink:#ffffff;--gas:#f2b200;--gas-ink:#2a2100;--red:#c9352f;--stage:#f2f3ef;--glow:#ffffff;
  --sans:"Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--fa:"Vazir","Plex Sans",Tahoma,sans-serif;--mono:"Plex Mono",ui-monospace,Menlo,Consolas,monospace;--display:"Bricolage","Plex Sans",system-ui,sans-serif;
  color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0e1012;--panel:#14171a;--card:#1a1e22;--ink:#eceee9;--ink2:#c2c7cc;--muted:#8a9096;--line:#272b30;--line2:#363b41;--accent:#5b9cf0;--accent-ink:#0b1320;--stage:#121417;--glow:#1d2228;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0e1012;--panel:#14171a;--card:#1a1e22;--ink:#eceee9;--ink2:#c2c7cc;--muted:#8a9096;--line:#272b30;--line2:#363b41;--accent:#5b9cf0;--accent-ink:#0b1320;--stage:#121417;--glow:#1d2228;color-scheme:dark}
*{box-sizing:border-box}
[hidden]{display:none!important}
html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--ink);font:15px/1.55 var(--sans);-webkit-font-smoothing:antialiased}
.fa,[lang="fa"]{font-family:var(--fa)}
button{font:inherit;color:inherit}
.app{display:grid;grid-template-columns:minmax(0,1fr) minmax(320px,460px);grid-template-rows:auto minmax(0,1fr);height:100vh;height:100dvh;padding-left:max(0px,env(safe-area-inset-left,0px));padding-right:max(0px,env(safe-area-inset-right,0px))}
/* language display */
[data-lang="en"] .fa{display:none!important}
[data-lang="fa"] .en{display:none!important}
.bi{display:flex;flex-direction:column}
[data-lang="both"] .stack{display:flex;flex-direction:column;gap:.15em}
[data-lang="both"] .stack>.fa{order:-1}
[data-lang="both"] .stack>.en{font-size:.78em;color:var(--muted);font-weight:500}
[data-lang="both"] .inline>.en{margin-inline-start:.5em;color:var(--muted);font-size:.86em}
[data-lang="both"] .inline>.fa{order:-1}
/* header */
.bar{grid-column:1/-1;display:flex;align-items:center;gap:14px;padding:12px max(16px,env(safe-area-inset-right,0px)) 12px max(16px,env(safe-area-inset-left,0px));border-bottom:1px solid var(--line);background:var(--panel);min-width:0}
.mark{width:34px;height:34px;flex:none}
.title{min-width:0;flex:1}
.title h1{margin:0;font:800 19px/1.15 var(--display);letter-spacing:-.01em;display:flex;flex-wrap:wrap;gap:.1em .6em;align-items:baseline}
.title h1 .fa{font:700 19px/1.3 var(--fa)}
.title p{margin:2px 0 0;color:var(--muted);font-size:12.5px;display:flex;gap:.6em;flex-wrap:wrap}
.pages{display:flex;flex-wrap:wrap;gap:4px 14px;margin-top:4px;font-size:12.5px}
.pages a{color:var(--accent);text-decoration:none;display:inline-flex;gap:.4em}
.pages a[aria-current]{color:var(--ink);font-weight:600;text-decoration:underline;text-underline-offset:3px}
[data-lang="both"] .pages a .en{color:var(--muted)}
.tools{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.seg{display:inline-flex;border:1px solid var(--line2);border-radius:999px;padding:2px;background:var(--card)}
.seg button,.btn{border:0;background:none;padding:6px 12px;border-radius:999px;cursor:pointer;font-size:13px;white-space:nowrap}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--bg)}
.btn{border:1px solid var(--line2);background:var(--card);display:inline-flex;align-items:center;gap:6px}
.btn:hover,.seg button:hover{border-color:var(--ink2)}
.btn[aria-pressed="true"]{background:var(--gas);color:var(--gas-ink);border-color:var(--gas)}
.btn svg{width:14px;height:14px}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
/* figure */
.figure{position:relative;display:grid;grid-template-rows:minmax(0,1fr) auto;min-width:0;min-height:0;border-inline-end:1px solid var(--line)}
.sgm-view{position:relative;overflow:hidden;background:radial-gradient(120% 90% at 50% 40%,var(--glow) 0%,var(--stage) 60%);touch-action:pan-y;cursor:grab;user-select:none;-webkit-user-select:none;min-height:0}
.sgm-view.iso{--anatomy-page:var(--stage)}
.sgm-stage{position:absolute;inset:0}
.sgm-stage .iso-svg{position:absolute;inset:0;width:100%;height:100%}
.sgm-overlay{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
.sgm-overlay .ring{fill:none;stroke:var(--accent);stroke-width:1.5;stroke-dasharray:5 4}
.sgm-overlay .lead{stroke:var(--accent);stroke-width:1.5;fill:none}
.sgm-overlay .dot{fill:var(--accent)}
.sgm-callout{position:absolute;left:0;top:0;display:flex;gap:10px;align-items:center;padding:9px 14px 9px 10px;background:var(--card);border:1.5px solid var(--accent);border-radius:12px;box-shadow:0 8px 24px -10px #0005;pointer-events:none;max-width:min(320px,70%)}
.sgm-callout b{font:600 13px/1 var(--mono);background:var(--accent);color:var(--accent-ink);border-radius:7px;padding:6px 7px}
.sgm-callout .cn{display:flex;flex-direction:column;font-weight:600;font-size:15px;line-height:1.3}
[data-lang="both"] .sgm-callout .cn .fa{order:-1}
[data-lang="both"] .sgm-callout .cn .en{font-size:12px;color:var(--muted);font-weight:500}
.sgm-badge{position:absolute;inset-inline-start:14px;bottom:12px;font:500 11.5px/1.3 var(--mono);color:var(--muted);background:color-mix(in srgb,var(--card) 85%,transparent);border:1px solid var(--line);padding:5px 9px;border-radius:8px;display:flex;flex-direction:column;gap:2px;pointer-events:none;max-width:calc(100% - 28px)}
.sgm-badge .fa{font-family:var(--fa);font-size:12px}
/* figure highlight */
.sgm-view[data-focus] .iso-live [data-name]{opacity:calc(1 - .78 * var(--focus,1));transition:opacity .2s}
.sgm-view[data-focus] .iso-live [data-name][data-on]{opacity:1}
.sgm-view .iso-live [data-on] .iso-edge{stroke:var(--accent)!important;stroke-width:1.6}
.sgm-view .iso-live [data-hover]:not([data-on]) .iso-edge{stroke:var(--accent)!important}
/* paints for parts the kit has no material for */
.iso-live [data-name^="index.drum.5"],.iso-live [data-name^="index.drum.6"],.iso-live [data-name^="index.drum.7"]{--anatomy-paper:#a8312c;--anatomy-face:#c9352f;--anatomy-top:#e2564f;--anatomy-shade-0:#7d1f1b;--anatomy-shade-1:#982824;--anatomy-shade-2:#b3302b;--anatomy-shade-3:#cd3d36;--anatomy-hi:#3d0b09;--anatomy-mid:#6e1a16;--anatomy-lo:#8a2420;--anatomy-faint:#b3302b}
.iso-live [data-name^="index.drum.5"] .iso-face-text,.iso-live [data-name^="index.drum.6"] .iso-face-text,.iso-live [data-name^="index.drum.7"] .iso-face-text{fill:#fff6f4!important}
.iso-live [data-name="board.pcb"],.iso-live [data-name="modem.pcb"],.iso-live [data-name="board.esp32.pcb"]{--anatomy-paper:#1d5b3a;--anatomy-face:#24704a;--anatomy-top:#2f8a5c;--anatomy-shade-0:#123b26;--anatomy-shade-1:#174a30;--anatomy-shade-2:#1d5b3a;--anatomy-shade-3:#236b45;--anatomy-hi:#0b2416;--anatomy-mid:#5fae84;--anatomy-lo:#3c8a61;--anatomy-faint:#2f7a52}
.iso-live [data-name^="device.base"],.iso-live [data-name="lid.plate"]{--anatomy-shade-0:#d5d7cf;--anatomy-shade-1:#dfe1d9;--anatomy-shade-2:#e8eae2;--anatomy-shade-3:#f0f1ea}
.iso-live [data-name="lid.lightpipe"],.iso-live [data-name="board.led"]{--anatomy-lit-top:#7fe0a3;--anatomy-lit-shade:#3fbf74;--anatomy-face:#5fd18d}
.iso-live [data-name="pulser.reed"]{--anatomy-lit-top:#e8f3ff;--anatomy-lit-shade:#b9d6f2}
.iso-live [data-name="index.magnet"]{--anatomy-lit-top:#ff8f87;--anatomy-lit-shade:#e0453d;--anatomy-face:#e0453d}
.sgm-t{font-family:var(--mono);letter-spacing:.02em}
.sgm-fa{font-family:var(--fa)!important;letter-spacing:0!important}
/* controls */
.controls{display:flex;flex-wrap:wrap;gap:10px 14px;align-items:center;padding:10px max(16px,env(safe-area-inset-left,0px));border-top:1px solid var(--line);background:var(--panel)}
.range{display:flex;align-items:center;gap:10px;flex:1 1 260px;min-width:0;font-size:12.5px;color:var(--muted)}
.range input{flex:1;min-width:0;accent-color:var(--accent)}
.range label{display:flex;gap:.4em;white-space:nowrap}
/* panel */
.panel{display:grid;grid-template-rows:auto minmax(0,1fr);min-height:0;background:var(--panel)}
.sgm-card{padding:22px 24px 16px;border-bottom:1px solid var(--line);min-height:260px}
.sgm-card .kicker{margin:0 0 10px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;font:600 12px/1.3 var(--mono);color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.sgm-card .kicker .fa{text-transform:none;letter-spacing:0;font-size:13px}
.badge{background:var(--accent);color:var(--accent-ink);border-radius:6px;padding:3px 7px;letter-spacing:0}
.sgm-card h2{margin:0 0 12px;font:700 26px/1.2 var(--sans);letter-spacing:-.01em;display:flex;flex-direction:column;gap:2px;text-wrap:balance}
.sgm-card .stack{display:flex;flex-direction:column}
.sgm-card .stack.body{gap:6px;margin-bottom:10px}
.sgm-card .stack.body p{margin:0}
.sgm-card h2 .fa{font:700 27px/1.35 var(--fa)}
[data-lang="both"] .sgm-card h2 .fa{order:-1}
[data-lang="both"] .sgm-card h2 .en{font-size:17px;color:var(--muted);font-weight:600}
.sgm-card p{margin:0 0 10px;color:var(--ink2);max-width:60ch}
.sgm-card p.fa{font-size:16.5px;line-height:1.85}
[data-lang="both"] .sgm-card p.en{font-size:13.5px;color:var(--muted)}
[data-lang="both"] .sgm-card p.fa{order:-1}
.sgm-card .facts{list-style:none;padding:0;margin:4px 0 8px;display:flex;flex-wrap:wrap;gap:6px}
.sgm-card .facts li{border:1px solid var(--line2);border-radius:8px;padding:4px 9px;font-size:12.5px;display:flex;flex-direction:column;background:var(--card)}
.sgm-card .facts .en{font-family:var(--mono);font-size:11.5px}
[data-lang="both"] .sgm-card .facts .fa{order:-1}
[data-lang="both"] .sgm-card .facts .en{color:var(--muted)}
.sgm-card .note,.sgm-card .hint{font-size:12.5px;color:var(--muted);gap:2px;margin-top:6px}
.pager{display:flex;gap:8px;padding:10px 24px;border-bottom:1px solid var(--line)}
.pager .btn{flex:1;justify-content:center}
.sgm-list{overflow:auto;padding:6px 12px 20px;min-height:0;position:relative}
.sgm-sec h3{margin:14px 12px 6px;font:600 11.5px/1.3 var(--mono);text-transform:uppercase;letter-spacing:.08em;color:var(--muted);display:flex;gap:.6em;flex-wrap:wrap}
.sgm-sec h3 .fa{font:700 13px/1.3 var(--fa);text-transform:none;letter-spacing:0;color:var(--ink2)}
.sgm-sec ol{list-style:none;margin:0;padding:0;display:grid;gap:2px}
.sgm-sec button{display:flex;gap:10px;align-items:center;width:100%;text-align:start;padding:7px 10px;border:1px solid transparent;border-radius:9px;background:none;cursor:pointer}
.sgm-sec button:hover{background:var(--card);border-color:var(--line)}
.sgm-sec button[aria-current="true"]{background:var(--card);border-color:var(--accent);box-shadow:inset 3px 0 0 var(--accent)}
[dir="rtl"] .sgm-sec button[aria-current="true"]{box-shadow:inset -3px 0 0 var(--accent)}
.num{font:600 11.5px/1 var(--mono);color:var(--muted);min-width:22px}
.nm{display:flex;flex-direction:column;line-height:1.3}
[data-lang="both"] .nm .fa{order:-1;font-size:14.5px}
[data-lang="both"] .nm .en{font-size:12px;color:var(--muted)}
.truth{grid-column:1/-1;display:none}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
@media (max-width:980px){
  .app{grid-template-columns:minmax(0,1fr);grid-template-rows:auto auto auto;height:auto}
  .figure{border-inline-end:0}
  .sgm-view{height:68vh;min-height:380px}
  .panel{grid-template-rows:auto auto auto}
  .sgm-list{max-height:none}
  .title h1,.title h1 .fa{font-size:16px}
  .bar{flex-wrap:wrap}
  .title{flex:1 1 220px}
  .tools{width:100%;justify-content:flex-start}
  .sgm-badge{font-size:10px;bottom:8px;inset-inline-start:8px}
  .sgm-badge>span:nth-child(n+3){display:none}
}
@media (prefers-reduced-motion:reduce){.sgm-view[data-focus] .iso-live [data-name]{transition:none}}
/* capture mode: bigger type for video */
:root[data-capture] body{font-size:17px}
:root[data-capture] .app{grid-template-columns:minmax(0,1fr) 620px}
:root[data-capture] .sgm-card{padding:30px 34px 20px}
:root[data-capture] .sgm-callout .cn{font-size:19px}
:root[data-capture] [data-lang="both"] .sgm-callout .cn .en{font-size:14px}
:root[data-capture] .sgm-callout b{font-size:15px}
:root[data-capture] .sgm-card h2 .fa{font-size:34px}
:root[data-capture] .sgm-card h2{font-size:30px}
:root[data-capture] .sgm-card p.fa{font-size:20px}
:root[data-capture] .sgm-card p.en{font-size:16px}
`;

const PAGES = [
  ["carrier.html", "Carrier board", "بُرد حامل"],
  ["modem.html", "Modem board", "بُرد مودم"],
  ["blocks.html", "Block diagram", "نمودار بلوکی"],
  ["../schematic/index.html", "Schematics", "شماتیک‌ها"],
  ["../exploded/index.html", "Whole device", "کل دستگاه"],
];
const MARK = `<svg class="mark" viewBox="0 0 34 34" aria-hidden="true"><rect x="1" y="1" width="32" height="32" rx="9" fill="#f2b200"/><path d="M9 23V14a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v9" fill="none" stroke="#15181b" stroke-width="2.6" stroke-linecap="round"/><circle cx="17" cy="19" r="3.4" fill="#c9352f"/><path d="M6 23h22" stroke="#15181b" stroke-width="2.6" stroke-linecap="round"/></svg>`;
const ICON = {
  left: `<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M13 8a5 5 0 1 1-1.5-3.6M13 2v3h-3" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>`,
  right: `<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8a5 5 0 1 0 1.5-3.6M3 2v3h3" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>`,
  play: `<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M5 3l8 5-8 5z" fill="currentColor"/></svg>`,
  moon: `<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M13 9.5A5.5 5.5 0 0 1 6.5 3a5.5 5.5 0 1 0 6.5 6.5z" fill="currentColor"/></svg>`,
};

const body = `
<div class="app">
  <header class="bar">
    ${MARK}
    <div class="title">
      <h1>${bi(META.title.en, META.title.fa)}</h1>
      <p>${bi(META.subtitle.en, META.subtitle.fa)}</p>
      <nav class="pages" aria-label="Pages / صفحه‌ها">${PAGES.map(([file, en, fa]) => `<a href="${file}"${file === `${NAME}.html` ? ' aria-current="page"' : ""}>${bi(en, fa)}</a>`).join("")}</nav>
    </div>
    <div class="tools">
      <div class="seg" role="group" aria-label="Language / زبان">
        <button type="button" data-set-lang="both" aria-pressed="false">EN + فا</button>
        <button type="button" data-set-lang="fa" aria-pressed="false">فارسی</button>
        <button type="button" data-set-lang="en" aria-pressed="false">English</button>
      </div>
      <button type="button" class="btn" data-tour aria-pressed="false">${ICON.play}<span class="inline bi" style="flex-direction:row">${bi("Tour", "تور")}</span></button>
      <button type="button" class="btn" data-toggle-theme aria-pressed="false" aria-label="Dark theme">${ICON.moon}</button>
    </div>
  </header>
  <section class="figure">
    <div class="sgm-view iso" data-theme="light" role="group" aria-label="Exploded model. Drag to turn it, scroll to zoom, click a part to see its name and job.">
      ${stage}
      <svg class="sgm-overlay" aria-hidden="true"></svg>
      <div class="sgm-callout" hidden></div>
      <div class="sgm-badge">${META.badge.map((b) => bi(b.en, b.fa)).join("")}</div>
      <p class="sgm-live sr" aria-live="polite"></p>
    </div>
    <div class="controls">
      <button type="button" class="btn" data-spin="30" aria-label="Turn left">${ICON.left}</button>
      <button type="button" class="btn" data-spin="-30" aria-label="Turn right">${ICON.right}</button>
      <div class="range">
        <label for="sgm-explode" class="inline bi" style="flex-direction:row">${bi("Assembled", "بسته")}</label>
        <input id="sgm-explode" type="range" min="0" max="100" value="0" aria-label="Explode / باز کردن">
        <span class="inline bi" style="flex-direction:row">${bi("Apart", "باز")}</span>
      </div>
      <button type="button" class="btn" data-explode="1"><span class="inline bi" style="flex-direction:row">${bi("Explode", "باز کن")}</span></button>
      <button type="button" class="btn" data-explode="0"><span class="inline bi" style="flex-direction:row">${bi("Assemble", "ببند")}</span></button>
      <button type="button" class="btn" data-reset><span class="inline bi" style="flex-direction:row">${bi("Reset", "از نو")}</span></button>
    </div>
  </section>
  <aside class="panel">
    <div>
      <div class="sgm-card" aria-live="polite"></div>
      <div class="pager">
        <button type="button" class="btn" data-prev><span class="inline bi" style="flex-direction:row">${bi("← Previous", "قبلی")}</span></button>
        <button type="button" class="btn" data-next><span class="inline bi" style="flex-direction:row">${bi("Next →", "بعدی")}</span></button>
      </div>
    </div>
    <nav class="sgm-list" aria-label="Parts / قطعه‌ها"></nav>
  </aside>
</div>`;

const LIVE = readFileSync(join(HERE, "live.js"), "utf8")
  .replace("__FIG__", JSON.stringify(FIG))
  .replace("__ITEMS__", JSON.stringify(ITEMS))
  .replace("__SECTIONS__", JSON.stringify(SECTIONS))
  .replace("__UI__", JSON.stringify(UI))
  .replace("const follow = null;", FOLLOW);
const script = (strip("turn.mjs") + "\n" + LIVE).replace(/<\/(script)/gi, "<\\/$1");
const html = `<!doctype html>
<html lang="fa" dir="ltr" data-lang="both">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>${META.htmlTitle}</title>
<meta name="description" content="${META.description}">
<style>${k.ISO_CSS}${out.css}${CSS}${ART_CSS}</style>
</head>
<body>${body}
<script type="module">${script}</script>
</body>
</html>`;
writeFileSync(join(HERE, `${NAME}.html`), html);
console.log(`wrote ${NAME}.html · ${(html.length / 1024).toFixed(0)} KB · ${ITEMS.length} items · ${T.parts.length} parts`);
