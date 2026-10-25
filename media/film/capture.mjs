// Render film.html frame by frame (deterministic seek) and encode with ffmpeg.
//   node media/film/capture.mjs [out.mp4] [--fps 60] [--from 0] [--to 30] [--stills 1.0,4.2,...]
import { spawn } from "node:child_process";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require("playwright")); } catch { ({ chromium } = require("/usr/local/lib/node_modules/playwright")); }
const HERE = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const opt = (k, d) => (args.includes(k) ? args[args.indexOf(k) + 1] : d);
const out = resolve(args[0] && !args[0].startsWith("--") ? args[0] : join(HERE, "sgm-launch-film.mp4"));
const fps = Number(opt("--fps", 60)), from = Number(opt("--from", 0)), to = Number(opt("--to", 30));
const stills = opt("--stills", "");
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
await page.goto("file://" + join(HERE, "film.html"));
await page.evaluate(() => window.filmReady);
if (stills) {
  for (const t of stills.split(",").map(Number)) {
    await page.evaluate((t) => window.render(t), t);
    await page.screenshot({ path: out.replace(/\.mp4$/, "") + `-${t.toFixed(2)}.png` });
  }
  await browser.close(); process.exit(0);
}
const ff = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(fps), "-i", "-",
  "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], { stdio: ["pipe", "inherit", "inherit"] });
const n = Math.round((to - from) * fps);
for (let i = 0; i < n; i++) {
  const t = from + i / fps;
  await page.evaluate((t) => window.render(t), t);
  const png = await page.screenshot({ type: "png" });
  if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once("drain", r));
  if (i % 300 === 0) console.log(`frame ${i}/${n}`);
}
ff.stdin.end();
await new Promise((r) => ff.on("close", r));
await browser.close();
console.log("wrote", out);
