# Evaluation: regelbasierte Planung vs. MILP-Optimierung

**Versuchsaufbau:** 15 Instanzen (5 Seeds × 3 Personaldecken) × 3 Ausfallszenarien ×
4 Verfahrensvarianten = **180 Pläne**
**Station:** Innere Medizin / Kardiologie, 30 Betten, 28 Planungstage, 28 Tage Historie
**Reproduktion:** `python campaign.py` (13–18 Min.), Auswertung `python campaign.py --report`
**Rohdaten:** `evaluation_results.csv` (180 Zeilen, eine je Plan)

Alle Zahlen sind **gemessene Ergebnisse des Prototyps**. Was daraus für den Business Impact
folgt und was nicht, steht in Abschnitt 6.

---

## 1. Warum eine Kampagne und nicht eine Instanz

Die erste Messung lief auf genau einem Datensatz und ergab einen Gleichstand: beide
Verfahren erreichten 100 % Besetzungsquote ohne Regelverstöße. Daraus lässt sich nichts
schließen — weder dass die Optimierung nichts bringt, noch dass sie etwas bringt. Eine
einzelne Instanz kann zu leicht sein.

Die Kampagne variiert deshalb zwei Größen unabhängig voneinander:

| Faktor | Werte | Wirkung |
|---|---|---|
| **Seed** | 5 verschiedene | andere Belegung, andere Belegschaft, andere Ausfälle |
| **Personaldecke** (`staffing_factor`) | 1,00 / 0,90 / 0,80 | Belegschaft relativ zum rechnerischen Bruttobedarf (Ø 22 / 20 / 18 Köpfe) |

Die Personaldecke ist die wichtigere Stellschraube: Sie steuert, ob die Aufgabe überhaupt
lösbar ist. 1,00 entspricht bedarfsgerechter Besetzung nach der Bruttobedarfsrechnung
(siehe `DATENKONZEPT.md`, Abschnitt 3.5); 0,80 bildet eine Station ab, die zwanzig Prozent
unter ihrem rechnerischen Bedarf arbeitet — in der Pflege keine exotische Annahme.

Verglichen werden vier Varianten: beide Verfahren jeweils als vollständige Neuplanung und
als reaktive Umplanung (bestehender Plan als Ausgangspunkt).

---

## 2. Ergebnisse nach Personaldecke

Mittelwerte über 5 Seeds × 3 Szenarien (15 Pläne je Zelle), ± Standardabweichung.

### Bedarfsgerechte Besetzung (100 %, Ø 22 Köpfe)

| Kennzahl | Greedy | Greedy reaktiv | MILP | MILP reaktiv |
|---|---|---|---|---|
| Besetzungsquote | 100,0 % | 100,0 % | 100,0 % | 100,0 % |
| Untergrenzenverstöße | 0,00 | 0,00 | 0,00 | 0,00 |
| harte Regelverstöße | 0,00 | 0,00 | 0,00 | 0,00 |
| weiche Abweichungen | 16,8 ± 0,9 | 16,4 ± 1,2 | **0,0 ± 0,0** | 1,0 ± 0,8 |
| Streuung Auslastung | 0,065 ± 0,017 | 0,076 ± 0,026 | **0,015 ± 0,004** | 0,039 ± 0,021 |
| Planstabilität | 63,2 % | 92,2 % | 48,7 % | **94,9 %** |
| Planungszeit | 0,44 s | 0,37 s | 7,58 s | 0,27 s |

### Knappe Besetzung (90 %, Ø 20 Köpfe)

| Kennzahl | Greedy | Greedy reaktiv | MILP | MILP reaktiv |
|---|---|---|---|---|
| Besetzungsquote | 99,6 % | 99,4 % | **100,0 %** | **100,0 %** |
| Untergrenzenverstöße | 0,53 ± 0,74 | 0,80 ± 0,86 | **0,00** | **0,00** |
| harte Regelverstöße | 0,20 ± 0,41 | 0,53 ± 0,74 | **0,00** | **0,00** |
| weiche Abweichungen | 15,1 ± 1,8 | 15,3 ± 2,0 | **0,7 ± 1,0** | 1,9 ± 1,9 |
| Streuung Auslastung | 0,060 ± 0,037 | 0,066 ± 0,032 | **0,016 ± 0,003** | 0,041 ± 0,022 |
| Planstabilität | 67,7 % | 91,9 % | 49,2 % | **94,4 %** |
| Planungszeit | 0,40 s | 0,33 s | 14,14 s | 0,27 s |

