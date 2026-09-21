# Projektübersicht: KI-gestützte Schichtplanung in der Pflege

**Stand:** 21.09.2026 · Datensatz 2.1.0, Seed 20261133 · Evaluation über 270 Pläne, mit Krankheitsgutschrift · Replikation auf vier Stationstypen (1.080 Pläne)

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
| `auswertung.py` | Berechnet jede Kennzahl aus `ERGEBNISSE.md` aus den Rohergebnissen |
| `instanzen/` | Drei Replikationsdatensätze anderer Stationstypen mit ihren Kampagnenergebnissen |
| `replikation.py` | Prüft die sieben tragenden Befunde auf allen vier Stationstypen nach |
| `sensitivitaet.py` / `.csv` | Sensitivitätsanalyse der Zielgewichte |
| `wochenend_analyse.py` / `wochenend_verteilung.csv` | Verteilung der Wochenenddienste über 608 Personenpläne |
| `make_charts.py` → `abbildungen/` | Fünf Abbildungen, ausschließlich aus den Rohdaten erzeugt |
| `make_deck.js` → `.pptx` | Ausführliche Präsentation (16 Folien) |
| `make_kurzdeck.js` → `.pptx` | Kurzpräsentation (8 Folien) |
| `make_gantt.py` | Gantt-Diagramm des Projektverlaufs |
| `DATENKONZEPT.md`, `ERGEBNISSE.md`, `HANDOUT.md`, `README.md` | Dokumentation |

**Das Konstruktionsprinzip:** Jede Zahl in Bericht und Präsentation stammt aus
`evaluation_results.csv` und wird von einem Skript dort herausgelesen (`auswertung.py`,
`make_charts.py`) — nichts ist von Hand eingetragen. Wer die Kampagne neu rechnet, bekommt
dieselben Zahlen; einzige Ausnahme sind die wenigen MILP-Läufe, die das Zeitlimit von 30 s
erreichen und deren Ergebnis dann von der Rechengeschwindigkeit abhängt
(`ERGEBNISSE.md`, Abschnitt 3.1).

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
  Stellt das Gewicht für Lastausgleich in der Zielfunktion (Abschnitt 8). Sie wirkt auf die
  Anpassung bei Ausfällen; der Ausgangsplan ist für alle drei Stufen derselbe, damit die
  Stufen vergleichbar bleiben
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
5. **Arbeitszeit** — Ist gegen Soll je Person, Krankheitsgutschrift, Abweichungen
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
| **Ausfallszenarien** | `absence_s1`, `absence_s2` + Vorlaufzeiten | Die simulierten kurzfristigen Ausfälle, je Szenario ein Spaltenpaar — ausführlich in Abschnitt 6 |
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

## 6. Die Ausfallszenarien

Die Projektvorgabe verlangt **mindestens zwei** Ausfallszenarien, weil Krankheitsausfälle
unsicher sind. Der Prototyp hat drei.

### 6.1 Warum überhaupt Szenarien — reicht nicht die manuelle Krankmeldung?

Die App kann jederzeit eine einzelne Person krankmelden, und der Plan rechnet sich neu. Das
ist gut für die Live-Demonstration, taugt aber nicht als Evaluationsgrundlage: Von Hand
gesetzte Ausfälle sind nicht reproduzierbar, nicht systematisch und nicht vergleichbar.
Beide Verfahren müssen **exakt denselben Störungen** ausgesetzt werden, sonst misst man den
Zufall statt das Verfahren.

Die Szenarien sind deshalb **fest im Datensatz hinterlegt** — als Spalten, nicht als
Zufallsziehung zur Laufzeit. Wer die Kampagne ein Jahr später wiederholt, bekommt dieselben
Ausfälle an denselben Tagen bei denselben Personen.

### 6.2 Die drei Szenarien im Überblick

