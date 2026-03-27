const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Inner Savages";
pres.title = "Anonimowa Weryfikacja Wieku";

// ── PALETTE: Deep navy + crimson (Polish gov feel) ──
const C = {
  navy: "1A2744",
  navyLight: "243556",
  crimson: "C41E3A",
  crimsonDark: "9E1830",
  white: "FFFFFF",
  offWhite: "F5F6FA",
  gray: "8892A0",
  grayLight: "E8EBF0",
  grayDark: "4A5568",
  green: "2E7D32",
  greenLight: "E8F5E9",
  blue: "2968A8",
  blueLight: "E3F2FD",
  amber: "F9A825",
  amberLight: "FFF8E1",
  pinkLight: "FCE4EC",
};

const makeShadow = () => ({ type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.12 });

// ════════════════════════════════════════════════════
// SLIDE 1: Tytuł
// ════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  // Accent bar top
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.crimson } });

  // Title
  s.addText("Anonimowa\nWeryfikacja Wieku", {
    x: 0.8, y: 1.0, w: 8.4, h: 2.2,
    fontSize: 44, fontFace: "Arial Black", color: C.white, bold: true,
    lineSpacingMultiple: 1.1,
  });

  // Subtitle
  s.addText("Jak udowodnić stronie internetowej, że masz 18+ lat,\nbez ujawniania kim jesteś", {
    x: 0.8, y: 3.2, w: 7, h: 0.9,
    fontSize: 18, fontFace: "Calibri", color: C.gray, italic: true,
    lineSpacingMultiple: 1.3,
  });

  // Bottom info bar
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 4.85, w: 10, h: 0.78, fill: { color: C.navyLight } });
  s.addText("BKI Hackathon 2026  |  Inner Savages", {
    x: 0.8, y: 4.9, w: 8.4, h: 0.65,
    fontSize: 14, fontFace: "Calibri", color: C.gray,
  });

  // Accent shape right
  s.addShape(pres.shapes.RECTANGLE, { x: 9.4, y: 1.0, w: 0.1, h: 2.8, fill: { color: C.crimson } });
}

// ════════════════════════════════════════════════════
// SLIDE 2: Problem
// ════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offWhite };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.crimson } });

  s.addText("Problem", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.7,
    fontSize: 32, fontFace: "Arial Black", color: C.navy, bold: true, margin: 0,
  });

  // Left column: problem description
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.2, w: 4.2, h: 3.8, fill: { color: C.white }, shadow: makeShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.2, w: 0.08, h: 3.8, fill: { color: C.crimson } });

  s.addText("Obecne rozwiazania", {
    x: 1.15, y: 1.35, w: 3.7, h: 0.5,
    fontSize: 16, fontFace: "Calibri", color: C.navy, bold: true, margin: 0,
  });

  s.addText([
    { text: "Podawanie danych osobowych stronom 18+", options: { bullet: true, breakLine: true } },
    { text: "Brak realnej weryfikacji (checkboxy)", options: { bullet: true, breakLine: true } },
    { text: "Wymuszanie logowania przez e-PUAP", options: { bullet: true, breakLine: true } },
    { text: "Ryzyko profilowania i inwigilacji", options: { bullet: true } },
  ], {
    x: 1.15, y: 1.95, w: 3.6, h: 2.8,
    fontSize: 13, fontFace: "Calibri", color: C.grayDark,
    paraSpaceAfter: 8,
  });

  // Right column: what we need
  s.addShape(pres.shapes.RECTANGLE, { x: 5.4, y: 1.2, w: 4.0, h: 3.8, fill: { color: C.white }, shadow: makeShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.4, y: 1.2, w: 0.08, h: 3.8, fill: { color: C.green } });

  s.addText("Czego potrzebujemy", {
    x: 5.75, y: 1.35, w: 3.5, h: 0.5,
    fontSize: 16, fontFace: "Calibri", color: C.green, bold: true, margin: 0,
  });

  s.addText([
    { text: "Weryfikacja wieku BEZ ujawniania tożsamości", options: { bullet: true, breakLine: true } },
    { text: "Brak możliwości śledzenia użytkownika", options: { bullet: true, breakLine: true } },
    { text: "Prostota użycia (6-cyfrowy kod)", options: { bullet: true, breakLine: true } },
    { text: "Odporność na zmowę podmiotów", options: { bullet: true } },
  ], {
    x: 5.75, y: 1.95, w: 3.5, h: 2.8,
    fontSize: 13, fontFace: "Calibri", color: C.grayDark,
    paraSpaceAfter: 8,
  });
}

