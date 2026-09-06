#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Planungs- und Bewertungslogik fuer die Schichtplanung (ohne Streamlit).

Bewusst frei von UI-Code, damit die Logik ohne laufende App testbar ist
(`test_planner.py`) und damit in Schritt 2 ein zweiter Planer (Constraint
Programming) mit identischer Schnittstelle danebengestellt werden kann:

    plan_greedy(ctx, scenario, ...)  ->  PlanResult      # Baseline
    plan_cp(ctx, scenario, ...)      ->  PlanResult      # spaeter

Alle Stamm-, Bedarfs- und Regeldaten stammen aus schichtplan_datensatz.csv.
Im Code stehen keine Grenzwerte: Ruhezeit, Hoechstarbeitszeit, Verhaeltniszahlen
und Qualifikationsvorgaben werden aus den Spalten des Datensatzes gelesen.

Wichtig fuer die Auswertung: `evaluate()` prueft den fertigen Plan unabhaengig
vom Planer nach. Ein Verfahren darf seine eigene Regelkonformitaet nicht selbst
behaupten - sonst waere der KPI-Vergleich zirkulaer.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from datetime import time as dtime

import pandas as pd

SHIFT_IDS = ["F", "S", "N"]
SCENARIOS = {
    "S0 - keine kurzfristigen Ausfaelle": None,
    "S1 - verteilte Ausfaelle": "absence_s1",
    "S2 - Ausfallwelle": "absence_s2",
}

REQUIRED_COLUMNS = [
    "employee_id", "date", "period", "role", "role_group", "employment_pct",
    "planable_minutes_horizon", "min_total_minutes", "max_total_minutes",
    "max_consecutive_shifts", "max_weekends", "max_night_shifts",
    "night_eligible", "ppug_countable", "ppug_category", "is_ward_lead",
    "time_account_start_min", "available", "history_shift",
    "absence_s1", "absence_s2",
] + [f"{p}_{s}" for s in SHIFT_IDS
     for p in ["required", "ppug_min", "min_fachkraft", "max_hilfskraft", "azubi_slots"]]


class DatasetError(ValueError):
    """Der Datensatz passt nicht zum erwarteten Schema."""


# --------------------------------------------------------------------------
# Laden und Kontext
# --------------------------------------------------------------------------

def load_dataset(source) -> pd.DataFrame:
    df = pd.read_csv(source)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DatasetError(
            "Im Datensatz fehlen erforderliche Spalten: " + ", ".join(missing[:8])
            + (" ..." if len(missing) > 8 else "")
        )
    df["date"] = pd.to_datetime(df["date"]).dt.date
    for col in ("availability_type", "history_shift", "request_on_shift", "holiday_name"):
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)
    return df


@dataclass
class Context:
    df: pd.DataFrame
    staff: pd.DataFrame                     # index: employee_id
    days: pd.DataFrame                      # index: date (nur Planhorizont)
    plan_dates: list[date]
    shifts: dict[str, dict]
    rules: dict[str, float]
    unavailable: set[tuple[str, date]]      # geplante Abwesenheiten im Horizont
    history: dict[tuple[str, date], str]    # Dienste der Vorperiode
    hist_dates: list[date]
    ward: dict


def _parse_time(value: str) -> dtime:
    return datetime.strptime(str(value).strip(), "%H:%M").time()


def build_context(df: pd.DataFrame) -> Context:
    g = df.iloc[0]
    shifts = {}
    for s in SHIFT_IDS:
        forb = str(g.get(f"shift_{s}_forbidden_next", "") or "")
        shifts[s] = {
            "start": _parse_time(g[f"shift_{s}_start"]),
            "end": _parse_time(g[f"shift_{s}_end"]),
            "net": int(g[f"shift_{s}_net_min"]),
            "forbidden_next": [x for x in forb.split("|") if x],
        }
    rules = {c: g[c] for c in df.columns if c.startswith("rule_")}
    ward = {c: g[c] for c in ("ward_id", "ward_name", "beds", "ppug_bereich",
                              "ppug_ratio_day", "ppug_ratio_night",
                              "dataset_version", "seed") if c in df.columns}

    staff = df.drop_duplicates("employee_id").set_index("employee_id").sort_index()
    plan = df[df["period"] == "plan"]
    days = plan.drop_duplicates("date").set_index("date").sort_index()

    unavailable = {(r.employee_id, r.date)
                   for r in plan[plan["available"] == 0].itertuples()}
    hist_rows = df[(df["period"] == "history") & (df["history_shift"] != "")]
    history = {(r.employee_id, r.date): r.history_shift for r in hist_rows.itertuples()}

    return Context(
        df=df, staff=staff, days=days,
        plan_dates=sorted(days.index),
        shifts=shifts, rules=rules, unavailable=unavailable, history=history,
        hist_dates=sorted(df.loc[df["period"] == "history", "date"].unique()),
        ward=ward,
    )


