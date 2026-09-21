#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alle Kennzahlen der Ausarbeitung aus den Rohdaten
=================================================
Jede Zahl in ERGEBNISSE.md, Abschnitte 2 bis 5, stammt aus diesem Skript.
Nichts ist von Hand eingetragen: Wer die Kampagne neu rechnet und dieses
Skript laufen laesst, bekommt dieselben Zahlen.

    python auswertung.py                          # evaluation_results.csv
    python auswertung.py pfad/zu/ergebnissen.csv  # andere Kampagne

Die Abschnittsnummern im Ausdruck entsprechen denen in ERGEBNISSE.md.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(BASE, "evaluation_results.csv")

GESTOERT = ["S1", "S2"]
KPI = [("planstabilitaet", "{:.1%}"), ("geaenderte_zuweisungen", "{:.1f}"),
       ("besetzungsquote", "{:.1%}"), ("offene_slots", "{:.2f}"),
       ("untergrenzen_verstoesse", "{:.2f}"), ("harte_verstoesse", "{:.2f}"),
       ("weiche_abweichungen", "{:.2f}"), ("auslastung_spanne", "{:.3f}")]


def ausfalltage(seeds, faktoren, ward="innere") -> pd.DataFrame:
    """Ausfalltage je Instanz aus dem Generator (stehen nicht in der Kampagnen-CSV)."""
    import generate_dataset as G
    rows = []
    for f in faktoren:
        for s in seeds:
            comb, _ = G.build_dataset(int(s), float(f), ward)
            rows.append({"seed": s, "staffing_factor": f,
                         "tage_s1": sum(int(r["absence_s1"]) for r in comb),
                         "tage_s2": sum(int(r["absence_s2"]) for r in comb)})
    return pd.DataFrame(rows)


def m(d, method, col, **filt):
    sub = d[d.method == method]
    for k, v in filt.items():
        sub = sub[sub[k].isin(v) if isinstance(v, (list, tuple)) else sub[k] == v]
    return sub[col]