| | Was es abbildet | Struktur | Realisiert im ausgelieferten Datensatz |
|---|---|---|---|
| **S0** | ungestörter Betrieb | keine kurzfristigen Ausfälle, nur geplante Abwesenheiten (Urlaub, Fortbildung) | 0 Ausfalltage |
| **S1** | normaler Krankenstand | unabhängige **Einzeltage**, Rate 4 % je Person und Tag über den gesamten Monat | 19 Ausfalltage bei 10 Personen, längste zusammenhängende Abwesenheit 1 Tag |
| **S2** | Infektwelle auf Station | 7 mehrtägige **Krankheitsepisoden** von 2–4 Tagen, Beginn zu 80 % im Fenster 14.–19.12. | 19 Ausfalltage bei 6 Personen, längste Episode 4 Tage |

**S0 ist kein Leerlauf**, sondern der Referenzplan. Beide Verfahren erstellen daraus ihren
Monatsplan; S1 und S2 werden dann gegen diesen Ausgangsplan gemessen. Ohne S0 gäbe es keinen
Bezugspunkt für die Planstabilität.

### 6.3 Der entscheidende Konstruktionsgrundsatz: gleicher Umfang, andere Struktur

S1 und S2 tragen im ausgelieferten Datensatz **exakt gleich viele Ausfalltage — 19 gegen 19**.
Das ist kein Zufall, sondern Absicht.

Unterschieden sich die beiden Szenarien zugleich in der *Menge* und in der *Verteilung* der
Ausfälle, wäre jeder gemessene Unterschied doppeldeutig: Man könnte ihn ebenso gut mit „S2 hat
eben mehr Ausfälle" erklären wie mit „gebündelte Ausfälle sind schwerer aufzufangen". Die
Aussage über korrelierte Ausfälle wäre dann nicht belegbar.

Die Episodenzahl in S2 ist deshalb **empirisch auf das Volumen von S1 kalibriert**: 7 Episoden
von im Mittel 3 Tagen ergeben über die 15 Kampagneninstanzen 17,8 Ausfalltage gegenüber 15,7
bei S1. Bei 8 Episoden wären es 22 % mehr gewesen, bei 6 Episoden 9 % weniger.

So wirkt sich die gleiche Menge in den beiden Szenarien aus:

| | S1 | S2 |
|---|---|---|
| Ausfalltage gesamt | 19 | 19 |
| betroffene Personen | 10 | **6** |
| längste zusammenhängende Abwesenheit | 1 Tag | **4 Tage** |
| Anteil im Wellenfenster (6 von 28 Tagen) | 5 % | **79 %** |
| Ausfälle je Tag **im** Fenster | 0,17 | **2,50** |
| Ausfälle je Tag **außerhalb** | 0,82 | 0,18 |

In S2 fallen also weniger Personen aus, diese dafür mehrtägig und weitgehend gleichzeitig.
Innerhalb des Sechstagefensters ist die Tageslast rund vierzehnmal so hoch wie außerhalb.
Das ist das Bild einer Infektwelle: Vier von fünf Ausfalltagen liegen in einer einzigen Woche.

### 6.4 Warum Episoden und nicht einfach eine erhöhte Tagesrate

Ein früheres Modell erhöhte im Wellenfenster nur die Tagesrate von 4 % auf 12 %. Das hatte
zwei Mängel, die erst in der Auswertung auffielen:

**Es erzeugte gar keine Episoden.** Jeder Tag wurde unabhängig gezogen, die längste
zusammenhängende Abwesenheit einer Person betrug einen Tag. Real fehlt jemand, der heute
krank ist, in aller Regel auch morgen — und genau diese Mehrtägigkeit bringt eine Station in
Bedrängnis, nicht der verstreute Einzeltag.

**Es veränderte den Umfang mit.** Über fünf Seeds erzeugte das alte S2 im Mittel 31,2
Ausfalltage gegenüber 18,8 bei S1 — zwei Drittel mehr. Die beiden Szenarien unterschieden
sich damit in zwei Dimensionen gleichzeitig, und der Vergleich war wertlos.

Das Episodenmodell behebt beides: Die Mehrtägigkeit ist explizit modelliert statt als
Nebeneffekt erhofft, und die Episodenzahl ist auf das Volumen von S1 kalibriert.

### 6.5 Wie es technisch funktioniert

Jedes Szenario belegt **zwei Spalten** im Datensatz:

