# KI-gestützte Schichtplanung in der Pflege

**Handout zum Use Case · WPM „KI und Management"**

---

## Worum es geht

Dienstpläne in der Pflege werden überwiegend manuell in Excel erstellt. Sie müssen
gleichzeitig Arbeitszeitrecht, gesetzliche Mindestbesetzungen, Qualifikationen und
wechselnden Personalbedarf einhalten — und bei jedem kurzfristigen Ausfall neu justiert
werden.

**Leitfrage:** Wie kann eine KI-gestützte Planungsempfehlung die Erstellung und
kurzfristige Anpassung eines Schichtplans gegenüber einer regelbasierten Excel-Planung
unterstützen?

**Prototyp:** Normalstation Innere Medizin/Kardiologie, 30 Betten, 23 Mitarbeitende,
28 Tage Planungshorizont. Zwei Verfahren auf identischer Datengrundlage: eine
regelbasierte Heuristik (Baseline) und eine mathematische Optimierung.

## Warum das wirtschaftlich relevant ist

- **66 % der Krankenhäuser** schrieben 2024 Verluste, 70 % erwarten für 2025 ein
  negatives Ergebnis (DKI Krankenhaus Barometer 2025, 376 Häuser).
- Unterschreitungen der **Pflegepersonaluntergrenzen** sind kein Qualitätsdetail: § 137i
  Abs. 5 SGB V sieht **Vergütungsabschläge oder eine Verringerung der Fallzahl** vor.
- Trotz Untergrenzen bleiben rund **15 % der Schichten regelmäßig unterbesetzt**; ein
  großer Teil der Häuser reagiert auf Personalmangel mit **Bettensperrungen** statt mit
  Einstellungen (Wissenschaftliche Dienste des Bundestages, WD 8-3000-008/26).

Planungsqualität wirkt also direkt auf Erlöse, Sanktionsrisiko und Personalbindung.

## Vorgehen

Orientiert an CRISP-DM. Datengrundlage vollständig **synthetisch** — keine
personenbezogenen Daten, keine Gesundheitsdaten. Ausfälle sind reine
Verfügbarkeitsereignisse ohne Grund oder Diagnose. Der Datensatz ist aus dokumentierten
Quellen abgeleitet (PpUGV, ArbZG, TVöD-K, Destatis, PPR 2.0) und über einen festen Seed
exakt reproduzierbar.

Evaluiert wurde über **15 Instanzen** (5 Zufallsseeds × 3 Personaldecken) × 3
Ausfallszenarien × 6 Verfahrensvarianten = **270 Pläne**. Die beiden Ausfallszenarien sind
auf dasselbe Ausfallvolumen kalibriert und unterscheiden sich nur in der Struktur —
verteilte Einzeltage gegen mehrtägige Episoden in einer Welle —, damit ein Unterschied der
Struktur zuzurechnen ist und nicht dem Umfang.

## Die sieben wichtigsten Learnings

**1. Machine Learning war nicht die Antwort — und das war das erste Ergebnis.**
Es gibt keine zu lernende Zielvariable und keine historischen Planentscheidungen als
Trainingsdaten. Das Problem ist eine Zuordnung unter harten Nebenbedingungen mit mehreren
konkurrierenden Zielen. Einschlägig sind mathematische Optimierung und Constraint
Programming. Zur erwartbaren Rückfrage „ist das dann überhaupt KI?": Umgangssprachlich —
nein, das Modell lernt nicht. Fachlich — ja, Suche, Constraint-Erfüllung und Scheduling
gehören seit den Anfängen zum Kern der KI (Russell & Norvig). Und die Aufgabenstellung
verlangt ausdrücklich eine *begründete* Methodenwahl, nicht ML. Wo ML anschlussfähig wäre:
Ausfall- und Belegungsprognose als Vorstufe der Optimierung — das steht im Ausblick, nicht
in den Ergebnissen.

**2. Ein zu leichter Datensatz hätte das Projekt entwertet.**
Bei bedarfsgerechter Personaldecke erreichen *beide* Verfahren nahezu 100 % Besetzung
ohne Regelverstöße — kein nennenswerter Unterschied. Erst als wir die Personaldecke
systematisch auf 90 % und 80 % absenkten, trennten sich die Verfahren: Bei 80 % war
**kein einziger** Plan der Heuristik vollständig regelkonform, gegenüber **100 %** der
optimierten Pläne. Wer nur eine bequeme Instanz rechnet, misst nichts.

**3. Die Zielfunktion entscheidet, nicht das Verfahren.**
Nach einem Ausfall neu zu optimieren erhielt nur 51 % der Dienste — schlechter als die
simple Heuristik. Erst als „möglichst wenig ändern" ausdrücklich ins Modell kam, stieg die
Stabilität auf 95 %. Der Preis dafür ist sichtbar: Unter der Ausfallwelle liegt die
Lastverteilung dann gleichauf mit der Heuristik (Spanne 0,377 gegen 0,380), während
vollständige Neuplanung 0,163 erreicht. Gewicht 200 für „nicht ändern" gegen 0,02 für
Lastausgleich — gleichmäßige Last **oder** stabiler Plan, unter Druck ist beides zugleich
nicht zu haben. Welches Ziel gewinnt, ist eine Führungsentscheidung, keine technische.

