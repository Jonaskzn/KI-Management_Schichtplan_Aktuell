# Evaluation: regelbasierte Planung vs. MILP-Optimierung

**Versuchsaufbau:** 15 Instanzen (5 Seeds × 3 Personaldecken) × 3 Ausfallszenarien ×
4 Verfahrensvarianten = **180 Pläne**
**Station:** Innere Medizin / Kardiologie, 30 Betten, 28 Planungstage, 28 Tage Historie
**Reproduktion:** `python campaign.py` (ca. 15 Min.), Auswertung `python campaign.py --report`
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
| weiche Abweichungen | 15,7 ± 1,8 | 16,1 ± 1,0 | **0,0 ± 0,0** | 0,9 ± 1,0 |
| Streuung Auslastung | 0,069 ± 0,012 | 0,083 ± 0,017 | **0,014 ± 0,004** | 0,057 ± 0,039 |
| Planstabilität | 72,6 % | 94,5 % | 48,5 % | **95,3 %** |
| Planungszeit | 0,52 s | 0,43 s | 9,54 s | 0,30 s |

### Knappe Besetzung (90 %, Ø 20 Köpfe)

| Kennzahl | Greedy | Greedy reaktiv | MILP | MILP reaktiv |
|---|---|---|---|---|
| Besetzungsquote | 99,7 % | 99,5 % | **100,0 %** | **100,0 %** |
| Untergrenzenverstöße | 0,33 ± 0,62 | 0,47 ± 0,64 | **0,00** | **0,00** |
| harte Regelverstöße | 0,33 ± 0,49 | 0,73 ± 0,70 | **0,00** | **0,00** |
| weiche Abweichungen | 15,1 ± 1,4 | 14,9 ± 1,9 | **0,2 ± 0,4** | 1,7 ± 1,8 |
| Streuung Auslastung | 0,059 ± 0,037 | 0,069 ± 0,038 | **0,017 ± 0,007** | 0,044 ± 0,024 |
| Planstabilität | 78,3 % | 93,5 % | 49,9 % | **95,9 %** |
| Planungszeit | 0,45 s | 0,38 s | 12,93 s | 0,40 s |

### Unterbesetzt (80 %, Ø 18 Köpfe)

| Kennzahl | Greedy | Greedy reaktiv | MILP | MILP reaktiv |
|---|---|---|---|---|
| Besetzungsquote | 95,4 % | 95,3 % | **100,0 %** | **100,0 %** |
| Untergrenzenverstöße | 4,33 ± 1,95 | 4,60 ± 1,88 | **0,00** | **0,00** |
| harte Regelverstöße | 0,93 ± 1,39 | 1,20 ± 1,52 | **0,00** | **0,00** |
| weiche Abweichungen | 14,1 ± 1,8 | 14,3 ± 2,0 | **3,0 ± 1,4** | 4,9 ± 2,0 |
| Streuung Auslastung | 0,088 ± 0,022 | 0,094 ± 0,021 | **0,065 ± 0,035** | 0,086 ± 0,035 |
| Planstabilität | 78,8 % | 92,4 % | 51,4 % | **93,8 %** |
| Planungszeit | 0,39 s | 0,33 s | 16,26 ± 10,43 s | 0,59 s |

### Anteil vollständig regelkonformer Pläne

(keine harten Regelverstöße **und** keine Untergrenzenverstöße)

| Verfahren | 80 % | 90 % | 100 % |
|---|---|---|---|
| Greedy | **0 %** | 67 % | 93 % |
| Greedy reaktiv | **0 %** | 40 % | 93 % |
| MILP | **100 %** | 100 % | 100 % |
| MILP reaktiv | **100 %** | 100 % | 100 % |

Über alle 90 MILP-Pläne hinweg gibt es **keinen einzigen** harten Regelverstoß, keine
Untergrenzenunterschreitung und keinen unbesetzten Dienst. Die Heuristik lässt bei 80 %
Decke insgesamt 104 Dienste unbesetzt und unterschreitet die Untergrenze 65-mal.

---

## 3. Ergebnisse nach Ausfallszenario

### 3.1 Aufbau des Vergleichs

S1 und S2 sollen sich **nur in der Struktur** unterscheiden, nicht im Umfang: S1 verteilt
Einzeltage über den Monat, S2 bündelt dieselbe Menge in mehrtägigen Episoden innerhalb
eines Sechstagefensters. Nur dann ist eine Ergebnisdifferenz der Struktur zuzurechnen und
nicht der schlichten Menge an Ausfällen.

Die Kalibrierung gelingt **im Mittel**, aber nicht in jeder Ziehung: Über die 15 Instanzen
trägt S1 im Schnitt 15,7 und S2 17,8 Ausfalltage — ein Restunterschied von 13,6 %, der je
Instanz zwischen −3 und +7 Tagen schwankt. Dieser Rest ist groß genug, um Ergebnisse zu
verfälschen, und wird in Abschnitt 3.3 ausdrücklich kontrolliert.

