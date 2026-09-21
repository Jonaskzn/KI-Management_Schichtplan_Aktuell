# Evaluation: regelbasierte Planung vs. MILP-Optimierung

**Versuchsaufbau:** 15 Instanzen (5 Seeds × 3 Personaldecken) × 3 Ausfallszenarien ×
6 Verfahrensvarianten = **270 Pläne**
**Station:** Innere Medizin / Kardiologie, 30 Betten, 28 Planungstage, 28 Tage Historie
**Reproduktion:** `python campaign.py` (ca. 15 Min.), alle Kennzahlen dieses Dokuments `python auswertung.py`
**Rohdaten:** `evaluation_results.csv` (270 Zeilen, eine je Plan)

Alle Zahlen sind **gemessene Ergebnisse des Prototyps**. Was daraus für den Business Impact
folgt und was nicht, steht in Abschnitt 8.

> **Fassung mit Krankheitsgutschrift.** Krankheitsbedingt ausgefallene Dienste werden seit
> dieser Fassung nach dem Entgeltausfallprinzip gutgeschrieben (§ 4 Abs. 1 EFZG). Die
> Szenarien S1 und S2 sind vollständig neu gerechnet, S0 ist unverändert. Mehrere Aussagen
> der vorigen Fassung halten der Korrektur nicht stand — sie sind in Abschnitt 3.2 einzeln
> benannt. Außerdem beziehen sich Planstabilität und geänderte Zuweisungen jetzt
> durchgängig auf die **gestörten** Pläne (S1, S2); in S0 gibt es nichts anzupassen, und
> die 100 % dieser Pläne hatten die Mittelwerte zuvor verdünnt.

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

### 2.1 Was die Kennzahlen bedeuten

Der Unterschied zwischen **harten** und **weichen** Verstößen entscheidet, wie die Tabellen
zu lesen sind. `evaluate()` unterscheidet drei Klassen:

| Klasse | Was zählt hinein | Grundlage | Bedeutung |
|---|---|---|---|
| **Untergrenzenverstöße** | Schicht unter der Pflegepersonaluntergrenze besetzt | PpUGV § 6 + Anlage | eigene Kennzahl, weil nach § 137i SGB V sanktionsbewehrt |
| **harte Regelverstöße** | Ruhezeit < 11 h · mehr als 5 Dienste in Folge · Arbeitszeit über Vertragsobergrenze (einschließlich Krankheitsgutschrift) · Fachkraftquote unterschritten · Hilfskraftanteil über 10 % · Nachtdienst ohne Nachtdiensteignung | ArbZG §§ 5, 6 · TVöD-K § 6 · PpUGV § 2 | **Ein Plan mit harten Verstößen ist nicht einsetzbar.** |
| **weiche Abweichungen** | mehr als 2 Wochenenden im Dienst je 4 Wochen · mehr als 8 Nachtdienste je 4 Wochen | Annahme A10, arbeitswissenschaftlich gestützt, im Gesetz nicht beziffert | zulässig, aber unerwünscht — Belastungsschutz, nicht Legalität |

Weiche Abweichungen sind also **keine Rechtsverstöße**. Sie messen, wie fair und
belastungsschonend ein Plan ist. Genau deshalb sind sie für Personalbindung und
Zufriedenheit die interessantere Größe: Zwei Pläne mit identischer Besetzungsquote und null
Rechtsverstößen können sich für die Mitarbeitenden völlig unterschiedlich anfühlen.

Zwei weitere Kennzahlen brauchen eine Definition:

- **Auslastung** ist gearbeitete Zeit plus Krankheitsgutschrift, geteilt durch die im
  Horizont verfügbare Sollzeit. Die **Spanne** ist der Abstand zwischen der am geringsten
  und der am stärksten ausgelasteten Person, die **Streuung** die Standardabweichung. Ohne
  die Gutschrift erschiene jede kranke Person als unterausgelastet (Abschnitt 3.2).
- **Offene Dienste** sind Dienste unterhalb der **fachlichen Sollbesetzung**. Sie sind kein
  Rechtsverstoß, solange die gesetzliche Untergrenze gehalten ist — die Sollbesetzung
  liegt aus dem Pflegeaufwand darüber (Datenkonzept, Abschnitt 4.5).

### 2.2 Ergebnisse

Mittelwerte über 5 Seeds × 3 Szenarien (15 Pläne je Zelle), ± Standardabweichung.
Planstabilität über die 10 gestörten Pläne je Zelle (S1, S2).

### Bedarfsgerechte Besetzung (100 %, Ø 22 Köpfe)

| Kennzahl | Greedy | Greedy reaktiv | MILP | MILP reaktiv |
|---|---|---|---|---|
| Besetzungsquote | 99,9 % | 100,0 % | 100,0 % | 100,0 % |
| Untergrenzenverstöße | 0,07 ± 0,26 | 0,00 | **0,00** | **0,00** |
| harte Regelverstöße | 0,07 ± 0,26 | 0,07 ± 0,26 | **0,00** | **0,00** |
| weiche Abweichungen | 16,1 ± 1,5 | 16,0 ± 1,2 | **0,0 ± 0,0** | 0,9 ± 0,9 |
| Streuung Auslastung | 0,069 ± 0,015 | 0,079 ± 0,014 | **0,011 ± 0,003** | 0,035 ± 0,017 |
| Planstabilität (eigener Ausgangsplan, S1/S2) | 44,9 % | 91,7 % | 19,8 % | 92,9 % |
| Planungszeit | 0,43 s | 0,36 s | 7,65 s | 0,40 s |

### Knappe Besetzung (90 %, Ø 20 Köpfe)

| Kennzahl | Greedy | Greedy reaktiv | MILP | MILP reaktiv |
|---|---|---|---|---|
| Besetzungsquote | 99,5 % | 99,2 % | **100,0 %** | **100,0 %** |
| Untergrenzenverstöße | 0,67 ± 1,18 | 0,87 ± 1,19 | **0,00** | **0,00** |
| harte Regelverstöße | 0,40 ± 0,63 | 0,73 ± 0,80 | **0,00** | **0,00** |
| weiche Abweichungen | 15,4 ± 1,7 | 14,7 ± 1,9 | **0,2 ± 0,4** | 1,6 ± 1,7 |
| Streuung Auslastung | 0,060 ± 0,043 | 0,063 ± 0,038 | **0,015 ± 0,003** | 0,032 ± 0,015 |
| Planstabilität (eigener Ausgangsplan, S1/S2) | 54,4 % | 89,6 % | 24,6 % | 93,8 % |
| Planungszeit | 0,38 s | 0,32 s | 13,34 s | 0,42 s |

### Unterbesetzt (80 %, Ø 18 Köpfe)

| Kennzahl | Greedy | Greedy reaktiv | MILP | MILP reaktiv |
|---|---|---|---|---|
| Besetzungsquote | 93,9 % | 93,9 % | **99,7 %** | 99,3 % |
| Untergrenzenverstöße | 6,53 ± 2,45 | 6,13 ± 2,45 | **0,00** | **0,00** |
| harte Regelverstöße | 0,67 ± 0,90 | 0,67 ± 0,72 | **0,00** | **0,00** |
| weiche Abweichungen | 16,5 ± 1,6 | 16,5 ± 2,3 | **3,7 ± 1,3** | 4,9 ± 1,9 |
| Streuung Auslastung | **0,083 ± 0,018** | 0,084 ± 0,014 | 0,093 ± 0,039 | 0,095 ± 0,039 |
| Planstabilität (eigener Ausgangsplan, S1/S2) | 61,6 % | 88,3 % | 29,7 % | 90,4 % |
| Planungszeit | 0,34 s | 0,29 s | 14,68 ± 10,60 s | 1,56 s |

### Anteil vollständig regelkonformer Pläne

(keine harten Regelverstöße **und** keine Untergrenzenverstöße)

| Verfahren | 80 % | 90 % | 100 % |
|---|---|---|---|
| Greedy | **0 %** | 53 % | 93 % |
| Greedy reaktiv | **0 %** | 40 % | 93 % |
| MILP | **100 %** | 100 % | 100 % |
| MILP reaktiv | **100 %** | 100 % | 100 % |

