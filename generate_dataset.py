#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Synthetischer Datensatz fuer die KI-gestuetzte Personal- und Schichtplanung
=========================================================================
Fallstudie: Normalstation "Innere Medizin und Kardiologie", 30 Betten.

Der Generator ist bewusst vollstaendig deterministisch (fester Seed) und
erzeugt aus wenigen dokumentierten Parametern alle Tabellen des Datensatzes.
Damit ist die Anforderung "Reproduzierbarkeit / Data Lineage" aus T2
(Schulz et al. 2026, S. 36-39) erfuellt: der Datensatz kann jederzeit exakt
neu erzeugt und je Attribut auf seine Quelle zurueckgefuehrt werden.

Es werden KEINE personenbezogenen und KEINE Gesundheitsdaten erzeugt.
Mitarbeitende sind ausschliesslich pseudonyme IDs; Ausfaelle sind reine
Verfuegbarkeitsereignisse ohne Grund, Diagnose oder Kategorie.

Quellenkuerzel (vollstaendige Belege in DATENKONZEPT.md):
  [PpUGV]   Pflegepersonaluntergrenzen-Verordnung, §2 (Begriffe, Tag-/Nachtschicht),
            §6 + Anlage (Verhaeltniszahlen, Pflegehilfskraftanteil)
  [PPBV]    Pflegepersonalbemessungsverordnung / PPR 2.0 (Grundwert, Fallwert,
            Spannweite der Minutenwerte A1/S1 - A4/S4)
  [ArbZG]   Arbeitszeitgesetz §3, §4, §5, §6
  [TVoeD-K] TVoeD-K §6 (38,5 h/Woche), §26 (30 Urlaubstage)
  [DESTATIS] Grunddaten der Krankenhaeuser 2024 (Bettenauslastung 72,0 %,
            Verweildauer 7,1 Tage)
  [SN]      Statistik Sachsen 2026 (Teilzeitquote 57,4 %, Fachkraftanteil 82,4 %,
            0,805 Vollkraefte je Kopf)
  [TK]      TK-Gesundheitsreport (28 AU-Tage/Jahr in der Krankenpflege)
  [ANNAHME] eigene, im Datenkonzept begruendete Setzung