| Spalte | Inhalt |
|---|---|
| `absence_s1` / `absence_s2` | 0 oder 1 — fällt diese Person an diesem Tag kurzfristig aus? |
| `absence_s1_notice_h` / `absence_s2_notice_h` | Vorlaufzeit in Stunden: wie lange vor Dienstbeginn die Meldung eingeht (2, 4, 8, 12 oder 24) |

Szenario S0 heißt schlicht: beide Ausfallspalten sind 0.

**Beim Planen** liest der Planer die Spalte des gewählten Szenarios und behandelt jedes Paar
(Person, Tag) mit einer 1 als **nicht verfügbar** — genau wie Urlaub, nur eben kurzfristig.
Für die regelbasierte Heuristik heißt das: Diese Person fällt aus dem Kandidatenpool. Für das
MILP: Die entsprechende Variable wird auf 0 fixiert.

Weil beide Szenarien als **eigene Spaltenpaare nebeneinander** liegen, kann man in der App
zwischen ihnen umschalten, ohne eine andere Datei zu laden. Dieselbe CSV trägt alle drei
Situationen.

**Die Vorlaufzeit** ist eine Besonderheit von S2: Dort trägt nur der **erste Tag einer
Episode** eine kurzfristige Meldung (2–12 Stunden); die Folgetage stehen mit 24 Stunden
Vorlauf, weil eine laufende Krankmeldung dem Plan bereits bekannt ist. Die Spalte ist im
Datensatz vorhanden, wird von den Planungsverfahren aber **derzeit nicht ausgewertet** — beide
behandeln alle Ausfälle gleich. Das ist eine bewusste Beschränkung des Prototyps und im
Datenkonzept als solche vermerkt.

### 6.6 Was beim Umschalten in der App passiert

1. Der Planer liest die Ausfallspalte des gewählten Szenarios.
2. Bei eingeschaltetem **„Reaktiv umplanen"** wird der S0-Plan als Ausgangspunkt genommen und
   nur dort aufgebrochen, wo ein Ausfall eine Lücke reißt. Ausgeschaltet wird der ganze Monat
   neu gerechnet.
3. Der neue Plan wird gegen den S0-Plan verglichen: Wie viele Zuweisungen haben sich geändert?
   Das ist die **Planstabilität**.
4. Alle übrigen KPIs — Besetzungsquote, Untergrenzenverstöße, Regelverstöße, Lastverteilung —
   werden für den neuen Plan neu berechnet.

Zusätzlich lässt sich über „Zusätzlicher Ausfall" eine Person **oben drauf** krankmelden. Das
ist die Live-Demonstration; für die Evaluation zählen nur die hinterlegten Szenarien.

### 6.7 Datenschutz

Ausfälle sind im Datensatz **reine Verfügbarkeitsereignisse**: eine 0/1-Spalte plus
Vorlaufzeit. Es gibt keine Spalte für Grund, Kategorie oder Diagnose — der Datensatz weiß,
*dass* jemand nicht verfügbar ist, nie *warum*. Das Prüfskript verifiziert, dass keine solche
Spalte existiert. Damit ist die Vorgabe „keine individuellen Gesundheitsdaten" nicht nur
eingehalten, sondern strukturell ausgeschlossen.

### 6.8 Was die Szenarien in der Auswertung gezeigt haben

Die Szenarien erfüllen ihren Zweck: Sie belasten beide Verfahren mit zwei strukturell
verschiedenen Störungsmustern, und unter beiden ist die Rangfolge der Verfahren dieselbe.
Einen eigenständigen Effekt der **Struktur** — Welle gegen verteilte Einzelausfälle — weist
die Kampagne dagegen nicht nach:

- **Lastverteilung:** Nach Kontrolle für das Restvolumen bleibt ein Unterschied von +0,008
  in der Spanne — praktisch null.
- **Planstabilität:** Der Unterschied folgt der Menge der Ausfälle, nicht ihrer
  Konzentration; unter Volumenkontrolle schrumpft er auf 0,1 Prozentpunkte.

Eine frühere Fassung hatte für die Lastverteilung einen strukturellen Effekt berichtet. Er
war ein Artefakt: Ohne Gutschrift für Krankheitstage erschienen gerade die mehrtägig
Erkrankten der Welle als stark unterausgelastet (Abschnitt 6.9). Details in
`ERGEBNISSE.md`, Abschnitte 3.2 und 3.3.

