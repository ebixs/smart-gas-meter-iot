// Bilingual notes for the modem daughterboard v0.1 exploded model. Values, references and nets come from
// hardware/kicad-modem/design_modem_v01.py; EC200U facts from the Quectel EC200U Series Hardware Design V1.0.
// The EC200U footprint on this board is PROVISIONAL (see hardware/kicad-modem/README.md).

export const SECTIONS = [
  { id: "stack", en: "Layer stack (4 layers)", fa: "لایه‌های بُرد (۴ لایه)", noteEn: "Slabs are drawn thicker and pulled apart so each layer's real artwork can be seen.", noteFa: "لایه‌ها ضخیم‌تر و جدا از هم کشیده شده‌اند تا طرح واقعی هر لایه دیده شود." },
  { id: "module", en: "LTE module and its power", fa: "ماژول LTE و تغذیهٔ آن", noteEn: "The EC200U footprint is provisional until Quectel's footprint file replaces it.", noteFa: "ردپای EC200U موقت است تا فایل رسمی Quectel جایگزین آن شود." },
  { id: "logic", en: "Control and level shifting", fa: "کنترل و تبدیل سطح ولتاژ" },
  { id: "sim", en: "SIM and antenna", fa: "سیم‌کارت و آنتن" },
  { id: "bench", en: "Carrier link and bench access", fa: "اتصال به بُرد حامل و دسترسی آزمایشگاهی" },
];

const L = (id, x, spin, en, fa, facts = []) => ({ id, sec: "stack", match: [`layer.${id}`], x, spin, en, fa, facts });
const C = (id, sec, refs, en, fa, facts = [], spin = 25, x = 0.45) => ({ id, sec, match: refs.map((r) => `cmp.${r}.`), x, spin, en, fa, facts });

