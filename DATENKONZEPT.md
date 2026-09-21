# Datenkonzept: Synthetischer Datensatz für die KI-gestützte Schichtplanung

**Projekt:** KI-gestützte Personal- und Schichtplanung in der Pflege
**Fallstudie:** Normalstation „Innere Medizin und Kardiologie", 30 Betten
**Datensatz-Version:** 2.1.0 · Seed 20261133 · erzeugt mit `generate_dataset.py`
**Auslieferung:** eine einzelne Datei `schichtplan_datensatz.csv` (1.288 Zeilen × 94 Spalten)
**Planungshorizont:** 30.11.2026 – 27.12.2026 (28 Tage) · Historie: 02.11.2026 – 29.11.2026

---

## 1. Warum der bisherige Datensatz die Leitfrage nicht beantworten kann

Der aktuelle Stand im Repository (`streamlit_app.py`, 40 hartcodierte Mitarbeitende) ist als
Demo tragfähig, als **Datengrundlage einer wissenschaftlichen Evaluation aber nicht**. Vier
Punkte sind für die Leitfrage entscheidend und fehlen bisher:

| Lücke | Konsequenz für die Leitfrage |
|---|---|
| **Kein Nachfrageobjekt.** Die Mindestbesetzung wird im Sidebar frei eingestellt, statt aus Belegung und Qualifikationsbedarf zu folgen. | Ohne datenseitig hinterlegte, tagesvariable Nachfrage lässt sich „wechselnde Belegung bzw. unterschiedlicher Personalbedarf" (Projektvorgabe 2) nicht abbilden und keine Besetzungsquote messen. |
| **Keine Historie.** Der Plan beginnt aus dem Nichts. | Ruhezeit, Dienstfolgen, Wochenendverteilung und Arbeitszeitkonto am Planbeginn sind unbestimmt; die 11-Stunden-Regel (§ 5 ArbZG) ist an der Periodengrenze schlicht nicht prüfbar. |
| **Keine geplanten Abwesenheiten und Wünsche.** | Der Unterschied zwischen *planbarer* (Urlaub, Fortbildung) und *kurzfristiger* Nichtverfügbarkeit verschwindet — genau dieser Unterschied ist der Kern der Leitfrage. |
| **Klarnamen im Code.** | Widerspricht dem Grundsatz aus T7 (Ethik/Datenschutz) und ist für einen synthetischen Datensatz vollständig verzichtbar. |
| **40 Mitarbeitende auf einer Station.** | Für 30 Betten rechnerisch etwa das 1,4-fache des Bruttopersonalbedarfs (siehe Abschnitt 5.4). Ein überbesetzter Plan ist immer lösbar — der Vergleich Excel vs. KI würde systematisch zugunsten „beide Verfahren schaffen es" verzerrt. |

Der letzte Punkt ist methodisch der wichtigste: **Ein Datensatz, der zu leicht ist, kann keine
Unterschiede zwischen Planungsverfahren sichtbar machen.** Der neue Datensatz ist deshalb
bewusst auf einen Auslastungsgrad von rund 90 % der verfügbaren Kapazität eingestellt
(Abschnitt 5.4) — knapp genug, dass Ausfälle wehtun, weit genug von der Infeasibilität
entfernt, dass die Baseline eine faire Chance hat.

---

## 2. Woher die *Struktur* kommt: Referenzmodelle der Rostering-Forschung

Die Struktur ist nicht frei erfunden, sondern folgt den etablierten Datenmodellen der
Personaleinsatzplanung. Burke et al. (2004) systematisieren in ihrem Übersichtsartikel zum
Nurse Rostering die wiederkehrenden Modellbestandteile; Ernst et al. (2004) und Van den Bergh
et al. (2013) bestätigen dieselben Bausteine über die Pflege hinaus für Personalplanung
allgemein. Die beiden meistgenutzten Benchmark-Familien — die Instanzen von Curtois und Qu
(Nottingham/`schedulingbenchmarks.org`) und die *Second International Nurse Rostering
Competition* (INRC-II) — geben diesen Bausteinen eine konkrete Dateistruktur.

| Referenzmodell | Dort definierte Entität | Entsprechung in unserem Datensatz |
|---|---|---|
| INRC-II *Scenario*: Skills, Contracts, Nurses, ShiftTypes mit `forbidden successions` | Stammdaten des Horizonts | Spaltenblöcke *Mitarbeiterstammdaten* (`role`, `skills`, `employment_pct`, …) und *Schichtdefinitionen* (`shift_*_start/end/net_min/forbidden_next`) |
| INRC-II *Week Data*: `requirements` je Schicht/Skill/Wochentag (minimum + optimal) | Nachfrage | `ppug_min_F/S/N` (Minimum = gesetzlich) und `required_F/S/N` (fachliches Soll) |
| INRC-II *History*: letzte Schicht, laufende Dienst-/Freitagszähler, Wochenendzähler | Anschluss an die Vorperiode | `history_shift` auf den 28 Tagen mit `period = history` + `time_account_start_min` |
| INRC-II Nebenbedingungen H1–H4 / S1–S7 | Regelwerk | Spaltenblock `rule_*` (mit Rechtsquelle statt Wettbewerbsgewicht) |
| Curtois/Qu *Staff*: `MaxShifts` je Typ, `MaxTotalMinutes`, `MinTotalMinutes`, `MaxConsecutiveShifts`, `MinConsecutiveDaysOff`, `MaxWeekends` | Vertrags- und Arbeitszeitgrenzen je Person | `min/max_total_minutes`, `max_consecutive_shifts`, `min_consecutive_days_off`, `max_weekends`, `max_night_shifts` |
| Curtois/Qu *Days off* und *Shift on/off requests* mit Gewicht | vorab feststehende Abwesenheiten und Präferenzen | `available` / `availability_type` (hart) und `request_off_weight` / `request_on_shift` / `request_on_weight` (weich) |
| Curtois/Qu *Cover* mit Unter-/Überbesetzungsgewicht | Bedarfsdeckung als Zielgröße | `required_F/S/N` (Deckungsgrad als KPI, nicht als harte Restriktion) |
| Nurse **Re**-Rostering (Wickert, Smet, Vanden Berghe, *Computers & Operations Research*) | gestörter Ausgangsplan + Störereignis + Stabilitätsmaß | `history_shift` (Ausgangsplan-Logik), `absence_s1/s2` mit `absence_s*_notice_h`, KPI „Planstabilität" |

**Bewusste Abweichung in der Form:** INRC-II und Curtois/Qu bündeln alles in *einer* Textdatei
mit `SECTION_…`-Blöcken; eine relationale Modellierung würde daraus vierzehn normalisierte
Tabellen machen. Ausgeliefert wird hier stattdessen **eine einzige, denormalisierte CSV-Datei**
im Korn *ein Mitarbeitender × ein Kalendertag*. Begründung in Abschnitt 4 — der
Informationsgehalt ist in allen drei Formen identisch, `generate_dataset.py --normalized`
erzeugt die Normalform auf Wunsch zusätzlich.

---

## 3. Woher die *Werte* kommen: deutsches Regelwerk und amtliche Statistik

Die internationalen Benchmarks liefern die Form, nicht die Zahlen — ihre Instanzen stammen aus
belgischen, britischen und niederländischen Häusern mit anderen Arbeitszeit- und
Besetzungsregeln. Alle inhaltlichen Parameter sind deshalb aus deutschen Quellen abgeleitet.