### 6.9 Krankheit ist keine Unterauslastung: die Krankheitsgutschrift

Fällt jemand krank aus, fehlt ein Dienst im Plan — aber nicht auf dem Arbeitszeitkonto. Nach
dem **Entgeltausfallprinzip** (§ 4 Abs. 1 EFZG) wird die Person so gestellt, als hätte sie
gearbeitet; das BAG hat bestätigt, dass dafür eine Zeitgutschrift verlangt werden kann
(BAG, 05.10.2023 – 6 AZR 210/22). Nacharbeiten muss niemand.

Der Prototyp bildet das so ab: Gutgeschrieben wird die Nettodauer des Dienstes, den die
Person laut **Ausgangsplan** an dem Ausfalltag gehabt hätte. Ein Ausfall an einem
dienstfreien Tag ergibt keine Gutschrift. Die Gutschrift zählt wie gearbeitete Zeit — für
die Auslastung, für die Zielarbeitszeit der Optimierung und für die vertragliche
Obergrenze —, nicht aber für die Grenzen des Arbeitszeitgesetzes, die tatsächliche Arbeit
begrenzen. Gesundheitsdaten braucht sie nicht: Sie knüpft allein an die Tatsache des
Ausfalls. In der Anwendung steht sie im Reiter „Arbeitszeit" als eigene Spalte.

**Warum das eingebaut wurde.** Ohne Gutschrift hielt das Modell Kranke für
unterausgelastet. Mit der Priorität „Verteilungsgerechtigkeit" ließ die Optimierung jede
erkrankte Person ihre ausgefallenen Dienste an anderen Tagen vollständig nacharbeiten, und
die Kennzahl „Spanne der Auslastung" maß unter S1/S2 zum Teil Krankheit statt
Planungsqualität. Ein automatisierter Test prüft seitdem, dass niemand Krankheit nacharbeitet.

---

## 7. Welche Rechtsgrundlagen verwendet werden — und warum

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

### Entgeltfortzahlungsgesetz (EFZG)

| Regel | Wert | Fundstelle |
|---|---|---|
| Entgeltausfallprinzip | Arbeitsunfähige werden gestellt, als hätten sie gearbeitet | § 4 Abs. 1 |
| Zeitgutschrift für ausgefallene Dienste | kann auf dem Arbeitszeitkonto verlangt werden | BAG, 05.10.2023 – 6 AZR 210/22 |
| Tarifliche Abweichung | in Grenzen zulässig | § 4 Abs. 4; BAG, 16.07.2014 – 10 AZR 242/13 |

**Warum:** Ohne diese Regel hielte das Modell Kranke für unterausgelastet und ließe sie
ausgefallene Dienste nacharbeiten. Umsetzung und Wirkung in Abschnitt 6.9.

### Was ausdrücklich **nicht** verwendet wird

Keine personenbezogenen Daten, keine Gesundheitsdaten, keine Diagnosen. Mitarbeitende sind
pseudonyme IDs (`PF-001`, `AZ-001`). Ausfälle sind reine **Verfügbarkeitsereignisse** ohne
Grund, Kategorie oder Diagnose — der Datensatz weiß, *dass* jemand nicht verfügbar ist, nie
*warum*. Das Prüfskript verifiziert, dass keine entsprechende Spalte existiert (Vorgabe aus
T7 und Projektvorgabe 2).

---

## 8. Wie die beiden Verfahren funktionieren

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
Produkt nötig. Rechenzeit: 7,7 s bei bedarfsgerechter, 14,7 s bei unterbesetzter Decke; die
reaktive Umplanung liegt im Median bei 0,55 s.

Beide Verfahren schreiben krankheitsbedingt ausgefallene Dienste gut (Abschnitt 6.9): Die
Heuristik verbucht die Gutschrift an dem Tag, an dem der Ausfall liegt, die Optimierung
rechnet sie in Zielarbeitszeit und Obergrenze über den ganzen Monat ein.

