// Bilingual notes for the carrier board v0.2 exploded model. Every value, reference and net comes from
// hardware/kicad/design_v02.py (schematic freeze candidate rc1) and the routed board; nothing is invented.
// Each item selects every drawn part whose name starts with one of `match`; `x` = explode needed to see it.

export const SECTIONS = [
  { id: "stack", en: "Layer stack (4 layers, 1.6 mm)", fa: "لایه‌های بُرد (۴ لایه، ۱٫۶ میلی‌متر)", noteEn: "Slabs are drawn thicker and pulled apart so each layer's real artwork can be seen.", noteFa: "لایه‌ها ضخیم‌تر و جدا از هم کشیده شده‌اند تا طرح واقعی هر لایه دیده شود." },
  { id: "power", en: "USB input and 3.3 V power", fa: "ورودی USB و تغذیهٔ ۳٫۳ ولت" },
  { id: "mcu", en: "ESP32-S3 and its support", fa: "ESP32-S3 و قطعه‌های کنار آن" },
  { id: "io", en: "Lab inputs and outputs", fa: "ورودی‌ها و خروجی‌های آزمایشگاهی" },
  { id: "modem", en: "Modem interface", fa: "رابط مودم" },
];

const L = (id, x, spin, en, fa, facts = []) => ({ id, sec: "stack", match: [`layer.${id}`], x, spin, en, fa, facts });
const C = (id, sec, refs, en, fa, facts = [], spin = 25) => ({ id, sec, match: refs.map((r) => `cmp.${r}.`), x: 0.45, spin, en, fa, facts });