### Unterbesetzt (80 %, Ø 18 Köpfe)

| Kennzahl | Greedy | Greedy reaktiv | MILP | MILP reaktiv |
|---|---|---|---|---|
| Besetzungsquote | 95,2 % | 95,5 % | **99,9 %** | **99,9 %** |
| Untergrenzenverstöße | 4,53 ± 1,96 | 4,27 ± 2,19 | **0,00** | **0,00** |
| harte Regelverstöße | 1,27 ± 1,10 | 1,40 ± 1,18 | **0,07 ± 0,26** | 0,07 ± 0,26 |
| weiche Abweichungen | 14,1 ± 2,5 | 14,6 ± 2,1 | **3,3 ± 1,0** | 4,6 ± 1,5 |
| Streuung Auslastung | 0,073 ± 0,023 | 0,083 ± 0,025 | **0,062 ± 0,036** | 0,077 ± 0,036 |
| Planstabilität | 70,9 % | 91,3 % | 53,6 % | **93,2 %** |
| Planungszeit | 0,35 s | 0,30 s | 14,95 ± 10,11 s | 0,56 s |

### Anteil vollständig regelkonformer Pläne

(keine harten Regelverstöße **und** keine Untergrenzenverstöße)

| Verfahren | 80 % | 90 % | 100 % |
|---|---|---|---|
| Greedy | **0 %** | 60 % | 100 % |
| Greedy reaktiv | **0 %** | 40 % | 100 % |
| MILP | **93 %** | 100 % | 100 % |
| MILP reaktiv | **93 %** | 100 % | 100 % |

---

## 3. Was die Kampagne beantwortet

**Der Gleichstand aus der Einzelmessung war instanzabhängig.** Bei bedarfsgerechter
Besetzung erreichen beide Verfahren die Sollbesetzung ohne Regelverstöße — die erste
Messung war also nicht falsch, aber nicht verallgemeinerbar. Sobald die Personaldecke
sinkt, trennen sich die Verfahren deutlich.

**Unter Knappheit sichert nur die Optimierung die gesetzliche Untergrenze.** Bei 80 %
Personaldecke unterschreitet die Heuristik die Pflegepersonaluntergrenze im Mittel 4,5-mal
je Plan und lässt insgesamt 106 Dienste unbesetzt; die Optimierung kommt auf null
Untergrenzenverstöße und 2 unbesetzte Dienste über alle 15 Pläne hinweg. **Kein einziger
Greedy-Plan bei 80 % war vollständig regelkonform, 93 % der MILP-Pläne waren es.** Das ist
das betriebswirtschaftlich relevanteste Ergebnis: Der Mehrwert der Optimierung entsteht
nicht im Normalbetrieb, sondern genau dort, wo es eng wird.

**Die Verteilungswirkung ist durchgängig und robust.** Die Streuung der individuellen
Auslastung sinkt bei bedarfsgerechter Besetzung von 0,065 auf 0,015 — ein Faktor von rund
vier, bei kleiner Standardabweichung über die Seeds. Die durchschnittlich 16,8
Überschreitungen der Wochenend- und Nachtdienst-Richtwerte der Heuristik gehen auf 0
zurück. Beides bei identischer Besetzungsquote: Die Heuristik entscheidet lokal optimal
und erzeugt dadurch systematisch Ungleichverteilung.

**Die reaktive Umplanung ist der größte Einzeleffekt.** Eine vollständige Neuplanung nach
Ausfällen erhält nur rund die Hälfte des Plans (MILP 48,7–53,6 %, Greedy 63,2–70,9 %). Die
reaktive Variante hält 93–95 % und rechnet in 0,37 s im Median (Maximum 2,45 s), bei
unveränderter Besetzungsquote und ohne zusätzliche Regelverstöße. Für die Mitarbeitenden
ist das der Unterschied zwischen „einige Dienste ändern sich" und „der Monat wird neu
gemacht".

