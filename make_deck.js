// Praesentation zum Use Case "KI-gestuetzte Schichtplanung in der Pflege"
// 15 Minuten, 14 Folien. Alle Zahlen stammen aus evaluation_results.csv
// bzw. aus den in ERGEBNISSE.md belegten Quellen.
//
//   node make_deck.js   ->  Praesentation_Schichtplanung.pptx

const pptxgen = require("pptxgenjs");
const path = require("path");

const BASE = __dirname;
const IMG = (n) => path.join(BASE, "abbildungen", n);

// Palette: Navy dominant, Eisblau tragend, Orange als Akzent -
// dasselbe Orange wie in den Diagrammen.
const NAVY = "1E2761";
const NAVY_D = "141C46";
const ICE = "CADCFC";
const ICE_L = "EEF4FE";
const ORANGE = "EB6834";
const BLUE = "2A78D6";
const INK = "0B0B0B";
const INK2 = "52514E";
const MUTED = "898781";
const WHITE = "FFFFFF";

const H = "Cambria";      // Ueberschriften
const B = "Calibri";      // Fliesstext

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";               // 13.33 x 7.5 Zoll
pres.author = "Projektteam KI & Management";
pres.title = "KI-gestützte Schichtplanung in der Pflege";

const W = 13.33, HG = 7.5, M = 0.7;

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
        x: x + 0.45, y: yy + 0.32, w: w - 0.45, h: 0.42, isTextBox: true, margin: 0,
        fontFace: B, fontSize: 13, color: INK2,
      });
    }
  });
}