def shift_start(ctx: Context, d: date, s: str) -> datetime:
    return datetime.combine(d, ctx.shifts[s]["start"])


def shift_end(ctx: Context, d: date, s: str) -> datetime:
    sh = ctx.shifts[s]
    end = datetime.combine(d, sh["end"])
    if sh["end"] <= sh["start"]:
        end += timedelta(days=1)
    return end


def effective_capacity(ctx: Context) -> dict[str, float]:
    """
    Im Horizont tatsaechlich verplanbare Minuten je Person.

    `planable_minutes_horizon` ist die Vertragskapazitaet fuer volle vier
    Wochen. Wer 14 Tage Urlaub hat, kann davon nur die Haelfte leisten. Ohne
    diese Korrektur passiert zweierlei: die Kennzahl Arbeitszeitabweichung
    misst Urlaub statt Planungsqualitaet, und der Planer haelt Abwesende
    faelschlich fuer unterausgelastet und ueberlastet sie an ihren
    Anwesenheitstagen.
    """
    horizon = max(len(ctx.plan_dates), 1)
    cap = {}
    for e in ctx.staff.index:
        absent = sum(1 for d in ctx.plan_dates if (e, d) in ctx.unavailable)
        base = float(ctx.staff.loc[e, "planable_minutes_horizon"])
        cap[e] = max(base * (1 - absent / horizon), 0.0)
    return cap


def scenario_absences(ctx: Context, scenario: str) -> set[tuple[str, date]]:
    col = SCENARIOS.get(scenario)
    if col is None:
        return set()
    rows = ctx.df[(ctx.df["period"] == "plan") & (ctx.df[col] == 1)]
    return {(r.employee_id, r.date) for r in rows.itertuples()}


# --------------------------------------------------------------------------
# Ergebnisobjekt
# --------------------------------------------------------------------------

@dataclass
class PlanResult:
    method: str
    scenario: str
    assignments: dict[tuple[str, date], str] = field(default_factory=dict)
    open_slots: list[dict] = field(default_factory=list)
    runtime_s: float = 0.0

    def as_frame(self) -> pd.DataFrame:
        rows = [{"employee_id": e, "date": d, "assigned_shift": s}
                for (e, d), s in sorted(self.assignments.items(), key=lambda x: (x[0][1], x[0][0]))]
        return pd.DataFrame(rows, columns=["employee_id", "date", "assigned_shift"])

    def matrix(self, ctx: Context) -> pd.DataFrame:
        """Dienstplan als Matrix Mitarbeitende x Tage."""
        m = pd.DataFrame("", index=ctx.staff.index, columns=ctx.plan_dates, dtype=object)
        for (e, d), s in self.assignments.items():
            if d in m.columns:
                m.at[e, d] = s
        for (e, d) in ctx.unavailable:
            if d in m.columns and not m.at[e, d]:
                m.at[e, d] = "–"
        m.columns = [d.strftime("%d.%m.") for d in m.columns]
        return m


# --------------------------------------------------------------------------
# Baseline-Planer: transparente Greedy-Heuristik
# --------------------------------------------------------------------------