// ════════════════════════════════════════════════════
// SLIDE 3: Architektura trójstronna
// ════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offWhite };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.crimson } });

  s.addText("Architektura trójstronna", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.7,
    fontSize: 32, fontFace: "Arial Black", color: C.navy, bold: true, margin: 0,
  });

  s.addText("Trzy podmioty, z których żaden nie wie wszystkiego", {
    x: 0.8, y: 0.95, w: 8.4, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: C.gray, italic: true, margin: 0,
  });

  // Three cards
  const cards = [
    { x: 0.5, label: "Rząd A", sub: "mObywatel", color: C.crimson, knows: "Kim jesteś\ni ile masz lat", notKnows: "Jakiego kodu użyjesz\nani na jakiej stronie" },
    { x: 3.6, label: "Rząd B", sub: "NASK", color: C.blue, knows: "Że ktoś anonimowy\nma 18+", notKnows: "Kim jest\nta osoba" },
    { x: 6.7, label: "Strona 18+", sub: "Odbiorca kodu", color: C.grayDark, knows: "Że wpisany kod\njest ważny", notKnows: "Kim jest\nużytkownik" },
  ];

  cards.forEach(c => {
    s.addShape(pres.shapes.RECTANGLE, { x: c.x, y: 1.55, w: 2.8, h: 3.6, fill: { color: C.white }, shadow: makeShadow() });
    // Color header bar
    s.addShape(pres.shapes.RECTANGLE, { x: c.x, y: 1.55, w: 2.8, h: 0.65, fill: { color: c.color } });
    s.addText(c.label, {
      x: c.x, y: 1.55, w: 2.8, h: 0.42,
      fontSize: 16, fontFace: "Calibri", color: C.white, bold: true, align: "center", margin: 0,
    });
    s.addText(c.sub, {
      x: c.x, y: 1.93, w: 2.8, h: 0.28,
      fontSize: 10, fontFace: "Calibri", color: "CCCCCC", align: "center", margin: 0,
    });

    // WIE
    s.addText("WIE:", {
      x: c.x + 0.2, y: 2.35, w: 2.4, h: 0.3,
      fontSize: 10, fontFace: "Calibri", color: C.green, bold: true, margin: 0,
    });
    s.addText(c.knows, {
      x: c.x + 0.2, y: 2.6, w: 2.4, h: 0.8,
      fontSize: 12, fontFace: "Calibri", color: C.grayDark, margin: 0,
    });

    // NIE WIE
    s.addText("NIE WIE:", {
      x: c.x + 0.2, y: 3.5, w: 2.4, h: 0.3,
      fontSize: 10, fontFace: "Calibri", color: C.crimson, bold: true, margin: 0,
    });
    s.addText(c.notKnows, {
      x: c.x + 0.2, y: 3.75, w: 2.4, h: 0.8,
      fontSize: 12, fontFace: "Calibri", color: C.grayDark, margin: 0,
    });
  });
}

// ════════════════════════════════════════════════════
// SLIDE 4: Jak to dziala - 3 kroki
// ════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.crimson } });

  s.addText("Jak to działa? 3 proste kroki", {
    x: 0.8, y: 0.25, w: 8.4, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", color: C.white, bold: true, margin: 0,
  });

  const steps = [
    {
      num: "1", title: "Weryfikacja wieku",
      desc: "Otwierasz mObywatel. Twój telefon generuje losowy token i chowa go w kryptograficznej kopercie. Rząd A sprawdza Twój wiek i podpisuje kopertę — nie widząc co jest w środku.",
      color: C.crimson, bg: C.crimsonDark,
    },
    {
      num: "2", title: "Pobranie kodu",
      desc: "Wysyłasz podpisany token (bez PESELu!) do Rządu B. NASK weryfikuje podpis, generuje jednorazowy 6-cyfrowy kod ważny 5 minut. Nie wie kim jesteś.",
      color: C.blue, bg: "1E4D7B",
    },
    {
      num: "3", title: "Wejście na stronę",
      desc: "Wpisujesz kod na stronie 18+. Strona pyta Rząd B: ważny? Odpowiedź: TAK. Kod spalony. Strona nie zna Twojej tożsamości.",
      color: C.green, bg: "1B5E20",
    },
  ];

  steps.forEach((st, i) => {
    const y = 1.15 + i * 1.4;
    s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y, w: 8.4, h: 1.2, fill: { color: C.navyLight }, shadow: makeShadow() });
    // Number circle
    s.addShape(pres.shapes.OVAL, { x: 1.05, y: y + 0.22, w: 0.75, h: 0.75, fill: { color: st.color } });
    s.addText(st.num, {
      x: 1.05, y: y + 0.22, w: 0.75, h: 0.75,
      fontSize: 28, fontFace: "Arial Black", color: C.white, align: "center", valign: "middle", margin: 0,
    });
    // Title
    s.addText(st.title, {
      x: 2.1, y: y + 0.1, w: 6.8, h: 0.4,
      fontSize: 17, fontFace: "Calibri", color: C.white, bold: true, margin: 0,
    });
    // Description
    s.addText(st.desc, {
      x: 2.1, y: y + 0.5, w: 6.8, h: 0.6,
      fontSize: 12, fontFace: "Calibri", color: C.gray, margin: 0,
    });
  });
}

