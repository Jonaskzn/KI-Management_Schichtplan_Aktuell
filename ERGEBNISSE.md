# Evaluation: regelbasierte Planung vs. MILP-Optimierung

**Versuchsaufbau:** 15 Instanzen (5 Seeds × 3 Personaldecken) × 3 Ausfallszenarien ×
6 Verfahrensvarianten = **270 Pläne**
**Station:** Innere Medizin / Kardiologie, 30 Betten, 28 Planungstage, 28 Tage Historie
**Reproduktion:** `python campaign.py` (ca. 15 Min.), Auswertung `python campaign.py --report`
**Rohdaten:** `evaluation_results.csv` (270 Zeilen, eine je Plan)

Alle Zahlen sind **gemessene Ergebnisse des Prototyps**. Was daraus für den Business Impact
folgt und was nicht, steht in Abschnitt 8.

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

Verglichen werden sechs Varianten: beide Verfahren als vollständige Neuplanung, beide als
reaktive Umplanung des **eigenen** Ausgangsplans, und beide als reaktive Umplanung des
**fremden** Ausgangsplans. Die beiden letzten Varianten sind nötig, weil die Planstabilität
zwischen den Verfahren sonst nicht vergleichbar ist — siehe Abschnitt 4.

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
| Planstabilität (eigener Ausgangsplan) | 72,6 % | 94,5 % | 48,5 % | 95,3 % |
| Planungszeit | 0,40 s | 0,35 s | 8,74 s | 0,24 s |

### Knappe Besetzung (90 %, Ø 20 Köpfe)

| Kennzahl | Greedy | Greedy reaktiv | MILP | MILP reaktiv |
|---|---|---|---|---|
| Besetzungsquote | 99,7 % | 99,5 % | **100,0 %** | **100,0 %** |
| Untergrenzenverstöße | 0,33 ± 0,62 | 0,47 ± 0,64 | **0,00** | **0,00** |
| harte Regelverstöße | 0,33 ± 0,49 | 0,73 ± 0,70 | **0,00** | **0,00** |
| weiche Abweichungen | 15,1 ± 1,4 | 14,9 ± 1,9 | **0,2 ± 0,4** | 1,7 ± 1,8 |
| Streuung Auslastung | 0,059 ± 0,037 | 0,069 ± 0,038 | **0,017 ± 0,007** | 0,044 ± 0,024 |
| Planstabilität (eigener Ausgangsplan) | 78,3 % | 93,5 % | 49,5 % | 95,9 % |
| Planungszeit | 0,35 s | 0,30 s | 12,23 s | 0,33 s |

### Unterbesetzt (80 %, Ø 18 Köpfe)

| Kennzahl | Greedy | Greedy reaktiv | MILP | MILP reaktiv |
|---|---|---|---|---|
| Besetzungsquote | 95,2 % | 95,2 % | **100,0 %** | **100,0 %** |
| Untergrenzenverstöße | 4,73 ± 1,79 | 5,07 ± 2,09 | **0,00** | **0,00** |
| harte Regelverstöße | 0,87 ± 1,36 | 1,20 ± 1,52 | **0,00** | **0,00** |
| weiche Abweichungen | 16,2 ± 2,3 | 16,3 ± 2,4 | **2,9 ± 1,2** | 4,8 ± 1,9 |
| Streuung Auslastung | 0,088 ± 0,021 | 0,094 ± 0,022 | **0,065 ± 0,036** | 0,086 ± 0,035 |
| Planstabilität (eigener Ausgangsplan) | 78,5 % | 92,2 % | 54,8 % | 93,9 % |
| Planungszeit | 0,32 s | 0,27 s | 15,38 ± 10,52 s | 0,45 s |

### Anteil vollständig regelkonformer Pläne

(keine harten Regelverstöße **und** keine Untergrenzenverstöße)

| Verfahren | 80 % | 90 % | 100 % |
|---|---|---|---|
| Greedy | **0 %** | 67 % | 93 % |
| Greedy reaktiv | **0 %** | 40 % | 93 % |
| MILP | **100 %** | 100 % | 100 % |
| MILP reaktiv | **100 %** | 100 % | 100 % |

Über alle 135 MILP-Pläne hinweg gibt es **keinen einzigen** harten Regelverstoß, keine
Untergrenzenunterschreitung und keinen unbesetzten Dienst. Die Heuristik lässt bei 80 %
Decke insgesamt 92 Dienste unbesetzt und unterschreitet die Untergrenze 71-mal.

Die Zeile „Planstabilität" ist in diesen Tabellen bewusst nicht fett ausgezeichnet: Sie
misst jedes Verfahren gegen seinen **eigenen** Ausgangsplan und ist deshalb zwischen den
Verfahren nicht vergleichbar. Abschnitt 4 holt das nach.

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