def main(path: str = CSV) -> None:
    d = pd.read_csv(path)
    ward = d["ward"].iloc[0] if "ward" in d.columns else "innere"
    p = print

    p(f"Quelle: {os.path.basename(path)} | {len(d)} Plaene | Station {ward}\n")

    # ------------------------------------------------------------------ 2.2
    p("=== 2.2 Ergebnisse nach Personaldecke (Mittel ueber 5 Seeds x 3 Szenarien)")
    basis = ["Greedy", "Greedy reaktiv", "MILP", "MILP reaktiv"]
    for f in [1.00, 0.90, 0.80]:
        b = d[d.staffing_factor == f]
        p(f"\n  Personaldecke {f:.0%}, Koepfe {b.headcount.mean():.0f}")
        for col, fmt in [("besetzungsquote", "{:.1%}"), ("untergrenzen_verstoesse", "{:.2f}"),
                         ("harte_verstoesse", "{:.2f}"), ("weiche_abweichungen", "{:.1f}"),
                         ("auslastung_streuung", "{:.3f}"), ("auslastung_spanne", "{:.3f}"),
                         ("planstabilitaet", "{:.1%}"), ("planungszeit_s", "{:.2f}")]:
            cells = []
            for meth in basis:
                # Planstabilitaet nur ueber gestoerte Plaene: In S0 gibt es
                # nichts anzupassen, die Zeile wuerde sonst mit 100 % verduennt.
                x = (m(b, meth, col, scenario=GESTOERT) if col == "planstabilitaet"
                     else m(b, meth, col))
                sd = f" ±{fmt.format(x.std())}" if col not in ("besetzungsquote", "planstabilitaet") else ""
                cells.append(fmt.format(x.mean()) + sd)
            p(f"    {col:26s} " + " | ".join(f"{c:>16s}" for c in cells))
    p("\n  Anteil regelkonformer Plaene (keine harten, keine Untergrenzenverstoesse)")
    d["konform"] = (d.harte_verstoesse == 0) & (d.untergrenzen_verstoesse == 0)
    for meth in basis:
        p(f"    {meth:16s} " + "  ".join(
            f"{f:.0%}: {m(d, meth, 'konform', staffing_factor=f).mean():.0%}"
            for f in [0.80, 0.90, 1.00]))
    g80 = d[(d.method == "Greedy") & (d.staffing_factor == 0.80)]
    p(f"  Greedy bei 80 %: {int(g80.offene_slots.sum())} offene Dienste, "
      f"{int(g80.untergrenzen_verstoesse.sum())} Untergrenzenverstoesse")
    milp3 = d[d.method.isin(["MILP", "MILP reaktiv", "MILP auf Greedy-Plan"])]
    p(f"  alle drei MILP-Varianten ({len(milp3)} Plaene): hart {int(milp3.harte_verstoesse.sum())}, "
      f"Untergrenze {int(milp3.untergrenzen_verstoesse.sum())}, offen {int(milp3.offene_slots.sum())} "
      f"(davon bei 80 %: {int(milp3[milp3.staffing_factor == 0.80].offene_slots.sum())}, "
      f"in S0: {int(milp3[milp3.scenario == 'S0'].offene_slots.sum())}; "
      f"Plaene mit offenen Diensten: {int((milp3.offene_slots > 0).sum())})")
    m80 = d[(d.method == "MILP") & (d.staffing_factor == 0.80)]
    p(f"  MILP Neuplanung bei 80 %: offen {int(m80.offene_slots.sum())}, Untergrenze "
      f"{int(m80.untergrenzen_verstoesse.sum())}")
    milp_all = d[d.method.isin(["MILP", "MILP reaktiv"])]
    p(f"  MILP + MILP reaktiv ({len(milp_all)} Plaene): hart {int(milp_all.harte_verstoesse.sum())}, "
      f"Untergrenze {int(milp_all.untergrenzen_verstoesse.sum())}, offen {int(milp_all.offene_slots.sum())}")

    # ------------------------------------------------------------------ 3.1
    p("\n=== 3.1 Nach Ausfallszenario (Mittel ueber 15 Instanzen)")
    for meth, label in [("Greedy", "Regelbasiert, Neuplanung"), ("MILP", "MILP, Neuplanung"),
                        ("Greedy reaktiv", "Regelbasiert, reaktiv"), ("MILP reaktiv", "MILP, reaktiv")]:
        p(f"  Spanne {label:26s} " + "  ".join(
            f"{sc}: {m(d, meth, 'auslastung_spanne', scenario=sc).mean():.3f}" for sc in ["S0", "S1", "S2"]))
    for col in ["offene_slots", "harte_verstoesse", "untergrenzen_verstoesse"]:
        p(f"  {col:22s} Greedy reaktiv  " + "  ".join(
            f"{sc}: {m(d, 'Greedy reaktiv', col, scenario=sc).mean():.2f}" for sc in ["S0", "S1", "S2"]))
    p("  Untergrenzen Greedy (Neuplanung) " + "  ".join(
        f"{sc}: {m(d, 'Greedy', 'untergrenzen_verstoesse', scenario=sc).mean():.2f}" for sc in ["S0", "S1", "S2"]))
    p("  Untergrenzen MILP (Neuplanung)   " + "  ".join(
        f"{sc}: {m(d, 'MILP', 'untergrenzen_verstoesse', scenario=sc).mean():.2f}" for sc in ["S0", "S1", "S2"]))
    p("  mittlere Auslastung S2: Greedy reaktiv "
      f"{m(d, 'Greedy reaktiv', 'auslastung_mittel', scenario='S2').mean():.1%}, MILP reaktiv "
      f"{m(d, 'MILP reaktiv', 'auslastung_mittel', scenario='S2').mean():.1%}")
    p("  offene Dienste S2 Greedy (Neuplanung): "
      f"{m(d, 'Greedy', 'offene_slots', scenario='S2').mean():.2f}, davon bei 80 %: "
      f"{m(d, 'Greedy', 'offene_slots', scenario='S2', staffing_factor=0.80).mean():.2f}")

    p("\n  S2, beide reaktiv auf dem Plan der Optimierung (Greedy auf MILP-Plan | MILP reaktiv)")
    for col, fmt in [("besetzungsquote", "{:.1%}"), ("offene_slots", "{:.2f}"),
                     ("harte_verstoesse", "{:.2f}"), ("weiche_abweichungen", "{:.2f}"),
                     ("auslastung_spanne", "{:.3f}"), ("planstabilitaet", "{:.1%}"),
                     ("geaenderte_zuweisungen", "{:.1f}")]:
        p(f"    {col:24s} {fmt.format(m(d, 'Greedy auf MILP-Plan', col, scenario='S2').mean()):>8s} | "
          f"{fmt.format(m(d, 'MILP reaktiv', col, scenario='S2').mean()):>8s}")

    # ------------------------------------------------------------------ 3.3
    p("\n=== 3.3 Kontrolle fuer das Ausfallvolumen")
    at = ausfalltage(sorted(d.seed.unique()), sorted(d.staffing_factor.unique()), ward)
    p(f"  Ausfalltage im Mittel: S1 {at.tage_s1.mean():.1f}, S2 {at.tage_s2.mean():.1f} "
      f"({(at.tage_s2.mean() - at.tage_s1.mean()) / at.tage_s1.mean():+.1%}); "
      f"Differenz je Instanz {int((at.tage_s2 - at.tage_s1).min()):+d} bis "
      f"{int((at.tage_s2 - at.tage_s1).max()):+d}")
    mr = d[d.method == "MILP reaktiv"].pivot_table(
        index=["seed", "staffing_factor"], columns="scenario",
        values=["auslastung_spanne", "planstabilitaet"])
    diff = pd.DataFrame({
        "spanne": mr[("auslastung_spanne", "S2")] - mr[("auslastung_spanne", "S1")],
        "stab": mr[("planstabilitaet", "S2")] - mr[("planstabilitaet", "S1")],
    }).reset_index().merge(at, on=["seed", "staffing_factor"])
    diff["vol"] = diff.tage_s2 - diff.tage_s1
    kontrolle = diff[diff.vol <= 0]
    for name, sub in [("alle", diff), (f"volumenkontrolliert ({len(kontrolle)})", kontrolle)]:
        p(f"  {name:28s} Spanne S2-S1 {sub.spanne.mean():+.3f} "
          f"({int((sub.spanne > 0).sum())} von {len(sub)} positiv) | Stabilitaet S2-S1 "
          f"{sub.stab.mean() * 100:+.2f} Pp. ({int((sub.stab < 0).sum())} von {len(sub)} negativ)")
    p(f"  Korrelation Volumendifferenz / Stabilitaetsdifferenz: "
      f"{np.corrcoef(diff.vol, diff.stab)[0, 1]:+.2f}")
    p(f"  Korrelation Volumendifferenz / Spannendifferenz:      "
      f"{np.corrcoef(diff.vol, diff.spanne)[0, 1]:+.2f}")
    gr = d[d.method == "Greedy reaktiv"].merge(at, on=["seed", "staffing_factor"])
    gk = gr[gr.tage_s2 <= gr.tage_s1]
    for col in ["harte_verstoesse", "offene_slots"]:
        p(f"  Greedy reaktiv, volumenkontrolliert, {col}: S1 "
          f"{gk[gk.scenario == 'S1'][col].mean():.2f} -> S2 {gk[gk.scenario == 'S2'][col].mean():.2f}")

    # ------------------------------------------------------------------ 4.1
    p("\n=== 4.1 End-to-End (Greedy reaktiv | MILP reaktiv), alle 45 Plaene je Verfahren")
    for col, fmt in [("planstabilitaet", "{:.1%}"), ("geaenderte_zuweisungen", "{:.1f}"),
                     ("besetzungsquote", "{:.1%}"), ("offene_slots", "{:.2f}"),
                     ("untergrenzen_verstoesse", "{:.2f}"), ("harte_verstoesse", "{:.2f}"),
                     ("weiche_abweichungen", "{:.2f}"), ("auslastung_spanne", "{:.3f}")]:
        p(f"    {col:24s} {fmt.format(m(d, 'Greedy reaktiv', col).mean()):>8s} | "
          f"{fmt.format(m(d, 'MILP reaktiv', col).mean()):>8s}")
    a = d[(d.method == "Greedy reaktiv") & d.scenario.isin(GESTOERT)].set_index(
        ["seed", "staffing_factor", "scenario"]).planstabilitaet
    b = d[(d.method == "MILP reaktiv") & d.scenario.isin(GESTOERT)].set_index(
        ["seed", "staffing_factor", "scenario"]).planstabilitaet
    p(f"  MILP stabiler in {int((b > a).sum())} von {len(a)} gestoerten Plaenen "
      f"(gleich: {int((b == a).sum())})")
    p("  nur gestoerte Plaene (S1/S2), 30 je Verfahren - Zustand nach Erstellung und Anpassung:")
    for col, fmt in KPI:
        p(f"    {col:24s} {fmt.format(m(d, 'Greedy reaktiv', col, scenario=GESTOERT).mean()):>8s} | "
          f"{fmt.format(m(d, 'MILP reaktiv', col, scenario=GESTOERT).mean()):>8s}")

    # ------------------------------------------------------------------ 4.2
    p("\n=== 4.2 Methodenkontrolle")
    # Die Ausgangsplaene selbst: "Greedy" in S0 ist der Referenzplan der
    # Heuristik; "MILP reaktiv" in S0 reproduziert den Referenzplan der
    # Optimierung exakt (0 Aenderungen). Die Zeile "MILP" in S0 ist eine
    # zweite, unabhaengige Loesung und kann bei Zeitlimit abweichen.
    for meth, label in [("Greedy", "Ausgangsplan Heuristik"),
                        ("MILP reaktiv", "Ausgangsplan Optimierung")]:
        s0 = d[(d.method == meth) & (d.scenario == "S0")]
        p(f"  {label:26s} weich {s0.weiche_abweichungen.mean():.1f}  Spanne "
          f"{s0.auslastung_spanne.mean():.3f}  offen {s0.offene_slots.mean():.2f}")
    p("  Auf dem Plan der Optimierung (Greedy auf MILP-Plan | MILP reaktiv), alle 45:")
    for col, fmt in [("planstabilitaet", "{:.1%}"), ("geaenderte_zuweisungen", "{:.1f}"),
                     ("weiche_abweichungen", "{:.2f}"), ("harte_verstoesse", "{:.2f}"),
                     ("offene_slots", "{:.2f}"), ("auslastung_spanne", "{:.3f}")]:
        p(f"    {col:24s} {fmt.format(m(d, 'Greedy auf MILP-Plan', col).mean()):>8s} | "
          f"{fmt.format(m(d, 'MILP reaktiv', col).mean()):>8s}")
    a = d[(d.method == "Greedy auf MILP-Plan") & (d.scenario == "S2")].set_index(
        ["seed", "staffing_factor"]).planstabilitaet
    b = d[(d.method == "MILP reaktiv") & (d.scenario == "S2")].set_index(
        ["seed", "staffing_factor"]).planstabilitaet
    p(f"  S2: MILP stabiler in {int((b > a).sum())} von {len(a)} Instanzen")
    a1 = d[(d.method == "Greedy auf MILP-Plan") & d.scenario.isin(GESTOERT)].set_index(
        ["seed", "staffing_factor", "scenario"]).planstabilitaet
    b1 = d[(d.method == "MILP reaktiv") & d.scenario.isin(GESTOERT)].set_index(
        ["seed", "staffing_factor", "scenario"]).planstabilitaet
    p(f"  S1/S2: MILP stabiler in {int((b1 > a1).sum())} von {len(a1)} Plaenen")
    p("  Auf dem Plan der Optimierung, nur gestoerte Plaene (30):")
    for col, fmt in KPI:
        p(f"    {col:24s} {fmt.format(m(d, 'Greedy auf MILP-Plan', col, scenario=GESTOERT).mean()):>8s} | "
          f"{fmt.format(m(d, 'MILP reaktiv', col, scenario=GESTOERT).mean()):>8s}")
    p("  Auf dem Plan der Heuristik, nur gestoerte Plaene (30):")
    for col, fmt in KPI:
        p(f"    {col:24s} {fmt.format(m(d, 'Greedy reaktiv', col, scenario=GESTOERT).mean()):>8s} | "
          f"{fmt.format(m(d, 'MILP auf Greedy-Plan', col, scenario=GESTOERT).mean()):>8s}")
    p("  Auf dem Plan der Heuristik (Greedy reaktiv | MILP auf Greedy-Plan), alle 45:")
    for col, fmt in [("planstabilitaet", "{:.1%}"), ("geaenderte_zuweisungen", "{:.1f}"),
                     ("auslastung_spanne", "{:.3f}"), ("harte_verstoesse", "{:.2f}"),
                     ("untergrenzen_verstoesse", "{:.2f}"), ("offene_slots", "{:.2f}")]:
        p(f"    {col:24s} {fmt.format(m(d, 'Greedy reaktiv', col).mean()):>8s} | "
          f"{fmt.format(m(d, 'MILP auf Greedy-Plan', col).mean()):>8s}")

    # ------------------------------------------------------------------ 4.3
    for titel, filt in [("alle 45", {}), ("nur gestoerte Plaene, 30", {"scenario": GESTOERT})]:
        p(f"\n=== 4.3 Vier-Felder-Tafel, geaenderte Zuweisungen ({titel})")
        for zeile, (mh, mo) in {"Ausgangsplan Heuristik": ("Greedy reaktiv", "MILP auf Greedy-Plan"),
                                "Ausgangsplan Optimierung": ("Greedy auf MILP-Plan", "MILP reaktiv")}.items():
            p(f"  {zeile:26s} Heuristik {m(d, mh, 'geaenderte_zuweisungen', **filt).mean():5.1f} | "
              f"Optimierung {m(d, mo, 'geaenderte_zuweisungen', **filt).mean():5.1f}")

    # ------------------------------------------------------------------ 4.4
    p("\n=== 4.4 Spanne auf dem Plan der Heuristik, nach Deckung")
    g = d[d.method == "Greedy reaktiv"].set_index(["seed", "staffing_factor", "scenario"])
    o = d[d.method == "MILP auf Greedy-Plan"].set_index(["seed", "staffing_factor", "scenario"])
    j = g[["auslastung_spanne", "offene_slots"]].join(
        o[["auslastung_spanne"]], rsuffix="_milp").reset_index()
    for name, sub in [("Heuristik besetzt vollstaendig", j[j.offene_slots == 0]),
                      ("Heuristik laesst Luecken", j[j.offene_slots > 0])]:
        p(f"  {name:32s} ({len(sub):2d}) Regelbasiert {sub.auslastung_spanne.mean():.3f} | "
          f"MILP {sub.auslastung_spanne_milp.mean():.3f} | offen {sub.offene_slots.mean():.2f}")
    voll = j[(j.offene_slots == 0) & j.scenario.isin(GESTOERT)]
    for sc in GESTOERT:
        s = voll[voll.scenario == sc]
        besser = int((s.auslastung_spanne_milp < s.auslastung_spanne).sum())
        p(f"  gestoert, ohne Deckungsunterschied, {sc}: MILP besser in {besser} von {len(s)} "
          f"(Differenz {(s.auslastung_spanne_milp - s.auslastung_spanne).mean():+.3f})")

    # ------------------------------------------------------------------ 5
    p("\n=== 5 Weitere Kennzahlen")
    for meth in ["MILP", "MILP reaktiv", "Greedy", "Greedy reaktiv"]:
        s = d[(d.method == meth) & d.scenario.isin(GESTOERT)]
        rng_ = s.groupby("staffing_factor").planstabilitaet.mean()
        p(f"  {meth:16s} gestoert: Stabilitaet je Decke {rng_.min():.1%} - {rng_.max():.1%}, "
          f"Aenderungen {s.geaenderte_zuweisungen.mean():.1f}")
    mr = d[d.method == "MILP reaktiv"]
    mrg = mr[mr.scenario.isin(GESTOERT)]
    p(f"  MILP reaktiv, gestoert: Rechenzeit Median {mrg.planungszeit_s.median():.2f} s, "
      f"Maximum {mrg.planungszeit_s.max():.2f} s")
    for f in [1.00, 0.80]:
        p(f"  MILP Erstplanung Rechenzeit bei {f:.0%}: "
          f"{m(d, 'MILP', 'planungszeit_s', staffing_factor=f).mean():.1f} s")
    milp3 = d[d.method.isin(["MILP", "MILP reaktiv", "MILP auf Greedy-Plan"])]
    p(f"  Zeitlimit gegriffen (Status 1): {int((milp3.solver_status == 1).sum())} von {len(milp3)} MILP-Laeufen")
    s100 = d[d.staffing_factor == 1.00]
    p(f"  100 %: Streuung Greedy {m(s100, 'Greedy', 'auslastung_streuung').mean():.3f} -> MILP "
      f"{m(s100, 'MILP', 'auslastung_streuung').mean():.3f} (MILP reaktiv "
      f"{m(s100, 'MILP reaktiv', 'auslastung_streuung').mean():.3f}); Spanne Greedy "
      f"{m(s100, 'Greedy', 'auslastung_spanne').mean():.3f} -> MILP {m(s100, 'MILP', 'auslastung_spanne').mean():.3f}; "
      f"weich Greedy {m(s100, 'Greedy', 'weiche_abweichungen').mean():.1f}, MILP reaktiv "
      f"{m(s100, 'MILP reaktiv', 'weiche_abweichungen').mean():.1f}")
    if "krankheitsgutschrift_min" in d.columns:
        kg = d[d.scenario.isin(GESTOERT)]
        p(f"  Krankheitsgutschrift je gestoertem Plan: Mittel "
          f"{kg.krankheitsgutschrift_min.mean() / 60:.1f} h")


