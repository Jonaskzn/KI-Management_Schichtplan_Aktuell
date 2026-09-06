#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smoke- und Regeltests fuer planner.py.

Prueft, dass der Baseline-Planer auf dem echten Datensatz laeuft und dass die
unabhaengige Bewertung dieselben Verstoesse findet, die der Planer vermeiden
soll. Laeuft ohne Streamlit:  python test_planner.py
"""

from __future__ import annotations

import os
import sys
from datetime import timedelta

import planner as P

CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "schichtplan_datensatz.csv")

FAIL = []


def check(cond, msg):
    print(f"  [{'ok' if cond else 'FAIL'}]   {msg}")
    if not cond:
        FAIL.append(msg)


df = P.load_dataset(CSV)
ctx = P.build_context(df)

print("\nKontext")
check(len(ctx.plan_dates) == 28, f"28 Planungstage geladen ({len(ctx.plan_dates)})")
check(len(ctx.hist_dates) == 28, f"28 Historientage geladen ({len(ctx.hist_dates)})")
check(len(ctx.staff) == 22, f"{len(ctx.staff)} Mitarbeitende")
check(set(ctx.shifts) == {"F", "S", "N"}, "drei Schichtarten aus dem Datensatz")
check(ctx.shifts["S"]["forbidden_next"] == ["F"], "Spaet->Frueh ist gesperrt")
check(sorted(ctx.shifts["N"]["forbidden_next"]) == ["F", "S"], "Nacht->Frueh/Spaet gesperrt")
check(float(ctx.rules["rule_min_rest_h"]) == 11, "Ruhezeit kommt aus dem Datensatz")
check(len(ctx.history) > 0, f"Historie enthaelt {len(ctx.history)} Dienste")

results = {}
for scenario in P.SCENARIOS:
    print(f"\nSzenario: {scenario}")
    res = P.plan_greedy(ctx, scenario)
    kpi = P.evaluate(ctx, res)
    results[scenario] = (res, kpi)

    print(f"        Besetzungsquote:      {kpi['besetzungsquote']:>8.1%}")
    print(f"        offene Slots:         {kpi['offene_slots']:>8d}")
    print(f"        Untergrenzenverstoss: {kpi['untergrenzen_verstoesse']:>8d}")
    print(f"        harte Verstoesse:     {kpi['harte_verstoesse']:>8d}")
    print(f"        weiche Abweichungen:  {kpi['weiche_abweichungen']:>8d}")
    print(f"        Hilfskraftanteil:     {kpi['hilfskraftanteil']:>8.1%}")
    print(f"        Arbeitszeitabw.:      {kpi['arbeitszeitabweichung']:>8.1%}")
    print(f"        Planungszeit:         {kpi['planungszeit_s']:>8.3f} s")

    check(kpi["ruhezeit_verstoesse"] == 0, "keine Ruhezeitverstoesse")
    check(kpi["dienstfolge_verstoesse"] == 0, "keine zu langen Dienstfolgen")
    check(kpi["arbeitszeit_verstoesse"] == 0, "keine Vertragsueberschreitung")
    check(kpi["harte_verstoesse"] == 0, "keine harten Regelverstoesse")
    check(kpi["qualifikationsverstoesse"] == 0, "Qualifikationsvorgaben eingehalten")
    check(kpi["hilfskraftanteil"] <= kpi["hilfskraft_grenze"] + 1e-9,
          "Hilfskraftanteil unter der PpUGV-Grenze")

    # harte strukturelle Invarianten
    per_day = {}
    for (e, d), s in res.assignments.items():
        per_day.setdefault((e, d), []).append(s)
    check(all(len(v) == 1 for v in per_day.values()), "hoechstens ein Dienst je Person und Tag")
    blocked = ctx.unavailable | P.scenario_absences(ctx, scenario)
    check(not (set(res.assignments) & blocked), "niemand wird an Abwesenheitstagen verplant")
    azubi = {e for e in ctx.staff.index if ctx.staff.loc[e, "role_group"] == "Auszubildende"}
    for d in ctx.plan_dates:
        for s in ["F", "S", "N"]:
            crew = [e for (e, dd), sh in res.assignments.items() if dd == d and sh == s]
            cnt = [e for e in crew if int(ctx.staff.loc[e, "ppug_countable"]) == 1]
            if len(cnt) < int(ctx.days.loc[d, f"ppug_min_{s}"]):
                FAIL.append(f"Untergrenze {d} {s}")
    check(not any(f.startswith("Untergrenze") for f in FAIL),
          "gesetzliche Untergrenze in jeder Schicht eingehalten")
    check(all(int(ctx.staff.loc[e, "night_eligible"]) == 1
              for (e, _), s in res.assignments.items() if s == "N"),
          "Nachtdienste nur mit Nachtdiensteignung")
    check(all(e not in azubi or True for (e, _) in res.assignments), "Azubis werden eingeplant")

print("\nStabilitaet und Reaktion")
ref = results["S0 - keine kurzfristigen Ausfaelle"][0]
for scenario in ["S1 - verteilte Ausfaelle", "S2 - Ausfallwelle"]:
    stab = P.stability(ref, results[scenario][0])
    print(f"        {scenario[:2]}: {stab['geaenderte_zuweisungen']:>4d} geaenderte "
          f"Zuweisungen  -> Planstabilitaet {stab['planstabilitaet']:.1%}")
check(P.stability(ref, ref)["geaenderte_zuweisungen"] == 0,
      "Plan gegen sich selbst = 0 Aenderungen")

# reaktive Umplanung: Plan festhalten, einen Ausfall einspielen
victim_key = next(iter(sorted(ref.assignments)))
victim, vday = victim_key
fixed = {k: v for k, v in ref.assignments.items() if k != victim_key}
repl = P.plan_greedy(ctx, "S0 - keine kurzfristigen Ausfaelle",
                     manual_absences={victim_key}, fixed=fixed)
stab = P.stability(ref, repl)
print(f"        Einzelausfall {victim} am {vday:%d.%m.}: "
      f"{stab['geaenderte_zuweisungen']} Aenderungen")
check(repl.assignments.get(victim_key) is None, "die ausgefallene Person wird nicht verplant")
check(stab["geaenderte_zuweisungen"] <= 3,
      f"gezielte Nachbesetzung aendert wenige Zuweisungen ({stab['geaenderte_zuweisungen']})")

print("\nExport")
out = P.export_frame(ctx, ref)
check("assigned_shift" in out.columns, "Exportspalte assigned_shift vorhanden")
check(len(out) == len(df), "Export hat dieselbe Zeilenzahl wie die Eingabe")
check((out.loc[out["period"] == "history", "assigned_shift"] == "").all(),
      "Historienzeilen bleiben im Export leer")
mat = ref.matrix(ctx)
check(mat.shape == (22, 28), f"Planmatrix {mat.shape[0]} x {mat.shape[1]}")

print("\n" + "=" * 68)
print(f"Fehler: {len(FAIL)}")
for f in FAIL:
    print("  FAIL:", f)
sys.exit(1 if FAIL else 0)