// ════════════════════════════════════════════════════
// SLIDE 5: Analogia z kopertą
// ════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offWhite };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.crimson } });

  s.addText("Analogia z koperta i kalka", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", color: C.navy, bold: true, margin: 0,
  });

  // Big quote card
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.2, w: 8.4, h: 3.8, fill: { color: C.white }, shadow: makeShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.2, w: 0.1, h: 3.8, fill: { color: C.amber } });

  const analogySteps = [
    { num: "1", text: "Piszesz tajny numer na kartce", color: C.grayDark },
    { num: "2", text: "Wkładasz kartkę do nieprzezroczystej koperty z kalką w środku", color: C.grayDark },
    { num: "3", text: "Urzędnik (Rząd A) sprawdza Twój dowód, podpisuje kopertę — podpis przechodzi przez kalkę na kartkę, ale urzędnik nie widzi co jest w środku", color: C.crimson },
    { num: "4", text: "Otwierasz kopertę — masz kartkę z Twoim numerem i podpisem urzędnika", color: C.green },
    { num: "5", text: "Idziesz do drugiego okienka (Rząd B), pokazujesz kartkę. Drugie okienko widzi ważny podpis, wydaje kod — ale nie wie kto stał w pierwszym okienku", color: C.blue },
  ];

  analogySteps.forEach((a, i) => {
    const y = 1.45 + i * 0.68;
    s.addShape(pres.shapes.OVAL, { x: 1.2, y: y, w: 0.4, h: 0.4, fill: { color: C.navy } });
    s.addText(a.num, {
      x: 1.2, y: y, w: 0.4, h: 0.4,
      fontSize: 14, fontFace: "Calibri", color: C.white, align: "center", valign: "middle", margin: 0,
    });
    s.addText(a.text, {
      x: 1.8, y: y, w: 7.1, h: 0.55,
      fontSize: 13, fontFace: "Calibri", color: a.color, margin: 0, valign: "middle",
    });
  });
}

