# CarePlan — KI-gestützte Schichtplanung in der Pflege

Prototyp und Datengrundlage für den Vergleich einer regelbasierten Planung mit einem
optimierungsbasierten Ansatz. Fallstudie: Normalstation Innere Medizin / Kardiologie,
30 Betten, 28 Tage Planungshorizont.

```
schichtplan_datensatz.csv   Datengrundlage — eine Datei, 1.232 Zeilen × 94 Spalten
planner.py                  Planungs- und Bewertungslogik (ohne Streamlit, testbar)
streamlit_app.py            Oberfläche
test_planner.py             Smoke- und Regeltests für die Planungslogik
generate_dataset.py         Generator für den Datensatz (Seed 20261130)
validate_dataset.py         Prüfskript für den Datensatz
DATENKONZEPT.md             Begründung jeder Spalte und jedes Parameters mit Quellen
```

## Starten

```bash
uv sync
uv run streamlit run streamlit_app.py
```

Die App lädt `schichtplan_datensatz.csv` aus dem Repository. Über den Uploader in der
Seitenleiste lässt sich stattdessen eine eigene Variante einspielen — nützlich für
Sensitivitätsanalysen mit anderem Seed oder anderer Ausfallrate.

## Aufbau

**Keine Grenzwerte im Code.** Ruhezeit, Höchstarbeitszeit, Verhältniszahlen und
Qualifikationsvorgaben liest die App aus den `rule_*`- und Bedarfsspalten des Datensatzes.
Wer die Regeln ändern will, ändert die Daten, nicht die Anwendung.

**Zwei getrennte Nachfragegrößen.** `ppug_min_*` ist die gesetzliche Untergrenze nach
PpUGV und eine harte Restriktion; `required_*` ist die fachliche Sollbesetzung aus dem
Pflegeaufwand und eine Qualitätskennzahl. Beide werden separat ausgewiesen.

**Planer und Prüfung sind getrennt.** `plan_greedy()` erzeugt den Plan, `evaluate()`
prüft ihn unabhängig davon nach. Ein Verfahren darf seine eigene Regelkonformität nicht
selbst behaupten — sonst wäre der spätere KPI-Vergleich zirkulär.

**Reaktive Umplanung.** Bei einem Ausfall kann der bestehende Plan festgehalten und nur
der betroffene Dienst neu besetzt werden (Schalter in der Seitenleiste). Der Unterschied
zur vollständigen Neuplanung wird als Planstabilität gemessen.

## Methodischer Stand

Der aktuelle Planer ist eine **transparente Greedy-Heuristik** und dient als regelbasierte
Referenz — ausdrücklich kein KI-Verfahren. Der nächste Schritt ist ein zweiter Planer auf
Basis von Constraint Programming mit identischer Schnittstelle:

```python
plan_greedy(ctx, scenario, manual_absences=None, fixed=None) -> PlanResult   # vorhanden
plan_cp(ctx, scenario, manual_absences=None, fixed=None)     -> PlanResult   # geplant
```

Erst dann steht Heuristik gegen Optimierung, und der Vergleich in der Hausarbeit hat einen
echten Kontrast.

## Tests

```bash
python test_planner.py      # Planungslogik gegen den Datensatz
python validate_dataset.py  # Datensatz gegen Schema, Recht, Erfüllbarkeit, PpUGV
```

Beide Skripte laufen ohne Streamlit und geben Exit-Code 0 zurück, wenn alle harten
Prüfungen bestanden sind.

## Datenschutz

Mitarbeitende sind pseudonyme IDs, Ausfälle reine Verfügbarkeitsereignisse ohne Grund
oder Diagnose. Der Datensatz ist vollständig synthetisch; reale Werte gehen nur als
veröffentlichte Aggregatkennzahlen ein. Details in `DATENKONZEPT.md`, Abschnitt 7.