export const ITEMS = [
  // ---------------- layers ----------------
  L("topmask", 1, 25,
    { name: "Top solder mask and silkscreen", does: "Green mask with openings for every pad, and the printing: the board name, ANT, SIM, NET and BOOT labels, and the warning FOOTPRINT PROVISIONAL next to the module." },
    { name: "لاک محافظ و چاپ رویی", does: "لاک سبز با دریچه برای هر پد، و نوشته‌ها: نام بُرد، برچسب‌های ANT، SIM، NET و BOOT و هشدار «ردپای موقت» کنار ماژول." }),
  L("fcu", 1, 25,
    { name: "Top copper (F.Cu)", does: "Module pads, the 50 Ω antenna line, the SIM traces and most signals, with a ground pour around them. Short tracks and vias drop every ground and VBAT pad to the planes below." },
    { name: "مس رویی (F.Cu)", does: "پدهای ماژول، خط ۵۰ اهمی آنتن، مسیرهای سیم‌کارت و بیشتر سیگنال‌ها، با سطح زمین در اطرافشان. مسیرهای کوتاه و ویاها هر پد زمین و VBAT را به صفحه‌های زیرین می‌رسانند." },
    [{ en: "Antenna line: 0.35 mm over In1 (to confirm with the fab's impedance calculator)", fa: "خط آنتن: ۰٫۳۵ میلی‌متر روی In1 (باید با محاسبه‌گر امپدانس سازنده تأیید شود)" }]),
  L("in1", 1, 25,
    { name: "Inner layer 1: ground plane", does: "Solid ground under the module and the antenna line: the reference that makes the 50 Ω line and the module's 2 A bursts behave." },
    { name: "لایهٔ داخلی ۱: صفحهٔ زمین", does: "زمین یکپارچه زیر ماژول و خط آنتن؛ مرجعی که خط ۵۰ اهمی و جریان‌های ۲ آمپری ماژول را مهار می‌کند." }),
  L("in2", 1, 25,
    { name: "Inner layer 2: VBAT plane", does: "The whole layer carries MODEM_VIN (VBAT, 3.8 V). The datasheet asks for VBAT traces at least 2–2.5 mm wide; a plane is wider than any trace and feeds VBAT_RF and VBAT_BB through short vias." },
    { name: "لایهٔ داخلی ۲: صفحهٔ VBAT", does: "کل این لایه ولتاژ MODEM_VIN (همان VBAT، ‏۳٫۸ ولت) را می‌برد. دیتاشیت پهنای مسیر VBAT را دست‌کم ۲ تا ۲٫۵ میلی‌متر می‌خواهد؛ صفحه از هر مسیری پهن‌تر است و با ویاهای کوتاه به VBAT_RF و VBAT_BB می‌رسد." }),
  L("bcu", 1, 25,
    { name: "Bottom copper (B.Cu)", does: "Signals that cross under the module, including the USB_BOOT line from its centre pad, with a ground pour stitched to the inner plane by a grid of vias." },
    { name: "مس زیرین (B.Cu)", does: "سیگنال‌هایی که از زیر ماژول عبور می‌کنند، از جمله خط USB_BOOT از پد میانی، با سطح زمینی که با شبکه‌ای از ویاها به صفحهٔ داخلی دوخته شده است." }),
  L("botmask", 1, 25,
    { name: "Bottom mask and silkscreen", does: "The underside carries the socket J1 and the line \"J1 = carrier J6 (pin 1 MODEM_VIN)\", seen mirrored from above." },
    { name: "لاک و چاپ زیرین", does: "زیر بُرد سوکت J1 قرار دارد و جملهٔ «J1 = J6 بُرد حامل (پایهٔ ۱ MODEM_VIN)» که از بالا وارونه دیده می‌شود." },
    [{ en: "Two M2.5 mounting holes", fa: "دو سوراخ نصب M2.5" }]),

  // ---------------- module and power ----------------
  C("ec200u", "module", ["U1"],
    { name: "Quectel EC200U-EU", does: "The LTE Cat 1 module that carries the readings to the server and sends the SMS fallback. It runs from VBAT directly and talks 1.8 V logic. 80 edge pads plus 64 pads underneath, 28 × 31 mm." },
    { name: "ماژول Quectel EC200U-EU", does: "ماژول LTE گربهٔ ۱ که خوانش‌ها را به سرور می‌رساند و پیامک پشتیبان را می‌فرستد. مستقیم از VBAT تغذیه می‌شود و منطق ۱٫۸ ولتی دارد. ۸۰ پد کناری و ۶۴ پد زیرین، ۲۸ × ۳۱ میلی‌متر." },
    [{ en: "VBAT 3.3–4.3 V, 3.8 V nominal; up to 2 A in bursts", fa: "VBAT ‏۳٫۳ تا ۴٫۳ ولت، نامی ۳٫۸؛ تا ۲ آمپر در لحظهٔ ارسال" }, { en: "Footprint PROVISIONAL: pad positions are placeholders", fa: "ردپا موقت است: جای پدها نمایشی است" }], 30),
  C("vbat", "module", ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "D1"],
    { name: "VBAT reservoir", does: "Two 100 µF low-ESR tantalum capacitors hold the voltage up during transmit bursts, and at each VBAT pin pair a 100 nF / 33 pF / 10 pF ceramic set filters RF noise, as the datasheet recommends. D1 is a TVS diode (4.7 V stand-off, to be selected) against surges." },
    { name: "مخزن VBAT", does: "دو خازن تانتالیوم ۱۰۰ میکروفاراد با مقاومت سری کم، ولتاژ را هنگام ارسال نگه می‌دارند و کنار هر جفت پایهٔ VBAT یک دستهٔ سرامیکی ۱۰۰ نانو / ۳۳ پیکو / ۱۰ پیکوفاراد نویز رادیویی را می‌گیرد، طبق توصیهٔ دیتاشیت. D1 دیود TVS (ولتاژ کار ۴٫۷، هنوز انتخاب نشده) در برابر ضربه است." },
    [{ en: "The voltage must never drop below 3.3 V in a burst", fa: "ولتاژ هنگام ارسال هرگز نباید زیر ۳٫۳ ولت بیفتد" }], 30),
  C("vddext", "module", ["C9"],
    { name: "VDD_EXT decoupling", does: "The module's own 1.8 V output (50 mA max) with its 2.2 µF capacitor. It powers the pull-ups and the module side of the level shifters, so they are off whenever the module is off." },
    { name: "خازن VDD_EXT", does: "خروجی ۱٫۸ ولت خود ماژول (حداکثر ۵۰ میلی‌آمپر) با خازن ۲٫۲ میکروفاراد. مقاومت‌های بالاکش و طرف ماژولِ مبدل‌های سطح را تغذیه می‌کند، پس هر وقت ماژول خاموش است آن‌ها هم خاموش‌اند." }, [], 30),

  // ---------------- control and level shifting ----------------
  C("pwrkey", "logic", ["Q1", "R1", "R2", "C16"],
    { name: "PWRKEY driver", does: "MODEM_EN from the ESP32 (GPIO9) turns Q1 on, which pulls PWRKEY low. Holding it for at least 2 s switches the module on or off; R2 keeps Q1 off while the line floats, and the carrier's 100 kΩ keeps MODEM_EN low at boot." },
    { name: "راه‌انداز PWRKEY", does: "خط MODEM_EN از ESP32 ‏(GPIO9) ترانزیستور Q1 را روشن می‌کند و PWRKEY پایین کشیده می‌شود. نگه داشتن آن به مدت دست‌کم ۲ ثانیه ماژول را روشن یا خاموش می‌کند؛ R2 ترانزیستور را وقتی خط رها است خاموش نگه می‌دارد و مقاومت ۱۰۰ کیلواهم بُرد حامل MODEM_EN را هنگام راه‌اندازی پایین نگه می‌دارد." },
    [{ en: "Open collector, as datasheet Fig. 10", fa: "کلکتور باز، مانند شکل ۱۰ دیتاشیت" }], 300),
  C("resetn", "logic", ["Q2", "R3", "R4"],
    { name: "RESET_N driver", does: "MODEM_RESET (GPIO10) drives Q2, which pulls the module's active-low RESET_N. A last resort when the module stops answering AT commands." },
    { name: "راه‌انداز RESET_N", does: "خط MODEM_RESET ‏(GPIO10) ترانزیستور Q2 را می‌راند که پایهٔ RESET_N (فعال با سطح پایین) ماژول را پایین می‌کشد. آخرین راه وقتی ماژول به فرمان‌های AT پاسخ نمی‌دهد." }, [], 300),
  C("shift", "logic", ["Q3", "Q4", "Q5", "R5", "R6", "R7"],
    { name: "3.3 V ↔ 1.8 V level shifters", does: "Three N-MOSFETs with their gates on VDD_EXT translate the UART (MODEM_TXD → MAIN_RXD, MAIN_TXD → MODEM_RXD) and the STATUS line. R5–R7 pull the 1.8 V side up to VDD_EXT." },
    { name: "مبدل‌های سطح ۳٫۳ ↔ ۱٫۸ ولت", does: "سه ماسفت N که گیت آن‌ها به VDD_EXT وصل است، خطوط UART ‏(MODEM_TXD ← MAIN_RXD و MAIN_TXD → MODEM_RXD) و خط STATUS را بین دو سطح ولتاژ جابه‌جا می‌کنند. R5 تا R7 طرف ۱٫۸ ولت را به VDD_EXT بالا می‌کشند." },
    [{ en: "Review item: the 3.3 V side relies on the ESP32's internal pull-ups (J6 carries no 3V3)", fa: "مورد بازبینی: طرف ۳٫۳ ولت به مقاومت بالاکش داخلی ESP32 متکی است (J6 خط ۳٫۳ ولت ندارد)" }, { en: "DMG2302U: gate threshold ≤ 1.0 V for a 1.8 V gate", fa: "DMG2302U: آستانهٔ گیت حداکثر ۱ ولت برای گیت ۱٫۸ ولتی" }], 10),
  C("netled", "logic", ["Q6", "R8", "R9", "R10", "D2"],
    { name: "Network LED", does: "NET_STATUS is a weak 1.8 V output, so it drives the green LED through Q6; R10 (1 kΩ) from VBAT sets about 1.8 mA. The blink pattern shows searching, registered and data transfer." },
    { name: "چراغ شبکه", does: "خروجی NET_STATUS ضعیف و ۱٫۸ ولتی است، پس LED سبز را از طریق Q6 روشن می‌کند؛ R10 (۱ کیلواهم) از VBAT جریان را حدود ۱٫۸ میلی‌آمپر نگه می‌دارد. الگوی چشمک‌زدن جست‌وجوی شبکه، ثبت‌شدن و انتقال داده را نشان می‌دهد." }, [], 300),

  // ---------------- SIM and antenna ----------------
  C("sim", "sim", ["J3"],
    { name: "micro-SIM holder", does: "A push-push 3FF holder. The module powers the card itself (USIM_VDD) and picks 1.8 V or 3.0 V automatically." },
    { name: "جای سیم‌کارت میکرو", does: "نگه‌دارندهٔ فشاری اندازهٔ 3FF. خود ماژول کارت را تغذیه می‌کند (USIM_VDD) و ۱٫۸ یا ۳٫۰ ولت را خودکار انتخاب می‌کند." },
    [{ en: "JAE SF53S006VCBR2000", fa: "JAE SF53S006VCBR2000" }], 300),
  C("simnet", "sim", ["U2", "R11", "R12", "R13", "R14", "C10", "C11", "C12", "C13"],
    { name: "SIM line protection", does: "Datasheet section 3.8, part by part: 0 Ω series resistors for debugging, 33 pF capacitors against GSM 900 interference, a 10 kΩ pull-up on DATA, 100 nF on USIM_VDD, and U2, an ESD224 array of only 0.5 pF (the limit is 15 pF), all next to the holder." },
    { name: "حفاظت خطوط سیم‌کارت", does: "بخش ۳٫۸ دیتاشیت، قطعه به قطعه: مقاومت‌های صفر اهم سری برای عیب‌یابی، خازن‌های ۳۳ پیکوفاراد در برابر تداخل GSM 900، بالاکش ۱۰ کیلواهم روی DATA، خازن ۱۰۰ نانو روی USIM_VDD و U2، آرایهٔ ESD224 با ظرفیت فقط ۰٫۵ پیکوفاراد (حد مجاز ۱۵ پیکوفاراد)، همه کنار نگه‌دارنده." }, [], 300),
  C("rf", "sim", ["J4", "R15", "C14", "C15"],
    { name: "Antenna: π network and u.FL", does: "The module's ANT_MAIN pad runs on a short 50 Ω line to the u.FL connector for an external LTE antenna. R15 (0 Ω) and the two empty shunt pads form a π network for tuning once the real antenna is known." },
    { name: "آنتن: شبکهٔ π و کانکتور u.FL", does: "پد ANT_MAIN ماژول با یک خط کوتاه ۵۰ اهمی به کانکتور u.FL برای آنتن LTE بیرونی می‌رسد. R15 (صفر اهم) و دو جای خالیِ خازن موازی یک شبکهٔ π می‌سازند تا پس از انتخاب آنتن واقعی تنظیم شود." },
    [{ en: "C14, C15 not mounted by default", fa: "C14 و C15 به‌طور پیش‌فرض نصب نمی‌شوند" }], 160),

  // ---------------- carrier link and bench ----------------
  C("j1", "bench", ["J1"],
    { name: "Socket J1 (to carrier J6)", does: "An 8-way socket under the board that plugs onto the carrier's J6 header, pin for pin: 1 MODEM_VIN, 2 GND, 3 MODEM_TXD, 4 MODEM_RXD, 5 MODEM_EN, 6 MODEM_RESET, 7 MODEM_STATUS, 8 GND." },
    { name: "سوکت J1 (به J6 بُرد حامل)", does: "سوکت هشت‌پایه زیر بُرد که پایه‌به‌پایه روی اتصال J6 بُرد حامل می‌نشیند: ۱ MODEM_VIN، ۲ زمین، ۳ MODEM_TXD، ۴ MODEM_RXD، ۵ MODEM_EN، ۶ MODEM_RESET، ۷ MODEM_STATUS، ۸ زمین." },
    [{ en: "A netlist check confirms the pin-out matches J6", fa: "بررسی نت‌لیست یکسان بودن ترتیب پایه‌ها با J6 را تأیید می‌کند" }], 10, 0.55),
  C("j2", "bench", ["J2"],
    { name: "Direct VBAT input J2 (not fitted)", does: "A spare 2-pin header for a short, heavy bench lead straight to VBAT. Fit it only if the carrier's J7 supply is not used: two supplies must never run in parallel." },
    { name: "ورودی مستقیم VBAT ‏(J2، نصب نمی‌شود)", does: "اتصال دوپایهٔ یدکی برای یک سیم کوتاه و ضخیم آزمایشگاهی مستقیم به VBAT. فقط اگر از منبع J7 بُرد حامل استفاده نمی‌شود نصب شود؛ دو منبع هرگز نباید موازی کار کنند." }, [], 10),
  C("boot", "bench", ["R16"],
    { name: "USB download jumper", does: "Firmware updates for the module go over its USB pins, brought out to test pads. Bridging the solder jumper next to R16 (4.7 kΩ to VDD_EXT) before power-up forces USB download mode; at normal start-up it must stay open." },
    { name: "جامپر بارگذاری از USB", does: "به‌روزرسانی فِرم‌ور ماژول از پایه‌های USB آن انجام می‌شود که روی نقاط آزمون آمده‌اند. وصل کردن جامپر لحیمی کنار R16 (۴٫۷ کیلواهم به VDD_EXT) پیش از روشن شدن، حالت بارگذاری USB را اجباری می‌کند؛ در راه‌اندازی عادی باید باز بماند." },
    [{ en: "Test pads: USB VBUS, D+, D−, VDD_EXT, debug TX/RX (1.8 V), VBAT, GND", fa: "نقاط آزمون: VBUS، ‏D+، ‏D−، VDD_EXT، سریال عیب‌یابی (۱٫۸ ولت)، VBAT و زمین" }], 10),
];

