// Builds the exploded SGM figure: node build.mjs [--audit] [--quick]
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "./kit/iso-kit.mjs";
import * as A from "./kit/audit.mjs";
import * as TA from "./kit/turn-audit.mjs";
import { P, R, T, WIDTH, HEIGHT, follow, poses, STAGES, TRAVEL } from "./model.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const strip = (file) => readFileSync(join(HERE, "kit", file), "utf8").replace(/^export /gm, "");

const t0 = Date.now();
const out = T.build({ statics: R.items, poses, strict: !argv.includes("--loose") });
A.settle(R, P);
console.log(`built ${out.report.parts} parts in ${((Date.now() - t0) / 1000).toFixed(1)} s · ${out.report.layers.map((l) => `${l.name}: ${l.planar} planar, ${l.framed ?? 0} framed, ${l.dynamic} dynamic`).join(" · ")} · data ${(JSON.stringify(out.data).length / 1024).toFixed(0)} KB`);

if (argv.includes("--audit")) {
  A.auditOrExit(R, P);
  TA.orbitOrExit(T, R, P, {
    sweep: { at: (x) => follow({ spin: x, explode: 0 }), from: 0, to: 360, frame: 0.5 },
    clips: [
      { name: "explode", at: (t) => follow({ spin: 20 + 6 * t, explode: t / 2 }), from: 0, to: 2, frame: 1 / 30 },
      { name: "apart", at: (x) => follow({ spin: x, explode: 1 }), from: 0, to: 360, frame: 1 },
    ],
    crowd: [["pulser.cable", "pulser.reed"]],
    quick: argv.includes("--quick"),
    only: argv.find((a) => a.startsWith("--only="))?.slice(7).split(",") ?? null,
    log: argv.includes("--verbose") ? (text) => console.log(`  … ${text}`) : null,
  });
}

const layerOf = (name) => R.items.filter((item) => item.layer === name).sort((a, b) => a.key - b.key).map((item) => item.svg);
const LABEL = "An exploded, turnable model of the smart gas meter bench prototype: a generic G4 diaphragm gas meter with its index, a reed pulser on the last drum, and the SGM enclosure with its main board, modem board, battery and antenna.";
const backSvg = k.figureSvg({ width: WIDTH, height: HEIGHT, label: LABEL, body: layerOf("back") });
const stage = `<div class="iso-stage iso-turn sgm-stage">${backSvg}${out.layerSvg("model", { width: WIDTH, height: HEIGHT })}</div>`;
const names = T.parts.map((p) => p.name);
const FIG = { turn: out.data, names, stages: STAGES, travel: TRAVEL, width: WIDTH, height: HEIGHT };
const FOLLOW = `const follow = ${follow.toString()};\nconst STAGES = ${JSON.stringify(STAGES)};\nconst TRAVEL = ${JSON.stringify(TRAVEL)};\n`;

export { out, stage, FIG, FOLLOW, k, strip, HERE };

if (argv.includes("--test")) {
  const page = `<!doctype html><html><head><meta charset="utf-8"><style>${k.ISO_CSS}${out.css}body{margin:0;background:#f2f3ef}.sgm-stage{width:760px}</style></head><body class="iso" data-theme="light">${stage}<script type="module">${strip("turn.mjs").replace("if (mark[w] === 1) {", "if (mark[w] === 1) { const __c = []; (window.__cyc ??= []).push(__c);").replace("if (!checked[edge]) {", "__c && __c.push(parts[x] + '>' + parts[to[edge]]); if (!checked[edge]) {")}
${FOLLOW}
const FIG = ${JSON.stringify(FIG)};
const stage = document.querySelector(".sgm-stage");
const c = TURN.mount(stage, FIG.turn, { follow });
window.__set = (spin, explode) => c.set({ spin, explode });
const q = new URLSearchParams(location.search);
c.set({ spin: +(q.get("spin") ?? 0), explode: +(q.get("x") ?? 0) });
</script></body></html>`;
  writeFileSync(join(HERE, "test.html"), page);
  console.log(`wrote test.html ${(page.length / 1024).toFixed(0)} KB`);
}
