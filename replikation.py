#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replikation ueber Stationstypen: haelt der Befund auch auf anderen Daten?
========================================================================
Die Hauptkampagne (campaign.py) variiert Seed und Personaldecke - aber immer
auf derselben Station: 30 Betten, Innere Medizin/Kardiologie, Verhaeltniszahl
10:1 tags. Damit ist gezeigt, dass der Befund nicht an einer einzelnen
Zufallsziehung haengt. Nicht gezeigt ist, dass er nicht an *dieser Station*
haengt.

Dieses Skript wertet die Replikationskampagnen aus, die auf denselben Code,
aber auf Instanzen anderer Stationstypen laufen:

    Geriatrie        40 Betten, 10:1 / 20:1, bis 15 % Hilfskraefte tags
    Herzchirurgie    24 Betten,  7:1 / 15:1, bis  5 % Hilfskraefte tags
    Intensivmedizin  12 Betten,  2:1 /  3:1, reine Fachkraftbesetzung

Entscheidend fuer die Aussagekraft: Geaendert wurden ausschliesslich Werte im
Datensatz (Bettenzahl, Verhaeltniszahlen, Qualifikationsmix, Personalstruktur).
Das Schema des Datensatzes ist identisch, und planner.py wurde nicht angefasst.
Das ist zugleich die Probe auf das Konstruktionsprinzip des Prototyps:
Grenzwerte stehen in den Daten, nicht im Code.

Geprueft werden die tragenden Befunde der Hauptkampagne, jeweils als
gerichtete Aussage (Hypothese), die pro Stationstyp bestaetigt oder
widerlegt wird.

    python replikation.py            ->  Vergleichstabellen
    python replikation.py --md       ->  Markdown fuer die Ausarbeitung
