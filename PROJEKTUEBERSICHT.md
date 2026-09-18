# Projektübersicht: KI-gestützte Schichtplanung in der Pflege

**Stand:** finale Version · Datensatz 2.1.0, Seed 20261133 · Evaluation über 270 Pläne

Dieses Dokument erklärt das Gesamtprojekt in einem Zug: was gebaut wurde, wie es
funktioniert, woher die Daten stammen, auf welche Rechtsgrundlagen sie sich stützen, wie die
Aufgabenstellung beantwortet wird und was am Ende herauskommt. Die Detaildokumente sind
`DATENKONZEPT.md` (Datenherkunft, Annahmenregister) und `ERGEBNISSE.md` (vollständige
Evaluation).

---

## 1. Was das Projekt ist

Ein **Prototyp**, der einen Dienstplan für eine Krankenhausstation über 28 Tage erstellt und
nach kurzfristigen Ausfällen anpasst — einmal mit einer regelbasierten Heuristik (Ersatz für
die manuelle Excel-Planung) und einmal mit mathematischer Optimierung. Beide Verfahren
arbeiten auf **demselben Datensatz**, unter denselben Regeln, in denselben Ausfallszenarien.
Ein drittes, verfahrensunabhängiges Modul bewertet die fertigen Pläne.

**Fallstudie:** Normalstation Innere Medizin / Kardiologie, 30 Betten, 23 Mitarbeitende,
28 Planungstage plus 28 Tage Historie.

**Nicht enthalten:** ärztliche Dienstplanung, mehrere Stationen, Springerpools,
Produktionsreife. Der Umfang ist bewusst klein gehalten (Projektvorgabe 8).

---

## 2. Aufbau des GitHub-Repositorys

Alle Dateien liegen flach im Wurzelverzeichnis. Es gibt vier Gruppen.

### Daten und ihre Erzeugung

| Datei | Funktion |
|---|---|
| `schichtplan_datensatz.csv` | **Die Datengrundlage.** Eine einzige Datei, 1.288 Zeilen × 94 Spalten |
| `generate_dataset.py` | Erzeugt diese Datei deterministisch aus dokumentierten Parametern (fester Seed) |
| `validate_dataset.py` | Prüft sie gegen Schema, Arbeitsrecht, Erfüllbarkeit, PpUGV, Datenschutz |

### Planungslogik

| Datei | Funktion |
|---|---|
| `planner.py` | Beide Planungsverfahren plus die unabhängige Bewertung. Kein Streamlit — testbar |
| `test_planner.py` | Rund 50 Prüfungen: beide Verfahren, alle Szenarien, reaktive Umplanung, Export |

### Anwendung

| Datei | Funktion |
|---|---|
| `streamlit_app.py` | Die Oberfläche. Enthält **keine** Planungslogik, nur Darstellung |
| `requirements.txt` | Abhängigkeiten für Streamlit Community Cloud |

### Evaluation und Abgabeartefakte

| Datei | Funktion |
|---|---|
| `campaign.py` | Evaluationskampagne: 15 Instanzen × 3 Szenarien × 6 Varianten = 270 Pläne |
| `evaluation_results.csv` | Rohergebnisse, eine Zeile je Plan |
| `sensitivitaet.py` / `.csv` | Sensitivitätsanalyse der Zielgewichte |
| `wochenend_analyse.py` / `wochenend_verteilung.csv` | Verteilung der Wochenenddienste über 608 Personenpläne |
| `make_charts.py` → `abbildungen/` | Fünf Abbildungen, ausschließlich aus den Rohdaten erzeugt |
| `make_deck.js` → `.pptx` | Ausführliche Präsentation (16 Folien) |
| `make_kurzdeck.js` → `.pptx` | Kurzpräsentation (8 Folien) |
| `make_gantt.py` | Gantt-Diagramm des Projektverlaufs |
| `DATENKONZEPT.md`, `ERGEBNISSE.md`, `HANDOUT.md`, `README.md` | Dokumentation |

**Das Konstruktionsprinzip:** Jede Zahl in Bericht und Präsentation stammt aus
`evaluation_results.csv` und wird von einem Skript dort herausgelesen — nichts ist von Hand
eingetragen. Wer die Kampagne neu rechnet, bekommt dieselben Abbildungen.

---

## 3. Die Anwendung in Streamlit

Die App läuft auf Streamlit Community Cloud und lädt beim Start
`schichtplan_datensatz.csv` aus dem Repository. Über den Uploader lässt sich eine eigene
Variante einspielen.