| Kennzahl | S0 | S1 | S2 |
|---|---|---|---|
| Spanne — Regelbasiert, Neuplanung | 0,283 | 0,301 | 0,328 |
| Spanne — MILP, Neuplanung | **0,122** | **0,140** | **0,163** |
| Spanne — Regelbasiert, reaktiv | 0,283 | 0,337 | 0,379 |
| Spanne — MILP, reaktiv | 0,122 | 0,275 | 0,377 |
| offene Dienste — Regelbasiert, reaktiv | 2,00 | 2,40 | **3,73** |
| harte Regelverstöße — Regelbasiert, reaktiv | 0,33 | 0,47 | **1,20** |

Planstabilität fehlt in dieser Tabelle bewusst — sie gehört in Abschnitt 4, weil sie nur
auf identischem Ausgangsplan zwischen den Verfahren aussagekräftig ist.

### 3.2 Warum der Abstand bei der Spanne unter S2 klein wird

In der reaktiven Betriebsart liegen beide Verfahren unter der Ausfallwelle bei der
Lastverteilung dicht beieinander: Spanne 0,377 gegen 0,379. Das ist erklärungsbedürftig,
weil die Optimierung ohne Störung um den Faktor 2,3 besser verteilt (0,122 gegen 0,283).
Drei Befunde ordnen das ein.

**Erstens: Die Optimierung verliert den Verteilungsvorteil nicht durch die Welle.** Bei
vollständiger Neuplanung hält sie die Spanne auch unter S2 auf 0,163 — gegenüber 0,329 bei
der Heuristik in derselben Betriebsart. Die Welle verschlechtert die Verteilung der
Optimierung nur moderat (0,122 → 0,140 → 0,163). Was den Vorteil aufzehrt, ist die
**reaktive Betriebsart selbst**: 0,163 → 0,377. Die Ursache steht in der Zielfunktion. Das
Gewicht für „Zuweisung beibehalten" beträgt 200, das für Lastausgleich 0,02. Wer dem Modell
sagt, es solle den Plan möglichst nicht anfassen, bekommt genau das: Lückenfüllen statt
Umverteilen — und damit dasselbe Verhalten wie die Heuristik. **Der schmale Abstand ist
eine Gewichtungsentscheidung, keine Grenze des Verfahrens.**

**Zweitens: Die gleiche Spanne bedeutet nicht die gleiche Leistung.** Die Heuristik erreicht
ihre Werte teilweise dadurch, dass sie Dienste **gar nicht besetzt**. Ein unbesetzter Dienst
erzeugt keine Auslastung, drückt die Spanne also nicht nach oben, und er erzeugt auch keine
Planänderung, hebt die Stabilität also künstlich. Unter S2 lässt die Heuristik im Mittel
3,87 Dienste offen (bei 80 % Decke sogar 9,4), die Optimierung keinen einzigen. Die mittlere
Auslastung liegt bei der Optimierung entsprechend höher: 98,6 % gegen 96,3 %. **Die
Optimierung verteilt also mehr Arbeit auf dieselbe Mannschaft und erreicht dabei dieselbe
Spanne.** Bei gleicher Besetzung wäre der Vergleich nicht ausgeglichen, sondern deutlich
zugunsten der Optimierung verschoben.

**Drittens: Der Unterschied verschwindet nicht, er verlagert sich.** Unter S2 stehen sich
gegenüber (beide reaktiv, jeweils auf dem Plan der Optimierung):

| Kennzahl unter S2 | Regelbasiert | MILP |
|---|---|---|
| Besetzungsquote | 99,3 % | **100,0 %** |
| offene Dienste je Plan | 1,33 | **0,00** |
| harte Regelverstöße je Plan | 0,53 | **0,00** |
| weiche Abweichungen je Plan | 6,00 | **3,27** |
| Spanne der Auslastung | 0,382 | 0,377 |
| Planstabilität | 87,2 % | **91,3 %** |
| geänderte Zuweisungen | 39,2 | **26,2** |

Auf der einen Kennzahl, die dicht beieinanderliegt, ist die Optimierung nicht schlechter.
Auf allen übrigen ist der Abstand eindeutig. Unter der Ausfallwelle liegt ihr Mehrwert in
**Versorgungssicherheit, Rechtskonformität und Planstabilität**, nicht mehr in der
Verteilungsgerechtigkeit — solange man ihr Stabilität als vorrangiges Ziel vorgibt.

### 3.3 Kontrolle für das Ausfallvolumen — und eine Korrektur

Weil S2 über die Instanzen im Mittel 13,6 % mehr Ausfalltage trägt, wurde jede
Szenariodifferenz zusätzlich auf der Teilmenge der **6 Instanzen** geprüft, in denen S2
**nicht** mehr Ausfalltage hat als S1:

| Differenz S2 − S1 (MILP reaktiv) | alle 15 Instanzen | volumenkontrolliert (6) |
|---|---|---|
| Spanne der Auslastung | +0,102 (13 von 15) | **+0,084 (6 von 6)** |
| Planstabilität | −2,5 Pp. (12 von 15) | −0,8 Pp. (4 von 6) |

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

