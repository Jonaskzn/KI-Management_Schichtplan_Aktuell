#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pruefskript fuer schichtplan_datensatz.csv (kombinierte Einzeltabelle).

Der Datensatz ist die Eingabe fuer beide Planungsansaetze (Excel-Baseline und
optimierungsbasierte Planung). Ist er in sich unschluessig, ist jeder spaetere
KPI-Vergleich wertlos. Geprueft werden:

  A Struktur und Redundanzkonsistenz der denormalisierten Tabelle
  B Rechtliche Konsistenz der Schichtdefinitionen (ArbZG)
  C Erfuellbarkeit: Kapazitaetsbilanz Soll-Stunden vs. verfuegbare Stunden
  D PpUGV-Konformitaet von Sollbesetzung und Qualifikationsmix
  E Plausibilitaet gegenueber den Referenzkennzahlen der Statistik
  F Datenschutz: keine Klarnamen, keine Gesundheitsdaten

Block A ist neu und in einer Einzeltabelle unverzichtbar: weil Stamm-, Tages-
und Regeldaten wiederholt werden, muss maschinell belegt sein, dass jede
Wiederholung identisch ist. Sonst waere die Denormalisierung eine
Fehlerquelle statt einer Bequemlichkeit.

Exit-Code 0 = alle harten Pruefungen bestanden.
"""

from __future__ import annotations

import math
import os
import sys
from datetime import date, datetime, time, timedelta

import pandas as pd

CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "schichtplan_datensatz.csv")

FAIL, WARN = [], []


def check(cond, msg, hard=True):
    if cond:
        print(f"  [ok]   {msg}")
    else:
        (FAIL if hard else WARN).append(msg)
        print(f"  [{'FAIL' if hard else 'warn'}] {msg}")


df = pd.read_csv(CSV, dtype={"holiday_name": str, "availability_type": str,
                             "request_on_shift": str, "history_shift": str})
df["holiday_name"] = df["holiday_name"].fillna("")
df["availability_type"] = df["availability_type"].fillna("")
df["history_shift"] = df["history_shift"].fillna("")
df["date_d"] = pd.to_datetime(df["date"]).dt.date

SHIFT_IDS = ["F", "S", "N"]
STAFF_COLS = ["role", "role_group", "skills", "employment_pct", "weekly_hours",
              "contract_minutes_horizon", "planable_minutes_horizon",
              "min_total_minutes", "max_total_minutes", "max_consecutive_shifts",
              "min_consecutive_days_off", "max_weekends", "max_night_shifts",
              "night_eligible", "ppug_countable", "ppug_category",
              "is_ward_lead", "lead_release_pct", "time_account_start_min"]
DAY_COLS = (["period", "day_index", "weekday", "weekday_num", "iso_week",
             "is_weekend", "is_holiday", "holiday_name", "census_1200",
             "census_0000", "admissions", "discharges", "isolation_patients",
             "care_minutes_total"]
            + [f"{p}_{s}" for s in SHIFT_IDS for p in
               ["required", "ppug_min", "min_fachkraft", "max_hilfskraft",
                "care_minutes", "azubi_slots"]])
GLOBAL_COLS = ([c for c in df.columns if c.startswith(("rule_", "shift_", "ppug_ratio"))]
               + ["ward_id", "ward_name", "beds", "ppug_bereich",
                  "dataset_version", "seed"])

staff = df.drop_duplicates("employee_id").set_index("employee_id")
days = df.drop_duplicates("date").set_index("date").sort_index()
plan = days[days["period"] == "plan"]
hist = days[days["period"] == "history"]
g = df.iloc[0]

print("\nA) Struktur und Redundanzkonsistenz")
n_emp, n_days = df["employee_id"].nunique(), df["date"].nunique()
check(len(df) == n_emp * n_days,
      f"vollstaendiges Kreuzprodukt {n_emp} Mitarbeitende x {n_days} Tage = {len(df)} Zeilen")
check(not df.duplicated(["employee_id", "date"]).any(),
      "Schluessel (employee_id, date) ist eindeutig")
d0, d1 = df["date_d"].min(), df["date_d"].max()
check((d1 - d0).days + 1 == n_days, "Kalender ist lueckenlos")
check(len(plan) == 28 and len(hist) == 28, "28 Planungstage und 28 Historientage")

bad_staff = [c for c in STAFF_COLS if df.groupby("employee_id")[c].nunique(dropna=False).max() > 1]
check(not bad_staff, f"Mitarbeiterstammdaten je employee_id konstant {bad_staff}")
bad_day = [c for c in DAY_COLS if df.groupby("date")[c].nunique(dropna=False).max() > 1]
check(not bad_day, f"Tages- und Bedarfsdaten je date konstant {bad_day}")
bad_glob = [c for c in GLOBAL_COLS if df[c].nunique(dropna=False) > 1]
check(not bad_glob, f"Stations- und Regelspalten global konstant {bad_glob}")
check(set(df["period"].unique()) == {"plan", "history"}, "period nur plan/history")
check(df.loc[df["period"] == "history", ["absence_s1", "absence_s2"]].to_numpy().sum() == 0,
      "Ausfallszenarien nur im Planhorizont belegt")
check((df.loc[df["history_shift"] != "", "period"] == "history").all(),
      "history_shift nur in der Vorperiode belegt")
check(df.loc[df["history_shift"] != "", "history_shift"].isin(SHIFT_IDS).all(),
      "history_shift enthaelt nur gueltige Schicht-IDs")
check(((df["available"] == 0) == (df["availability_type"] != "")).all(),
      "available und availability_type widerspruchsfrei")

print("\nB) Rechtliche Konsistenz der Schichtdefinitionen (ArbZG)")
SH = {s: {"start": g[f"shift_{s}_start"], "end": g[f"shift_{s}_end"],
          "net": int(g[f"shift_{s}_net_min"]),
          "forb": [] if pd.isna(g[f"shift_{s}_forbidden_next"])
                  else str(g[f"shift_{s}_forbidden_next"]).split("|")}
      for s in SHIFT_IDS}


def sdt(d: date, s: str, end=False):
    st = datetime.combine(d, time.fromisoformat(SH[s]["start"]))
    en = datetime.combine(d, time.fromisoformat(SH[s]["end"]))
    if en <= st:
        en += timedelta(days=1)
    return en if end else st


def gross(s):
    return (sdt(date(2026, 1, 5), s, end=True) - sdt(date(2026, 1, 5), s)).total_seconds() / 60


check(all(gross(s) - SH[s]["net"] >= (45 if gross(s) > 540 else 30) for s in SHIFT_IDS),
      "Pausen nach ArbZG § 4 (>=30 min ab 6 h, >=45 min ab 9 h)")
check(all(SH[s]["net"] <= 600 for s in SHIFT_IDS),
      "Nettoarbeitszeit je Dienst <= 10 h (ArbZG § 3)")
check(SH["N"]["net"] <= 600, "Nachtdienst <= 10 h, Monatsausgleich (ArbZG § 6 Abs. 2)")

d0_ = date(2026, 1, 5)
viol = []
for a in SHIFT_IDS:
    for b in SHIFT_IDS:
        rest = (sdt(d0_ + timedelta(days=1), b) - sdt(d0_, a, end=True)).total_seconds() / 3600
        if (rest < int(g["rule_min_rest_h"])) != (b in SH[a]["forb"]):
            viol.append((a, b, round(rest, 2)))
check(not viol, f"verbotene Schichtfolgen decken alle Ruhezeitverstoesse ab {viol}")

print("\nC) Erfuellbarkeit: Kapazitaetsbilanz im Planhorizont")
soll_min = int(sum(plan[f"required_{s}"].sum() * SH[s]["net"] for s in SHIFT_IDS))
azubi = staff.index[staff["role_group"] == "Auszubildende"]
countable = staff.index[staff["ppug_countable"] == 1]
cap = int(staff.loc[countable, "planable_minutes_horizon"].sum())
pl = df[(df["period"] == "plan") & (df["available"] == 0)
        & (df["employee_id"].isin(countable))]
lost = int((pl["weekly_hours"] * 60 / 5).sum())
net_cap = cap - lost
print(f"        Soll-Minuten (Pflegekraefte):      {soll_min:>9,d}")
print(f"        Vertragskapazitaet anrechenbar:    {cap:>9,d}")
print(f"        ./. geplante Abwesenheiten:        {lost:>9,d}")
print(f"        = verfuegbar:                      {net_cap:>9,d}")
print(f"        Auslastungsgrad:                   {soll_min / net_cap:>9.1%}")
check(net_cap >= soll_min, "Sollbesetzung ist mit dem vorhandenen Personal deckbar")
check(0.85 <= soll_min / net_cap <= 1.00,
      "Auslastung im realistisch knappen Korridor 85-100 %", hard=False)

print("\nD) PpUGV-Konformitaet")
ratio = {"F": float(g["ppug_ratio_day"]), "S": float(g["ppug_ratio_day"]),
         "N": float(g["ppug_ratio_night"])}
ref = {"F": "census_1200", "S": "census_1200", "N": "census_0000"}
ok_ratio, ok_floor, ok_sum = True, True, True
for s in SHIFT_IDS:
    exp = days[ref[s]].apply(lambda c: math.ceil(c / ratio[s]))
    ok_ratio &= bool((days[f"ppug_min_{s}"] == exp).all())
    ok_floor &= bool((days[f"required_{s}"] >= days[f"ppug_min_{s}"]).all())
    ok_sum &= bool((days[f"min_fachkraft_{s}"] + days[f"max_hilfskraft_{s}"]
                    == days[f"required_{s}"]).all())
check(ok_ratio, "Untergrenze = aufgerundeter Quotient Bestand / Verhaeltniszahl")
check(ok_floor, "Sollbesetzung erreicht in jeder Schicht die Untergrenze")
check(ok_sum, "Qualifikationsanforderungen summieren sich zur Sollbesetzung")
check((days["max_hilfskraft_N"] == 0).all(),
      "keine Pflegehilfskraft im Nachtdienst (1 von 2 = 50 % > 10 %)")
helper_fte = staff.loc[staff["ppug_category"] == "Pflegehilfskraft", "employment_pct"].sum()
count_fte = staff.loc[countable, "employment_pct"].sum()
share = helper_fte / count_fte
print(f"        Hilfskraft-Kapazitaetsanteil:      {share:>9.1%} "
      f"(Grenze {float(g['rule_max_helper_share']):.0%})")
check(share <= float(g["rule_max_helper_share"]),
      "Pflegehilfskraft-Anteil der Kapazitaet haelt die Grenze ein")
check((staff.loc[azubi, "ppug_countable"] == 0).all(),
      "Auszubildende sind nicht auf die Untergrenze anrechenbar (PpUGV § 2)")

print("\nE) Plausibilitaet gegenueber Referenzkennzahlen")
ausl = days["census_1200"].mean() / int(g["beds"])
print(f"        mittlere Bettenauslastung:         {ausl:>9.1%} (DESTATIS 72,0 %)")
check(0.68 <= ausl <= 0.76, "Bettenauslastung im Zielkorridor", hard=False)
exam = staff[staff["role_group"] != "Auszubildende"]
fach = exam[exam["ppug_category"] == "Pflegefachkraft"]
tz = exam[exam["employment_pct"] < 1.0]
print(f"        Fachkraftanteil (ohne Azubis):     {len(fach) / len(exam):>9.1%} (SN 82,4 %)")
print(f"        Teilzeitquote (ohne Azubis):       {len(tz) / len(exam):>9.1%} (SN 57,4 %)")
print(f"        VK je Kopf:                        "
      f"{staff['employment_pct'].mean():>9.3f} (SN 0,805)")
check(len(fach) / len(exam) >= 0.824, "Fachkraftanteil mindestens auf Bundesniveau", hard=False)
check(0.45 <= len(tz) / len(exam) <= 0.70, "Teilzeitquote im Zielkorridor", hard=False)

h = df[(df["period"] == "history") & (df["history_shift"] != "")]
rest_viol = consec_viol = 0
for eid, grp in h.groupby("employee_id"):
    lst = sorted(zip(grp["date_d"], grp["history_shift"]))
    run = 1
    for (da, sa), (db, sb) in zip(lst, lst[1:]):
        if (sdt(db, sb) - sdt(da, sa, end=True)).total_seconds() / 3600 < int(g["rule_min_rest_h"]):
            rest_viol += 1
        run = run + 1 if (db - da).days == 1 else 1
        if run > int(staff.loc[eid, "max_consecutive_shifts"]):
            consec_viol += 1
check(rest_viol == 0, f"Historie ohne Ruhezeitverstoss ({rest_viol})")
check(consec_viol == 0, f"Historie ohne zu lange Dienstfolgen ({consec_viol})")
check(not h.duplicated(["employee_id", "date"]).any(),
      "hoechstens ein Dienst je Person und Tag in der Historie")
filled = h.groupby(["date", "history_shift"]).size().unstack(fill_value=0)
need = hist[[f"required_{s}" for s in SHIFT_IDS]]
open_slots = sum(max(0, int(need.loc[d, f"required_{s}"]) - int(filled.loc[d, s]))
                 for d in hist.index for s in SHIFT_IDS if s in filled.columns)
tot = int(need.to_numpy().sum())
print(f"        offene Slots in der Historie:      {open_slots:>9d} von {tot} "
      f"({open_slots / tot:.1%})")
check(open_slots / tot <= 0.10, "Historie ist weitgehend besetzt", hard=False)

pd_days = len(plan) * len(staff)
for s in ["s1", "s2"]:
    n = int(df[f"absence_{s}"].sum())
    print(f"        {s.upper()}: {n:>3d} Ausfallereignisse ({n / pd_days:.1%} der Personentage)")
n1, n2 = int(df["absence_s1"].sum()), int(df["absence_s2"].sum())
check(n2 > n1, "Szenario S2 enthaelt mehr Ausfaelle als S1")
win = df[(df["absence_s2"] == 1) & (df["date_d"] >= date(2026, 12, 14))
         & (df["date_d"] < date(2026, 12, 20))]
check(len(win) / max(n2, 1) > 6 / 28,
      "S2-Ausfaelle sind im Wellenfenster ueberproportional (korreliert)")
check(df.loc[df["absence_s1"] == 1, "absence_s1_notice_h"].notna().all()
      and df.loc[df["absence_s2"] == 1, "absence_s2_notice_h"].notna().all(),
      "jedes Ausfallereignis hat eine Vorlaufzeit")
check(not ((df["absence_s1"] == 1) & (df["available"] == 0)).any()
      and not ((df["absence_s2"] == 1) & (df["available"] == 0)).any(),
      "kein kurzfristiger Ausfall an bereits geplanten Abwesenheitstagen")

print("\nF) Datenschutz")
forbidden = {"name", "vorname", "nachname", "geburtsdatum", "geburtstag",
             "diagnose", "krankheit", "grund", "reason", "icd", "adresse",
             "email", "telefon", "personalnummer"}
hits = sorted(set(c.lower() for c in df.columns) & forbidden)
check(not hits, f"keine personenbezogenen oder Gesundheitsspalten {hits}")
check(df["employee_id"].str.split("-").str[0].isin(["PK", "PH", "AZ"]).all(),
      "Mitarbeitende ausschliesslich als pseudonyme IDs gefuehrt")
check(set(df["availability_type"].unique())
      <= {"", "URLAUB", "FORTBILDUNG", "LANGZEITABWESENHEIT"},
      "Abwesenheitsarten ohne Grund- oder Diagnoseangabe")

print("\n" + "=" * 70)
print(f"harte Fehler: {len(FAIL)} | Hinweise: {len(WARN)}")
for m in FAIL:
    print("  FAIL:", m)
for m in WARN:
    print("  warn:", m)
sys.exit(1 if FAIL else 0)