export const ITEMS = [
  // ---------------- layer stack ----------------
  L("topmask", 1, 25,
    { name: "Top solder mask and silkscreen", does: "The green lacquer that covers the top copper except where parts are soldered, and the white printing on it: reference designators and the header labels PULSE, TAMPER, I2C, UART, MODEM IF and VMODEM, plus the line LAB PROTOTYPE – NO GAS-LINE CONNECTION." },
    { name: "لاک محافظ و چاپ رویی", does: "لاک سبزی که مس رویی را جز در محل لحیم قطعه‌ها می‌پوشاند و نوشته‌های سفید روی آن: نام قطعه‌ها و برچسب اتصال‌ها PULSE، TAMPER، I2C، UART، MODEM IF و VMODEM، و جملهٔ «نمونهٔ آزمایشگاهی – بدون اتصال به لولهٔ گاز»." },
    [{ en: "Openings in the mask = the copper pads below", fa: "دریچه‌های لاک = پدهای مسی زیر آن" }]),
  L("fcu", 1, 25,
    { name: "Top copper (F.Cu)", does: "The main signal layer: the pads for every part and most of the tracks. Each ground pad drops straight to the inner ground plane through its own short track and via." },
    { name: "مس رویی (F.Cu)", does: "لایهٔ اصلی سیگنال: پد همهٔ قطعه‌ها و بیشتر مسیرها. هر پد زمین با یک مسیر کوتاه و یک ویا مستقیم به صفحهٔ زمین داخلی می‌رود." },
    [{ en: "USB D+/D− pair: 0.2 mm tracks, 0.2 mm gap", fa: "زوج USB ‏D+/D−: مسیر ۰٫۲ و فاصلهٔ ۰٫۲ میلی‌متر" }, { en: "Tracks 0.25 mm; power 0.4 mm", fa: "مسیرها ۰٫۲۵؛ تغذیه ۰٫۴ میلی‌متر" }]),
  L("in1", 1, 25,
    { name: "Inner layer 1: ground plane", does: "One unbroken copper sheet at 0 V. It is the return path under every top-layer signal, which keeps the USB pair and the buck converter's fast edges quiet. No tracks are routed on it, by design." },
    { name: "لایهٔ داخلی ۱: صفحهٔ زمین", does: "یک ورقهٔ مسی یکپارچه با ولتاژ صفر. مسیر برگشت جریانِ همهٔ سیگنال‌های لایهٔ رو است و لبه‌های سریع USB و مبدل باک را آرام نگه می‌دارد. عمداً هیچ مسیری روی آن کشیده نشده است." },
    [{ en: "The notch at the top edge is the ESP32 antenna keep-out", fa: "بریدگی لبهٔ بالا ناحیهٔ ممنوعهٔ آنتن ESP32 است" }]),
  L("in2", 1, 25,
    { name: "Inner layer 2: 3.3 V pour", does: "A copper area at +3V3 that feeds the module and the pull-ups, with a few signal tracks where needed. It also stops short of the antenna end of the module." },
    { name: "لایهٔ داخلی ۲: سطح ۳٫۳ ولت", does: "سطح مسی با ولتاژ ‎+3V3 که ماژول و مقاومت‌های بالاکش را تغذیه می‌کند و در صورت نیاز چند مسیر سیگنال هم دارد. این لایه هم پیش از انتهای آنتن ماژول تمام می‌شود." }),
  L("bcu", 1, 25,
    { name: "Bottom copper (B.Cu)", does: "The second signal layer, for tracks that must cross others, joined to the top through vias. The through-hole header pins pass through every layer." },
    { name: "مس زیرین (B.Cu)", does: "لایهٔ دوم سیگنال برای مسیرهایی که باید از روی هم عبور کنند و با ویا به لایهٔ رو وصل می‌شوند. پایه‌های اتصال‌های سوراخ‌دار از همهٔ لایه‌ها می‌گذرند." }),
  L("botmask", 1, 25,
    { name: "Bottom solder mask and silkscreen", does: "Green mask on the underside and the line \"Smart Gas Meter IoT carrier v0.2 – bench use only\", seen here from above, so it reads mirrored." },
    { name: "لاک و چاپ زیرین", does: "لاک سبز زیر بُرد و جملهٔ «بُرد حامل کنتور هوشمند گاز نسخهٔ ۰٫۲ – فقط برای میز آزمایش»؛ چون از بالا دیده می‌شود، وارونه خوانده می‌شود." },
    [{ en: "Four M3 mounting holes in the corners", fa: "چهار سوراخ نصب M3 در گوشه‌ها" }]),

  // ---------------- USB input and power ----------------
  C("usb", "power", ["J1", "R1", "R2"],
    { name: "USB-C input J1", does: "Bench power and the ESP32-S3's native USB for flashing and logs. R1 and R2 (5.1 kΩ) on CC1/CC2 tell the charger this is a power sink, so it supplies 5 V." },
    { name: "ورودی USB-C ‏(J1)", does: "تغذیه روی میز آزمایش و USB داخلی ESP32-S3 برای بارگذاری فِرم‌ور و گزارش‌ها. مقاومت‌های R1 و R2 (۵٫۱ کیلواهم) روی CC1/CC2 به شارژر می‌گویند این دستگاه مصرف‌کننده است تا ۵ ولت بدهد." },
    [{ en: "GCT USB4105-GF-A", fa: "GCT USB4105-GF-A" }], 20),
  C("protect", "power", ["F1", "D1", "U2"],
    { name: "Input protection", does: "F1 is a resettable PTC fuse (0.75 A hold) in the VBUS line; D1, an SMAJ6.5CA TVS diode, clamps surges on the 5 V rail; U2, a USBLC6-2SC6, shields the D+/D− lines from static discharge right at the connector." },
    { name: "حفاظت ورودی", does: "F1 فیوز PTC خودترمیم (جریان نگهداری ۰٫۷۵ آمپر) روی خط VBUS است؛ D1 دیود TVS مدل SMAJ6.5CA ضربه‌های ولتاژ را روی ریل ۵ ولت مهار می‌کند؛ U2 (USBLC6-2SC6) خطوط D+/D− را درست کنار کانکتور در برابر تخلیهٔ الکتریسیتهٔ ساکن محافظت می‌کند." },
    [], 20),
  C("buck", "power", ["U3", "L1", "C1", "C2", "C3", "C4", "C5"],
    { name: "3.3 V buck converter", does: "U3, an AP63203 fixed 3.3 V buck regulator, turns 5 V into 3.3 V for the whole board. C1/C2 are its input capacitors, C3 the bootstrap capacitor, L1 (3.9 µH) the inductor and C4/C5 (2 × 22 µF) the output capacitors, all from the datasheet's typical circuit, in a tight loop in the corner far from the pulse input." },
    { name: "مبدل باک ۳٫۳ ولت", does: "U3 رگولاتور باک AP63203 با خروجی ثابت ۳٫۳ ولت است و ۵ ولت را برای کل بُرد به ۳٫۳ ولت تبدیل می‌کند. C1/C2 خازن‌های ورودی، C3 خازن بوت‌استرپ، L1 (۳٫۹ میکروهانری) سلف و C4/C5 (دو ۲۲ میکروفاراد) خازن‌های خروجی‌اند؛ همه طبق مدار نمونهٔ دیتاشیت و در حلقه‌ای فشرده در گوشه‌ای دور از ورودی پالس." },
    [{ en: "Diodes Inc. AP63203WU-7 · Sunlord SWPA4030S3R9MT", fa: "Diodes Inc. AP63203WU-7 · Sunlord SWPA4030S3R9MT" }], 20),

  // ---------------- ESP32-S3 ----------------
  C("esp32", "mcu", ["U1"],
    { name: "ESP32-S3-WROOM-1-N8", does: "The microcontroller module: it counts pulses, keeps the total in flash, closes each Jalali season and drives the modem. Its printed antenna sits at the board edge, and every copper layer is kept clear underneath it." },
    { name: "ماژول ESP32-S3-WROOM-1-N8", does: "ماژول میکروکنترلر: پالس‌ها را می‌شمارد، مجموع را در فلش نگه می‌دارد، هر فصل شمسی را می‌بندد و مودم را راه می‌اندازد. آنتن چاپی آن کنار لبهٔ بُرد است و زیر آن در هیچ لایه‌ای مس نیست." },
    [{ en: "8 MB flash · Wi-Fi + Bluetooth LE", fa: "۸ مگابایت فلش · Wi-Fi و بلوتوث کم‌مصرف" }], 30),
  C("decouple", "mcu", ["C6", "C7"],
    { name: "Module decoupling", does: "C6 (10 µF) and C7 (100 nF) at the module's 3.3 V pin supply the current spikes of Wi-Fi transmit bursts." },
    { name: "خازن‌های کنار ماژول", does: "C6 (۱۰ میکروفاراد) و C7 (۱۰۰ نانوفاراد) کنار پایهٔ ۳٫۳ ولت ماژول، جریان‌های لحظه‌ای هنگام ارسال Wi-Fi را تأمین می‌کنند." }, [], 30),
  C("reset", "mcu", ["R3", "C8", "SW1"],
    { name: "Reset: EN delay and RESET button", does: "R3 (10 kΩ) and C8 (1 µF) hold the chip's EN pin low for a moment at power-up, as Espressif recommends; SW1 pulls EN low to reset by hand." },
    { name: "ریست: تأخیر EN و دکمهٔ RESET", does: "R3 (۱۰ کیلواهم) و C8 (۱ میکروفاراد) پایهٔ EN را هنگام روشن شدن کمی پایین نگه می‌دارند، طبق توصیهٔ Espressif؛ SW1 با پایین کشیدن EN ریست دستی می‌کند." }, [], 30),
  C("boot", "mcu", ["R4", "SW2"],
    { name: "BOOT button", does: "R4 (10 kΩ) keeps GPIO0 high so the chip runs from flash. Holding SW2 during reset pulls it low for USB download mode." },
    { name: "دکمهٔ BOOT", does: "R4 (۱۰ کیلواهم) پایهٔ GPIO0 را بالا نگه می‌دارد تا تراشه از فلش اجرا شود. نگه داشتن SW2 هنگام ریست آن را پایین می‌کشد و حالت بارگذاری از USB فعال می‌شود." }, [], 30),

  // ---------------- lab I/O ----------------
  C("pulse", "io", ["J2", "R5", "R6", "C9"],
    { name: "Pulse input J2", does: "A synthetic 3.3 V pulse or a dry contact to ground enters here. R5 (10 kΩ) pulls the line high, R6 (1 kΩ) limits current into GPIO4, and C9 is a filter footprint left empty by default." },
    { name: "ورودی پالس J2", does: "پالس شبیه‌سازی‌شدهٔ ۳٫۳ ولت یا یک کنتاکت خشک به زمین اینجا وارد می‌شود. R5 (۱۰ کیلواهم) خط را بالا نگه می‌دارد، R6 (۱ کیلواهم) جریان ورودی به GPIO4 را محدود می‌کند و C9 جای خالی یک فیلتر است که به‌طور پیش‌فرض نصب نمی‌شود." },
    [{ en: "Bench only: never wire to a live gas meter", fa: "فقط روی میز آزمایش: هرگز به کنتور گاز واقعی وصل نشود" }], 35),
  C("led", "io", ["R7", "D2"],
    { name: "Status LED D2", does: "A red LED driven from GPIO5 through R7 (1 kΩ), about 1.3 mA. It blinks with pulses and connection state during tests." },
    { name: "چراغ وضعیت D2", does: "یک LED قرمز که GPIO5 از طریق R7 (۱ کیلواهم) با حدود ۱٫۳ میلی‌آمپر روشنش می‌کند. هنگام آزمایش با پالس‌ها و وضعیت اتصال چشمک می‌زند." }, [], 35),
  C("tamper", "io", ["J3", "R8", "R9", "C10"],
    { name: "Tamper input J3", does: "The enclosure switch closes to ground while the lid is shut. R8 pulls the line high, so an open lid or a cut wire reads high on GPIO15; R9 and C10 debounce it (about 1 ms). The flag is advisory only." },
    { name: "ورودی ضددستکاری J3", does: "کلید محفظه تا وقتی در بسته است به زمین وصل است. R8 خط را بالا می‌کشد، پس درِ باز یا سیم بریده روی GPIO15 سطح بالا می‌خواند؛ R9 و C10 لرزش کلید را (حدود ۱ میلی‌ثانیه) صاف می‌کنند. این هشدار فقط جنبهٔ اطلاع‌رسانی دارد." }, [], 35),
  C("i2c", "io", ["J4", "R10", "R11"],
    { name: "I²C expansion J4", does: "3.3 V, SDA, SCL and ground for optional sensors, with R10/R11 (4.7 kΩ) pull-ups on GPIO6/GPIO7." },
    { name: "درگاه توسعهٔ I²C ‏(J4)", does: "۳٫۳ ولت، SDA، SCL و زمین برای حسگرهای اختیاری، با مقاومت‌های بالاکش R10/R11 (۴٫۷ کیلواهم) روی GPIO6/GPIO7." }, [], 35),
  C("uart", "io", ["J5"],
    { name: "Debug UART J5", does: "TXD0, RXD0 and ground of the module's UART0 at 3.3 V for a serial console. It has no power pin, so a connected adapter cannot back-feed the board." },
    { name: "درگاه سریال عیب‌یابی J5", does: "TXD0، RXD0 و زمینِ UART0 ماژول با سطح ۳٫۳ ولت برای کنسول سریال. پایهٔ تغذیه ندارد تا مبدل وصل‌شده بُرد را از بیرون تغذیه نکند." }, [], 35),

  // ---------------- modem interface ----------------
  C("j6", "modem", ["J6"],
    { name: "Modem header J6", does: "Eight pins to the plug-in modem board: 1 MODEM_VIN, 2 GND, 3 MODEM_TXD, 4 MODEM_RXD, 5 MODEM_EN, 6 MODEM_RESET, 7 MODEM_STATUS, 8 GND. Logic is 3.3 V; the modem board does the level shifting and the module's power design." },
    { name: "اتصال مودم J6", does: "هشت پایه به بُرد مودم جداشدنی: ۱ MODEM_VIN، ۲ زمین، ۳ MODEM_TXD، ۴ MODEM_RXD، ۵ MODEM_EN، ۶ MODEM_RESET، ۷ MODEM_STATUS، ۸ زمین. منطق ۳٫۳ ولت است؛ تبدیل سطح ولتاژ و طراحی تغذیهٔ ماژول بر عهدهٔ بُرد مودم است." },
    [{ en: "GPIO17 TXD · GPIO18 RXD · GPIO9 EN · GPIO10 RESET · GPIO11 STATUS", fa: "GPIO17 ارسال · GPIO18 دریافت · GPIO9 روشن‌سازی · GPIO10 ریست · GPIO11 وضعیت" }], 10),
  C("j7", "modem", ["J7", "R12", "R13"],
    { name: "Modem supply J7 and safe defaults", does: "J7 brings in a separate, current-limited bench supply for the modem (MODEM_VIN, 3.8 V for the EC200U); it is never taken from +3V3. R12 and R13 (100 kΩ) hold MODEM_EN and MODEM_RESET low, so the modem stays off while the ESP32 boots." },
    { name: "تغذیهٔ مودم J7 و حالت امن پیش‌فرض", does: "J7 یک منبع جدا و با محدودیت جریان برای مودم وارد می‌کند (MODEM_VIN، برای EC200U ‏۳٫۸ ولت)؛ هرگز از ‎+3V3 گرفته نمی‌شود. R12 و R13 (۱۰۰ کیلواهم) خطوط MODEM_EN و MODEM_RESET را پایین نگه می‌دارند تا مودم هنگام راه‌اندازی ESP32 خاموش بماند." }, [], 10),
];