"""

from __future__ import annotations

import glob
import os
import sys

import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
HAUPT = os.path.join(BASE, "evaluation_results.csv")
REPL = os.path.join(BASE, "instanzen")

LABEL = {
    "innere": "Innere Medizin (Haupt)",
    "geriatrie": "Geriatrie",
    "herzchirurgie": "Herzchirurgie",
    "intensiv": "Intensivmedizin",
}
ORDER = ["innere", "geriatrie", "herzchirurgie", "intensiv"]


def laden() -> pd.DataFrame:
    teile = []
    if os.path.exists(HAUPT):
        teile.append(pd.read_csv(HAUPT))
    for p in sorted(glob.glob(os.path.join(REPL, "evaluation_*.csv"))):
        if os.path.getsize(p) > 0:
            teile.append(pd.read_csv(p))
    if not teile:
        raise SystemExit("Keine Ergebnisdateien gefunden - erst campaign.py laufen lassen.")
    d = pd.concat(teile, ignore_index=True)
    if "ward" not in d.columns:
        d["ward"] = "innere"
    d["ward"] = d["ward"].fillna("innere")
    return d


# --------------------------------------------------------------------------
# Hypothesen: jede liefert (Wert Heuristik, Wert Optimierung, erfuellt?)
# --------------------------------------------------------------------------

def h1_untergrenze(b: pd.DataFrame):
    """Unter Knappheit (80 %) verletzt nur die Heuristik die Untergrenze."""
    s = b[b.staffing_factor == 0.80]
    g = s[s.method == "Greedy"]["untergrenzen_verstoesse"].mean()
    m = s[s.method == "MILP"]["untergrenzen_verstoesse"].mean()
    return g, m, m < g


def h2_offene(b: pd.DataFrame):
    """Unter Knappheit (80 %) laesst nur die Heuristik Dienste unbesetzt."""
    s = b[b.staffing_factor == 0.80]
    g = s[s.method == "Greedy"]["offene_slots"].sum()
    m = s[s.method == "MILP"]["offene_slots"].sum()
    return g, m, m < g


def h3_konform(b: pd.DataFrame):
    """Unter Knappheit (80 %) ist der Anteil regelkonformer Plaene hoeher."""
    s = b[b.staffing_factor == 0.80].copy()
    s["konform"] = (s.harte_verstoesse == 0) & (s.untergrenzen_verstoesse == 0)
    g = s[s.method == "Greedy"]["konform"].mean()
    m = s[s.method == "MILP"]["konform"].mean()
    return g, m, m > g


def h4_spanne(b: pd.DataFrame):
    """Bei bedarfsgerechter Decke verteilt die Optimierung die Last gleichmaessiger."""
    s = b[b.staffing_factor == 1.00]
    g = s[s.method == "Greedy"]["auslastung_spanne"].mean()
    m = s[s.method == "MILP"]["auslastung_spanne"].mean()
    return g, m, m < g


def h5_weich(b: pd.DataFrame):
    """Die Optimierung haelt die weichen Richtwerte besser ein (alle Decken)."""
    g = b[b.method == "Greedy"]["weiche_abweichungen"].mean()
    m = b[b.method == "MILP"]["weiche_abweichungen"].mean()
    return g, m, m < g


def h6_stabil_e2e(b: pd.DataFrame):
    """End-to-End: die Optimierung haelt den Plan bei Ausfaellen stabiler."""
    s = b[b.scenario.isin(["S1", "S2"])]
    g = s[s.method == "Greedy reaktiv"]["planstabilitaet"].mean()
    m = s[s.method == "MILP reaktiv"]["planstabilitaet"].mean()
    return g, m, m > g


def h7_stabil_kontrolle(b: pd.DataFrame):
    """Methodenkontrolle: auf demselben Ausgangsplan der Optimierung."""
    s = b[b.scenario.isin(["S1", "S2"])]
    g = s[s.method == "Greedy auf MILP-Plan"]["planstabilitaet"].mean()
    m = s[s.method == "MILP reaktiv"]["planstabilitaet"].mean()
    return g, m, m > g


HYPOTHESEN = [
    ("H1", "Untergrenzenverstoesse bei 80 % Decke", h1_untergrenze, "{:.2f}"),
    ("H2", "unbesetzte Dienste bei 80 % Decke (Summe)", h2_offene, "{:.0f}"),
    ("H3", "Anteil regelkonformer Plaene bei 80 %", h3_konform, "{:.0%}"),
    ("H4", "Spanne der Auslastung bei 100 % Decke", h4_spanne, "{:.3f}"),
    ("H5", "weiche Abweichungen je Plan", h5_weich, "{:.1f}"),
    ("H6", "Planstabilitaet End-to-End (S1/S2)", h6_stabil_e2e, "{:.1%}"),
    ("H7", "Planstabilitaet auf gemeinsamem Plan", h7_stabil_kontrolle, "{:.1%}"),
]


def report(md: bool = False) -> str:
    d = laden()
    wards = [w for w in ORDER if w in set(d.ward)]
    out = []

    out.append("Replikation ueber Stationstypen\n")
    out.append("Identischer Code, identisches Datenschema - andere Station.\n")

    # --- Kopfzeile: worin sich die Instanzen unterscheiden -----------------
    kopf = f"{'Stationstyp':<26s}{'Instanzen':>11s}{'Koepfe':>9s}{'Solldienste':>13s}"
    out.append(kopf)
    out.append("-" * len(kopf))
    for w in wards:
        b = d[d.ward == w]
        n = len(b.groupby(["seed", "staffing_factor"]))
        out.append(f"{LABEL[w]:<26s}{n:>11d}{b.headcount.mean():>9.0f}"
                   f"{b.soll_dienste.mean():>13.0f}")

    # --- Hypothesentabelle -------------------------------------------------
    out.append("\n\nBefunde je Stationstyp (Heuristik -> Optimierung)\n")
    breite = 26 + 22 * len(wards)
    out.append(f"{'Befund':<26s}" + "".join(f"{LABEL[w]:>22s}" for w in wards))
    out.append("-" * breite)
    bestaetigt = {w: 0 for w in wards}
    for key, name, fn, fmt in HYPOTHESEN:
        zeile = f"{key} {name:<23s}"
        for w in wards:
            g, m, ok = fn(d[d.ward == w])
            bestaetigt[w] += int(ok)
            zelle = f"{fmt.format(g)} -> {fmt.format(m)} {'ok' if ok else 'NEIN'}"
            zeile += f"{zelle:>22s}"
        out.append(zeile)
    out.append("-" * breite)
    out.append(f"{'bestaetigt':<26s}"
               + "".join(f"{f'{bestaetigt[w]} von {len(HYPOTHESEN)}':>22s}"
                         for w in wards))

    # --- Planungszeit ------------------------------------------------------
    out.append("\n\nPlanungszeit je Plan in Sekunden (Mittel)\n")
    piv = d[d.method.isin(["Greedy", "MILP", "MILP reaktiv"])].pivot_table(
        index="ward", columns="method", values="planungszeit_s", aggfunc="mean")
    piv = piv.reindex([w for w in ORDER if w in piv.index])
    piv.index = [LABEL[w] for w in piv.index]
    out.append(piv.round(2).to_string())

    if md:
        out.append("\n\n<!-- Markdown-Tabelle fuer die Ausarbeitung -->\n")
        kopf = "| Befund | " + " | ".join(LABEL[w] for w in wards) + " |"
        out.append(kopf)
        out.append("|" + "---|" * (len(wards) + 1))
        for key, name, fn, fmt in HYPOTHESEN:
            zellen = []
            for w in wards:
                g, m, ok = fn(d[d.ward == w])
                mark = "**ok**" if ok else "**nein**"
                zellen.append(f"{fmt.format(g)} → {fmt.format(m)} {mark}")
            out.append(f"| {key} {name} | " + " | ".join(zellen) + " |")
    return "\n".join(out)


if __name__ == "__main__":
    print(report(md="--md" in sys.argv))
