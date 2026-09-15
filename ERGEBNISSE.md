# Evaluation: regelbasierte Planung vs. MILP-Optimierung

**Versuchsaufbau:** 15 Instanzen (5 Seeds × 3 Personaldecken) × 3 Ausfallszenarien ×
4 Verfahrensvarianten = **180 Pläne**
**Station:** Innere Medizin / Kardiologie, 30 Betten, 28 Planungstage, 28 Tage Historie
**Reproduktion:** `python campaign.py` (ca. 14 Min.), Auswertung `python campaign.py --report`
**Rohdaten:** `evaluation_results.csv` (180 Zeilen, eine je Plan)

Alle Zahlen sind **gemessene Ergebnisse des Prototyps**. Was daraus für den Business Impact
folgt und was nicht, steht in Abschnitt 7.

---

## 1. Warum eine Kampagne und nicht eine Instanz

Die erste Messung lief auf genau einem Datensatz und ergab einen Gleichstand: beide
Verfahren erreichten 100 % Besetzungsquote ohne Regelverstöße. Daraus lässt sich nichts
schließen — weder dass die Optimierung nichts bringt, noch dass sie etwas bringt. Eine
einzelne Instanz kann schlicht zu leicht sein.

Die Kampagne variiert deshalb drei Größen unabhängig voneinander:

| Faktor | Werte | Wirkung |
|---|---|---|
| **Seed** | 5 verschiedene | andere Belegung, andere Belegschaft, andere Ausfälle |
| **Personaldecke** (`staffing_factor`) | 1,00 / 0,90 / 0,80 | Belegschaft relativ zum rechnerischen Bruttobedarf (Ø 22 / 20 / 18 Köpfe) |
| **Ausfallszenario** | S0 / S1 / S2 | keine / verteilte Einzelausfälle / Ausfallwelle in Episoden |

Die Personaldecke ist die wichtigere der beiden quantitativen Stellschrauben: Sie steuert,
ob die Aufgabe überhaupt lösbar ist. 1,00 entspricht bedarfsgerechter Besetzung nach der
Bruttobedarfsrechnung (siehe `DATENKONZEPT.md`, Abschnitt 3.5); 0,80 bildet eine Station
ab, die zwanzig Prozent unter ihrem rechnerischen Bedarf arbeitet — in der Pflege keine
exotische Annahme.

Verglichen werden vier Varianten: beide Verfahren jeweils als vollständige Neuplanung und
als reaktive Umplanung (bestehender Plan als Ausgangspunkt).

---

## 2. Ergebnisse nach Personaldecke

Mittelwerte über 5 Seeds × 3 Szenarien (15 Pläne je Zelle), ± Standardabweichung.

### Bedarfsgerechte Besetzung (100 %, Ø 22 Köpfe)

| Kennzahl | Greedy | Greedy reaktiv | MILP | MILP reaktiv |
|---|---|---|---|---|
| Besetzungsquote | 99,9 % | 100,0 % | 100,0 % | 100,0 % |
| Untergrenzenverstöße | 0,07 ± 0,26 | 0,00 | **0,00** | **0,00** |
| harte Regelverstöße | 0,07 ± 0,26 | 0,07 ± 0,26 | **0,00** | **0,00** |
| weiche Abweichungen | 16,0 ± 1,8 | 16,5 ± 1,0 | **0,0 ± 0,0** | 1,2 ± 1,2 |
| Streuung Auslastung | 0,064 ± 0,016 | 0,077 ± 0,020 | **0,015 ± 0,004** | 0,057 ± 0,038 |
| Planstabilität | 70,9 % | 94,2 % | 48,9 % | **95,4 %** |
| Planungszeit | 0,50 s | 0,42 s | 7,42 s | 0,30 s |

### Knappe Besetzung (90 %, Ø 20 Köpfe)

