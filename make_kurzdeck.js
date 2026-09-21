// Kurzpraesentation zum Use Case "KI-gestuetzte Schichtplanung in der Pflege"
// 8 Folien, ca. 8 Minuten. Alle Zahlen stammen aus evaluation_results.csv
// bzw. aus den in ERGEBNISSE.md und DATENKONZEPT.md belegten Quellen.
//
//   node make_kurzdeck.js   ->  Kurzpraesentation_Schichtplanung.pptx

const pptxgen = require("pptxgenjs");
const path = require("path");

const BASE = __dirname;
const IMG = (n) => path.join(BASE, "abbildungen", n);

const NAVY = "1E2761";
const ICE = "CADCFC";
const ICE_L = "EEF4FE";
const ORANGE = "EB6834";
const INK = "0B0B0B";
const INK2 = "52514E";
const MUTED = "898781";
const WHITE = "FFFFFF";

const H = "Cambria";
const B = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Projektteam KI & Management";
pres.title = "KI-gestützte Schichtplanung in der Pflege — Kurzfassung";

const W = 13.33, M = 0.7;

// ---------- Bausteine ------------------------------------------------------

function titleSlide(s, kicker, title, subtitle, meta) {
  s.background = { color: NAVY };
  s.addText(kicker, {
    x: M, y: 1.5, w: 10, h: 0.35, isTextBox: true, margin: 0,
    fontFace: B, fontSize: 13, bold: true, color: ORANGE, charSpacing: 2,
  });
  s.addText(title, {
    x: M, y: 2.0, w: 11.4, h: 1.6, isTextBox: true, margin: 0,
    fontFace: H, fontSize: 44, bold: true, color: WHITE, lineSpacing: 46,
  });
  s.addText(subtitle, {
    x: M, y: 3.75, w: 10.5, h: 0.9, isTextBox: true, margin: 0,
    fontFace: B, fontSize: 17, color: ICE, lineSpacing: 26,
  });
  if (meta) {
    s.addText(meta, {
      x: M, y: 6.3, w: 11.4, h: 0.5, isTextBox: true, margin: 0,
      fontFace: B, fontSize: 12, color: "9BA8CC",
    });
  }
}

function head(s, title, takeaway) {
  s.addText(title, {
    x: M, y: 0.45, w: W - 2 * M, h: 0.7, isTextBox: true, margin: 0,
    fontFace: H, fontSize: 32, bold: true, color: NAVY,
  });
  if (takeaway) {
    s.addText(takeaway, {
      x: M, y: 1.18, w: W - 2 * M, h: 0.5, isTextBox: true, margin: 0,
      fontFace: B, fontSize: 15, color: INK2, italic: true,
    });
  }
}

function source(s, text) {
  s.addText(text, {
    x: M, y: 6.92, w: W - 2 * M, h: 0.35, isTextBox: true, margin: 0,
    fontFace: B, fontSize: 10, color: MUTED,
  });
}

function card(s, x, y, w, h, fill) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.08, fill: { color: fill || ICE_L },
    line: { color: fill || ICE_L, width: 0 },
    shadow: { type: "outer", angle: 90, blur: 6, offset: 1, opacity: 0.10, color: "000000" },
  });
}

function bulletRows(s, items, x, y, w, gap) {
  items.forEach((it, i) => {
    const yy = y + i * gap;
    s.addShape(pres.ShapeType.ellipse, {
      x, y: yy + 0.06, w: 0.26, h: 0.26,
      fill: { color: i % 2 === 0 ? NAVY : ORANGE }, line: { width: 0 },
    });
    s.addText(it.t, {
      x: x + 0.45, y: yy, w: w - 0.45, h: 0.32, isTextBox: true, margin: 0,
      fontFace: B, fontSize: 15, bold: true, color: INK,
    });
    if (it.d) {
      s.addText(it.d, {
        x: x + 0.45, y: yy + 0.32, w: w - 0.45, h: 0.5, isTextBox: true, margin: 0,
        fontFace: B, fontSize: 13, color: INK2, lineSpacing: 17,
      });
    }
  });
}

function stat(s, x, y, w, value, label, color) {
  card(s, x, y, w, 1.85);
  s.addText(value, {
    x: x + 0.25, y: y + 0.22, w: w - 0.5, h: 0.85, isTextBox: true, margin: 0,
    fontFace: H, fontSize: 42, bold: true, color: color || NAVY,
  });
  s.addText(label, {
    x: x + 0.25, y: y + 1.08, w: w - 0.5, h: 0.65, isTextBox: true, margin: 0,
    fontFace: B, fontSize: 13, color: INK2, lineSpacing: 16,
  });
}