Über alle 135 Pläne der drei MILP-Varianten gibt es **keinen einzigen** harten Regelverstoß
und **keine** Unterschreitung der Pflegepersonaluntergrenze. Die Heuristik unterschreitet
die Untergrenze bei 80 % Decke 98-mal und lässt 113 Dienste unbesetzt.

**Offene Dienste gibt es jetzt auch bei der Optimierung** — in der vorigen Fassung waren es
null. Betroffen sind 18 der 135 MILP-Pläne mit zusammen 56 Diensten, ausnahmslos bei 80 %
Personaldecke und ausnahmslos in den Ausfallszenarien. Jeder dieser Dienste liegt unter der
fachlichen Sollbesetzung, aber **über** der gesetzlichen Untergrenze. Die Ursache ist die
Krankheitsgutschrift: Wer krank war, darf seine ausgefallenen Stunden nicht nacharbeiten, und
bei 80 % Decke reicht der Spielraum der übrigen Belegschaft nicht mehr für jeden Dienst. Die
frühere „vollständige Deckung" war zum Teil dadurch erkauft, dass Kranke ihre Dienste an
anderen Tagen nachholten (Abschnitt 3.2). Die Optimierung setzt die knappe Kapazität dort
ein, wo sie gesetzlich zwingend ist — an der Untergrenze —, und lässt die fachliche
Sollbesetzung dort offen, wo es nicht anders geht.

Bei 80 % Decke ist die Streuung der Auslastung bei der Heuristik jetzt geringfügig kleiner
als bei der Optimierung (0,083 gegen 0,093). Das ist kein Verteilungsvorteil: Die Heuristik
lässt dort 113 Dienste offen, die Optimierung 10 (Neuplanung). Ein unbesetzter Dienst
erzeugt keine Auslastung und drückt die Streuung künstlich (Abschnitt 4.4).

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
Instanz zwischen −3 und +7 Tagen schwankt. Dieser Rest wird in Abschnitt 3.3 ausdrücklich
kontrolliert.

| Kennzahl | S0 (Ausgangsplan) | S1 | S2 |
|---|---|---|---|
| Spanne — Regelbasiert, Neuplanung | 0,283 | 0,306 | 0,297 |
| Spanne — MILP, Neuplanung | **0,123** | **0,184** | **0,187** |
| Spanne — Regelbasiert, reaktiv | 0,283 | 0,333 | 0,317 |
| Spanne — MILP, reaktiv | **0,123** | **0,238** | **0,257** |
| offene Dienste — Regelbasiert, reaktiv | 2,00 | 3,27 | 4,60 |
| Untergrenzenverstöße — Regelbasiert, reaktiv | 1,80 | 2,47 | 2,73 |
| harte Regelverstöße — Regelbasiert, reaktiv | 0,33 | 0,40 | 0,73 |

Die Optimierung behält ihren Verteilungsvorteil unter beiden Ausfallszenarien und in beiden
Betriebsarten. Die reaktive Betriebsart kostet einen Teil davon — unter S2 steigt ihre
Spanne von 0,187 bei vollständiger Neuplanung auf 0,257. Das ist der Preis der Vorgabe,
den Plan möglichst unverändert zu lassen (Abschnitt 4.5). Die Heuristik verliert unter
Ausfällen dagegen vor allem an **Regelkonformität**: Offene Dienste, Untergrenzenverstöße
und harte Verstöße steigen von S0 über S1 zu S2. Bei der Optimierung bleiben
Untergrenzenverstöße und harte Verstöße in allen drei Szenarien bei null.

Planstabilität fehlt in dieser Tabelle bewusst — sie gehört in Abschnitt 4, weil sie nur
auf identischem Ausgangsplan zwischen den Verfahren aussagekräftig ist.

*Hinweis zur Reproduzierbarkeit:* 8 der 135 MILP-Läufe erreichen das Zeitlimit von 30 s,
bevor die geforderte Genauigkeit von 1 % belegt ist. Ihr Ergebnis hängt dann von der
Rechengeschwindigkeit ab. Im Vergleich zweier vollständiger Läufe wich genau eine Instanz ab
(Seed 20260906, 80 % Decke); dort liefern zwei unabhängige Lösungen des Referenzszenarios
unterschiedliche Pläne. Die Spalte S0 zeigt deshalb den tatsächlich verwendeten
Ausgangsplan. Alle übrigen Instanzen sind zwischen den Läufen identisch.

### 3.2 Eine Korrektur: Krankheit ist keine Unterauslastung

**Was falsch war.** Die vorige Fassung behandelte eine kranke Person so, als hätte sie an
den Ausfalltagen einfach nicht gearbeitet. Ihre Auslastung sank, und das Modell hielt sie für
unterausgelastet. Aufgefallen ist das bei der Prüfung der Priorität
„Verteilungsgerechtigkeit" in der Anwendung: Sie ließ unter S2 jede der sechs erkrankten
Personen ihre ausgefallenen Dienste an anderen Tagen **vollständig nacharbeiten** — PK-005
verlor zwei Dienste und bekam zwei zusätzliche, PK-007 drei und drei. Aus Sicht der
Kennzahl war das gerecht; tatsächlich war es unzulässig.

**Rechtslage.** Nach dem Entgeltausfallprinzip (§ 4 Abs. 1 EFZG) wird eine arbeitsunfähige
Person so gestellt, als hätte sie gearbeitet. Das BAG hat bestätigt, dass für
krankheitsbedingt ausgefallene, im Dienstplan vorgesehene Dienste eine Zeitgutschrift auf dem
Arbeitszeitkonto verlangt werden kann (BAG, Urteil vom 05.10.2023 – 6 AZR 210/22).
Tarifverträge dürfen davon in Grenzen abweichen (§ 4 Abs. 4 EFZG; BAG, 16.07.2014 –
10 AZR 242/13). Nacharbeiten muss niemand.

**Umsetzung.** Gutgeschrieben wird die Nettodauer des Dienstes, den die Person laut
**Ausgangsplan** an dem Ausfalltag gehabt hätte. Ein Ausfall an einem dienstfreien Tag
ergibt keine Gutschrift, weil keine Arbeitsleistung ausgefallen ist. Die Gutschrift zählt
wie gearbeitete Zeit — für die Auslastung, für die Zielarbeitszeit der Optimierung und für
die vertragliche Obergrenze. Für die Grenzen des Arbeitszeitgesetzes zählt sie nicht, weil
diese tatsächliche Arbeit begrenzen. Die Heuristik verbucht die Gutschrift an dem Tag, an dem
der Ausfall liegt; die Optimierung berücksichtigt sie über den ganzen Monat. `evaluate()`
berechnet sie unabhängig vom Planer selbst. Gesundheitsdaten braucht die Gutschrift nicht:
Sie knüpft allein an die Tatsache der Arbeitsunfähigkeit. Im Mittel werden je gestörtem Plan
75,5 Stunden gutgeschrieben.

**Was sich dadurch ändert** (Hauptstation, 15 Instanzen):

| Kennzahl | vorige Fassung | mit Gutschrift |
|---|---|---|
| Spanne unter S2, Regelbasiert reaktiv | 0,379 | 0,317 |
| Spanne unter S2, MILP reaktiv | 0,377 | **0,257** |
| Spanne unter S2, MILP Neuplanung | 0,163 | 0,187 |
| Spannendifferenz S2 − S1, volumenkontrolliert | +0,084 (6 von 6) | +0,008 (5 von 6) |
| offene Dienste der MILP-Varianten bei 80 % Decke | 0 | 56 (in 18 von 135 Plänen) |
| Untergrenzenverstöße Heuristik bei 80 % Decke, je Plan | 4,73 | 6,53 |
| Untergrenzenverstöße aller MILP-Varianten | 0 | 0 |
| Planstabilität S1/S2 End-to-End, Regelbasiert → MILP | 90,1 % → 92,5 % | 89,9 % → 92,4 % |

**Drei Aussagen der vorigen Fassung halten nicht mehr:**