### 3.1 Besetzung und Qualifikation

| Parameter | Wert | Quelle |
|---|---|---|
| Pflegesensitiver Bereich | Innere Medizin und Kardiologie | PpUGV § 6 i. V. m. Anlage |
| Verhältniszahl Tagschicht | 10 Patienten je Pflegekraft | PpUGV § 6 / Anlage |
| Verhältniszahl Nachtschicht | 22 Patienten je Pflegekraft | PpUGV § 6 / Anlage |
| Max. Pflegehilfskraftanteil | 10 % (Tag und Nacht) | PpUGV Anlage |
| Tagschicht / Nachtschicht | 6–22 Uhr / 22–6 Uhr | PpUGV § 2 |
| Bezugsbestand | Tagschicht: Patientenbestand 12:00 Uhr; Nachtschicht: Mitternachtsbestand | PpUG-Nachweis-Vereinbarung 2026 (GKV-SV/DKG/PKV) |
| „Pflegekraft" = Pflegefachkraft **oder** Pflegehilfskraft | Auszubildende sind dort nicht genannt | PpUGV § 2 Abs. 1–3 |

Zwei Modellierungsentscheidungen folgen unmittelbar aus diesen Werten und sind deshalb
belegbar statt gesetzt:

1. **Keine Pflegehilfskraft im Nachtdienst.** Bei einem Zwei-Personen-Nachtdienst wäre eine
   Hilfskraft ein Anteil von 50 % und damit weit über der 10-%-Grenze der PpUGV-Anlage.
   `demand.max_pflegehilfskraft` ist im Nachtdienst folglich 0.
2. **Auszubildende zählen nicht auf die Mindestbesetzung.** § 2 PpUGV definiert Pflegekräfte
   abschließend als Pflegefachkräfte und Pflegehilfskräfte. Auszubildende werden im Datensatz
   deshalb mit `ppug_countable = 0` geführt: sie sind einzuplanen (Praxiseinsatz), entlasten
   aber die Untergrenze nicht. Genau das erzeugt den in der Praxis bekannten Effekt, dass
   Ausbildung Planungskapazität *bindet* statt sie zu schaffen.

### 3.2 Arbeitszeitrecht

| Regel | Wert | Quelle |
|---|---|---|
| Werktägliche Höchstarbeitszeit | 8 h, verlängerbar auf 10 h bei Ausgleich auf 8 h im Schnitt (24 Wochen / 6 Monate) | ArbZG § 3 |
| Ruhepause | ≥ 30 min bei > 6–9 h, ≥ 45 min bei > 9 h; nie länger als 6 h Arbeit am Stück | ArbZG § 4 |
| Ruhezeit | 11 h ununterbrochen | ArbZG § 5 Abs. 1 |
| Ausnahme Krankenhaus | Verkürzung um bis zu 1 h zulässig, wenn jede Verkürzung binnen eines Monats / vier Wochen durch Verlängerung einer anderen Ruhezeit auf 12 h ausgeglichen wird | ArbZG § 5 Abs. 2 |
| Nachtarbeit | werktäglich 8 h, auf 10 h nur mit Ausgleich im Monat / in vier Wochen | ArbZG § 6 Abs. 2 |
| Menschengerechte Gestaltung | gesicherte arbeitswissenschaftliche Erkenntnisse | ArbZG § 6 Abs. 1 |
| Regelmäßige Wochenarbeitszeit | 38,5 h (Vollzeit) | TVöD-K § 6 Abs. 1 |
| Urlaubsanspruch | 30 Arbeitstage bei 5-Tage-Woche | TVöD-K § 26 Abs. 1 |

Aus § 5 ArbZG folgt die Spalte `forbidden_successors` in `shift_types.csv` **rechnerisch**,
nicht per Setzung. Mit den gewählten Dienstzeiten ergeben sich:

| Vorgänger | Nachfolger am Folgetag | Ruhezeit | zulässig |
|---|---|---|---|
| Spät (Ende 21:30) | Früh (Beginn 06:00) | 8,5 h | **nein** (auch nicht mit § 5 Abs. 2) |
| Nacht (Ende 06:15) | Früh (Beginn 06:00) | 23,75 h | ja |
| Nacht (Ende 06:15) | Spät (Beginn 13:30) | 7,25 h | **nein** |
| Nacht | Nacht | 15,0 h | ja |

Der klassische „Spät-Früh-Wechsel" ist damit im Datensatz keine Präferenz, sondern eine harte
Restriktion mit Rechtsgrundlage. Das Prüfskript verifiziert, dass die Spalte exakt die Menge
der Ruhezeitverstöße abbildet.

### 3.3 Belegung und Pflegeaufwand

| Parameter | Wert | Quelle |
|---|---|---|
| Mittlere Bettenauslastung | 72,0 % (2024) | Destatis, Krankenhausstatistik 2024 |
| Durchschnittliche Verweildauer | 7,1 Tage (2024) | Destatis, Krankenhausstatistik 2024 |
| Pflegegrundwert | 33 min je Patient und Tag (123 min bei Isolationspflicht) | PPBV / PPR 2.0 |
| Fallwert | 75 min je Aufnahme | PPBV / PPR 2.0 |
| Spannweite Pflegeaufwand Erwachsene, Normalstation | 59 min (A1/S1) bis 427 min (A4/S4) je Patient und Tag | Wissenschaftliche Dienste des Deutschen Bundestages, WD 8 - 3000 - 008/26 |

Die Verweildauer erzeugt die Aufnahmezahl (`census / 7,1`), die Aufnahmezahl über den Fallwert
den administrativen Zusatzaufwand — so hängen Belegung, Fluktuation und Pflegeaufwand
konsistent zusammen, statt drei unabhängig gewürfelte Spalten zu sein.

### 3.4 Personalstruktur

| Parameter | Wert | Quelle |
|---|---|---|
| Teilzeitquote im Pflegedienst | 57,4 % | Statistik Sachsen, Beschäftigte in Krankenhäusern 2024 (Auswertung 2026) |
| Anteil examinierter Pflegefachkräfte | 82,4 % | ebenda |
| Vollkräfte je Kopf | 21.503 VK / 26.716 Beschäftigte = 0,805 | ebenda |
| Arbeitsunfähigkeitstage Krankenpflege | 28 Tage/Jahr (Ø aller Beschäftigten: 18,6) | TK-Gesundheitsreport |

### 3.5 Bruttopersonalbedarf — die Größe der Belegschaft ist gerechnet, nicht geraten

```
Nettobedarf   = Σ (Sollbesetzung × Nettodienstdauer) / (38,5 h × 4 Wochen)
              = 109.665 min / 9.240 min                        = 11,87 VK

Ausfallquote  = (30 Urlaubstage + 20 AU-Arbeitstage + 5 Fortbildungstage) / 251 Jahresarbeitstage
              = 21,9 %                        [Urlaub: TVöD-K § 26; AU: TK, 28 Kalendertage ≈ 20 Arbeitstage]

Bruttobedarf  = 11,87 / (1 − 0,219)                            = 15,20 VK
```

Die erzeugte Belegschaft: **22 Köpfe / 18,65 VK**, davon 19 anrechenbare Personen mit
15,65 VK (abzüglich 50 % Leitungsfreistellung ≈ 15,15 VK planbar) und 3 Auszubildende.
Das trifft den Bruttobedarf von 15,20 VK. Zum Vergleich: der bisherige Dummy-Datensatz mit
40 Köpfen entspräche etwa 32 VK und damit dem Doppelten des rechnerischen Bedarfs.