"""

from __future__ import annotations

import csv
import json
import math
import os
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

import numpy as np

# --------------------------------------------------------------------------
# 0) Globale Parameter
# --------------------------------------------------------------------------

SEED = 20261130
DATASET_VERSION = "2.0.0"
BASE = os.path.dirname(os.path.abspath(__file__))
COMBINED_FILE = os.path.join(BASE, "schichtplan_datensatz.csv")
OUT = os.path.join(BASE, "data")   # nur bei --normalized

WARD = {
    "ward_id": "ST-IK1",
    "name": "Normalstation Innere Medizin / Kardiologie",
    "ppug_bereich": "Innere Medizin und Kardiologie",          # [PpUGV] Anlage
    "beds": 30,                                                 # [ANNAHME]
    "ratio_day": 10.0,                                          # [PpUGV] 10:1 Tagschicht
    "ratio_night": 22.0,                                        # [PpUGV] 22:1 Nachtschicht
    "max_helper_share_day": 0.10,                               # [PpUGV] max. 10 %
    "max_helper_share_night": 0.10,                             # [PpUGV] max. 10 %
    "bundesland": "Hamburg",                                    # [ANNAHME]
}

# Planungshorizont: 4 volle Wochen, Start Montag; Historie: 4 Wochen davor.
PLAN_START = date(2026, 11, 30)
PLAN_DAYS = 28
HIST_DAYS = 28
HIST_START = PLAN_START - timedelta(days=HIST_DAYS)
PLAN_END = PLAN_START + timedelta(days=PLAN_DAYS - 1)

# Gesetzliche Feiertage im Betrachtungszeitraum (Hamburg)
HOLIDAYS = {
    date(2026, 12, 25): "1. Weihnachtsfeiertag",
    date(2026, 12, 26): "2. Weihnachtsfeiertag",
}

# Belegungsmodell
BASE_OCCUPANCY = 0.72          # [DESTATIS] Bettenauslastung 2024 = 72,0 %
AVG_LOS_DAYS = 7.1             # [DESTATIS] durchschnittliche Verweildauer 2024
WEEKDAY_FACTOR = {             # [ANNAHME] Elektivsteuerung Mo-Do, Entlassungen Fr
    0: 1.06, 1: 1.09, 2: 1.09, 3: 1.05, 4: 0.98, 5: 0.90, 6: 0.90,
}
HOLIDAY_FACTOR = 0.85          # [ANNAHME]
XMAS_FACTOR = 0.80             # [ANNAHME] 24.12.-01.01. reduzierter Elektivbetrieb
OCC_NOISE_SD = 0.05            # [ANNAHME]

# Pflegeaufwand je Patient und Tag (Minuten)
PPR_MIN = 59                   # [PPBV] A1/S1 Erwachsene Normalstation
PPR_MAX = 427                  # [PPBV] A4/S4 Erwachsene Normalstation
PPR_MEDIAN = 118               # [ANNAHME] rechtsschiefe Verteilung, Median
PPR_SIGMA = 0.42               # [ANNAHME] Streuung (lognormal)
GRUNDWERT_MIN = 33             # [PPBV] Pflegegrundwert je Patient und Tag
FALLWERT_MIN = 75              # [PPBV] Fallwert je Aufnahme
ISOLATION_SURCHARGE = 90       # [PPBV] Zuschlag Isolationspflicht (33 -> 123)
ISOLATION_RATE = 0.05          # [ANNAHME]

# Verteilung des Tagesaufwands auf die Schichten
SHIFT_SHARE = {"F": 0.40, "S": 0.35, "N": 0.25}   # [ANNAHME]

# Ausfallzeiten fuer den Bruttopersonalbedarf
URLAUBSTAGE = 30               # [TVoeD-K] §26
AU_KALENDERTAGE = 28           # [TK] Krankenpflege
FORTBILDUNGSTAGE = 5           # [ANNAHME]
JAHRESARBEITSTAGE = 251        # [ANNAHME] 5-Tage-Woche abzgl. Feiertage

# Personalstruktur
WEEKLY_HOURS_FULL = 38.5       # [TVoeD-K] §6
PART_TIME_SHARE = 0.574        # [SN] Teilzeitquote im Pflegedienst
FACHKRAFT_SHARE = 0.824        # [SN] Anteil examinierter Pflegefachkraefte
PART_TIME_LEVELS = [0.50, 0.60, 0.70, 0.75, 0.80, 0.90]   # [ANNAHME]
LEITUNG_FREISTELLUNG = 0.50    # [ANNAHME] 50 % Leitungsfreistellung

# Arbeitszeitregeln
MIN_REST_H = 11                # [ArbZG] §5 Abs. 1
MIN_REST_H_HOSPITAL = 10       # [ArbZG] §5 Abs. 2 (nur mit Ausgleich)
MAX_CONSEC_SHIFTS = 5          # [ANNAHME] gestuetzt auf [ArbZG] §6 Abs. 1
MIN_CONSEC_DAYS_OFF = 2        # [ANNAHME]
MAX_WEEKENDS_PER_4W = 2        # [ANNAHME]
MAX_NIGHTS_PER_4W = 8          # [ANNAHME]

# Ausfallszenarien (kurzfristige Nichtverfuegbarkeit, ohne Grund/Diagnose)
SCEN_S1_RATE = 0.040           # [ANNAHME] abgeleitet aus [TK]
SCEN_S2_RATE = 0.040           # Grundrate; im Cluster erhoeht
SCEN_S2_CLUSTER_FACTOR = 3.0   # [ANNAHME]
SCEN_S2_CLUSTER_START = date(2026, 12, 14)
SCEN_S2_CLUSTER_LEN = 6

rng = np.random.default_rng(SEED)

# --------------------------------------------------------------------------
# 1) Kalender
# --------------------------------------------------------------------------

WD_DE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def all_days():
    d = HIST_START
    while d <= PLAN_END:
        yield d
        d += timedelta(days=1)


def build_calendar():
    rows = []
    for d in all_days():
        rows.append({
            "date": d.isoformat(),
            "weekday": WD_DE[d.weekday()],
            "weekday_num": d.weekday() + 1,
            "iso_week": d.isocalendar()[1],
            "is_weekend": int(d.weekday() >= 5),
            "is_holiday": int(d in HOLIDAYS),
            "holiday_name": HOLIDAYS.get(d, ""),
            "period": "history" if d < PLAN_START else "plan",
            "day_index": (d - PLAN_START).days,     # negativ = Historie
        })
    return rows


# --------------------------------------------------------------------------
# 2) Schichtarten
# --------------------------------------------------------------------------

SHIFTS = [
    # id, name, start, end, brutto, pause, ppug-Segment
    ("F", "Fruehdienst", time(6, 0), time(14, 0), 480, 30, "Tagschicht"),
    ("S", "Spaetdienst", time(13, 30), time(21, 30), 480, 30, "Tagschicht"),
    ("N", "Nachtdienst", time(21, 15), time(6, 15), 540, 45, "Nachtschicht"),
]
SHIFT_IDS = [s[0] for s in SHIFTS]
NET_MIN = {s[0]: s[4] - s[5] for s in SHIFTS}


def shift_start_dt(d: date, sid: str) -> datetime:
    s = [x for x in SHIFTS if x[0] == sid][0]
    return datetime.combine(d, s[2])


def shift_end_dt(d: date, sid: str) -> datetime:
    s = [x for x in SHIFTS if x[0] == sid][0]
    end = datetime.combine(d, s[3])
    if s[3] <= s[2]:
        end += timedelta(days=1)
    return end


def rest_hours(d1: date, s1: str, d2: date, s2: str) -> float:
    return (shift_start_dt(d2, s2) - shift_end_dt(d1, s1)).total_seconds() / 3600.0


def forbidden_successors(sid: str) -> list[str]:
    """Direkte Folgeschicht am Folgetag, die die 11-h-Ruhezeit verletzt [ArbZG §5]."""
    out = []
    d0 = date(2026, 1, 5)
    for nxt in SHIFT_IDS:
        if rest_hours(d0, sid, d0 + timedelta(days=1), nxt) < MIN_REST_H:
            out.append(nxt)
    return out


def build_shift_types():
    rows = []
    for sid, name, st, en, gross, brk, seg in SHIFTS:
        rows.append({
            "shift_id": sid,
            "name": name,
            "start_time": st.strftime("%H:%M"),
            "end_time": en.strftime("%H:%M"),
            "duration_min_gross": gross,
            "break_min": brk,
            "duration_min_net": gross - brk,
            "is_night_shift": int(sid == "N"),
            "ppug_segment": seg,
            "forbidden_successors": "|".join(forbidden_successors(sid)),
            "source": "Pausen nach ArbZG §4; Ruhezeit/Folgeschicht nach ArbZG §5; "
                      "Segmentzuordnung nach PpUGV §2 (Tag 6-22, Nacht 22-6)",
        })
    return rows


# --------------------------------------------------------------------------
# 3) Belegung und Pflegeaufwand
# --------------------------------------------------------------------------

def occ_factor(d: date) -> float:
    f = WEEKDAY_FACTOR[d.weekday()]
    if d in HOLIDAYS:
        f *= HOLIDAY_FACTOR
    if (d.month == 12 and d.day >= 24) or (d.month == 1 and d.day == 1):
        f *= XMAS_FACTOR
    return f


def build_occupancy():
    rows = []
    for d in all_days():
        mean = WARD["beds"] * BASE_OCCUPANCY * occ_factor(d)
        census12 = int(np.clip(round(rng.normal(mean, mean * OCC_NOISE_SD)), 10, WARD["beds"]))
        # Aufnahmen aus Verweildauer: census / LOS, elektiv Mo-Do etwas hoeher
        adm_mean = census12 / AVG_LOS_DAYS * (1.15 if d.weekday() <= 3 else 0.70)
        admissions = int(np.clip(rng.poisson(adm_mean), 0, 8))
        discharges = int(np.clip(rng.poisson(adm_mean * 0.95), 0, 8))
        # Mitternachtsbestand: nach Abendentlassungen leicht niedriger
        census00 = int(np.clip(census12 - rng.integers(0, 3), 8, WARD["beds"]))
        isolation = int(rng.binomial(census12, ISOLATION_RATE))

        # Pflegeaufwand je Patient (A+S) aus rechtsschiefer Verteilung, begrenzt
        # auf die in der PPBV dokumentierte Spannweite 59-427 Minuten.
        draws = rng.lognormal(mean=math.log(PPR_MEDIAN), sigma=PPR_SIGMA, size=census12)
        draws = np.clip(draws, PPR_MIN, PPR_MAX)
        care_min = float(draws.sum())
        care_min += census12 * GRUNDWERT_MIN
        care_min += isolation * ISOLATION_SURCHARGE
        care_min += admissions * FALLWERT_MIN

        rows.append({
            "date": d.isoformat(),
            "census_1200": census12,
            "census_0000": census00,
            "admissions": admissions,
            "discharges": discharges,
            "isolation_patients": isolation,
            "care_minutes_total": round(care_min),
            "period": "history" if d < PLAN_START else "plan",
        })
    return rows


def build_demand(occ_rows):
    """Ableitung der Sollbesetzung je Tag und Schicht (Data Lineage!)."""
    rows = []
    for o in occ_rows:
        d = date.fromisoformat(o["date"])
        for sid in SHIFT_IDS:
            if sid == "N":
                census = o["census_0000"]
                ratio = WARD["ratio_night"]
            else:
                census = o["census_1200"]
                ratio = WARD["ratio_day"]

            ppug_min = math.ceil(census / ratio)
            shift_care = o["care_minutes_total"] * SHIFT_SHARE[sid]
            ppr_based = shift_care / NET_MIN[sid]
            soll = max(ppug_min, int(round(ppr_based)))
            if sid == "N":
                soll = max(soll, 2)          # [ANNAHME] Zwei-Personen-Nachtdienst
            elif census >= 15:
                soll = max(soll, 3)          # [ANNAHME] Pausenabloesung nach ArbZG § 4

            if sid == "N":
                max_helper = 0               # 1 von 2 = 50 % > 10 % [PpUGV]
            else:
                max_helper = 1 if soll >= 3 else 0

            rows.append({
                "date": o["date"],
                "shift_id": sid,
                "census_reference": census,
                "ppug_ratio": ratio,
                "required_min_ppug": ppug_min,
                "care_minutes_shift": round(shift_care),
                "required_staff": soll,
                "min_pflegefachkraft": soll - max_helper,
                "max_pflegehilfskraft": max_helper,
                "azubi_slots": 1 if (sid in ("F", "S")) else 0,
                "period": o["period"],
            })
    return rows


# --------------------------------------------------------------------------
# 4) Personal
# --------------------------------------------------------------------------

@dataclass
class Employee:
    employee_id: str
    role: str
    role_group: str
    employment_pct: float
    night_eligible: int
    ppug_countable: int
    ppug_category: str
    leitung: int = 0
    skills: list[str] = field(default_factory=list)


def required_fte(demand_rows) -> float:
    """Netto-Vollkraftbedarf aus der Sollbesetzung des Planhorizonts."""
    minutes = sum(r["required_staff"] * NET_MIN[r["shift_id"]]
                  for r in demand_rows if r["period"] == "plan")
    fte_minutes = WEEKLY_HOURS_FULL * 60 * (PLAN_DAYS / 7)
    return minutes / fte_minutes


def ausfallquote() -> float:
    au_arbeitstage = AU_KALENDERTAGE * 5 / 7
    return (URLAUBSTAGE + au_arbeitstage + FORTBILDUNGSTAGE) / JAHRESARBEITSTAGE


def build_staff(demand_rows):
    netto = required_fte(demand_rows)
    brutto = netto / (1 - ausfallquote())

    staff: list[Employee] = []
    # 1 Stationsleitung, 50 % Leitungsfreistellung -> 0,5 VK in der Besetzung
    staff.append(Employee("PK-001", "Stationsleitung", "Pflegefachkraft", 1.0,
                          0, 1, "Pflegefachkraft", leitung=1,
                          skills=["EXAM", "LEITUNG", "PRAXISANLEITUNG"]))
    fte = 1.0 - LEITUNG_FREISTELLUNG

    # 2 Pflegehilfskraefte in Teilzeit: haelt den Hilfskraftanteil unter 10 %
    for i, pct in enumerate([0.75, 0.50], start=1):
        staff.append(Employee(f"PH-{i:03d}", "Pflegehilfskraft", "Pflegehilfskraft",
                              pct, 0, 1, "Pflegehilfskraft", skills=["PFLEGEHILFE"]))
        fte += pct

    # Pflegefachkraefte auffuellen bis zum Bruttobedarf
    idx = 2
    while fte < brutto - 0.15:
        part_time = rng.random() < PART_TIME_SHARE
        pct = float(rng.choice(PART_TIME_LEVELS)) if part_time else 1.0
        if fte + pct > brutto + 0.35:
            pct = min(PART_TIME_LEVELS, key=lambda p: abs(fte + p - brutto))
        skills = ["EXAM"]
        if rng.random() < 0.25:
            skills.append("PRAXISANLEITUNG")
        if rng.random() < 0.30:
            skills.append("KARDIO_MONITORING")
        staff.append(Employee(f"PK-{idx:03d}", "Pflegefachkraft", "Pflegefachkraft",
                              pct, 1, 1, "Pflegefachkraft", skills=skills))
        fte += pct
        idx += 1

    # 3 Auszubildende (Praxiseinsatz), nicht auf die Untergrenze anrechenbar
    for i, (yr, pct) in enumerate([(3, 1.0), (2, 1.0), (1, 1.0)], start=1):
        staff.append(Employee(f"AZ-{i:03d}", f"Auszubildende_r_{yr}_Ausbildungsjahr",
                              "Auszubildende", pct, 1 if yr >= 2 else 0, 0,
                              "nicht anrechenbar", skills=["AUSZUBILDEND"]))

    return staff, netto, brutto


def staff_rows(staff, accounts):
    rows = []
    for e in staff:
        weekly = round(WEEKLY_HOURS_FULL * e.employment_pct, 2)
        contract_min = int(round(weekly * 60 * PLAN_DAYS / 7))
        avail_factor = (1 - LEITUNG_FREISTELLUNG) if e.leitung else 1.0
        rows.append({
            "employee_id": e.employee_id,
            "role": e.role,
            "role_group": e.role_group,
            "employment_pct": round(e.employment_pct, 2),
            "weekly_hours": weekly,
            "contract_minutes_horizon": contract_min,
            "planable_minutes_horizon": int(round(contract_min * avail_factor)),
            "min_total_minutes": int(round(contract_min * avail_factor * 0.90)),
            "max_total_minutes": int(round(contract_min * avail_factor * 1.10)),
            "max_consecutive_shifts": MAX_CONSEC_SHIFTS,
            "min_consecutive_days_off": MIN_CONSEC_DAYS_OFF,
            "max_weekends": MAX_WEEKENDS_PER_4W,
            "max_night_shifts": MAX_NIGHTS_PER_4W if e.night_eligible else 0,
            "night_eligible": e.night_eligible,
            "ppug_countable": e.ppug_countable,
            "ppug_category": e.ppug_category,
            "is_ward_lead": e.leitung,
            "lead_release_pct": LEITUNG_FREISTELLUNG if e.leitung else 0.0,
            "time_account_start_min": accounts.get(e.employee_id, 0),
        })
    return rows


# --------------------------------------------------------------------------
# 5) Geplante Abwesenheiten und Wuensche
# --------------------------------------------------------------------------

def build_availability(staff):
    """Urlaub, Fortbildung, Leitungsfreistellung, eine Langzeitabwesenheit."""
    rows = []
    ids = [e.employee_id for e in staff]

    # Urlaub: 30 Tage/Jahr -> im 28-Tage-Fenster im Mittel ~2,3 Tage je Person;
    # realistisch als Bloecke, nicht als Einzeltage.
    n_vacation = max(4, int(round(len(staff) * 0.22)))
    vac_ids = list(rng.choice(ids, size=n_vacation, replace=False))
    for eid in vac_ids:
        length = int(rng.choice([7, 10, 10, 14]))
        start = PLAN_START + timedelta(days=int(rng.integers(0, PLAN_DAYS - 3)))
        for k in range(length):
            d = start + timedelta(days=k)
            if PLAN_START <= d <= PLAN_END:
                rows.append({"employee_id": eid, "date": d.isoformat(),
                             "availability_type": "URLAUB", "available": 0,
                             "known_at_planning": 1})

    # Fortbildung: einzelne Tage
    for eid in rng.choice(ids, size=max(2, len(staff) // 7), replace=False):
        d = PLAN_START + timedelta(days=int(rng.integers(0, PLAN_DAYS)))
        rows.append({"employee_id": eid, "date": d.isoformat(),
                     "availability_type": "FORTBILDUNG", "available": 0,
                     "known_at_planning": 1})

    # Eine bereits vor Planungsbeginn bekannte Langzeitabwesenheit (neutral,
    # ohne Grund) - trennt planbare von kurzfristiger Nichtverfuegbarkeit.
    long_id = [e.employee_id for e in staff if e.role_group == "Pflegefachkraft"][-1]
    for k in range(PLAN_DAYS):
        d = PLAN_START + timedelta(days=k)
        rows.append({"employee_id": long_id, "date": d.isoformat(),
                     "availability_type": "LANGZEITABWESENHEIT", "available": 0,
                     "known_at_planning": 1})

    # Deduplizieren (Urlaub kann sich mit Fortbildung ueberlappen)
    seen, uniq = set(), []
    for r in rows:
        key = (r["employee_id"], r["date"])
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    uniq.sort(key=lambda r: (r["date"], r["employee_id"]))
    return uniq


def build_requests(staff, unavailable):
    """Wunschfrei / Wunschdienst mit Gewichtung (analog INRC-II S4)."""
    rows = []
    for e in staff:
        for _ in range(int(rng.integers(1, 4))):
            d = PLAN_START + timedelta(days=int(rng.integers(0, PLAN_DAYS)))
            if (e.employee_id, d.isoformat()) in unavailable:
                continue
            if rng.random() < 0.75:
                rows.append({"employee_id": e.employee_id, "date": d.isoformat(),
                             "shift_id": "ALL", "request_type": "OFF",
                             "weight": int(rng.choice([1, 2, 3]))})
            else:
                rows.append({"employee_id": e.employee_id, "date": d.isoformat(),
                             "shift_id": str(rng.choice(SHIFT_IDS)),
                             "request_type": "ON",
                             "weight": int(rng.choice([1, 2]))})
    rows.sort(key=lambda r: (r["date"], r["employee_id"]))
    return rows


# --------------------------------------------------------------------------
# 6) Historie (Vorperiode) - einfache, dokumentierte Greedy-Belegung
# --------------------------------------------------------------------------

def build_history(staff, demand_rows):
    dem = {(r["date"], r["shift_id"]): r for r in demand_rows if r["period"] == "history"}
    last: dict[str, tuple[date, str]] = {}
    consec: dict[str, int] = {e.employee_id: 0 for e in staff}
    worked: dict[str, int] = {e.employee_id: 0 for e in staff}
    weekends: dict[str, set] = {e.employee_id: set() for e in staff}
    nights: dict[str, int] = {e.employee_id: 0 for e in staff}
    by_id = {e.employee_id: e for e in staff}

    # Vorperiodenurlaub (grob, damit die Historie nicht ueberzeichnet)
    hist_off = set()
    for eid in rng.choice([e.employee_id for e in staff], size=3, replace=False):
        start = HIST_START + timedelta(days=int(rng.integers(0, HIST_DAYS - 7)))
        for k in range(7):
            hist_off.add((eid, (start + timedelta(days=k)).isoformat()))

    assignments = []
    for k in range(HIST_DAYS):
        d = HIST_START + timedelta(days=k)
        assigned_today = set()
        for sid in ["N", "F", "S"]:
            row = dem[(d.isoformat(), sid)]
            need = row["required_staff"]
            need_fach = row["min_pflegefachkraft"]
            pool = []
            for e in staff:
                eid = e.employee_id
                if eid in assigned_today or (eid, d.isoformat()) in hist_off:
                    continue
                if sid == "N" and not e.night_eligible:
                    continue
                if e.leitung and sid != "F":
                    continue
                if consec[eid] >= MAX_CONSEC_SHIFTS:
                    continue
                if eid in last:
                    ld, ls = last[eid]
                    if rest_hours(ld, ls, d, sid) < MIN_REST_H:
                        continue
                if sid == "N" and nights[eid] >= MAX_NIGHTS_PER_4W:
                    continue
                cap = WEEKLY_HOURS_FULL * 60 * (HIST_DAYS / 7) * e.employment_pct
                pool.append((worked[eid] / max(cap, 1), eid))
            pool.sort()

            picked, fach = [], 0
            for _, eid in pool:
                if len(picked) >= need:
                    break
                e = by_id[eid]
                is_fach = e.ppug_category == "Pflegefachkraft"
                remaining = need - len(picked)
                if not is_fach and (need_fach - fach) >= remaining:
                    continue
                if e.role_group == "Auszubildende":
                    continue
                picked.append(eid)
                fach += int(is_fach)

            for eid in picked:
                assignments.append({"employee_id": eid, "date": d.isoformat(),
                                    "shift_id": sid})
                assigned_today.add(eid)
                last[eid] = (d, sid)
                worked[eid] += NET_MIN[sid]
                nights[eid] += int(sid == "N")
                if d.weekday() >= 5:
                    weekends[eid].add(d.isocalendar()[1])

        for e in staff:
            consec[e.employee_id] = consec[e.employee_id] + 1 if e.employee_id in assigned_today else 0

    # Arbeitszeitkonto zu Planbeginn: geleistete Minuten + Gutschrift fuer
    # abwesende Tage abzueglich Sollarbeitszeit der Vorperiode.
    accounts = {}
    for e in staff:
        cap = WEEKLY_HOURS_FULL * 60 * (HIST_DAYS / 7) * e.employment_pct
        if e.leitung:
            cap *= (1 - LEITUNG_FREISTELLUNG)
        off_days = sum(1 for k in range(HIST_DAYS)
                       if (e.employee_id, (HIST_START + timedelta(days=k)).isoformat()) in hist_off)
        credit = off_days * (WEEKLY_HOURS_FULL * 60 / 5) * e.employment_pct
        accounts[e.employee_id] = int(round(worked[e.employee_id] + credit - cap))

    assignments.sort(key=lambda r: (r["date"], r["shift_id"], r["employee_id"]))
    return assignments, accounts, hist_off


# --------------------------------------------------------------------------
# 7) Ausfallszenarien
# --------------------------------------------------------------------------

def build_scenarios(staff, demand_rows, unavailable):
    scen_meta = [
        {"scenario_id": "S0", "name": "Referenz ohne kurzfristige Ausfaelle",
         "description": "Basisplan; nur geplante Abwesenheiten aus availability.csv.",
         "short_notice_rate": 0.0, "clustered": 0,
         "source": "Referenzszenario fuer die Baseline-Messung"},
        {"scenario_id": "S1", "name": "Regelbetrieb mit verteilten Ausfaellen",
         "description": "Kurzfristige Nichtverfuegbarkeit einzelner Dienste, "
                        "unabhaengig ueber den Horizont verteilt.",
         "short_notice_rate": SCEN_S1_RATE, "clustered": 0,
         "source": "Rate abgeleitet aus TK-Gesundheitsreport (28 AU-Tage/Jahr), "
                   "Langzeitanteil herausgerechnet [ANNAHME]"},
        {"scenario_id": "S2", "name": "Ausfallwelle",
         "description": "Gleiche Grundrate wie S1, zusaetzlich verdreifachte Rate "
                        "in einem sechstaegigen Fenster (korrelierte Ausfaelle).",
         "short_notice_rate": SCEN_S2_RATE, "clustered": 1,
         "source": "Clusterannahme fuer Infektwellen [ANNAHME]"},
    ]

    plan_days = [PLAN_START + timedelta(days=k) for k in range(PLAN_DAYS)]
    events = []
    for meta in scen_meta:
        if meta["short_notice_rate"] == 0:
            continue
        for d in plan_days:
            rate = meta["short_notice_rate"]
            if meta["clustered"] and 0 <= (d - SCEN_S2_CLUSTER_START).days < SCEN_S2_CLUSTER_LEN:
                rate *= SCEN_S2_CLUSTER_FACTOR
            for e in staff:
                if (e.employee_id, d.isoformat()) in unavailable:
                    continue
                if rng.random() < rate:
                    events.append({
                        "scenario_id": meta["scenario_id"],
                        "employee_id": e.employee_id,
                        "date": d.isoformat(),
                        "shift_id": "ALL",
                        "available": 0,
                        "notice_hours": int(rng.choice([2, 4, 8, 12, 12, 24])),
                        "event_type": "KURZFRISTIGE_NICHTVERFUEGBARKEIT",
                    })
    events.sort(key=lambda r: (r["scenario_id"], r["date"], r["employee_id"]))
    return scen_meta, events


# --------------------------------------------------------------------------
# 8) Regelwerk
# --------------------------------------------------------------------------

def build_rules():
    R = lambda i, c, p, v, u, s, sc, n: {
        "rule_id": i, "category": c, "parameter": p, "value": v, "unit": u,
        "scope": sc, "legal_source": s, "note": n}
    return [
        R("R01", "Arbeitszeit", "max_werktaegliche_arbeitszeit", 8, "Stunden",
          "ArbZG § 3 Satz 1", "Mitarbeitende", "Verlaengerung auf 10 h nur mit Ausgleich"),
        R("R02", "Arbeitszeit", "max_werktaegliche_arbeitszeit_mit_ausgleich", 10, "Stunden",
          "ArbZG § 3 Satz 2", "Mitarbeitende", "Durchschnitt 8 h in 24 Wochen/6 Monaten"),
        R("R03", "Pause", "pause_ab_6h", 30, "Minuten",
          "ArbZG § 4", "Schicht", "bei mehr als 6 bis 9 Stunden"),
        R("R04", "Pause", "pause_ab_9h", 45, "Minuten",
          "ArbZG § 4", "Schicht", "bei mehr als 9 Stunden"),
        R("R05", "Pause", "max_arbeit_ohne_pause", 6, "Stunden",
          "ArbZG § 4 Satz 3", "Schicht", "keine Arbeit laenger als 6 h am Stueck"),
        R("R06", "Ruhezeit", "min_ruhezeit", MIN_REST_H, "Stunden",
          "ArbZG § 5 Abs. 1", "Schichtfolge", "harte Nebenbedingung"),
        R("R07", "Ruhezeit", "min_ruhezeit_krankenhaus", MIN_REST_H_HOSPITAL, "Stunden",
          "ArbZG § 5 Abs. 2", "Schichtfolge",
          "Verkuerzung um 1 h nur mit Ausgleich auf 12 h im Monat/4 Wochen"),
        R("R08", "Nachtarbeit", "max_nachtschicht_dauer", 8, "Stunden",
          "ArbZG § 6 Abs. 2", "Nachtdienst", "10 h nur mit Ausgleich im Monat/4 Wochen"),
        R("R09", "Nachtarbeit", "arbeitswissenschaftliche_gestaltung", 1, "boolean",
          "ArbZG § 6 Abs. 1", "Schichtsystem",
          "Begruendung fuer max. aufeinanderfolgende Dienste und Vorwaertsrotation"),
        R("R10", "Mindestbesetzung", "verhaeltniszahl_tagschicht", WARD["ratio_day"],
          "Patienten je Pflegekraft", "PpUGV § 6 i. V. m. Anlage",
          "Tagschicht 6-22 Uhr", "Innere Medizin und Kardiologie"),
        R("R11", "Mindestbesetzung", "verhaeltniszahl_nachtschicht", WARD["ratio_night"],
          "Patienten je Pflegekraft", "PpUGV § 6 i. V. m. Anlage",
          "Nachtschicht 22-6 Uhr", "Innere Medizin und Kardiologie"),
        R("R12", "Qualifikation", "max_pflegehilfskraftanteil", 0.10, "Anteil",
          "PpUGV § 6 i. V. m. Anlage", "Station/Monat",
          "Monatsdurchschnitt je Station und Schichtart"),
        R("R13", "Qualifikation", "azubi_anrechenbar", 0, "boolean",
          "PpUGV § 2 Abs. 1", "Mindestbesetzung",
          "Pflegekraft = Pflegefachkraft oder Pflegehilfskraft; Auszubildende "
          "sind dort nicht genannt und werden hier nicht angerechnet"),
        R("R14", "Arbeitszeit", "regelmaessige_wochenarbeitszeit", WEEKLY_HOURS_FULL,
          "Stunden", "TVoeD-K § 6 Abs. 1", "Vollzeit", "Vollzeitaequivalent"),
        R("R15", "Abwesenheit", "urlaubsanspruch", URLAUBSTAGE, "Arbeitstage",
          "TVoeD-K § 26 Abs. 1", "Jahr", "5-Tage-Woche"),
        R("R16", "Schichtfolge", "max_aufeinanderfolgende_dienste", MAX_CONSEC_SHIFTS,
          "Dienste", "ANNAHME (gestuetzt auf ArbZG § 6 Abs. 1)", "Mitarbeitende", ""),
        R("R17", "Schichtfolge", "min_freie_tage_am_stueck", MIN_CONSEC_DAYS_OFF,
          "Tage", "ANNAHME", "Mitarbeitende", "weiche Nebenbedingung"),
        R("R18", "Schichtfolge", "max_wochenenden_pro_4_wochen", MAX_WEEKENDS_PER_4W,
          "Wochenenden", "ANNAHME", "Mitarbeitende", "weiche Nebenbedingung"),
        R("R19", "Nachtarbeit", "max_nachtdienste_pro_4_wochen", MAX_NIGHTS_PER_4W,
          "Dienste", "ANNAHME", "Mitarbeitende", "weiche Nebenbedingung"),
        R("R20", "Datenschutz", "gesundheitsdaten_im_datensatz", 0, "boolean",
          "DSGVO Art. 9 / Projektvorgabe T7", "Datensatz",
          "Ausfaelle sind reine Verfuegbarkeitsereignisse ohne Grund oder Diagnose"),
    ]


# --------------------------------------------------------------------------
# 9) Kombinierte Einzeltabelle
# --------------------------------------------------------------------------
#
# Analysekorn: eine Zeile je Mitarbeitendem und Kalendertag.
#
# Damit der gesamte Datensatz in einer einzigen CSV-Datei transportiert werden
# kann, werden die Stamm-, Bedarfs- und Regeldaten bewusst denormalisiert:
# Mitarbeiterattribute wiederholen sich je Tag, Tages- und Bedarfsattribute je
# Mitarbeitendem, Stations- und Regelattribute in jeder Zeile. Das verletzt die
# dritte Normalform absichtlich (siehe DATENKONZEPT.md, Abschnitt 4). Die
# Konsistenz der Wiederholungen ist nicht Aufgabe des Nutzers, sondern wird vom
# Generator erzeugt und vom Pruefskript verifiziert.

CONST_RULES = {
    "rule_min_rest_h": MIN_REST_H,                          # ArbZG § 5 Abs. 1
    "rule_min_rest_h_with_compensation": MIN_REST_H_HOSPITAL,  # ArbZG § 5 Abs. 2
    "rule_max_daily_h": 8,                                  # ArbZG § 3 Satz 1
    "rule_max_daily_h_with_compensation": 10,               # ArbZG § 3 Satz 2
    "rule_break_min_6_to_9h": 30,                           # ArbZG § 4
    "rule_break_min_over_9h": 45,                           # ArbZG § 4
    "rule_max_night_h": 8,                                  # ArbZG § 6 Abs. 2
    "rule_weekly_hours_fulltime": WEEKLY_HOURS_FULL,        # TVoeD-K § 6
    "rule_annual_leave_days": URLAUBSTAGE,                  # TVoeD-K § 26
    "rule_max_helper_share": WARD["max_helper_share_day"],  # PpUGV Anlage
    "rule_azubi_counts_towards_minimum": 0,                 # PpUGV § 2
}


def build_combined(calendar, shift_types, st_rows, staff, occupancy, demand,
                   availability, requests, history, absence_events, hist_off):
    occ = {r["date"]: r for r in occupancy}
    dem = {(r["date"], r["shift_id"]): r for r in demand}
    stm = {r["employee_id"]: r for r in st_rows}
    sk = {}
    for e in staff:
        sk[e.employee_id] = "|".join(e.skills)
    avail = {(r["employee_id"], r["date"]): r for r in availability}
    hist = {(r["employee_id"], r["date"]): r["shift_id"] for r in history}
    req_off, req_on = {}, {}
    for r in requests:
        key = (r["employee_id"], r["date"])
        if r["request_type"] == "OFF":
            req_off[key] = r["weight"]
        else:
            req_on[key] = (r["shift_id"], r["weight"])
    ev = {}
    for r in absence_events:
        ev[(r["scenario_id"], r["employee_id"], r["date"])] = r["notice_hours"]

    shift_const = {}
    for s in shift_types:
        p = s["shift_id"]
        shift_const[f"shift_{p}_start"] = s["start_time"]
        shift_const[f"shift_{p}_end"] = s["end_time"]
        shift_const[f"shift_{p}_net_min"] = s["duration_min_net"]
        shift_const[f"shift_{p}_forbidden_next"] = s["forbidden_successors"]

    ward_const = {
        "ward_id": WARD["ward_id"],
        "ward_name": WARD["name"],
        "beds": WARD["beds"],
        "ppug_bereich": WARD["ppug_bereich"],
        "ppug_ratio_day": WARD["ratio_day"],
        "ppug_ratio_night": WARD["ratio_night"],
    }

    rows = []
    for c in calendar:
        d = c["date"]
        o = occ[d]
        for e in staff:
            eid = e.employee_id
            m = stm[eid]
            a = avail.get((eid, d))
            in_hist_off = (eid, d) in hist_off
            if a is not None:
                available, atype = 0, a["availability_type"]
            elif in_hist_off:
                available, atype = 0, "URLAUB"
            else:
                available, atype = 1, ""
            on = req_on.get((eid, d), ("", ""))

            row = {
                # Schluessel und Kalender
                "employee_id": eid,
                "date": d,
                "period": c["period"],
                "day_index": c["day_index"],
                "weekday": c["weekday"],
                "weekday_num": c["weekday_num"],
                "iso_week": c["iso_week"],
                "is_weekend": c["is_weekend"],
                "is_holiday": c["is_holiday"],
                "holiday_name": c["holiday_name"],
                # Mitarbeiterstammdaten (konstant je employee_id)
                "role": m["role"],
                "role_group": m["role_group"],
                "skills": sk[eid],
                "employment_pct": m["employment_pct"],
                "weekly_hours": m["weekly_hours"],
                "contract_minutes_horizon": m["contract_minutes_horizon"],
                "planable_minutes_horizon": m["planable_minutes_horizon"],
                "min_total_minutes": m["min_total_minutes"],
                "max_total_minutes": m["max_total_minutes"],
                "max_consecutive_shifts": m["max_consecutive_shifts"],
                "min_consecutive_days_off": m["min_consecutive_days_off"],
                "max_weekends": m["max_weekends"],
                "max_night_shifts": m["max_night_shifts"],
                "night_eligible": m["night_eligible"],
                "ppug_countable": m["ppug_countable"],
                "ppug_category": m["ppug_category"],
                "is_ward_lead": m["is_ward_lead"],
                "lead_release_pct": m["lead_release_pct"],
                "time_account_start_min": m["time_account_start_min"],
                # Belegung (konstant je date)
                "census_1200": o["census_1200"],
                "census_0000": o["census_0000"],
                "admissions": o["admissions"],
                "discharges": o["discharges"],
                "isolation_patients": o["isolation_patients"],
                "care_minutes_total": o["care_minutes_total"],
                # Verfuegbarkeit, Wuensche, Historie (je Mitarbeitendem und Tag)
                "available": available,
                "availability_type": atype,
                "request_off_weight": req_off.get((eid, d), ""),
                "request_on_shift": on[0],
                "request_on_weight": on[1],
                "history_shift": hist.get((eid, d), ""),
                # Ausfallszenarien (nur im Planhorizont belegt)
                "absence_s1": int(("S1", eid, d) in ev),
                "absence_s1_notice_h": ev.get(("S1", eid, d), ""),
                "absence_s2": int(("S2", eid, d) in ev),
                "absence_s2_notice_h": ev.get(("S2", eid, d), ""),
            }
            # Bedarf je Schicht (konstant je date)
            for sid in SHIFT_IDS:
                r = dem[(d, sid)]
                row[f"required_{sid}"] = r["required_staff"]
                row[f"ppug_min_{sid}"] = r["required_min_ppug"]
                row[f"min_fachkraft_{sid}"] = r["min_pflegefachkraft"]
                row[f"max_hilfskraft_{sid}"] = r["max_pflegehilfskraft"]
                row[f"care_minutes_{sid}"] = r["care_minutes_shift"]
                row[f"azubi_slots_{sid}"] = r["azubi_slots"]
            row.update(ward_const)
            row.update(shift_const)
            row.update(CONST_RULES)
            row["dataset_version"] = DATASET_VERSION
            row["seed"] = SEED
            rows.append(row)

    rows.sort(key=lambda r: (r["date"], r["employee_id"]))
    return rows


# --------------------------------------------------------------------------
# 10) Schreiben
# --------------------------------------------------------------------------

def write_csv(name, rows, fieldnames=None):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    fn = fieldnames or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fn)
        w.writeheader()
        w.writerows(rows)
    return path, len(rows)


def main(write_normalized: bool = False):
    calendar = build_calendar()
    shift_types = build_shift_types()
    occupancy = build_occupancy()
    demand = build_demand(occupancy)
    staff, netto, brutto = build_staff(demand)
    history, accounts, hist_off = build_history(staff, demand)
    availability = build_availability(staff)
    unavailable = {(r["employee_id"], r["date"]) for r in availability}
    requests = build_requests(staff, unavailable)
    scen_meta, absence_events = build_scenarios(staff, demand, unavailable)
    st_rows = staff_rows(staff, accounts)

    skills = [
        {"skill_id": "EXAM", "name": "Pflegefachkraft (examiniert)",
         "description": "Erlaubnis zur Fuehrung der Berufsbezeichnung nach PflBG",
         "source": "PpUGV § 2 Abs. 2"},
        {"skill_id": "PFLEGEHILFE", "name": "Pflegehilfskraft",
         "description": "landesrechtlich geregelte Assistenz-/Helferausbildung (mind. 1 Jahr)",
         "source": "PpUGV § 2 Abs. 3"},
        {"skill_id": "AUSZUBILDEND", "name": "Auszubildende/r",
         "description": "Praxiseinsatz, nicht auf die Untergrenze anrechenbar",
         "source": "PpUGV § 2 Abs. 1 (Umkehrschluss)"},
        {"skill_id": "LEITUNG", "name": "Stationsleitung",
         "description": "Leitungsfunktion mit teilweiser Freistellung", "source": "ANNAHME"},
        {"skill_id": "PRAXISANLEITUNG", "name": "Praxisanleitung",
         "description": "Anleitung von Auszubildenden im Praxiseinsatz", "source": "ANNAHME"},
        {"skill_id": "KARDIO_MONITORING", "name": "Monitoring-Qualifikation",
         "description": "Telemetrie-/Rhythmusueberwachung auf der kardiologischen Station",
         "source": "ANNAHME"},
    ]
    staff_skills = [{"employee_id": e.employee_id, "skill_id": s}
                    for e in staff for s in e.skills]

    ward_rows = [{**WARD, "plan_start": PLAN_START.isoformat(),
                  "plan_end": PLAN_END.isoformat(), "plan_days": PLAN_DAYS,
                  "history_start": HIST_START.isoformat(),
                  "history_days": HIST_DAYS, "seed": SEED}]

    # --- die auszuliefernde Einzeldatei -----------------------------------
    combined = build_combined(calendar, shift_types, st_rows, staff, occupancy,
                              demand, availability, requests, history,
                              absence_events, hist_off)
    fieldnames = list(combined[0].keys())
    with open(COMBINED_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(combined)

    print(f"Netto-VK-Bedarf: {netto:.2f} | Ausfallquote: {ausfallquote():.1%} "
          f"| Brutto-VK-Bedarf: {brutto:.2f}")
    print(f"Personal: {len(staff)} Koepfe / {sum(e.employment_pct for e in staff):.2f} VK")
    print(f"\n{os.path.basename(COMBINED_FILE)}: {len(combined)} Zeilen "
          f"({len(staff)} Mitarbeitende x {len(calendar)} Tage), "
          f"{len(fieldnames)} Spalten, "
          f"{os.path.getsize(COMBINED_FILE) / 1024:.0f} KB")

    # --- optionale Normalform fuer Nachvollziehbarkeit ---------------------
    if write_normalized:
        written = [
            write_csv("ward.csv", ward_rows),
            write_csv("calendar.csv", calendar),
            write_csv("shift_types.csv", shift_types),
            write_csv("skills.csv", skills),
            write_csv("staff.csv", st_rows),
            write_csv("staff_skills.csv", staff_skills),
            write_csv("occupancy.csv", occupancy),
            write_csv("demand.csv", demand),
            write_csv("availability.csv", availability),
            write_csv("shift_requests.csv", requests),
            write_csv("history_assignments.csv", history),
            write_csv("scenarios.csv", scen_meta),
            write_csv("absence_events.csv", absence_events),
            write_csv("rules.csv", build_rules()),
        ]
        meta = {
            "dataset": "careplan-innere-kardiologie-30betten",
            "version": DATASET_VERSION,
            "generated_by": os.path.basename(__file__),
            "seed": SEED,
            "plan_horizon": [PLAN_START.isoformat(), PLAN_END.isoformat()],
            "history_horizon": [HIST_START.isoformat(),
                                (PLAN_START - timedelta(days=1)).isoformat()],
            "headcount": len(staff),
            "fte_total": round(sum(e.employment_pct for e in staff), 2),
            "fte_netto_bedarf": round(netto, 2),
            "fte_brutto_bedarf": round(brutto, 2),
            "ausfallquote_planung": round(ausfallquote(), 4),
            "contains_personal_data": False,
            "contains_health_data": False,
            "files": {os.path.basename(p): c for p, c in written},
        }
        with open(os.path.join(OUT, "dataset_meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        print("\noptionale Normalform in data/:")
        for p, c in written:
            print(f"  {os.path.basename(p):26s} {c:6d} Zeilen")


if __name__ == "__main__":
    import sys
    main(write_normalized="--normalized" in sys.argv)