function stat(s, x, y, w, value, label, color) {
  card(s, x, y, w, 1.85);
  s.addText(value, {
    x: x + 0.25, y: y + 0.22, w: w - 0.5, h: 0.85, isTextBox: true, margin: 0,
    fontFace: H, fontSize: 46, bold: true, color: color || NAVY,
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
  card(s, bx, 1.85, bw, Math.max(ih, 2.2));
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
  "WPM KI UND MANAGEMENT · USE CASE",
  "KI-gestützte Schichtplanung in der Pflege",
  "Was eine Optimierung gegenüber regelbasierter Excel-Planung wirklich leistet —\nund unter welchen Bedingungen sie es nicht tut.",
  "Prototyp und Evaluation über 180 Dienstpläne · Projektteam · Wintersemester");
s.addNotes("Einstieg: Dienstpläne in der Pflege werden überwiegend manuell erstellt. Wir haben geprüft, ob und wann sich Optimierung lohnt. Die Antwort ist differenzierter als erwartet.");

// ---------- 2 Ausgangslage -------------------------------------------------
s = pres.addSlide();
head(s, "Warum Dienstplanung ein wirtschaftliches Thema ist",
  "Planungsqualität wirkt auf Erlöse, Sanktionsrisiko und Personalbindung.");
stat(s, M, 2.0, 3.85, "66 %", "der Krankenhäuser schrieben 2024 Verluste;\n70 % erwarten das auch für 2025", NAVY);
stat(s, M + 4.1, 2.0, 3.85, "15 %", "der Schichten bleiben trotz gesetzlicher\nUntergrenzen regelmäßig unterbesetzt", NAVY);
stat(s, M + 8.2, 2.0, 3.73, "§ 137i", "SGB V: Unterschreitung der Untergrenze\nführt zu Vergütungsabschlägen", ORANGE);
s.addText("Der übliche Ausweg bei Personalmangel ist die Bettensperrung — also bewusst " +
  "verzichtete Erlöse. Wer mit demselben Personal regelkonform planen kann, verschiebt " +
  "diese Schwelle.", {
  x: M, y: 4.35, w: W - 2 * M, h: 0.9, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 16, color: INK, lineSpacing: 24,
});
source(s, "DKI Krankenhaus Barometer 2025 (376 Häuser) · Wissenschaftliche Dienste des Bundestages WD 8-3000-008/26 · § 137i Abs. 5 SGB V");
s.addNotes("Kernbotschaft: Das ist kein reines Pflege- oder IT-Thema. Zwei Drittel der Häuser sind defizitär, und Untergrenzenverstöße sind sanktionsbewehrt.");

// ---------- 3 Restriktionen ------------------------------------------------
s = pres.addSlide();
head(s, "Was ein Dienstplan gleichzeitig einhalten muss",
  "Sechs Anforderungen, die sich gegenseitig widersprechen können.");
bulletRows(s, [
  { t: "Ruhezeit", d: "11 Stunden zwischen zwei Diensten (§ 5 ArbZG) — schließt den Spät-Früh-Wechsel aus" },
  { t: "Pausen und Höchstarbeitszeit", d: "30 bzw. 45 Minuten, werktäglich 8 Stunden (§§ 3, 4 ArbZG)" },
  { t: "Mindestbesetzung", d: "10 Patienten je Pflegekraft tags, 22 nachts (PpUGV § 6)" },
], M, 2.0, 5.7, 1.15);
bulletRows(s, [
  { t: "Qualifikation", d: "höchstens 10 % Pflegehilfskräfte; Auszubildende zählen nicht mit (PpUGV § 2)" },
  { t: "Wechselnde Belegung", d: "Personalbedarf schwankt täglich mit Belegung und Pflegeaufwand" },
  { t: "Kurzfristige Ausfälle", d: "Krankenstand in der Krankenpflege: 28 Fehltage im Jahr" },
], M + 6.3, 2.0, 5.7, 1.15);
source(s, "ArbZG · PpUGV · TVöD-K · TK-Gesundheitsreport");
s.addNotes("Wichtig: Diese Regeln stehen bei uns nicht im Programmcode, sondern als Spalten im Datensatz. Ändert sich die Rechtslage, ändert sich eine Zahl.");

// ---------- 4 Leitfrage ----------------------------------------------------
s = pres.addSlide();
s.background = { color: ICE_L };
s.addText("Leitfrage", {
  x: M, y: 1.6, w: 11.9, h: 0.5, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 14, bold: true, color: ORANGE, charSpacing: 2,
});
s.addText("Wie kann eine KI-gestützte Planungsempfehlung die Erstellung und " +
  "kurzfristige Anpassung eines Schichtplans gegenüber einer regelbasierten " +
  "Excel-Planung unterstützen?", {
  x: M, y: 2.15, w: 11.9, h: 1.8, isTextBox: true, margin: 0,
  fontFace: H, fontSize: 30, bold: true, color: NAVY, lineSpacing: 40,
});
s.addText([
  { text: "Zielsetzung: ", options: { bold: true } },
  { text: "ein lauffähiger Prototyp, der beide Verfahren auf identischer Datengrundlage " +
      "vergleicht — bewertet an nachvollziehbaren Kennzahlen statt an Eindrücken." },
], {
  x: M, y: 4.3, w: 11.9, h: 0.9, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 16, color: INK, lineSpacing: 24,
});
s.addNotes("Bewusst kein produktionsreifes System. Der Anspruch ist ein Prototyp, an dem sich die Frage beantworten lässt.");

// ---------- 5 Methodenauswahl ---------------------------------------------
s = pres.addSlide();
head(s, "Methodenauswahl: warum kein Machine Learning",
  "Die erste Erkenntnis des Projekts war eine Absage.");
card(s, M, 2.0, 5.85, 3.5, "F7EEEA");
s.addText("Machine Learning", {
  x: M + 0.35, y: 2.25, w: 5.15, h: 0.4, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 18, bold: true, color: ORANGE,
});
s.addText([
  { text: "Keine zu lernende Zielvariable", options: { bullet: true, breakLine: true } },
  { text: "Keine historischen Planentscheidungen als Trainingsdaten", options: { bullet: true, breakLine: true } },
  { text: "Regelkonformität lässt sich nicht „ungefähr“ lernen — sie ist binär", options: { bullet: true } },
], {
  x: M + 0.35, y: 2.75, w: 5.15, h: 2.5, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 14, color: INK2, lineSpacing: 20, paraSpaceAfter: 8,
});
card(s, M + 6.2, 2.0, 5.73, 3.5);
s.addText("Mathematische Optimierung", {
  x: M + 6.55, y: 2.25, w: 5.03, h: 0.4, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 18, bold: true, color: NAVY,
});
s.addText([
  { text: "Zuordnungsproblem unter harten Nebenbedingungen", options: { bullet: true, breakLine: true } },
  { text: "Mehrere konkurrierende Ziele — gewichtbar in einer Zielfunktion", options: { bullet: true, breakLine: true } },
  { text: "Etabliertes Verfahren für Nurse Rostering (Burke et al. 2004)", options: { bullet: true } },
], {
  x: M + 6.55, y: 2.75, w: 5.03, h: 2.5, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 14, color: INK2, lineSpacing: 20, paraSpaceAfter: 8,
});
s.addText("Umgesetzt als gemischt-ganzzahliges Modell mit 2.338 Variablen und 4.066 " +
  "Nebenbedingungen, gelöst mit dem freien Solver HiGHS.", {
  x: M, y: 5.75, w: W - 2 * M, h: 0.6, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 15, color: INK, lineSpacing: 22,
});
source(s, "Burke et al. (2004), Journal of Scheduling · Van den Bergh et al. (2013), EJOR");
s.addNotes("Diese Folie ist wichtig für die Bewertung: Methodenwahl begründet, nicht ML als Default angenommen.");

// ---------- 6 Daten --------------------------------------------------------
s = pres.addSlide();
head(s, "Datengrundlage: synthetisch, aber hergeleitet",
  "Keine personenbezogenen Daten, keine Gesundheitsdaten — als Konstruktionsprinzip.");
bulletRows(s, [
  { t: "Eine Station, 30 Betten, 23 Mitarbeitende", d: "28 Planungstage plus 28 Tage Historie, 1.288 Zeilen in einer Datei" },
  { t: "Werte aus dokumentierten Quellen", d: "Bettenauslastung 72 % und Verweildauer 7,1 Tage (Destatis), Pflegeaufwand nach PPR 2.0, Teilzeit- und Fachkraftquoten" },
  { t: "Belegschaftsgröße gerechnet, nicht geschätzt", d: "Netto-Bedarf 11,9 Vollkräfte, Ausfallquote 21,9 % → Brutto-Bedarf 15,2 Vollkräfte" },
], M, 2.0, 6.9, 1.25);
card(s, M + 7.4, 1.95, 4.53, 3.6);
s.addText("Datenschutz", {
  x: M + 7.75, y: 2.2, w: 3.9, h: 0.4, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 17, bold: true, color: NAVY,
});
s.addText([
  { text: "Mitarbeitende nur als pseudonyme IDs", options: { bullet: true, breakLine: true } },
  { text: "Ausfälle sind reine Verfügbarkeit — kein Grund, keine Diagnose, auch nicht aggregiert", options: { bullet: true, breakLine: true } },
  { text: "Ein Prüfskript verweigert die Freigabe, wenn eine entsprechende Spalte auftaucht", options: { bullet: true } },
], {
  x: M + 7.75, y: 2.7, w: 3.9, h: 2.7, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 13, color: INK2, lineSpacing: 19, paraSpaceAfter: 8,
});
source(s, "Reproduzierbar über festen Seed · Generator und Prüfskript liegen dem Bericht bei");
s.addNotes("Der Datensatz ist das Fundament. Fester Seed heißt: jederzeit exakt neu erzeugbar.");

// ---------- 7 Prototyp -----------------------------------------------------
s = pres.addSlide();
head(s, "Der Prototyp", "Zwei Verfahren, dieselben Daten, dieselbe unabhängige Bewertung.");
bulletRows(s, [
  { t: "Regelbasierte Planung (Baseline)", d: "Tag für Tag, Schicht für Schicht die am wenigsten ausgelastete regelkonforme Person — das Vorgehen einer manuellen Excel-Planung" },
  { t: "MILP-Optimierung", d: "betrachtet alle 28 Tage gleichzeitig und kann eine heute ungünstige Zuweisung in Kauf nehmen, wenn sie den Gesamtplan verbessert" },
  { t: "Reaktive Umplanung", d: "hält den bestehenden Plan fest und besetzt nur das Nötige neu, statt den Monat neu zu rechnen" },
  { t: "Getrennte Prüfinstanz", d: "bewertet den fertigen Plan unabhängig vom Verfahren — sonst wäre der Vergleich zirkulär" },
], M, 1.95, 11.9, 1.2);
source(s, "Lauffähig als Web-Anwendung; Rechenzeit 8–15 Sekunden je Monatsplan, unter einer Sekunde je Umplanung");
s.addNotes("Hier ggf. kurze Live-Demo der Streamlit-App: Szenario umschalten, Ausfall melden, Plan ändert sich.");

// ---------- 8 Versuchsaufbau ----------------------------------------------
s = pres.addSlide();
head(s, "Versuchsaufbau", "Eine einzelne Instanz beweist nichts — also 15 davon.");
stat(s, M, 2.0, 2.75, "5", "Zufallsseeds:\nandere Belegung, Belegschaft, Ausfälle", NAVY);
stat(s, M + 3.0, 2.0, 2.75, "3", "Personaldecken:\n100 %, 90 %, 80 % des Bedarfs", NAVY);
stat(s, M + 6.0, 2.0, 2.75, "3", "Ausfallszenarien:\nkeine, verteilt, Ausfallwelle", NAVY);
stat(s, M + 9.0, 2.0, 2.93, "180", "Pläne insgesamt,\nvier Verfahrensvarianten", ORANGE);
s.addText("Die Personaldecke steuert, ob die Aufgabe überhaupt lösbar ist — ohne diese " +
  "Variation hätten wir nur gemessen, dass beide Verfahren eine leichte Aufgabe lösen. " +
  "Die beiden Ausfallszenarien tragen bewusst dasselbe Ausfallvolumen und unterscheiden " +
  "sich nur in der Struktur: verteilte Einzeltage gegen mehrtägige Episoden in einer " +
  "Welle. Nur so ist ein Unterschied der Struktur zuzurechnen und nicht dem Umfang.", {
  x: M, y: 4.4, w: W - 2 * M, h: 1.2, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 15, color: INK, lineSpacing: 22,
});
source(s, "Alle Rohergebnisse in evaluation_results.csv, eine Zeile je Plan");
s.addNotes("80 Prozent Personaldecke ist keine exotische Annahme — sie bildet eine real unterbesetzte Station ab.");

// ---------- 9 Ergebnis Regelkonformitaet ----------------------------------
s = pres.addSlide();
chartSlide(s, "Ergebnis 1: Regelkonformität unter Knappheit",
  "Bei bedarfsgerechter Besetzung sind beide gleich gut. Der Unterschied entsteht erst, wenn es eng wird.",
  IMG("01_regelkonformitaet.png"), 1.451, [
    { t: "Bei 80 % Personaldecke", d: "war kein einziger Plan der Baseline vollständig regelkonform — gegenüber 100 % der optimierten Pläne." },
    { t: "Im Mittel 4,3 Untergrenzen­verstöße je Plan", d: "gegenüber null. Das ist ein Rechtsrisiko nach § 137i SGB V, kein Qualitätsdetail." },
    { t: "Besetzungsquote", d: "95,4 % gegenüber 100,0 % — 104 unbesetzte Dienste gegenüber keinem." },
  ]);
s.addNotes("Das ist die Kernfolie. Betonen: Der Mehrwert entsteht nicht im Normalbetrieb, sondern genau dort, wo es eng wird.");

// ---------- 10 Ergebnis Lastverteilung ------------------------------------
s = pres.addSlide();
chartSlide(s, "Ergebnis 2: Verteilung der Arbeitslast",
  "Gleiche Besetzungsquote, sehr unterschiedliche Belastung der einzelnen Person.",
  IMG("04_lastverteilung.png"), 1.805, [
    { t: "Spanne von 33 auf 7 Prozentpunkte", d: "Abstand zwischen der am geringsten und der am stärksten ausgelasteten Person." },
    { t: "Wochenend-Richtwerte", d: "Die Baseline überschreitet sie im Schnitt 16-mal je Plan, die Optimierung kein einziges Mal." },
    { t: "Warum", d: "Die Heuristik entscheidet lokal optimal und erzeugt dadurch systematisch Ungleichverteilung." },
  ]);
s.addNotes("Für die Personalbindung ist das der relevante Wert: Zwei Pläne mit identischer Besetzungsquote fühlen sich sehr unterschiedlich an.");

// ---------- 11 Ergebnis Planstabilitaet -----------------------------------
s = pres.addSlide();
chartSlide(s, "Ergebnis 3: Reaktion auf kurzfristige Ausfälle",
  "Zwei Befunde — einer über die Zielfunktion, einer über die Messung selbst.",
  IMG("03_planstabilitaet.png"), 2.027, [
    { t: "Links: die Zielfunktion", d: "Neu zu optimieren erhält nur 51 % der Dienste. Erst mit „möglichst wenig ändern“ im Modell steigt der Wert auf 95 %." },
    { t: "Rechts: derselbe Ausgangsplan", d: "Erst so sind die Verfahren vergleichbar. Unter der Welle: 91 % gegen 87 % — die Optimierung in 14 von 15 Instanzen vorn." },
    { t: "Warum das nötig war", d: "Wer jedes Verfahren gegen seinen eigenen Plan misst, belohnt den schlechteren Planer: Einen schwachen Plan zu halten ist billig." },
  ]);
s.addNotes("Zwei Punkte. Erstens die Zielfunktion - unser methodischer Kernbefund. Zweitens: Wir hatten die Planstabilitaet zunaechst falsch gemessen, jedes Verfahren gegen seinen eigenen Ausgangsplan. Der Greedy-Plan ist schlechter, und einen schlechten Plan unveraendert zu lassen kostet nichts. Auf identischem Ausgangsplan dreht sich das Ergebnis. Diesen Fehler zeigen wir offen - er ist lehrreicher als das Ergebnis.");

// ---------- 12 Ergebnis Ausfallstruktur -----------------------------------
s = pres.addSlide();
chartSlide(s, "Ergebnis 4: Der Zielkonflikt, den Excel nicht sichtbar macht",
  "Gleichmäßige Last oder stabiler Plan — unter der Ausfallwelle ist beides zugleich nicht zu haben.",
  IMG("05_zielkonflikt.png"), 1.847, [
    { t: "Nicht die Welle", d: "Bei vollständiger Neuplanung hält die Optimierung die Spanne auch unter S2 auf 16 Punkten. Die Heuristik liegt bei 33." },
    { t: "Sondern die Zielfunktion", d: "Gewicht 200 für „nicht ändern“ gegen 0,02 für Lastausgleich. Dann füllt das Modell nur noch Lücken — wie die Heuristik." },
    { t: "Eine Führungsfrage", d: "Welches Ziel schwerer wiegt, entscheidet nicht das Verfahren. Der Prototyp macht den Preis beider Optionen sichtbar." },
  ]);
s.addNotes("Haeufige Rueckfrage: Warum ist der Abstand bei Spanne und Stabilitaet unter S2 so klein? Drei Punkte. Erstens: Er liegt an der Zielfunktion, nicht an der Welle - bei voller Neuplanung bleibt die Optimierung klar vorn. Zweitens: Die Heuristik erreicht ihre Spanne teilweise dadurch, dass sie 3,9 Dienste gar nicht besetzt - unbesetzte Dienste erzeugen weder Auslastung noch Planaenderung. Drittens: Auf allen anderen Kennzahlen ist der Abstand unter S2 riesig - 100 gegen 97,9 Prozent Besetzung, null gegen 1,2 harte Verstoesse.");

// ---------- 13 Business Impact --------------------------------------------
s = pres.addSlide();
head(s, "Business Impact", "Strikt getrennt: was wir gemessen haben und was wir nur vermuten.");
card(s, M, 2.0, 5.85, 3.9, "E8F1E8");
s.addText("Gemessen", {
  x: M + 0.35, y: 2.25, w: 5.15, h: 0.4, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 18, bold: true, color: "0C6B2E",
});
s.addText([
  { text: "Regelkonformität unter Knappheit: 100 % gegenüber 0 % der Pläne", options: { bullet: true, breakLine: true } },
  { text: "Ungleichverteilung der Last um Faktor fünf reduziert — aber nur ohne Ausfallwelle", options: { bullet: true, breakLine: true } },
  { text: "Umplanung auf identischem Plan: 15 statt 25 Änderungen", options: { bullet: true, breakLine: true } },
  { text: "Umplanung in unter einer Sekunde", options: { bullet: true } },
], {
  x: M + 0.35, y: 2.75, w: 5.15, h: 2.9, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 14, color: INK2, lineSpacing: 20, paraSpaceAfter: 8,
});
card(s, M + 6.2, 2.0, 5.73, 3.9, "F7F2E8");
s.addText("Geschätzt — nicht belegt", {
  x: M + 6.55, y: 2.25, w: 5.03, h: 0.4, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 18, bold: true, color: "8A5A12",
});
s.addText([
  { text: "Reduktion des manuellen Planungsaufwands", options: { bullet: true, breakLine: true } },
  { text: "Wirkung gleichmäßigerer Belastung auf Zufriedenheit und Fluktuation", options: { bullet: true, breakLine: true } },
  { text: "Vermiedene Bettensperrungen und Sanktionen", options: { bullet: true, breakLine: true } },
  { text: "Alle drei erfordern eine Erhebung im Betrieb, keine Simulation", options: { bullet: true } },
], {
  x: M + 6.55, y: 2.75, w: 5.03, h: 2.9, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 14, color: INK2, lineSpacing: 20, paraSpaceAfter: 8,
});
s.addNotes("Diese Trennung ist bewertungsrelevant: gemessene Prototyp-Ergebnisse gegen geschätztes Potenzial.");

// ---------- 13 Limitationen ------------------------------------------------
s = pres.addSlide();
head(s, "Limitationen und Risiken", "Was die Untersuchung nicht hergibt.");
bulletRows(s, [
  { t: "Fünf Seeds sind wenig", d: "Die Streuungen tragen die Kernaussagen, für Inferenzstatistik reicht die Stichprobe nicht" },
  { t: "Die Baseline ist keine echte Excel-Planung", d: "Sie ist konsistenter und schneller als ein Mensch — der reale Unterschied dürfte größer sein" },
  { t: "Gewichte sind gesetzt, nicht hergeleitet", d: "Wie stark Unterbesetzung gegen Lastverteilung zählt, ist eine Managemententscheidung" },
], M, 1.95, 5.7, 1.3);
bulletRows(s, [
  { t: "Alle Daten sind synthetisch", d: "Die Höhe der Kennzahlen ist nicht auf eine konkrete Station übertragbar" },
  { t: "Optimierung ersetzt kein Personal", d: "Bei extremer Knappheit verwaltet auch das beste Verfahren nur noch den Mangel" },
  { t: "Verantwortung bleibt beim Menschen", d: "Der Prototyp liefert eine Empfehlung, keine Freigabe — die Leitung entscheidet" },
], M + 6.3, 1.95, 5.7, 1.3);
s.addNotes("Ehrlichkeit ist hier ein Pluspunkt. Besonders der zweite Punkt links: Wir überschätzen unsere eigene Baseline bewusst nicht.");

// ---------- 14 Fazit -------------------------------------------------------
s = pres.addSlide();
s.background = { color: NAVY };
s.addText("Fazit", {
  x: M, y: 0.9, w: 11.9, h: 0.6, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 14, bold: true, color: ORANGE, charSpacing: 2,
});
s.addText("Optimierung schlägt Heuristik dann,\nwenn die richtigen Ziele im Modell stehen.", {
  x: M, y: 1.5, w: 11.9, h: 1.5, isTextBox: true, margin: 0,
  fontFace: H, fontSize: 34, bold: true, color: WHITE, lineSpacing: 44,
});
s.addText([
  { text: "Bei der Erstellung ", options: { bold: true, color: ICE } },
  { text: "liegt der Mehrwert nicht in der Machbarkeit, sondern in Regelkonformität unter Knappheit und in der Verteilungsgerechtigkeit. Ist genug Personal da, genügt auch eine Regelheuristik.", options: { color: ICE } },
], {
  x: M, y: 3.35, w: 11.9, h: 1.0, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 16, lineSpacing: 24,
});
s.addText([
  { text: "Bei der Anpassung ", options: { bold: true, color: ICE } },
  { text: "liegt er in der Planstabilität — aber nur, wenn Stabilität ausdrücklich als Ziel modelliert wird. Eine bloße Neuoptimierung ist für die Mitarbeitenden schlechter als die Heuristik.", options: { color: ICE } },
], {
  x: M, y: 4.45, w: 11.9, h: 1.0, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 16, lineSpacing: 24,
});
s.addText("Empfehlung: Optimierung dort einführen, wo Stationen dauerhaft knapp besetzt " +
  "sind — und Planstabilität von Anfang an als Ziel mitgeben, nicht als Nebeneffekt erhoffen.", {
  x: M, y: 5.75, w: 11.9, h: 0.9, isTextBox: true, margin: 0,
  fontFace: B, fontSize: 16, bold: true, color: WHITE, lineSpacing: 24,
});
s.addNotes("Schluss: Die Frage war nicht, ob Optimierung besser ist, sondern wann und warum. Danke — Fragen?");

pres.writeFile({ fileName: path.join(BASE, "Praesentation_Schichtplanung.pptx") })
  .then((f) => console.log("geschrieben:", f));