Der Unterschied ist nicht „schlauer", sondern **global statt lokal**: Das Modell bewertet alle
28 Tage gleichzeitig und wägt eine Zuweisung am 3. gegen ihre Folgen am 27. ab.

### Die unabhängige Bewertung

`evaluate()` prüft den fertigen Plan, **ohne zu wissen, wer ihn erzeugt hat**. Ein Verfahren
darf seine eigene Regelkonformität nicht selbst behaupten — sonst wäre der KPI-Vergleich
zirkulär. Diese Trennung hat im Projektverlauf zwei echte Fehler in der eigenen Logik
aufgedeckt.

---

## 9. Die Methodenwahl — und die KI-Frage

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

## 10. Wie die Aufgabenstellung beantwortet wird

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
| **Wissenschaftliche Anforderungen** | Quellen belegt, 14 Annahmen ausgewiesen, Limitationen benannt, eigene Ergebnisse von Literatur getrennt |
| **Business Impact** | Eigener Abschnitt, getrennt nach gemessen und geschätzt |
| **Prototyp, kein Produkt** | Eine Station, ein Monat, nur Pflegedienst |

---

## 11. Das zusammenfassende Ergebnis

Die Leitfrage lautet: *Wie kann eine KI-gestützte Planungsempfehlung die Erstellung und
kurzfristige Anpassung eines Schichtplans gegenüber einer regelbasierten Excel-Planung
unterstützen?*

### Der End-to-End-Vergleich

Jedes Verfahren erstellt den Monatsplan selbst und passt ihn selbst an — so, wie es in der
jeweiligen Welt real liefe. Mittel über die 30 gestörten Pläne je Verfahren (S1, S2):

| Kennzahl | Regelbasiert | MILP |
|---|---|---|
| Besetzungsquote | 97,3 % | **99,7 %** |
| offene Dienste je Plan | 3,93 | **0,77** |
| Untergrenzenverstöße | 2,60 | **0,00** |
| harte Regelverstöße | 0,57 | **0,00** |
| weiche Abweichungen | 15,5 | **3,17** |
| Spanne der Auslastung | 0,325 | **0,247** |
| Planstabilität | 89,9 % | **92,4 %** |
| geänderte Zuweisungen | 30,3 | **22,8** |

**Die Optimierung gewinnt jede einzelne Kennzahl.**

### Die fünf wichtigsten Befunde

**1. Der Mehrwert entsteht unter Knappheit, nicht im Normalbetrieb.** Bei bedarfsgerechter
Personaldecke erreichen beide Verfahren nahezu dieselbe Besetzung und Regelkonformität; sie
unterscheiden sich dort in der Verteilung der Last (Befund 2). Erst bei 80 % Personaldecke
trennen sie sich deutlich: **kein einziger** Plan der Heuristik ist dort vollständig
regelkonform, **alle** Pläne der Optimierung sind es. Über alle 135 MILP-Pläne gibt es keinen
harten Regelverstoß und keine Untergrenzenunterschreitung. Bei 80 % Decke bleiben unter
Ausfällen einzelne Dienste unter der fachlichen Sollbesetzung (56 Dienste in 18 von 135
Plänen) — jeder davon oberhalb der gesetzlichen Untergrenze. Die Heuristik unterschreitet dort
die Untergrenze 6,5-mal je Plan.

**2. Der greifbarste Unterschied sind die Wochenenden.** Über 608 Personenpläne gemessen
arbeiten in den Plänen der Heuristik **41 % der Belegschaft an allen vier Wochenenden des
Monats** und 75 % über dem Richtwert von zwei; bei der Optimierung liegen 88 % genau auf dem
Richtwert. Das hängt nicht an der Knappheit: Schon bei bedarfsgerechter Decke, wo beide
Verfahren nahezu gleich besetzen und regelkonform planen, sind es 43 % gegen niemanden.
Gleiche Daten, gleiche Regeln — und trotzdem ein völlig anderer Monat für die Mitarbeitenden.