| Kennzahl | Greedy | Greedy reaktiv | MILP | MILP reaktiv |
|---|---|---|---|---|
| Besetzungsquote | 99,7 % | 99,3 % | **100,0 %** | **100,0 %** |
| Untergrenzenverstöße | 0,33 ± 0,62 | 0,67 ± 0,72 | **0,00** | **0,00** |
| harte Regelverstöße | 0,33 ± 0,49 | 0,80 ± 0,68 | **0,00** | **0,00** |
| weiche Abweichungen | 15,3 ± 1,5 | 15,1 ± 2,0 | **0,5 ± 0,7** | 2,1 ± 1,9 |
| Streuung Auslastung | 0,065 ± 0,036 | 0,073 ± 0,038 | **0,018 ± 0,006** | 0,045 ± 0,026 |
| Planstabilität | 73,2 % | 92,4 % | 48,8 % | **95,3 %** |
| Planungszeit | 0,44 s | 0,38 s | 12,53 s | 0,45 s |

### Unterbesetzt (80 %, Ø 18 Köpfe)

| Kennzahl | Greedy | Greedy reaktiv | MILP | MILP reaktiv |
|---|---|---|---|---|
| Besetzungsquote | 95,4 % | 95,3 % | **100,0 %** | **100,0 %** |
| Untergrenzenverstöße | 4,40 ± 1,88 | 4,47 ± 2,10 | **0,00** | **0,00** |
| harte Regelverstöße | 1,07 ± 1,33 | 1,40 ± 1,45 | **0,00** | **0,00** |
| weiche Abweichungen | 14,1 ± 1,8 | 14,4 ± 2,0 | **3,2 ± 0,9** | 4,9 ± 1,9 |
| Streuung Auslastung | 0,083 ± 0,028 | 0,087 ± 0,028 | **0,059 ± 0,035** | 0,078 ± 0,037 |
| Planstabilität | 78,0 % | 92,2 % | 53,3 % | **93,3 %** |
| Planungszeit | 0,39 s | 0,33 s | 16,48 ± 10,04 s | 0,60 s |

### Anteil vollständig regelkonformer Pläne

(keine harten Regelverstöße **und** keine Untergrenzenverstöße)

| Verfahren | 80 % | 90 % | 100 % |
|---|---|---|---|
| Greedy | **0 %** | 67 % | 93 % |
| Greedy reaktiv | **0 %** | 33 % | 93 % |
| MILP | **100 %** | 100 % | 100 % |
| MILP reaktiv | **100 %** | 100 % | 100 % |

Über alle 90 MILP-Pläne hinweg gibt es **keinen einzigen** harten Regelverstoß und keine
einzige Untergrenzenunterschreitung. Die Heuristik lässt bei 80 % Decke insgesamt
102 Dienste unbesetzt und unterschreitet die Untergrenze 66-mal; die Optimierung kommt auf
einen einzigen unbesetzten Dienst über alle 15 Pläne und null Untergrenzenverstöße.

---

## 3. Ergebnisse nach Ausfallszenario

Mittelwerte über alle 15 Instanzen. S1 und S2 tragen **dasselbe Ausfallvolumen** (Ø 17,0
gegen 18,1 Ausfalltage je Instanz, Abweichung 6,7 %) und unterscheiden sich nur in der
**Struktur**: S1 verteilt Einzeltage über 28 Tage und im Mittel 11 Personen, S2 bündelt
sie in rund 7 mehrtägigen Episoden von 2–4 Tagen bei im Mittel 6 Personen, überwiegend im
Fenster 14.–19.12. Der Unterschied zwischen beiden ist damit ein reiner Strukturunterschied
und nicht einer des Umfangs (siehe `DATENKONZEPT.md`, Abschnitt 5).

| Kennzahl (MILP reaktiv) | S0 | S1 | S2 |
|---|---|---|---|
| Spanne der Auslastung | 0,108 | 0,260 | **0,374** |
| Planstabilität | 100,0 % | 92,9 % | **91,1 %** |
| geänderte Zuweisungen | 0 | 21,1 | **26,7** |
| Planungszeit | 0,18 s | 0,42 s | 0,76 s |

