// Bilingual part notes for the exploded model. Each item selects every part whose name starts with one of `match`.
// `x` is how far the model must come apart to show the item; `spin` is a good turntable angle to see it.
// Facts about the SGM device come from the repository (board v0.2 BOM, board.h, firmware README, hardware decisions).
// The G4 internals are generic: every diaphragm meter differs in detail.

export const SECTIONS = [
  { id: "meter", en: "G4 diaphragm meter", fa: "کنتور دیافراگمی G4", noteEn: "Generic illustration of how a household diaphragm meter works, not one maker's design.", noteFa: "تصویری عمومی از سازوکار کنتورهای دیافراگمی خانگی؛ طرح هیچ سازندهٔ خاصی نیست." },
  { id: "index", en: "Index and pulse output", fa: "شمارنده و خروجی پالس", noteEn: "Where the mechanical count becomes an electrical pulse.", noteFa: "جایی که شمارش مکانیکی به پالس الکتریکی تبدیل می‌شود." },
  { id: "device", en: "SGM device (bench prototype)", fa: "دستگاه SGM (نمونهٔ آزمایشگاهی)", noteEn: "Board v0.2 with the v0.3 recommendations (battery, modem board). The enclosure is a concept.", noteFa: "بُرد نسخهٔ ۰٫۲ همراه با پیشنهادهای نسخهٔ ۰٫۳ (باتری و بُرد مودم). محفظه طرح مفهومی است." },
];