// ════════════════════════════════════════════════════
// SLIDE 6: 4 warstwy ochrony
// ════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offWhite };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.crimson } });

  s.addText("4 warstwy ochrony prywatnosci", {
    x: 0.8, y: 0.25, w: 8.4, h: 0.65,
    fontSize: 28, fontFace: "Arial Black", color: C.navy, bold: true, margin: 0,
  });

  s.addText("Nawet jesli jedno zabezpieczenie zawiedzie, pozostale trzymaja", {
    x: 0.8, y: 0.85, w: 8.4, h: 0.35,
    fontSize: 13, fontFace: "Calibri", color: C.gray, italic: true, margin: 0,
  });

  const layers = [
    { label: "Separacja prawna", desc: "Dwa resorty + ustawowy zakaz wymiany danych. Zmowa = przestepstwo.", badge: "PRAWNA", badgeColor: C.green, bgColor: C.greenLight },
    { label: "Slepe podpisy RSA", desc: "Zaslepiony token =/= odslepiony token. Matematycznie niepowiazalne.", badge: "MATEMATYCZNA", badgeColor: C.blue, bgColor: C.blueLight },
    { label: "OPRF", desc: "Serwer przetwarza dane, ktorych nigdy nie widzial. Nawet logi sa bezuzyteczne.", badge: "MATEMATYCZNA", badgeColor: C.blue, bgColor: C.amberLight },
    { label: "Enklawy TEE", desc: "Intel SGX / ARM TrustZone. Kod open-source. Nawet admin serwera nie widzi danych.", badge: "SPRZETOWA", badgeColor: C.crimson, bgColor: C.pinkLight },
  ];

  layers.forEach((l, i) => {
    const y = 1.35 + i * 1.0;
    // Card
    s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y, w: 8.4, h: 0.85, fill: { color: C.white }, shadow: makeShadow() });
    // Left accent
    s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y, w: 0.08, h: 0.85, fill: { color: l.badgeColor } });
    // Number
    s.addShape(pres.shapes.OVAL, { x: 1.1, y: y + 0.17, w: 0.5, h: 0.5, fill: { color: l.bgColor } });
    s.addText(String(i + 1), {
      x: 1.1, y: y + 0.17, w: 0.5, h: 0.5,
      fontSize: 16, fontFace: "Calibri", color: l.badgeColor, align: "center", valign: "middle", bold: true, margin: 0,
    });
    // Title
    s.addText(l.label, {
      x: 1.8, y: y + 0.08, w: 4.5, h: 0.35,
      fontSize: 15, fontFace: "Calibri", color: C.navy, bold: true, margin: 0,
    });
    // Desc
    s.addText(l.desc, {
      x: 1.8, y: y + 0.42, w: 4.5, h: 0.35,
      fontSize: 11, fontFace: "Calibri", color: C.grayDark, margin: 0,
    });
    // Badge
    s.addShape(pres.shapes.RECTANGLE, { x: 7.4, y: y + 0.25, w: 1.6, h: 0.35, fill: { color: l.bgColor } });
    s.addText(l.badge, {
      x: 7.4, y: y + 0.25, w: 1.6, h: 0.35,
      fontSize: 9, fontFace: "Calibri", color: l.badgeColor, bold: true, align: "center", valign: "middle", margin: 0,
    });
  });
}

// ════════════════════════════════════════════════════
// SLIDE 7: Zmowa A+B?
// ════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.crimson } });

  s.addText("Co jesli Rzad A i B zmowia sie?", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", color: C.white, bold: true, margin: 0,
  });

  // Left: A has
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.3, w: 4.0, h: 2.0, fill: { color: C.navyLight }, shadow: makeShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.3, w: 4.0, h: 0.5, fill: { color: C.crimson } });
  s.addText("Rzad A ma:", {
    x: 0.8, y: 1.3, w: 4.0, h: 0.5,
    fontSize: 15, fontFace: "Calibri", color: C.white, bold: true, align: "center", valign: "middle", margin: 0,
  });
  s.addText("PESEL + zaslepiony token\n(losowy szum)", {
    x: 1.0, y: 1.95, w: 3.6, h: 1.1,
    fontSize: 14, fontFace: "Calibri", color: C.gray, align: "center",
  });

  // Right: B has
  s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.3, w: 4.0, h: 2.0, fill: { color: C.navyLight }, shadow: makeShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.3, w: 4.0, h: 0.5, fill: { color: C.blue } });
  s.addText("Rzad B ma:", {
    x: 5.2, y: 1.3, w: 4.0, h: 0.5,
    fontSize: 15, fontFace: "Calibri", color: C.white, bold: true, align: "center", valign: "middle", margin: 0,
  });
  s.addText("Odslepiony token + kod\n(bez tozsamosci)", {
    x: 5.4, y: 1.95, w: 3.6, h: 1.1,
    fontSize: 14, fontFace: "Calibri", color: C.gray, align: "center",
  });

  // Result
  s.addShape(pres.shapes.RECTANGLE, { x: 1.5, y: 3.7, w: 7.0, h: 1.5, fill: { color: C.green }, shadow: makeShadow() });
  s.addText([
    { text: "Zaslepiony token  =/=  Odslepiony token\n", options: { fontSize: 18, bold: true, breakLine: true } },
    { text: "To jest sedno slepego podpisu! Nawet majac OBA dzienniki,\nNIE DA SIE powiazac wpisow Rzadu A z wpisami Rzadu B." },
  ], {
    x: 1.7, y: 3.8, w: 6.6, h: 1.3,
    fontSize: 13, fontFace: "Calibri", color: C.white, align: "center", valign: "middle",
  });
}

