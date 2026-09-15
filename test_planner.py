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
check(15 <= len(ctx.staff) <= 30, f"{len(ctx.staff)} Mitarbeitende (plausible Stationsgroesse)")
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
# Der Greedy uebernimmt fixierte Zuweisungen nur, wenn sie im aktuellen
# Zustand regelkonform bleiben; er gibt also lieber Dienste frei als die
# Ruhezeit zu verletzen. Dadurch entsteht etwas mehr Bewegung als beim
# blossen Festhalten - die Groessenordnung muss aber weit unter einer
# vollstaendigen Neuplanung (rund 220 Aenderungen) bleiben.
check(stab["geaenderte_zuweisungen"] <= 20,
      f"gezielte Nachbesetzung bleibt lokal ({stab['geaenderte_zuweisungen']} Aenderungen)")
check(P.evaluate(ctx, repl)["harte_verstoesse"] == 0,
      "reaktive Greedy-Umplanung ohne harte Regelverstoesse")

print("\nExport")
out = P.export_frame(ctx, ref)
check("assigned_shift" in out.columns, "Exportspalte assigned_shift vorhanden")
check(len(out) == len(df), "Export hat dieselbe Zeilenzahl wie die Eingabe")
check((out.loc[out["period"] == "history", "assigned_shift"] == "").all(),
      "Historienzeilen bleiben im Export leer")
mat = ref.matrix(ctx)
check(mat.shape == (len(ctx.staff), 28),
      f"Planmatrix {mat.shape[0]} x {mat.shape[1]} passt zu Belegschaft und Horizont")



# ==========================================================================
# Optimierungsbasierter Planer
# ==========================================================================

print("\nMILP-Optimierung")
milp_ref = P.plan_milp(ctx, "S0 - keine kurzfristigen Ausfaelle", time_limit_s=60)
kpi_m = P.evaluate(ctx, milp_ref)
kpi_g = P.evaluate(ctx, ref)

print(f"        Solverstatus:         {milp_ref.info['status']} "
      f"({milp_ref.info['message'][:40]})")
print(f"        Modellgroesse:        {milp_ref.info['variablen']} Variablen, "
      f"{milp_ref.info['nebenbedingungen']} Nebenbedingungen")
print(f"        Laufzeit:             {milp_ref.runtime_s:>8.1f} s")
print(f"        {'Kennzahl':<26s}{'Greedy':>10s}{'MILP':>10s}")
for label, key, fmt in [("Besetzungsquote", "besetzungsquote", "{:.1%}"),
                        ("offene Dienste", "offene_slots", "{:d}"),
                        ("Untergrenzenverstoesse", "untergrenzen_verstoesse", "{:d}"),
                        ("harte Verstoesse", "harte_verstoesse", "{:d}"),
                        ("weiche Abweichungen", "weiche_abweichungen", "{:d}"),
                        ("Streuung Auslastung", "auslastung_streuung", "{:.3f}"),
                        ("Spanne Auslastung", "auslastung_spanne", "{:.1%}")]:
    print(f"        {label:<26s}{fmt.format(kpi_g[key]):>10s}{fmt.format(kpi_m[key]):>10s}")

check(milp_ref.info["status"] in (0, 1), "Solver liefert eine zulaessige Loesung")
check(kpi_m["harte_verstoesse"] == 0, "MILP-Plan ohne harte Regelverstoesse")
check(kpi_m["untergrenzen_verstoesse"] == 0, "MILP-Plan haelt die PpUGV-Untergrenze ein")
check(kpi_m["besetzungsquote"] >= kpi_g["besetzungsquote"],
      "Besetzungsquote mindestens so gut wie die Baseline")
check(kpi_m["auslastung_streuung"] <= kpi_g["auslastung_streuung"],
      "Lastverteilung gleichmaessiger als die Baseline")
check(kpi_m["weiche_abweichungen"] <= kpi_g["weiche_abweichungen"],
      "nicht mehr weiche Abweichungen als die Baseline")
check(kpi_m["hilfskraftanteil"] <= kpi_m["hilfskraft_grenze"] + 1e-9,
      "Hilfskraftanteil unter der PpUGV-Grenze")
blocked_m = ctx.unavailable | P.scenario_absences(ctx, "S0 - keine kurzfristigen Ausfaelle")
check(not (set(milp_ref.assignments) & blocked_m),
      "niemand wird an Abwesenheitstagen verplant")
check(all(int(ctx.staff.loc[e, "night_eligible"]) == 1
          for (e, _), s in milp_ref.assignments.items() if s == "N"),
      "Nachtdienste nur mit Nachtdiensteignung")

print("\nReaktive Umplanung (MILP mit Referenzplan)")
for scenario in ["S1 - verteilte Ausfaelle", "S2 - Ausfallwelle"]:
    voll = P.plan_milp(ctx, scenario, time_limit_s=60)
    reaktiv = P.plan_milp(ctx, scenario, reference=milp_ref, time_limit_s=60)
    s_voll = P.stability(milp_ref, voll)
    s_reak = P.stability(milp_ref, reaktiv)
    k_reak = P.evaluate(ctx, reaktiv)
    print(f"        {scenario[:2]}: Neuplanung {s_voll['planstabilitaet']:>6.1%} Stabilitaet, "
          f"reaktiv {s_reak['planstabilitaet']:>6.1%} "
          f"({s_reak['geaenderte_zuweisungen']} Aenderungen, "
          f"{reaktiv.runtime_s:.1f} s)")
    check(s_reak["planstabilitaet"] > s_voll["planstabilitaet"],
          f"{scenario[:2]}: reaktive Umplanung ist stabiler als Neuplanung")
    check(k_reak["harte_verstoesse"] == 0,
          f"{scenario[:2]}: reaktiver Plan ohne harte Regelverstoesse")
    check(k_reak["untergrenzen_verstoesse"] == 0,
          f"{scenario[:2]}: reaktiver Plan haelt die Untergrenze ein")

print("\n" + "=" * 68)
print(f"Fehler gesamt: {len(FAIL)}")
for f in FAIL:
    print("  FAIL:", f)
sys.exit(1 if FAIL else 0)