export const ITEMS = [
  // ---------------- meter ----------------
  {
    id: "case-upper", sec: "meter", match: ["case.upper"], x: 0, spin: -30,
    en: { name: "Upper case", does: "The top half of the sealed steel housing. It carries the data plate and keeps gas inside: the whole mechanism works in gas at supply pressure." },
    fa: { name: "پوستهٔ بالایی", does: "نیمهٔ بالای بدنهٔ فولادی و آب‌بندی‌شده. پلاک مشخصات روی آن است و گاز را درون کنتور نگه می‌دارد؛ کل سازوکار درون گازِ تحت فشار شبکه کار می‌کند." },
    facts: [{ en: "Pressed steel, crimped to the lower case", fa: "ورق فولادی پرس‌شده، پرچ‌شده به پوستهٔ پایینی" }, { en: "Data plate: G4 · Qmax 6 m³/h", fa: "پلاک: G4 · بیشینهٔ دبی ۶ مترمکعب در ساعت" }],
  },
  {
    id: "ports", sec: "meter", match: ["port."], x: 0, spin: -30,
    en: { name: "Inlet and outlet unions", does: "Gas from the street pipe enters through one union and leaves through the other to the home. Everything that flows between them is measured." },
    fa: { name: "اتصال‌های ورودی و خروجی", does: "گاز از لولهٔ شبکه از یک اتصال وارد و از دیگری به سمت مصرف‌کننده خارج می‌شود. هر چه بین این دو جریان یابد اندازه‌گیری می‌شود." },
    facts: [{ en: "Threaded unions on top of the case", fa: "مهره‌ماسوره‌های رزوه‌ای روی بدنه" }],
  },
  {
    id: "case-lower", sec: "meter", match: ["case.lower"], x: 0.5, spin: -30,
    en: { name: "Lower case", does: "The bottom half of the housing. The measuring unit sits inside it." },
    fa: { name: "پوستهٔ پایینی", does: "نیمهٔ پایینی بدنه که واحد اندازه‌گیری درون آن قرار می‌گیرد." },
    facts: [],
  },
  {
    id: "block", sec: "meter", match: ["unit.block"], x: 1, spin: -30,
    en: { name: "Measuring unit body", does: "The central casting with two measuring chambers, one on each side. Each chamber is split by a diaphragm, so four compartments fill and empty in turn." },
    fa: { name: "بدنهٔ واحد اندازه‌گیری", does: "قطعهٔ مرکزی با دو محفظهٔ اندازه‌گیری در دو طرف. دیافراگم هر محفظه را دو نیم می‌کند؛ پس چهار بخش به نوبت پر و خالی می‌شوند." },
    facts: [{ en: "Positive displacement: counts volume, not speed", fa: "جابه‌جایی مثبت: حجم را می‌شمارد، نه سرعت را" }],
  },
  {
    id: "diaphragm", sec: "meter", match: ["unit.diaphragm", "unit.plate"], x: 1, spin: -30,
    en: { name: "Diaphragms", does: "Flexible membranes pushed back and forth as gas fills one side and then the other. Every full stroke moves the same fixed volume, which is what the meter counts." },
    fa: { name: "دیافراگم‌ها", does: "غشاهای انعطاف‌پذیری که با پر شدن یک طرف و سپس طرف دیگر، به جلو و عقب رانده می‌شوند. هر رفت‌وبرگشت کامل، حجم ثابتی را جابه‌جا می‌کند و کنتور همین را می‌شمارد." },
    facts: [{ en: "A stiff plate in the middle drives the flag rod", fa: "صفحهٔ سفت وسط، میلهٔ پرچمی را حرکت می‌دهد" }],
  },
  {
    id: "covers", sec: "meter", match: ["unit.cover"], x: 1, spin: -30,
    en: { name: "Chamber covers", does: "Close the outer side of each measuring chamber and hold the diaphragm's rim gas-tight." },
    fa: { name: "درپوش محفظه‌ها", does: "طرف بیرونی هر محفظه را می‌بندند و لبهٔ دیافراگم را گازبند نگه می‌دارند." },
    facts: [],
  },
  {
    id: "flags", sec: "meter", match: ["mech.flag", "mech.link"], x: 1, spin: -30,
    en: { name: "Flag rods and link arms", does: "Turn each diaphragm's back-and-forth stroke into a rocking motion at the top, and pass it to the crank." },
    fa: { name: "میله‌های پرچمی و بازوها", does: "حرکت رفت‌وبرگشتی هر دیافراگم را به حرکت نوسانی در بالا تبدیل می‌کنند و به میل‌لنگ می‌رسانند." },
    facts: [{ en: "The two strokes are a quarter-cycle apart, so the crank never stalls", fa: "دو حرکت یک‌چهارم دور اختلاف فاز دارند تا میل‌لنگ هیچ‌وقت نایستد" }],
  },
  {
    id: "crank", sec: "meter", match: ["mech.crank"], x: 1, spin: -30,
    en: { name: "Crank", does: "Turns the rocking motion into rotation. Its shaft drives the valves and the gear train together, so valve timing and the count can never drift apart." },
    fa: { name: "میل‌لنگ", does: "حرکت نوسانی را به چرخش تبدیل می‌کند. محور آن هم سوپاپ‌ها و هم چرخ‌دنده‌ها را می‌چرخاند؛ پس زمان‌بندی سوپاپ و شمارش هرگز از هم جدا نمی‌شوند." },
    facts: [],
  },
  {
    id: "valves", sec: "meter", match: ["mech.grid", "mech.valve"], x: 1, spin: -30,
    en: { name: "Slide valves and valve grid", does: "Driven by the crank, the slide valves open and close ports in the grid, sending gas into the compartment that should fill and letting the full one empty toward the outlet." },
    fa: { name: "سوپاپ‌های کشویی و صفحهٔ سوپاپ", does: "سوپاپ‌ها با میل‌لنگ جابه‌جا می‌شوند و دریچه‌های صفحه را باز و بسته می‌کنند تا گاز به بخشی که باید پر شود برود و بخش پر به سمت خروجی خالی شود." },
    facts: [],
  },
  {
    id: "gear", sec: "meter", match: ["mech.gear", "mech.spindle"], x: 1, spin: -30,
    en: { name: "Gear and drive spindle", does: "Carry the crank's rotation toward the front of the meter, scaled so the index reads cubic metres." },
    fa: { name: "چرخ‌دنده و محور انتقال", does: "چرخش میل‌لنگ را با نسبت مناسب به جلوی کنتور می‌برند تا شمارنده برحسب مترمکعب بخواند." },
    facts: [],
  },
  {
    id: "coupling", sec: "meter", match: ["mech.coupling"], x: 1, spin: -30,
    en: { name: "Magnetic coupling", does: "Passes rotation through the sealed case wall with magnets, so no shaft has to pierce the gas-tight housing." },
    fa: { name: "کوپلینگ مغناطیسی", does: "چرخش را با آهنربا از پشت دیوارهٔ آب‌بندی‌شده عبور می‌دهد تا هیچ محوری لازم نباشد بدنهٔ گازبند را سوراخ کند." },
    facts: [{ en: "Common in modern meters; shown generically", fa: "در کنتورهای جدید رایج است؛ این‌جا به‌صورت عمومی نمایش داده شده" }],
  },
  // ---------------- index ----------------
  {
    id: "index", sec: "index", match: ["index.body", "index.bezel", "index.axle"], x: 0.6, spin: -30,
    en: { name: "Index (counter)", does: "The register the reader sees. It holds the number drums behind a window on the front of the meter." },
    fa: { name: "شمارنده", does: "همان صفحه‌ای که مأمور قرائت می‌بیند. غلتک‌های عددی را پشت پنجرهٔ جلوی کنتور نگه می‌دارد." },
    facts: [],
  },
  {
    id: "drums", sec: "index", match: ["index.drum"], x: 0.6, spin: -30,
    en: { name: "Number drums", does: "Five black drums count whole cubic metres; three red drums count tenths, hundredths and thousandths. Reading here: 00512.347 m³." },
    fa: { name: "غلتک‌های عددی", does: "پنج غلتک مشکی مترمکعب‌های کامل و سه غلتک قرمز دهم، صدم و هزارم مترمکعب را می‌شمارند. عدد نمایش‌داده‌شده: ۰۰۵۱۲٫۳۴۷ مترمکعب." },
    facts: [{ en: "Last drum: 0.001 m³ per digit", fa: "غلتک آخر: هر رقم ۰٫۰۰۱ مترمکعب" }],
  },
  {
    id: "magnet", sec: "index", match: ["index.magnet"], x: 0.6, spin: -20,
    en: { name: "Magnet in the last drum", does: "Turns with the last red drum. One full turn of that drum is 0.01 m³ (10 litres), and the magnet passes the reed switch once on every turn." },
    fa: { name: "آهنربای غلتک آخر", does: "همراه آخرین غلتک قرمز می‌چرخد. هر دور کامل این غلتک ۰٫۰۱ مترمکعب (۱۰ لیتر) است و آهنربا در هر دور یک بار از کنار کلید رید می‌گذرد." },
    facts: [{ en: "1 turn = 1 pulse = 0.01 m³", fa: "۱ دور = ۱ پالس = ۰٫۰۱ مترمکعب" }],
  },
  {
    id: "pulser", sec: "index", match: ["pulser.body", "pulser.boot"], x: 0.3, spin: -30,
    en: { name: "Reed pulser", does: "A small sensor clipped under the index. It turns each pass of the magnet into one electrical pulse, without touching the mechanism or the gas." },
    fa: { name: "پالسر رید", does: "حسگر کوچکی که زیر شمارنده نصب می‌شود. هر عبور آهنربا را بدون تماس با سازوکار یا گاز به یک پالس الکتریکی تبدیل می‌کند." },
    facts: [{ en: "Like the Elster IN-Z61 family", fa: "مشابه خانوادهٔ IN-Z61 شرکت Elster" }, { en: "Optional NC tamper contact (v0.3)", fa: "کنتاکت ضد دست‌کاری اختیاری (نسخهٔ ۰٫۳)" }],
  },
  {
    id: "reed", sec: "index", match: ["pulser.reed"], x: 0.3, spin: -30,
    en: { name: "Reed switch", does: "Two thin blades in a glass tube that close when the magnet is near. The firmware only counts a closure that lasts at least 30 ms, so contact bounce never counts twice." },
    fa: { name: "کلید رید", does: "دو تیغهٔ نازک در لولهٔ شیشه‌ای که با نزدیک شدن آهنربا به هم می‌چسبند. فِرم‌ور فقط بسته‌شدنی را می‌شمارد که دست‌کم ۳۰ میلی‌ثانیه طول بکشد؛ پس لرزش کنتاکت دوبار شمرده نمی‌شود." },
    facts: [{ en: "Debounced in firmware (30 ms)", fa: "حذف لرزش در فِرم‌ور (۳۰ میلی‌ثانیه)" }],
  },
  {
    id: "cable", sec: "index", match: ["pulser.cable"], x: 0.3, spin: -30,
    en: { name: "Pulse cable", does: "Two wires carry the reed contact to the device's pulse input." },
    fa: { name: "کابل پالس", does: "دو سیم، کنتاکت رید را به ورودی پالس دستگاه می‌رسانند." },
    facts: [{ en: "Ends at J2 (PULSE_IN, GPIO4)", fa: "به J2 می‌رسد (PULSE_IN، GPIO4)" }],
  },
  // ---------------- device ----------------
  {
    id: "enclosure", sec: "device", match: ["device.base", "device.mount"], x: 0, spin: 40,
    en: { name: "Enclosure and mount", does: "A sealed box that keeps the electronics dry beside the meter. Concept only: the real enclosure, its sealing and the radio test with it are still open items." },
    fa: { name: "محفظه و پایه", does: "جعبه‌ای آب‌بندی‌شده که قطعات الکترونیکی را کنار کنتور خشک نگه می‌دارد. فعلاً طرح مفهومی است؛ محفظهٔ واقعی، آب‌بندی و آزمون رادیویی آن هنوز باز است." },
    facts: [],
  },
  {
    id: "gland", sec: "device", match: ["device.gland"], x: 0, spin: 40,
    en: { name: "Cable gland", does: "Seals the pulse cable where it enters the enclosure." },
    fa: { name: "گلند کابل", does: "محل ورود کابل پالس به محفظه را آب‌بند می‌کند." },
    facts: [],
  },
  {
    id: "lid", sec: "device", match: ["lid.plate", "lid.lightpipe"], x: 0.35, spin: 40,
    en: { name: "Lid and light pipe", does: "Closes the box. A light pipe brings the status LED to the surface." },
    fa: { name: "درپوش و هدایت‌گر نور", does: "جعبه را می‌بندد. یک هدایت‌گر نور، چراغ وضعیت را به سطح درپوش می‌آورد." },
    facts: [],
  },
  {
    id: "tamper", sec: "device", match: ["device.tamper"], x: 0.4, spin: 40,
    en: { name: "Tamper switch", does: "Held closed by the lid. Opening the lid or cutting the wire raises the TAMPER_IN line, and the device logs it. It is a diagnostic, not proof of tampering." },
    fa: { name: "کلید ضد دست‌کاری", does: "درپوش آن را بسته نگه می‌دارد. باز شدن درپوش یا قطع سیم، خط TAMPER_IN را فعال می‌کند و دستگاه آن را ثبت می‌کند. این یک نشانهٔ تشخیصی است، نه اثبات دست‌کاری." },
    facts: [{ en: "GPIO15 · high = lid open or wire cut", fa: "GPIO15 · سطح بالا = درِ باز یا سیم قطع" }],
  },
  {
    id: "antenna", sec: "device", match: ["lid.antenna"], x: 0.35, spin: 40,
    en: { name: "Antenna", does: "Sends and receives the cellular signal. It connects to the modem board's antenna connector; its placement must be tested inside the real enclosure." },
    fa: { name: "آنتن", does: "سیگنال شبکهٔ موبایل را می‌فرستد و دریافت می‌کند. به کانکتور آنتنِ بُرد مودم وصل است و جای آن باید درون محفظهٔ واقعی آزمایش شود." },
    facts: [],
  },
  {
    id: "modem", sec: "device", match: ["modem.pcb", "modem.module", "modem.ufl"], x: 0.6, spin: 40,
    en: { name: "Modem board", does: "A plug-in board with one footprint for two Quectel modems: BG95-M3 (LTE-M, sleeps between sends) or EC200U-EU (Cat-1, switched off between sends). It uploads readings and sends the SMS fallback." },
    fa: { name: "بُرد مودم", does: "بُردی جداشدنی با یک جای مشترک برای دو مودم Quectel: ‏BG95-M3 (شبکهٔ LTE-M، بین ارسال‌ها می‌خوابد) یا EC200U-EU (شبکهٔ Cat-1، بین ارسال‌ها خاموش می‌شود). خوانش‌ها را بارگذاری می‌کند و پیامک پشتیبان را می‌فرستد." },
    facts: [{ en: "UART AT commands · GPIO17/18, EN 9, RESET 10", fa: "فرمان‌های AT روی UART · GPIO17/18، EN 9، RESET 10" }, { en: "Replaceable, because LTE-M coverage in Iran is unconfirmed", fa: "قابل تعویض، چون پوشش LTE-M در ایران تأیید نشده است" }],
  },
  {
    id: "sim", sec: "device", match: ["modem.sim"], x: 0.6, spin: 40,
    en: { name: "SIM holder", does: "Holds the operator SIM that gives the meter its mobile identity. A registered IoT SIM or an eSIM is chosen with the operator." },
    fa: { name: "جای سیم‌کارت", does: "سیم‌کارت اپراتور را نگه می‌دارد که هویت کنتور در شبکهٔ موبایل است. سیم‌کارت اینترنت اشیای ثبت‌شده یا eSIM با هماهنگی اپراتور انتخاب می‌شود." },
    facts: [],
  },
  {
    id: "esp32", sec: "device", match: ["board.esp32"], x: 0.7, spin: 40,
    en: { name: "ESP32-S3 module", does: "The brain. It counts every pulse, keeps the total safe in flash, closes each Jalali season at 00:00 Tehran time, queues the records and talks to the modem. Sleeping between pulses is the v0.3 power plan." },
    fa: { name: "ماژول ESP32-S3", does: "مغز دستگاه. هر پالس را می‌شمارد، مجموع را در حافظهٔ فلش ایمن نگه می‌دارد، هر فصل شمسی را ساعت ۰۰:۰۰ به وقت تهران می‌بندد، رکوردها را در صف می‌گذارد و با مودم کار می‌کند. خوابیدن بین پالس‌ها برنامهٔ مصرف انرژی نسخهٔ ۰٫۳ است." },
    facts: [{ en: "Counter in two flash slots with CRC-32", fa: "شمارنده در دو بخش حافظه با CRC-32" }, { en: "Wi-Fi on the bench, cellular in the field", fa: "Wi-Fi روی میز آزمایش، شبکهٔ موبایل در میدان" }],
  },
  {
    id: "pcb", sec: "device", match: ["board.pcb", "board.standoff", "board.modem.post"], x: 0.7, spin: 40,
    en: { name: "Main board", does: "Two-layer board that joins everything: power, the pulse input, the modem header and the test points." },
    fa: { name: "بُرد اصلی", does: "بُرد دولایه‌ای که همه‌چیز را به هم وصل می‌کند: تغذیه، ورودی پالس، اتصال مودم و نقاط آزمون." },
    facts: [{ en: "Board v0.2 · KiCad", fa: "بُرد نسخهٔ ۰٫۲ · KiCad" }],
  },
  {
    id: "power", sec: "device", match: ["board.buck"], x: 0.7, spin: 40,
    en: { name: "Power stage", does: "On the v0.2 bench board an AP63203 buck turns USB 5 V into 3.3 V. For battery life, v0.3 replaces it with a regulator that draws under 1 µA at rest." },
    fa: { name: "طبقهٔ تغذیه", does: "در بُرد آزمایشگاهی ۰٫۲، مبدل AP63203 ولتاژ ۵ ولت USB را به ۳٫۳ ولت تبدیل می‌کند. برای عمر باتری، نسخهٔ ۰٫۳ آن را با رگولاتوری جایگزین می‌کند که در حالت سکون کمتر از ۱ میکروآمپر مصرف دارد." },
    facts: [],
  },
  {
    id: "usb", sec: "device", match: ["board.usb", "board.esd"], x: 0.7, spin: 40,
    en: { name: "USB-C and ESD guard", does: "Bench power, flashing and logs over the ESP32's native USB. A protection chip guards the data lines." },
    fa: { name: "درگاه USB-C و محافظ ESD", does: "برای تغذیه روی میز آزمایش، بارگذاری فِرم‌ور و دیدن گزارش‌ها از طریق USB داخلی ESP32. یک تراشهٔ محافظ از خطوط داده محافظت می‌کند." },
    facts: [],
  },
  {
    id: "j2", sec: "device", match: ["board.j2"], x: 0.7, spin: 40,
    en: { name: "Pulse input J2", does: "Where the reed cable lands. A 10 kΩ pull-up and 1 kΩ series resistor feed GPIO4, whose interrupt catches every closure." },
    fa: { name: "ورودی پالس J2", does: "محل اتصال کابل رید. یک مقاومت بالاکش ۱۰ کیلواهم و یک مقاومت سری ۱ کیلواهم به GPIO4 وصل‌اند و وقفهٔ آن هر بسته‌شدن را ثبت می‌کند." },
    facts: [{ en: "v0.3: 1 MΩ pull-up, so a parked magnet cannot drain the battery", fa: "نسخهٔ ۰٫۳: بالاکش ۱ مگااهم تا آهنربای ایستاده باتری را خالی نکند" }],
  },
  {
    id: "j3", sec: "device", match: ["board.j3"], x: 0.7, spin: 40,
    en: { name: "Expansion header J3", does: "Spare 3.3 V, ground, I²C and a reserved UART for later sensors or a debug probe." },
    fa: { name: "اتصال توسعهٔ J3", does: "ولتاژ ۳٫۳، زمین، I²C و یک UART رزرو برای حسگرهای بعدی یا ابزار عیب‌یابی." },
    facts: [],
  },
  {
    id: "buttons", sec: "device", match: ["board.sw"], x: 0.7, spin: 40,
    en: { name: "BOOT and RESET buttons", does: "For the bench: hold BOOT while resetting to load new firmware." },
    fa: { name: "دکمه‌های BOOT و RESET", does: "برای کار روی میز آزمایش: با نگه داشتن BOOT هنگام ریست، فِرم‌ور تازه بارگذاری می‌شود." },
    facts: [],
  },
  {
    id: "led", sec: "device", match: ["board.led"], x: 0.7, spin: 40,
    en: { name: "Status LED", does: "Blinks to show pulses and connection state while testing." },
    fa: { name: "چراغ وضعیت", does: "هنگام آزمایش با چشمک زدن، پالس‌ها و وضعیت اتصال را نشان می‌دهد." },
    facts: [{ en: "D1 · GPIO5", fa: "D1 · GPIO5" }],
  },
  {
    id: "battery", sec: "device", match: ["battery.cell", "battery.terminal", "battery.cradle"], x: 1, spin: 40,
    en: { name: "Li-SOCl₂ battery", does: "A 3.6 V lithium thionyl-chloride D cell, the v0.3 recommendation because meter boxes rarely have a socket. With deep sleep and one upload a day the power budget estimates more than ten years." },
    fa: { name: "باتری لیتیوم-تیونیل‌کلرید", does: "یک پیل سایز D با ولتاژ ۳٫۶، پیشنهاد نسخهٔ ۰٫۳؛ چون جعبهٔ کنتور معمولاً پریز برق ندارد. با خواب عمیق و یک ارسال در روز، بودجهٔ انرژی عمری بیش از ده سال تخمین می‌زند." },
    facts: [{ en: "Estimate, still to be measured", fa: "تخمینی؛ هنوز باید اندازه‌گیری شود" }],
  },
  {
    id: "hlc", sec: "device", match: ["battery.hlc"], x: 1, spin: 40,
    en: { name: "Hybrid layer capacitor", does: "Stores charge for the modem's short transmit bursts (about 0.2 A for BG95), which the battery cell alone cannot deliver." },
    fa: { name: "خازن لایهٔ ترکیبی (HLC)", does: "برای جریان‌های کوتاه و زیاد هنگام ارسال مودم (حدود ۰٫۲ آمپر برای BG95) انرژی ذخیره می‌کند؛ جریانی که باتری به‌تنهایی نمی‌تواند بدهد." },
    facts: [],
  },
  {
    id: "platter", sec: "device", match: ["stand.platter"], x: 0, spin: 0,
    en: { name: "Display turntable", does: "Not part of the product: the stand the model turns on." },
    fa: { name: "صفحهٔ گردان نمایش", does: "جزو محصول نیست؛ پایه‌ای که مدل روی آن می‌چرخد." },
    facts: [],
  },
];