def baseline_nachtrichtwert(seeds=(20261133, 4711, 20260906, 777, 31415),
                            faktoren=(1.00, 0.90, 0.80), ward="innere") -> None:
    """
    Abschnitt 7.3: Wirkung der Korrektur an der Baseline (Nachtdienst-Richtwert
    weich statt hart). Rechnet die Heuristik in beiden Varianten neu, jeweils
    als Neuplanung mit dem eigenen S0-Plan als Basis fuer die Gutschrift.
    """
    import io
    import generate_dataset as G
    import planner as P
    rows = []
    for f in faktoren:
        for s in seeds:
            comb, _ = G.build_dataset(int(s), float(f), ward)
            buf = io.StringIO()
            pd.DataFrame(comb).to_csv(buf, index=False)
            buf.seek(0)
            ctx = P.build_context(P.load_dataset(buf))
            for soft in (False, True):
                ref = P.plan_greedy(ctx, "S0 - keine kurzfristigen Ausfaelle", soft_night=soft)
                for sc in P.SCENARIOS:
                    r = ref if sc.startswith("S0") else P.plan_greedy(
                        ctx, sc, soft_night=soft, basisplan=ref)
                    k = P.evaluate(ctx, r, basisplan=ref)
                    rows.append({"faktor": f, "weich": soft, "besetzung": k["besetzungsquote"],
                                 "offen": k["offene_slots"], "ppug": k["untergrenzen_verstoesse"],
                                 "hart": k["harte_verstoesse"], "soft": k["weiche_abweichungen"]})
    t = pd.DataFrame(rows)
    print("=== 7.3 Nachtdienst-Richtwert der Heuristik: hart | weich (15 Instanzen x 3 Szenarien)")
    for col, fmt in [("besetzung", "{:.1%}"), ("offen", "{:.2f}"), ("ppug", "{:.2f}"),
                     ("hart", "{:.2f}"), ("soft", "{:.1f}")]:
        print(f"  {col:10s} {fmt.format(t[~t.weich][col].mean()):>8s} | "
              f"{fmt.format(t[t.weich][col].mean()):>8s}")
    for f in faktoren:
        a, b = t[(t.faktor == f) & ~t.weich], t[(t.faktor == f) & t.weich]
        print(f"  Decke {f:.0%}: offen {int(a.offen.sum())} -> {int(b.offen.sum())}, "
              f"Untergrenze {int(a.ppug.sum())} -> {int(b.ppug.sum())}, "
              f"weich {a.soft.mean():.1f} -> {b.soft.mean():.1f}, konform "
              f"{((a.hart == 0) & (a.ppug == 0)).mean():.0%} -> {((b.hart == 0) & (b.ppug == 0)).mean():.0%}")


if __name__ == "__main__":
    if "--baseline" in sys.argv:
        baseline_nachtrichtwert()
    else:
        args = [a for a in sys.argv[1:] if not a.startswith("--")]
        main(args[0] if args else CSV)
