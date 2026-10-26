// Bilingual notes for the 3D exploded block diagram. Each block names the real parts on the carrier board
// (hardware/kicad/design_v02.py) or the modem board (hardware/kicad-modem/design_modem_v01.py).

export const SECTIONS = [
  { id: "power", en: "5 V input (carrier board)", fa: "ورودی ۵ ولت (بُرد حامل)", noteEn: "Exploded, each voltage domain rises to its own level; an arrow that breaks at the gap is a rail or signal crossing between domains.", noteFa: "در نمای انفجاری هر حوزهٔ ولتاژ به ترازی جدا بالا می‌رود؛ پیکانی که در فاصله شکسته می‌شود ریل یا سیگنالی است که از یک حوزه به حوزهٔ دیگر می‌رود." },
  { id: "logic", en: "3.3 V logic (carrier board)", fa: "منطق ۳٫۳ ولت (بُرد حامل)" },
  { id: "modem", en: "Modem board (VBAT 3.8 V and 1.8 V)", fa: "بُرد مودم (VBAT ‏۳٫۸ ولت و ۱٫۸ ولت)" },
];

const B = (id, sec, match, en, fa, facts = [], x = 0.6) => ({ id, sec, match, x, spin: 0, en, fa, facts });

export const ITEMS = [
  B("usb", "power", ["block.power.usb", "link.power.usbdata", "block.power.tab", "plate"],
    { name: "USB-C 5 V", does: "The only power input of the carrier on the bench, and the ESP32-S3's own USB for flashing and logs. Its data pair crosses straight into the 3.3 V logic domain." },
    { name: "ورودی USB-C ‏۵ ولت", does: "تنها ورودی تغذیهٔ بُرد حامل روی میز آزمایش و همان USB داخلی ESP32-S3 برای بارگذاری فِرم‌ور و گزارش‌ها. زوج داده‌اش مستقیم به حوزهٔ منطق ۳٫۳ ولت می‌رود." },
    [{ en: "J1 · R1, R2 5.1 kΩ (power sink)", fa: "J1 · R1 و R2 ‏۵٫۱ کیلواهم (مصرف‌کننده)" }], 0),
  B("protect", "power", ["block.power.protect", "link.power.usb-protect"],
    { name: "Protection", does: "A resettable fuse, a TVS clamp on 5 V and an ESD array on the data lines, all at the connector." },
    { name: "حفاظت", does: "فیوز خودترمیم، دیود TVS روی ۵ ولت و آرایهٔ ESD روی خطوط داده، همه کنار کانکتور." },
    [{ en: "F1 PTC 0.75 A · D1 SMAJ6.5CA · U2 USBLC6-2SC6", fa: "F1 فیوز ۰٫۷۵ آمپر · D1 ‏SMAJ6.5CA · U2 ‏USBLC6-2SC6" }], 0),
  B("buck", "power", ["block.power.buck", "link.power.protect-buck", "link.power.3v3"],
    { name: "Buck regulator 3.3 V", does: "Turns 5 V into the 3.3 V rail for everything on the carrier. The rail is the arrow that rises into the logic domain." },
    { name: "مبدل باک ۳٫۳ ولت", does: "۵ ولت را به ریل ۳٫۳ ولت برای همهٔ بُرد حامل تبدیل می‌کند. همین ریل پیکانی است که به حوزهٔ منطق بالا می‌رود." },
    [{ en: "U3 AP63203WU-7 · L1 3.9 µH · 2 × 22 µF", fa: "U3 ‏AP63203WU-7 · L1 ‏۳٫۹ میکروهانری · دو ۲۲ میکروفاراد" }], 0),

  B("esp32", "logic", ["block.logic.esp32", "block.logic.tab", "link.logic.3v3", "link.logic.usbdata"],
    { name: "ESP32-S3", does: "Counts pulses, keeps the total in flash, closes each Jalali season and decides when the modem wakes. Everything in this domain runs at 3.3 V." },
    { name: "ESP32-S3", does: "پالس‌ها را می‌شمارد، مجموع را در فلش نگه می‌دارد، هر فصل شمسی را می‌بندد و تصمیم می‌گیرد مودم کی بیدار شود. همهٔ این حوزه با ۳٫۳ ولت کار می‌کند." },
    [{ en: "U1 ESP32-S3-WROOM-1-N8", fa: "U1 ‏ESP32-S3-WROOM-1-N8" }]),
  B("inputs", "logic", ["block.logic.pulse", "block.logic.tamper", "link.logic.pulse", "link.logic.tamper"],
    { name: "Pulse and tamper inputs", does: "The synthetic 3.3 V pulse (GPIO4) and the enclosure tamper switch (GPIO15), each with a pull-up and a series resistor." },
    { name: "ورودی‌های پالس و ضددستکاری", does: "پالس شبیه‌سازی‌شدهٔ ۳٫۳ ولت (GPIO4) و کلید ضددستکاری محفظه (GPIO15)، هر کدام با مقاومت بالاکش و مقاومت سری." },
    [{ en: "J2 · J3 · bench signals only", fa: "J2 · J3 · فقط سیگنال آزمایشگاهی" }]),
  B("keys", "logic", ["block.logic.keys", "link.logic.keys"],
    { name: "RESET and BOOT", does: "SW1 resets the chip; SW2 held during reset enters USB download mode." },
    { name: "ریست و بوت", does: "SW1 تراشه را ریست می‌کند؛ نگه داشتن SW2 هنگام ریست حالت بارگذاری از USB را فعال می‌کند." }),
  B("outputs", "logic", ["block.logic.led", "block.logic.io", "link.logic.led", "link.logic.io"],
    { name: "LED, I²C and debug UART", does: "The status LED on GPIO5, the I²C expansion header with pull-ups and the 3.3 V debug serial port." },
    { name: "LED، ‏I²C و سریال عیب‌یابی", does: "چراغ وضعیت روی GPIO5، اتصال توسعهٔ I²C با مقاومت‌های بالاکش و درگاه سریال عیب‌یابی ۳٫۳ ولت." },
    [{ en: "D2 · J4 · J5", fa: "D2 · J4 · J5" }]),
  B("j6", "logic", ["block.logic.header", "link.logic.j6", "link.logic.uart-out", "link.logic.en-out"],
    { name: "Modem header J6", does: "UART, enable, reset and status leave the 3.3 V domain here: the two arrows that break toward the modem level." },
    { name: "اتصال مودم J6", does: "خطوط UART، روشن‌سازی، ریست و وضعیت از اینجا از حوزهٔ ۳٫۳ ولت خارج می‌شوند: همان دو پیکانی که به سمت تراز مودم شکسته می‌شوند." },
    [{ en: "8 pins, mated by modem-board J1", fa: "هشت پایه، جفت‌شده با J1 بُرد مودم" }]),

  B("shift", "modem", ["block.modem.shift", "link.modem.uart-in", "link.modem.shift-ec", "block.modem.tab"],
    { name: "Level shifting", does: "The module speaks 1.8 V; three MOSFET shifters translate the UART and STATUS lines to and from 3.3 V." },
    { name: "تبدیل سطح ولتاژ", does: "ماژول با ۱٫۸ ولت کار می‌کند؛ سه مبدل ماسفتی خطوط UART و STATUS را به ۳٫۳ ولت و برعکس تبدیل می‌کنند." },
    [{ en: "Q3–Q5 DMG2302U · R5–R7 10 kΩ", fa: "Q3 تا Q5 ‏DMG2302U · R5 تا R7 ‏۱۰ کیلواهم" }], 1),
  B("drivers", "modem", ["block.modem.drivers", "link.modem.en-in", "link.modem.drivers-ec"],
    { name: "PWRKEY and RESET drivers", does: "Two open-collector transistors let the 3.3 V enable and reset lines pull the module's VBAT-domain PWRKEY and RESET_N low." },
    { name: "راه‌اندازهای PWRKEY و RESET", does: "دو ترانزیستور کلکتور باز اجازه می‌دهند خطوط روشن‌سازی و ریست ۳٫۳ ولتی، پایه‌های PWRKEY و RESET_N ماژول را که در حوزهٔ VBAT هستند پایین بکشند." },
    [{ en: "Q1 · Q2 MMBT3904", fa: "Q1 · Q2 ‏MMBT3904" }], 1),
  B("ec200u", "modem", ["block.modem.ec200u"],
    { name: "EC200U-EU module", does: "LTE Cat 1 radio that sends the readings and the SMS fallback, with its network LED." },
    { name: "ماژول EC200U-EU", does: "رادیوی LTE گربهٔ ۱ که خوانش‌ها و پیامک پشتیبان را می‌فرستد، همراه با چراغ شبکه." },
    [{ en: "Footprint provisional on the v0.1 board", fa: "ردپا در بُرد ۰٫۱ موقت است" }], 1),
  B("vbat", "modem", ["block.modem.vbat", "block.modem.bench", "link.modem.vbat", "link.modem.bench"],
    { name: "VBAT supply and reservoir", does: "A separate current-limited 3.8 V bench supply (carrier J7) feeds the module through a VBAT plane and two 100 µF tantalum capacitors that carry the 2 A transmit bursts. It is never taken from the 3.3 V rail." },
    { name: "تغذیه و مخزن VBAT", does: "یک منبع جدای ۳٫۸ ولت با محدودیت جریان (J7 روی بُرد حامل) ماژول را از طریق صفحهٔ VBAT و دو خازن تانتالیوم ۱۰۰ میکروفاراد تغذیه می‌کند که جریان‌های ۲ آمپری ارسال را می‌دهند. هرگز از ریل ۳٫۳ ولت گرفته نمی‌شود." }, [], 1),
  B("simant", "modem", ["block.modem.sim", "block.modem.ant", "link.modem.sim", "link.modem.ant"],
    { name: "SIM and antenna", does: "The protected micro-SIM and the 50 Ω line to the u.FL antenna connector with its π matching network." },
    { name: "سیم‌کارت و آنتن", does: "سیم‌کارت میکرو با حفاظت و خط ۵۰ اهمی تا کانکتور آنتن u.FL با شبکهٔ تطبیق π." },
    [{ en: "J3 + U2 ESD224 · J4 u.FL + R15/C14/C15", fa: "J3 و U2 ‏ESD224 · J4 ‏u.FL با R15/C14/C15" }], 1),
];

