#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sensitivitaetsanalyse der Zielgewichte
======================================
Frage: Wie stark haengen die Ergebnisse der reaktiven Umplanung am Gewicht
`keep` (Belohnung je beibehaltener Zuweisung)?

Hintergrund: In der Zielfunktion steht `keep` = 200 je Zuweisung gegen
`fair` = 0,02 je Minute Abweichung von der Zielarbeitszeit. Eine Person um
500 Minuten besser auszulasten ist damit 10 Punkte wert, eine einzige
Zuweisung aufzubrechen kostet 200. Das Modell verzichtet deshalb rational auf
Umverteilung - nicht, weil es sie nicht koennte.

Diese Analyse variiert `keep` und misst, wie sich Lastverteilung und
Planstabilitaet gegeneinander bewegen. Gerechnet wird auf dem Ausgangsplan der
Heuristik, weil dort der Zielkonflikt am deutlichsten wird.

    python sensitivitaet.py           ->  sensitivitaet.csv
    python sensitivitaet.py --report  ->  aggregierte Auswertung
"""

from __future__ import annotations

import io
import os
import sys
import time

import pandas as pd

import campaign as C
import generate_dataset as G
import planner as P

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "sensitivitaet.csv")

KEEP_WERTE = [200, 50, 20, 5, 0]      # 200 = Standard
FAKTOR = 1.00                          # bedarfsgerechte Personaldecke
SZENARIO = "S2 - Ausfallwelle"
REFERENZ = "S0 - keine kurzfristigen Ausfaelle"


def main() -> None:
    rows = []
    t0 = time.perf_counter()
    for i, seed in enumerate(C.SEEDS, 1):
        comb, _ = G.build_dataset(seed, FAKTOR)
        buf = io.StringIO()
        pd.DataFrame(comb).to_csv(buf, index=False)
        buf.seek(0)
        ctx = P.build_context(P.load_dataset(buf))

        ref = P.plan_greedy(ctx, REFERENZ)
        k_ref = P.evaluate(ctx, ref)

        # Vergleichspunkt: die Heuristik repariert ihren eigenen Plan
        gr = P.plan_greedy(ctx, SZENARIO, fixed=ref.assignments)
        s_gr, k_gr = P.stability(ref, gr), P.evaluate(ctx, gr)
        rows.append({"seed": seed, "verfahren": "Regelbasiert", "keep": None,
                     "spanne": k_gr["auslastung_spanne"],
                     "streuung": k_gr["auslastung_streuung"],
                     "planstabilitaet": s_gr["planstabilitaet"],
                     "geaenderte_zuweisungen": s_gr["geaenderte_zuweisungen"],
                     "weiche_abweichungen": k_gr["weiche_abweichungen"],
                     "harte_verstoesse": k_gr["harte_verstoesse"],
                     "offene_slots": k_gr["offene_slots"],
                     "ref_spanne": k_ref["auslastung_spanne"]})

        for keep in KEEP_WERTE:
            w = dict(P.WEIGHTS)
            w["keep"] = float(keep)
            r = P.plan_milp(ctx, SZENARIO, reference=ref, weights=w,
                            time_limit_s=60.0)
            st, k = P.stability(ref, r), P.evaluate(ctx, r)
            rows.append({"seed": seed, "verfahren": "MILP", "keep": keep,
                         "spanne": k["auslastung_spanne"],
                         "streuung": k["auslastung_streuung"],
                         "planstabilitaet": st["planstabilitaet"],
                         "geaenderte_zuweisungen": st["geaenderte_zuweisungen"],
                         "weiche_abweichungen": k["weiche_abweichungen"],
                         "harte_verstoesse": k["harte_verstoesse"],
                         "offene_slots": k["offene_slots"],
                         "ref_spanne": k_ref["auslastung_spanne"]})
        print(f"  [{i}/{len(C.SEEDS)}] Seed {seed}")

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nFertig in {(time.perf_counter() - t0) / 60:.1f} Minuten -> {OUT}")
    print()
    print(report())


def report(path: str = OUT) -> str:
    d = pd.read_csv(path)
    out = [f"Sensitivitaet des Gewichts 'keep' | Szenario {SZENARIO[:2]}, "
           f"Personaldecke {FAKTOR:.0%}, {d.seed.nunique()} Seeds\n"]
    g = d[d.verfahren == "Regelbasiert"]
    out.append(f"{'Verfahren':<26s}{'Spanne':>9s}{'Stabilitaet':>13s}"
               f"{'Aenderungen':>13s}{'weich':>8s}")
    out.append("-" * 69)
    out.append(f"{'Regelbasiert (Referenz)':<26s}{g.spanne.mean():>9.3f}"
               f"{g.planstabilitaet.mean():>12.1%}"
               f"{g.geaenderte_zuweisungen.mean():>13.1f}"
               f"{g.weiche_abweichungen.mean():>8.1f}")
    for keep in KEEP_WERTE:
        m = d[(d.verfahren == "MILP") & (d.keep == keep)]
        if m.empty:
            continue
        label = f"MILP, keep = {keep}" + (" (Standard)" if keep == 200 else "")
        out.append(f"{label:<26s}{m.spanne.mean():>9.3f}"
                   f"{m.planstabilitaet.mean():>12.1%}"
                   f"{m.geaenderte_zuweisungen.mean():>13.1f}"
                   f"{m.weiche_abweichungen.mean():>8.1f}")
    out.append("\nAusgangsplan der Heuristik: Spanne "
               f"{d.ref_spanne.mean():.3f}")
    return "\n".join(out)


if __name__ == "__main__":
    if "--report" in sys.argv:
        print(report())
    else:
        main()
