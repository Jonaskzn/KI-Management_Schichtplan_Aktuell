# Evaluationsergebnisse: regelbasierte Planung vs. MILP-Optimierung

**Instanz:** Normalstation Innere Medizin / Kardiologie, 30 Betten, 22 Mitarbeitende,
28 Planungstage (30.11.–27.12.2026), Datensatz-Version 2.0.0, Seed 20261130
**Stand:** erste vollständige Messung nach Fertigstellung beider Verfahren
**Reproduktion:** `python test_planner.py` — beide Verfahren, alle drei Szenarien

Alle Zahlen unten sind **gemessene Ergebnisse des Prototyps**, keine Schätzungen und
keine Literaturwerte. Was daraus für den Business Impact folgt und was nicht, steht in
Abschnitt 5.

---

## 1. Die beiden Verfahren

| | Regelbasiert (Baseline) | MILP-Optimierung |
|---|---|---|
| Vorgehen | Tag für Tag, Schicht für Schicht; jeweils die am wenigsten ausgelastete regelkonforme Person | gesamte Periode als ein gemischt-ganzzahliges Programm |
| Blickweite | eine Schicht | 28 Tage gleichzeitig |
| Löser | — (Heuristik) | HiGHS über `scipy.optimize.milp` |
| Modellgröße | — | 2.338 Variablen, 4.066 Nebenbedingungen |
| Entspricht | manueller Excel-Planung | dem „KI-gestützten" Ansatz der Leitfrage |

Beide arbeiten auf **identischen Daten, Regeln und Szenarien** — Voraussetzung für einen
fairen Vergleich (Projektvorgabe 3). Beide werden von derselben, verfahrensunabhängigen
Funktion `evaluate()` bewertet.

### Zur Methodenwahl

Machine Learning wurde geprüft und verworfen: Es gibt keine zu lernende Zielvariable und
keine historischen Planentscheidungen als Trainingsdaten. Das Problem ist eine Zuordnung
unter harten Nebenbedingungen mit mehreren konkurrierenden Zielen — dafür sind
mathematische Optimierung und Constraint Programming die einschlägigen Verfahren
(Burke et al. 2004; Van den Bergh et al. 2013). Umgesetzt ist ein MILP; ein
CP-SAT-Modell wäre eine gleichwertige Alternative.

---

## 2. Ergebnisse

| Szenario | Verfahren | Rechenzeit | Besetzungsquote | offene Dienste | Untergrenzen­verstöße | harte Regel­verstöße | weiche Abweichungen | Streuung Auslastung | Spanne Auslastung | Planstabilität | geänderte Zuweisungen |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S0 | Regelbasiert | 0,5 s | 100,0 % | 0 | 0 | 0 | 17 | 0,040 | 18,9 % | Referenz | – |
| S0 | MILP | 6,2 s | 100,0 % | 0 | 0 | 0 | **0** | **0,017** | **9,1 %** | Referenz | – |
| S1 | Regelbasiert | 0,5 s | 100,0 % | 0 | 0 | 0 | 17 | 0,039 | 18,9 % | 38,9 % | 223 |
| S1 | MILP (Neuplanung) | 3,6 s | 100,0 % | 0 | 0 | 0 | 0 | 0,017 | 9,1 % | 29,3 % | 266 |
| S1 | MILP (reaktiv) | 0,2 s | 100,0 % | 0 | 0 | 0 | 2 | 0,074 | 30,4 % | **93,3 %** | **20** |
| S2 | Regelbasiert | 0,5 s | 100,0 % | 0 | 0 | 0 | 16 | 0,055 | 25,3 % | 32,9 % | 251 |
| S2 | MILP (Neuplanung) | 7,4 s | 100,0 % | 0 | 0 | 0 | 0 | 0,020 | 9,1 % | 21,7 % | 307 |
| S2 | MILP (reaktiv) | 0,3 s | 100,0 % | 0 | 0 | 0 | 2 | 0,038 | 15,8 % | **94,0 %** | **18** |

Kennzahlen: *Streuung* = Standardabweichung der individuellen Auslastung (Ist-Stunden zur
verfügbaren Sollzeit), *Spanne* = Abstand zwischen der am geringsten und der am stärksten
ausgelasteten Person, *Planstabilität* = Anteil der (Person, Tag)-Zuweisungen, die
gegenüber dem Referenzplan unverändert bleiben.

---

## 3. Was die Zahlen zeigen

**Der Unterschied liegt nicht in der Besetzung.** Beide Verfahren erreichen in allen
Szenarien 100 % Besetzungsquote, null Untergrenzenverstöße und null harte
Regelverstöße. Das war nicht selbstverständlich, ist aber erklärbar: Der Datensatz ist
so dimensioniert, dass der Bedarf rund 90 % der verfügbaren Kapazität bindet — knapp,
aber lösbar. **Für die Hausarbeit ist das ein Ergebnis, kein Fehlschlag:** Wenn die
Besetzung ohnehin gelingt, ist die Frage nach dem Mehrwert einer Optimierung eine Frage
nach *Planqualität*, nicht nach *Machbarkeit*.