export const UI = {
  overviewKicker: { en: "Modem daughterboard v0.1 · exploded", fa: "بُرد مودم نسخهٔ ۰٫۱ · نمای انفجاری" },
  overviewTitle: { en: "The board that talks to the network", fa: "بُردی که با شبکه حرف می‌زند" },
  overviewBody: {
    en: "A plug-in board for the Quectel EC200U-EU LTE Cat 1 module, designed in KiCad from the module's hardware design guide: a VBAT plane and reservoir, open-collector power and reset drivers, 1.8 V level shifting, a protected micro-SIM and a 50 Ω antenna line. Its module footprint is provisional, so this is a layout study, not a board to order.",
    fa: "بُردی جداشدنی برای ماژول LTE گربهٔ ۱ مدل Quectel EC200U-EU که در KiCad و بر پایهٔ راهنمای طراحی سخت‌افزار ماژول طراحی شده است: صفحه و مخزن VBAT، راه‌اندازهای روشن‌سازی و ریست با کلکتور باز، تبدیل سطح ۱٫۸ ولت، سیم‌کارت میکرو با حفاظت و خط آنتن ۵۰ اهمی. ردپای ماژول موقت است؛ پس این یک مطالعهٔ چیدمان است، نه بُردی برای سفارش ساخت.",
  },
  hint: { en: "Drag to turn · scroll to zoom · click any part or layer · ↑ ↓ open and close · [ ] previous and next · L language · T tour", fa: "برای چرخاندن بکشید · برای بزرگ‌نمایی اسکرول کنید · روی هر قطعه یا لایه کلیک کنید · ↑ ↓ باز و بسته · [ ] قبلی و بعدی · L زبان · T تور" },
};

export const META = {
  file: "modem",
  title: { en: "Modem board v0.1 — exploded", fa: "بُرد مودم نسخهٔ ۰٫۱ — نمای انفجاری" },
  subtitle: { en: "EC200U-EU · new KiCad design · provisional footprint", fa: "EC200U-EU · طراحی تازه در KiCad · ردپای موقت" },
  badge: [{ en: "KiCad v0.1-draft · 75 × 50 mm · 4 layers · EC200U footprint PROVISIONAL", fa: "KiCad نسخهٔ 0.1-draft · ‏۷۵ × ۵۰ میلی‌متر · ۴ لایه · ردپای EC200U موقت" }, { en: "Bench use only — never connect to a live gas meter, gas line or mains", fa: "فقط برای میز آزمایش — هرگز به کنتور، لولهٔ گاز یا برق شهر وصل نشود" }],
  htmlTitle: "SGM Modem Board",
  description: "Exploded, turnable bilingual model of the Smart Gas Meter EC200U modem daughterboard v0.1 built from its KiCad layout.",
};
