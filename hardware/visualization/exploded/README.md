# Exploded 3D model · مدل انفجاری سه‌بعدی

> **خلاصهٔ فارسی.** یک مدل سه‌بعدیِ قابل‌چرخش از کنتور دیافراگمی G4 (نمونهٔ عمومی) و دستگاه SGM با ۱۱۹ قطعه در ۳۵ بخش. با یک اسلایدر از هم باز می‌شود. روی هر قطعه که کلیک کنید، بزرگ می‌شود و نام و کارکردش را به فارسی و انگلیسی نشان می‌دهد. صفحه آفلاین است (همهٔ فونت‌ها و کدها داخل یک فایل)، پس در کنفرانس بدون اینترنت هم کار می‌کند. کلید T یک تور خودکار پخش می‌کند و F صفحه را تمام‌صفحه می‌کند.

`index.html` is one self-contained, offline page: a turnable, explodable model of a generic G4 diaphragm gas
meter with the SGM bench prototype beside it. 119 convex parts in 35 named items, each with a Persian and
English name and job (`parts.mjs`).

| Key | Does |
|---|---|
| drag · ← → | turn the model |
| ↑ ↓ · slider | take it apart, put it back |
| click a part · `[` `]` | select, zoom in, show its name and job |
| `L` | language: both · فارسی · English |
| `T` | guided tour (the same timeline the video uses) |
| `F` | full screen |
| scroll · double-click | zoom · reset the view |

## What is true here

- The **SGM device** follows the repository: board v0.2 (ESP32-S3-WROOM-1, AP63203 buck, USB-C with ESD, J2 pulse
  input on GPIO4, J3 header, BOOT/RESET, D1 on GPIO5), the tamper input on GPIO15, and the v0.3 recommendations from
  [`docs/hardware-decisions.md`](../../../docs/hardware-decisions.md) (Li-SOCl₂ D cell with a hybrid layer capacitor,
  a plug-in modem board for BG95-M3 or EC200U-EU).
- The **enclosure, mount and antenna placement** are a concept; they are still open items.
- The **G4 internals** (diaphragms, covers, flag rods, links, crank, slide valves, gear, magnetic coupling) are a
  generic illustration of how diaphragm meters work, not one maker's design.
- Bench only: synthetic 3.3 V pulses; never connect anything here to a live gas meter, gas line or mains.

## Build

The model is drawn with the vendored [anatomy](kit/LICENSE) kit (MIT): every part is a convex solid built at its
assembled place, every assembly is a slide group riding one turntable group, and the painter's order comes from
separating planes solved at build time.

```bash
cd hardware/visualization/exploded
node page.mjs                  # → index.html (builds the model: about 10 s)
node build.mjs --audit         # kit audit + orbit audit over the turn, the explode and the turn apart (~1 h)
node build.mjs --audit --quick # the same, undersampled, for iteration
node print.mjs --png           # → ../media/sgm-exploded-sheets-a4.pdf (8 A4 pages)
node capture.mjs ../media/sgm-exploded-tour.mp4 --lang both   # guided tour, 1920×1080, 30 fps
```

`capture.mjs` and `print.mjs` drive the built page through `window.__sgm` (`render`, `snapshot`), so the video, the
sheets and the live page always show the same model and the same notes.