1. *„Unter der Ausfallwelle liegen beide Verfahren bei der Lastverteilung gleichauf (0,377
   gegen 0,379)."* Das war ein Artefakt. S2 konzentriert die Ausfälle auf wenige Personen
   mit mehrtägigen Episoden; ohne Gutschrift erschienen genau diese als stark
   unterausgelastet, und zwar bei beiden Verfahren gleichermaßen. Mit Gutschrift liegt die
   Optimierung unter S2 deutlich vorn (0,257 gegen 0,317).
2. *„Eine gebündelte Ausfallwelle verschlechtert die Lastverteilung strukturell."* Der
   Befund (+0,084 in 6 von 6 volumenkontrollierten Instanzen) schrumpft auf +0,008. Er war
   dieselbe Verzerrung: Wer mehrere Tage am Stück fehlte, zog die Spanne nach unten.
3. *„Die Optimierung besetzt auch bei 80 % Decke jeden Dienst."* Das gelang zum Teil nur,
   weil Kranke ihre Dienste nachholten. Mit Gutschrift bleiben dort unter Ausfällen
   vereinzelt Dienste unter der fachlichen Sollbesetzung — die gesetzliche Untergrenze
   hält die Optimierung weiterhin in jedem Plan.

**Was hält:** Die Optimierung bleibt in allen 135 Plänen frei von harten Verstößen und
Untergrenzenverstößen, sie gewinnt den End-to-End-Vergleich auf jeder Kennzahl
(Abschnitt 4.1), und die reaktive Umplanung bleibt der größte Einzeleffekt auf die
Planstabilität. Die Korrektur verschlechtert beide Verfahren unter Knappheit, weil
Krankheit jetzt tatsächlich Kapazität kostet — die Heuristik stärker als die Optimierung.

### 3.3 Kontrolle für das Ausfallvolumen

Weil S2 über die Instanzen im Mittel 13,6 % mehr Ausfalltage trägt, wurde jede
Szenariodifferenz zusätzlich auf der Teilmenge der **6 Instanzen** geprüft, in denen S2
**nicht** mehr Ausfalltage hat als S1:

| Differenz S2 − S1 (MILP reaktiv) | alle 15 Instanzen | volumenkontrolliert (6) |
|---|---|---|
| Spanne der Auslastung | +0,019 (9 von 15) | +0,008 (5 von 6) |
| Planstabilität | −1,85 Pp. (10 von 15) | −0,10 Pp. (3 von 6) |

**Weder der Verteilungs- noch der Stabilitätseffekt ist ein belegbarer Struktureffekt.**
Beide sind über alle Instanzen klein und schrumpfen unter Volumenkontrolle gegen null. Die
Stabilitätsdifferenz folgt dem Volumen (Korrelation zwischen Volumen- und
Stabilitätsdifferenz −0,39). Das folgt direkt aus der Definition: Planstabilität ist der
Anteil unveränderter Zuweisungen, und jeder Ausfalltag, der einen geplanten Dienst trifft,
erzwingt eine Änderung. **Planstabilität misst primär die Menge der Störung, nicht ihre
Konzentration.**

Bei der Heuristik zeigt sich in der volumenkontrollierten Teilmenge eine Richtung — harte
Verstöße 0,17 → 0,33, offene Dienste 1,33 → 1,67 von S1 zu S2 —, die Fallzahl ist jedoch zu
klein und die Werte sind zu nah an null, um darauf eine Aussage zu stützen.

**Konsequenz für die Interpretation.** Die beiden Szenarien erfüllen ihren Zweck: Sie
belasten beide Verfahren mit zwei strukturell verschiedenen Störungsmustern, und die
Rangfolge der Verfahren ist unter beiden dieselbe. Einen eigenständigen Effekt der
**Struktur** — Welle gegen verteilte Einzelausfälle — weist diese Kampagne dagegen nicht
nach, weder für die Lastverteilung noch für die Planstabilität. Die vorige Fassung hatte
einen solchen Effekt für die Lastverteilung behauptet; er ging auf die fehlende
Krankheitsgutschrift zurück (Abschnitt 3.2).

### 3.4 Eine zurückgenommene Beobachtung

Die vorige Fassung berichtete, die Untergrenzenverstöße der Heuristik lägen unter S1 knapp
*unter* denen von S0, und deutete das als Nicht-Monotonie der greedy Auswahl. Mit
Gutschrift tritt das nicht mehr auf: 1,80 unter S0, 2,53 unter S1, 2,93 unter S2 bei der
Neuplanung. Da die Gutschrift die einzige Änderung an der Heuristik ist, war die Beobachtung
eine Folge der fehlenden Gutschrift — naheliegend, weil Kranke nach ihrer Rückkehr als
unterausgelastet galten und deshalb bevorzugt eingeteilt wurden. Sie wird zurückgenommen.

---

## 4. Planstabilität: welcher Vergleich welche Frage beantwortet

### 4.1 Der End-to-End-Vergleich — die Antwort auf die Leitfrage

Die Leitfrage fragt nach „Erstellung **und** kurzfristiger Anpassung" — also nach einer
**Kette aus zwei Schritten**, nicht nach einem isolierten Reparaturalgorithmus. In der
Excel-Welt erstellt die Heuristik den Monatsplan und passt ihn an; in der KI-Welt macht das
die Optimierung. Beide arbeiten dabei auf **demselben Datensatz**: derselben Belegschaft,
denselben Bedarfs- und Regelspalten, denselben Ausfallszenarien. Was sich unterscheidet, ist
allein das Verfahren. Jedes tut also, was es real täte. Gemessen wird der Zustand nach
Erstellung **und** Anpassung, also über die 30 gestörten Pläne je Verfahren (S1, S2):

| Kennzahl (Mittel über 30 gestörte Pläne) | Regelbasiert | MILP | |
|---|---|---|---|
| Planstabilität | 89,9 % | **92,4 %** | ✓ |
| geänderte Zuweisungen je Plan | 30,3 | **22,8** | ✓ |
| Besetzungsquote | 97,3 % | **99,7 %** | ✓ |
| offene Dienste | 3,93 | **0,77** | ✓ |
| Untergrenzenverstöße | 2,60 | **0,00** | ✓ |
| harte Regelverstöße | 0,57 | **0,00** | ✓ |
| weiche Abweichungen | 15,5 | **3,17** | ✓ |
| Spanne der Auslastung | 0,325 | **0,247** | ✓ |

**Die Optimierung gewinnt jede einzelne Kennzahl.** Entscheidend ist, dass Planstabilität
und absolute Änderungszahl **in dieselbe Richtung** zeigen: 92,4 % gegen 89,9 % bei
gleichzeitig 22,8 gegen 30,3 geänderten Diensten. Ginge nur der Prozentwert zugunsten der
Optimierung aus, wäre der Einwand berechtigt, die beiden Werte bezögen sich auf
unterschiedliche Ausgangspläne. Da auch die absolute Zahl geänderter Dienste niedriger ist,
trägt die Aussage: **Die Mitarbeitenden erleben in der KI-Welt rund ein Viertel weniger
Planänderungen.**

Auf Einzelplanebene ist die Optimierung in 23 der 30 gestörten Pläne stabiler (77 %) — nicht
in allen. Die Aussage gilt im Mittel, nicht in jeder Instanz.

### 4.2 Die Methodenkontrolle — reparieren beide denselben Plan

Der End-to-End-Vergleich misst die Planstabilität gegen zwei unterschiedlich gute
Ausgangspläne:

| Ausgangsplan (Szenario S0) | weiche Abweichungen | Spanne | offene Dienste |
|---|---|---|---|
| der Heuristik | 16,1 | 0,283 | 2,00 |
| der Optimierung | **1,1** | **0,123** | **0,00** |

Einen schwachen Plan unverändert zu lassen ist billig — es gibt nichts zu verteidigen.
Deshalb prüft die Kampagne zusätzlich, was passiert, wenn **beide Verfahren denselben Plan
reparieren** (je 30 gestörte Pläne).

**Auf dem Plan der Optimierung:**

