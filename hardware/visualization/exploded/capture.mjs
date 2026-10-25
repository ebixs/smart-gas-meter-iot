// Records the guided tour of index.html to an MP4, one deterministic frame at a time.
// node capture.mjs out.mp4 [--fps 30] [--lang both|fa|en] [--theme light|dark] [--from 0] [--to end] [--stills 10,40]
import { spawn } from "node:child_process";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const HERE = dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const opt = (name, fallback) => {
  const i = argv.indexOf(`--${name}`);
  return i >= 0 ? argv[i + 1] : fallback;
};
const out = argv[0] && !argv[0].startsWith("--") ? argv[0] : "exploded-tour.mp4";
const fps = Number(opt("fps", 30));
const lang = opt("lang", "both");
const theme = opt("theme", "light");
const stills = opt("stills", "");

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.goto(pathToFileURL(join(HERE, "index.html")).href);
await page.evaluate(({ lang, theme }) => {
  document.documentElement.dataset.capture = "";
  const style = document.createElement("style");
  style.textContent = ".controls,.pager,.seg,[data-tour],[data-toggle-theme],.sgm-card .hint{display:none!important}.sgm-list{scroll-behavior:auto!important}";
  document.head.append(style);
  __sgm.setTheme(theme);
  __sgm.setLang(lang);
}, { lang, theme });
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(400);
const length = await page.evaluate(() => { window.__tl = __sgm.timeline(); return window.__tl.length; });
const from = Number(opt("from", 0));
const to = Math.min(length, Number(opt("to", length)));
const frameAt = async (t) => page.evaluate((t) => {
  const r = __sgm.render(window.__tl, t);
  const card = document.querySelector(".sgm-card");
  const a = Math.min(1, Math.max(0, r.selAge / 0.45));
  card.style.opacity = String(a * a * (3 - 2 * a));
  card.style.transform = `translateY(${((1 - a) * 8).toFixed(2)}px)`;
  const current = document.querySelector('.sgm-list [aria-current="true"]');
  if (current) current.scrollIntoView({ block: "center" });
  return r.sel;
}, t);

if (stills) {
  for (const t of stills.split(",").map(Number)) {
    await frameAt(t);
    await page.screenshot({ path: out.replace(/\.mp4$/, "") + `-t${t}.png` });
  }
  console.log(`stills written · errors ${JSON.stringify(errors)}`);
  await browser.close();
  process.exit(0);
}

const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(fps), "-c:v", "mjpeg", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], { stdio: ["pipe", "inherit", "inherit"] });
const frames = Math.round((to - from) * fps);
const t0 = Date.now();
for (let i = 0; i < frames; i++) {
  await frameAt(from + i / fps);
  const jpg = await page.screenshot({ type: "jpeg", quality: 94 });
  if (!ff.stdin.write(jpg)) await new Promise((r) => ff.stdin.once("drain", r));
  if (i % (fps * 10) === 0) console.log(`${(i / fps).toFixed(0)} s / ${(frames / fps).toFixed(0)} s · ${((Date.now() - t0) / 1000).toFixed(0)} s elapsed`);
}
ff.stdin.end();
await new Promise((r) => ff.on("close", r));
await browser.close();
console.log(`wrote ${out} · ${frames} frames · ${(frames / fps).toFixed(1)} s · errors ${JSON.stringify(errors)}`);