export const UI = {
  overviewKicker: { en: "Block diagram · 3D exploded", fa: "نمودار بلوکی · نمای انفجاری سه‌بعدی" },
  overviewTitle: { en: "Three voltage domains, two boards", fa: "سه حوزهٔ ولتاژ، دو بُرد" },
  overviewBody: {
    en: "Assembled, this is the block diagram of the whole electronics. Pull it apart and it separates by voltage: the 5 V input stays on the plate, the 3.3 V carrier logic rises one level and the modem board's VBAT and 1.8 V domain rises to the top. Every arrow that breaks at a gap crosses a domain boundary, and that is exactly where the design needs a regulator, a level shifter or a driver.",
    fa: "در حالت بسته، این نمودار بلوکی کل الکترونیک است. بازش کنید تا بر اساس ولتاژ جدا شود: ورودی ۵ ولت روی صفحه می‌ماند، منطق ۳٫۳ ولت بُرد حامل یک تراز بالا می‌رود و حوزهٔ VBAT و ۱٫۸ ولت بُرد مودم به بالاترین تراز می‌رسد. هر پیکانی که در فاصله شکسته می‌شود از مرز یک حوزه عبور می‌کند؛ درست همان‌جا که طرح به رگولاتور، مبدل سطح یا راه‌انداز نیاز دارد.",
  },
  hint: { en: "Drag to turn · scroll to zoom · click a block · ↑ ↓ open and close · [ ] previous and next · L language · T tour", fa: "برای چرخاندن بکشید · برای بزرگ‌نمایی اسکرول کنید · روی هر بلوک کلیک کنید · ↑ ↓ باز و بسته · [ ] قبلی و بعدی · L زبان · T تور" },
};

export const META = {
  file: "blocks",
  title: { en: "Block diagram — exploded by voltage domain", fa: "نمودار بلوکی — جدا شده بر اساس حوزهٔ ولتاژ" },
  subtitle: { en: "Carrier v0.2 + modem board v0.1", fa: "بُرد حامل ۰٫۲ و بُرد مودم ۰٫۱" },
  badge: [{ en: "Every block names real schematic parts", fa: "هر بلوک نام قطعه‌های واقعی شماتیک را دارد" }, { en: "Bench use only — never connect to a live gas meter, gas line or mains", fa: "فقط برای میز آزمایش — هرگز به کنتور، لولهٔ گاز یا برق شهر وصل نشود" }],
  htmlTitle: "SGM Block Diagram",
  description: "A 3D block diagram of the Smart Gas Meter electronics that separates into its three voltage domains.",
};
