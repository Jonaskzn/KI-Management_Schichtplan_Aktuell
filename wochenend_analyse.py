#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verteilung der Wochenenddienste je Person, gepoolt ueber alle Kampagneninstanzen.

Hintergrund: 95 % der weichen Abweichungen in den Plaenen der Heuristik sind
Ueberschreitungen des Wochenend-Richtwerts (hoechstens zwei Wochenenden je vier
Wochen, Annahme A10). Diese Auswertung zeigt, wie sich die Wochenenddienste
tatsaechlich auf die Belegschaft verteilen - die anschaulichste Form des
Verteilungsunterschieds zwischen beiden Verfahren.

Gerechnet wird auf Szenario S0 (ungestoerte Planerstellung), weil es um die
Qualitaet der Planerstellung geht, nicht um die Reaktion auf Ausfaelle.

    python wochenend_analyse.py   ->  wochenend_verteilung.csv
"""

from __future__ import annotations

import io
import os

import pandas as pd

import campaign as C
import generate_dataset as G
import planner as P

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "wochenend_verteilung.csv")
SZENARIO = "S0 - keine kurzfristigen Ausfaelle"


def wochenenden_je_person(ctx, result) -> dict[str, int]:
    """Anzahl verschiedener Kalenderwochen mit Wochenenddienst je Person."""
    zaehler: dict[str, set] = {e: set() for e in ctx.staff.index}
    for (e, d), _s in result.assignments.items():
        if d.weekday() >= 5:
            zaehler[e].add(d.isocalendar()[1])
    return {e: len(w) for e, w in zaehler.items()}


def main() -> None:
    rows = []
    gesamt = len(C.SEEDS) * len(C.FACTORS)
    i = 0
    for seed in C.SEEDS:
        for faktor in C.FACTORS:
            i += 1
            comb, _ = G.build_dataset(seed, faktor)
            buf = io.StringIO()
            pd.DataFrame(comb).to_csv(buf, index=False)
            buf.seek(0)
            ctx = P.build_context(P.load_dataset(buf))
            plaene = {
                "Regelbasiert": P.plan_greedy(ctx, SZENARIO),
                "MILP": P.plan_milp(ctx, SZENARIO, time_limit_s=30.0),
            }
            for verfahren, plan in plaene.items():
                richtwert = int(ctx.staff["max_weekends"].iloc[0])
                for e, n in wochenenden_je_person(ctx, plan).items():
                    rows.append({"seed": seed, "staffing_factor": faktor,
                                 "method": verfahren, "employee_id": e,
                                 "wochenenden": n, "richtwert": richtwert})
            print(f"  [{i}/{gesamt}] Seed {seed}, Faktor {faktor:.2f}")

    d = pd.DataFrame(rows)
    d.to_csv(OUT, index=False)
    print(f"\n{OUT}: {len(d)} Zeilen")
    print("\nVerteilung (Anteil der Personen je Zahl von Wochenenddiensten):")
    tab = (d.pivot_table(index="wochenenden", columns="method",
                         values="employee_id", aggfunc="count")
             .fillna(0))
    print((tab / tab.sum() * 100).round(1).to_string())
    ueber = d[d.wochenenden > d.richtwert]
    print("\nAnteil der Personen ueber dem Richtwert:")
    print((ueber.groupby("method").size() / d.groupby("method").size() * 100)
          .round(1).to_string())


if __name__ == "__main__":
    main()