def plan_greedy(ctx: Context, scenario: str,
                manual_absences: set[tuple[str, date]] | None = None,
                fixed: dict[tuple[str, date], str] | None = None) -> PlanResult:
    """
    Regelbasierte Referenzplanung. Entspricht dem Vorgehen einer manuellen
    Excel-Planung: Tag fuer Tag, Schicht fuer Schicht, jeweils die Person mit
    der geringsten bisherigen Auslastung, die alle harten Regeln erfuellt.

    `fixed` haelt bereits getroffene Zuweisungen fest und ist die Grundlage der
    reaktiven Umplanung (Schritt 3): nur die von einem Ausfall betroffenen
    Slots werden neu besetzt, der Rest des Plans bleibt stehen.
    """
    t0 = time.perf_counter()
    manual = set(manual_absences or set())
    fixed = dict(fixed or {})
    blocked = ctx.unavailable | scenario_absences(ctx, scenario) | manual

    min_rest = float(ctx.rules.get("rule_min_rest_h", 11))
    st = ctx.staff
    cap_eff = effective_capacity(ctx)

    last_end: dict[str, datetime] = {}
    consec: dict[str, int] = {e: 0 for e in st.index}
    worked: dict[str, int] = {e: 0 for e in st.index}
    nights: dict[str, int] = {e: 0 for e in st.index}
    weekends: dict[str, set] = {e: set() for e in st.index}

    # Anschluss an die Vorperiode: letzte Schicht und laufende Dienstfolge
    for e in st.index:
        own = sorted((d for (emp, d) in ctx.history if emp == e))
        if not own:
            continue
        last_end[e] = shift_end(ctx, own[-1], ctx.history[(e, own[-1])])
        run, cursor = 0, ctx.plan_dates[0] - timedelta(days=1)
        while (e, cursor) in ctx.history:
            run += 1
            cursor -= timedelta(days=1)
        consec[e] = run

    assignments: dict[tuple[str, date], str] = {}
    open_slots: list[dict] = []

    def eligible(e: str, d: date, s: str) -> bool:
        row = st.loc[e]
        if (e, d) in blocked or (e, d) in assignments:
            return False
        if s == "N" and not int(row["night_eligible"]):
            return False
        if int(row["is_ward_lead"]) and s != "F":
            return False
        if consec[e] >= int(row["max_consecutive_shifts"]):
            return False
        if s == "N" and nights[e] >= int(row["max_night_shifts"]):
            return False
        if worked[e] + ctx.shifts[s]["net"] > int(row["max_total_minutes"]):
            return False
        if e in last_end:
            gap = (shift_start(ctx, d, s) - last_end[e]).total_seconds() / 3600
            if gap < min_rest:
                return False
        return True

    def score(e: str, d: date) -> tuple:
        row = st.loc[e]
        cap = max(cap_eff[e], 1.0)          # Urlaub bereits herausgerechnet
        weekend_pressure = 1 if (d.weekday() >= 5
                                 and len(weekends[e]) >= int(row["max_weekends"])) else 0
        return (weekend_pressure, worked[e] / cap,
                int(row["time_account_start_min"]), e)

    def assign(e: str, d: date, s: str) -> None:
        assignments[(e, d)] = s
        worked[e] += ctx.shifts[s]["net"]
        last_end[e] = shift_end(ctx, d, s)
        nights[e] += 1 if s == "N" else 0
        if d.weekday() >= 5:
            weekends[e].add(d.isocalendar()[1])

    for d in ctx.plan_dates:
        # bereits fixierte Zuweisungen zuerst uebernehmen
        for (e, dd), s in fixed.items():
            if dd == d and (e, d) not in blocked and (e, d) not in assignments:
                assign(e, d, s)

        for s in ["N", "F", "S"]:                 # Nachtdienst ist am staerksten
            day = ctx.days.loc[d]                 # eingeschraenkt -> zuerst
            need = int(day[f"required_{s}"])
            need_fach = int(day[f"min_fachkraft_{s}"])
            max_help = int(day[f"max_hilfskraft_{s}"])
            crew = [e for (e, dd), sh in assignments.items() if dd == d and sh == s]
            # Auszubildende zaehlen nicht auf die Besetzung (PpUGV § 2)
            placed = [e for e in crew if int(st.loc[e, "ppug_countable"]) == 1]
            fach = sum(1 for e in placed if st.loc[e, "ppug_category"] == "Pflegefachkraft")
            helpers = sum(1 for e in placed if st.loc[e, "ppug_category"] == "Pflegehilfskraft")

            pool = [e for e in st.index
                    if int(st.loc[e, "ppug_countable"]) == 1 and eligible(e, d, s)]
            pool.sort(key=lambda e: score(e, d))

            while len(placed) < need:
                remaining = need - len(placed)
                pick = None
                for e in pool:
                    if e in placed:
                        continue
                    is_fach = st.loc[e, "ppug_category"] == "Pflegefachkraft"
                    # Fachkraftquote absichern
                    if not is_fach and (need_fach - fach) >= remaining:
                        continue
                    if not is_fach and helpers >= max_help:
                        continue
                    pick = e
                    break
                if pick is None:
                    open_slots.append({"date": d, "shift_id": s,
                                       "slot": len(placed) + 1,
                                       "reason": "keine regelkonforme Besetzung verfuegbar"})
                    break
                assign(pick, d, s)
                placed.append(pick)
                fach += int(st.loc[pick, "ppug_category"] == "Pflegefachkraft")
                helpers += int(st.loc[pick, "ppug_category"] == "Pflegehilfskraft")

            # Auszubildende als zusaetzliche Besetzung (nicht anrechenbar).
            # Bereits fixierte Azubis zaehlen auf die Plaetze, sonst wuerde eine
            # Umplanung stillschweigend zusaetzliche Personen einplanen.
            slots = int(day[f"azubi_slots_{s}"]) - sum(
                1 for e in crew if st.loc[e, "role_group"] == "Auszubildende")
            if slots > 0 and (s != "N" or any(
                    st.loc[e, "ppug_category"] == "Pflegefachkraft" for e in placed)):
                azubis = [e for e in st.index
                          if st.loc[e, "role_group"] == "Auszubildende" and eligible(e, d, s)]
                azubis.sort(key=lambda e: score(e, d))
                for e in azubis[:slots]:
                    assign(e, d, s)

        for e in st.index:
            consec[e] = consec[e] + 1 if (e, d) in assignments else 0

    return PlanResult(method="Greedy-Heuristik (Baseline)", scenario=scenario,
                      assignments=assignments, open_slots=open_slots,
                      runtime_s=time.perf_counter() - t0)