// ════════════════════════════════════════════════════
// SLIDE 8: Proof of Concept
// ════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.offWhite };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.crimson } });

  s.addText("Proof of Concept", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.7,
    fontSize: 30, fontFace: "Arial Black", color: C.navy, bold: true, margin: 0,
  });

  s.addText("Dzialajacy kod + interaktywny mockup aplikacji", {
    x: 0.8, y: 0.9, w: 8.4, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: C.gray, italic: true, margin: 0,
  });

  // Card: Python PoC
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.5, w: 4.0, h: 3.4, fill: { color: C.white }, shadow: makeShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.5, w: 4.0, h: 0.55, fill: { color: C.navy } });
  s.addText("Kod kryptograficzny (Python)", {
    x: 0.8, y: 1.5, w: 4.0, h: 0.55,
    fontSize: 13, fontFace: "Calibri", color: C.white, bold: true, align: "center", valign: "middle", margin: 0,
  });
  s.addText([
    { text: "Slepe podpisy RSA (Chaum 1983)", options: { bullet: true, breakLine: true } },
    { text: "Nieswiadoma Funkcja PRF (OPRF)", options: { bullet: true, breakLine: true } },
    { text: "Generowanie liczb pierwszych", options: { bullet: true, breakLine: true } },
    { text: "Pelna symulacja 3 podmiotow", options: { bullet: true, breakLine: true } },
    { text: "Test: dorosly, nieletni, ponowne uzycie", options: { bullet: true, breakLine: true } },
    { text: "Zero zewnetrznych bibliotek", options: { bullet: true } },
  ], {
    x: 1.0, y: 2.2, w: 3.6, h: 2.5,
    fontSize: 12, fontFace: "Calibri", color: C.grayDark,
    paraSpaceAfter: 5,
  });

  // Card: Interactive mockup
  s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.5, w: 4.0, h: 3.4, fill: { color: C.white }, shadow: makeShadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.5, w: 4.0, h: 0.55, fill: { color: C.crimson } });
  s.addText("Mockup aplikacji (HTML)", {
    x: 5.2, y: 1.5, w: 4.0, h: 0.55,
    fontSize: 13, fontFace: "Calibri", color: C.white, bold: true, align: "center", valign: "middle", margin: 0,
  });
  s.addText([
    { text: "Wyglad jak mObywatel", options: { bullet: true, breakLine: true } },
    { text: "Generowanie kodow z timerem 5 min", options: { bullet: true, breakLine: true } },
    { text: "7 krokow kryptografii z analogiami", options: { bullet: true, breakLine: true } },
    { text: "Okno strony 18+ do weryfikacji", options: { bullet: true, breakLine: true } },
    { text: "Jednorazowe spalanie kodow", options: { bullet: true, breakLine: true } },
    { text: "Pelna interakcja w przegladarce", options: { bullet: true } },
  ], {
    x: 5.4, y: 2.2, w: 3.6, h: 2.5,
    fontSize: 12, fontFace: "Calibri", color: C.grayDark,
    paraSpaceAfter: 5,
  });
}