### Steuerung in der Seitenleiste

- **Verfahren** — Regelbasiert (Baseline) oder MILP-Optimierung
- **Ausfallszenario** — S0 (keine Ausfälle), S1 (verteilte Einzeltage), S2 (Ausfallwelle)
- **Reaktiv umplanen** — an: der bestehende Plan wird als Ausgangspunkt genutzt und nur dort
  aufgebrochen, wo nötig; aus: der Monat wird vollständig neu gerechnet
- **Priorität der Optimierung** — Planungsruhe / Ausgewogen / Verteilungsgerechtigkeit.
  Stellt das Gewicht für Lastausgleich in der Zielfunktion (Abschnitt 8)
- **Rechenzeit je Plan** — Abbruchgrenze für den Solver
- **Zusätzlicher Ausfall** — eine Person für einen oder mehrere Tage krankmelden und den
  Plan live neu rechnen lassen

### Die sieben Reiter

1. **Dienstplan** — die Planmatrix Person × Tag mit Früh/Spät/Nacht, dazu CSV-Export des
   vollständigen Datensatzes plus Ergebnisspalte `assigned_shift`
2. **Verfahrensvergleich** — beide Verfahren nebeneinander auf allen KPIs. Drei Modi:
   *End-to-End* (jedes Verfahren plant und repariert selbst — beantwortet die Leitfrage) und
   zwei Kontrollmodi mit gemeinsamem Ausgangsplan
3. **Bedarf & Besetzung** — je Tag und Schicht: gesetzliche Untergrenze, fachliche
   Sollbesetzung, tatsächliche Besetzung
4. **Prüfhinweise** — jede einzelne Regelabweichung mit Person, Datum und Begründung
5. **Arbeitszeit** — Ist gegen Soll je Person, Zeitkonto, Abweichungen
6. **Mitarbeitende** — Stammdaten, Qualifikationen, Verfügbarkeiten
7. **Daten & Regeln** — Herkunft jeder Regel, Erklärung beider Verfahren, methodische
   Hinweise

Die Kopfzeile zeigt bei jedem Lauf Verfahren, Rechenzeit, Modellgröße und aktive Priorität.

---

## 4. Wie der Datensatz aufgebaut ist

### Eine Datei, ein Korn

Der gesamte Datensatz ist **eine** CSV mit dem Korn **Mitarbeitender × Kalendertag**:
23 Mitarbeitende × 56 Tage = 1.288 Zeilen, 94 Spalten. Das ist bewusst gewählt: Die
Planungsentscheidung selbst — „welchen Dienst bekommt Person *i* am Tag *d*?" — ist genau
eine Zeile. Der Preis ist Redundanz: Stationsdaten und Regelwerk stehen in allen 1.288
Zeilen. Das verletzt die dritte Normalform, macht die Datei aber ohne Join lesbar und in
Streamlit direkt hochladbar. Das Prüfskript verifiziert, dass die redundanten Spalten
konsistent sind.

### Die Spaltenblöcke und wozu sie dienen

| Block | Beispielspalten | Wofür gebraucht |
|---|---|---|
| **Schlüssel & Kalender** | `employee_id`, `date`, `period`, `is_weekend`, `is_holiday` | Primärschlüssel; `period` trennt Historie von Planhorizont |
| **Mitarbeiterstammdaten** | `employment_pct`, `max_total_minutes`, `max_consecutive_shifts`, `max_weekends`, `max_night_shifts`, `night_eligible`, `ppug_countable`, `is_ward_lead` | Vertrags- und Arbeitszeitgrenzen je Person; entscheiden, wer wann eingeplant werden **darf** |
| **Belegung** | `census_1200`, `census_0000`, `admissions`, `isolation_patients`, `care_minutes_total` | Treiben den Personalbedarf; die Bezugszeitpunkte folgen der PpUG-Nachweisvereinbarung |
| **Bedarf je Schicht** | `ppug_min_*`, `required_*`, `min_fachkraft_*`, `max_hilfskraft_*`, `azubi_slots_*` | Wie viele Personen welcher Qualifikation je Schicht nötig sind |
| **Verfügbarkeit & Wünsche** | `available`, `availability_type`, `request_off_weight`, `request_on_*` | Urlaub, Fortbildung, Langzeitabwesenheit; Dienstwünsche mit Gewicht 1–3 |
| **Historie** | `history_shift` | Die Vorperiode — ohne sie wüsste der Planer am 1. Tag nicht, wer gerade Nachtdienst hatte |
| **Ausfallszenarien** | `absence_s1`, `absence_s2` + Vorlaufzeiten | Die simulierten kurzfristigen Ausfälle, je Szenario eine Spalte |
| **Station & Schichten** | `beds`, `ppug_ratio_day/night`, `shift_*_start/end/net_min`, `shift_*_forbidden_next` | Stationsstammdaten und Schichtdefinitionen |
| **Regelwerk** | `rule_min_rest_h`, `rule_max_daily_h`, `rule_max_helper_share`, … | **Alle Grenzwerte als Zahlen im Datensatz** |
| **Metadaten** | `dataset_version`, `seed` | Macht jeden exportierten Plan auf seine Datenversion rückführbar |