**Der Unterschied liegt in der Verteilung.** Die Streuung der Auslastung sinkt von 0,040
auf 0,017, die Spanne zwischen der am wenigsten und der am stärksten belasteten Person
von 18,9 auf 9,1 Prozentpunkte. Die 17 Überschreitungen des Wochenend-Richtwerts der
Baseline verschwinden vollständig. Die Heuristik entscheidet lokal optimal und
produziert dadurch systematisch Ungleichverteilung; das Modell sieht alle 28 Tage und
kann eine heute ungünstige Zuweisung in Kauf nehmen.

**Der größte Effekt betrifft die Umplanung.** Eine vollständige Neuplanung nach Ausfällen
zerstört den Plan: 223 bis 307 geänderte Zuweisungen, Planstabilität zwischen 22 und
39 %. Für die Mitarbeitenden bedeutet das einen komplett neuen Dienstplan wegen einiger
weniger Ausfälle. Die reaktive Variante — bestehender Plan als Ausgangspunkt, Änderungen
werden bestraft — kommt mit **18 bis 20 Änderungen** aus und hält 93 bis 94 %
Planstabilität, bei unveränderter Besetzungsquote und in **0,2 Sekunden**.

**Der Preis dafür ist sichtbar.** Der reaktive Plan hat eine schlechtere Lastverteilung
(Streuung 0,074 bzw. 0,038 statt 0,017) und zwei weiche Abweichungen. Das ist kein
Mangel, sondern der Zielkonflikt selbst: Stabilität gegen Gleichverteilung. Der
Prototyp macht ihn messbar, statt ihn zu verstecken.

**Rechenzeit.** 3,6 bis 7,4 Sekunden für einen kompletten 28-Tage-Plan, 0,2 bis 0,3
Sekunden für eine Umplanung. Beides ist für den Einsatzzweck unkritisch.

---

## 4. Grenzen dieser Messung

1. **Eine Instanz, ein Seed.** Alle Zahlen stammen aus genau einem Datensatz. Für
   belastbare Aussagen müssten mehrere Instanzen mit unterschiedlichen Seeds gerechnet
   und die KPIs gemittelt werden. Der Generator ist dafür vorbereitet.
2. **Die Gewichte der Zielfunktion sind gesetzt, nicht hergeleitet.** Wie stark
   Unterbesetzung gegen Lastverteilung gegen Wunscherfüllung zählt, ist eine
   Managemententscheidung. Andere Gewichte liefern andere Pläne.
3. **Der Solver stoppt bei 1 % Optimalitätslücke.** Die Lösungen sind nachweislich
   nahezu optimal, aber nicht garantiert optimal, und bei mehrfachem Lauf kann eine
   andere gleichwertige Lösung herauskommen.
4. **Die Baseline ist eine programmierte Heuristik, kein echter Mensch mit Excel.** Sie
   ist konsistenter und schneller als manuelle Planung. Die gemessene Zeitersparnis
   unterschätzt daher den realen Unterschied vermutlich deutlich — belegen lässt sich
   das mit diesem Aufbau aber nicht.
5. **Kein Vergleich mit einem realen Dienstplan.** Der Datensatz ist synthetisch; die
   absolute Höhe der Kennzahlen ist nicht auf eine konkrete Station übertragbar. Der
   *Vergleich zweier Verfahren auf identischer Datenbasis* bleibt gültig.

---

## 5. Business Impact: gemessen und geschätzt

**Gemessen** (gilt für diese Instanz): gleichmäßigere Lastverteilung bei gleicher
Besetzung; vollständige Einhaltung der Wochenend-Richtwerte; 18–20 statt 223–307
Planänderungen nach Ausfällen; Umplanung in unter einer Sekunde.

**Nicht gemessen, nur plausibel** (und in der Hausarbeit als Schätzung zu kennzeichnen):
Reduktion des manuellen Planungsaufwands, Wirkung gleichmäßigerer Belastung auf
Zufriedenheit und Fluktuation, wirtschaftliche Effekte durch weniger Überstunden.
Solche Aussagen erfordern eine Erhebung im Betrieb, keine Simulation.

Ein Punkt verdient betriebswirtschaftlich besondere Aufmerksamkeit: Planstabilität ist
kein Selbstzweck. Jede kurzfristige Planänderung bedeutet für die betroffene Person eine
Umstellung privater Planung. Ein Verfahren, das bei gleicher Versorgungsqualität mit
einem Zehntel der Änderungen auskommt, wirkt genau dort, wo in der Pflege die Belastung
entsteht — und das ist über die reine Besetzungsquote nicht sichtbar.

---

## Quellen

- Burke, E. K., De Causmaecker, P., Vanden Berghe, G., & Van Landeghem, H. (2004). The State of the Art of Nurse Rostering. *Journal of Scheduling*, 7(6), 441–499.
- Van den Bergh, J., Beliën, J., De Bruecker, P., Demeulemeester, E., & De Boeck, L. (2013). Personnel scheduling: A literature review. *European Journal of Operational Research*, 226(3), 367–385.
- Wickert, T. I., Smet, P., & Vanden Berghe, G. The nurse rerostering problem: Strategies for reconstructing disrupted schedules. *Computers & Operations Research*.
- HiGHS-Solver über `scipy.optimize.milp` — <https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html>

Rechtsgrundlagen und Datenherkunft: siehe `DATENKONZEPT.md`.