| Kennzahl | Regelbasiert repariert | MILP repariert |
|---|---|---|
| Planstabilität | 88,2 % | **92,4 %** |
| geänderte Zuweisungen | 36,0 | **22,8** |
| offene Dienste | 1,67 | **0,77** |
| Untergrenzenverstöße | 0,83 | **0,00** |
| harte Regelverstöße | 0,17 | **0,00** |
| weiche Abweichungen | 6,23 | **3,17** |
| Spanne der Auslastung | **0,230** | 0,247 |

Die Optimierung ist in **29 von 30** gestörten Plänen stabiler und gewinnt jede Kennzahl bis
auf eine: die Spanne. Dort liegt die Heuristik knapp vorn. Zwei Gründe, beide gemessen:
Die Heuristik lässt mehr als doppelt so viele Dienste offen (1,67 gegen 0,77), und ein
unbesetzter Dienst drückt die Spanne (Abschnitt 4.4). Und ihre einzige Auswahlregel —
„die am wenigsten ausgelastete Person zuerst" — ist genau eine Lastausgleichsregel, während
die Optimierung Lastausgleich im Standardaufbau kaum gewichtet (Abschnitt 4.5). Der
End-to-End-Befund ist also kein Artefakt der Ausgangspläne; auf der Lastverteilung ist der
Vorsprung der Optimierung aber an ihren eigenen Ausgangsplan gebunden.

**Auf dem Plan der Heuristik:**

| Kennzahl | Regelbasiert repariert | MILP repariert |
|---|---|---|
| Planstabilität | **89,9 %** | 88,6 % |
| geänderte Zuweisungen | **30,3** | 34,8 |
| offene Dienste | 3,93 | **0,77** |
| Untergrenzenverstöße | 2,60 | **0,00** |
| harte Regelverstöße | 0,57 | **0,00** |
| weiche Abweichungen | 15,5 | **15,0** |
| Spanne der Auslastung | **0,325** | 0,334 |

Hier ändert die Optimierung **mehr**. Das ist kein Qualitätsmangel, sondern eine logische
Folge: Die 3,93 unbesetzten Dienste und 2,60 Untergrenzenverstöße im geerbten Plan lassen
sich nur beheben, **indem** Zuweisungen geändert werden. Ein Verfahren, das sie stehen
lässt, gewinnt die Stabilitätskennzahl durch Untätigkeit. Wer einen schlechten Plan erbt,
muss ihn anfassen, um ihn rechtskonform zu machen.

### 4.3 Alle vier Kombinationen — warum der Vorteil systemisch ist

Kreuzt man beide Ausgangspläne mit beiden Reparaturverfahren, ergibt sich ein Bild, das
weder dem einen noch dem anderen Schritt allein zuzuschreiben ist. Geänderte Zuweisungen je
gestörtem Plan:

| | repariert von der Heuristik | repariert von der Optimierung |
|---|---|---|
| **Ausgangsplan der Heuristik** | 30,3 | 34,8 |
| **Ausgangsplan der Optimierung** | 36,0 | **22,8** |

Zwei Ablesungen:

**Zeilenweise** ändert die Optimierung auf dem geerbten Plan der Heuristik mehr als die
Heuristik selbst. Das ist zwingend und kein Tuning-Problem: Ein Plan mit offenen Diensten und
Regelverstößen wird nur dadurch rechtskonform, dass Zuweisungen geändert werden.

**Diagonal** zeigt sich der eigentliche Befund: Nur die Kombination „Optimierung plant und
Optimierung repariert" erreicht 22,8. Ein guter Plan, von der Heuristik repariert, kostet
mit 36,0 Änderungen **mehr** als der schwache Plan der Heuristik in ihrer eigenen Hand
(30,3) — weil ein dicht gepackter Plan ohne Slack von einer lokal entscheidenden Heuristik
nicht effizient repariert werden kann. Der Vorteil steckt also **weder in der Planung noch
in der Anpassung allein, sondern im Zusammenspiel**: Die Optimierung baut einen Plan, der
Spielraum an den richtigen Stellen lässt, und weiß zugleich, wie sie ihn nutzt.

Betriebswirtschaftlich ist das die relevante Aussage: Ein Optimierer, der nur als
Feuerwehr auf bestehende Excel-Pläne gesetzt wird, hebt einen Teil des Nutzens — die
Rechtskonformität —, aber nicht den Effizienzvorteil. Der entsteht erst, wenn auch die
Monatsplanung aus dem System kommt.

### 4.4 Warum die Optimierung auf dem fremden Plan bei der Lastverteilung nicht gewinnt

Repariert die Optimierung den Plan der Heuristik, liegt ihre Spanne mit 0,323 über der der
Heuristik (0,311; alle 45 Pläne). Teilt man die Pläne danach auf, ob die Heuristik überhaupt
Lücken lässt, löst sich das auf:

| Teilmenge | Spanne Regelbasiert | Spanne MILP | offene Dienste (Regelbasiert) |
|---|---|---|---|
| Heuristik besetzt vollständig (19 Pläne) | 0,314 | **0,278** | 0,00 |
| Heuristik lässt Lücken (26 Pläne) | **0,309** | 0,356 | 5,69 |

**Wo beide dieselbe Arbeit verteilen, verteilt die Optimierung sie besser.** Der Rückstand
im Mittel entsteht vollständig dort, wo die Optimierung **zusätzlich 5,69 Dienste besetzt**,
die die Heuristik offen lässt. Diese Arbeit muss jemand übernehmen, und das hebt die
Spitzenauslastung. Insoweit „gewinnt" die Heuristik diese Kennzahl, indem sie die Arbeit
nicht tut. In den gestörten Plänen ohne Deckungsunterschied ist die Optimierung unter S1 in
5 von 6 Fällen besser (im Mittel −0,090), unter S2 in 1 von 5 (im Mittel dennoch −0,027) —
bei so wenigen Fällen ohne klare Richtung.