### Zwei Entscheidungen, die den Unterschied machen

**Regeln stehen in den Daten, nicht im Code.** Ruhezeit, Höchstarbeitszeit,
Verhältniszahlen und Qualifikationsvorgaben sind `rule_*`-Spalten. Ändert sich die
Rechtslage, ändert sich eine Zahl in der CSV — nicht das Programm. Der Prototyp hat keine
fest verdrahteten Grenzwerte.

**Zwei getrennte Nachfragegrößen.** Je Schicht stehen **zwei** Besetzungszahlen im Datensatz:

- `ppug_min_F/S/N` = ⌈Patienten ÷ Verhältniszahl⌉, die **gesetzliche Untergrenze**. Ihre
  Unterschreitung ist ein Rechtsverstoß — eine harte Nebenbedingung.
- `required_F/S/N` = die **fachliche Sollbesetzung** aus dem Pflegeaufwand nach PPR-2.0-Logik.
  Ihre Unterschreitung ist Unterbesetzung — eine Qualitätskennzahl.

Ohne diese Trennung ließe sich die betriebswirtschaftliche Kernaussage gar nicht formulieren:
Ein Plan kann das Gesetz einhalten und trotzdem fachlich unterbesetzt sein. Genau darauf weist
das Gutachten der Wissenschaftlichen Dienste des Bundestages hin — trotz Untergrenzen bleiben
rund 15 % der Schichten regelmäßig unterbesetzt.

---

## 5. Woher die Daten stammen

Die Daten sind **vollständig synthetisch**, aber nicht erfunden. Struktur und Werte kommen aus
zwei verschiedenen Quellen.

### Die Struktur: internationale Referenzmodelle

Welche Felder ein Rostering-Datensatz überhaupt braucht, ist in der Forschung standardisiert.
Wir orientieren uns an der **Second International Nurse Rostering Competition (INRC-II)** und
an den **Nurse Rostering Benchmark Instances** der University of Nottingham. Von dort stammen
das Instanzformat, die Trennung in harte und weiche Restriktionen und die Systematik der
Dienstwünsche.

### Die Werte: deutsches Regelwerk und amtliche Statistik

Die internationalen Benchmarks liefern die Form, nicht die Zahlen — ihre Instanzen stammen aus
belgischen, britischen und niederländischen Häusern mit anderen Arbeitszeitregeln. Alle
inhaltlichen Parameter sind deshalb aus deutschen Quellen abgeleitet:

| Parameter | Wert | Quelle |
|---|---|---|
| Bettenauslastung | 72,0 % (2024) | Destatis, Krankenhausstatistik 2024 |
| Verweildauer | 7,1 Tage (2024) | Destatis, ebenda |
| Teilzeitquote Pflegedienst | 57,4 % | Statistik Sachsen, Beschäftigte in Krankenhäusern 2024 |
| Anteil examinierter Fachkräfte | 82,4 % | ebenda |
| Vollkräfte je Kopf | 0,805 | ebenda |
| AU-Tage Krankenpflege | 28 Tage/Jahr (Ø aller Beschäftigten 18,6) | TK-Gesundheitsreport |
| Pflegegrundwert | 33 min je Patient und Tag (123 bei Isolation) | PPBV / PPR 2.0 |
| Fallwert | 75 min je Aufnahme | PPBV / PPR 2.0 |
| Spannweite Pflegeaufwand | 59 bis 427 min je Patient und Tag | Wissenschaftliche Dienste des Bundestages, WD 8-3000-008/26 |

**Die Belegschaftsgröße ist gerechnet, nicht geraten.** Aus Betten × Auslastung folgt der
Patientenbestand, daraus über die PPR-Minutenwerte der Pflegeaufwand, daraus der
Netto-Personalbedarf. Auf den Nettobedarf werden die Ausfallzeiten aufgeschlagen — 30 Urlaubs-,
20 AU- und 5 Fortbildungstage von 251 Arbeitstagen — und daraus ergibt sich der
Bruttopersonalbedarf und damit die Kopfzahl. Die Kette ist im Datenkonzept vollständig als
Data Lineage dokumentiert (Anforderung aus T2).