export const UI = {
  overviewKicker: { en: "Carrier board v0.2 · exploded", fa: "بُرد حامل نسخهٔ ۰٫۲ · نمای انفجاری" },
  overviewTitle: { en: "Four copper layers, 48 parts, one job", fa: "چهار لایهٔ مس، ۴۸ قطعه، یک کار" },
  overviewBody: {
    en: "This is the real KiCad board: every part sits at its pick-and-place position and every layer shows its own routed copper. Pull it apart to see the ground plane, the 3.3 V pour and the two signal layers between the solder masks.",
    fa: "این همان بُرد واقعی KiCad است: هر قطعه در مختصات مونتاژ خودش نشسته و هر لایه مس مسیرکشی‌شدهٔ خودش را نشان می‌دهد. بُرد را باز کنید تا صفحهٔ زمین، سطح ۳٫۳ ولت و دو لایهٔ سیگنالِ میان دو لاک محافظ را ببینید.",
  },
  hint: { en: "Drag to turn · scroll to zoom · click any part or layer · ↑ ↓ open and close · [ ] previous and next · L language · T tour", fa: "برای چرخاندن بکشید · برای بزرگ‌نمایی اسکرول کنید · روی هر قطعه یا لایه کلیک کنید · ↑ ↓ باز و بسته · [ ] قبلی و بعدی · L زبان · T تور" },
};

export const META = {
  file: "carrier",
  title: { en: "Carrier board v0.2 — exploded", fa: "بُرد حامل نسخهٔ ۰٫۲ — نمای انفجاری" },
  subtitle: { en: "Real KiCad layout · every layer, every part", fa: "طرح واقعی KiCad · همهٔ لایه‌ها و قطعه‌ها" },
  badge: [{ en: "KiCad v0.2-rc1 · 100 × 70 mm · 4 layers · not released for fabrication", fa: "KiCad نسخهٔ 0.2-rc1 · ‏۱۰۰ × ۷۰ میلی‌متر · ۴ لایه · هنوز برای ساخت آزاد نشده" }, { en: "Bench use only — never connect to a live gas meter, gas line or mains", fa: "فقط برای میز آزمایش — هرگز به کنتور، لولهٔ گاز یا برق شهر وصل نشود" }],
  htmlTitle: "SGM Carrier Board",
  description: "Exploded, turnable bilingual model of the Smart Gas Meter carrier board v0.2 built from its real KiCad layout.",
};
