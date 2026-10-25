# Persian explainer video · ویدیوی معرفی فارسی

> **راهنمای سریع.** متن گویندگی در [`docs/video/explainer-script-fa.md`](../../docs/video/explainer-script-fa.md) است.
> هر صحنه را جدا ضبط کنید و فایل‌ها را با نام `s01` تا `s12` در پوشهٔ `audio/` بگذارید (wav، m4a، mp3 یا ogg).
> سپس دو فرمان زیر را اجرا کنید؛ طول هر صحنه با طول صدای شما تنظیم می‌شود و زیرنویس هم با آن هماهنگ می‌شود.

```bash
node media/explainer/build.mjs      # timing from the recordings (estimates when none) → explainer.html, timing.json, explainer-fa.srt
node media/explainer/capture.mjs    # → hardware/visualization/media/sgm-explainer-fa.mp4 (1920×1080, 30 fps)
```

- `scenes.json` is the single source: narration, on-screen text, visual notes and sources for every scene.
  `python3 media/explainer/script_md.py` rewrites the recording script from it.
- Every frame is a pure function of time (`render(t)`), so a capture is repeatable. The 3D scenes use the same model
  as the exploded page; highlights and camera moves are timed from where each phrase sits in the narration, so they
  follow the voice when the recordings arrive.
- Without recordings the video is silent with Persian subtitles. With them, each scene's file is placed at its
  narration start, high-passed at 70 Hz and the mix is normalised to −16 LUFS.
- Benefits for households and for the National Iranian Gas Company are stated as potential; every figure on screen
  carries its source (Mehr News Agency, IRIB News, and the repository's own analytics). Data in the video is synthetic.
