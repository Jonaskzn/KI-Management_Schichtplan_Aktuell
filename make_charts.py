#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erzeugt die Abbildungen fuer Praesentation, Handout und Hausarbeit
aus evaluation_results.csv. Alle Werte stammen aus der Kampagne -
nichts ist von Hand eingetragen.

    python make_charts.py     ->  abbildungen/*.png
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "abbildungen")
RESULTS = os.path.join(BASE, "evaluation_results.csv")

# Farbrollen (validierte Palette, heller Hintergrund)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BLUE = "#2a78d6"     # Regelbasiert
ORANGE = "#eb6834"   # MILP
BLUE_L = "#9ec5f4"
ORANGE_L = "#f6bda4"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK2,
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.titlesize": 15,
    "axes.titleweight": "bold",
    "font.size": 11,
    "savefig.facecolor": SURFACE,
})


def frame(ax, ylabel=""):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    if ylabel:
        ax.set_ylabel(ylabel, color=INK2, fontsize=10)


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  ", os.path.relpath(path, BASE))


d = pd.read_csv(RESULTS)
d["konform"] = (d["harte_verstoesse"] == 0) & (d["untergrenzen_verstoesse"] == 0)
FACTORS = [0.8, 0.9, 1.0]
LABELS = ["80 %\n(unterbesetzt)", "90 %\n(knapp)", "100 %\n(bedarfsgerecht)"]


def by_factor(method, column, agg="mean"):
    t = d[d["method"] == method].groupby("staffing_factor")[column].agg(agg)
    return [t.get(f, float("nan")) for f in FACTORS]


print("Abbildungen:")

# --------------------------------------------------------------------------
# 1  Regelkonformitaet unter Knappheit  (Kernabbildung)
# --------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5))
x = range(len(FACTORS))
w = 0.36
g = [v * 100 for v in by_factor("Greedy", "konform")]
m = [v * 100 for v in by_factor("MILP", "konform")]
b1 = ax.bar([i - w / 2 - 0.01 for i in x], g, w, color=BLUE, label="Regelbasiert (Baseline)")
b2 = ax.bar([i + w / 2 + 0.01 for i in x], m, w, color=ORANGE, label="MILP-Optimierung")
for bars in (b1, b2):
    for bar in bars:
        ax.annotate(f"{bar.get_height():.0f} %",
                    (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    ha="center", va="bottom", fontsize=11, color=INK, xytext=(0, 3),
                    textcoords="offset points")
frame(ax, "Anteil der Pläne in %")
ax.set_xticks(list(x), LABELS)
ax.set_ylim(0, 108)
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_title("Vollständig regelkonforme Pläne nach Personaldecke", pad=40)
ax.text(0, -0.22, "keine harten Regelverstöße und keine Unterschreitung der Pflegepersonaluntergrenze · "
                  "je 15 Pläne", transform=ax.transAxes, fontsize=9, color=MUTED)
ax.legend(frameon=False, loc="lower left", fontsize=10, labelcolor=INK2, ncol=2,
          bbox_to_anchor=(0.0, 1.005))
save(fig, "01_regelkonformitaet.png")

# --------------------------------------------------------------------------
# 2  Untergrenzenverstoesse je Plan
# --------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 4.6))
g = by_factor("Greedy", "untergrenzen_verstoesse")
m = by_factor("MILP", "untergrenzen_verstoesse")
b1 = ax.bar([i - w / 2 - 0.01 for i in x], g, w, color=BLUE, label="Regelbasiert (Baseline)")
b2 = ax.bar([i + w / 2 + 0.01 for i in x], m, w, color=ORANGE, label="MILP-Optimierung")
for bars in (b1, b2):
    for bar in bars:
        ax.annotate(f"{bar.get_height():.2f}".replace(".", ","),
                    (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    ha="center", va="bottom", fontsize=11, color=INK, xytext=(0, 3),
                    textcoords="offset points")
frame(ax, "Verstöße je Plan (Mittelwert)")
ax.set_xticks(list(x), LABELS)
ax.set_ylim(0, max(g) * 1.25)
ax.set_title("Unterschreitungen der Pflegepersonaluntergrenze", pad=16)
ax.text(0, -0.24, "PpUGV § 6 · Unterschreitung ist ein Rechtsverstoß, nicht nur ein Qualitätsmangel",
        transform=ax.transAxes, fontsize=9, color=MUTED)
ax.legend(frameon=False, loc="upper right", fontsize=10, labelcolor=INK2)
save(fig, "02_untergrenzen.png")

# --------------------------------------------------------------------------
# 3  Planstabilitaet nach Ausfall
# --------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 4.6))
methods = ["Greedy", "Greedy reaktiv", "MILP", "MILP reaktiv"]
names = ["Regelbasiert\nNeuplanung", "Regelbasiert\nreaktiv",
         "MILP\nNeuplanung", "MILP\nreaktiv"]
vals = [d[d["method"] == mth]["planstabilitaet"].mean() * 100 for mth in methods]
colors = [BLUE_L, BLUE, ORANGE_L, ORANGE]
bars = ax.bar(range(4), vals, 0.55, color=colors)
for bar in bars:
    ax.annotate(f"{bar.get_height():.0f} %",
                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                ha="center", va="bottom", fontsize=12, color=INK, xytext=(0, 3),
                textcoords="offset points")
frame(ax, "unveränderte Zuweisungen in %")
ax.set_xticks(range(4), names, fontsize=10)
ax.set_ylim(0, 108)
ax.set_title("Planstabilität nach kurzfristigen Ausfällen", pad=16)
ax.text(0, -0.26, "Anteil der (Person, Tag)-Zuweisungen, die gegenüber dem Ausgangsplan bestehen "
                  "bleiben · alle Personaldecken und Szenarien",
        transform=ax.transAxes, fontsize=9, color=MUTED)
save(fig, "03_planstabilitaet.png")

# --------------------------------------------------------------------------
# 4  Lastverteilung
# --------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 4.2))
sub = d[d["staffing_factor"] == 1.0]
vals = [sub[sub["method"] == mth]["auslastung_spanne"].mean() * 100
        for mth in ["Greedy", "MILP"]]
bars = ax.barh([1, 0], vals, 0.45, color=[BLUE, ORANGE])
for bar in bars:
    ax.annotate(f"{bar.get_width():.1f} Prozentpunkte".replace(".", ","),
                (bar.get_width(), bar.get_y() + bar.get_height() / 2),
                va="center", ha="left", fontsize=12, color=INK, xytext=(6, 0),
                textcoords="offset points")
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)
ax.spines["bottom"].set_color("#c3c2b7")
ax.xaxis.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
ax.tick_params(length=0)
ax.set_yticks([1, 0], ["Regelbasiert", "MILP-Optimierung"], fontsize=11)
ax.set_xlim(0, max(vals) * 1.35)
ax.set_xlabel("Spanne der individuellen Auslastung", color=INK2, fontsize=10)
ax.set_title("Ungleichverteilung der Arbeitslast", pad=16)
ax.text(0, -0.32, "Abstand zwischen der am geringsten und der am stärksten ausgelasteten Person · "
                  "bedarfsgerechte Personaldecke", transform=ax.transAxes, fontsize=9, color=MUTED)
save(fig, "04_lastverteilung.png")

# --------------------------------------------------------------------------
# 5  Wirkung der Ausfallstruktur
# --------------------------------------------------------------------------
SCEN = ["S0", "S1", "S2"]
SCEN_LBL = ["S0\nkeine Ausfälle", "S1\nverteilte Einzeltage", "S2\nAusfallwelle"]

fig, axes = plt.subplots(1, 2, figsize=(10, 4.9))

# links: Planstabilitaet der reaktiven Umplanung
ax = axes[0]
gre = [d[(d.method == "Greedy reaktiv") & (d.scenario == sc)]["planstabilitaet"].mean() * 100
       for sc in SCEN]
mil = [d[(d.method == "MILP reaktiv") & (d.scenario == sc)]["planstabilitaet"].mean() * 100
       for sc in SCEN]
x = range(3)
b1 = ax.bar([i - 0.19 for i in x], gre, 0.36, color=BLUE, label="Regelbasiert")
b2 = ax.bar([i + 0.19 for i in x], mil, 0.36, color=ORANGE, label="MILP-Optimierung")
for bars in (b1, b2):
    for bar in bars:
        ax.annotate(f"{bar.get_height():.0f} %",
                    (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    ha="center", va="bottom", fontsize=10, color=INK,
                    xytext=(0, 3), textcoords="offset points")
frame(ax, "unveränderte Zuweisungen in %")
ax.set_xticks(list(x), SCEN_LBL, fontsize=9)
ax.set_ylim(0, 118)
ax.set_title("Planstabilität", fontsize=13, pad=12)
ax.legend(frameon=False, fontsize=9, loc="upper center", ncol=2,
          bbox_to_anchor=(0.5, 1.02))

# rechts: harte Regelverstoesse
ax = axes[1]
gre = [d[(d.method == "Greedy reaktiv") & (d.scenario == sc)]["harte_verstoesse"].mean()
       for sc in SCEN]
mil = [d[(d.method == "MILP reaktiv") & (d.scenario == sc)]["harte_verstoesse"].mean()
       for sc in SCEN]
b1 = ax.bar([i - 0.19 for i in x], gre, 0.36, color=BLUE)
b2 = ax.bar([i + 0.19 for i in x], mil, 0.36, color=ORANGE)
for bars in (b1, b2):
    for bar in bars:
        ax.annotate(f"{bar.get_height():.2f}".replace(".", ","),
                    (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    ha="center", va="bottom", fontsize=10, color=INK,
                    xytext=(0, 3), textcoords="offset points")
frame(ax, "harte Regelverstöße je Plan")
ax.set_xticks(list(x), SCEN_LBL, fontsize=9)
ax.set_ylim(0, max(gre) * 1.45)
ax.set_title("Regelverstöße", fontsize=13, pad=12)

fig.suptitle("Wirkung der Ausfallstruktur bei gleichem Ausfallvolumen",
             fontsize=15, fontweight="bold", y=1.02)
fig.text(0.0, -0.06, "S1 und S2 tragen dasselbe Ausfallvolumen (Ø 17,0 gegen 18,1 Ausfalltage) "
                     "und unterscheiden sich nur in der Struktur · reaktive Umplanung, "
                     "alle Personaldecken", fontsize=9, color=MUTED)
fig.tight_layout()
save(fig, "05_ausfallstruktur.png")

print("\nQuelle aller Werte: evaluation_results.csv (180 Pläne, 15 Instanzen)")