---

## 6. Welche Rechtsgrundlagen verwendet werden — und warum

### Arbeitszeitgesetz (ArbZG)

| Regel | Wert | Fundstelle |
|---|---|---|
| Werktägliche Höchstarbeitszeit | 8 h, auf 10 h verlängerbar bei Ausgleich | § 3 |
| Ruhepause | ≥ 30 min bei > 6–9 h, ≥ 45 min bei > 9 h | § 4 |
| **Ruhezeit** | **11 h ununterbrochen** | § 5 Abs. 1 |
| Ausnahme Krankenhaus | Verkürzung um bis zu 1 h mit Ausgleich | § 5 Abs. 2 |
| Nachtarbeit | werktäglich 8 h, 10 h nur mit Ausgleich | § 6 Abs. 2 |
| Menschengerechte Gestaltung | gesicherte arbeitswissenschaftliche Erkenntnisse | § 6 Abs. 1 |

**Warum:** Das ArbZG gilt zwingend für alle Arbeitnehmer in Deutschland. Ein Dienstplan, der
die 11-Stunden-Ruhezeit verletzt, ist nicht umsetzbar — unabhängig davon, wie gut er sonst
aussieht. Deshalb sind diese Regeln **harte** Nebenbedingungen in beiden Verfahren.

Aus § 5 folgt eine Modellierung, die nicht gesetzt, sondern **gerechnet** ist: Mit unseren
Dienstzeiten ergibt der Wechsel Spätdienst (Ende 21:30) → Frühdienst (Beginn 06:00) nur
8,5 Stunden Ruhezeit und ist damit unzulässig — auch mit der Krankenhausausnahme. Der
klassische „Spät-Früh-Wechsel" ist im Datensatz deshalb keine Präferenz, sondern eine harte
Restriktion mit Rechtsgrundlage.

### Pflegepersonaluntergrenzen-Verordnung (PpUGV)

| Regel | Wert | Fundstelle |
|---|---|---|
| Pflegesensitiver Bereich | Innere Medizin und Kardiologie | § 6 i. V. m. Anlage |
| Verhältniszahl Tagschicht | 10 Patienten je Pflegekraft | § 6 / Anlage |
| Verhältniszahl Nachtschicht | 22 Patienten je Pflegekraft | § 6 / Anlage |
| Max. Pflegehilfskraftanteil | 10 % | Anlage |
| Schichtdefinition | Tag 6–22 Uhr, Nacht 22–6 Uhr | § 2 |
| „Pflegekraft" | Pflegefachkraft **oder** Pflegehilfskraft | § 2 Abs. 1–3 |

**Warum:** Die PpUGV ist der Grund, warum Dienstplanung in der Pflege überhaupt ein
wirtschaftliches Thema ist. Nach **§ 137i Abs. 5 SGB V** kann eine Unterschreitung zu
Vergütungsabschlägen oder einer Verringerung der Fallzahl führen. Untergrenzenverstöße sind
deshalb im Prototyp eine **eigene** Kennzahl und nicht mit anderen Regelverstößen vermischt.

Zwei Modellierungsentscheidungen folgen unmittelbar aus dem Verordnungstext:

1. **Keine Pflegehilfskraft im Nachtdienst.** Bei einem Zwei-Personen-Nachtdienst wäre eine
   Hilfskraft ein Anteil von 50 % — weit über der 10-%-Grenze.
2. **Auszubildende zählen nicht auf die Mindestbesetzung.** § 2 PpUGV definiert Pflegekräfte
   abschließend als Fach- und Hilfskräfte; Auszubildende sind dort nicht genannt. Sie werden
   mit `ppug_countable = 0` geführt: einzuplanen, aber ohne Entlastung der Untergrenze. Genau
   das erzeugt den in der Praxis bekannten Effekt, dass Ausbildung Planungskapazität
   **bindet**, statt sie zu schaffen.

### Tarifvertrag (TVöD-K)

| Regel | Wert | Fundstelle |
|---|---|---|
| Regelmäßige Wochenarbeitszeit | 38,5 h (Vollzeit) | § 6 Abs. 1 |
| Erholungsurlaub | 30 Arbeitstage bei 5-Tage-Woche | § 26 Abs. 1 |