function chartSlide(s, title, takeaway, img, aspect, notes) {
  head(s, title, takeaway);
  const maxH = 4.85;
  const iw = Math.min(8.0, maxH * aspect), ih = iw / aspect;
  s.addImage({ path: img, x: M, y: 1.85, w: iw, h: ih });
  const bx = M + iw + 0.45;
  const bw = W - bx - M;
  card(s, bx, 1.85, bw, Math.max(ih, 0.4 + notes.length * 1.35));
  notes.forEach((n, i) => {
    s.addText(n.t, {
      x: bx + 0.3, y: 2.1 + i * 1.35, w: bw - 0.6, h: 0.35, isTextBox: true, margin: 0,
      fontFace: B, fontSize: 15, bold: true, color: NAVY,
    });
    s.addText(n.d, {
      x: bx + 0.3, y: 2.45 + i * 1.35, w: bw - 0.6, h: 0.9, isTextBox: true, margin: 0,
      fontFace: B, fontSize: 13, color: INK2, lineSpacing: 17,
    });
  });
}

// ---------- 1 Titel --------------------------------------------------------
let s = pres.addSlide();
titleSlide(s,
  "WPM KI UND MANAGEMENT · KURZFASSUNG",
  "KI-gestützte Schichtplanung in der Pflege",
  "Was mathematische Optimierung gegenüber regelbasierter Excel-Planung leistet —\nund unter welchen Bedingungen sie es nicht tut.",
  "Prototyp und Evaluation über 270 Dienstpläne · Projektteam · Wintersemester");
s.addNotes("Kurzfassung in acht Folien. Wir zeigen die Aufgabe, unser Vorgehen, drei Kernergebnisse und die Antwort auf die Leitfrage.");

// ---------- 2 Die Aufgabe --------------------------------------------------
s = pres.addSlide();
head(s, "Die Aufgabe", "Dienstpläne in der Pflege entstehen überwiegend manuell in Excel.");

card(s, M, 1.85, W - 2 * M, 1.5, NAVY);
s.addText("Wie kann eine KI-gestützte Planungsempfehlung die Erstellung und kurzfristige "
  + "Anpassung eines Schichtplans gegenüber einer regelbasierten Excel-Planung unterstützen?", {
  x: M + 0.4, y: 2.1, w: W - 2 * M - 0.8, h: 1.0, isTextBox: true, margin: 0,
  fontFace: H, fontSize: 19, bold: true, color: WHITE, lineSpacing: 27,
});

stat(s, M, 3.7, 3.85, "66 %", "der Krankenhäuser schrieben 2024 Verluste", NAVY);
stat(s, M + 4.1, 3.7, 3.85, "15 %", "der Schichten bleiben trotz gesetzlicher\nUntergrenzen unterbesetzt", NAVY);
stat(s, M + 8.2, 3.7, 3.73, "§ 137i", "SGB V: Unterschreitung führt zu\nVergütungsabschlägen", ORANGE);

s.addText("Ein Dienstplan muss gleichzeitig Arbeitszeitrecht, gesetzliche Mindestbesetzung, "
  + "Qualifikationen und wechselnden Personalbedarf einhalten — und bei jedem kurzfristigen "
  + "Ausfall neu justiert werden.", {
  x: M, y: 5.75, w: W - 2 * M, h: 0.8, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 15, color: INK, lineSpacing: 22,
});
source(s, "DKI Krankenhaus Barometer 2025 · Wissenschaftliche Dienste des Bundestages, WD 8-3000-008/26");
s.addNotes("Kernbotschaft: Das ist kein reines Pflegethema, sondern ein wirtschaftliches. Untergrenzenverstoesse sind sanktionsbewehrt.");

// ---------- 3 Herangehensweise ---------------------------------------------
s = pres.addSlide();
head(s, "Herangehensweise", "Erst die Methode begründen, dann die Datengrundlage bauen — nicht umgekehrt.");