**Der Preis der Stabilität ist messbar.** Die reaktive Variante erkauft sich die
Planstabilität mit schlechterer Lastverteilung (Streuung 0,039 statt 0,015 bei 100 %
Decke) und einzelnen weichen Abweichungen. Das ist kein Mangel, sondern der Zielkonflikt
selbst — der Prototyp macht ihn quantifizierbar, statt ihn zu verstecken.

**Rechenzeit ist kein limitierender Faktor.** Die Optimierung braucht 7,6 s bei
bedarfsgerechter und knapp 15 s bei knapper Besetzung; in 13 % der Läufe griff das
Zeitlimit von 30 s, ohne dass die Ergebnisqualität erkennbar litt. Die Umplanung liegt
unter einer Sekunde. Beides ist für eine Stationsleitung unproblematisch.

---

## 4. Was die Kampagne **nicht** beantwortet

**Ein einziger MILP-Plan verletzt eine harte Regel** (Seed 31415, 80 % Decke, Szenario S2:
ein Qualifikationsverstoß, 2 offene Dienste). Das ist kein Modellfehler: Unter extremer
Knappheit plus Ausfallwelle ist die Instanz nicht vollständig lösbar, und das Modell
verletzt bewusst die am geringsten gewichtete Vorgabe, statt gar keinen Plan zu liefern.
Genau dieses Verhalten ist beabsichtigt — es gibt aber eine Grenze, jenseits derer auch
Optimierung nur noch verwaltet, was fehlt.

**Die Heuristik ist keine echte Excel-Planung.** Sie ist eine programmierte Regelheuristik:
konsistenter, schneller und ermüdungsfrei. Der Unterschied zu manueller Planung dürfte
größer sein als hier gemessen — belegen lässt sich das mit diesem Aufbau nicht.

**Fünf Seeds sind wenig.** Die Streuungen sind bei den Kernaussagen klein genug, um sie zu
tragen (Untergrenzenverstöße bei 80 %: Greedy 4,53 ± 1,96 gegen MILP 0,00 ± 0,00), aber
für inferenzstatistische Aussagen wäre eine größere Stichprobe nötig. Ein Signifikanztest
wird hier bewusst nicht gerechnet.

**Die Gewichte der Zielfunktion sind gesetzt, nicht hergeleitet.** Wie stark Unterbesetzung
gegen Lastverteilung gegen Wunscherfüllung zählt, ist eine Managemententscheidung. Andere
Gewichte liefern andere Pläne. Eine Sensitivitätsanalyse dazu steht aus.

**Alle Daten sind synthetisch.** Die absolute Höhe der Kennzahlen ist nicht auf eine
konkrete Station übertragbar. Der Vergleich zweier Verfahren auf identischer Datenbasis
bleibt gültig.

---

## 5. Methodenwahl

Machine Learning wurde geprüft und verworfen: Es gibt keine zu lernende Zielvariable und
keine historischen Planentscheidungen als Trainingsdaten. Das Problem ist eine Zuordnung
unter harten Nebenbedingungen mit mehreren konkurrierenden Zielen — dafür sind
mathematische Optimierung und Constraint Programming die einschlägigen Verfahren
(Burke et al. 2004; Van den Bergh et al. 2013). Umgesetzt ist ein MILP mit 2.338 Variablen
und 4.066 Nebenbedingungen, gelöst mit HiGHS über `scipy.optimize.milp`; ein CP-SAT-Modell
wäre eine gleichwertige Alternative.

Rechtliche und vertragliche Grenzen sind harte Nebenbedingungen. Unterbesetzung,
Untergrenzenverstöße, Lastverteilung, Dienstwünsche sowie Wochenend- und
Nachtdienstverteilung gehen gewichtet in die Zielfunktion ein. Alle Besetzungsziele sind
weich modelliert, damit das Modell auch bei unlösbarer Instanz einen Plan mit
ausgewiesenen Lücken liefert statt gar keinen.