**3. Die Zielfunktion entscheidet, nicht das Verfahren.** Eine vollständige Neuoptimierung
nach einem Ausfall erhält nur rund ein Viertel der Dienste — schlechter als die Heuristik.
Erst als „möglichst wenig ändern" ausdrücklich ins Modell kam, stieg die Planstabilität auf
92 %. Umgekehrt gilt dasselbe: Das Gewicht für Lastausgleich stand faktisch bei null,
weshalb die Optimierung eine geerbte Schieflage nicht ausglich. Bei einem realistischeren
Gewicht (0,1 statt 0,02) erreicht sie auf dem Plan der Heuristik **weniger als die halbe
Spanne** (0,170 gegen 0,379) **bei höherer Planstabilität** (92,7 % gegen 91,8 %). Ein Optimierer tut, was in der Zielfunktion steht — nicht, was man sich
davon erhofft.

**4. Der Vorteil steckt in der Kette, nicht in einem Schritt.** Alle vier Kombinationen aus
Ausgangsplan und Reparaturverfahren, gemessen in geänderten Diensten je gestörtem Plan:
Excel-Plan von Excel repariert 30,3 · Excel-Plan von MILP 34,8 · MILP-Plan von Excel 36,0 ·
**MILP-Plan von MILP 22,8**. Auf jedem geerbten Plan ändert die Optimierung mehr — weil sie dessen Mängel
mitbehebt. Nur wenn Planung **und** Anpassung aus demselben System kommen, sinkt der Wert.
Für die Praxis: Ein Optimierer als reine Feuerwehr auf bestehenden Excel-Plänen hebt die
Rechtssicherheit, aber nicht die Entlastung.

**5. Die Befunde hängen nicht an dieser einen Station.** Die Kampagne wurde auf drei
weiteren Stationstypen wiederholt — Geriatrie (40 Betten, 10:1), Herzchirurgie (24 Betten,
7:1) und Intensivmedizin (12 Betten, 2:1). Geändert wurden ausschließlich Werte im
Datensatz; das Schema und `planner.py` blieben unangetastet. **Alle sieben geprüften
Befunde replizieren auf allen vier Stationen — 28 von 28.** Dass ein anderer Stationstyp
ohne eine Zeile Codeänderung planbar ist, ist zugleich der Beleg für das
Konstruktionsprinzip: Grenzwerte stehen in den Daten, nicht im Code. Wäre irgendwo eine
Verhältniszahl fest verdrahtet, würde die Intensivstation mit 2:1 sofort falsche
Untergrenzen erzeugen.

Die Intensivstation zeigt dabei die ehrliche Grenze: Sie ist die einzige, auf der die
Optimierung bei 80 % Personaldecke nicht durchgängig null Untergrenzenverstöße erreicht
(0,87 im Mittel gegen 8,13 bei der Heuristik). Die verbleibenden Verstöße treten nur in den
Ausfallszenarien auf. In 11 von 15 Fällen entspricht ihre Zahl genau der Zahl der Tage, an
denen die Untergrenze **rechnerisch nicht erreichbar** ist — auch dann nicht, wenn jede verfügbare
Person einen Dienst übernähme; in den übrigen binden zusätzlich Monatsarbeitszeit,
Ruhezeiten und Dienstfolgen. Die korrekte Aussage lautet deshalb nicht „die Optimierung hält
die Untergrenze immer ein", sondern: **Sie hält sie ein, solange das mit Arbeitszeitrecht
und Arbeitsvertrag vereinbar ist.** Wo Personal fehlt, kann kein Verfahren es erzeugen.

### Die Antwort auf die Leitfrage

1. **Bei der Erstellung** liegt der Mehrwert nicht in der Machbarkeit, sondern in
   Regelkonformität unter Knappheit und in Verteilungsgerechtigkeit. Ist genug Personal da,
   sichert auch eine Regelheuristik Besetzung und Rechtskonformität — den Unterschied macht
   dann allein die Verteilung der Last.
2. **Bei der kurzfristigen Anpassung** liegt der Mehrwert in der Planstabilität — und zwar
   nur, wenn Stabilität ausdrücklich als Ziel modelliert wird.
3. **Beides zusammen** ergibt mehr als die Summe: Nur die durchgängige Nutzung erreicht die
   niedrige Änderungszahl.