Die vorige Fassung hatte hier eine zweite, systematische Ursache ausgemacht („unter S2 in 5
von 5 Fällen schlechter"). Sie ging auf die fehlende Krankheitsgutschrift zurück und entfällt
(Abschnitt 3.2).

Warum die Optimierung auf dem fremden Plan nicht **stärker** umverteilt, bleibt eine Frage
der Gewichtung: `keep` = 200 je beibehaltener Zuweisung steht gegen `fair` = 0,02 je Minute
Abweichung von der Zielarbeitszeit. Eine Person um 500 Minuten besser auszulasten ist damit
10 Punkte wert; eine einzige Zuweisung aufzubrechen kostet 200. Das Modell verzichtet also
**rational** auf Umverteilung.

### 4.5 Sensitivitätsanalyse: was das Gewicht „beibehalten" kostet

Wie stark die Lastverteilung an der Gewichtung hängt, lässt sich messen. Die folgende
Analyse variiert allein `keep` und lässt alles andere unverändert (Szenario S2,
bedarfsgerechte Personaldecke, 5 Seeds, Ausgangsplan der Heuristik; Skript
`sensitivitaet.py`):

| Verfahren | Spanne | Planstabilität | Änderungen | weiche Abweichungen |
|---|---|---|---|---|
| Regelbasiert (Referenz) | 0,379 | 91,8 % | 25,0 | 16,0 |
| MILP, `keep` = 200 *(Standard)* | 0,344 | **93,7 %** | **18,8** | 15,6 |
| MILP, `keep` = 50 | 0,348 | 93,4 % | 20,0 | 15,2 |
| MILP, `keep` = 20 | 0,164 | 80,6 % | 62,0 | 2,8 |
| MILP, `keep` = 5 | 0,076 | 68,3 % | 108,2 | 0,2 |
| MILP, `keep` = 0 | **0,042** | 15,6 % | 351,0 | **0,0** |

Bei bedarfsgerechter Decke liegt die Optimierung schon im Standardaufbau auf dem Plan der
Heuristik vorn — bei der Spanne (0,344 gegen 0,379) wie bei der Stabilität (93,7 % gegen
91,8 %). Den geerbten Plan gleicht sie dabei aber kaum aus: Er startet mit einer Spanne von
0,326. Erst bei `keep` = 20 beginnt sie umzuverteilen und räumt die weichen Abweichungen
weitgehend ab; bei `keep` = 5 erreicht sie eine Spanne von 0,076 — ein Fünftel des Werts der
Heuristik.

Der Preis ist ebenso klar: Bei `keep` = 5 sinkt die Planstabilität von 93,7 % auf 68,3 %,
die Zahl geänderter Dienste steigt von 18,8 auf 108. Für die Mitarbeitenden bedeutet das den
Unterschied zwischen zwanzig und über hundert Umstellungen im Monat.

Bemerkenswert ist die **Schwelle**: Zwischen `keep` = 50 und `keep` = 20 kippt das Verhalten
abrupt von „Lücken füllen" zu „Monat umverteilen". Dazwischen gibt es kaum einen sanften
Übergang.

**Die zweite Stellschraube ist besser dosierbar.** Statt `keep` zu senken, lässt sich
`fair` anheben — das Gewicht je Minute Abweichung von der Zielarbeitszeit. Dieselben
Instanzen, `keep` konstant bei 200:

| Konfiguration | Spanne | Planstabilität | Änderungen |
|---|---|---|---|
| Regelbasiert (Referenz) | 0,379 | 91,8 % | 25,0 |
| MILP, `fair` = 0,02 *(Standard)* | 0,344 | **93,7 %** | **18,8** |
| MILP, `fair` = 0,1 | 0,170 | 92,7 % | 22,2 |
| MILP, `fair` = 0,3 | 0,156 | 92,2 % | 23,8 |
| MILP, `fair` = 1,0 | 0,075 | 91,0 % | 27,4 |
| MILP, `fair` = 3,0 | **0,066** | 89,7 % | 31,6 |

Bei `fair` = 0,1 erreicht die Optimierung **weniger als die halbe Spanne der Heuristik
(0,170 gegen 0,379) bei höherer Planstabilität** (92,7 % gegen 91,8 %) und weniger
Änderungen (22,2 gegen 25,0). Erst ab `fair` = 1,0 fällt die Stabilität unter die der
Heuristik. Die Reihe ist monoton: Jede Stufe mehr Lastausgleich kostet etwas Stabilität und
bringt eine gleichmäßigere Last. Der Zielkonflikt ist damit **stetig und dosierbar**, keine
Entweder-oder-Entscheidung.

Warum der Standard trotzdem bei 0,02 bleibt: Die veröffentlichten Kampagnenzahlen sind mit
diesem Wert gerechnet, und eine Gewichtsänderung nach Sichtung der Ergebnisse wäre
ergebnisgetriebenes Tuning. Stattdessen macht der Prototyp die Wahl **explizit**: Die
Anwendung bietet die drei Stufen „Planungsruhe" (0,02), „Ausgewogen" (0,1) und
„Verteilungsgerechtigkeit" (1,0) zur Auswahl an. Die Entscheidung gehört ohnehin nicht in
eine Konfigurationsdatei, sondern auf die Leitungsebene.

**Konsequenz für die Interpretation.** Die Spanne der reaktiven Optimierung darf nicht als
Leistungsgrenze gelesen werden. Sie ist die Folge eines Gewichts, das Lastausgleich fast
nichts wert sein lässt — ein Kalibrierungsbefund, kein Verfahrensbefund. Genau das ist der
methodische Kern: Ein Optimierer tut, was in der Zielfunktion steht, nicht was man sich
davon erhofft.

*Zur Einordnung gegenüber der vorigen Fassung:* Dort lag die Optimierung in dieser Analyse
im Standardaufbau bei der Spanne **hinter** der Heuristik (0,478 gegen 0,391). Auch das war
eine Folge der fehlenden Krankheitsgutschrift (Abschnitt 3.2).

### 4.6 Was daraus folgt

Erbt die Optimierung einen Plan **mit** Mängeln — offenen Diensten, Untergrenzenverstößen —,
kann sie nicht auf allen Kennzahlen gleichzeitig gewinnen: „möglichst wenig ändern" und
„Mängel beheben" sind dann unvereinbare Ziele. Das ist über alle Personaldecken hinweg der
Fall (Abschnitt 4.2). Hat der geerbte Plan kaum Mängel, wie bei bedarfsgerechter Decke,
gelingt es: Dort liegt sie selbst auf dem Plan der Heuristik bei Spanne, Stabilität und
Änderungszahl vorn (Abschnitt 4.5). Die Grenze ist also keine Schwäche des Verfahrens,
sondern eine Eigenschaft der Kennzahl: **Planstabilität misst Zurückhaltung, nicht
Qualität.**

Für die Arbeit folgt daraus eine klare Ordnung:

1. **Hauptaussage ist der End-to-End-Vergleich** (4.1). Er beantwortet die Leitfrage, und
   die Optimierung gewinnt dort jede Kennzahl.
2. **Belegt wird er durch die Methodenkontrolle auf dem Plan der Optimierung** (4.2). Sie
   zeigt, dass der Vorsprung bei Planstabilität, Deckung und Regelkonformität nicht an
   unterschiedlichen Ausgangsplänen hängt. Bei der Lastverteilung hängt er daran — auf
   demselben Plan liegt die Heuristik knapp vorn, weil sie mehr Dienste offen lässt.
3. **Die Vier-Felder-Tafel (4.3) trägt den Wirkmechanismus**: Der Effizienzvorteil ist
   systemisch und entsteht erst, wenn Planung und Anpassung aus derselben Hand kommen.
4. **Wo die Optimierung auf einer Kennzahl zurückliegt, liegt es an Deckung oder
   Gewichtung** (4.4, 4.5) — nicht am Verfahren. Beides ist gemessen und einstellbar.
5. **Der Migrationsfall — Optimierung erbt einen Excel-Plan — gehört in die Diskussion**,
   nicht in die Ergebnistabelle: Wer umsteigt, muss im ersten Monat mit mehr Änderungen
   rechnen, weil Altlasten mitbehoben werden.
6. **Jede Stabilitätsangabe nennt ihren Ausgangsplan.** Unsere erste Auswertung tat das
   nicht und war dadurch nicht interpretierbar.

---

## 5. Was die Kampagne beantwortet

**Der Gleichstand aus der Einzelmessung war instanzabhängig.** Bei bedarfsgerechter
Besetzung erreichen beide Verfahren nahezu die Sollbesetzung. Sobald die Personaldecke
sinkt, trennen sich die Verfahren deutlich.

**Unter Knappheit sichert nur die Optimierung die gesetzliche Untergrenze.** Bei 80 %
Personaldecke unterschreitet die Heuristik die Pflegepersonaluntergrenze im Mittel 6,5-mal
je Plan und lässt insgesamt 113 Dienste unbesetzt; die Optimierung kommt auf null
Untergrenzenverstöße über alle 15 Pläne hinweg und lässt 10 Dienste unter der fachlichen
Sollbesetzung, keinen unter der Untergrenze. **Kein einziger Greedy-Plan bei 80 % war
vollständig regelkonform, 100 % der MILP-Pläne waren es.** Das ist das betriebswirtschaftlich
relevanteste Ergebnis: Der Mehrwert der Optimierung entsteht nicht im Normalbetrieb, sondern
genau dort, wo es eng wird.

**Die Verteilungswirkung ist groß — solange Stabilität nicht vorrangig ist.** Bei
bedarfsgerechter Besetzung sinkt die Streuung der individuellen Auslastung von 0,069 auf
0,011, die Spanne zwischen der am geringsten und der am stärksten ausgelasteten Person von
33 auf 5 Prozentpunkte, und alle 16,1 Überschreitungen der Wochenend- und
Nachtdienst-Richtwerte je Plan entfallen.

Am greifbarsten wird das bei den Wochenenddiensten. **95,5 % aller weichen Abweichungen der
Heuristik sind Wochenend-Überschreitungen** — die Nachtdienst-Richtwerte spielen praktisch
keine Rolle. Über alle 15 Instanzen und 608 Personenpläne verteilt sich die Wochenendarbeit
so:

| Wochenenden im Dienst je Monat | Regelbasiert | MILP |
|---|---|---|
| keines | 4,9 % | 4,9 % |
| eines | 0,7 % | 1,3 % |
| zwei (Richtwert) | 19,1 % | **88,5 %** |
| drei | 33,9 % | 4,9 % |
| **alle vier** | **41,4 %** | 0,3 % |
| **über dem Richtwert** | **75,3 %** | **5,3 %** |

In den Plänen der Heuristik arbeiten also **vier von zehn Pflegekräften an jedem einzelnen
Wochenende des Monats**, während eine Person gar keines übernimmt. Bei der Optimierung
liegen knapp neun von zehn exakt auf dem Richtwert. Das ist kein Machbarkeitsproblem — die
Optimierung beweist auf denselben Daten, dass eine nahezu richtwertkonforme Verteilung
existiert. Die Heuristik findet sie nur nicht: Bei ihr ist der Wochenend-Richtwert lediglich
ein Sortierkriterium. Wer sein Kontingent ausgeschöpft hat, rutscht in der Rangfolge nach
hinten, bleibt aber wählbar — und wird eingeteilt, sobald die Bevorzugten nicht können. Da
sie keine Entscheidung zurücknimmt, gibt es aus dieser Schieflage keinen Weg heraus.

Für die Personalbindung ist das die relevanteste Einzelzahl der ganzen Auswertung: gleiche
Daten, gleiche Regeln — und trotzdem für 41 % der Belegschaft jedes Wochenende im Dienst statt
höchstens jedes zweite. Mit Knappheit hat das nichts zu tun: Schon bei bedarfsgerechter
Decke, wo beide Verfahren nahezu gleich besetzen und regelkonform planen, sind es bei der
Heuristik 43 % und bei der Optimierung niemand.
Auch nach Ausfällen bleibt der Vorsprung weitgehend erhalten: 3,2 gegen 15,5 weiche
Abweichungen je gestörtem Plan (Abschnitt 4.1).

**Die reaktive Umplanung ist der größte Einzeleffekt.** Eine vollständige Neuplanung nach
Ausfällen erhält nur ein Fünftel bis knapp ein Drittel des Plans (MILP 19,8–29,7 % je
Personaldecke) und ändert im Mittel 283 Zuweisungen. Die reaktive Variante hält 90,4–93,8 %
Planstabilität bei Ø 22,8 Änderungen und rechnet in 0,55 s im Median (Maximum 5,2 s), ohne
zusätzliche Regelverstöße und bei nahezu gleicher Besetzungsquote (99,7 % gegen 99,9 %).
Für die Mitarbeitenden ist das der Unterschied zwischen „einige Dienste ändern sich" und
„der Monat wird neu gemacht". Dieser Vergleich ist innerhalb eines Verfahrens gezogen und
deshalb von der Frage aus Abschnitt 4 nicht betroffen.

**Im End-to-End-Vergleich gewinnt die Optimierung jede Kennzahl.** Gegenüber der
Excel-Welt, je gestörtem Plan: 99,7 % statt 97,3 % Besetzung, 0,77 statt 3,93 offene
Dienste, null statt 2,60 Untergrenzenverstöße, 3,2 statt 15,5 weiche Abweichungen, Spanne
0,247 statt 0,325 — und dabei 22,8 statt 30,3 geänderte Dienste bei 92,4 % statt 89,9 %
Planstabilität (Abschnitt 4.1).

**Der Preis der Stabilität ist messbar.** Die reaktive Variante erkauft sich die
Planstabilität mit schlechterer Lastverteilung (Spanne 0,159 statt 0,048 in den gestörten
Plänen bei 100 % Decke) und einzelnen weichen Abweichungen (1,3 statt 0,0). Das ist kein
Mangel, sondern der Zielkonflikt selbst — der Prototyp macht ihn quantifizierbar, statt ihn
zu verstecken.

**Rechenzeit ist kein limitierender Faktor.** Die Optimierung braucht 7,7 s bei
bedarfsgerechter und 14,7 s bei unterbesetzter Decke (80 %); in 8 von 135 Läufen (6 %) griff das
Zeitlimit von 30 s, ohne dass die Regelkonformität litt — auch diese Pläne sind frei von
harten Verstößen und Untergrenzenverstößen. Die Umplanung liegt im Median bei 0,55 s.

### 5.1 Replikation: gilt der Befund auch auf anderen Stationen?

Die Kampagne variiert Seed und Personaldecke — aber immer auf **derselben Station**: 30
Betten, Innere Medizin/Kardiologie, Verhältniszahl 10:1 tags. Damit ist belegt, dass die
Befunde nicht an einer einzelnen Zufallsziehung hängen. Nicht belegt ist damit, dass sie
nicht an *dieser Station* hängen.

Für diese Frage wurde die Kampagne auf drei weiteren Stationstypen wiederholt. Geändert
wurden dabei ausschließlich **Werte im Datensatz** — Bettenzahl, Verhältniszahl nach PpUGV,
Qualifikationsmix, Personalstruktur. Das **Schema** des Datensatzes ist identisch, und
`planner.py` wurde nicht angefasst. Das ist Absicht und zugleich der Grund, warum die
Replikation aussagekräftig ist: Ein zweites Schema hieße ein zweiter Lesepfad, und dann
prüfte die Replikation das CSV-Einlesen mit statt der Planungsverfahren (Datenkonzept,
Abschnitt 3.6).

| Stationstyp | Betten | Tags | Nachts | Ø Köpfe | Ø Solldienste |
|---|---|---|---|---|---|
| Innere Medizin / Kardiologie *(Haupt)* | 30 | 10:1 | 22:1 | 20 | 236 |
| Geriatrie | 40 | 10:1 | 20:1 | 25 | 304 |
| Herzchirurgie | 24 | 7:1 | 15:1 | 19 | 221 |
| Intensivmedizin | 12 | 2:1 | 3:1 | 27 | 330 |

Die Intensivstation ist dabei der härteste Test: kleinste Bettenzahl, aber wegen der
Verhältniszahl 2:1 der höchste Personalbedarf aller vier Stationen und die einzige ohne
Pflegehilfskräfte. Jede Station durchläuft dieselben 15 Instanzen (5 Seeds × 3
Personaldecken) und dieselben sechs Planungsvarianten — insgesamt 1.080 Pläne.

Geprüft wurden die sieben tragenden Befunde, jeder als **gerichtete Aussage**
(`replikation.py`). Die Werte lauten „Heuristik → Optimierung":

| Befund | Innere Medizin | Geriatrie | Herzchirurgie | Intensivmedizin |
|---|---|---|---|---|
| H1 Untergrenzenverstöße bei 80 % Decke | 6,53 → **0,00** | 6,13 → **0,00** | 8,33 → **0,00** | 8,13 → **0,87** |
| H2 unbesetzte Dienste bei 80 % Decke (Summe) | 113 → **10** | 132 → **36** | 145 → **51** | 122 → **20** |
| H3 Anteil regelkonformer Pläne bei 80 % | 0 % → **100 %** | 0 % → **93 %** | 0 % → **100 %** | 7 % → **67 %** |
| H4 Spanne der Auslastung bei 100 % Decke | 0,328 → **0,054** | 0,362 → **0,057** | 0,223 → **0,047** | 0,323 → **0,050** |
| H5 weiche Abweichungen je Plan | 16,0 → **1,3** | 17,7 → **1,4** | 15,1 → **2,3** | 18,3 → **1,2** |
| H6 Planstabilität End-to-End (S1/S2) | 89,9 % → **92,4 %** | 89,3 % → **91,6 %** | 90,1 % → **91,2 %** | 88,5 % → **89,9 %** |
| H7 Planstabilität auf gemeinsamem Plan | 88,2 % → **92,4 %** | 87,8 % → **91,6 %** | 87,8 % → **91,2 %** | 86,9 % → **89,9 %** |
| **bestätigt** | 7 von 7 | 7 von 7 | 7 von 7 | 7 von 7 |

**Alle sieben Befunde replizieren auf allen vier Stationstypen** — 28 von 28 gerichteten
Aussagen, auch nach Einführung der Krankheitsgutschrift. Die Größenordnungen verschieben
sich, die Richtung nicht. Das ist der Beleg dafür, dass die Ergebnisse nicht an der
Parametrierung *einer* Station hängen. H2 zeigt zugleich, was die Gutschrift auf allen
Stationen bewirkt: Bei 80 % Decke bleiben auch unter der Optimierung Dienste unter der
fachlichen Sollbesetzung — deutlich weniger als bei der Heuristik, aber nicht mehr null.

**Zugleich zeigt die Intensivstation die Grenze der Optimierung — und sie ist erklärbar.**
Sie ist die einzige Station, auf der die Optimierung bei 80 % Personaldecke nicht
durchgängig null Untergrenzenverstöße erreicht (0,87 im Mittel, höchstens 7 je Plan gegen
bis zu 16 bei der Heuristik). Die verbleibenden Verstöße treten **ausschließlich in den
Ausfallszenarien** auf, nie im Referenzszenario. Der Grund ist keine Schwäche des
Verfahrens, sondern Arithmetik: Bei der Verhältniszahl 2:1 und 20 % fehlender Personaldecke
gibt es Tage, an denen die Untergrenze selbst dann nicht erreichbar wäre, wenn jede
verfügbare anrechenbare Person an diesem Tag einen Dienst übernähme. Zählt man diese Tage
ab, stimmt ihre Zahl in **11 von 15 Fällen exakt** mit der Zahl der verbleibenden Verstöße
überein. In vier Fällen liegt die Zahl der Verstöße darüber; dort binden zusätzlich die Monatsarbeitszeit
einschließlich Krankheitsgutschrift, Ruhezeiten und Dienstfolgen, die diese einfache
Abzählung nicht berücksichtigt. Drei dieser vier Lösungen weist der Solver als optimal aus —
mehr Untergrenze ist dort unter den übrigen harten Regeln nicht zu haben.

Die Aussage lautet also nicht „die Optimierung hält die Untergrenze immer ein", sondern
präziser: **Sie hält sie ein, solange das mit den übrigen gesetzlichen und vertraglichen
Grenzen vereinbar ist.** Das ist eine bewusste Rangfolge im Modell: Arbeitszeitrecht und
Arbeitsvertrag sind harte Grenzen, die Untergrenze wird mit dem höchsten Strafgewicht
verfolgt. Wo Personal fehlt, kann kein Planungsverfahren es erzeugen — und der Prototyp macht
genau diese Grenze sichtbar, statt sie zu verdecken.

Ein Nebenbefund aus der Replikation betrifft die Datenqualität: Der erste Entwurf der
Herzchirurgie enthielt eine Pflegehilfskraft, die in **keiner** Schicht einsetzbar war — die
PpUGV lässt dort höchstens 5 % zu, was bei Schichtteams von drei bis fünf Personen
ganzzahlig null ergibt. Diese eine Person verzerrte die Spanne der Auslastung auf über 1,0
und ließ den Verteilungsvorteil der Optimierung auf dieser Station praktisch verschwinden
(mit dieser Person 1,08 → 1,08, ohne sie heute 0,223 → 0,047). Das Prüfskript enthält seither eine
Prüfung auf Einsetzbarkeit. Der Fall ist lehrreich: Eine strukturell nicht einsetzbare
Person sieht in keiner Kennzahl wie ein Datenfehler aus — sie sieht aus wie ein Verfahren,
das die Last nicht verteilen kann.

**Rechenzeit über alle Stationen (Mittel je Plan):**

| Stationstyp | Regelbasiert | MILP Erstplanung | MILP reaktiv |
|---|---|---|---|
| Innere Medizin | 0,38 s | 11,89 s | 0,79 s |
| Geriatrie | 0,47 s | 16,17 s | 1,64 s |
| Herzchirurgie | 0,35 s | 12,78 s | 0,77 s |
| Intensivmedizin | 0,51 s | 14,42 s | 1,74 s |

Die Rechenzeit bleibt über alle Stationen in derselben Größenordnung: Die Erstplanung
braucht 12 bis 16 s, die reaktive Umplanung im Mittel unter zwei Sekunden. Gegenüber der
vorigen Fassung ist die Umplanung etwas langsamer geworden, weil unter Knappheit mit
Gutschrift weniger Spielraum bleibt und der Solver länger sucht.

---

## 6. Was die Kampagne **nicht** beantwortet

**Ein Effekt der Ausfallstruktur ist nicht nachgewiesen.** Nach Volumenkontrolle bleibt
zwischen Welle und verteilten Einzelausfällen weder bei der Lastverteilung noch bei der
Planstabilität ein belastbarer Unterschied (Abschnitt 3.3). Ob es ihn nicht gibt oder ob die
Stichprobe von 6 volumenkontrollierten Instanzen zu klein ist, lässt sich nicht entscheiden.

**Alle Ausfälle eines Szenarios sind beim Umplanen gleichzeitig bekannt.** Das Szenario wird
auf einen Schlag angewendet — als wüsste man am Monatsanfang schon, wer in der dritten Woche
krank wird. In der Wirklichkeit kommen Ausfälle einzeln, und vergangene Tage sind nicht mehr
änderbar. Rückwirkende Änderungen treten in der reaktiven Betriebsart nicht auf; das
Vorwissen über spätere Ausfälle kann aber nur die Optimierung nutzen, weil die Heuristik Tag
für Tag entscheidet. Eine rollierende Umplanung — Ausfall für Ausfall, Vergangenheit
fixiert — wäre der realistischere Test und ist nicht umgesetzt.

**Die Krankheitsgutschrift zählt auf die vertragliche Obergrenze.** Das ist eine
[ANNAHME]: Die Obergrenze von 110 % der Sollzeit ist als Grenze des Arbeitszeitkontos
modelliert, und gutgeschriebene Zeit steht dort wie gearbeitete Zeit. Zählte sie nicht mit,
dürfte eine kranke Person zusätzlich bis an die Obergrenze eingeplant werden. Die offenen
Dienste der Optimierung bei 80 % Decke hängen an dieser Setzung.

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
(Untergrenzenverstöße bei 80 %: Greedy 6,53 ± 2,45 gegen MILP 0,00 ± 0,00). Für die
Szenarienanalyse in Abschnitt 3.3 steht nur eine Teilmenge von 6 Instanzen zur Verfügung —
zu wenig für inferenzstatistische Aussagen. Ein Signifikanztest wird bewusst nicht
gerechnet.

**Die Gewichte der Zielfunktion sind gesetzt, nicht hergeleitet.** Wie stark Unterbesetzung
gegen Lastverteilung gegen Wunscherfüllung zählt, ist eine Managemententscheidung. Für das
wichtigste Gewicht — `keep` — ist die Wirkung in Abschnitt 4.5 quantifiziert. Die übrigen
Gewichte sind nicht systematisch variiert; insbesondere das Verhältnis von
Untergrenzenstrafe zu Unterbesetzungsstrafe und die Gewichtung der Dienstwünsche bleiben
ungeprüft.

**Die Obergrenze der Optimierung wurde auf dieser Station nicht erreicht.** Alle 135
MILP-Pläne sind frei von harten Verstößen und Untergrenzenverstößen; bei 80 % Decke bleiben
unter Ausfällen einzelne Dienste unter der fachlichen Sollbesetzung. Das heißt nicht, dass
das immer so wäre — auf der Intensivstation wird die Grenze erreicht (Abschnitt 5.1).

**Alle Daten sind synthetisch.** Die absolute Höhe der Kennzahlen ist nicht auf eine
konkrete Station übertragbar. Der Vergleich zweier Verfahren auf identischer Datenbasis
bleibt gültig. Die Replikation auf vier Stationstypen (Abschnitt 5.1) zeigt, dass die
**Richtung** der Befunde nicht an einer Parametrierung hängt — sie ersetzt aber keine
Erhebung an einer realen Station, weil alle vier Instanzen aus demselben Generator und
denselben Annahmen stammen. Ein systematischer Fehler im Modell würde in allen vier
gleichermaßen auftreten und durch die Replikation gerade nicht auffallen.

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

**Wirkung, über alle 15 Instanzen und drei Szenarien gemessen** (`python auswertung.py
--baseline`, mit Krankheitsgutschrift):

| Heuristik, Neuplanung | Richtwert hart | Richtwert weich |
|---|---|---|
| Besetzungsquote | 97,8 % | 97,8 % |
| offene Dienste je Plan | 3,07 | **2,82** |
| Untergrenzenverstöße je Plan | **2,24** | 2,42 |
| harte Regelverstöße je Plan | 0,38 | 0,38 |
| weiche Abweichungen je Plan | **15,2** | 16,0 |

Bei 90 % und 100 % Personaldecke ändert sich **nichts** — dort wird der Richtwert nie
bindend. Bei 80 % sinken die offenen Dienste über alle Instanzen von 124 auf 113, dafür
steigen die Untergrenzenverstöße von 90 auf 98 und die weichen Abweichungen von 14,0 auf
16,5 je Plan. Die Heuristik besetzt also mehr Dienste, erkauft das aber mit mehr
Richtwertüberschreitungen und trifft dabei stellenweise schlechtere Folgeentscheidungen:
Eine greedy Auswahl ist nicht monoton — mehr Spielraum an einer Stelle kann an einer
anderen schaden, weil keine Entscheidung zurückgenommen wird.

**Bewertung.** Die Korrektur verschiebt die Baseline in beide Richtungen und ändert das
Gesamtbild nicht: Die Heuristik bleibt bei 80 % Decke in **keinem einzigen** Plan
vollständig regelkonform, das MILP in **allen**. Der Befund hängt also nicht an dieser
Modellierungsentscheidung. Berichtet werden durchgängig die Zahlen der korrigierten
Variante.

---

## 8. Business Impact

**Gemessen** (gilt für diese 15 Instanzen):

- Bei knapper Personaldecke sichert die Optimierung die gesetzliche Mindestbesetzung, die
  Heuristik nicht: 0 gegen 6,5 Untergrenzenverstöße je Plan bei 80 % Decke; 100 % gegen
  0 % vollständig regelkonforme Pläne.
- Gleichmäßigere Belastung im Normalbetrieb: Streuung der Auslastung um Faktor 6 geringer,
  Spanne von 33 auf 5 Prozentpunkte, alle Wochenend- und Nachtdienst-Richtwerte eingehalten.
- Reaktion auf Ausfälle: Auf demselben Ausgangsplan hält die Optimierung 92,4 %
  Planstabilität gegen 88,2 % der Heuristik und braucht dafür 22,8 statt 36,0 Änderungen —
  bei null Untergrenzenverstößen gegen 0,83 und halb so vielen offenen Diensten (0,77 gegen
  1,67). Die Umplanung läuft im Median in 0,55 s.

**Gemessen, aber mit Zielkonflikt:** In der reaktiven Betriebsart steigt die Spanne der
Optimierung unter der Ausfallwelle auf 0,257, bei vollständiger Neuplanung bleibt sie bei
0,187. Die Differenz ist der Preis der Vorgabe „möglichst wenig ändern" — vor der Heuristik
(0,317) liegt die Optimierung in beiden Betriebsarten. Gleichmäßigere Belastung *und*
maximale Planstabilität sind nicht gleichzeitig zu haben; welches Ziel schwerer wiegt, ist
eine Managemententscheidung.

**Der Effizienzvorteil ist an die durchgängige Nutzung gebunden.** Übernimmt die
Optimierung nur die Anpassung bestehender Excel-Pläne, sichert sie weiterhin
Rechtskonformität und Besetzung (null statt 2,60 Untergrenzenverstöße, 0,77 statt 3,93
offene Dienste), braucht dafür aber 34,8 statt 30,3 Änderungen. Der Rückgang auf 22,8
Änderungen stellt sich erst ein, wenn auch die Monatsplanung aus dem System kommt
(Abschnitt 4.3). Für
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
gleicher Versorgungsqualität mit rund einem Viertel weniger Änderungen auskommt, adressiert genau
den Punkt, den die reine Besetzungsquote nicht sichtbar macht.

**Die Gewichtung der Ziele ist eine Führungsentscheidung, keine technische.** Ob ein
Ausfall durch minimales Lückenfüllen oder durch Umverteilen im ganzen Monat aufgefangen
wird, entscheidet nicht das Verfahren, sondern ein einziges Gewicht. Die Sensitivitätsanalyse
in Abschnitt 4.5 beziffert den Wechselkurs: Planstabilität 93,7 % bei einer Spanne von 0,344
auf der einen Seite, 68,3 % bei 0,076 auf der anderen — neunzehn gegen über hundert geänderte
Dienste im Monat. Dazwischen liegt mit `fair` = 0,1 eine Einstellung, die beides verbessert
gegenüber der Heuristik: halbe Spanne bei höherer Stabilität. Beides ist vertretbar: Stabilität schützt die private Planung der
Mitarbeitenden, Umverteilung schützt die Gleichverteilung der Last. Der Prototyp macht den
Preis beider Optionen sichtbar; die Abwägung gehört auf die Leitungsebene, nicht in die
Konfigurationsdatei.

---

## 9. Einordnung in die Leitfrage

„Wie kann eine KI-gestützte Planungsempfehlung die Erstellung und kurzfristige Anpassung
eines Schichtplans gegenüber einer regelbasierten Excel-Planung unterstützen?"

Nach dieser Kampagne lässt sich die Antwort präzisieren:

1. **Bei der Erstellung** liegt der Mehrwert nicht in der Machbarkeit, sondern in
   Regelkonformität unter Knappheit und in der Verteilungsgerechtigkeit. Ist genug Personal
   da, sichert auch eine Regelheuristik Besetzung und Rechtskonformität — den Unterschied
   macht dann allein die Verteilung der Last.
2. **Bei der kurzfristigen Anpassung** liegt der Mehrwert in der Planstabilität — und zwar
   nur, wenn Stabilität ausdrücklich als Ziel modelliert wird. Eine bloße Neuoptimierung
   nach dem Ausfall ist für die Mitarbeitenden schlechter als die Heuristik.
3. **Die beiden Ziele schließen einander teilweise aus.** Unter einer gebündelten
   Ausfallwelle erreicht die Optimierung entweder die gleichmäßigere Last (Spanne 0,187 bei
   vollständiger Neuplanung, aber nur 25 % unveränderte Dienste) oder den stabilen Plan
   (91 % unveränderte Dienste bei Spanne 0,257), nicht beides zugleich. Die
   Regelkonformität bleibt in jedem Fall erhalten, und in beiden Betriebsarten liegt sie bei
   der Lastverteilung vor der Heuristik.

4. **Erstellung und Anpassung sind nicht trennbar.** Die Vier-Felder-Tafel in Abschnitt 4.3
   zeigt, dass der Effizienzvorteil nur entsteht, wenn beide Schritte aus demselben System
   kommen: 22,8 geänderte Dienste je gestörtem Plan gegenüber 30,3 in der Excel-Welt —
   während dieselbe Optimierung auf einem geerbten Excel-Plan 34,8 Änderungen braucht. Die
   Leitfrage fragt zu Recht nach beidem zusammen.

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
- Entgeltfortzahlungsgesetz (EFZG), § 4 Abs. 1 und 4 — Entgeltausfallprinzip und tarifliche Abweichung
- BAG, Urteil vom 05.10.2023 – 6 AZR 210/22: Zeitgutschrift für krankheitsbedingt ausgefallene, im Dienstplan vorgesehene Dienste — <https://www.stollfuss.de/blog/BAG-Stundengutschriften-auf-einem-Arbeitszeitkonto-fuer-krankheitsbedingt-nicht-geleistete-Bereitschaftsdienste-2024-01-29>
- BAG, Urteil vom 16.07.2014 – 10 AZR 242/13: tarifliche Abweichung vom Entgeltausfallprinzip beim Arbeitszeitkonto — <https://www.bundesarbeitsgericht.de/entscheidung/10-azr-242-13/>

Rechtsgrundlagen, Datenherkunft und Annahmenregister: siehe `DATENKONZEPT.md`.
