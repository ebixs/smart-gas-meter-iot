// Builds one exploded board figure: node build.mjs <carrier|modem|blocks> [--audit] [--quick] [--test]
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "../exploded/kit/iso-kit.mjs";
import * as A from "../exploded/kit/audit.mjs";
import * as TA from "../exploded/kit/turn-audit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const NAME = argv.find((a) => !a.startsWith("--")) ?? "carrier";
const mod = await import(`./models/${NAME}.mjs`);
const { P, R, T, WIDTH, HEIGHT, follow, poses, STAGES, TRAVEL } = mod.model;
const strip = (file) => readFileSync(join(HERE, "..", "exploded", "kit", file), "utf8").replace(/^export /gm, "");

const t0 = Date.now();
const out = T.build({ statics: R.items, poses, strict: !argv.includes("--loose") });
A.settle(R, P);
console.log(`${NAME}: built ${out.report.parts} parts in ${((Date.now() - t0) / 1000).toFixed(1)} s · ${out.report.layers.map((l) => `${l.name}: ${l.planar} planar, ${l.framed ?? 0} framed, ${l.dynamic} dynamic`).join(" · ")} · data ${(JSON.stringify(out.data).length / 1024).toFixed(0)} KB`);

if (argv.includes("--audit")) {
  A.auditOrExit(R, P);
  TA.orbitOrExit(T, R, P, {
    sweep: { at: (x) => follow({ spin: x, explode: 0 }), from: 0, to: 360, frame: 1 },
    clips: [
      { name: "explode", at: (t) => follow({ spin: 20 + 6 * t, explode: t / 2 }), from: 0, to: 2, frame: 1 / 15 },
      { name: "apart", at: (x) => follow({ spin: x, explode: 1 }), from: 0, to: 360, frame: 2 },
    ],
    quick: argv.includes("--quick"),
    log: argv.includes("--verbose") ? (text) => console.log(`  … ${text}`) : null,
  });
}

const layerOf = (name) => R.items.filter((item) => item.layer === name).sort((a, b) => a.key - b.key).map((item) => item.svg);
const backSvg = k.figureSvg({ width: WIDTH, height: HEIGHT, label: mod.LABEL, body: layerOf("back") });
const stage = `<div class="iso-stage iso-turn sgm-stage">${backSvg}${out.layerSvg("model", { width: WIDTH, height: HEIGHT })}</div>`;
const names = T.parts.map((p) => p.name);
const FIG = { turn: out.data, names, stages: STAGES, travel: TRAVEL, width: WIDTH, height: HEIGHT };
const FOLLOW = `const follow = ${follow.toString()};\nconst STAGES = ${JSON.stringify(STAGES)};\nconst TRAVEL = ${JSON.stringify(TRAVEL)};\n`;
export const ART_CSS = readFileSync(join(HERE, "art.css"), "utf8");

export { out, stage, FIG, FOLLOW, k, strip, HERE, NAME, mod };

if (argv.includes("--test")) {
  const page = `<!doctype html><html><head><meta charset="utf-8"><style>${k.ISO_CSS}${out.css}${ART_CSS}body{margin:0;background:#f2f3ef}.sgm-stage{width:${WIDTH}px}</style></head><body class="iso" data-theme="light">${stage}<script type="module">${strip("turn.mjs")}
${FOLLOW}
const FIG = ${JSON.stringify(FIG)};
const stage = document.querySelector(".sgm-stage");
const c = TURN.mount(stage, FIG.turn, { follow });
window.__set = (spin, explode) => c.set({ spin, explode });
const q = new URLSearchParams(location.search);
c.set({ spin: +(q.get("spin") ?? 0), explode: +(q.get("x") ?? 0) });
</script></body></html>`;
  writeFileSync(join(HERE, `test-${NAME}.html`), page);
  console.log(`wrote test-${NAME}.html ${(page.length / 1024).toFixed(0)} KB`);
}