// ════════════════════════════════════════════════════
// SLIDE 9: Podsumowanie
// ════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.crimson } });

  s.addText("Podsumowanie", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.8,
    fontSize: 36, fontFace: "Arial Black", color: C.white, bold: true, margin: 0,
  });

  // Table
  const tblData = [
    [
      { text: "Warstwa", options: { fill: { color: C.crimson }, color: C.white, bold: true, fontSize: 12, fontFace: "Calibri", align: "center" } },
      { text: "Co gwarantuje", options: { fill: { color: C.crimson }, color: C.white, bold: true, fontSize: 12, fontFace: "Calibri", align: "center" } },
      { text: "Typ", options: { fill: { color: C.crimson }, color: C.white, bold: true, fontSize: 12, fontFace: "Calibri", align: "center" } },
    ],
    [
      { text: "Separacja prawna", options: { fill: { color: C.navyLight }, color: C.white, fontSize: 12, fontFace: "Calibri" } },
      { text: "Wymiana danych = przestepstwo", options: { fill: { color: C.navyLight }, color: C.gray, fontSize: 11, fontFace: "Calibri" } },
      { text: "Prawna", options: { fill: { color: C.navyLight }, color: C.green, bold: true, fontSize: 11, fontFace: "Calibri", align: "center" } },
    ],
    [
      { text: "Slepe podpisy RSA", options: { fill: { color: C.navy }, color: C.white, fontSize: 12, fontFace: "Calibri" } },
      { text: "Nie da sie powiazac tokenow", options: { fill: { color: C.navy }, color: C.gray, fontSize: 11, fontFace: "Calibri" } },
      { text: "Matematyczna", options: { fill: { color: C.navy }, color: C.blue, bold: true, fontSize: 11, fontFace: "Calibri", align: "center" } },
    ],
    [
      { text: "OPRF", options: { fill: { color: C.navyLight }, color: C.white, fontSize: 12, fontFace: "Calibri" } },
      { text: "Serwer nie widzi danych", options: { fill: { color: C.navyLight }, color: C.gray, fontSize: 11, fontFace: "Calibri" } },
      { text: "Matematyczna", options: { fill: { color: C.navyLight }, color: C.blue, bold: true, fontSize: 11, fontFace: "Calibri", align: "center" } },
    ],
    [
      { text: "Enklawy TEE", options: { fill: { color: C.navy }, color: C.white, fontSize: 12, fontFace: "Calibri" } },
      { text: "Kod robi to co deklaruje", options: { fill: { color: C.navy }, color: C.gray, fontSize: 11, fontFace: "Calibri" } },
      { text: "Sprzetowa", options: { fill: { color: C.navy }, color: C.amber, bold: true, fontSize: 11, fontFace: "Calibri", align: "center" } },
    ],
    [
      { text: "Open-source", options: { fill: { color: C.navyLight }, color: C.white, fontSize: 12, fontFace: "Calibri" } },
      { text: "Brak ukrytych backdoorow", options: { fill: { color: C.navyLight }, color: C.gray, fontSize: 11, fontFace: "Calibri" } },
      { text: "Spoleczna", options: { fill: { color: C.navyLight }, color: C.gray, bold: true, fontSize: 11, fontFace: "Calibri", align: "center" } },
    ],
  ];

  s.addTable(tblData, {
    x: 0.8, y: 1.3, w: 8.4,
    colW: [2.5, 4.0, 1.9],
    border: { pt: 0.5, color: C.navyLight },
    rowH: [0.45, 0.42, 0.42, 0.42, 0.42, 0.42],
  });

  // Bottom callout
  s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 4.1, w: 8.4, h: 1.1, fill: { color: C.green }, shadow: makeShadow() });
  s.addText("Zeby deanonimizowac uzytkownika, trzeba jednoczesnie:\nzlamac matematyke OPRF + zhackowac enklawe sprzetowa\n+ obejsc audyt open-source + zlamac prawo", {
    x: 1.0, y: 4.15, w: 8.0, h: 1.0,
    fontSize: 14, fontFace: "Calibri", color: C.white, align: "center", valign: "middle", bold: true,
  });
}

// ════════════════════════════════════════════════════
// SLIDE 10: Kontakt / CTA
// ════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.crimson } });

  s.addText("Dziekujemy!", {
    x: 0.8, y: 1.2, w: 8.4, h: 1.2,
    fontSize: 48, fontFace: "Arial Black", color: C.white, bold: true, align: "center", margin: 0,
  });

  s.addText("Kod zrodlowy + interaktywne demo:", {
    x: 0.8, y: 2.6, w: 8.4, h: 0.5,
    fontSize: 16, fontFace: "Calibri", color: C.gray, align: "center", margin: 0,
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 2.0, y: 3.2, w: 6.0, h: 0.6, fill: { color: C.navyLight } });
  s.addText("github.com/Inner-Savages/BKIHack2026", {
    x: 2.0, y: 3.2, w: 6.0, h: 0.6,
    fontSize: 16, fontFace: "Consolas", color: C.crimson, align: "center", valign: "middle", bold: true, margin: 0,
    hyperlink: { url: "https://github.com/Inner-Savages/BKIHack2026" },
  });

  s.addText("BKI Hackathon 2026  |  Inner Savages", {
    x: 0.8, y: 4.5, w: 8.4, h: 0.5,
    fontSize: 14, fontFace: "Calibri", color: C.gray, align: "center", margin: 0,
  });
}

// ── SAVE ──
pres.writeFile({ fileName: "/Users/janbaumgart/BKIHACK20216/prezentacja.pptx" })
  .then(() => console.log("Prezentacja zapisana!"))
  .catch(e => console.error(e));