card(s, M, 1.85, 5.85, 4.6, "F7EEEA");
s.addText("Methodenwahl: kein Machine Learning", {
  x: M + 0.35, y: 2.1, w: 5.15, h: 0.4, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 17, bold: true, color: ORANGE,
});
s.addText([
  { text: "Keine zu lernende Zielvariable, keine historischen Planentscheidungen als Trainingsdaten", options: { bullet: true, breakLine: true } },
  { text: "Das Problem ist eine Zuordnung unter harten Nebenbedingungen mit konkurrierenden Zielen", options: { bullet: true, breakLine: true } },
  { text: "Einschlägig sind mathematische Optimierung und Constraint Programming", options: { bullet: true, breakLine: true } },
  { text: "Umgesetzt als MILP mit 2.429 Variablen und 4.232 Nebenbedingungen, gelöst mit dem freien Solver HiGHS", options: { bullet: true } },
], {
  x: M + 0.35, y: 2.6, w: 5.15, h: 3.6, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 13, color: INK2, lineSpacing: 19, paraSpaceAfter: 9,
});

card(s, M + 6.2, 1.85, 5.73, 4.6);
s.addText("Datengrundlage: synthetisch, aber hergeleitet", {
  x: M + 6.55, y: 2.1, w: 5.03, h: 0.4, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 17, bold: true, color: NAVY,
});
s.addText([
  { text: "Struktur aus den Rostering-Benchmarks (INRC-II, Nottingham)", options: { bullet: true, breakLine: true } },
  { text: "Werte aus deutschem Recht und amtlicher Statistik: ArbZG, PpUGV, TVöD-K, Destatis, PPR 2.0", options: { bullet: true, breakLine: true } },
  { text: "Belegschaftsgröße gerechnet, nicht geraten — über Pflegeaufwand und Bruttobedarf", options: { bullet: true, breakLine: true } },
  { text: "Keine personenbezogenen Daten, keine Gesundheitsdaten — Ausfälle sind reine Verfügbarkeitsereignisse", options: { bullet: true } },
], {
  x: M + 6.55, y: 2.6, w: 5.03, h: 3.6, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 13, color: INK2, lineSpacing: 19, paraSpaceAfter: 9,
});
source(s, "Vorgehen an CRISP-DM orientiert · Burke et al. (2004), Journal of Scheduling · Van den Bergh et al. (2013), EJOR");
s.addNotes("Wichtig fuer die Bewertung: Die Methodenwahl ist begruendet, ML wurde nicht als Default angenommen. Erwartbare Rueckfrage - ist das dann KI? Fachlich ja, Suche und Scheduling gehoeren zum Kern der KI. Umgangssprachlich nein, das Modell lernt nichts. Die Aufgabenstellung verlangt eine begruendete Methodenwahl, nicht ML.");

// ---------- 4 Umsetzung ----------------------------------------------------
s = pres.addSlide();
head(s, "Umsetzung", "Ein Datensatz, zwei Verfahren, eine unabhängige Prüfung.");

bulletRows(s, [
  { t: "Eine Datei als Datengrundlage", d: "1.288 Zeilen × 94 Spalten, Korn Mitarbeitender × Tag. Alle Grenzwerte stehen als Spalten im Datensatz — ändert sich die Rechtslage, ändert sich eine Zahl, nicht das Programm." },
  { t: "Zwei Verfahren auf identischen Daten", d: "Regelbasierte Heuristik als Excel-Äquivalent: Tag für Tag, nie zurücknehmen. MILP-Optimierung: alle 28 Tage gleichzeitig." },
  { t: "Die Prüfung ist vom Planer getrennt", d: "Eine eigene Funktion bewertet den fertigen Plan, ohne zu wissen, wer ihn erzeugt hat — sonst wäre der KPI-Vergleich zirkulär." },
], M, 1.95, 6.6, 1.45);

card(s, M + 7.2, 1.95, W - M - (M + 7.2), 4.3);
s.addText("Versuchsaufbau", {
  x: M + 7.55, y: 2.2, w: 4.3, h: 0.4, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 17, bold: true, color: NAVY,
});
s.addText([
  { text: "5 Zufallsseeds", options: { bullet: true, breakLine: true } },
  { text: "3 Personaldecken: 100 %, 90 %, 80 % des Bedarfs", options: { bullet: true, breakLine: true } },
  { text: "3 Ausfallszenarien: keine, verteilte Einzeltage, Ausfallwelle", options: { bullet: true, breakLine: true } },
  { text: "6 Verfahrensvarianten", options: { bullet: true, breakLine: true } },
  { text: "= 270 Dienstpläne", options: { bullet: false } },
], {
  x: M + 7.55, y: 2.7, w: 4.3, h: 3.2, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 13, color: INK2, lineSpacing: 19, paraSpaceAfter: 9,
});
s.addText("Prototyp live in Streamlit Cloud", {
  x: M, y: 6.35, w: W - 2 * M, h: 0.4, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 14, bold: true, color: ORANGE,
});
source(s, "Eine einzelne Instanz beweist nichts — die Personaldecke steuert, ob die Aufgabe überhaupt lösbar ist");
s.addNotes("Hier ggf. kurze Live-Demo: Szenario umschalten, Ausfall melden, Plan aendert sich in unter einer Sekunde.");