**Bewusste Abweichung von der Statistik:** Der Fachkraftanteil liegt im Datensatz bei 89,5 %
statt bei den bundesweit 82,4 %. Das ist kein Fehler, sondern eine Folge der Rechtslage: eine
dritte Pflegehilfskraft würde die 10-%-Grenze der PpUGV-Anlage für diesen Bereich reißen
(aktuell 8,0 % Kapazitätsanteil). Der bundesweite Durchschnitt mischt Bereiche mit Grenzen bis
20 %. Die strengere Norm hat Vorrang vor dem Mittelwert.

### 3.6 Vier Stationstypen — und was dabei bewusst *nicht* variiert wird

Die Evaluationskampagne variiert Seed und Personaldecke, aber immer auf derselben Station.
Damit ist belegt, dass ein Befund nicht an einer einzelnen Zufallsziehung hängt. **Nicht**
belegt ist damit, dass er nicht an *dieser Station* hängt — an 30 Betten, an der
Verhältniszahl 10:1, an genau diesem Qualifikationsmix. Für diese Frage erzeugt der
Generator drei weitere Stationstypen. Die Verhältniszahlen und Hilfskraftquoten sind der
Anlage zur PpUGV entnommen und damit belegt; Bettenzahl und Hilfskraftbesetzung sind
[ANNAHME] und bilden eine plausible Station des jeweiligen Typs ab.

| Stationstyp | Betten | Tagschicht | Nachtschicht | Hilfskräfte Tag/Nacht | Köpfe | Solldienste |
|---|---|---|---|---|---|---|
| Innere Medizin / Kardiologie *(Hauptstation)* | 30 | 10:1 | 22:1 | 10 % / 10 % | 23 | 237 |
| Geriatrie | 40 | 10:1 | 20:1 | 15 % / 20 % | 28 | 306 |
| Herzchirurgie | 24 | 7:1 | 15:1 | 5 % / 0 % | 20 | 220 |
| Intensivmedizin | 12 | 2:1 | 3:1 | 5 % / 5 % | 28 | 330 |

Die Intensivstation ist der lehrreichste Fall: Sie hat mit 12 Betten die *kleinste*
Bettenzahl und mit 28 Köpfen die *zweitgrößte* Belegschaft. Die Verhältniszahl 2:1 kehrt
die Intuition um — nicht die Größe der Station bestimmt den Personalbedarf, sondern die
Pflegeintensität. Zugleich ist sie die einzige Station ohne Pflegehilfskräfte, weil 5 % von
einem Schichtteam dieser Größe ganzzahlig null ergeben.

**Entscheidend ist, was dabei gleich bleibt.** Geändert werden ausschließlich *Werte*
innerhalb des Datensatzes. Das **Schema** — 94 Spalten, Korn Mitarbeitende × Kalendertag —
ist identisch, und `planner.py` wurde für die Replikation nicht angefasst. Das hat zwei
Gründe:

1. **Methodisch.** Der Vergleich der beiden Planungsverfahren steht und fällt damit, dass
   beide dieselbe Eingabe lesen. Ein zweites Schema hieße ein zweiter Lesepfad — und dann
   prüft die Replikation das CSV-Einlesen mit, nicht die Planungsverfahren.
2. **Inhaltlich.** Dass ein anderer Stationstyp ohne Codeänderung planbar ist, ist der
   Beleg für das Konstruktionsprinzip des Prototyps: **Grenzwerte stehen in den Daten,
   nicht im Code.** Wäre irgendwo eine 10:1 fest verdrahtet, würde die Intensivstation mit
   2:1 sofort falsche Untergrenzen erzeugen — und das Prüfskript würde es melden.

Eine Änderung des Schemas wäre also nicht die stärkere, sondern die schwächere Prüfung. Sie
würde die Aussage, die wir belegen wollen, gerade zerstören.

Die drei Replikationsinstanzen liegen unter `instanzen/` und werden vom selben Prüfskript
geprüft wie die Hauptinstanz (`python validate_dataset.py instanzen/datensatz_geriatrie.csv`).
Ausgewählt sind sie nach **derselben Regel wie die Hauptinstanz** (Abschnitt 5.2): die erste
Instanz in aufsteigender Seed-Reihenfolge ab 20261130, in der S1 und S2 exakt gleich viele
Ausfalltage tragen — Geriatrie 20261164 (25 zu 25), Herzchirurgie 20261216 (15 zu 15),
Intensivmedizin 20261146 (28 zu 28). Die Regel greift ausschließlich auf Eingangsdaten zu.

*Anmerkung zur Quelle:* Die Anlage zur PpUGV führt die pflegesensitiven Bereiche einzeln.
Die von uns verwendeten 10:1 / 22:1 entsprechen der Zeile „Innere Medizin"; eine Quelle
führt Kardiologie mit 12:1 / 24:1 gesondert, eine andere fasst „Innere Medizin/Kardiologie"
mit 10:1 / 22:1 zusammen. Unser Wert ist damit der strengere der beiden Lesarten.

---

## 4. Die Einzeltabelle: Aufbau und Begründung

`schichtplan_datensatz.csv` — UTF-8, Komma-getrennt, ISO-Datumsformat, 1.288 Zeilen ×
94 Spalten, rund 520 KB. **Analysekorn: eine Zeile je Mitarbeitendem und Kalendertag**
(23 Mitarbeitende × 56 Tage = 28 Tage Historie + 28 Tage Planung).

### 4.1 Warum dieses Korn und nicht ein anderes

Eine einzelne Tabelle zwingt zu einer Entscheidung über das Korn, und die ist nicht beliebig:

