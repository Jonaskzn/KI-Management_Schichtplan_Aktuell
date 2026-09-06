# Datenkonzept: Synthetischer Datensatz für die KI-gestützte Schichtplanung

**Projekt:** KI-gestützte Personal- und Schichtplanung in der Pflege
**Fallstudie:** Normalstation „Innere Medizin und Kardiologie", 30 Betten
**Datensatz-Version:** 2.0.0 · Seed 20261130 · erzeugt mit `generate_dataset.py`
**Auslieferung:** eine einzelne Datei `schichtplan_datensatz.csv` (1.232 Zeilen × 94 Spalten)
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

---

## 4. Die Einzeltabelle: Aufbau und Begründung

`schichtplan_datensatz.csv` — UTF-8, Komma-getrennt, ISO-Datumsformat, 1.232 Zeilen ×
94 Spalten, rund 520 KB. **Analysekorn: eine Zeile je Mitarbeitendem und Kalendertag**
(22 Mitarbeitende × 56 Tage = 28 Tage Historie + 28 Tage Planung).

### 4.1 Warum dieses Korn und nicht ein anderes

Eine einzelne Tabelle zwingt zu einer Entscheidung über das Korn, und die ist nicht beliebig:

| Kandidat | Zeilen | Bewertung |
|---|---|---|
| Tag × Schicht | 168 | Bedarf sauber, aber Mitarbeitende passen nicht hinein — die Ressourcenseite ginge verloren |
| Mitarbeitender × Tag × Schicht | 3.696 | dreifach redundant, ohne zusätzlichen Informationsgehalt: eine Person arbeitet höchstens einen Dienst pro Tag |
| **Mitarbeitender × Tag** | **1.232** | die Planungsentscheidung selbst („welchen Dienst bekommt Person *i* am Tag *d*?") ist genau eine Zeile; Bedarf je Schicht passt als drei Spaltengruppen daneben |

Das gewählte Korn ist damit identisch mit dem **Entscheidungsraum des Planungsproblems**: Der
gesuchte Dienstplan ist genau eine zusätzliche Spalte (`assigned_shift`) zu dieser Tabelle.
Das ist auch der Grund, warum die Excel-Baseline damit unmittelbar arbeiten kann — die Datei
ist bereits die leere Planmatrix.

### 4.2 Der Preis: bewusste Denormalisierung

Mitarbeiterstammdaten wiederholen sich in 56 Zeilen, Tages- und Bedarfsdaten in 22, Stations-
und Regelspalten in allen 1.232. Das verletzt die dritte Normalform. Das ist ein realer
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

| Szenario | Beschreibung | Spalten | Realisiert |
|---|---|---|---|
| **S0** | Referenz ohne kurzfristige Ausfälle; nur geplante Abwesenheiten | keine (beide Ausfallspalten 0) | 0 Ereignisse |
| **S1** | Regelbetrieb: unabhängig über den Horizont verteilte Einzelausfälle, Rate 4 % der Personentage | `absence_s1`, `absence_s1_notice_h` | 23 Ereignisse (3,7 %) |
| **S2** | Ausfallwelle: gleiche Grundrate, im Fenster 14.–19.12. verdreifacht (korrelierte Ausfälle) | `absence_s2`, `absence_s2_notice_h` | 32 Ereignisse (5,2 %) |

Die Grundrate von 4 % ist aus dem TK-Wert von 28 AU-Tagen je Jahr in der Krankenpflege
abgeleitet (≈ 7,7 % der Kalendertage), abzüglich des Anteils, der auf Langzeitfälle entfällt
und im Datensatz bereits als `LANGZEITABWESENHEIT` **planbar** hinterlegt ist. Die Aufteilung
zwischen Langzeit- und Kurzzeitanteil ist eine Annahme (A7).

Das Feld `absence_s*_notice_h` (2 bis 24 Stunden Vorlauf) ist die entscheidende Größe für die zweite
Hälfte der Leitfrage: Ein Ausfall, der 24 h vorher bekannt ist, lässt Umplanung zu; einer mit
2 h Vorlauf zwingt zu Holen-aus-dem-Frei oder Unterbesetzung. Die Re-Rostering-Literatur
(Wickert et al.) modelliert Störungen genau so und misst den Erfolg an der Nähe zum
ursprünglichen Plan — das entspricht dem KPI „Planstabilität" der Projektvorgabe.

Das Szenariodesign trennt sauber, was die Arbeit trennen muss: **S0 misst Planerstellung,
S1/S2 messen Anpassungsfähigkeit.** Beide Verfahren erhalten identische Ereignisdateien.

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
| A7 | Anteil kurzfristiger an gesamten Ausfällen | Grundrate 4 % der Personentage | AU-Tage insgesamt sind belegt, die Aufteilung Kurz-/Langzeit nicht | **hoch** — Kerngröße der Szenarien |
| A8 | Zwei-Personen-Nachtdienst | Minimum 2 | die Untergrenze ergäbe bei 21 Patienten rechnerisch 1 Kraft; ein Alleindienst ist auf 30 Betten praktisch nicht vertretbar (Pausenablösung, § 4 ArbZG) | mittel |
| A9 | Mindestbesetzung Tagdienst | 3 ab 15 Patienten | Pausenablösung und Vertretbarkeit | mittel |
| A10 | Max. 5 Dienste in Folge, ≥ 2 freie Tage am Stück, max. 2 Wochenenden / 4 Wochen, max. 8 Nachtdienste / 4 Wochen | – | gestützt auf § 6 Abs. 1 ArbZG (arbeitswissenschaftliche Erkenntnisse), aber nicht beziffert im Gesetz | mittel |
| A11 | Leitungsfreistellung 50 %, Leitung nur im Frühdienst | – | übliche Praxis; senkt die planbare Kapazität | niedrig |
| A12 | Historie per Greedy-Heuristik erzeugt | – | die Historie ist Eingabe, nicht Evaluationsgegenstand; sie muss nur regelkonform und plausibel sein | niedrig |
| A13 | Ausfallzeiten für den Bruttobedarf | 30 Urlaub + 20 AU + 5 Fortbildung von 251 Arbeitstagen | Urlaub und AU belegt, Fortbildungstage und Jahresarbeitstage gesetzt | mittel |

Die Annahmen mit hoher Sensitivität (A3, A7) gehören in die Limitationen der Hausarbeit und
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