**Warum:** Der TVöD-K ist der Referenztarif für kommunale Krankenhäuser und liefert die
vertragliche Obergrenze der Arbeitszeit sowie die Urlaubstage für die Bruttobedarfsrechnung.

### Was ausdrücklich **nicht** verwendet wird

Keine personenbezogenen Daten, keine Gesundheitsdaten, keine Diagnosen. Mitarbeitende sind
pseudonyme IDs (`PF-001`, `AZ-001`). Ausfälle sind reine **Verfügbarkeitsereignisse** ohne
Grund, Kategorie oder Diagnose — der Datensatz weiß, *dass* jemand nicht verfügbar ist, nie
*warum*. Das Prüfskript verifiziert, dass keine entsprechende Spalte existiert (Vorgabe aus
T7 und Projektvorgabe 2).

---

## 7. Wie die beiden Verfahren funktionieren

### Regelbasiert (Baseline)

Sequenziell, Tag für Tag, Schicht für Schicht — Nachtdienst zuerst, weil dort die wenigsten
Personen infrage kommen. Für jede Schicht:

1. **Wer darf?** Aus allen 23 Mitarbeitenden bleiben nur die übrig, die *jede* harte Regel
   erfüllen: Abwesenheit, ein Dienst pro Tag, Nachtdiensteignung, Stationsleitung nur
   Frühdienst, maximale Dienstfolge, Vertragsobergrenze, 11 h Ruhezeit.
2. **Wer ist dran?** Sortierung nach Wochenenddruck, dann bisherige Auslastung geteilt durch
   Kapazität, dann Zeitkonto — die am wenigsten ausgelastete Person gewinnt.
3. **Zuweisen**, dabei Fachkraftquote und Hilfskraftanteil absichern; Auszubildende kommen
   zusätzlich dazu, ohne auf die Untergrenze zu zählen.
4. **Findet sich niemand**, bleibt der Dienst offen und wird protokolliert.

Der entscheidende Punkt: Sie nimmt **keine Entscheidung zurück und schaut nie voraus**. Wen
sie am 3. Dezember einteilt, entscheidet sie ohne zu wissen, dass genau diese Person am 27.
gebraucht würde. Das ist die Schwäche manueller Planung — und deshalb die richtige Baseline.

### MILP-Optimierung

Der gesamte Monat wird als **ein** mathematisches Problem formuliert und in einem Zug gelöst.

**Variablen:** x[Person, Tag, Schicht] ∈ {0,1} — 23 × 28 × 3 = 1.932 Binärvariablen, dazu
Schlupfvariablen. Insgesamt **2.429 Variablen, 4.232 Nebenbedingungen**.

**Harte Nebenbedingungen:** ein Dienst je Person und Tag · verbotene Schichtfolgen
(Ruhezeit) · maximale Dienstfolge inklusive Übernahme aus der Historie · Hilfskraftanteil ·
vertragliche Höchstarbeitszeit.

**Weiche Ziele mit Strafgewichten:** Untergrenzenunterschreitung 10.000 · Unterbesetzung
1.000 · beibehaltene Zuweisung −200 · Wochenend- und Nachtdienstrichtwerte je 30 ·
Überbesetzung 20 · Ausbildungsplätze 10 · Dienstwünsche 5 · Abweichung von der
Zielarbeitszeit 0,02 je Minute.

Gelöst wird mit **HiGHS** über `scipy.optimize.milp` — ein freier Solver, kein kommerzielles
Produkt nötig. Rechenzeit: 8,7 s bei bedarfsgerechter, 15,4 s bei knapper Besetzung; die
reaktive Umplanung liegt im Median bei 0,16 s.

Der Unterschied ist nicht „schlauer", sondern **global statt lokal**: Das Modell bewertet alle
28 Tage gleichzeitig und wägt eine Zuweisung am 3. gegen ihre Folgen am 27. ab.

### Die unabhängige Bewertung

`evaluate()` prüft den fertigen Plan, **ohne zu wissen, wer ihn erzeugt hat**. Ein Verfahren
darf seine eigene Regelkonformität nicht selbst behaupten — sonst wäre der KPI-Vergleich
zirkulär. Diese Trennung hat im Projektverlauf zwei echte Fehler in der eigenen Logik
aufgedeckt.

---

## 8. Die Methodenwahl — und die KI-Frage