| Kennzahl (reaktive Umplanung) | S0 | S1 | S2 |
|---|---|---|---|
| Spanne der Auslastung — Regelbasiert | 0,283 | 0,338 | **0,380** |
| Spanne der Auslastung — MILP | **0,115** | 0,277 | **0,376** |
| Planstabilität — Regelbasiert | 100 % | 90,7 % | 89,7 % |
| Planstabilität — MILP | 100 % | 93,7 % | 91,2 % |
| offene Dienste — Regelbasiert | 2,27 | 2,53 | **3,87** |
| harte Regelverstöße — Regelbasiert | 0,33 | 0,47 | **1,20** |

### 3.2 Der belastbare Befund: der Verteilungsvorteil der Optimierung verschwindet

Bei ungestörter Planung verteilt die Optimierung die Last dramatisch gleichmäßiger als die
Heuristik: Spanne 0,115 gegen 0,283, ein Faktor von 2,5. Unter verteilten Einzelausfällen
schrumpft der Vorsprung (0,277 gegen 0,338). **Unter der Ausfallwelle ist er vollständig
verschwunden: 0,376 gegen 0,380 — kein Unterschied mehr.**

Das ist das inhaltlich interessanteste Ergebnis der Kampagne, und es ist kein Mangel des
Verfahrens. Gleichverteilung setzt Spielraum voraus: Es muss jemanden geben, der die
Schicht übernehmen kann, ohne selbst an seine Grenze zu geraten. Fallen mehrere Personen
gleichzeitig und mehrtägig aus, ist dieser Spielraum weg. Die Optimierung kann dann nur
noch verteilen, was übrig ist — und das ist dieselbe knappe Menge, die auch die Heuristik
vorfindet. Der Mehrwert der Optimierung liegt hier weiterhin in der **Regelkonformität**
(null Verstöße gegen 1,20), nicht mehr in der **Verteilungsgerechtigkeit**.

### 3.3 Kontrolle für das Ausfallvolumen — und eine Korrektur

Weil S2 über die Instanzen im Mittel 13,6 % mehr Ausfalltage trägt, wurde jede
Szenariodifferenz zusätzlich auf der Teilmenge der **6 Instanzen** geprüft, in denen S2
**nicht** mehr Ausfalltage hat als S1:

| Differenz S2 − S1 (MILP reaktiv) | alle 15 Instanzen | volumenkontrolliert (6) |
|---|---|---|
| Spanne der Auslastung | +0,100 (13 von 15) | **+0,084 (6 von 6)** |
| Planstabilität | −2,55 Pp. (12 von 15) | −0,79 Pp. (4 von 6) |

**Der Verteilungseffekt ist ein echter Struktureffekt.** Er bleibt in der volumen­kontrollierten
Teilmenge nahezu unverändert bestehen und tritt dort in **allen sechs** Instanzen auf.

**Der Stabilitätseffekt ist es überwiegend nicht.** Kontrolliert man das Volumen, schrumpft
er von 2,55 auf 0,79 Prozentpunkte und tritt nur noch in vier von sechs Instanzen auf. Die
Korrelation zwischen Volumendifferenz und Stabilitätsdifferenz beträgt −0,51. Das ist
plausibel und folgt direkt aus der Definition: Planstabilität ist der Anteil unveränderter
Zuweisungen, und jeder Ausfalltag, der auf einen geplanten Dienst fällt, erzwingt eine
Änderung. **Planstabilität misst primär die Menge der Störung, nicht ihre Konzentration.**

Dasselbe gilt abgeschwächt für Regelverstöße und offene Dienste der Heuristik: In der
volumenkontrollierten Teilmenge gehen die harten Verstöße von 0,17 auf 0,50 und die offenen
Dienste von 0,83 auf 1,50 — die Richtung bleibt, die Fallzahl ist jedoch zu klein und die
Werte sind zu nah an null, um darauf eine Aussage zu stützen.

**Konsequenz für die Interpretation.** Aus dieser Kampagne lässt sich belegen, dass eine
gebündelte Ausfallwelle die Lastverteilung strukturell verschlechtert und den Vorsprung der
Optimierung in dieser Dimension aufzehrt. Die Aussage „eine Welle macht den Plan
instabiler" lässt sich **nicht** sauber von „eine Welle bringt mehr Ausfälle mit sich"
trennen — jedenfalls nicht mit dieser Stichprobe. Beide Sätze sind für sich plausibel; die
Daten belegen nur den ersten.

### 3.4 Eine Eigenschaft der Heuristik