# --------------------------------------------------------------------------
# Unabhaengige Bewertung
# --------------------------------------------------------------------------

def evaluate(ctx: Context, result: PlanResult) -> dict:
    """Prueft den fertigen Plan gegen die Regeln aus dem Datensatz."""
    st = ctx.staff
    a = result.assignments
    min_rest = float(ctx.rules.get("rule_min_rest_h", 11))
    viol: list[dict] = []

    def add(kind: str, msg: str, **kw):
        viol.append({"art": kind, "hinweis": msg, **kw})

    # --- Besetzung je Tag und Schicht -----------------------------------
    required = filled = 0
    ppug_breaches = fach_breaches = help_breaches = 0
    for d in ctx.plan_dates:
        day = ctx.days.loc[d]
        for s in SHIFT_IDS:
            need = int(day[f"required_{s}"])
            crew = [e for (e, dd), sh in a.items() if dd == d and sh == s]
            countable = [e for e in crew if int(st.loc[e, "ppug_countable"]) == 1]
            fach = [e for e in countable if st.loc[e, "ppug_category"] == "Pflegefachkraft"]
            helpers = [e for e in countable if st.loc[e, "ppug_category"] == "Pflegehilfskraft"]
            required += need
            filled += min(len(countable), need)
            if len(countable) < int(day[f"ppug_min_{s}"]):
                ppug_breaches += 1
                add("Untergrenze (PpUGV)",
                    f"{d:%d.%m.} {s}: {len(countable)} statt {int(day[f'ppug_min_{s}'])} Pflegekraefte",
                    datum=d, schicht=s)
            elif len(countable) < need:
                add("Unterbesetzung",
                    f"{d:%d.%m.} {s}: {len(countable)} statt {need} (Untergrenze eingehalten)",
                    datum=d, schicht=s)
            if len(fach) < min(int(day[f"min_fachkraft_{s}"]), len(countable)):
                fach_breaches += 1
                add("Qualifikation",
                    f"{d:%d.%m.} {s}: nur {len(fach)} Pflegefachkraefte", datum=d, schicht=s)
            if len(helpers) > int(day[f"max_hilfskraft_{s}"]):
                help_breaches += 1
                add("Qualifikation",
                    f"{d:%d.%m.} {s}: {len(helpers)} Pflegehilfskraefte ueber Grenze",
                    datum=d, schicht=s)

    # --- Regeln je Person ------------------------------------------------
    rest_v = consec_v = night_v = hours_v = weekend_v = night_count_v = 0
    for e in st.index:
        own = sorted([(d, s) for (emp, d), s in a.items() if emp == e])
        hist_own = sorted([(d, s) for (emp, d), s in ctx.history.items() if emp == e])
        chain = hist_own + own
        run = 1
        for (d1, s1), (d2, s2) in zip(chain, chain[1:]):
            gap = (shift_start(ctx, d2, s2) - shift_end(ctx, d1, s1)).total_seconds() / 3600
            if gap < min_rest and d2 in ctx.plan_dates:
                rest_v += 1
                add("Ruhezeit", f"{e}: {gap:.1f} h zwischen {d1:%d.%m.} {s1} "
                                f"und {d2:%d.%m.} {s2}", mitarbeiter=e, datum=d2)
            run = run + 1 if (d2 - d1).days == 1 else 1
            if run > int(st.loc[e, "max_consecutive_shifts"]) and d2 in ctx.plan_dates:
                consec_v += 1
                add("Dienstfolge", f"{e}: {run} Dienste in Folge bis {d2:%d.%m.}",
                    mitarbeiter=e, datum=d2)
        if any(s == "N" for _, s in own) and not int(st.loc[e, "night_eligible"]):
            night_v += 1
            add("Qualifikation", f"{e}: Nachtdienst ohne Nachtdiensteignung", mitarbeiter=e)
        n_nights = sum(1 for _, s in own if s == "N")
        if n_nights > int(st.loc[e, "max_night_shifts"]):
            night_count_v += 1
            add("Nachtarbeit (weich)", f"{e}: {n_nights} Nachtdienste ueber Richtwert",
                mitarbeiter=e)
        minutes = sum(ctx.shifts[s]["net"] for _, s in own)
        if minutes > int(st.loc[e, "max_total_minutes"]):
            hours_v += 1
            add("Arbeitszeit", f"{e}: {minutes / 60:.1f} h ueber Vertragsobergrenze",
                mitarbeiter=e)
        wk = {d.isocalendar()[1] for d, _ in own if d.weekday() >= 5}
        if len(wk) > int(st.loc[e, "max_weekends"]):
            weekend_v += 1
            add("Wochenende (weich)", f"{e}: {len(wk)} Wochenenden im Dienst",
                mitarbeiter=e)

    # --- Kennzahlen -------------------------------------------------------
    countable_ids = [e for e in st.index if int(st.loc[e, "ppug_countable"]) == 1]
    shifts_by_cat: dict[str, int] = {"Pflegefachkraft": 0, "Pflegehilfskraft": 0}
    for (e, _), _s in a.items():
        cat = st.loc[e, "ppug_category"]
        if cat in shifts_by_cat:
            shifts_by_cat[cat] += 1
    total_countable_shifts = sum(shifts_by_cat.values())
    helper_share = (shifts_by_cat["Pflegehilfskraft"] / total_countable_shifts
                    if total_countable_shifts else 0.0)

    # Arbeitszeitabweichung gegen die im Horizont tatsaechlich verfuegbare
    # Sollzeit (siehe effective_capacity)
    dev, hours_detail = [], []
    cap_eff = effective_capacity(ctx)
    for e in countable_ids:
        minutes = sum(ctx.shifts[s]["net"] for (emp, _), s in a.items() if emp == e)
        soll = cap_eff[e]
        if soll > 0:
            dev.append(abs(minutes - soll) / soll)
            hours_detail.append({"employee_id": e, "ist_min": minutes,
                                 "soll_min": round(soll),
                                 "abweichung_min": round(minutes - soll),
                                 "abweichung_pct": round((minutes - soll) / soll * 100, 1)})

    hard = rest_v + consec_v + hours_v + fach_breaches + help_breaches + night_v
    soft = weekend_v + night_count_v
    return {
        "besetzungsquote": filled / required if required else 0.0,
        "soll_dienste": required,
        "besetzte_dienste": filled,
        "offene_slots": len(result.open_slots),
        "untergrenzen_verstoesse": ppug_breaches,
        "qualifikationsverstoesse": fach_breaches + help_breaches + night_v,
        "harte_verstoesse": hard,
        "weiche_abweichungen": soft,
        "ruhezeit_verstoesse": rest_v,
        "dienstfolge_verstoesse": consec_v,
        "arbeitszeit_verstoesse": hours_v,
        "wochenend_abweichungen": weekend_v,
        "nachtdienst_abweichungen": night_count_v,
        "hilfskraftanteil": helper_share,
        "hilfskraft_grenze": float(ctx.rules.get("rule_max_helper_share", 0.10)),
        "arbeitszeitabweichung": sum(dev) / len(dev) if dev else 0.0,
        "arbeitszeit_detail": hours_detail,
        "planungszeit_s": result.runtime_s,
        "verstoesse": viol,
    }


def stability(reference: PlanResult, current: PlanResult) -> dict:
    """Planstabilitaet: wie stark weicht der angepasste Plan vom Ausgangsplan ab?"""
    keys = set(reference.assignments) | set(current.assignments)
    changed = sum(1 for k in keys
                  if reference.assignments.get(k) != current.assignments.get(k))
    base = max(len(reference.assignments), 1)
    return {"geaenderte_zuweisungen": changed,
            "anteil_geaendert": changed / base,
            "planstabilitaet": 1 - changed / base}


def export_frame(ctx: Context, result: PlanResult) -> pd.DataFrame:
    """Eingabedatensatz plus Ergebnisspalte - ein Artefakt fuer die Auswertung."""
    out = ctx.df.copy()
    key = pd.Series(list(zip(out["employee_id"], out["date"])), index=out.index)
    out["assigned_shift"] = key.map(result.assignments).fillna("")
    out.loc[out["period"] != "plan", "assigned_shift"] = ""
    out["plan_method"] = result.method
    out["plan_scenario"] = result.scenario
    return out