| Kennzahl (Greedy reaktiv) | S0 | S1 | S2 |
|---|---|---|---|
| Besetzungsquote | 98,5 % | 98,2 % | **97,8 %** |
| Untergrenzenverstöße | 1,60 | 1,73 | 1,80 |
| harte Regelverstöße | 0,33 | 0,60 | **1,33** |
| offene Dienste | 2,2 | 2,8 | **3,9** |

**S2 ist konsistent die härtere Instanz.** Die Richtung ist über alle drei Personaldecken
hinweg stabil — bei 80 %, 90 % und 100 % Decke liegt die Spanne der Auslastung unter S2
jeweils über der unter S1 (0,357→0,430 / 0,199→0,269 / 0,224→0,422), die Planstabilität
jeweils darunter. Das ist genau der Effekt, den das Episodenmodell abbilden soll: Wenn
dieselbe Zahl an Ausfalltagen auf wenige Personen und wenige Tage zusammenfällt, fehlen
gleichzeitig mehrere Personen, und die verbleibende Mannschaft muss die Lücke in einem
engen Zeitfenster auffangen. Bei über den Monat verteilten Einzeltagen kann die Last über
28 Tage ausgeglichen werden; in der Welle geht das nicht.

**Die Heuristik ist nicht monoton.** Bei den Untergrenzenverstößen der Baseline liegt S1
mit 1,33 knapp *unter* S0 mit 1,60, obwohl S1 zusätzliche Ausfälle enthält. Auf
Instanzebene zeigt sich, dass die Ordnung S0 < S1 < S2 nicht durchgängig gilt (z. B. Seed
20260906 bei 80 % Decke: 4 / 1 / 6). Der Grund ist die Konstruktion der Heuristik: Sie
wählt je Dienst die momentan am wenigsten ausgelastete geeignete Person. Fällt jemand aus,
ändert sich die Reihenfolge — und gelegentlich zum Besseren. Eine greedy Auswahl kann
durch eine Verschlechterung der Ausgangslage zufällig einen besseren Plan finden. Für den
Verfahrensvergleich ist das kein Störeffekt, sondern selbst ein Befund: Die Baseline
reagiert auf Störungen unsystematisch, die Optimierung nicht (MILP: 0,00 Verstöße in
allen drei Szenarien).

---

## 4. Was die Kampagne beantwortet

**Der Gleichstand aus der Einzelmessung war instanzabhängig.** Bei bedarfsgerechter
Besetzung erreichen beide Verfahren nahezu die Sollbesetzung — die erste Messung war also
nicht falsch, aber nicht verallgemeinerbar. Sobald die Personaldecke sinkt, trennen sich
die Verfahren deutlich.

**Unter Knappheit sichert nur die Optimierung die gesetzliche Untergrenze.** Bei 80 %
Personaldecke unterschreitet die Heuristik die Pflegepersonaluntergrenze im Mittel 4,4-mal
je Plan und lässt insgesamt 102 Dienste unbesetzt; die Optimierung kommt auf null
Untergrenzenverstöße und einen unbesetzten Dienst über alle 15 Pläne hinweg. **Kein
einziger Greedy-Plan bei 80 % war vollständig regelkonform, 100 % der MILP-Pläne waren
es.** Das ist das betriebswirtschaftlich relevanteste Ergebnis: Der Mehrwert der
Optimierung entsteht nicht im Normalbetrieb, sondern genau dort, wo es eng wird.

**Die Verteilungswirkung ist durchgängig und robust.** Die Streuung der individuellen
Auslastung sinkt bei bedarfsgerechter Besetzung von 0,064 auf 0,015 — ein Faktor von rund
vier, bei kleiner Standardabweichung über die Seeds. Die Spanne zwischen der am geringsten
und der am stärksten ausgelasteten Person geht von 29 auf 7 Prozentpunkte zurück. Die
durchschnittlich 16,0 Überschreitungen der Wochenend- und Nachtdienst-Richtwerte der
Heuristik gehen auf 0 zurück. Beides bei praktisch identischer Besetzungsquote: Die
Heuristik entscheidet lokal optimal und erzeugt dadurch systematisch Ungleichverteilung.

