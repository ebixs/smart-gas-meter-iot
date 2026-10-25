// Records explainer.html frame by frame and, when the scene recordings exist, lays each one at its scene's narration start.
// node media/explainer/capture.mjs out.mp4 [--fps 30] [--from s] [--to s] [--stills 10,20]
import { spawn, spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const HERE = dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const opt = (name, fallback) => { const i = argv.indexOf(`--${name}`); return i >= 0 ? argv[i + 1] : fallback; };
const out = argv[0] && !argv[0].startsWith("--") ? argv[0] : join(HERE, "..", "..", "hardware", "visualization", "media", "sgm-explainer-fa.mp4");
const fps = Number(opt("fps", 30));
const timing = JSON.parse(readFileSync(join(HERE, "timing.json"), "utf8"));
const from = Number(opt("from", 0));
const to = Math.min(timing.length, Number(opt("to", timing.length)));

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.goto(pathToFileURL(join(HERE, "explainer.html")).href);
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(300);

const stills = opt("stills", "");
if (stills) {
  for (const t of stills.split(",").map(Number)) { await page.evaluate((t) => window.__render(t), t); await page.screenshot({ path: out.replace(/\.mp4$/, "") + `-t${t}.png` }); }
  await browser.close();
  console.log(`stills · errors ${JSON.stringify(errors)}`);
  process.exit(0);
}

const silent = out.replace(/\.mp4$/, "") + ".video.mp4";
const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(fps), "-c:v", "mjpeg", "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", silent], { stdio: ["pipe", "inherit", "inherit"] });
const frames = Math.round((to - from) * fps);
const t0 = Date.now();
for (let i = 0; i < frames; i++) {
  await page.evaluate((t) => window.__render(t), from + i / fps);
  const jpg = await page.screenshot({ type: "jpeg", quality: 94 });
  if (!ff.stdin.write(jpg)) await new Promise((r) => ff.stdin.once("drain", r));
  if (i % (fps * 15) === 0) console.log(`${(i / fps).toFixed(0)} / ${(frames / fps).toFixed(0)} s · ${((Date.now() - t0) / 1000).toFixed(0)} s elapsed`);
}
ff.stdin.end();
await new Promise((r) => ff.on("close", r));
await browser.close();

// audio: every recorded scene delayed to its narration start, mixed, loudness-normalised; silence when nothing is recorded
const voiced = timing.scenes.filter((s) => s.audio && s.narrStart >= from && s.narrStart < to);
if (voiced.length) {
  const inputs = voiced.flatMap((s) => ["-i", join(HERE, s.audio)]);
  const chains = voiced.map((s, i) => `[${i + 1}:a]aresample=48000,highpass=f=70,adelay=${Math.round((s.narrStart - from) * 1000)}:all=1[a${i}]`).join(";");
  const mix = `${chains};${voiced.map((_, i) => `[a${i}]`).join("")}amix=inputs=${voiced.length}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11,apad[aout]`;
  const r = spawnSync("ffmpeg", ["-y", "-loglevel", "error", "-i", silent, ...inputs, "-filter_complex", mix, "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], { stdio: "inherit" });
  if (r.status) process.exit(r.status);
} else {
  spawnSync("ffmpeg", ["-y", "-loglevel", "error", "-i", silent, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart", out], { stdio: "inherit" });
}
spawnSync("rm", ["-f", silent]);
console.log(`wrote ${out} · ${frames} frames · ${(frames / fps).toFixed(1)} s · ${voiced.length} voiced scenes · errors ${JSON.stringify(errors)}`);
