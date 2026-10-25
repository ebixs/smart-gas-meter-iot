// Builds the Persian explainer page (explainer.html), its timing and subtitles.
// node media/explainer/build.mjs        → uses audio/s01..s12 lengths when the recordings exist, estimates otherwise
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";
import { stage, FIG, FOLLOW, k, strip, out } from "../../hardware/visualization/exploded/build.mjs";
import { ITEMS } from "../../hardware/visualization/exploded/parts.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..", "..");
const plan = JSON.parse(readFileSync(join(HERE, "scenes.json"), "utf8"));
const LEAD = 0.6;
const TAIL = 1.0;

// ---------- timing: recorded lengths when present ----------
const audioOf = (id) => ["wav", "m4a", "mp3", "ogg", "aac", "flac"].map((ext) => join(HERE, "audio", `${id}.${ext}`)).find(existsSync);
const lengthOf = (file) => Number(execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", file]).toString().trim());
let t = 0;
const scenes = plan.scenes.map((s) => {
  const audio = audioOf(s.id);
  const narrDur = audio ? lengthOf(audio) : s.text.split(/\s+/).length / plan.wordsPerSecond;
  const dur = LEAD + narrDur + TAIL;
  const scene = { id: s.id, name: s.name, text: s.text, start: t, dur, narrStart: t + LEAD, narrDur, audio: audio ? audio.slice(HERE.length + 1) : null };
  t += dur;
  return scene;
});
const length = t;

// ---------- subtitles: sentences, split long ones at commas, timed by character share ----------
const chars = (s) => s.replace(/\s/g, "").length;
for (const s of scenes) {
  const parts = [];
  for (const sentence of s.text.split(/(?<=[.؛!؟:])\s+/)) {
    if (chars(sentence) <= 95) { parts.push(sentence); continue; }
    let buf = "";
    for (const piece of sentence.split(/(?<=،)\s+/)) {
      if (buf && chars(buf + piece) > 95) { parts.push(buf.trim()); buf = ""; }
      buf += (buf ? " " : "") + piece;
    }
    if (buf) parts.push(buf.trim());
  }
  const total = chars(s.text);
  let acc = 0;
  s.subs = parts.map((text) => {
    const a = s.narrStart + (acc / total) * s.narrDur;
    acc += chars(text);
    const b = s.narrStart + (acc / total) * s.narrDur;
    return { text, a, b: b + 0.25 };
  });
}
const pad = (n, w = 2) => String(Math.floor(n)).padStart(w, "0");
const srtTime = (x) => `${pad(x / 3600)}:${pad((x % 3600) / 60)}:${pad(x % 60)},${pad((x % 1) * 1000, 3)}`;
const srt = scenes.flatMap((s) => s.subs).map((seg, i) => `${i + 1}\n${srtTime(seg.a)} --> ${srtTime(seg.b)}\n${seg.text}\n`).join("\n");
writeFileSync(join(HERE, "explainer-fa.srt"), srt);
writeFileSync(join(HERE, "timing.json"), JSON.stringify({ length, scenes: scenes.map(({ subs, ...rest }) => rest) }, null, 2));

// ---------- data from the analytics sample (same as the launch film) ----------
const sandbox = { window: {} };
vm.runInNewContext(readFileSync(join(ROOT, "media", "film", "film-data.js"), "utf8"), sandbox);
const F = sandbox.window.FILM_DATA;
const FILM = { fleet: F.fleet, invoice: F.invoice, qr: F.qr };

// ---------- fonts ----------
const FONTS = join(ROOT, "media", "film", "fonts");
const font = (family, file, weight) => `@font-face{font-family:"${family}";src:url(data:font/woff2;base64,${readFileSync(join(FONTS, file)).toString("base64")}) format("woff2");font-weight:${weight};font-display:block}`;
const FONT_CSS = [
  font("Vazir", "vazirmatn-arabic-400-normal.woff2", 400), font("Vazir", "vazirmatn-arabic-700-normal.woff2", 700),
  font("Plex Sans", "ibm-plex-sans-latin-400-normal.woff2", 400), font("Plex Sans", "ibm-plex-sans-latin-600-normal.woff2", 600),
  font("Plex Mono", "ibm-plex-mono-latin-400-normal.woff2", 400), font("Plex Mono", "ibm-plex-mono-latin-600-normal.woff2", 600),
  font("Bricolage", "bricolage-grotesque-latin-800-normal.woff2", 800),
].join("\n");

const CSS = `
${FONT_CSS}
:root{--bg:#f2f3ef;--paper:#fbfbf8;--ink:#15181b;--ink2:#454b52;--muted:#767c83;--line:#dfe1db;--line2:#c9ccc4;--pipe:#f2b200;--blue:#2a78d6;--red:#c9352f;--serious:#ec835a;--good:#0a7d0a;--fa:"Vazir","Plex Sans",sans-serif}
*{box-sizing:border-box}
html,body{margin:0;width:1920px;height:1080px;overflow:hidden;background:var(--bg);color:var(--ink);font-family:var(--fa);-webkit-font-smoothing:antialiased}
body{direction:rtl}
.mono,.ltr{direction:ltr;font-family:"Plex Mono",monospace}
.scene{position:absolute;inset:0;opacity:0;visibility:hidden}
svg.full{position:absolute;inset:0;width:1920px;height:1080px;overflow:visible}
.fa-svg{font-family:var(--fa)}
.col{position:absolute;right:96px;top:120px;width:620px;display:flex;flex-direction:column;gap:22px;text-align:right}
.h{font:700 64px/1.25 var(--fa);margin:0;text-wrap:balance}
.k{font:700 28px/1.4 var(--fa);color:var(--muted)}
.lead{font:400 34px/1.7 var(--fa);color:var(--ink2);margin:0}
.big b{display:block;font:800 150px/1 "Bricolage",var(--fa);letter-spacing:-.02em}
.big span{font:700 32px/1.4 var(--fa);color:var(--ink2)}
.chip{display:inline-flex;align-self:flex-start;gap:14px;align-items:center;font:700 30px/1.3 var(--fa);background:var(--paper);border:2px solid var(--line2);border-radius:999px;padding:12px 26px}
.chip i{width:14px;height:14px;border-radius:50%;background:var(--pipe);display:inline-block;flex:none}
.src{position:absolute;left:96px;top:1000px;font:400 20px/1.4 var(--fa);color:var(--muted);direction:rtl}
.track{height:18px;border-radius:9px;background:#e3e5df;overflow:hidden}
.track div{height:100%;background:var(--pipe);transform-origin:right center;transform:scaleX(0)}
#modelbox{position:absolute;left:40px;top:96px;width:1150px;height:830px;opacity:0;visibility:hidden}
#model{position:absolute;inset:0;overflow:hidden;background:transparent;-webkit-mask-image:linear-gradient(to right,transparent 0,#000 60px,#000 calc(100% - 90px),transparent 100%),linear-gradient(to bottom,transparent 0,#000 50px,#000 calc(100% - 60px),transparent 100%);-webkit-mask-composite:source-in;mask-composite:intersect}
#model .sgm-stage{position:absolute;inset:0}
#model .iso-svg{position:absolute;inset:0;width:100%;height:100%}
#model[data-focus] .iso-live [data-name]{opacity:calc(1 - .8 * var(--focus,1))}
#model[data-focus] .iso-live [data-name][data-on]{opacity:1}
#model .iso-live [data-on] .iso-edge{stroke:var(--blue)!important;stroke-width:1.8}
.iso-live [data-name^="index.drum.5"],.iso-live [data-name^="index.drum.6"],.iso-live [data-name^="index.drum.7"]{--anatomy-paper:#a8312c;--anatomy-face:#c9352f;--anatomy-top:#e2564f;--anatomy-shade-0:#7d1f1b;--anatomy-shade-1:#982824;--anatomy-shade-2:#b3302b;--anatomy-shade-3:#cd3d36;--anatomy-hi:#3d0b09;--anatomy-mid:#6e1a16;--anatomy-lo:#8a2420;--anatomy-faint:#b3302b}
.iso-live [data-name^="index.drum.5"] .iso-face-text,.iso-live [data-name^="index.drum.6"] .iso-face-text,.iso-live [data-name^="index.drum.7"] .iso-face-text{fill:#fff6f4!important}
.iso-live [data-name="board.pcb"],.iso-live [data-name="modem.pcb"],.iso-live [data-name="board.esp32.pcb"]{--anatomy-paper:#1d5b3a;--anatomy-face:#24704a;--anatomy-top:#2f8a5c;--anatomy-shade-0:#123b26;--anatomy-shade-1:#174a30;--anatomy-shade-2:#1d5b3a;--anatomy-shade-3:#236b45;--anatomy-hi:#0b2416;--anatomy-mid:#5fae84;--anatomy-lo:#3c8a61;--anatomy-faint:#2f7a52}
.iso-live [data-name^="device.base"],.iso-live [data-name="lid.plate"]{--anatomy-shade-0:#d5d7cf;--anatomy-shade-1:#dfe1d9;--anatomy-shade-2:#e8eae2;--anatomy-shade-3:#f0f1ea}
.iso-live [data-name="lid.lightpipe"],.iso-live [data-name="board.led"]{--anatomy-lit-top:#7fe0a3;--anatomy-lit-shade:#3fbf74;--anatomy-face:#5fd18d}
.iso-live [data-name="pulser.reed"]{--anatomy-lit-top:#e8f3ff;--anatomy-lit-shade:#b9d6f2}
.iso-live [data-name="index.magnet"]{--anatomy-lit-top:#ff8f87;--anatomy-lit-shade:#e0453d;--anatomy-face:#e0453d}
.sgm-t{font-family:"Plex Mono",monospace;letter-spacing:.02em}
.sgm-fa{font-family:var(--fa)!important;letter-spacing:0!important}
#partcard{position:absolute;right:96px;top:120px;width:620px;background:var(--paper);border:2px solid var(--line);border-right:8px solid var(--blue);border-radius:20px;padding:28px 32px;box-shadow:0 24px 50px -26px #0004;opacity:0;visibility:hidden}
#partcard h3{margin:0;font:700 52px/1.25 var(--fa)}
#partcard small{display:block;direction:ltr;text-align:right;font:600 22px "Plex Sans";color:var(--muted);margin:4px 0 12px}
#partcard p{margin:0;font:400 29px/1.75 var(--fa);color:var(--ink2)}
#sub{position:absolute;left:50%;bottom:34px;transform:translateX(-50%);max-width:1560px;text-align:center;background:color-mix(in srgb,var(--ink) 88%,transparent);color:#fff;font:700 38px/1.6 var(--fa);padding:12px 34px 14px;border-radius:16px;opacity:0}
#brand{position:absolute;right:96px;top:40px;display:flex;gap:16px;align-items:center;font:700 26px var(--fa);color:var(--ink)}
#brand i{width:30px;height:30px;border-radius:9px;background:var(--pipe);display:inline-block}
#chapter{font:400 22px var(--fa);color:var(--muted);margin-right:14px}
#honest{position:absolute;left:96px;top:46px;font:400 21px var(--fa);color:var(--muted)}
#progress{position:absolute;left:0;right:0;bottom:0;height:6px;background:var(--pipe);transform-origin:right center;transform:scaleX(0)}
/* S05 */
#s05eq{font:800 54px/1.3 "Bricolage",var(--fa);color:var(--ink)}
#s05eq .fa{font-family:var(--fa);font-weight:700}
.panel{background:var(--paper);border:2px solid var(--line);border-radius:18px;padding:18px 22px}
.panel .k{font-size:22px}
#s05trace svg,#s05deb svg{display:block;width:580px;height:150px}
/* S06 */
#s06ab{display:flex;gap:18px;align-items:stretch}
#s06ab .slot{flex:1;border:3px solid var(--line2);border-radius:16px;padding:16px 18px;background:var(--paper);direction:ltr;text-align:left}
#s06ab .slot b{display:block;font:600 30px "Plex Mono"}
#s06ab .slot span{font:400 22px "Plex Mono";color:var(--muted)}
#s06ab .slot.on{border-color:var(--blue);box-shadow:0 0 0 5px #2a78d622}
/* S07 */
#s07clockwrap{position:absolute;left:96px;top:120px;width:900px;background:#c9d6c4;border-radius:28px;padding:40px 46px;color:#1d2b1f;transition:none}
#s07clockwrap.hit{box-shadow:0 0 0 10px var(--pipe)}
#s07date{font:700 52px/1.3 var(--fa)}
#s07clock{font:700 150px/1.05 var(--fa);letter-spacing:.02em}
#s07rec{position:absolute;left:96px;top:520px;width:900px;background:#f7faf5;border-radius:22px;padding:24px 32px;box-shadow:0 26px 50px -20px #1d2b1f55}
#s07json{margin:8px 0 0;font:400 23px/1.45 "Plex Mono";color:#1d2b1f;white-space:pre;direction:ltr;text-align:left;min-height:270px}
#s07json mark{background:#f2b20055;color:inherit}
#s07q{display:flex;gap:14px;align-items:center}
#s07q div{width:96px;height:66px;border-radius:12px;border:3px solid var(--pipe);background:#f7faf5}
#s07timer{display:flex;gap:22px;align-items:center}
#s07timer svg{width:110px;height:110px;transform:rotate(-90deg)}
#s07timer b{font:700 46px var(--fa)}
#s07sms{background:var(--paper);border:2px solid var(--line2);border-radius:28px 28px 8px 28px;padding:20px 26px}
#s07sms .mono{font-size:24px;line-height:1.5;min-height:72px;overflow-wrap:anywhere;text-align:left}
/* S08 */
#s08flag{position:absolute;left:300px;top:250px;font:700 28px var(--fa);background:#fff4ec;border:2px solid var(--serious);border-radius:999px;padding:10px 24px;display:flex;gap:12px;align-items:center}
#s08flag i{width:16px;height:16px;border-radius:50%;background:var(--serious)}
#s08flag.hot{box-shadow:0 0 0 8px #ec835a33}
#s08inv{position:absolute;right:96px;top:300px;width:600px;background:var(--paper);border:2px solid var(--line);border-radius:20px;padding:26px 30px;box-shadow:0 30px 60px -30px #0005}
#s08inv .id{font:600 22px "Plex Mono";color:var(--muted);direction:ltr;text-align:right}
#s08inv .period{font:700 30px var(--fa);margin:6px 0 14px}
#s08inv .lines div{display:flex;justify-content:space-between;font:400 24px/1.9 var(--fa);border-bottom:1px solid var(--line)}
#s08inv .foot{display:flex;gap:20px;align-items:center;margin-top:16px}
#s08inv svg.qr{width:150px;height:150px;flex:none}
#s08ok{position:absolute;right:96px;top:880px;width:600px;font:700 28px var(--fa);color:var(--good);background:#e7f5e5;border-radius:16px;padding:14px 22px}
#s08lab{position:absolute;left:110px;top:780px;font:400 24px var(--fa);color:var(--muted)}
/* S09 */
#s09phone{position:absolute;left:220px;top:150px;width:430px;height:760px;border-radius:56px;background:var(--ink);padding:22px}
#s09phone .scr{background:var(--paper);border-radius:40px;height:100%;padding:56px 30px;display:flex;flex-direction:column;gap:22px}
#s09phone .bill{border:2px solid var(--line);border-radius:20px;padding:22px}
#s09phone .bill b{display:block;font:800 64px "Bricolage",var(--fa)}
#s09phone .alert{background:#fff4ec;border:2px solid var(--serious);border-radius:18px;padding:16px 18px;font:700 24px/1.5 var(--fa)}
.benefit{display:flex;gap:20px;align-items:center;font:700 40px/1.4 var(--fa);padding:22px 26px;border-radius:20px;border:2px solid transparent}
.benefit i{width:22px;height:22px;border-radius:50%;background:var(--line2);flex:none}
.benefit.on{background:var(--paper);border-color:var(--line)}
.benefit.on i{background:var(--pipe)}
/* S10 */
.gain{font:700 32px/1.45 var(--fa);padding:18px 24px;border-radius:18px;background:var(--paper);border:2px solid var(--line);display:flex;gap:16px;align-items:center}
.gain i{width:16px;height:16px;border-radius:50%;background:var(--line2);flex:none}
.gain.on{border-color:var(--blue)}
.gain.on i{background:var(--blue)}
#s10two{position:absolute;left:120px;top:720px;width:1000px;font:700 34px/1.5 var(--fa);background:#e9f1fc;border-radius:18px;padding:18px 26px}
#s10two small{display:block;font:400 21px var(--fa);color:var(--muted)}
#s10note{font:400 26px/1.6 var(--fa);color:var(--ink2);border-top:2px solid var(--line);padding-top:16px}
/* S11 */
.tag{font:700 40px/1.4 var(--fa);display:flex;gap:18px;align-items:center}
.tag i{width:20px;height:20px;border-radius:5px;background:var(--pipe);flex:none}
.next{margin:10px 0 0;padding:0;list-style:none;display:flex;flex-direction:column;gap:14px}
.next li{font:400 32px/1.5 var(--fa);color:var(--ink2);border-right:6px solid var(--blue);padding-right:18px}
#s11plate{position:absolute;left:150px;top:220px;width:860px;border-radius:26px;background:var(--paper);box-shadow:0 30px 70px -30px #0006;overflow:hidden;border:3px solid var(--ink);opacity:0}
#s11plate .stripes{height:46px;background:repeating-linear-gradient(-45deg,var(--pipe) 0 28px,var(--ink) 28px 56px)}
#s11plate .body{padding:34px 40px 40px;display:flex;flex-direction:column;gap:12px}
#s11plate b{font:700 64px/1.2 var(--fa)}
#s11plate .ltr{font:600 26px "Plex Mono";color:var(--muted);text-align:right}
#s11plate p{margin:8px 0 0;font:400 32px/1.7 var(--fa);color:var(--ink2)}
/* S12 */
.end.h{font-size:96px}
`;

const html = `<!doctype html>
<html lang="fa" dir="rtl">
<head><meta charset="utf-8"><title>کنتور هوشمند گاز — ویدیوی معرفی</title>
<style>${k.ISO_CSS}${out.css}${CSS}</style></head>
<body>
<div id="modelbox"><div id="model" class="iso" data-theme="light">${stage}</div></div>

<section class="scene" id="s01">
  <div class="col">
    <div class="k" id="s01k">شبکهٔ گاز ایران · یک روز سرد زمستان</div>
    <div class="big" id="s01n1"><b>۰</b><span>میلیون مترمکعب گاز در روز به خطوط فشارقوی</span></div>
    <div class="big" id="s01n2"><b>۰</b><span>میلیون مترمکعب در خانه‌ها و واحدهای تجاری</span><div class="track" style="margin-top:14px"><div id="s01bar"></div></div></div>
    <div class="chip" id="s01chip"><i></i>نصب کنتور هوشمند در خانه‌ها تازه آغاز شده</div>
  </div>
  <div class="src">منبع: سعید توکلی، مدیرعامل شرکت ملی گاز، خبرگزاری مهر، ۳۰ آذر ۱۴۰۴ · خبرگزاری صدا و سیما، ۸ تیر ۱۴۰۵</div>
</section>

<section class="scene" id="s02">
  <svg class="full" id="s02svg"></svg>
  <div class="col">
    <h2 class="h" id="s02h">مصرفِ واقعی، بین دو قرائت پنهان است</h2>
    <div class="big" id="s02n" style="margin-top:160px"><b>۰</b><span>میلیون مشترک گاز</span></div>
    <div class="chip" id="s02cost" style="font-size:27px"><i style="background:var(--red)"></i>برآورد هزینهٔ هوشمندسازی: حدود ۴ میلیارد دلار</div>
  </div>
  <div class="src">منبع: رضا نوشادی، شرکت مهندسی و توسعهٔ گاز، خبرگزاری مهر، ۱۳ مرداد ۱۴۰۳. نمودار مصرف فقط شکلی نمایشی است.</div>
</section>

<section class="scene" id="s03">
  <div class="col">
    <h2 class="h" id="s03h">به‌جای تعویض کنتور، کنارِ همان کنتور</h2>
    <div class="chip"><i></i>شمارش هر ۱۰ لیتر</div>
    <div class="chip"><i></i>خوداظهاری فصلی</div>
    <div class="chip"><i></i>ارسال با سیم‌کارت</div>
    <div class="chip"><i></i>فاکتور قابل‌چاپ و قابل‌راستی‌آزمایی</div>
  </div>
</section>

<section class="scene" id="s04"><div class="col"><h2 class="h" id="s04h">درون یک کنتور دیافراگمی</h2></div></section>

<section class="scene" id="s05">
  <div class="col" style="top:560px;gap:18px">
    <div id="s05eq">۱ دور = ۱ پالس = <span dir="ltr">0.01 m³</span></div>
    <div style="position:relative"><div class="panel" id="s05deb" style="position:absolute;right:0;top:78px;width:620px"><div class="k">حذف لرزش: فقط بسته‌شدنِ ۳۰ میلی‌ثانیه یا بیشتر</div><svg viewBox="0 0 600 150" style="direction:ltr"><path d="M10 40H90L96 120L102 40L108 120L114 40L120 120H400V40H590" fill="none" stroke="var(--muted)" stroke-width="4"/><path d="M120 132H400" stroke="var(--pipe)" stroke-width="6"/><text x="260" y="105" text-anchor="middle" font-family="Plex Mono" font-size="26" fill="var(--ink)">≥ 30 ms</text></svg></div>
    <div class="panel" id="s05trace"><div class="k">ورودی پالس · GPIO4</div><svg viewBox="0 0 600 150"><path d="" fill="none" stroke="var(--blue)" stroke-width="6" stroke-linejoin="round"/></svg></div></div>
  </div>
</section>

<section class="scene" id="s06">
  <div class="col" style="top:560px;gap:18px">
    <div id="s06ab"><div class="slot"><b>A</b><span>count · CRC-32</span></div><div class="slot"><b>B</b><span>count · CRC-32</span></div></div>
    <div class="chip" id="s06batt"><i></i>عمر باتری: بیش از ۱۰ سال، تخمینی و هنوز اندازه‌گیری‌نشده</div>
  </div>
</section>

<section class="scene" id="s07">
  <div class="col" style="width:700px"><h2 class="h" id="s07h">خوداظهاری فصلی</h2>
    <div class="k">ساعت ۰۰:۰۰ اولین روز هر فصل شمسی · به وقت تهران</div>
    <div id="s07q"><span class="k">در صف تا تأیید سرور</span><div></div><div></div><div></div></div>
    <div id="s07timer"><svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="42" fill="none" stroke="var(--line)" stroke-width="10"/><circle class="fg" cx="50" cy="50" r="42" fill="none" stroke="var(--pipe)" stroke-width="10" stroke-dasharray="264" stroke-dashoffset="264"/></svg><b>۰ ساعت</b></div>
    <div id="s07sms"><div class="k">پیامک پشتیبان</div><div class="mono"></div></div>
  </div>
  <div id="s07clockwrap"><div id="s07date"></div><div id="s07clock"></div><div class="k" style="color:#3c4d3f">به وقت تهران</div></div>
  <div id="s07rec"><div class="k" style="color:#5d6f60">رکورد «بستن دوره» · period_close</div><pre id="s07json"></pre></div>
</section>

<section class="scene" id="s08">
  <svg class="full" id="s08svg"></svg>
  <div class="col" style="right:96px;top:120px;width:1100px"><h2 class="h" id="s08h">در سمت سرور</h2></div>
  <div id="s08lab">مصرف روزانهٔ ۲۴۰ خانهٔ شبیه‌سازی‌شده در شش شهر · مترمکعب</div>
  <div id="s08flag"><i></i>«یک نفر نگاه کند» · هرگز به‌تنهایی اثبات نشتی نیست</div>
  <div id="s08inv"><div class="id"></div><div class="period"></div><div class="lines"></div><div class="foot"><svg class="qr"></svg><div class="k">کد QR به رکورد خودِ صادرکننده باز می‌شود و هر کسی می‌تواند فاکتور را بررسی کند.</div></div></div>
  <div id="s08ok">✓ صادرشده توسط اپراتور کنتور · تعرفهٔ نمایشی</div>
</section>

<section class="scene" id="s09">
  <div id="s09phone"><div class="scr"><div class="k">قبض فصلی</div><div class="bill"><div class="k">۱۴۰۵/۰۴ تا ۱۴۰۵/۰۶</div><b>۲۱۹٫۵۶</b><div class="k">مترمکعب · از خوانش خودکار</div></div><div class="alert">مصرف امروز از الگوی همیشگی شما بیشتر است. لطفاً نگاهی بیندازید.</div><div class="k" style="font-size:20px">نمونهٔ نمایشی؛ داده‌ها شبیه‌سازی‌شده‌اند.</div></div></div>
  <div class="col"><h2 class="h" id="s09h">در زندگی روزمره</h2>
    <div class="benefit"><i></i>قبض بر اساس عدد واقعی</div>
    <div class="benefit"><i></i>بی‌نیاز از ماندن در خانه برای مأمور</div>
    <div class="benefit"><i></i>خبرِ زودترِ مصرفِ غیرعادی</div>
  </div>
</section>

<section class="scene" id="s10">
  <svg class="full" id="s10svg"></svg>
  <div class="col"><h2 class="h" id="s10h">برای شرکت ملی گاز: مزیت‌های بالقوه</h2>
    <div class="gain"><i></i>قرائت خودکار به‌جای مراجعهٔ حضوری</div>
    <div class="gain"><i></i>تصویر نزدیک به لحظه در روزهای اوج</div>
    <div class="gain"><i></i>کشف زودتر دست‌کاری و مصرف غیرعادی</div>
    <div class="gain"><i></i>هوشمندسازی کنتورهای موجود، بدون تعویض همه</div>
    <div id="s10note">هزینه و دقتِ واقعی این راه فقط با آزمون میدانی و همکاری با اپراتور معلوم می‌شود.</div>
  </div>
  <div id="s10two">دو درجه خنک‌تر بودنِ خانه‌ها ≈ ۵۰ میلیون مترمکعب گاز در روز<small>سعید توکلی، مدیرعامل شرکت ملی گاز، خبرگزاری مهر، ۳۰ آذر ۱۴۰۴ · منحنی بالا فقط شکلی نمایشی است</small></div>
</section>

<section class="scene" id="s11">
  <div id="s11plate"><div class="stripes"></div><div class="body"><b>فقط برای آزمایشگاه</b><span class="ltr">BENCH PROTOTYPE · NOT FOR LIVE GAS</span><p>ورودی فقط پالس شبیه‌سازی‌شده ۳٫۳ ولت. هرگز به کنتور، لولهٔ گاز، شیر، برق شهر یا سیم‌کشی میدانی وصل نشود. علامت ناهنجاری اثبات نشتی نیست.</p></div></div>
  <div class="col" style="width:640px"><h2 class="h" id="s11h">امروز کجا هستیم</h2>
    <div class="tag"><i></i>پالس‌ها شبیه‌سازی‌شده‌اند</div>
    <div class="tag"><i></i>تعرفه نمایشی است</div>
    <div class="tag"><i style="background:var(--red)"></i>هرگز به کنتور یا لولهٔ گاز واقعی وصل نشود</div>
    <ul class="next"><li>آزمون میدانی با اپراتور</li><li>گواهی‌های ایمنی و اندازه‌شناسی</li><li>طراحی محفظهٔ نهایی</li></ul>
  </div>
</section>

<section class="scene" id="s12">
  <div class="col" style="top:280px;width:720px">
    <div class="end h">کنتور هوشمند گاز</div>
    <div class="end lead">هر ده لیتر، شمرده می‌شود.</div>
    <div class="end mono" style="font-size:28px;font-weight:600;text-align:right;white-space:nowrap">github.com/ebixs/smart-gas-meter-iot</div>
    <div class="end k" style="font-size:24px">نمونهٔ آزمایشگاهی متن‌باز · داده‌های شبیه‌سازی‌شده · قیمت‌های نمایشی</div>
  </div>
</section>

<div id="partcard"><h3></h3><small></small><p></p></div>
<div id="brand"><i></i>کنتور هوشمند گاز<span id="chapter"></span></div>
<div id="honest">نمونهٔ آزمایشگاهی · داده‌های شبیه‌سازی‌شده</div>
<div id="sub"><span id="subtext"></span></div>
<div id="progress"></div>
<script type="module">${(strip("turn.mjs") + "\n" + readFileSync(join(HERE, "explainer.js"), "utf8")
  .replace("__FIG__", JSON.stringify(FIG))
  .replace("__ITEMS__", JSON.stringify(ITEMS))
  .replace("__PLAN__", JSON.stringify({ length, scenes }))
  .replace("__FILM__", JSON.stringify(FILM))
  .replace("const follow = null;", FOLLOW)).replace(/<\/(script)/gi, "<\\/$1")}</script>
</body></html>`;
writeFileSync(join(HERE, "explainer.html"), html);
console.log(`wrote explainer.html · ${(html.length / 1024).toFixed(0)} KB · ${length.toFixed(1)} s · ${scenes.filter((s) => s.audio).length}/${scenes.length} scenes with recorded audio`);
