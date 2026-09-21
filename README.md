# CarePlan — KI-gestützte Schichtplanung in der Pflege

Prototyp zum Vergleich einer regelbasierten Planung (Baseline, entspricht einer
Excel-Planung) mit einer MILP-Optimierung. Fallstudie: Normalstation Innere Medizin /
Kardiologie, 30 Betten, 28 Tage Planungshorizont, synthetischer Datensatz.

```
streamlit_app.py            Oberfläche (Streamlit)
planner.py                  Planungs- und Bewertungslogik (ohne Streamlit testbar)
schichtplan_datensatz.csv   Datengrundlage (synthetisch, pseudonym)
requirements.txt            Abhängigkeiten für Streamlit Community Cloud
```

Alle Dateien liegen im Hauptverzeichnis des Repositorys, ohne Unterordner.

## Starten

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Die zwei Verfahren

**Regelbasiert (Baseline).** Tag für Tag, Schicht für Schicht, jeweils die am wenigsten
ausgelastete Person, die alle harten Regeln erfüllt. Findet sich niemand, bleibt der
Dienst offen.

**MILP-Optimierung.** Die gesamte Periode als gemischt-ganzzahliges Programm, gelöst mit
HiGHS über `scipy.optimize.milp`. Gesetzliche und vertragliche Grenzen sind harte
Nebenbedingungen; Unterbesetzung, Lastverteilung, Dienstwünsche sowie Wochenend- und
Nachtdienstverteilung gehen gewichtet in die Zielfunktion ein. Bei der reaktiven
Umplanung wird jede beibehaltene Zuweisung des Ausgangsplans belohnt.

Beide Verfahren lesen denselben Datensatz; `evaluate()` prüft jeden Plan unabhängig
vom Verfahren nach.

## Krankheit muss nicht nachgearbeitet werden

Fällt jemand kurzfristig aus (Szenario S1, S2 oder ein manuell gemeldeter Ausfall), wird
der ausgefallene Dienst mit seiner Dauer laut Ausgangsplan **gutgeschrieben** und zählt
wie gearbeitete Zeit — für die Auslastung, die Zielarbeitszeit und die vertragliche
Obergrenze (Entgeltausfallprinzip, § 4 Abs. 1 EFZG). Krankheitstage sind damit keine
Minusstunden, und keins der beiden Verfahren plant die ausgefallene Zeit später im Monat
nach. Für die Ruhezeit- und Höchstarbeitszeitprüfung nach ArbZG zählt die Gutschrift
nicht, weil dort nur tatsächlich geleistete Arbeit relevant ist.
Umsetzung: `krankheitsgutschrift()` in `planner.py`; sichtbar im Reiter „Arbeitszeit“
(Spalte „Gutschrift Krankheit (h)“).

## Rechenzeit

Der Ausgangsplan der MILP-Optimierung (Szenario S0) nutzt die volle Rechenzeitgrenze von
30 Sekunden. Er wird einmal je App-Instanz berechnet und danach für alle Sitzungen
wiederverwendet. Die Umplanungen bei Ausfällen brauchen reaktiv unter 2 Sekunden, eine
vollständige Neuplanung mit dem MILP etwa 6 bis 8 Sekunden (gemessen lokal).

## Datenschutz

Mitarbeitende sind pseudonyme IDs, Ausfälle reine Verfügbarkeitsereignisse ohne Grund
oder Diagnose. Es werden keine Gesundheitsdaten verarbeitet.