## 4. Planstabilität: welcher Vergleich welche Frage beantwortet

### 4.1 Der End-to-End-Vergleich — die Antwort auf die Leitfrage

Die Leitfrage fragt nach „Erstellung **und** kurzfristiger Anpassung" — also nach einer
**Kette aus zwei Schritten**, nicht nach einem isolierten Reparaturalgorithmus. In der
Excel-Welt erstellt die Heuristik den Monatsplan und passt ihn an; in der KI-Welt macht das
die Optimierung. Beide arbeiten dabei auf **demselben Datensatz**: derselben Belegschaft,
denselben Bedarfs- und Regelspalten, denselben Ausfallszenarien. Was sich unterscheidet, ist
allein das Verfahren. Jedes tut also, was es real täte:

| Kennzahl (Mittel über 45 Pläne) | Regelbasiert | MILP | |
|---|---|---|---|
| Planstabilität | 93,4 % | **95,0 %** | ✓ |
| geänderte Zuweisungen je Plan | 19,7 | **14,9** | ✓ |
| Besetzungsquote | 98,2 % | **100,0 %** | ✓ |
| offene Dienste | 2,71 | **0,00** | ✓ |
| Untergrenzenverstöße | 1,84 | **0,00** | ✓ |
| harte Regelverstöße | 0,67 | **0,00** | ✓ |
| weiche Abweichungen | 15,8 | **2,47** | ✓ |
| Spanne der Auslastung | 0,333 | **0,258** | ✓ |

**Die Optimierung gewinnt jede einzelne Kennzahl.** Entscheidend ist, dass Planstabilität
und absolute Änderungszahl **in dieselbe Richtung** zeigen: 95,0 % gegen 93,4 % bei
gleichzeitig 14,9 gegen 19,7 geänderten Diensten. Ginge nur der Prozentwert zugunsten der
Optimierung aus, wäre der Einwand berechtigt, die beiden Werte bezögen sich auf
unterschiedliche Ausgangspläne. Da auch die absolute Zahl geänderter Dienste niedriger ist,
trägt die Aussage: **Die Mitarbeitenden erleben in der KI-Welt rund ein Viertel weniger
Planänderungen.**

Auf Einzelplanebene ist die Optimierung in 21 der 30 gestörten Pläne stabiler (70 %) — nicht
in allen. Die Aussage gilt im Mittel, nicht in jeder Instanz.

### 4.2 Die Methodenkontrolle — reparieren beide denselben Plan

Der End-to-End-Vergleich misst die Planstabilität gegen zwei unterschiedlich gute
Ausgangspläne:

| Ausgangsplan (Szenario S0) | weiche Abweichungen | Spanne | offene Dienste |
|---|---|---|---|
| der Heuristik | 15,3 | 0,283 | 2,27 |
| der Optimierung | **1,1** | **0,122** | **0,00** |

Einen schwachen Plan unverändert zu lassen ist billig — es gibt nichts zu verteidigen.
Deshalb prüft die Kampagne zusätzlich, was passiert, wenn **beide Verfahren denselben Plan
reparieren**.

**Auf dem Plan der Optimierung:**

| Kennzahl | Regelbasiert repariert | MILP repariert |
|---|---|---|
| Planstabilität | 91,8 % | **95,0 %** |
| geänderte Zuweisungen | 24,8 | **14,9** |
| weiche Abweichungen | 5,07 | **2,47** |
| harte Regelverstöße | 0,22 | **0,00** |
| offene Dienste | 0,73 | **0,00** |

Die Optimierung bleibt in jeder Kennzahl vorn; unter der Ausfallwelle ist sie in **14 von
15 Instanzen** stabiler. Der End-to-End-Befund ist also kein Artefakt der Ausgangspläne.

**Auf dem Plan der Heuristik:**

| Kennzahl | Regelbasiert repariert | MILP repariert |
|---|---|---|
| Planstabilität | **93,4 %** | 91,5 % |
| geänderte Zuweisungen | **19,7** | 25,8 |
| Spanne der Auslastung | **0,333** | 0,362 |
| harte Regelverstöße | 0,67 | **0,00** |
| Untergrenzenverstöße | 1,84 | **0,00** |
| offene Dienste | 2,71 | **0,00** |

Hier ändert die Optimierung **mehr**. Das ist kein Qualitätsmangel, sondern eine logische
Folge: Die 2,71 unbesetzten Dienste und 1,84 Untergrenzenverstöße im geerbten Plan lassen
sich nur beheben, **indem** Zuweisungen geändert werden. Ein Verfahren, das sie stehen
lässt, gewinnt die Stabilitätskennzahl durch Untätigkeit. Wer einen schlechten Plan erbt,
muss ihn anfassen, um ihn rechtskonform zu machen.