**Die reaktive Umplanung ist der größte Einzeleffekt.** Eine vollständige Neuplanung nach
Ausfällen erhält nur rund die Hälfte des Plans (MILP 48,8–53,3 %, Greedy 70,9–78,0 %) und
ändert im Mittel 279 Zuweisungen. Die reaktive Variante hält 93–95 % Planstabilität bei
Ø 24 Änderungen und rechnet in 0,21 s im Median (Maximum 3,15 s), bei unveränderter
Besetzungsquote und ohne zusätzliche Regelverstöße. Für die Mitarbeitenden ist das der
Unterschied zwischen „einige Dienste ändern sich" und „der Monat wird neu gemacht".

**Der Preis der Stabilität ist messbar.** Die reaktive Variante erkauft sich die
Planstabilität mit schlechterer Lastverteilung (Streuung 0,057 statt 0,015 bei 100 %
Decke) und einzelnen weichen Abweichungen (1,2 statt 0,0). Das ist kein Mangel, sondern
der Zielkonflikt selbst — der Prototyp macht ihn quantifizierbar, statt ihn zu verstecken.

**Rechenzeit ist kein limitierender Faktor.** Die Optimierung braucht 7,4 s bei
bedarfsgerechter und 16,5 s bei knapper Besetzung; in 6 von 90 Läufen (7 %) griff das
Zeitlimit von 30 s, ohne dass die Ergebnisqualität erkennbar litt — auch diese Pläne sind
vollständig regelkonform. Die Umplanung liegt im Median unter einer Viertelsekunde. Beides
ist für eine Stationsleitung unproblematisch.

---

## 5. Was die Kampagne **nicht** beantwortet

**Die Heuristik ist keine echte Excel-Planung.** Sie ist eine programmierte Regelheuristik:
konsistenter, schneller und ermüdungsfrei. Der Unterschied zu manueller Planung dürfte
größer sein als hier gemessen — belegen lässt sich das mit diesem Aufbau nicht.

**Fünf Seeds sind wenig.** Die Streuungen sind bei den Kernaussagen klein genug, um sie zu
tragen (Untergrenzenverstöße bei 80 %: Greedy 4,40 ± 1,88 gegen MILP 0,00 ± 0,00), aber
für inferenzstatistische Aussagen wäre eine größere Stichprobe nötig. Ein Signifikanztest
wird hier bewusst nicht gerechnet.

**Die Gewichte der Zielfunktion sind gesetzt, nicht hergeleitet.** Wie stark Unterbesetzung
gegen Lastverteilung gegen Wunscherfüllung zählt, ist eine Managemententscheidung. Andere
Gewichte liefern andere Pläne. Eine Sensitivitätsanalyse dazu steht aus.

**Der Restunterschied im Ausfallvolumen zwischen S1 und S2 beträgt 6,7 %.** Er ist klein
genug, um den beobachteten Effekt nicht zu erklären (die Spanne der Auslastung steigt um
44 %), aber die beiden Szenarien sind nicht exakt volumengleich. Eine exakte Angleichung
wäre nur um den Preis einer künstlichen Konstruktion zu haben.

**Die Obergrenze der Optimierung wurde in dieser Kampagne nicht erreicht.** Das MILP löst
alle 90 Instanzen vollständig regelkonform. Das heißt nicht, dass es das immer täte —
es heißt, dass der untersuchte Knappheitsbereich bis 80 % Personaldecke für das Modell
noch lösbar ist. Wo die Grenze liegt, jenseits derer auch Optimierung nur noch verwaltet,
was fehlt, ist mit diesem Aufbau offen.

**Alle Daten sind synthetisch.** Die absolute Höhe der Kennzahlen ist nicht auf eine
konkrete Station übertragbar. Der Vergleich zweier Verfahren auf identischer Datenbasis
bleibt gültig.

---

## 6. Methodenwahl

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

## 7. Business Impact

**Gemessen** (gilt für diese 15 Instanzen):