**Beide Verfahren werden von derselben, verfahrensunabhängigen Funktion `evaluate()`
bewertet.** Ein Verfahren darf seine eigene Regelkonformität nicht selbst behaupten.

---

## 6. Business Impact

**Gemessen** (gilt für diese 15 Instanzen):

- Bei knapper Personaldecke sichert die Optimierung die gesetzliche Mindestbesetzung, die
  Heuristik nicht: 0 gegen 4,5 Untergrenzenverstöße je Plan bei 80 % Decke; 93 % gegen 0 %
  vollständig regelkonforme Pläne.
- Gleichmäßigere Belastung bei identischer Besetzung: Streuung der Auslastung um Faktor 4
  geringer, alle Wochenend- und Nachtdienst-Richtwerte eingehalten.
- Reaktion auf Ausfälle: 93–95 % Planstabilität statt 49–71 %, Umplanung unter einer
  Sekunde.

**Nicht gemessen, nur plausibel** — in der Hausarbeit als Schätzung zu kennzeichnen:
Reduktion des manuellen Planungsaufwands, Wirkung gleichmäßigerer Belastung auf
Zufriedenheit und Fluktuation, wirtschaftliche Effekte durch weniger Überstunden oder
vermiedene Bettensperrungen. Solche Aussagen erfordern eine Erhebung im Betrieb.

Zwei Punkte verdienen betriebswirtschaftlich besondere Aufmerksamkeit:

**Untergrenzenverstöße sind kein Qualitätsdetail, sondern ein Rechtsrisiko.** Krankenhäuser
weisen die Einhaltung der Pflegepersonaluntergrenzen quartalsweise gegenüber dem InEK nach.
Ein Planungsverfahren, das bei knapper Besetzung systematisch darunter gerät, erzeugt einen
Nachweis- und Sanktionsdruck, der mit der Alternative — Betten sperren — teuer wird.

**Planstabilität wirkt dort, wo die Belastung entsteht.** Jede kurzfristige Änderung
bedeutet für die betroffene Person eine Umstellung privater Planung. Ein Verfahren, das bei
gleicher Versorgungsqualität mit einem Bruchteil der Änderungen auskommt, adressiert genau
den Punkt, den die reine Besetzungsquote nicht sichtbar macht.

---

## 7. Einordnung in die Leitfrage

„Wie kann eine KI-gestützte Planungsempfehlung die Erstellung und kurzfristige Anpassung
eines Schichtplans gegenüber einer regelbasierten Excel-Planung unterstützen?"

Nach dieser Kampagne lässt sich die Antwort präzisieren:

1. **Bei der Erstellung** liegt der Mehrwert nicht in der Machbarkeit, sondern in
   Regelkonformität unter Knappheit und in der Verteilungsgerechtigkeit. Ist genug Personal
   da, tut es auch eine Regelheuristik.
2. **Bei der kurzfristigen Anpassung** liegt der Mehrwert in der Planstabilität — und zwar
   nur, wenn Stabilität ausdrücklich als Ziel modelliert wird. Eine bloße Neuoptimierung
   nach dem Ausfall ist für die Mitarbeitenden schlechter als die Heuristik.

Punkt 2 ist der eigentliche methodische Befund der Arbeit: Nicht „Optimierung schlägt
Heuristik", sondern „Optimierung schlägt Heuristik dann, wenn die richtigen Ziele im Modell
stehen".

---

## Quellen

- Burke, E. K., De Causmaecker, P., Vanden Berghe, G., & Van Landeghem, H. (2004). The State of the Art of Nurse Rostering. *Journal of Scheduling*, 7(6), 441–499.
- Van den Bergh, J., Beliën, J., De Bruecker, P., Demeulemeester, E., & De Boeck, L. (2013). Personnel scheduling: A literature review. *European Journal of Operational Research*, 226(3), 367–385.
- Wickert, T. I., Smet, P., & Vanden Berghe, G. The nurse rerostering problem: Strategies for reconstructing disrupted schedules. *Computers & Operations Research*.
- HiGHS über `scipy.optimize.milp` — <https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html>

Rechtsgrundlagen, Datenherkunft und Annahmenregister: siehe `DATENKONZEPT.md`.