Bei den Untergrenzenverstößen der Baseline liegt S1 mit 1,33 knapp *unter* S0 mit 1,67,
obwohl S1 zusätzliche Ausfälle enthält. Der Grund ist die Konstruktion der Heuristik: Sie
wählt je Dienst die momentan am wenigsten ausgelastete geeignete Person. Fällt jemand aus,
ändert sich die Reihenfolge — und gelegentlich zum Besseren. Eine greedy Auswahl ist nicht
monoton: Eine Verschlechterung der Ausgangslage kann zufällig zu einem besseren Plan
führen. Für den Verfahrensvergleich ist das selbst ein Befund — die Baseline reagiert auf
Störungen unsystematisch, die Optimierung nicht (MILP: 0,00 Verstöße in allen drei
Szenarien).

---

## 4. Was die Kampagne beantwortet

**Der Gleichstand aus der Einzelmessung war instanzabhängig.** Bei bedarfsgerechter
Besetzung erreichen beide Verfahren nahezu die Sollbesetzung. Sobald die Personaldecke
sinkt, trennen sich die Verfahren deutlich.

**Unter Knappheit sichert nur die Optimierung die gesetzliche Untergrenze.** Bei 80 %
Personaldecke unterschreitet die Heuristik die Pflegepersonaluntergrenze im Mittel 4,3-mal
je Plan und lässt insgesamt 104 Dienste unbesetzt; die Optimierung kommt auf null
Untergrenzenverstöße und null unbesetzte Dienste über alle 15 Pläne hinweg. **Kein einziger
Greedy-Plan bei 80 % war vollständig regelkonform, 100 % der MILP-Pläne waren es.** Das ist
das betriebswirtschaftlich relevanteste Ergebnis: Der Mehrwert der Optimierung entsteht
nicht im Normalbetrieb, sondern genau dort, wo es eng wird.

**Die Verteilungswirkung ist im Normalbetrieb groß und unter Störung fragil.** Bei
bedarfsgerechter Besetzung sinkt die Streuung der individuellen Auslastung von 0,069 auf
0,014, die Spanne zwischen der am geringsten und der am stärksten ausgelasteten Person von
33 auf 7 Prozentpunkte, und alle 15,7 Überschreitungen der Wochenend- und
Nachtdienst-Richtwerte entfallen. Unter der Ausfallwelle ist dieser Vorsprung aufgezehrt
(Abschnitt 3.2).

**Die reaktive Umplanung ist der größte Einzeleffekt.** Eine vollständige Neuplanung nach
Ausfällen erhält nur rund die Hälfte des Plans (MILP 48,5–51,4 %, Greedy 72,6–78,8 %) und
ändert im Mittel 277 Zuweisungen. Die reaktive Variante hält 93,8–95,9 % Planstabilität bei
Ø 23 Änderungen und rechnet in 0,20 s im Median (Maximum 3,08 s), bei unveränderter
Besetzungsquote und ohne zusätzliche Regelverstöße. Für die Mitarbeitenden ist das der
Unterschied zwischen „einige Dienste ändern sich" und „der Monat wird neu gemacht".

**Der Preis der Stabilität ist messbar.** Die reaktive Variante erkauft sich die
Planstabilität mit schlechterer Lastverteilung (Streuung 0,057 statt 0,014 bei 100 %
Decke) und einzelnen weichen Abweichungen (0,9 statt 0,0). Das ist kein Mangel, sondern
der Zielkonflikt selbst — der Prototyp macht ihn quantifizierbar, statt ihn zu verstecken.

**Rechenzeit ist kein limitierender Faktor.** Die Optimierung braucht 9,5 s bei
bedarfsgerechter und 16,3 s bei knapper Besetzung; in 8 von 90 Läufen (9 %) griff das
Zeitlimit von 30 s, ohne dass die Ergebnisqualität erkennbar litt — auch diese Pläne sind
vollständig regelkonform. Die Umplanung liegt im Median unter einer Viertelsekunde.

---

## 5. Was die Kampagne **nicht** beantwortet

**Volumen und Struktur der Ausfälle sind nicht vollständig entkoppelt.** Der Restunterschied
von 13,6 % im Ausfallvolumen zwischen S1 und S2 erlaubt es nicht, den Stabilitätsunterschied
der Struktur zuzuschreiben (Abschnitt 3.3). Für den Verteilungseffekt reicht die Kontrolle;
für den Stabilitätseffekt nicht.

**Die Heuristik ist keine echte Excel-Planung.** Sie ist eine programmierte Regelheuristik:
konsistenter, schneller und ermüdungsfrei. Der Unterschied zu manueller Planung dürfte
größer sein als hier gemessen — belegen lässt sich das mit diesem Aufbau nicht.