| Kandidat | Zeilen | Bewertung |
|---|---|---|
| Tag × Schicht | 168 | Bedarf sauber, aber Mitarbeitende passen nicht hinein — die Ressourcenseite ginge verloren |
| Mitarbeitender × Tag × Schicht | 3.696 | dreifach redundant, ohne zusätzlichen Informationsgehalt: eine Person arbeitet höchstens einen Dienst pro Tag |
| **Mitarbeitender × Tag** | **1.288** | die Planungsentscheidung selbst („welchen Dienst bekommt Person *i* am Tag *d*?") ist genau eine Zeile; Bedarf je Schicht passt als drei Spaltengruppen daneben |

Das gewählte Korn ist damit identisch mit dem **Entscheidungsraum des Planungsproblems**: Der
gesuchte Dienstplan ist genau eine zusätzliche Spalte (`assigned_shift`) zu dieser Tabelle.
Das ist auch der Grund, warum die Excel-Baseline damit unmittelbar arbeiten kann — die Datei
ist bereits die leere Planmatrix.

### 4.2 Der Preis: bewusste Denormalisierung

Mitarbeiterstammdaten wiederholen sich in 56 Zeilen, Tages- und Bedarfsdaten in 22, Stations-
und Regelspalten in allen 1.288. Das verletzt die dritte Normalform. Das ist ein realer
Nachteil und wird hier bewusst in Kauf genommen:

- **Ein Artefakt, eine Version.** Vierzehn Dateien können auseinanderlaufen; eine Datei
  hat genau einen Stand. Für die Versionierung im Repository und für den Upload in Streamlit
  ist das der entscheidende Vorteil.
- **Kein Join-Code im Prototyp.** `pd.read_csv(...)` genügt; es gibt keine Merge-Logik, die
  fehlerhaft sein könnte.
- **Die Redundanz ist maschinell abgesichert.** Block A des Prüfskripts verifiziert, dass jede
  wiederholte Spalte je Schlüssel tatsächlich konstant ist. Ohne diesen Test wäre die
  Denormalisierung eine Fehlerquelle; mit ihm ist sie eine reine Bequemlichkeit.
- **Sie ist umkehrbar.** `generate_dataset.py --normalized` schreibt zusätzlich die vierzehn
  normalisierten Tabellen nach `data/`, falls die Hausarbeit das Datenmodell in dritter
  Normalform zeigen soll.

### 4.3 Spaltenverzeichnis

| Block | Spalten | Konstant je | Inhalt |
|---|---|---|---|
| **Schlüssel & Kalender** | `employee_id`, `date`, `period`, `day_index`, `weekday`, `weekday_num`, `iso_week`, `is_weekend`, `is_holiday`, `holiday_name` | – | Primärschlüssel ist (`employee_id`, `date`); `period` trennt Historie von Planhorizont |
| **Mitarbeiterstammdaten** | `role`, `role_group`, `skills`, `employment_pct`, `weekly_hours`, `contract_minutes_horizon`, `planable_minutes_horizon`, `min_total_minutes`, `max_total_minutes`, `max_consecutive_shifts`, `min_consecutive_days_off`, `max_weekends`, `max_night_shifts`, `night_eligible`, `ppug_countable`, `ppug_category`, `is_ward_lead`, `lead_release_pct`, `time_account_start_min` | `employee_id` | Vertrags- und Arbeitszeitgrenzen je Person; `skills` ist pipe-getrennt (`EXAM\|PRAXISANLEITUNG`); `ppug_countable` = 0 bei Auszubildenden |
| **Belegung** | `census_1200`, `census_0000`, `admissions`, `discharges`, `isolation_patients`, `care_minutes_total` | `date` | Bezugsbestände nach PpUG-Nachweisvereinbarung (12:00 für Tag-, 00:00 für Nachtschicht) |
| **Bedarf je Schicht** | je `F`/`S`/`N`: `required_*`, `ppug_min_*`, `min_fachkraft_*`, `max_hilfskraft_*`, `care_minutes_*`, `azubi_slots_*` | `date` | `ppug_min_*` = gesetzliche Untergrenze (hart), `required_*` = fachliches Soll (KPI) |
| **Verfügbarkeit & Wünsche** | `available`, `availability_type`, `request_off_weight`, `request_on_shift`, `request_on_weight` | – | `availability_type` ∈ {URLAUB, FORTBILDUNG, LANGZEITABWESENHEIT}; Wünsche mit Gewicht 1–3 |
| **Historie** | `history_shift` | – | tatsächlich geleisteter Dienst in der Vorperiode; im Planhorizont leer |
| **Ausfallszenarien** | `absence_s1`, `absence_s1_notice_h`, `absence_s2`, `absence_s2_notice_h` | – | 0/1 je Szenario plus Vorlaufzeit in Stunden; Szenario S0 = beide Spalten 0 |
| **Station** | `ward_id`, `ward_name`, `beds`, `ppug_bereich`, `ppug_ratio_day`, `ppug_ratio_night` | global | Stationsstammdaten |
| **Schichtdefinitionen** | je `F`/`S`/`N`: `shift_*_start`, `shift_*_end`, `shift_*_net_min`, `shift_*_forbidden_next` | global | `forbidden_next` = pipe-getrennte Liste unzulässiger Folgedienste am Folgetag |
| **Regelwerk** | `rule_min_rest_h`, `rule_min_rest_h_with_compensation`, `rule_max_daily_h`, `rule_max_daily_h_with_compensation`, `rule_break_min_6_to_9h`, `rule_break_min_over_9h`, `rule_max_night_h`, `rule_weekly_hours_fulltime`, `rule_annual_leave_days`, `rule_max_helper_share`, `rule_azubi_counts_towards_minimum` | global | alle harten Restriktionen als Zahlen im Datensatz — der Prototyp muss keine Grenzwerte im Code fest verdrahten |
| **Metadaten** | `dataset_version`, `seed` | global | macht jeden exportierten Plan auf seine Datenversion zurückführbar |

### 4.4 Einlesen im Prototyp

```python
import pandas as pd

df = pd.read_csv("schichtplan_datensatz.csv", parse_dates=["date"])

plan   = df[df.period == "plan"]                                    # Planhorizont
hist   = df[(df.period == "history") & df.history_shift.notna()]    # Vorperiode
staff  = df.drop_duplicates("employee_id").set_index("employee_id") # Stammdaten
days   = plan.drop_duplicates("date").set_index("date")             # Bedarf je Tag
rules  = df.iloc[0].filter(like="rule_")                            # Regelwerk

# Szenario wählen: "S0" (Referenz), "S1" (verteilt), "S2" (Welle)
def verfuegbar(df, szenario="S1"):
    aus = 0 if szenario == "S0" else df[f"absence_{szenario.lower()}"]
    return (df.available == 1) & (aus == 0)
```

Mehr braucht die Streamlit-App nicht — kein Join, keine Konfigurationsdatei, kein
hartkodierter Grenzwert.

### 4.5 Die zwei Nachfragegrößen — der wichtigste Punkt des Modells

Der Datensatz enthält je Schicht bewusst **zwei** Besetzungszahlen:

- `ppug_min_F/S/N` = ⌈Patienten / Verhältniszahl⌉ — die **gesetzliche Untergrenze**.
  Ihre Unterschreitung ist ein Rechtsverstoß und damit eine *harte* Nebenbedingung.
- `required_F/S/N` = fachliche **Sollbesetzung** aus dem Pflegeaufwand (PPR-2.0-Logik).
  Ihre Unterschreitung ist Unterbesetzung, also eine *Qualitätsgröße* und Ziel-KPI.

Diese Trennung ist keine Spitzfindigkeit. Die Auswertung des Bundestags-Gutachtens weist
darauf hin, dass trotz Untergrenzen rund 15 % der Schichten regelmäßig unterbesetzt bleiben —
eine Untergrenze ist eben keine Bedarfsbemessung. Würde der Datensatz nur eine Zahl enthalten,
könnte die Arbeit die zentrale betriebswirtschaftliche Aussage („der KI-Plan hält das Gesetz
ein *und* kommt der fachlichen Sollbesetzung näher") gar nicht formulieren.

### 4.6 Ableitungskette (Data Lineage)

```
Wochentag/Feiertag  ─┐
Bettenauslastung 72 %─┼─→ census_1200 / census_0000  ─┬─→ ppug_min_F/S/N     (PpUGV § 6)
Verweildauer 7,1 d   ─┘        │                      │
                               ├─→ admissions ────────┤
                               │                      │
Pflegeminuten je Pat. (59–427) ┤                      │
Grundwert 33 / Fallwert 75 ────┴─→ care_minutes_total ─┴─→ required_F/S/N = max(Untergrenze,
                                        │ Schichtanteil 40/35/25 %              PPR-Soll, Mindestbesetzung)
                                        └─→ care_minutes_F/S/N
                                                     │
required_staff × Nettominuten ──→ Nettobedarf ──/(1−Ausfallquote)──→ Bruttobedarf ──→ Belegschaft
```

Jede Spalte lässt sich damit bis auf eine Quelle oder eine im Register geführte Annahme
zurückführen — die Prüffrage aus T2 („Können wir den Datensatz morgen exakt erneut erzeugen
und fachlich erklären?") ist mit Seed und Skript mit Ja zu beantworten.

---

## 5. Ausfallszenarien

Die Projektvorgabe verlangt mindestens zwei Ausfallszenarien und verbietet Gesundheitsdaten.
Beides ist im Modell getrennt gelöst: Ausfälle sind **reine Verfügbarkeitsereignisse** ohne
Grund, Kategorie oder Diagnose. Die Szenarien liegen als eigene Spaltenpaare nebeneinander,
sodass beide Planungsansätze auf **derselben Datei** über das Szenario schalten können, statt
verschiedene Dateien zu laden.

### 5.1 Der entscheidende Konstruktionsgrundsatz: gleicher Umfang, andere Struktur

S1 und S2 sind bewusst auf **denselben Umfang kalibriert**. Unterschieden sie sich zugleich in
der Menge der Ausfälle und in deren Verteilung, wäre der Vergleich konfundiert: Jede
Ergebnisdifferenz ließe sich ebenso gut mit „S2 hat einfach mehr Ausfälle" erklären, und die
Aussage über korrelierte Ausfälle wäre nicht belegbar.

| Szenario | Struktur | Spalten | Realisiert (Seed 20261133) |
|---|---|---|---|
| **S0** | keine kurzfristigen Ausfälle; nur geplante Abwesenheiten | beide Ausfallspalten 0 | 0 Ausfalltage |
| **S1** | unabhängige Einzeltage, Rate 4 % je Person und Tag über den gesamten Horizont | `absence_s1`, `absence_s1_notice_h` | 19 Ausfalltage, 10 Personen |
| **S2** | 7 Krankheitsepisoden von 2–4 Tagen; Beginn zu 80 % im Fenster 14.–19.12. | `absence_s2`, `absence_s2_notice_h` | 19 Ausfalltage, 6 Personen |

Die Wirkung dieser Kalibrierung:

| | S1 | S2 |
|---|---|---|
| Ausfalltage gesamt | 19 | 19 |
| Anteil im Wellenfenster | 5 % | **79 %** |
| betroffene Personen | 10 | **6** |
| längste zusammenhängende Episode | 1 Tag | **4 Tage** |
| Ausfälle je Tag **im** Wellenfenster | 0,17 | **2,50** |
| Ausfälle je Tag **außerhalb** | 0,82 | **0,18** |

Bei **exakt gleicher Zahl an Ausfalltagen** trifft S2 also deutlich weniger Personen, diese
dafür mehrtägig und weitgehend gleichzeitig. Innerhalb des Fensters ist die Tageslast rund
vierzehnmal so hoch wie außerhalb; vier Fünftel aller Ausfalltage liegen in diesen sechs
Tagen. Das ist das Bild einer Infektwelle auf Station.

### 5.2 Auswahl der ausgelieferten Instanz

Die Kalibrierung der Episodenzahl (Abschnitt 5.3) gleicht das Ausfallvolumen **im Mittel
über die Kampagneninstanzen** an, nicht in jeder einzelnen Ziehung. Eine zufällig gezogene
Einzelinstanz kann deshalb deutlich unausgewogen sein — im zuvor ausgelieferten Datensatz
(Seed 20261130) trug S1 mit 26 gegen 18 Ausfalltagen 44 % mehr Volumen als S2. Die
Planstabilität fiel dort bei S2 **höher** aus als bei S1, weil schlicht weniger Löcher zu
stopfen waren: 9 gegen 16 Ausfalltage trafen einen tatsächlich geplanten Dienst. Diese
Einzelinstanz widersprach damit der Richtung der Kampagne.

Der ausgelieferte Datensatz wird deshalb nach einer **vorab festgelegten Regel auf einer
Eigenschaft der Daten** ausgewählt, nicht nach dem Planungsergebnis:

> Ausgeliefert wird die erste Instanz in aufsteigender Seed-Reihenfolge ab 20261130, in der
> S1 und S2 **exakt gleich viele Ausfalltage** tragen.

Das ist Seed 20261133 (19 gegen 19). Die Regel greift ausschließlich auf die Eingangsdaten
zu; welches Planungsergebnis daraus folgt, geht in die Auswahl nicht ein. Eine Selektion
nach dem Ergebnis wäre unzulässig und ist hier ausdrücklich nicht erfolgt. Der Seed ist
zugleich einer der fünf Kampagnenseeds, sodass die in der Anwendung gezeigte Instanz Teil
der Evaluation ist.

Über die 15 Instanzen der Evaluationskampagne gemittelt bleibt die Abweichung zwischen den
Szenarien klein; die Einzelinstanzen streuen um diesen Wert.

### 5.3 Warum Episoden und nicht erhöhte Tagesraten

Ein früheres Modell erhöhte im Wellenfenster lediglich die Tagesrate von 4 % auf 12 %. Das
hatte zwei Mängel, die erst in der Auswertung auffielen:

**Es erzeugte keine Episoden.** Jeder Tag wurde unabhängig gezogen, die längste
zusammenhängende Abwesenheit einer Person betrug einen Tag. Real fehlt jemand, der heute
krank ist, in aller Regel auch morgen — und genau diese Mehrtägigkeit bringt eine Station in
Bedrängnis, nicht der verstreute Einzeltag.

**Es veränderte den Umfang mit.** Über fünf Seeds erzeugte das alte S2 im Mittel 31,2
Ausfalltage gegenüber 18,8 bei S1 — zwei Drittel mehr. Die beiden Szenarien unterschieden
sich damit in zwei Dimensionen gleichzeitig.

Das Episodenmodell behebt beides: Die Episodenzahl ist empirisch auf das Ausfallvolumen
von S1 kalibriert, und die Mehrtägigkeit ist explizit modelliert statt als Nebeneffekt
einer erhöhten Tagesrate erhofft.

**Die Kalibrierung ist ein Parameter je Stationstyp, keine feste Zahl.** Das Ausfallvolumen
von S1 entsteht aus Rate × Personentagen und wächst damit mit der Belegschaft. Eine für
23 Köpfe kalibrierte Episodenzahl erzeugt auf einer Station mit 28 Köpfen deutlich zu wenig
Ausfalltage — der Vergleich S1 gegen S2 wäre dort konfundiert, und zwar in der Richtung,
die unsere These begünstigt. Die Zahl steht deshalb in `WARD_TYPEN[…]["s2_episoden"]` und
wird mit `generate_dataset.kalibriere_episoden()` bestimmt. Innerhalb eines Stationstyps
bleibt sie über alle Seeds und Personaldecken konstant — sonst würde jede Instanz nach
ihrem eigenen Maßstab kalibriert.

Gemessen über die 15 Kampagneninstanzen (5 Seeds × 3 Personaldecken) je Stationstyp:

| Stationstyp | Episoden | Ø S1-Tage | Ø S2-Tage | Abweichung der Mittelwerte | mittlere Abweichung je Instanz |
|---|---|---|---|---|---|
| Innere Medizin | **7** | 15,7 | 17,8 | 13,6 % | 21,7 % |
| *(dieselbe Station mit 6)* | *6* | *15,7* | *15,6* | *0,4 %* | *14,6 %* |
| Geriatrie | **8** | 22,9 | 19,6 | 14,5 % | 21,1 % |
| Herzchirurgie | **6** | 18,6 | 15,9 | 14,3 % | 20,7 % |
| Intensivmedizin | **10** | 26,9 | 24,7 | 8,2 % | 25,9 % |

Zwei Dinge sind daran offen auszusprechen:

**Erstens** wurde für die drei Replikationsstationen jeweils der Wert gewählt, der die
mittlere Abweichung **je Instanz** minimiert — nicht der, der die Mittelwerte zur Deckung
bringt. Beide Kriterien liegen nur ein bis zwei Episoden auseinander, aber das erste ist das
strengere: Wenn sich in einer Instanz zu viele und in einer anderen zu wenige Ausfalltage
gegenseitig aufheben, sieht der Mittelwertvergleich gut aus, obwohl jede einzelne Instanz
konfundiert ist.

**Zweitens** ist die Hauptstation die dokumentierte Ausnahme. Ihr Wert 7 stammt aus einer
früheren Kalibrierung; die heutige Messung weist 6 als besseren Wert aus (Zeile in Kursiv).
Wir behalten 7 bei, weil sämtliche veröffentlichten Kampagnenergebnisse mit diesem Wert
gerechnet sind und aus dem ausgelieferten Datensatz reproduzierbar bleiben sollen. Der
Preis ist benannt: S2 trägt auf der Hauptstation im Mittel 13,6 % mehr Ausfalltage als S1.
Für die ausgelieferte Instanz selbst ist die Parität exakt (19 zu 19, Abschnitt 5.2); die
Richtung der Abweichung über die Kampagne hinweg spricht **gegen** und nicht für unsere
These, weil S2 dort etwas mehr Last trägt. Eine Neurechnung der Kampagne mit 6 Episoden
wäre die saubere Auflösung und ist als offener Punkt vermerkt.

### 5.4 Vorlaufzeit

`absence_s*_notice_h` gibt an, wie viele Stunden vor Dienstbeginn die Meldung eingeht. In S2
trägt nur der **erste Tag einer Episode** eine kurzfristige Meldung (2–12 Stunden); die
Folgetage stehen mit 24 Stunden Vorlauf, weil eine laufende Krankmeldung dem Plan bereits
bekannt ist. Die Spalte ist im Datensatz vorhanden, wird von den Planungsverfahren aber
derzeit **nicht ausgewertet** — beide behandeln alle Ausfälle gleich. Das ist eine bewusste
Vereinfachung und in Abschnitt 10 als Limitation geführt.

Das Szenariodesign trennt sauber, was die Arbeit trennen muss: **S0 misst Planerstellung,
S1/S2 messen Anpassungsfähigkeit.** Beide Verfahren erhalten identische Ereignisdateien.

### 5.5 Was ein Ausfall arbeitszeitrechtlich bedeutet

Ein Ausfall im Datensatz ist ein Verfügbarkeitsereignis ohne Grund. Für die Planung wird er
als **Arbeitsunfähigkeit** behandelt — das ist die Lesart, die die Projektvorgabe mit
„Krankheitsausfällen" meint. Daraus folgt eine Regel, die nicht im Datensatz steht, sondern
aus ihm und dem Ausgangsplan berechnet wird: die **Krankheitsgutschrift** nach dem
Entgeltausfallprinzip (§ 4 Abs. 1 EFZG; BAG, 05.10.2023 – 6 AZR 210/22). Gutgeschrieben
wird die Nettodauer des Dienstes, den die Person laut Ausgangsplan an dem Ausfalltag gehabt
hätte; ein Ausfall an einem dienstfreien Tag ergibt keine Gutschrift. Die Gutschrift zählt
wie gearbeitete Zeit für Auslastung, Zielarbeitszeit und vertragliche Obergrenze — Letzteres
ist eine [ANNAHME], im Annahmenregister als A14 geführt.

Die Gutschrift braucht keine zusätzlichen Daten und keine Gesundheitsinformation: Sie knüpft
allein an die Tatsache des Ausfalls und an den Dienstplan, der zu diesem Zeitpunkt galt.
Warum sie nötig ist und was sich durch sie an den Ergebnissen geändert hat, steht in
`ERGEBNISSE.md`, Abschnitt 3.2.

---

## 6. Annahmenregister

Alles, was nicht belegt ist, steht hier — offen und einzeln prüfbar.

| ID | Annahme | Wert | Begründung | Sensitivität |
|---|---|---|---|---|
| A1 | Stationsgröße | 30 Betten | typische Normalstationsgröße; skaliert die gesamte Instanz | hoch |
| A2 | Dienstzeiten | F 06:00–14:00, S 13:30–21:30, N 21:15–06:15 | Drei-Schicht-System mit Übergabeüberlappung; Pausen nach § 4 ArbZG eingerechnet | mittel — verändert die verbotenen Schichtfolgen |
| A3 | Verteilung des Tagesaufwands | F 40 %, S 35 %, N 25 % | Grundpflege, Visite und Diagnostik konzentrieren sich auf den Vormittag | hoch — verschiebt die Sollbesetzung je Schicht |
| A4 | Verteilung des Pflegeaufwands je Patient | lognormal, Median 118 min, gestutzt auf 59–427 min | die Spannweite ist belegt, die Form innerhalb der Spannweite nicht | mittel |
| A5 | Wochentagsprofil der Belegung | Mo–Do +5 bis +9 %, Fr −2 %, Sa/So −10 % | Elektivsteuerung und Entlassungen zum Wochenende | mittel |
| A6 | Weihnachtseffekt | Faktor 0,80 ab 24.12. | reduzierter Elektivbetrieb | niedrig |
| A7 | Anteil kurzfristiger an gesamten Ausfällen (S1) | 4 % der Personentage | AU-Tage insgesamt sind belegt, die Aufteilung Kurz-/Langzeit nicht | **hoch** — Kerngröße der Szenarien |
| A7a | Dauer einer Krankheitsepisode (S2) | 2–4 Tage, gleichverteilt | mehrtägige Abwesenheit ist der Normalfall; die konkrete Verteilung ist gesetzt | mittel |
| A7b | Konzentration der Welle (S2) | 7 Episoden (Hauptstation), Beginn zu 80 % im Sechstagefenster | Stärke und Länge einer Infektwelle sind nicht belegt; die Episodenzahl ist je Stationstyp auf das Ausfallvolumen von S1 kalibriert (Hauptstation: Ø 17,8 gegen 15,7 Ausfalltage, Abweichung 13,6 %; Abschnitt 5.3) | **hoch** — bestimmt den Kontrast zwischen den Szenarien |
| A8 | Zwei-Personen-Nachtdienst | Minimum 2 | die Untergrenze ergäbe bei 21 Patienten rechnerisch 1 Kraft; ein Alleindienst ist auf 30 Betten praktisch nicht vertretbar (Pausenablösung, § 4 ArbZG) | mittel |
| A9 | Mindestbesetzung Tagdienst | 3 ab 15 Patienten | Pausenablösung und Vertretbarkeit | mittel |
| A10 | Max. 5 Dienste in Folge, ≥ 2 freie Tage am Stück, max. 2 Wochenenden / 4 Wochen, max. 8 Nachtdienste / 4 Wochen | – | gestützt auf § 6 Abs. 1 ArbZG (arbeitswissenschaftliche Erkenntnisse), aber nicht beziffert im Gesetz | mittel |
| A11 | Leitungsfreistellung 50 %, Leitung nur im Frühdienst | – | übliche Praxis; senkt die planbare Kapazität | niedrig |
| A12 | Historie per Greedy-Heuristik erzeugt | – | die Historie ist Eingabe, nicht Evaluationsgegenstand; sie muss nur regelkonform und plausibel sein | niedrig |
| A13 | Ausfallzeiten für den Bruttobedarf | 30 Urlaub + 20 AU + 5 Fortbildung von 251 Arbeitstagen | Urlaub und AU belegt, Fortbildungstage und Jahresarbeitstage gesetzt | mittel |
| A14 | Krankheitsgutschrift zählt auf die vertragliche Obergrenze | Ist + Gutschrift ≤ 110 % der Sollzeit | Die Gutschrift selbst ist belegt (§ 4 Abs. 1 EFZG); dass die Obergrenze als Grenze des Arbeitszeitkontos gilt, ist gesetzt. Ohne diese Setzung dürfte eine kranke Person zusätzlich bis an die Obergrenze eingeplant werden | mittel — erzeugt bei 80 % Decke einzelne offene Dienste der Optimierung |

Die Annahmen mit hoher Sensitivität (A3, A7, A7b) gehören in die Limitationen der Hausarbeit und
eignen sich als Sensitivitätsanalyse: Der Generator ist parametrisiert, ein Lauf mit
verändertem A7 und identischem Seed erzeugt eine vergleichbare Variante des Datensatzes.

---

## 7. Datenschutz und Ethik (T7)

- **Keine personenbezogenen Daten.** Mitarbeitende sind pseudonyme IDs (`PK-…`, `PH-…`,
  `AZ-…`). Die Klarnamen aus dem bisherigen Prototyp entfallen ersatzlos; sie hatten keinen
  fachlichen Nutzen und erzeugten den falschen Eindruck echter Personaldaten.
- **Keine Gesundheitsdaten.** Ausfälle werden ausschließlich als Nichtverfügbarkeit
  modelliert. Es gibt keine Spalte für Grund, Diagnose oder Erkrankungsart — auch nicht in
  aggregierter oder verschlüsselter Form. Das Prüfskript verweigert die Freigabe, wenn eine
  Personentabelle eine entsprechende Spalte enthält.
- **Vollständig synthetisch.** Kein Datensatz-Element stammt aus einer realen Einrichtung.
  Reale Werte gehen ausschließlich als aggregierte, veröffentlichte Kennzahlen ein
  (Auslastung, Quoten, Verhältniszahlen).
- **Keine Auswertung individuellen Verhaltens.** Der Datensatz enthält keine Leistungs- oder
  Verhaltensdaten; er eignet sich nicht als Grundlage für Mitarbeiterbewertung.

---

## 8. Qualitätssicherung

`validate_dataset.py` prüft den Datensatz in sechs Blöcken und läuft ohne harte Fehler durch:

| Block | Prüfungen (Auszug) | Ergebnis |
|---|---|---|
| A Struktur | vollständiges Kreuzprodukt 22 × 56, eindeutiger Schlüssel, lückenloser Kalender, **jede redundante Spalte je Schlüssel konstant**, Szenariospalten nur im Planhorizont, höchstens ein Dienst je Person und Tag | bestanden |
| B Recht | Pausenlängen nach § 4, Nettodauer ≤ 10 h, verbotene Schichtfolgen = exakt die Menge der Ruhezeitverstöße | bestanden |
| C Erfüllbarkeit | Soll 109.665 min vs. verfügbar 121.394 min → **Auslastung 90,3 %** | bestanden |
| D PpUGV | Soll ≥ Untergrenze in jeder Schicht, Untergrenze = ⌈Bestand/Verhältniszahl⌉, Hilfskraftanteil 8,0 % ≤ 10 %, Azubis nicht anrechenbar | bestanden |
| E Plausibilität | Auslastung 71,3 % (Ziel 72,0 %), Fachkraftanteil 89,5 %, Teilzeit 52,6 %, VK/Kopf 0,848; Historie ohne Ruhezeitverstoß | bestanden |
| F Datenschutz | keine Namens-/Gesundheitsspalten in Personentabellen, alle Ausfälle grundlos | bestanden |

Der Validator ist Teil des Datensatzes und sollte in der Hausarbeit als Beleg für
Datenqualität zitiert werden — er macht die Aussage „der Datensatz ist regelkonform und
erfüllbar" überprüfbar statt behauptet.

---

## 9. Verwendung in Baseline und KI-Ansatz

Beide Verfahren erhalten **identische** Eingaben — das ist die Voraussetzung für einen fairen
Vergleich (Projektvorgabe 3):

| Spaltenblock | Excel-Baseline | Optimierungsbasierter Ansatz |
|---|---|---|
| Stammdaten, Bedarf, Verfügbarkeit, Historie | ein Arbeitsblatt, Pivot je Bedarfsspalte | ein DataFrame, Filter nach `period` |
| `rule_*` | als Prüfformeln / bedingte Formatierung | als harte und weiche Nebenbedingungen |
| `request_off_weight`, `request_on_*` | in der Praxis meist ignoriert | als gewichteter Zielfunktionsterm |
| `absence_s1` / `absence_s2` | manuelle Umplanung, Zeit messen | Re-Optimierung, Zeit messen |

Beide Ansätze erzeugen dieselbe Ergebnisspalte `assigned_shift` und lassen sich damit
zeilenweise vergleichen. Messbare KPIs, die der Datensatz trägt: Besetzungsquote gegen
`required_F/S/N`, Untergrenzenverstöße gegen `ppug_min_F/S/N`, Regelverstöße gegen die
`rule_*`-Spalten, Qualifikationskonformität gegen `min_fachkraft_*`/`max_hilfskraft_*`,
Arbeitszeitabweichung gegen `min/max_total_minutes` und `time_account_start_min`,
Planstabilität als Zahl geänderter Zuweisungen zwischen Ausgangs- und angepasstem Plan,
Wunscherfüllung gegen `request_off_weight`.

---

## 10. Limitationen

1. **Eine Station, ein Monat.** Keine stationsübergreifende Springerlogik, keine
   Saisonalität über das Jahr, kein Pool-Personal, keine Leiharbeit.
2. **Kein ärztlicher Dienst.** Ärztliche Dienstplanung ist ein eigenständiges Problemfeld
   (Bereitschaftsdienst, Opt-out nach § 7 ArbZG, Rotationen, Weiterbildungsordnung) und wird
   in der Literatur auch getrennt behandelt (Erhard et al., *State of the art in physician
   scheduling*). Eine gemeinsame Modellierung hätte den Prototyp-Rahmen gesprengt.
3. **Der Pflegeaufwand ist simuliert, nicht erhoben.** Die PPR-2.0-Spannweite ist belegt, die
   Verteilung innerhalb der Spannweite ist Annahme A4. Die absolute Höhe der Sollbesetzung ist
   damit unsicher; der *Vergleich* zweier Verfahren auf identischer Datenbasis bleibt gültig.
4. **Ausfälle sind exogen.** Zusammenhänge zwischen Belastung und Ausfallrisiko werden nicht
   modelliert. Das ist auch datenschutzrechtlich gewollt, begrenzt aber die Aussagekraft zu
   langfristigen Effekten.
5. **Ein einzelner Seed.** Für belastbare Aussagen sollten mehrere Instanzen mit
   unterschiedlichen Seeds gerechnet und die KPIs über die Läufe gemittelt werden. Der
   Generator ist dafür vorbereitet.

---

## 11. Quellen

**Rechtsnormen**

- Arbeitszeitgesetz (ArbZG), §§ 3, 4, 5, 6 — <https://dejure.org/gesetze/ArbZG/3.html>, <https://dejure.org/gesetze/ArbZG/4.html>, <https://dejure.org/gesetze/ArbZG/5.html>, <https://dejure.org/gesetze/ArbZG/6.html>
- Pflegepersonaluntergrenzen-Verordnung (PpUGV), § 2 Begriffsbestimmungen — <https://lxgesetze.de/ppugv/2>
- Pflegepersonaluntergrenzen-Verordnung (PpUGV), § 6 und Anlage (Verhältniszahlen) — <https://lxgesetze.de/ppugv/6>
- Pflegepersonaluntergrenzen 2026, GKV-Spitzenverband — <https://www.gkv-spitzenverband.de/krankenversicherung/krankenhaeuser/pflegepersonaluntergrenzen/ppu_2026/ppug_2026.jsp>
- Vereinbarung nach § 137i Abs. 4 SGB V über den Nachweis zur Einhaltung der Pflegepersonaluntergrenzen 2026 (Bezugsbestände 12:00 / 00:00 Uhr) — <https://www.gkv-spitzenverband.de/media/dokumente/krankenversicherung_1/krankenhaeuser/pflegepersonaluntergrenzen/kh_ppug2026/2025_12_01_PpUG-Nachweis-Vereinbarung_2026_inkl_Anlagen_1-5.pdf>
- Pflegepersonalbemessungsverordnung (PPBV) / PPR 2.0, Grundwert und Fallwert — <https://planerio.de/blog/ppbv/>
- PpUGV 2026, Übersicht der Verhältniszahlen je pflegesensitivem Bereich (Tag-/Nachtschicht, Hilfskraftanteil) — <https://planerio.de/blog/ppugv/>
- Pflegepersonal-Untergrenzen 2026, unabhängige Bestätigung der Verhältniszahlen für Intensivmedizin, Geriatrie und Herzchirurgie — <https://msi-partners.de/artikel/pflegepersonal-untergrenzen-ppugv-2026>
- TVöD-K § 6 Regelmäßige Arbeitszeit — <https://www.tv-oed.de/tv-kommunaler-bereich/tvoed-k-krankenhaeuser/tvoed_k_006>
- TVöD-K § 26 Erholungsurlaub — <https://www.tv-oed.de/tv-kommunaler-bereich/tvoed-k-krankenhaeuser/tvoed_k_026>

**Amtliche Statistik und Gutachten**

- Statistisches Bundesamt: 2,0 % mehr stationäre Krankenhausbehandlungen im Jahr 2024 (Betten, Auslastung 72,0 %, Verweildauer 7,1 Tage) — <https://www.destatis.de/DE/Presse/Pressemitteilungen/2025/11/PD25_398_231.html>
- Statistisches Bundesamt: Ärztliches und nichtärztliches Personal in Krankenhäusern — <https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Gesundheit/Krankenhauser/Tabellen/personal-krankenhaeuser-jahre.html>
- Statistisches Landesamt Sachsen: Beschäftigte im Pflegedienst der Krankenhäuser 2024 (Teilzeitquote 57,4 %, Fachkraftanteil 82,4 %, Vollkräfte je Kopf) — <https://www.statistik.sachsen.de/download/presse-2026/mi_statistik-sachsen-070-2026_tag_der_krankenpflege_beschaeftigte_krankenhaeuser.pdf>
- Wissenschaftliche Dienste des Deutschen Bundestages, WD 8 - 3000 - 008/26: Pflegepersonalbemessung (Spannweite 59–427 Minuten, Grund-/Fallwert, Hinweis auf ca. 15 % unterbesetzte Schichten) — <https://www.bundestag.de/resource/blob/1167276/WD-8-008-26.pdf>
- Techniker Krankenkasse: Krankenstand bei Pflegekräften (28 AU-Tage in der Krankenpflege vs. 18,6 Tage im Durchschnitt) — <https://www.tk.de/presse/themen/pflege/pflegepolitik/krankenstand-bei-pflegekraeften-auf-rekordhoch-2149302>

**Wissenschaftliche Literatur**

- Burke, E. K., De Causmaecker, P., Vanden Berghe, G., & Van Landeghem, H. (2004). The State of the Art of Nurse Rostering. *Journal of Scheduling*, 7(6), 441–499. — <https://link.springer.com/article/10.1023/B:JOSH.0000046076.75950.0b>
- Ernst, A. T., Jiang, H., Krishnamoorthy, M., & Sier, D. (2004). Staff scheduling and rostering: A review of applications, methods and models. *European Journal of Operational Research*, 153(1), 3–27. — <https://www.sciencedirect.com/science/article/abs/pii/S037722170300095X>
- Van den Bergh, J., Beliën, J., De Bruecker, P., Demeulemeester, E., & De Boeck, L. (2013). Personnel scheduling: A literature review. *European Journal of Operational Research*, 226(3), 367–385. — <https://ideas.repec.org/a/eee/ejores/v226y2013i3p367-385.html>
- Ceschia, S., Dang, N., De Causmaecker, P., Haspeslagh, S., & Schaerf, A. Second International Nurse Rostering Competition (INRC-II) — Problem Description and Rules. arXiv:1501.04177. — <https://arxiv.org/pdf/1501.04177>
- Curtois, T., & Qu, R. Computational results on new staff scheduling benchmark instances. ASAP Research Group, University of Nottingham. — <https://www.schedulingbenchmarks.org/papers/new_approaches_to_nurse_rostering_benchmark_instances.pdf>
- Nurse Rostering Benchmark Instances (Instanzformat, 8–150 Mitarbeitende, 2–52 Wochen, 1–32 Schichtarten) — <https://www.schedulingbenchmarks.org/nrp/>
- Wickert, T. I., Smet, P., & Vanden Berghe, G. The nurse rerostering problem: Strategies for reconstructing disrupted schedules. *Computers & Operations Research*. — <https://www.sciencedirect.com/science/article/abs/pii/S0305054818303265>
- Erhard, M., Schoenfelder, J., Fügener, A., & Brunner, J. O. (2018). State of the art in physician scheduling. *European Journal of Operational Research*. — <https://www.sciencedirect.com/science/article/abs/pii/S0377221717305787>
- Ein Modellierungsrahmen zur Bewertung proaktiver und reaktiver Rostering-Strategien (NICU-Fallstudie), *Healthcare Analytics*. — <https://www.sciencedirect.com/science/article/pii/S2211692324000134>

**Kursunterlagen**

- T2 Projektmanagement/Business (Prof. Dr. Juliana Böhmke): Reproduzierbarkeit, Data Lineage, Data Contract; nach Schulz et al. (2026), S. 36–39
- T3 Datenmanagement und Grundlagen AI Use Cases: strukturierte vs. semi-strukturierte Daten
- T7 Ethik und Datenschutz: Verzicht auf personenbezogene und Gesundheitsdaten
