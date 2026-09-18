#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gantt-Diagramm des Projektverlaufs fuer den Anhang der Hausarbeit.

ANPASSEN: Die Termine unten sind die Meilensteine aus den Kursunterlagen (T1)
mit der Jahreszahl 2026. Traegt eure tatsaechlichen Arbeitszeitraeume ein -
das Diagramm soll den realen Projektverlauf zeigen, nicht einen idealisierten.

    python make_gantt.py   ->  abbildungen/00_gantt.png
"""

from __future__ import annotations

import os
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "abbildungen")

# --- HIER ANPASSEN --------------------------------------------------------
# (Bezeichnung, Start, Ende, Kategorie)
#   Kategorie: "planung" | "daten" | "prototyp" | "auswertung" | "arbeit"
PHASEN = [
    ("Themenfindung und Zielsetzung",      date(2026, 9, 28),  date(2026, 10, 19), "planung"),
    ("Projektplan",                        date(2026, 10, 15), date(2026, 10, 30), "planung"),
    ("Literatur- und Methodenrecherche",   date(2026, 10, 20), date(2026, 11, 15), "planung"),
    ("Datenkonzeption und Rechtsrahmen",   date(2026, 10, 26), date(2026, 11, 9),  "daten"),
    ("Datensatz erzeugen und validieren",  date(2026, 11, 2),  date(2026, 11, 16), "daten"),
    ("Prototyp: regelbasierte Planung",    date(2026, 11, 9),  date(2026, 11, 23), "prototyp"),
    ("Prototyp: MILP-Optimierung",         date(2026, 11, 18), date(2026, 11, 30), "prototyp"),
    ("Evaluationskampagne",                date(2026, 11, 28), date(2026, 12, 5),  "auswertung"),
    ("Auswertung und Business Impact",     date(2026, 12, 1),  date(2026, 12, 8),  "auswertung"),
    ("Ausarbeitung Hausarbeit",            date(2026, 11, 25), date(2026, 12, 13), "arbeit"),
    ("Präsentation und Handout",           date(2026, 11, 27), date(2026, 12, 11), "arbeit"),
]

MEILENSTEINE = [
    ("Themenabgabe",      date(2026, 10, 19)),
    ("Projektplan",       date(2026, 10, 30)),
    ("Präsentationen",    date(2026, 12, 4)),
    ("Abgabe Hausarbeit", date(2026, 12, 14)),
]
# --- ENDE ANPASSEN --------------------------------------------------------

SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
FARBEN = {
    "planung":    "#9ec5f4",
    "daten":      "#2a78d6",
    "prototyp":   "#eb6834",
    "auswertung": "#1baf7a",
    "arbeit":     "#4a3aa7",
}
LEGENDE = {
    "planung": "Projektaufsatz", "daten": "Daten",
    "prototyp": "Prototyp", "auswertung": "Evaluation", "arbeit": "Ausarbeitung",
}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE, "text.color": INK, "font.size": 10,
    "savefig.facecolor": SURFACE,
})

fig, ax = plt.subplots(figsize=(11, 5.4))
for i, (name, start, ende, kat) in enumerate(reversed(PHASEN)):
    ax.barh(i, (ende - start).days, left=start, height=0.55,
            color=FARBEN[kat], zorder=3)

ax.set_yticks(range(len(PHASEN)), [p[0] for p in reversed(PHASEN)], fontsize=10)
ax.tick_params(length=0)
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)
ax.spines["bottom"].set_color("#c3c2b7")
ax.xaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
ax.set_axisbelow(True)

ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m."))
plt.setp(ax.get_xticklabels(), color=MUTED)

ymax = len(PHASEN) - 0.3
for name, tag in MEILENSTEINE:
    ax.axvline(tag, color="#d03b3b", linewidth=1.4, linestyle=(0, (4, 3)), zorder=4)
    ax.annotate(f"{name}\n{tag:%d.%m.}", (tag, ymax), xytext=(4, 0),
                textcoords="offset points", fontsize=8.5, color="#d03b3b",
                va="top", ha="left", zorder=5)

handles = [plt.Rectangle((0, 0), 1, 1, color=FARBEN[k]) for k in LEGENDE]
ax.legend(handles, list(LEGENDE.values()), frameon=False, ncol=5, fontsize=9.5,
          loc="upper center", bbox_to_anchor=(0.5, -0.12), labelcolor=INK2)

ax.set_title("Projektverlauf", fontsize=15, fontweight="bold", pad=14, loc="left")
ax.set_ylim(-0.7, len(PHASEN) + 0.6)

os.makedirs(OUT, exist_ok=True)
path = os.path.join(OUT, "00_gantt.png")
fig.savefig(path, dpi=200, bbox_inches="tight")
print("  ", os.path.relpath(path, BASE))
print("   Termine in make_gantt.py anpassen, dann erneut ausführen.")