**Fünf Seeds sind wenig.** Die Streuungen tragen die Kernaussagen zur Regelkonformität
(Untergrenzenverstöße bei 80 %: Greedy 4,33 ± 1,95 gegen MILP 0,00 ± 0,00). Für die
Szenarienanalyse in Abschnitt 3.3 steht nur eine Teilmenge von 6 Instanzen zur Verfügung —
zu wenig für inferenzstatistische Aussagen. Ein Signifikanztest wird bewusst nicht
gerechnet.

**Die Gewichte der Zielfunktion sind gesetzt, nicht hergeleitet.** Wie stark Unterbesetzung
gegen Lastverteilung gegen Wunscherfüllung zählt, ist eine Managemententscheidung. Andere
Gewichte liefern andere Pläne. Eine Sensitivitätsanalyse dazu steht aus.

**Die Obergrenze der Optimierung wurde nicht erreicht.** Das MILP löst alle 90 Instanzen
vollständig regelkonform. Das heißt nicht, dass es das immer täte — es heißt, dass der
untersuchte Knappheitsbereich bis 80 % Personaldecke für das Modell noch lösbar ist.

**Alle Daten sind synthetisch.** Die absolute Höhe der Kennzahlen ist nicht auf eine
konkrete Station übertragbar. Der Vergleich zweier Verfahren auf identischer Datenbasis
bleibt gültig.

---

## 6. Methodenwahl

Machine Learning wurde geprüft und verworfen: Es gibt keine zu lernende Zielvariable und
keine historischen Planentscheidungen als Trainingsdaten. Das Problem ist eine Zuordnung
unter harten Nebenbedingungen mit mehreren konkurrierenden Zielen — dafür sind
mathematische Optimierung und Constraint Programming die einschlägigen Verfahren
(Burke et al. 2004; Van den Bergh et al. 2013). Umgesetzt ist ein MILP, gelöst mit HiGHS
über `scipy.optimize.milp`; ein CP-SAT-Modell wäre eine gleichwertige Alternative.

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
  Heuristik nicht: 0 gegen 4,3 Untergrenzenverstöße je Plan bei 80 % Decke; 100 % gegen
  0 % vollständig regelkonforme Pläne.
- Gleichmäßigere Belastung im Normalbetrieb: Streuung der Auslastung um Faktor 5 geringer,
  Spanne von 33 auf 7 Prozentpunkte, alle Wochenend- und Nachtdienst-Richtwerte eingehalten.
- Reaktion auf Ausfälle: 94–96 % Planstabilität statt 49–79 %, Ø 23 statt 277 geänderte
  Zuweisungen, Umplanung im Median unter einer Viertelsekunde.

**Gemessen, aber gegenläufig:** Unter einer gebündelten Ausfallwelle verschwindet der
Verteilungsvorteil der Optimierung vollständig (Spanne 0,376 gegen 0,380). Die
Regelkonformität bleibt erhalten, die Verteilungsgerechtigkeit nicht. Eine Einführung darf
also nicht mit gleichmäßigerer Belastung *in der Krise* beworben werden.

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

**Optimierung ersetzt kein Personal.** Der Verteilungsvorteil setzt Spielraum voraus. Ist
der Spielraum weg, sichert die Optimierung noch die Regelkonformität, aber nicht mehr die
Gerechtigkeit der Verteilung. Wer eine Planungssoftware als Antwort auf strukturelle
Unterbesetzung einführt, kauft Rechtssicherheit — keine Entlastung der Mitarbeitenden.

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
3. **Die Unterstützung hat eine Grenze.** Unter einer gebündelten Ausfallwelle bleibt die
   Regelkonformität erhalten, der Verteilungsvorteil nicht. Optimierung nutzt vorhandenen
   Spielraum besser aus; sie erzeugt keinen.

Punkt 2 ist der methodische Kernbefund der Arbeit: Nicht „Optimierung schlägt Heuristik",
sondern „Optimierung schlägt Heuristik dann, wenn die richtigen Ziele im Modell stehen".
Punkt 3 ist der betriebswirtschaftliche: Sie schlägt die Heuristik nicht in jeder Dimension
und nicht in jeder Lage.

---

## Quellen

- Burke, E. K., De Causmaecker, P., Vanden Berghe, G., & Van Landeghem, H. (2004). The State of the Art of Nurse Rostering. *Journal of Scheduling*, 7(6), 441–499.
- Van den Bergh, J., Beliën, J., De Bruecker, P., Demeulemeester, E., & De Boeck, L. (2013). Personnel scheduling: A literature review. *European Journal of Operational Research*, 226(3), 367–385.
- Wickert, T. I., Smet, P., & Vanden Berghe, G. The nurse rerostering problem: Strategies for reconstructing disrupted schedules. *Computers & Operations Research*.
- HiGHS über `scipy.optimize.milp` — <https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html>

Rechtsgrundlagen, Datenherkunft und Annahmenregister: siehe `DATENKONZEPT.md`.