### 4.3 Alle vier Kombinationen — warum der Vorteil systemisch ist

Kreuzt man beide Ausgangspläne mit beiden Reparaturverfahren, ergibt sich ein Bild, das
weder dem einen noch dem anderen Schritt allein zuzuschreiben ist. Geänderte Zuweisungen je
Plan:

| | repariert von der Heuristik | repariert von der Optimierung |
|---|---|---|
| **Ausgangsplan der Heuristik** | 19,7 | 25,8 |
| **Ausgangsplan der Optimierung** | 24,8 | **14,9** |

Zwei Ablesungen:

**Zeilenweise** ändert die Optimierung auf jedem geerbten Plan mehr als die Heuristik. Das
ist zwingend und kein Tuning-Problem: Ein Plan mit offenen Diensten und Regelverstößen wird
nur dadurch rechtskonform, dass Zuweisungen geändert werden. Ein gemeinsamer Ausgangsplan —
gleich welcher — kann die Optimierung auf dieser Kennzahl deshalb nie vorn sehen.

**Diagonal** zeigt sich der eigentliche Befund: Nur die Kombination „Optimierung plant und
Optimierung repariert" erreicht 14,9. Ein guter Plan, von der Heuristik repariert, kostet
mit 24,8 Änderungen **mehr** als der schwache Plan der Heuristik in ihrer eigenen Hand
(19,7) — weil ein dicht gepackter Plan ohne Slack von einer lokal entscheidenden Heuristik
nicht effizient repariert werden kann. Der Vorteil steckt also **weder in der Planung noch
in der Anpassung allein, sondern im Zusammenspiel**: Die Optimierung baut einen Plan, der
Spielraum an den richtigen Stellen lässt, und weiß zugleich, wie sie ihn nutzt.

Betriebswirtschaftlich ist das die relevante Aussage: Ein Optimierer, der nur als
Feuerwehr auf bestehende Excel-Pläne gesetzt wird, hebt einen Teil des Nutzens — die
Rechtskonformität —, aber nicht den Effizienzvorteil. Der entsteht erst, wenn auch die
Monatsplanung aus dem System kommt.

### 4.4 Was daraus folgt

Es gibt **keinen** Aufbau, in dem die Optimierung auf allen Kennzahlen gleichzeitig gewinnt,
wenn sie einen mangelhaften Plan erbt — „möglichst wenig ändern" und „Mängel beheben" sind
dann unvereinbare Ziele. Das ist keine Schwäche des Verfahrens, sondern eine Eigenschaft der
Kennzahl: **Planstabilität misst Zurückhaltung, nicht Qualität.**

Für die Arbeit folgt daraus eine klare Ordnung:

1. **Hauptaussage ist der End-to-End-Vergleich** (4.1). Er beantwortet die Leitfrage, und
   die Optimierung gewinnt dort jede Kennzahl.
2. **Belegt wird er durch die Methodenkontrolle auf dem Plan der Optimierung** (4.2). Sie
   zeigt, dass der Vorsprung nicht an unterschiedlichen Ausgangsplänen hängt.
3. **Die Vier-Felder-Tafel (4.3) trägt den Wirkmechanismus**: Der Effizienzvorteil ist
   systemisch und entsteht erst, wenn Planung und Anpassung aus derselben Hand kommen.
4. **Der Migrationsfall — Optimierung erbt einen Excel-Plan — gehört in die Diskussion**,
   nicht in die Ergebnistabelle: Wer umsteigt, muss im ersten Monat mit mehr Änderungen
   rechnen, weil Altlasten mitbehoben werden.
5. **Jede Stabilitätsangabe nennt ihren Ausgangsplan.** Unsere erste Auswertung tat das
   nicht und war dadurch nicht interpretierbar.

---

## 5. Was die Kampagne beantwortet

**Der Gleichstand aus der Einzelmessung war instanzabhängig.** Bei bedarfsgerechter
Besetzung erreichen beide Verfahren nahezu die Sollbesetzung. Sobald die Personaldecke
sinkt, trennen sich die Verfahren deutlich.

**Unter Knappheit sichert nur die Optimierung die gesetzliche Untergrenze.** Bei 80 %
Personaldecke unterschreitet die Heuristik die Pflegepersonaluntergrenze im Mittel 4,7-mal
je Plan und lässt insgesamt 92 Dienste unbesetzt; die Optimierung kommt auf null
Untergrenzenverstöße und null unbesetzte Dienste über alle 15 Pläne hinweg. **Kein einziger
Greedy-Plan bei 80 % war vollständig regelkonform, 100 % der MILP-Pläne waren es.** Das ist
das betriebswirtschaftlich relevanteste Ergebnis: Der Mehrwert der Optimierung entsteht
nicht im Normalbetrieb, sondern genau dort, wo es eng wird.