4. **Der Prototyp macht einen Zielkonflikt entscheidbar**, den die Excel-Planung unsichtbar
   lässt: Planungsruhe gegen Verteilungsgerechtigkeit. Welches Ziel schwerer wiegt, ist eine
   Führungsentscheidung — keine technische.

### Business Impact

**Gemessen** (gilt für diese 15 Instanzen): Rechtssicherheit unter Knappheit (0 gegen 6,5
Untergrenzenverstöße je Plan bei 80 % Decke), gleichmäßigere Belastung (Spanne von 33 auf
5 Prozentpunkte im Normalbetrieb, 25 statt 32 nach Ausfällen), ein Viertel weniger
Planänderungen je Monat mit Ausfällen, Umplanung im Median in rund einer halben Sekunde.

**Nicht gemessen, nur plausibel:** Reduktion des manuellen Planungsaufwands, Wirkung auf
Zufriedenheit und Fluktuation, vermiedene Bettensperrungen. Diese Aussagen bräuchten eine
Erhebung im Betrieb und sind als Schätzung gekennzeichnet.

---

## 12. Grenzen der Aussage

- **Alle Daten sind synthetisch.** Die absolute Höhe der Kennzahlen ist nicht auf eine
  konkrete Station übertragbar; der Vergleich zweier Verfahren auf identischer Datenbasis
  bleibt gültig.
- **Die Replikation ersetzt keine Erhebung.** Vier Stationstypen zeigen, dass die Richtung
  der Befunde nicht an einer Parametrierung hängt. Alle vier stammen jedoch aus demselben
  Generator und denselben Annahmen — ein systematischer Modellfehler träte in allen vier
  gleichermaßen auf und fiele durch die Replikation gerade nicht auf.
- **Die Heuristik ist keine echte Excel-Planung.** Sie ist konsistenter, schneller und
  ermüdungsfrei. Der Unterschied zu manueller Planung dürfte größer sein als hier gemessen.
- **Fünf Seeds sind wenig.** Für die Kernaussagen zur Regelkonformität reicht die Streuung;
  inferenzstatistische Aussagen wären damit nicht belastbar, ein Signifikanztest wird bewusst
  nicht gerechnet.
- **Die Gewichte sind gesetzt, nicht hergeleitet.** Für das wichtigste Gewicht ist die Wirkung
  quantifiziert; die übrigen bleiben ungeprüft.
- **Planstabilität misst Zurückhaltung, nicht Qualität.** Jede Angabe nennt deshalb ihren
  Ausgangsplan mit.
- **Alle Ausfälle eines Szenarios sind beim Umplanen gleichzeitig bekannt.** In der
  Wirklichkeit kommen sie einzeln. Das Vorwissen kann nur die Optimierung nutzen; eine
  rollierende Umplanung wäre der realistischere Test und ist nicht umgesetzt.
- **Ein Mangel ist erst spät aufgefallen.** Die erste Fassung schrieb Krankheitstage nicht
  gut; mehrere Aussagen zu den Ausfallszenarien waren dadurch Artefakte und sind
  zurückgenommen (`ERGEBNISSE.md`, Abschnitt 3.2). Dass der Fehler über eine Prüfung der
  Anwendung gefunden wurde und nicht über die Kennzahlen, zeigt, wie leicht eine plausible
  Zahl einen Modellfehler verdeckt.
- **14 Annahmen** sind im Datenkonzept als solche ausgewiesen, drei davon mit hoher
  Ergebnissensitivität.

---

## 13. Quellen

**Rechtsnormen**

- Entgeltfortzahlungsgesetz (EFZG), § 4 Abs. 1 und 4 — Entgeltausfallprinzip
- BAG, Urteil vom 05.10.2023 – 6 AZR 210/22 (Zeitgutschrift für krankheitsbedingt ausgefallene Dienste) — <https://www.stollfuss.de/blog/BAG-Stundengutschriften-auf-einem-Arbeitszeitkonto-fuer-krankheitsbedingt-nicht-geleistete-Bereitschaftsdienste-2024-01-29>
- BAG, Urteil vom 16.07.2014 – 10 AZR 242/13 (tarifliche Abweichung) — <https://www.bundesarbeitsgericht.de/entscheidung/10-azr-242-13/>
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