**Machine Learning wurde geprüft und verworfen.** Es gibt keine zu lernende Zielvariable und
keine historischen Planentscheidungen als Trainingsdaten. Das Problem ist eine Zuordnung
unter harten Nebenbedingungen mit mehreren konkurrierenden Zielen; einschlägig sind
mathematische Optimierung und Constraint Programming (Burke et al. 2004; Van den Bergh et al.
2013). Das entspricht genau der Projektvorgabe 4: objektiv prüfen, welcher Ansatz passt, und
ML nicht als Standardantwort annehmen.

**Ist das dann KI?** Drei Ebenen:

- *Umgangssprachlich* — nein. „KI" meint heute meist maschinelles Lernen; das Modell lernt
  nichts.
- *Fachlich* — ja. Suche, Constraint-Erfüllung und automatisches Planen gehören seit den
  Anfängen zum Kern der KI (Russell & Norvig 2021). Nurse Rostering wird in der KI- wie in der
  Operations-Research-Literatur behandelt.
- *Regulatorisch* — offen. Art. 3 Abs. 1 der KI-Verordnung (EU) 2024/1689 definiert
  funktional über Inferenz; Erwägungsgrund 12 nennt „logik- und wissensbasierte Ansätze, die
  aus kodiertem Wissen schlussfolgern" als Inferenztechnik, nimmt aber Systeme aus, die
  „ausschließlich auf von natürlichen Personen definierten Regeln beruhen". Ein Solver liegt
  dazwischen; eine eindeutige Zuordnung nehmen wir nicht vor.