**Die Verteilungswirkung ist groß — solange Stabilität nicht vorrangig ist.** Bei
bedarfsgerechter Besetzung sinkt die Streuung der individuellen Auslastung von 0,069 auf
0,014, die Spanne zwischen der am geringsten und der am stärksten ausgelasteten Person von
33 auf 7 Prozentpunkte, und alle 15,7 Überschreitungen der Wochenend- und
Nachtdienst-Richtwerte entfallen. In der reaktiven Betriebsart gibt die Optimierung diesen
Vorsprung weitgehend auf, weil die Zielfunktion sie dazu anhält (Abschnitt 3.2).

**Die reaktive Umplanung ist der größte Einzeleffekt.** Eine vollständige Neuplanung nach
Ausfällen erhält nur rund die Hälfte des Plans (MILP 48,5–54,8 %) und ändert im Mittel 277
Zuweisungen. Die reaktive Variante hält 93,9–95,9 % Planstabilität bei Ø 15 Änderungen und
rechnet in 0,16 s im Median (Maximum 2,79 s), bei unveränderter Besetzungsquote und ohne
zusätzliche Regelverstöße. Für die Mitarbeitenden ist das der Unterschied zwischen „einige
Dienste ändern sich" und „der Monat wird neu gemacht". Dieser Vergleich ist innerhalb eines
Verfahrens gezogen und deshalb von der Frage aus Abschnitt 4 nicht betroffen.

**Im End-to-End-Vergleich gewinnt die Optimierung jede Kennzahl.** Gegenüber der
Excel-Welt: 100 % statt 98,2 % Besetzung, null statt 2,71 offene Dienste, null statt 1,84
Untergrenzenverstöße, 2,5 statt 15,8 weiche Abweichungen, Spanne 0,258 statt 0,333 — und
dabei 14,9 statt 19,7 geänderte Dienste je Plan bei 95,0 % statt 93,4 % Planstabilität
(Abschnitt 4.1).

**Der Preis der Stabilität ist messbar.** Die reaktive Variante erkauft sich die
Planstabilität mit schlechterer Lastverteilung (Streuung 0,057 statt 0,014 bei 100 %
Decke) und einzelnen weichen Abweichungen (0,9 statt 0,0). Das ist kein Mangel, sondern
der Zielkonflikt selbst — der Prototyp macht ihn quantifizierbar, statt ihn zu verstecken.

**Rechenzeit ist kein limitierender Faktor.** Die Optimierung braucht 8,7 s bei
bedarfsgerechter und 15,4 s bei knapper Besetzung; in 6 von 135 Läufen (4 %) griff das
Zeitlimit von 30 s, ohne dass die Ergebnisqualität erkennbar litt — auch diese Pläne sind
vollständig regelkonform. Die Umplanung liegt im Median bei 0,16 s.

---

## 6. Was die Kampagne **nicht** beantwortet

**Volumen und Struktur der Ausfälle sind nicht vollständig entkoppelt.** Der Restunterschied
von 13,6 % im Ausfallvolumen zwischen S1 und S2 erlaubt es nicht, den Stabilitätsunterschied
der Struktur zuzuschreiben (Abschnitt 3.3). Für den Verteilungseffekt reicht die Kontrolle;
für den Stabilitätseffekt nicht.

**Planstabilität misst Zurückhaltung, nicht Qualität.** Sie hängt von der Güte des
Ausgangsplans ab (Abschnitt 4). Ein Verfahren, das offene Dienste und Regelverstöße im
geerbten Plan stehen lässt, schneidet auf dieser Kennzahl besser ab als eines, das sie
behebt. Jede Stabilitätsangabe in dieser Arbeit nennt deshalb ihren Ausgangsplan mit. Für
die Bewertung eines eingeführten Systems ist der End-to-End-Vergleich maßgeblich; der
Migrationsfall — die Optimierung erbt einen Excel-Plan — ist gesondert ausgewiesen.

**Die Heuristik ist keine echte Excel-Planung.** Sie ist eine programmierte Regelheuristik:
konsistenter, schneller und ermüdungsfrei. Der Unterschied zu manueller Planung dürfte
größer sein als hier gemessen — belegen lässt sich das mit diesem Aufbau nicht.

**Fünf Seeds sind wenig.** Die Streuungen tragen die Kernaussagen zur Regelkonformität
(Untergrenzenverstöße bei 80 %: Greedy 4,73 ± 1,79 gegen MILP 0,00 ± 0,00). Für die
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

## 7. Methodenwahl

Machine Learning wurde geprüft und verworfen: Es gibt keine zu lernende Zielvariable und
keine historischen Planentscheidungen als Trainingsdaten. Das Problem ist eine Zuordnung
unter harten Nebenbedingungen mit mehreren konkurrierenden Zielen — dafür sind
mathematische Optimierung und Constraint Programming die einschlägigen Verfahren
(Burke et al. 2004; Van den Bergh et al. 2013). Umgesetzt ist ein MILP mit 2.429 Variablen und
4.232 Nebenbedingungen, gelöst mit HiGHS über `scipy.optimize.milp`; ein CP-SAT-Modell wäre
eine gleichwertige Alternative.