- Bei knapper Personaldecke sichert die Optimierung die gesetzliche Mindestbesetzung, die
  Heuristik nicht: 0 gegen 4,4 Untergrenzenverstöße je Plan bei 80 % Decke; 100 % gegen
  0 % vollständig regelkonforme Pläne.
- Gleichmäßigere Belastung bei identischer Besetzung: Streuung der Auslastung um Faktor 4
  geringer, Spanne von 29 auf 7 Prozentpunkte, alle Wochenend- und Nachtdienst-Richtwerte
  eingehalten.
- Reaktion auf Ausfälle: 93–95 % Planstabilität statt 49–78 %, Ø 24 statt 279 geänderte
  Zuweisungen, Umplanung im Median unter einer Viertelsekunde.
- Robustheit gegenüber der Ausfallstruktur: Unter der Ausfallwelle steigen bei der
  Heuristik die harten Regelverstöße von 0,60 auf 1,33 und die offenen Dienste von 2,8 auf
  3,9; die Optimierung bleibt in beiden Szenarien bei null.

**Nicht gemessen, nur plausibel** — in der Hausarbeit als Schätzung zu kennzeichnen:
Reduktion des manuellen Planungsaufwands, Wirkung gleichmäßigerer Belastung auf
Zufriedenheit und Fluktuation, wirtschaftliche Effekte durch weniger Überstunden oder
vermiedene Bettensperrungen. Solche Aussagen erfordern eine Erhebung im Betrieb.

Drei Punkte verdienen betriebswirtschaftlich besondere Aufmerksamkeit:

**Untergrenzenverstöße sind kein Qualitätsdetail, sondern ein Rechtsrisiko.** Krankenhäuser
weisen die Einhaltung der Pflegepersonaluntergrenzen quartalsweise gegenüber dem InEK nach.
Ein Planungsverfahren, das bei knapper Besetzung systematisch darunter gerät, erzeugt einen
Nachweis- und Sanktionsdruck, der mit der Alternative — Betten sperren — teuer wird.

**Planstabilität wirkt dort, wo die Belastung entsteht.** Jede kurzfristige Änderung
bedeutet für die betroffene Person eine Umstellung privater Planung. Ein Verfahren, das bei
gleicher Versorgungsqualität mit einem Bruchteil der Änderungen auskommt, adressiert genau
den Punkt, den die reine Besetzungsquote nicht sichtbar macht.

**Der Wert zeigt sich in der Störung, nicht im Normalbetrieb.** Die beiden Szenarien mit
identischem Ausfallvolumen, aber unterschiedlicher Struktur trennen die Verfahren stärker
als das Ausfallvolumen selbst. Eine Investitionsentscheidung sollte deshalb nicht am
Durchschnittsmonat bemessen werden, sondern an der Woche, in der mehrere Personen
gleichzeitig ausfallen.

---

## 8. Einordnung in die Leitfrage

„Wie kann eine KI-gestützte Planungsempfehlung die Erstellung und kurzfristige Anpassung
eines Schichtplans gegenüber einer regelbasierten Excel-Planung unterstützen?"

Nach dieser Kampagne lässt sich die Antwort präzisieren:

1. **Bei der Erstellung** liegt der Mehrwert nicht in der Machbarkeit, sondern in
   Regelkonformität unter Knappheit und in der Verteilungsgerechtigkeit. Ist genug Personal
   da, tut es auch eine Regelheuristik.
2. **Bei der kurzfristigen Anpassung** liegt der Mehrwert in der Planstabilität — und zwar
   nur, wenn Stabilität ausdrücklich als Ziel modelliert wird. Eine bloße Neuoptimierung
   nach dem Ausfall ist für die Mitarbeitenden schlechter als die Heuristik.
3. **Die Struktur der Ausfälle entscheidet mit.** Gleich viele Ausfalltage wirken sehr
   unterschiedlich, je nachdem ob sie verteilt oder gebündelt auftreten. Die Optimierung
   fängt beides ohne Regelverstoß auf, die Heuristik nicht.

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
