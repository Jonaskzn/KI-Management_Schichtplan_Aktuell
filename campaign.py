#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluationskampagne: beide Planungsverfahren ueber mehrere Instanzen.

Warum das noetig ist: Eine einzelne Instanz sagt nichts darueber, ob ein
Unterschied zwischen zwei Verfahren systematisch ist oder Zufall. Die Kampagne
variiert deshalb zwei Dinge unabhaengig voneinander:

  Seed            - andere Belegung, andere Belegschaft, andere Ausfaelle
  staffing_factor - Personaldecke relativ zum rechnerischen Bruttobedarf
                    (1,00 = bedarfsgerecht, 0,80 = zwanzig Prozent darunter)

Der zweite Faktor ist der wichtigere: Bei bedarfsgerechter Besetzung erreichen
beide Verfahren die Sollbesetzung, der Unterschied liegt nur in der Verteilung.
Erst unter Knappheit zeigt sich, ob die Optimierung auch die Versorgung besser
sichert - genau das ist die Frage, die eine einzelne Instanz offenlaesst.

Ergebnis: evaluation_results.csv (eine Zeile je Instanz x Szenario x Verfahren)

    python campaign.py                # voller Lauf
    python campaign.py --quick        # kleiner Probelauf
"""

from __future__ import annotations

import csv
import os
import sys
import tempfile
import time

import generate_dataset as G
import planner as P

BASE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(BASE, "evaluation_results.csv")

SEEDS = [20261133, 4711, 20260906, 777, 31415]
FACTORS = [1.00, 0.90, 0.80]
TIME_LIMIT = 30.0
REFERENCE_SCENARIO = "S0 - keine kurzfristigen Ausfaelle"

FIELDS = [
    "seed", "staffing_factor", "headcount", "fte", "fte_netto_bedarf",
    "fte_brutto_ziel", "soll_dienste", "scenario", "method",
    "besetzungsquote", "offene_slots", "untergrenzen_verstoesse",
    "harte_verstoesse", "weiche_abweichungen", "qualifikationsverstoesse",
    "hilfskraftanteil", "auslastung_mittel", "auslastung_streuung",
    "auslastung_spanne", "arbeitszeitabweichung", "planstabilitaet",
    "geaenderte_zuweisungen", "planungszeit_s", "solver_status",
]


def run_instance(seed: int, factor: float, time_limit: float) -> list[dict]:
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "instanz.csv")
        meta = G.write_instance(path, seed=seed, staffing_factor=factor)
        df = P.load_dataset(path)
    ctx = P.build_context(df)

    ref_greedy = P.plan_greedy(ctx, REFERENCE_SCENARIO)
    ref_milp = P.plan_milp(ctx, REFERENCE_SCENARIO, time_limit_s=time_limit)

    rows = []
    for scenario in P.SCENARIOS:
        # Reaktive Varianten werden zusaetzlich ueber Kreuz gerechnet: jedes
        # Verfahren repariert einmal seinen eigenen und einmal den fremden
        # Ausgangsplan. Nur auf identischem Ausgangsplan ist die Planstabilitaet
        # zwischen den Verfahren vergleichbar - ein schlechter Ausgangsplan
        # laesst sich billiger unveraendert lassen als ein guter.
        plans = {
            "Greedy": (P.plan_greedy(ctx, scenario), ref_greedy),
            "Greedy reaktiv": (P.plan_greedy(ctx, scenario,
                                             fixed=ref_greedy.assignments), ref_greedy),
            "MILP": (P.plan_milp(ctx, scenario, time_limit_s=time_limit), ref_milp),
            "MILP reaktiv": (P.plan_milp(ctx, scenario, reference=ref_milp,
                                         time_limit_s=time_limit), ref_milp),
            # Kreuzvergleich: gleicher Ausgangsplan, unterschiedliches Verfahren
            "Greedy auf MILP-Plan": (P.plan_greedy(ctx, scenario,
                                                   fixed=ref_milp.assignments), ref_milp),
            "MILP auf Greedy-Plan": (P.plan_milp(ctx, scenario, reference=ref_greedy,
                                                 time_limit_s=time_limit), ref_greedy),
        }
        for name, (plan, ref) in plans.items():
            k = P.evaluate(ctx, plan)
            s = P.stability(ref, plan)
            rows.append({
                "seed": seed, "staffing_factor": factor,
                "headcount": meta["headcount"], "fte": meta["fte"],
                "fte_netto_bedarf": meta["fte_netto_bedarf"],
                "fte_brutto_ziel": meta["fte_brutto_ziel"],
                "soll_dienste": meta["soll_dienste"],
                "scenario": scenario[:2], "method": name,
                "besetzungsquote": round(k["besetzungsquote"], 4),
                "offene_slots": k["offene_slots"],
                "untergrenzen_verstoesse": k["untergrenzen_verstoesse"],
                "harte_verstoesse": k["harte_verstoesse"],
                "weiche_abweichungen": k["weiche_abweichungen"],
                "qualifikationsverstoesse": k["qualifikationsverstoesse"],
                "hilfskraftanteil": round(k["hilfskraftanteil"], 4),
                "auslastung_mittel": round(k["auslastung_mittel"], 4),
                "auslastung_streuung": round(k["auslastung_streuung"], 4),
                "auslastung_spanne": round(k["auslastung_spanne"], 4),
                "arbeitszeitabweichung": round(k["arbeitszeitabweichung"], 4),
                "planstabilitaet": round(s["planstabilitaet"], 4),
                "geaenderte_zuweisungen": s["geaenderte_zuweisungen"],
                "planungszeit_s": round(k["planungszeit_s"], 3),
                "solver_status": plan.info.get("status", ""),
            })
    return rows


def main(quick: bool = False):
    seeds = SEEDS[:2] if quick else SEEDS
    factors = [1.00, 0.80] if quick else FACTORS
    limit = 10.0 if quick else TIME_LIMIT

    total = len(seeds) * len(factors)
    t0 = time.perf_counter()
    with open(RESULTS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        done = 0
        for factor in factors:
            for seed in seeds:
                t = time.perf_counter()
                rows = run_instance(seed, factor, limit)
                writer.writerows(rows)
                f.flush()
                done += 1
                print(f"[{done}/{total}] Seed {seed}, Faktor {factor:.2f} "
                      f"-> {len(rows)} Zeilen in {time.perf_counter() - t:.1f}s",
                      flush=True)
    print(f"\nFertig in {(time.perf_counter() - t0) / 60:.1f} Minuten "
          f"-> {os.path.basename(RESULTS)}")




# --------------------------------------------------------------------------
# Auswertung
# --------------------------------------------------------------------------

def report(path: str = RESULTS) -> str:
    """Aggregiert die Kampagne zu den Tabellen fuer die Hausarbeit."""
    import pandas as pd

    d = pd.read_csv(path)
    n_inst = d.groupby("staffing_factor")["seed"].nunique()
    order = ["Greedy", "Greedy reaktiv", "MILP", "MILP reaktiv",
             "Greedy auf MILP-Plan", "MILP auf Greedy-Plan"]
    d["method"] = pd.Categorical(d["method"], order, ordered=True)

    out = []
    out.append(f"Instanzen: {d['seed'].nunique()} Seeds x "
               f"{d['staffing_factor'].nunique()} Personaldecken = "
               f"{len(d.groupby(['seed', 'staffing_factor']))} Instanzen, "
               f"{len(d)} Plaene\n")

    metrics = {
        "besetzungsquote": ("Besetzungsquote", "{:.1%}"),
        "untergrenzen_verstoesse": ("Untergrenzenverstoesse", "{:.2f}"),
        "harte_verstoesse": ("harte Regelverstoesse", "{:.2f}"),
        "weiche_abweichungen": ("weiche Abweichungen", "{:.1f}"),
        "auslastung_streuung": ("Streuung Auslastung", "{:.3f}"),
        "planstabilitaet": ("Planstabilitaet", "{:.1%}"),
        "planungszeit_s": ("Planungszeit (s)", "{:.2f}"),
    }

    basis = ["Greedy", "Greedy reaktiv", "MILP", "MILP reaktiv"]

    for factor, block in d.groupby("staffing_factor"):
        out.append(f"\n### Personaldecke {factor:.0%} des Bruttobedarfs "
                   f"({n_inst[factor]} Seeds, Ø {block['headcount'].mean():.0f} Koepfe)\n")
        head = f"{'Kennzahl':<26s}" + "".join(f"{m:>17s}" for m in basis)
        out.append(head)
        out.append("-" * len(head))
        for key, (label, fmt) in metrics.items():
            cells = []
            for m in basis:
                sub = block[block["method"] == m][key]
                mean, sd = sub.mean(), sub.std()
                cells.append(f"{fmt.format(mean)} ±{fmt.format(sd).lstrip('0')}"
                             if key not in ("besetzungsquote", "planstabilitaet")
                             else f"{fmt.format(mean)}")
            out.append(f"{label:<26s}" + "".join(f"{c:>17s}" for c in cells))

    out.append("\n\n### Fairer Stabilitaetsvergleich: identischer Ausgangsplan\n")
    out.append("Planstabilitaet ist nur vergleichbar, wenn beide Verfahren denselben\n"
               "Ausgangsplan reparieren - ein schlechter Plan laesst sich billiger\n"
               "unveraendert lassen als ein guter.\n")
    paare = [("Ausgangsplan der Heuristik", "Greedy reaktiv", "MILP auf Greedy-Plan"),
             ("Ausgangsplan der Optimierung", "Greedy auf MILP-Plan", "MILP reaktiv")]
    for titel, m_g, m_m in paare:
        out.append(f"\n  {titel}")
        for key, label in [("planstabilitaet", "Planstabilitaet"),
                           ("geaenderte_zuweisungen", "geaenderte Zuweisungen"),
                           ("weiche_abweichungen", "weiche Abweichungen"),
                           ("harte_verstoesse", "harte Regelverstoesse"),
                           ("offene_slots", "offene Dienste")]:
            g = d[d["method"] == m_g][key].mean()
            m = d[d["method"] == m_m][key].mean()
            f = "{:.1%}" if key == "planstabilitaet" else "{:.2f}"
            out.append(f"    {label:<24s} Heuristik {f.format(g):>8s}   "
                       f"Optimierung {f.format(m):>8s}")

    out.append("\n\n### Verstoesse nach Szenario (alle Personaldecken)\n")
    piv = d.pivot_table(index=["scenario", "method"], observed=True,
                        values=["besetzungsquote", "untergrenzen_verstoesse",
                                "harte_verstoesse", "planstabilitaet"],
                        aggfunc="mean")
    out.append(piv.round(3).to_string())

    out.append("\n\n### Anteil regelkonformer Plaene (keine harten Verstoesse, "
               "keine Untergrenzenverstoesse)\n")
    d["konform"] = ((d["harte_verstoesse"] == 0)
                    & (d["untergrenzen_verstoesse"] == 0))
    konform = d.pivot_table(index="method", columns="staffing_factor",
                            values="konform", aggfunc="mean", observed=True)
    out.append((konform * 100).round(1).to_string() + "   (Prozent)")
    return "\n".join(out)




if __name__ == "__main__":
    if "--report" in sys.argv:
        print(report())
    else:
        main(quick="--quick" in sys.argv)