// ---------- 5 Ergebnis 1 ---------------------------------------------------
s = pres.addSlide();
chartSlide(s, "Ergebnis 1: Regelkonformität unter Knappheit",
  "Bei bedarfsgerechter Besetzung sind beide nahezu gleich regelkonform. Der Unterschied entsteht, wenn es eng wird.",
  IMG("01_regelkonformitaet.png"), 1.366, [
    { t: "Bei 80 % Personaldecke", d: "war kein einziger Plan der Baseline vollständig regelkonform — gegenüber 100 % der optimierten Pläne." },
    { t: "6,5 Untergrenzenverstöße je Plan", d: "gegenüber null. Das ist ein Rechtsrisiko nach § 137i SGB V, kein Qualitätsdetail." },
    { t: "113 unbesetzte Dienste", d: "lässt die Heuristik bei 80 % Decke stehen — die Optimierung 10, und jeden davon oberhalb der Untergrenze." },
  ]);
s.addNotes("Die Kernfolie fuer den wirtschaftlichen Teil: Der Mehrwert entsteht nicht im Normalbetrieb, sondern genau dort, wo es eng wird.");

// ---------- 6 Ergebnis 2 ---------------------------------------------------
s = pres.addSlide();
chartSlide(s, "Ergebnis 2: Vier von zehn arbeiten jedes Wochenende",
  "Gleiche Daten, gleiche Regeln — und schon bei bedarfsgerechter Decke ein völlig anderer Monat.",
  IMG("04_lastverteilung.png"), 2.221, [
    { t: "41 % gegen 0,3 %", d: "So groß ist der Anteil der Belegschaft, der in den Plänen der Heuristik an allen vier Wochenenden im Dienst ist." },
    { t: "Kein Machbarkeitsproblem", d: "Auf denselben Daten findet die Optimierung eine Verteilung, in der 88 % genau auf dem Richtwert von zwei Wochenenden liegen." },
    { t: "Für die Personalbindung", d: "ist das die relevanteste Zahl der ganzen Auswertung — sie taucht in keiner Besetzungsquote auf." },
  ]);
s.addNotes("Gepoolt ueber alle 15 Instanzen und 608 Personenplaene. Wochenend-Ueberschreitungen sind KEINE Rechtsverstoesse, sondern weiche Abweichungen vom Richtwert - Belastungsschutz, nicht Legalitaet.");

// ---------- 7 Ergebnis 3 ---------------------------------------------------
s = pres.addSlide();
chartSlide(s, "Ergebnis 3: Die Zielfunktion entscheidet",
  "Optimierung ist nur so gut wie die Ziele, die man ihr vorgibt — das war unser methodischer Kernbefund.",
  IMG("05_zielkonflikt.png"), 1.847, [
    { t: "Neu optimieren war schlechter", d: "als die simple Heuristik: nur rund ein Viertel der Dienste blieb bestehen. Der Monat wird faktisch neu gemacht." },
    { t: "Erst mit „wenig ändern“ im Modell", d: "stieg die Planstabilität auf 92 % — bei nahezu gleicher Besetzungsquote und in rund einer halben Sekunde." },
    { t: "Der Preis ist messbar", d: "Unter der Welle steigt die Spanne der Auslastung von 19 auf 26 Prozentpunkte. Welches Ziel gewinnt, ist eine Führungsfrage." },
  ]);
s.addNotes("Das ist unser methodischer Kernbefund und zugleich die ehrlichste Folie: Nicht das Verfahren entscheidet, sondern die Gewichtung der Ziele. Der Prototyp macht diesen Zielkonflikt entscheidbar, Excel macht ihn unsichtbar.");

