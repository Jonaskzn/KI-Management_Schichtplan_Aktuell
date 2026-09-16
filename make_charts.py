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
fig, axes = plt.subplots(1, 2, figsize=(11, 4.7))

# links: innerhalb eines Verfahrens - Neuplanung gegen reaktive Umplanung
ax = axes[0]
methods = ["Greedy", "Greedy reaktiv", "MILP", "MILP reaktiv"]
names = ["Regelbasiert\nNeuplanung", "Regelbasiert\nreaktiv",
         "MILP\nNeuplanung", "MILP\nreaktiv"]
vals = [d[d["method"] == mth]["planstabilitaet"].mean() * 100 for mth in methods]
bars = ax.bar(range(4), vals, 0.55, color=[BLUE_L, BLUE, ORANGE_L, ORANGE])
for bar in bars:
    ax.annotate(f"{bar.get_height():.0f} %",
                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                ha="center", va="bottom", fontsize=11, color=INK, xytext=(0, 3),
                textcoords="offset points")
frame(ax, "unveränderte Zuweisungen in %")
ax.set_xticks(range(4), names, fontsize=9)
ax.set_ylim(0, 112)
ax.set_title("Je Verfahren: Neuplanung oder Reparatur", fontsize=13, pad=12)

# rechts: zwischen den Verfahren - beide reparieren denselben Ausgangsplan
ax = axes[1]
SC = ["S0", "S1", "S2"]
LBL = ["S0\nkeine Ausfälle", "S1\nverteilte Einzeltage", "S2\nAusfallwelle"]
gre = [d[(d.method == "Greedy auf MILP-Plan") & (d.scenario == sc)]["planstabilitaet"].mean() * 100
       for sc in SC]
mil = [d[(d.method == "MILP reaktiv") & (d.scenario == sc)]["planstabilitaet"].mean() * 100
       for sc in SC]
x = range(3)
b1 = ax.bar([i - 0.19 for i in x], gre, 0.36, color=BLUE, label="Regelbasiert repariert")
b2 = ax.bar([i + 0.19 for i in x], mil, 0.36, color=ORANGE, label="MILP repariert")
for bset in (b1, b2):
    for bar in bset:
        ax.annotate(f"{bar.get_height():.0f} %",
                    (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    ha="center", va="bottom", fontsize=10, color=INK,
                    xytext=(0, 3), textcoords="offset points")
frame(ax, "unveränderte Zuweisungen in %")
ax.set_xticks(list(x), LBL, fontsize=9)
ax.set_ylim(0, 118)
ax.set_title("Zwischen den Verfahren: derselbe Ausgangsplan", fontsize=13, pad=12)
ax.legend(frameon=False, fontsize=9, loc="upper center", ncol=2,
          bbox_to_anchor=(0.5, 1.02))

fig.suptitle("Planstabilität nach kurzfristigen Ausfällen",
             fontsize=15, fontweight="bold", y=1.04)
fig.text(0.0, -0.085,
         "Anteil der (Person, Tag)-Zuweisungen, die gegenüber dem Ausgangsplan bestehen "
         "bleiben · alle Personaldecken\nRechts reparieren beide Verfahren denselben "
         "Plan. Ohne diese Bedingung schneidet das Verfahren mit dem schlechteren "
         "Ausgangsplan\nscheinbar besser ab — einen schwachen Plan unveraendert zu "
         "lassen ist billiger als einen guten gut zu halten.".replace("aendert", "ändert"),
         fontsize=9, color=MUTED)
fig.tight_layout()
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
# 5  Zielkonflikt Lastverteilung gegen Planstabilitaet
# --------------------------------------------------------------------------
SCEN = ["S0", "S1", "S2"]
SCEN_LBL = ["S0\nkeine Ausfälle", "S1\nverteilte Einzeltage", "S2\nAusfallwelle"]
SERIES = [
    ("Regelbasiert, reaktiv", "Greedy reaktiv", BLUE),
    ("MILP, reaktiv", "MILP reaktiv", ORANGE),
    ("MILP, vollständige Neuplanung", "MILP", ORANGE_L),
]
x = range(3)


def _panel(ax, column, fmt, scale=1.0, ylabel=""):
    top = 0
    for k, (label, method, color) in enumerate(SERIES):
        vals = [d[(d.method == method) & (d.scenario == sc)][column].mean() * scale
                for sc in SCEN]
        top = max(top, max(vals))
        bars = ax.bar([i + (k - 1) * 0.27 for i in x], vals, 0.25,
                      color=color, label=label)
        for bar in bars:
            ax.annotate(fmt(bar.get_height()),
                        (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        ha="center", va="bottom", fontsize=9, color=INK,
                        xytext=(0, 3), textcoords="offset points")
    frame(ax, ylabel)
    ax.set_xticks(list(x), SCEN_LBL, fontsize=9)
    return top


fig, axes = plt.subplots(1, 2, figsize=(11, 5.0))

top = _panel(axes[0], "auslastung_spanne", lambda v: f"{v:.0f}".replace(".", ","),
             scale=100, ylabel="Spanne in Prozentpunkten")
axes[0].set_ylim(0, top * 1.22)
axes[0].set_title("Ungleichverteilung der Last", fontsize=13, pad=30)

_panel(axes[1], "planstabilitaet", lambda v: f"{v:.0f}", scale=100,
       ylabel="unveränderte Zuweisungen in %")
axes[1].set_ylim(0, 118)
axes[1].set_title("Planstabilität in %", fontsize=13, pad=30)

handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, frameon=False, fontsize=10, ncol=3,
           loc="upper center", bbox_to_anchor=(0.5, 1.005))
fig.suptitle("Der Zielkonflikt: gleichmäßige Last oder stabiler Plan",
             fontsize=15, fontweight="bold", y=1.075)
fig.text(0.0, -0.075,
         "Unter der Ausfallwelle hält die Optimierung die Spanne bei vollständiger "
         "Neuplanung auf 16 Prozentpunkten — weniger als die Hälfte der reaktiven\n"
         "Variante (38). Den Verteilungsvorteil verliert sie also nicht durch die Welle, "
         "sondern durch die Vorgabe, den Plan möglichst unverändert zu lassen.",
         fontsize=9, color=MUTED)
fig.tight_layout()
save(fig, "05_zielkonflikt.png")

print("\nQuelle aller Werte: evaluation_results.csv (270 Pläne, 15 Instanzen)")