Rechtliche und vertragliche Grenzen sind harte Nebenbedingungen. Unterbesetzung,
Untergrenzenverstöße, Lastverteilung, Dienstwünsche sowie Wochenend- und
Nachtdienstverteilung gehen gewichtet in die Zielfunktion ein. Alle Besetzungsziele sind
weich modelliert, damit das Modell auch bei unlösbarer Instanz einen Plan mit
ausgewiesenen Lücken liefert statt gar keinen.

**Beide Verfahren werden von derselben, verfahrensunabhängigen Funktion `evaluate()`
bewertet.** Ein Verfahren darf seine eigene Regelkonformität nicht selbst behaupten.

### 7.1 Begriffsklärung: In welchem Sinn ist das „KI"?

Die Frage ist berechtigt und wird in der Verteidigung gestellt werden. Die Antwort hat drei
Ebenen, die auseinandergehalten werden müssen.

**Umgangssprachlich** meint „KI" heute meist maschinelles Lernen. In diesem Sinn ist das
Verfahren **keine** KI: Das Modell lernt nichts, es hat keine Trainingsphase, keine
Parameter, die aus Daten geschätzt werden. Es löst bei jedem Aufruf ein frisch aufgestelltes
Optimierungsproblem.

**Fachlich** gehören Suche, Constraint-Erfüllung und automatisches Planen und Scheduling
seit den Anfängen zum Kern der Künstlichen Intelligenz und stehen in jedem Standardlehrbuch
des Fachs (Russell & Norvig 2021). Nurse Rostering wird in der KI- wie in der
Operations-Research-Literatur gleichermaßen behandelt (Burke et al. 2004). In diesem Sinn
ist das Verfahren KI — und zwar eine ihrer ältesten und am besten verstandenen Formen.

**Regulatorisch** ist die Einordnung offen. Art. 3 Abs. 1 der KI-Verordnung (EU) 2024/1689
definiert ein KI-System funktional über die Fähigkeit, aus Eingaben abzuleiten, wie Ausgaben
erzeugt werden. Erwägungsgrund 12 nennt „logik- und wissensbasierte Ansätze, die aus
kodiertem Wissen schlussfolgern" ausdrücklich als Inferenztechnik, nimmt aber Systeme aus,
die „ausschließlich auf von natürlichen Personen definierten Regeln beruhen, um Operationen
automatisch auszuführen". Ein MILP-Solver liegt dazwischen: Die Regeln und Gewichte stammen
von Menschen, der Dienstplan selbst aber ist nicht vorprogrammiert, sondern wird aus dem
kodierten Wissen abgeleitet. Eine eindeutige Zuordnung nehmen wir nicht vor; beide Lesarten
sind vertretbar.

**Für dieses Projekt entscheidend ist:** Die Aufgabenstellung verlangt kein maschinelles
Lernen. Sie verlangt, „objektiv zu prüfen, welcher technische Ansatz für das Problem
geeignet ist", nennt mathematische Optimierung und Constraint Programming ausdrücklich als
Kandidaten und warnt davor, ML als Standardantwort anzunehmen. Die Methodenwahl folgt genau
dieser Vorgabe und ist aus der Problemstruktur begründet, nicht aus einer Begriffsmode.

### 7.2 Wo maschinelles Lernen anschlussfähig wäre