// ---------- 8 Antwort auf die Leitfrage ------------------------------------
s = pres.addSlide();
s.background = { color: NAVY };
s.addText("Die Antwort auf unsere Leitfrage", {
  x: M, y: 0.6, w: W - 2 * M, h: 0.7, isTextBox: true, margin: 0,
  fontFace: H, fontSize: 32, bold: true, color: WHITE,
});
s.addText("Im End-to-End-Vergleich gewinnt die Optimierung jede einzelne Kennzahl.", {
  x: M, y: 1.35, w: W - 2 * M, h: 0.45, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 16, color: ICE, italic: true,
});

const facts = [
  ["99,7 %", "Besetzungsquote\nstatt 97,3 %"],
  ["0", "Untergrenzenverstöße\nstatt 2,60 je Plan"],
  ["25 Pp.", "Spanne der Auslastung\nstatt 32 Prozentpunkte"],
  ["22,8", "geänderte Dienste\nstatt 30,3 je Monat"],
];
facts.forEach((f, i) => {
  const x = M + i * 3.05;
  s.addShape(pres.ShapeType.roundRect, {
    x, y: 2.0, w: 2.85, h: 1.55, rectRadius: 0.08,
    fill: { color: "2A3670" }, line: { width: 0 },
  });
  s.addText(f[0], {
    x: x + 0.22, y: 2.18, w: 2.4, h: 0.6, isTextBox: true, margin: 0,
    fontFace: H, fontSize: 32, bold: true, color: ORANGE,
  });
  s.addText(f[1], {
    x: x + 0.22, y: 2.8, w: 2.4, h: 0.62, isTextBox: true, margin: 0,
    fontFace: B, fontSize: 12, color: ICE, lineSpacing: 15,
  });
});

s.addText([
  { text: "Bei der Erstellung  ", options: { bold: true, color: WHITE } },
  { text: "liegt der Mehrwert nicht in der Machbarkeit, sondern in Regelkonformität unter Knappheit und in Verteilungsgerechtigkeit. Ist genug Personal da, sichert auch eine Regelheuristik die Rechtskonformität — den Unterschied macht dann die Lastverteilung.", options: { color: ICE } },
], {
  x: M, y: 3.85, w: W - 2 * M, h: 0.7, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 15, lineSpacing: 22,
});
s.addText([
  { text: "Bei der Anpassung  ", options: { bold: true, color: WHITE } },
  { text: "liegt er in der Planstabilität — aber nur, wenn Stabilität ausdrücklich als Ziel modelliert wird.", options: { color: ICE } },
], {
  x: M, y: 4.55, w: W - 2 * M, h: 0.5, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 15, lineSpacing: 22,
});
s.addText([
  { text: "Beides zusammen  ", options: { bold: true, color: WHITE } },
  { text: "ergibt mehr als die Summe: Nur wenn Planung und Anpassung aus demselben System kommen, sinkt die Zahl der Planänderungen auf 22,8. Ein Optimierer als reine Feuerwehr auf bestehenden Excel-Plänen hebt die Rechtssicherheit, aber nicht die Entlastung.", options: { color: ICE } },
], {
  x: M, y: 5.05, w: W - 2 * M, h: 0.9, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 15, lineSpacing: 22,
});

s.addText("Unsere Empfehlung: Optimierung einführen, wo die Personaldecke knapp ist — "
  + "und die Gewichtung der Ziele als Führungsentscheidung behandeln, nicht als Konfigurationsdetail.", {
  x: M, y: 6.1, w: W - 2 * M, h: 0.7, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 15, bold: true, color: ORANGE, lineSpacing: 22,
});
s.addNotes("Die vier Zahlen sind Mittelwerte ueber die 30 gestoerten Plaene je Verfahren (Szenarien S1 und S2), also der Zustand nach Erstellung und Anpassung. Krankheitsbedingt ausgefallene Dienste sind nach dem Entgeltausfallprinzip (Paragraf 4 EFZG) gutgeschrieben. Abschluss. Wichtig fuer die Diskussion: Wir unterscheiden strikt zwischen gemessenen Ergebnissen und geschaetztem Business Impact. Gemessen sind Regelkonformitaet, Lastverteilung, Planstabilitaet und Rechenzeit. Nicht gemessen, nur plausibel: Reduktion des manuellen Planungsaufwands, Wirkung auf Fluktuation, vermiedene Bettensperrungen.");

// ---------- schreiben ------------------------------------------------------
const out = path.join(BASE, "Kurzpraesentation_Schichtplanung.pptx");
pres.writeFile({ fileName: out }).then(() => console.log("geschrieben:", out));
