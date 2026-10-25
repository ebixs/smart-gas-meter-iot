"""Writes docs/video/explainer-script-fa.md from scenes.json (one source for the narration and the video)."""
import json, pathlib
here = pathlib.Path(__file__).parent
d = json.loads((here / "scenes.json").read_text(encoding="utf-8"))
fa = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
out = [f"# متن گویندگی ویدیوی معرفی — {d['title']}", "",
       "> **وضعیت:** نمونهٔ آزمایشگاهی. همهٔ پالس‌ها شبیه‌سازی‌شده‌اند، تعرفه نمایشی است و دستگاه هرگز نباید به کنتور، لولهٔ گاز یا برق شهرِ واقعی وصل شود.", "",
       "## راهنمای ضبط", "",
       "- هر صحنه را در **یک فایل جدا** ضبط کنید و نامش را شمارهٔ صحنه بگذارید: `s01`، `s02`، … `s12` (فرمت wav، m4a یا mp3، هر کدام راحت‌تر است).",
       "- اتاق ساکت؛ گوشی را در حالت پرواز بگذارید و حدود ۲۰ سانتی‌متر از دهان فاصله بدهید.",
       "- قبل و بعد از هر صحنه نیم ثانیه سکوت کنید.",
       "- اگر جایی اشتباه شد، همان صحنه را از اول دوباره بگیرید؛ فقط آخرین نسخه را بفرستید.",
       "- با سرعت طبیعی بخوانید. تصویر با طول صدای شما هماهنگ می‌شود؛ زمان‌های زیر فقط تخمین است.",
       "- اعداد را همان‌طور که با حروف نوشته شده بخوانید.", "",
       "## صحنه‌ها", ""]
total = 0
for i, s in enumerate(d["scenes"], 1):
    secs = len(s["text"].split()) / d["wordsPerSecond"]
    total += secs
    out += [f"### صحنهٔ {str(i).translate(fa)} — {s['name']}  (`{s['id']}` · حدود {str(round(secs)).translate(fa)} ثانیه)", "",
            f"> {s['text']}", "",
            f"*تصویر:* {s['visual']}", ""]
    if s["onScreen"]:
        out += ["*روی صفحه:* " + " · ".join(s["onScreen"]), ""]
    if s["source"]:
        out += ["*منبع:* " + "، ".join(f"[{d['sources'][k]['title']}]({d['sources'][k]['url']})" for k in s["source"]), ""]
out += [f"**مدت تقریبی کل:** {str(round(total / 60, 1)).translate(fa)} دقیقه", "", "## منابع", ""]
out += [f"- [{v['title']}]({v['url']})" for v in d["sources"].values()]
out += ["", "> مزیت‌هایی که برای مردم و شرکت ملی گاز گفته شده «بالقوه» هستند؛ این نمونه هنوز در میدان آزمایش نشده است."]
(here.parent.parent / "docs" / "video" / "explainer-script-fa.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("ok", round(total / 60, 2))