**Wo ML anschlussfähig wäre** (Ausblick, nicht umgesetzt): ein Prognosemodell für Belegung und
Ausfallwahrscheinlichkeit, dessen Schätzungen als Parameter in die Optimierung eingehen
(„predict-then-optimize"). Mit synthetischen Daten würde ein solches Modell allerdings nur die
eigenen Generatorannahmen zurückgeben.

---

## 9. Wie die Aufgabenstellung beantwortet wird

| Vorgabe | Umsetzung |
|---|---|
| **Ruhezeiten, Pausen, Höchstarbeitszeiten** | ArbZG §§ 3–6 als `rule_*`-Spalten, harte Nebenbedingungen in beiden Verfahren |
| **Mindestbesetzungen** | PpUGV-Verhältniszahlen je Tag und Schicht, eigene KPI |
| **Qualifikationen** | Fachkraftquote, Hilfskraftanteil, Nachtdiensteignung, Praxisanleitung |
| **Wechselnde Belegung** | Belegungsmodell aus Destatis-Werten, daraus tagesgenauer Bedarf |
| **Kurzfristige Ausfälle** | Zwei Szenarien plus manuelle Krankmeldung in der App |
| **Mindestens zwei Ausfallszenarien** | S1 verteilte Einzeltage, S2 Ausfallwelle in Episoden — auf gleiches Volumen kalibriert |
| **Keine Gesundheitsdaten** | Ausfälle als reine Verfügbarkeitsereignisse, maschinell geprüft |
| **Vergleich mit Baseline** | Regelbasierte Heuristik als Excel-Äquivalent, identische Daten und Szenarien |
| **Nachvollziehbare KPIs** | Besetzungsquote, Unterbesetzung, Regelverstöße, Qualifikationskonformität, Planungszeit, Umplanungen, Planstabilität, Arbeitszeitabweichung |
| **Methodenwahl begründet** | ML geprüft und verworfen, Optimierung begründet gewählt |
| **CRISP-DM** | Business Understanding → Data Understanding → Data Preparation (Generator) → Modeling (zwei Verfahren) → Evaluation (Kampagne) → Deployment (Streamlit Cloud) |
| **Synthetische Daten, dokumentiert** | Generator, Prüfskript, Datenkonzept mit Quellen und Annahmenregister |
| **Wissenschaftliche Anforderungen** | Quellen belegt, 13 Annahmen ausgewiesen, Limitationen benannt, eigene Ergebnisse von Literatur getrennt |
| **Business Impact** | Eigener Abschnitt, getrennt nach gemessen und geschätzt |
| **Prototyp, kein Produkt** | Eine Station, ein Monat, nur Pflegedienst |

---

## 10. Das zusammenfassende Ergebnis

Die Leitfrage lautet: *Wie kann eine KI-gestützte Planungsempfehlung die Erstellung und
kurzfristige Anpassung eines Schichtplans gegenüber einer regelbasierten Excel-Planung
unterstützen?*

### Der End-to-End-Vergleich

Jedes Verfahren erstellt den Monatsplan selbst und passt ihn selbst an — so, wie es in der
jeweiligen Welt real liefe. Mittel über 45 Pläne:

| Kennzahl | Regelbasiert | MILP |
|---|---|---|
| Besetzungsquote | 98,2 % | **100,0 %** |
| offene Dienste je Plan | 2,71 | **0,00** |
| Untergrenzenverstöße | 1,84 | **0,00** |
| harte Regelverstöße | 0,67 | **0,00** |
| weiche Abweichungen | 15,8 | **2,47** |
| Spanne der Auslastung | 0,333 | **0,258** |
| Planstabilität | 93,4 % | **95,0 %** |
| geänderte Zuweisungen | 19,7 | **14,9** |

**Die Optimierung gewinnt jede einzelne Kennzahl.**

### Die vier wichtigsten Befunde

**1. Der Mehrwert entsteht unter Knappheit, nicht im Normalbetrieb.** Bei bedarfsgerechter
Personaldecke erreichen beide Verfahren nahezu dieselben Werte. Erst bei 80 % Personaldecke
trennen sie sich deutlich: **kein einziger** Plan der Heuristik ist dort vollständig
regelkonform, **alle** Pläne der Optimierung sind es. Über alle 135 MILP-Pläne gibt es keinen
harten Regelverstoß, keine Untergrenzenunterschreitung und keinen unbesetzten Dienst.

**2. Der greifbarste Unterschied sind die Wochenenden.** Über 608 Personenpläne gemessen
arbeiten in den Plänen der Heuristik **41 % der Belegschaft an allen vier Wochenenden des
Monats** und 75 % über dem Richtwert von zwei; bei der Optimierung liegen 88 % genau auf dem
Richtwert. Gleiche Daten, gleiche Regeln, gleiche Besetzungsquote, null Rechtsverstöße auf
beiden Seiten — und trotzdem ein völlig anderer Monat für die Mitarbeitenden.

**3. Die Zielfunktion entscheidet, nicht das Verfahren.** Eine vollständige Neuoptimierung
nach einem Ausfall erhält nur 51 % der Dienste — schlechter als die Heuristik. Erst als
„möglichst wenig ändern" ausdrücklich ins Modell kam, stieg die Planstabilität auf 95 %.
Umgekehrt gilt dasselbe: Das Gewicht für Lastausgleich stand faktisch bei null, weshalb die
Optimierung eine geerbte Schieflage nicht ausglich. Bei einem realistischeren Gewicht
erreicht sie eine um 29 % bessere Lastverteilung als die Heuristik **bei gleicher
Planstabilität**. Ein Optimierer tut, was in der Zielfunktion steht — nicht, was man sich
davon erhofft.

**4. Der Vorteil steckt in der Kette, nicht in einem Schritt.** Alle vier Kombinationen aus
Ausgangsplan und Reparaturverfahren, gemessen in geänderten Diensten je Monat: Excel-Plan von
Excel repariert 19,7 · Excel-Plan von MILP 25,8 · MILP-Plan von Excel 24,8 · **MILP-Plan von
MILP 14,9**. Auf jedem geerbten Plan ändert die Optimierung mehr — weil sie dessen Mängel
mitbehebt. Nur wenn Planung **und** Anpassung aus demselben System kommen, sinkt der Wert.
Für die Praxis: Ein Optimierer als reine Feuerwehr auf bestehenden Excel-Plänen hebt die
Rechtssicherheit, aber nicht die Entlastung.

### Die Antwort auf die Leitfrage

1. **Bei der Erstellung** liegt der Mehrwert nicht in der Machbarkeit, sondern in
   Regelkonformität unter Knappheit und in Verteilungsgerechtigkeit. Ist genug Personal da,
   tut es auch eine Regelheuristik.
2. **Bei der kurzfristigen Anpassung** liegt der Mehrwert in der Planstabilität — und zwar
   nur, wenn Stabilität ausdrücklich als Ziel modelliert wird.
3. **Beides zusammen** ergibt mehr als die Summe: Nur die durchgängige Nutzung erreicht die
   niedrige Änderungszahl.
4. **Der Prototyp macht einen Zielkonflikt entscheidbar**, den die Excel-Planung unsichtbar
   lässt: Planungsruhe gegen Verteilungsgerechtigkeit. Welches Ziel schwerer wiegt, ist eine
   Führungsentscheidung — keine technische.

### Business Impact

**Gemessen** (gilt für diese 15 Instanzen): Rechtssicherheit unter Knappheit (0 gegen 4,7
Untergrenzenverstöße je Plan bei 80 % Decke), gleichmäßigere Belastung (Spanne von 33 auf
7 Prozentpunkte), ein Viertel weniger Planänderungen je Monat, Umplanung im Median unter einer
Viertelsekunde.

**Nicht gemessen, nur plausibel:** Reduktion des manuellen Planungsaufwands, Wirkung auf
Zufriedenheit und Fluktuation, vermiedene Bettensperrungen. Diese Aussagen bräuchten eine
Erhebung im Betrieb und sind als Schätzung gekennzeichnet.

---

## 11. Grenzen der Aussage

- **Alle Daten sind synthetisch.** Die absolute Höhe der Kennzahlen ist nicht auf eine
  konkrete Station übertragbar; der Vergleich zweier Verfahren auf identischer Datenbasis
  bleibt gültig.
- **Die Heuristik ist keine echte Excel-Planung.** Sie ist konsistenter, schneller und
  ermüdungsfrei. Der Unterschied zu manueller Planung dürfte größer sein als hier gemessen.
- **Fünf Seeds sind wenig.** Für die Kernaussagen zur Regelkonformität reicht die Streuung;
  inferenzstatistische Aussagen wären damit nicht belastbar, ein Signifikanztest wird bewusst
  nicht gerechnet.
- **Die Gewichte sind gesetzt, nicht hergeleitet.** Für das wichtigste Gewicht ist die Wirkung
  quantifiziert; die übrigen bleiben ungeprüft.
- **Planstabilität misst Zurückhaltung, nicht Qualität.** Jede Angabe nennt deshalb ihren
  Ausgangsplan mit.
- **13 Annahmen** sind im Datenkonzept als solche ausgewiesen, drei davon mit hoher
  Ergebnissensitivität.

---

## 12. Quellen

**Rechtsnormen**

- Arbeitszeitgesetz (ArbZG), §§ 3, 4, 5, 6
- Pflegepersonaluntergrenzen-Verordnung (PpUGV), § 2 und § 6 mit Anlage
- Vereinbarung nach § 137i Abs. 4 SGB V über den Nachweis zur Einhaltung der
  Pflegepersonaluntergrenzen 2026 (GKV-Spitzenverband / DKG / PKV)
- Pflegepersonalbemessungsverordnung (PPBV) / PPR 2.0 — Grundwert und Fallwert
- TVöD-K § 6 (Regelmäßige Arbeitszeit), § 26 (Erholungsurlaub)
- Verordnung (EU) 2024/1689 (KI-Verordnung), Art. 3 Abs. 1 und Erwägungsgrund 12

**Amtliche Statistik und Gutachten**

- Statistisches Bundesamt, Krankenhausstatistik 2024 (Auslastung 72,0 %, Verweildauer 7,1 Tage)
- Statistisches Landesamt Sachsen, Beschäftigte im Pflegedienst der Krankenhäuser 2024
- Wissenschaftliche Dienste des Deutschen Bundestages, WD 8-3000-008/26, Pflegepersonalbemessung
- Techniker Krankenkasse, Krankenstand bei Pflegekräften

**Wissenschaftliche Literatur**

- Burke, E. K., De Causmaecker, P., Vanden Berghe, G., & Van Landeghem, H. (2004). The State of the Art of Nurse Rostering. *Journal of Scheduling*, 7(6), 441–499.
- Ernst, A. T., Jiang, H., Krishnamoorthy, M., & Sier, D. (2004). Staff scheduling and rostering: A review of applications, methods and models. *EJOR*, 153(1), 3–27.
- Van den Bergh, J., Beliën, J., De Bruecker, P., Demeulemeester, E., & De Boeck, L. (2013). Personnel scheduling: A literature review. *EJOR*, 226(3), 367–385.
- Ceschia, S., Dang, N., De Causmaecker, P., Haspeslagh, S., & Schaerf, A. Second International Nurse Rostering Competition (INRC-II). arXiv:1501.04177.
- Curtois, T., & Qu, R. Computational results on new staff scheduling benchmark instances. University of Nottingham.
- Wickert, T. I., Smet, P., & Vanden Berghe, G. The nurse rerostering problem. *Computers & Operations Research*.
- Russell, S. J., & Norvig, P. (2021). *Artificial Intelligence: A Modern Approach* (4th ed.). Pearson.

**Kursunterlagen**

- T2 Projektmanagement/Business: Reproduzierbarkeit, Data Lineage, Data Contract
- T3 Datenmanagement und Grundlagen AI Use Cases
- T7 Ethik und Datenschutz

Vollständige Fundstellen mit URLs in `DATENKONZEPT.md`, Abschnitt 11.