Verworfen ist ML für die **Planerstellung**, nicht für das Gesamtsystem. Ein hybrider Aufbau
ist naheliegend: Ein Prognosemodell schätzt aus historischen Daten die zu erwartende
Belegung und die Ausfallwahrscheinlichkeit je Tag; diese Schätzungen gehen als Parameter in
die Optimierung ein („predict-then-optimize"). Der Optimierer könnte dann Reserven dort
vorhalten, wo Ausfälle wahrscheinlich sind, statt gleichmäßig.

**Das ist in diesem Prototyp ausdrücklich nicht umgesetzt.** Für ein Prognosemodell
bräuchte es echte historische Betriebsdaten; unsere Daten sind synthetisch, ein darauf
trainiertes Modell würde nur die eigenen Generatorannahmen zurückgeben. Der Punkt gehört in
den Ausblick, nicht in die Ergebnisse.

### 7.3 Fairness der Baseline

Ein Verfahrensvergleich taugt nur so viel wie seine Baseline. Wird sie strenger behandelt
als das Verfahren, das sie schlagen soll, misst man den eigenen Aufbau statt der Methode.
Eine solche Asymmetrie war zunächst im Code:

Der **Nachtdienst-Richtwert** (höchstens 8 Nachtdienste in vier Wochen) ist eine gesetzte
Annahme, keine gesetzliche Grenze — er ist arbeitswissenschaftlich gestützt, aber im ArbZG
nicht beziffert (siehe `DATENKONZEPT.md`, Annahme A10). `evaluate()` zählt seine
Überschreitung folgerichtig als **weiche** Abweichung. Das MILP modelliert ihn ebenfalls
weich, mit einem Strafgewicht von 30. Die Heuristik behandelte ihn jedoch als **harte**
Sperre: Wer sein Kontingent ausgeschöpft hatte, kam für den Nachtdienst nicht mehr infrage —
auch dann nicht, wenn der Dienst sonst unbesetzt geblieben wäre.

Die Folge war eine Ungleichbehandlung: Das MILP durfte eine weiche Überschreitung in Kauf
nehmen, um einen Dienst zu besetzen (Strafe 30 gegen 1.000 für Unterbesetzung), die
Heuristik nicht. Da eine reale Stationsleitung in dieser Lage den internen Richtwert
überschreiten und nicht die Schicht leer lassen würde, war die Baseline damit strenger
modelliert als die Wirklichkeit — und strenger als ihr Konkurrent.

**Korrektur.** Die Heuristik darf den Nachtdienst-Richtwert seit dieser Version
überschreiten, wenn andernfalls ein Dienst unbesetzt bliebe. Sie versucht zuerst eine
richtwertkonforme Besetzung und greift erst im zweiten Durchgang auf Personen zurück, die
ihr Kontingent bereits ausgeschöpft haben. Die Überschreitung wird von `evaluate()` normal
als weiche Abweichung gezählt.

**Wirkung, über alle 15 Instanzen und drei Szenarien gemessen:**

| Heuristik, Neuplanung | Richtwert hart | Richtwert weich |
|---|---|---|
| Besetzungsquote | 98,3 % | 98,3 % |
| offene Dienste je Plan | 2,49 | **2,22** |
| Untergrenzenverstöße je Plan | **1,58** | 1,71 |
| harte Regelverstöße je Plan | 0,44 | **0,42** |
| weiche Abweichungen je Plan | **14,9** | 15,6 |

Bei 90 % und 100 % Personaldecke ändert sich **nichts** — dort wird der Richtwert nie
bindend. Bei 80 % sinken die offenen Dienste über alle Instanzen von 104 auf 92, dafür
steigen die Untergrenzenverstöße von 65 auf 71 und die weichen Abweichungen von 14,1 auf
16,2 je Plan. Die Heuristik besetzt also mehr Dienste, erkauft das aber mit mehr
Richtwertüberschreitungen und trifft dabei stellenweise schlechtere Folgeentscheidungen —
erneut die in Abschnitt 3.4 beschriebene Nicht-Monotonie.

**Bewertung.** Die Korrektur verschiebt die Baseline in beide Richtungen und ändert das
Gesamtbild nicht: Die Heuristik bleibt bei 80 % Decke in **keinem einzigen** Plan
vollständig regelkonform, das MILP in **allen**. Der Befund hängt also nicht an dieser
Modellierungsentscheidung. Berichtet werden durchgängig die Zahlen der korrigierten
Variante.

---

## 8. Business Impact

**Gemessen** (gilt für diese 15 Instanzen):

- Bei knapper Personaldecke sichert die Optimierung die gesetzliche Mindestbesetzung, die
  Heuristik nicht: 0 gegen 4,7 Untergrenzenverstöße je Plan bei 80 % Decke; 100 % gegen
  0 % vollständig regelkonforme Pläne.
- Gleichmäßigere Belastung im Normalbetrieb: Streuung der Auslastung um Faktor 5 geringer,
  Spanne von 33 auf 7 Prozentpunkte, alle Wochenend- und Nachtdienst-Richtwerte eingehalten.
- Reaktion auf Ausfälle: Auf demselben Ausgangsplan hält die Optimierung 95,0 %
  Planstabilität gegen 91,8 % der Heuristik und braucht dafür 14,9 statt 24,8 Änderungen —
  bei null Regelverstößen und null unbesetzten Diensten gegen 0,22 und 0,71. Die Umplanung
  läuft im Median in 0,16 s.

**Gemessen, aber mit Zielkonflikt:** In der reaktiven Betriebsart liegt die Spanne der
Optimierung unter der Ausfallwelle gleichauf mit der Heuristik (0,377 gegen 0,379) — nicht
weil die Welle den Spielraum nähme, sondern weil die Vorgabe „möglichst wenig ändern" das
Umverteilen unterbindet. Bei vollständiger Neuplanung hält die Optimierung auch unter der
Welle 0,163. Gleichmäßigere Belastung *und* maximale Planstabilität sind nicht gleichzeitig
zu haben; welches Ziel schwerer wiegt, ist eine Managemententscheidung.

**Der Effizienzvorteil ist an die durchgängige Nutzung gebunden.** Übernimmt die
Optimierung nur die Anpassung bestehender Excel-Pläne, sichert sie weiterhin
Rechtskonformität und Besetzung (null statt 0,67 harte Verstöße, null statt 2,71 offene
Dienste), braucht dafür aber 25,8 statt 19,7 Änderungen. Der Rückgang auf 14,9 Änderungen
stellt sich erst ein, wenn auch die Monatsplanung aus dem System kommt (Abschnitt 4.3). Für
eine Einführungsentscheidung heißt das: Eine reine „Feuerwehr"-Nutzung hebt den
Rechtssicherheitsnutzen, nicht den Entlastungsnutzen.

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

**Die Gewichtung der Ziele ist eine Führungsentscheidung, keine technische.** Ob ein
Ausfall durch minimales Lückenfüllen oder durch Umverteilen im ganzen Monat aufgefangen
wird, entscheidet nicht das Verfahren, sondern das Gewicht in der Zielfunktion. Beides ist
vertretbar: Stabilität schützt die private Planung der Mitarbeitenden, Umverteilung schützt
die Gleichverteilung der Last. Der Prototyp macht den Preis beider Optionen sichtbar —
diese Abwägung gehört auf die Leitungsebene, nicht in die Konfigurationsdatei.

---

## 9. Einordnung in die Leitfrage

„Wie kann eine KI-gestützte Planungsempfehlung die Erstellung und kurzfristige Anpassung
eines Schichtplans gegenüber einer regelbasierten Excel-Planung unterstützen?"

Nach dieser Kampagne lässt sich die Antwort präzisieren:

1. **Bei der Erstellung** liegt der Mehrwert nicht in der Machbarkeit, sondern in
   Regelkonformität unter Knappheit und in der Verteilungsgerechtigkeit. Ist genug Personal
   da, tut es auch eine Regelheuristik.
2. **Bei der kurzfristigen Anpassung** liegt der Mehrwert in der Planstabilität — und zwar
   nur, wenn Stabilität ausdrücklich als Ziel modelliert wird. Eine bloße Neuoptimierung
   nach dem Ausfall ist für die Mitarbeitenden schlechter als die Heuristik.
3. **Die beiden Ziele schließen einander teilweise aus.** Unter einer gebündelten
   Ausfallwelle erreicht die Optimierung entweder eine gleichmäßige Last (Spanne 0,163 bei
   vollständiger Neuplanung) oder einen stabilen Plan (91 % unveränderte Dienste), nicht
   beides zugleich. Die Regelkonformität bleibt in jedem Fall erhalten.

4. **Erstellung und Anpassung sind nicht trennbar.** Die Vier-Felder-Tafel in Abschnitt 4.3
   zeigt, dass der Effizienzvorteil nur entsteht, wenn beide Schritte aus demselben System
   kommen: 14,9 geänderte Dienste je Plan gegenüber 19,7 in der Excel-Welt — während
   dieselbe Optimierung auf einem geerbten Excel-Plan 25,8 Änderungen braucht. Die Leitfrage
   fragt zu Recht nach beidem zusammen.

Punkt 2 ist der methodische Kernbefund der Arbeit: Nicht „Optimierung schlägt Heuristik",
sondern „Optimierung schlägt Heuristik dann, wenn die richtigen Ziele im Modell stehen".
Punkt 3 ist der betriebswirtschaftliche Vorbehalt: Der Prototyp liefert keine überlegene
Lösung auf allen Kennzahlen in jeder Lage, sondern macht einen Zielkonflikt entscheidbar,
der in der Excel-Planung unsichtbar bleibt. Punkt 4 ist die Einführungsempfehlung: Ein
Optimierer, der nur reaktiv auf bestehende Pläne gesetzt wird, hebt einen Teil des Nutzens
nicht.

---

## Quellen

- Russell, S. J., & Norvig, P. (2021). *Artificial Intelligence: A Modern Approach* (4th ed.). Pearson. — Suche, Constraint-Erfüllung und automatisches Planen als Kerngebiete der KI
- Verordnung (EU) 2024/1689 (KI-Verordnung), Art. 3 Abs. 1 und Erwägungsgrund 12 — <https://artificialintelligenceact.eu/article/3/>
- Burke, E. K., De Causmaecker, P., Vanden Berghe, G., & Van Landeghem, H. (2004). The State of the Art of Nurse Rostering. *Journal of Scheduling*, 7(6), 441–499.
- Van den Bergh, J., Beliën, J., De Bruecker, P., Demeulemeester, E., & De Boeck, L. (2013). Personnel scheduling: A literature review. *European Journal of Operational Research*, 226(3), 367–385.
- Wickert, T. I., Smet, P., & Vanden Berghe, G. The nurse rerostering problem: Strategies for reconstructing disrupted schedules. *Computers & Operations Research*.
- HiGHS über `scipy.optimize.milp` — <https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html>

Rechtsgrundlagen, Datenherkunft und Annahmenregister: siehe `DATENKONZEPT.md`.