**4. Regeln gehören in die Daten, nicht in den Code.**
Ruhezeiten, Verhältniszahlen und Qualifikationsvorgaben stehen als Spalten im Datensatz.
Ändert sich die Rechtslage, ändert sich eine Zahl — nicht das Programm. Das hat die
Diskussion mit Fachlogik erheblich vereinfacht.

**5. Die Prüfung muss vom Verfahren getrennt sein.**
Eine eigene Funktion bewertet den fertigen Plan unabhängig davon, wer ihn erzeugt hat.
Ohne diese Trennung wäre jeder KPI-Vergleich zirkulär gewesen — und sie hat uns
tatsächlich zwei Fehler in der eigenen Logik gezeigt.

**6. Der Vorteil steckt in der Kette, nicht in einem Schritt.**
Wir haben alle vier Kombinationen aus Ausgangsplan und Reparaturverfahren gerechnet
(geänderte Dienste je Monat): Excel-Plan von Excel repariert **19,5** · Excel-Plan von MILP
**25,2** · MILP-Plan von Excel **24,8** · MILP-Plan von MILP **14,9**. Auf jedem geerbten
Plan ändert die Optimierung *mehr* — weil sie dessen offene Dienste und Regelverstöße
mitbehebt. Nur wenn Planung **und** Anpassung aus demselben System kommen, sinkt der Wert.
Für die Praxis: Ein Optimierer als reine Feuerwehr auf bestehenden Excel-Plänen hebt die
Rechtssicherheit, aber nicht die Entlastung.

**7. Eine Kennzahl ohne ihren Bezugspunkt ist nicht interpretierbar.**
Planstabilität als Prozentwert hängt davon ab, wie gut der Ausgangsplan war — ein Verfahren,
das offene Dienste und Regelverstöße stehen lässt, gewinnt sie durch Untätigkeit. Wir
berichten sie deshalb nie allein, sondern mit der absoluten Zahl geänderter Dienste, und
haben zusätzlich beide Verfahren denselben Plan reparieren lassen (95,0 % gegen 91,8 %).
Dieselbe Disziplin beim Szenarienvergleich: Die Ausfallwelle sah zunächst instabiler aus als
verteilte Einzelausfälle — betrachtet man nur die Instanzen, in denen sie *nicht* mehr
Ausfalltage enthielt, schrumpfte der Unterschied von 2,5 auf 0,8 Prozentpunkte. Überwiegend
ein Mengen-, kein Struktureffekt. Der Verteilungseffekt hielt der Prüfung stand (6 von 6).
Nur den berichten wir.

## Herausforderungen und Erfolgsfaktoren

- **Realitätsnähe kollidiert mit Recht.** Der Bundesdurchschnitt an Hilfskräften (17,6 %)
  liegt über der PpUGV-Grenze für unseren Bereich (10 %). Die strengere Norm hat Vorrang.
- **13 Annahmen** mussten als solche gekennzeichnet werden, weil sie nicht belegbar sind.
- **Datensatz zuerst, reproduzierbar und dokumentiert** — fester Seed, Generator- und
  Prüfskript. Ohne das ist keine Aussage belastbar.
- **Klein bleiben.** Eine Station, ein Monat, nur der Pflegedienst.
- **Datenschutz als Konstruktionsprinzip**, nicht als nachträgliche Prüfung.

## Werkzeuge

Python mit pandas · **SciPy/HiGHS** für die Optimierung (kein kommerzieller Solver nötig)
· Streamlit · GitHub und Streamlit Community Cloud. Rechenzeit: 10–16 Sekunden für einen
28-Tage-Plan, im Median unter einer Viertelsekunde für eine Umplanung.

## Was wir gemessen haben — und was nicht

**Gemessen:** Regelkonformität unter Knappheit (bei 80 % Decke 0 gegen 4,3
Untergrenzenverstöße je Plan), Gleichverteilung der Arbeitslast (Spanne von 33 auf 7
Prozentpunkte), Planstabilität nach Ausfällen (95,0 % gegen 93,5 % bei 14,9 statt 19,5
geänderten Diensten), der Zielkonflikt zwischen Lastverteilung und Stabilität, Rechenzeit.

**Nicht gemessen, nur plausibel:** Reduktion des manuellen Planungsaufwands, Wirkung auf
Zufriedenheit und Fluktuation, vermiedene Bettensperrungen. Diese Aussagen bräuchten eine
Erhebung im Betrieb — wir kennzeichnen sie im Bericht ausdrücklich als Schätzung.

---

*Datensatz, Generator, Prüfskripte und Evaluationsdaten sind im Anhang der Hausarbeit
enthalten und vollständig reproduzierbar.*
