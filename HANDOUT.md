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

**Prototyp:** Normalstation Innere Medizin/Kardiologie, 30 Betten, 22 Mitarbeitende,
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
Ausfallszenarien × 4 Verfahrensvarianten = **180 Pläne**. Die beiden Ausfallszenarien
tragen dasselbe Ausfallvolumen und unterscheiden sich nur in der Struktur — verteilte
Einzeltage gegen mehrtägige Episoden in einer Welle —, damit ein Unterschied der Struktur
zuzurechnen ist und nicht dem Umfang.

## Die sechs wichtigsten Learnings

**1. Machine Learning war nicht die Antwort — und das war das erste Ergebnis.**
Es gibt keine zu lernende Zielvariable und keine historischen Planentscheidungen als
Trainingsdaten. Das Problem ist eine Zuordnung unter harten Nebenbedingungen mit
mehreren konkurrierenden Zielen. Einschlägig sind mathematische Optimierung und
Constraint Programming. Wer „KI" automatisch mit ML gleichsetzt, baut am Problem vorbei.

**2. Ein zu leichter Datensatz hätte das Projekt entwertet.**
Bei bedarfsgerechter Personaldecke erreichen *beide* Verfahren nahezu 100 % Besetzung
ohne Regelverstöße — kein nennenswerter Unterschied. Erst als wir die Personaldecke
systematisch auf 90 % und 80 % absenkten, trennten sich die Verfahren: Bei 80 % war
**kein einziger** Plan der Heuristik vollständig regelkonform, gegenüber **100 %** der
optimierten Pläne. Wer nur eine bequeme Instanz rechnet, misst nichts.

**3. Die Zielfunktion entscheidet, nicht das Verfahren.**
Nach einem Ausfall neu zu optimieren lieferte *schlechtere* Planstabilität als die
simple Heuristik (50 % gegen 74 % unveränderte Dienste). Erst als „möglichst wenig
ändern" ausdrücklich ins Modell kam, stieg die Stabilität auf 95 %. Optimierung ist nur
so gut wie die Ziele, die man ihr vorgibt.

**4. Regeln gehören in die Daten, nicht in den Code.**
Ruhezeiten, Verhältniszahlen und Qualifikationsvorgaben stehen als Spalten im Datensatz.
Ändert sich die Rechtslage, ändert sich eine Zahl — nicht das Programm. Das hat die
Diskussion mit Fachlogik erheblich vereinfacht.

**5. Die Prüfung muss vom Verfahren getrennt sein.**
Eine eigene Funktion bewertet den fertigen Plan unabhängig davon, wer ihn erzeugt hat.
Ohne diese Trennung wäre jeder KPI-Vergleich zirkulär gewesen — und sie hat uns
tatsächlich zwei Fehler in der eigenen Logik gezeigt.

**6. Gleich viele Ausfälle wirken sehr unterschiedlich.**
Zwei Szenarien mit identischem Ausfallvolumen, aber unterschiedlicher Struktur: verteilte
Einzeltage gegen mehrtägige Episoden in einer Welle. Die Welle kostet mehr — bei der
Heuristik steigen die harten Regelverstöße von 0,6 auf 1,3 je Plan, bei der Optimierung
bleiben sie null. Der Wert eines Planungsverfahrens zeigt sich in der Störung, nicht im
Durchschnittsmonat.

## Herausforderungen

- **Realitätsnähe kollidiert mit Recht.** Der bundesweite Durchschnitt an Hilfskräften
  (17,6 %) liegt über der PpUGV-Grenze für unseren Bereich (10 %). Die strengere Norm
  hat Vorrang — solche Konflikte muss man bemerken und begründen.
- **Annahmen sauber kennzeichnen.** 13 Setzungen mussten als Annahmen dokumentiert
  werden, weil sie nicht belegbar sind. Das ist mühsam, aber prüfungsrelevant.
- **Deployment.** Die Abhängigkeitsdatei der Streamlit Cloud hat den Prototyp zweimal
  lahmgelegt, bevor er lief.

## Erfolgsfaktoren

- **Datensatz zuerst, reproduzierbar und dokumentiert.** Fester Seed, ein Generatorskript,
  ein Prüfskript. Ohne das ist keine Aussage belastbar.
- **Automatisierte Prüfungen von Anfang an.** Schema, Rechtskonformität, Erfüllbarkeit.
- **Klein bleiben.** Eine Station, ein Monat, nur der Pflegedienst. Ärztliche
  Dienstplanung ist ein eigenes Problemfeld und hätte den Rahmen gesprengt.
- **Datenschutz als Konstruktionsprinzip**, nicht als nachträgliche Prüfung.

## Werkzeuge

Python mit pandas · **SciPy/HiGHS** für die Optimierung (kein kommerzieller Solver nötig)
· Streamlit für die Oberfläche · GitHub und Streamlit Community Cloud für Versionierung
und Betrieb. Rechenzeit: 7–17 Sekunden für einen kompletten 28-Tage-Plan, im Median unter
einer Viertelsekunde für eine Umplanung.

## Was wir gemessen haben — und was nicht

**Gemessen:** Regelkonformität unter Knappheit (bei 80 % Decke 0 gegen 4,4
Untergrenzenverstöße je Plan), Gleichverteilung der Arbeitslast (Spanne von 29 auf 7
Prozentpunkte), Planstabilität nach Ausfällen (93–95 % statt 49–78 %), Rechenzeit.

**Nicht gemessen, nur plausibel:** Reduktion des manuellen Planungsaufwands, Wirkung auf
Zufriedenheit und Fluktuation, vermiedene Bettensperrungen. Diese Aussagen bräuchten eine
Erhebung im Betrieb — wir kennzeichnen sie im Bericht ausdrücklich als Schätzung.

---

*Datensatz, Generator, Prüfskripte und Evaluationsdaten sind im Anhang der Hausarbeit
enthalten und vollständig reproduzierbar.*
