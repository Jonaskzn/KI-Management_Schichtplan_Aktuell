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

## Die neun wichtigsten Learnings

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
Bei bedarfsgerechter Personaldecke erreichen *beide* Verfahren nahezu 100 % Besetzung ohne
Regelverstöße. Erst als wir die Decke systematisch auf 90 % und 80 % absenkten, trennten
sich die Verfahren: Bei 80 % war **kein einziger** Plan der Heuristik vollständig
regelkonform, gegenüber **100 %** der optimierten. Wer nur eine bequeme Instanz rechnet,
misst nichts.

**3. Die Zielfunktion entscheidet, nicht das Verfahren.**
Nach einem Ausfall neu zu optimieren erhielt nur rund ein Viertel der Dienste — schlechter
als die simple Heuristik. Erst als „möglichst wenig ändern" ausdrücklich ins Modell kam,
stieg die Stabilität auf 92 %. Der Preis dafür ist sichtbar: Unter der Ausfallwelle steigt
die Spanne der Auslastung von 0,187 bei vollständiger Neuplanung auf 0,257 — die
Optimierung bleibt damit vor der Heuristik (0,317), verteilt aber schlechter, als sie
könnte. Gewicht 200 für „nicht ändern" gegen 0,02 für Lastausgleich — welches Ziel gewinnt,
ist eine Führungsentscheidung, keine technische.

**4. Regeln gehören in die Daten, nicht in den Code.**
Ruhezeiten, Verhältniszahlen und Qualifikationsvorgaben stehen als Spalten im Datensatz.
Ändert sich die Rechtslage, ändert sich eine Zahl — nicht das Programm.

**5. Vier von zehn Pflegekräften arbeiten jedes Wochenende — oder eben nicht.**
Der greifbarste Unterschied steckt nicht in der Besetzungsquote, sondern in den *weichen*
Abweichungen: Überschreitungen von Richtwerten, die dem Belastungsschutz dienen, aber keine
Rechtsverstöße sind. 95 % davon betreffen Wochenenden. Über 608 Personenpläne gemessen sind
bei der Heuristik **41 % der Belegschaft an allen vier Wochenenden im Dienst** und 75 % über
dem Richtwert von zwei; bei der Optimierung liegen 88 % genau auf dem Richtwert. Kein
Machbarkeitsproblem und keine Folge der Knappheit — schon bei bedarfsgerechter Decke, wo
beide Verfahren nahezu gleich besetzen, sind es 43 % gegen niemanden.

**6. Die Prüfung muss vom Verfahren getrennt sein.**
Eine eigene Funktion bewertet den fertigen Plan unabhängig davon, wer ihn erzeugt hat.
Ohne diese Trennung wäre jeder KPI-Vergleich zirkulär gewesen — und sie hat uns
tatsächlich zwei Fehler in der eigenen Logik gezeigt.

**7. Der Vorteil steckt in der Kette, nicht in einem Schritt.**
Wir haben alle vier Kombinationen aus Ausgangsplan und Reparaturverfahren gerechnet
(geänderte Dienste je gestörtem Plan): Excel-Plan von Excel repariert **30,3** · Excel-Plan
von MILP **34,8** · MILP-Plan von Excel **36,0** · MILP-Plan von MILP **22,8**. Auf jedem geerbten
Plan ändert die Optimierung *mehr* — weil sie dessen offene Dienste und Regelverstöße
mitbehebt. Nur wenn Planung **und** Anpassung aus demselben System kommen, sinkt der Wert.
Für die Praxis: Ein Optimierer als reine Feuerwehr auf bestehenden Excel-Plänen hebt die
Rechtssicherheit, aber nicht die Entlastung.

**8. Eine Kennzahl ohne ihren Bezugspunkt ist nicht interpretierbar.**
Planstabilität als Prozentwert hängt davon ab, wie gut der Ausgangsplan war — wer offene
Dienste und Regelverstöße stehen lässt, gewinnt sie durch Untätigkeit. Wir berichten sie
deshalb nie allein, sondern mit der absoluten Zahl geänderter Dienste, und haben beide
Verfahren zusätzlich denselben Plan reparieren lassen (92,4 % gegen 88,2 %).

**9. Ein plausibles Ergebnis kann einen Modellfehler verdecken.**
Die Ausfallwelle schien die Lastverteilung strukturell zu verschlechtern — bis wir
Krankheitstage nach dem Entgeltausfallprinzip (§ 4 EFZG) gutschrieben. Ohne Gutschrift
galten gerade die mehrtägig Erkrankten als unterausgelastet; mit ihr schrumpfte der Effekt
von +0,084 auf +0,008. Aufgefallen ist das nicht in den Kennzahlen, sondern in der App: Die
Priorität „Verteilungsgerechtigkeit" ließ Kranke ihre Dienste nacharbeiten.

## Herausforderungen und Erfolgsfaktoren

- **Realitätsnähe kollidiert mit Recht.** Der Bundesdurchschnitt an Hilfskräften (17,6 %)
  liegt über der PpUGV-Grenze für unseren Bereich (10 %). Die strengere Norm hat Vorrang.
- **14 Annahmen** mussten als solche gekennzeichnet werden, weil sie nicht belegbar sind.
- **Datensatz zuerst, reproduzierbar und dokumentiert** — fester Seed, Generator- und
  Prüfskript. Ohne das ist keine Aussage belastbar.
- **Klein bleiben.** Eine Station, ein Monat, nur der Pflegedienst.
- **Die Baseline muss fair konfiguriert sein.** Nachtdienst-Richtwert in der Heuristik
  hart, im Optimierer weich — korrigiert und nachgemessen, Gesamtbild unverändert.
- **Datenschutz als Konstruktionsprinzip**, nicht als nachträgliche Prüfung.

## Werkzeuge

Python mit pandas · **SciPy/HiGHS** für die Optimierung (kein kommerzieller Solver nötig)
· Streamlit · GitHub und Streamlit Community Cloud. Rechenzeit: 8–15 Sekunden für einen
28-Tage-Plan, im Median rund eine halbe Sekunde für eine Umplanung.

## Was wir gemessen haben — und was nicht

**Gemessen:** Regelkonformität unter Knappheit (bei 80 % Decke 0 gegen 6,5
Untergrenzenverstöße je Plan), Gleichverteilung der Arbeitslast (Spanne von 33 auf 5
Prozentpunkte), Planstabilität nach Ausfällen (92,4 % gegen 89,9 % bei 22,8 statt 30,3
geänderten Diensten), der Zielkonflikt zwischen Lastverteilung und Stabilität, Rechenzeit.

**Nicht gemessen, nur plausibel:** Reduktion des manuellen Planungsaufwands, Wirkung auf
Zufriedenheit und Fluktuation, vermiedene Bettensperrungen. Diese Aussagen bräuchten eine
Erhebung im Betrieb — wir kennzeichnen sie im Bericht ausdrücklich als Schätzung.

---

*Datensatz, Generator, Prüfskripte und Evaluationsdaten sind im Anhang der Hausarbeit
enthalten und vollständig reproduzierbar.*
