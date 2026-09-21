#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Planungs- und Bewertungslogik fuer die Schichtplanung (ohne Streamlit).

Bewusst frei von UI-Code, damit die Logik ohne laufende App testbar ist
(`test_planner.py`). Zwei Planer mit identischer Schnittstelle stehen
nebeneinander und arbeiten auf denselben Daten, Regeln und Szenarien:

    plan_greedy(ctx, scenario, ...)  ->  PlanResult   # regelbasierte Baseline
    plan_milp(ctx, scenario, ...)    ->  PlanResult   # MILP-Optimierung (HiGHS)

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

# Stand der Schnittstelle. streamlit_app.py prueft ihn beim Start, damit eine
# neue Oberflaeche nicht unbemerkt auf eine alte Planungslogik trifft.
# 2 = Krankheitsgutschrift (Parameter basisplan in beiden Planern und evaluate)
API_VERSION = 2

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
        raw = g.get(f"shift_{s}_forbidden_next", "")
        # Leere CSV-Felder kommen als NaN an; str(NaN) waere "nan" und wuerde
        # als Schicht-ID missverstanden.
        forb = "" if raw is None or pd.isna(raw) else str(raw)
        shifts[s] = {
            "start": _parse_time(g[f"shift_{s}_start"]),
            "end": _parse_time(g[f"shift_{s}_end"]),
            "net": int(g[f"shift_{s}_net_min"]),
            "forbidden_next": [x for x in forb.split("|") if x in SHIFT_IDS],
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


def _as_assignments(plan) -> dict[tuple[str, date], str]:
    # Bewusst ueber das Attribut statt ueber isinstance: Wird das Modul zur
    # Laufzeit neu geladen (Streamlit), stammen zwischengespeicherte Plaene
    # noch von der alten Klasse PlanResult.
    if plan is None:
        return {}
    return dict(getattr(plan, "assignments", plan))


def krankheitsgutschrift(ctx: Context, scenario: str,
                         manual_absences: set[tuple[str, date]] | None = None,
                         basisplan=None) -> dict[str, int]:
    """
    Zeitgutschrift fuer krankheitsbedingt ausgefallene Dienste, in Minuten je
    Person.

    Rechtsgrundlage ist das Entgeltausfallprinzip (§ 4 Abs. 1 EFZG): Wer
    arbeitsunfaehig ist, wird so gestellt, als haette er gearbeitet. Das BAG
    hat bestaetigt, dass dafuer eine Zeitgutschrift auf dem Arbeitszeitkonto
    verlangt werden kann (BAG, 05.10.2023 - 6 AZR 210/22). Nacharbeiten muss
    niemand.

    Gutgeschrieben wird der Dienst, den die Person laut **Ausgangsplan** an
    diesem Tag gehabt haette - das ist der Dienstplan, der zum Zeitpunkt der
    Krankmeldung gilt. Ein Ausfall an einem dienstfreien Tag ergibt keine
    Gutschrift, weil keine Arbeitsleistung ausgefallen ist.

    Ohne diese Gutschrift hielte das Modell eine kranke Person fuer
    unterausgelastet: Das MILP liesse sie ihre Dienste an anderen Tagen
    nacharbeiten, die Heuristik zoege sie als Ersatz vor, und die Kennzahl
    "Spanne der Auslastung" mass unter S1/S2 teilweise Krankheit statt
    Planungsqualitaet.
    """
    ref = _as_assignments(basisplan)
    if not ref:
        return {}
    krank = scenario_absences(ctx, scenario) | set(manual_absences or set())
    gutschrift: dict[str, int] = {}
    for (e, d) in krank:
        s = ref.get((e, d))
        if s and (e, d) not in ctx.unavailable:
            gutschrift[e] = gutschrift.get(e, 0) + int(ctx.shifts[s]["net"])
    return gutschrift


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
    info: dict = field(default_factory=dict)

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
                fixed: dict[tuple[str, date], str] | None = None,
                soft_night: bool = True,
                basisplan=None) -> PlanResult:
    """
    Regelbasierte Referenzplanung. Entspricht dem Vorgehen einer manuellen
    Excel-Planung: Tag fuer Tag, Schicht fuer Schicht, jeweils die Person mit
    der geringsten bisherigen Auslastung, die alle harten Regeln erfuellt.

    `fixed` haelt bereits getroffene Zuweisungen fest und ist die Grundlage der
    reaktiven Umplanung (Schritt 3): nur die von einem Ausfall betroffenen
    Slots werden neu besetzt, der Rest des Plans bleibt stehen.

    `basisplan` ist der Dienstplan, der bei der Krankmeldung gilt; aus ihm
    wird die Krankheitsgutschrift berechnet. Ohne Angabe gilt `fixed` als
    Basisplan.
    """
    t0 = time.perf_counter()
    manual = set(manual_absences or set())
    fixed = dict(fixed or {})
    blocked = ctx.unavailable | scenario_absences(ctx, scenario) | manual
    gutschrift = krankheitsgutschrift(ctx, scenario, manual,
                                      basisplan if basisplan is not None else fixed)

    min_rest = float(ctx.rules.get("rule_min_rest_h", 11))
    st = ctx.staff
    cap_eff = effective_capacity(ctx)

    last_end: dict[str, datetime] = {}
    consec: dict[str, int] = {e: 0 for e in st.index}
    # Gutgeschriebene Krankheitszeit zaehlt wie gearbeitete Zeit. Die Heuristik
    # arbeitet Tag fuer Tag; die Gutschrift wird deshalb an dem Tag verbucht,
    # an dem der Ausfall liegt - so wie sie auch auf dem Arbeitszeitkonto
    # auflaeuft. Fuer die Obergrenze wird die noch ausstehende Gutschrift
    # vorab reserviert, damit am Monatsende Ist plus Gutschrift die
    # Vertragsgrenze nicht uebersteigt.
    worked: dict[str, int] = {e: 0 for e in st.index}
    gut_offen: dict[str, int] = {e: gutschrift.get(e, 0) for e in st.index}
    basis = _as_assignments(basisplan if basisplan is not None else fixed)
    krank_tage = scenario_absences(ctx, scenario) | manual
    gut_je_tag: dict[date, list[tuple[str, int]]] = {}
    for (e, d) in krank_tage:
        s_b = basis.get((e, d))
        if s_b and (e, d) not in ctx.unavailable:
            gut_je_tag.setdefault(d, []).append((e, int(ctx.shifts[s_b]["net"])))
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

    def eligible(e: str, d: date, s: str, relax_night: bool = False) -> bool:
        row = st.loc[e]
        if (e, d) in blocked or (e, d) in assignments:
            return False
        if s == "N" and not int(row["night_eligible"]):
            return False
        if int(row["is_ward_lead"]) and s != "F":
            return False
        if consec[e] >= int(row["max_consecutive_shifts"]):
            return False
        # Der Nachtdienst-Richtwert ist eine weiche Vorgabe ([ANNAHME] A10), keine
        # gesetzliche Grenze - evaluate() zaehlt seine Ueberschreitung als weiche
        # Abweichung. Die Heuristik darf ihn deshalb ueberschreiten, wenn sonst ein
        # Dienst unbesetzt bliebe. Ohne diese Moeglichkeit waere die Baseline
        # kuenstlich schwaecher als das MILP, das denselben Richtwert weich
        # modelliert - der Verfahrensvergleich waere dann nicht fair.
        if s == "N" and not relax_night and nights[e] >= int(row["max_night_shifts"]):
            return False
        if (worked[e] + gut_offen[e] + ctx.shifts[s]["net"]
                > int(row["max_total_minutes"])):
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
        # Krankheitsgutschrift des Tages verbuchen
        for e, minuten in gut_je_tag.get(d, []):
            worked[e] += minuten
            gut_offen[e] -= minuten

        # Fixierte Zuweisungen zuerst uebernehmen - aber nur, wenn sie im
        # aktuellen Zustand regelkonform sind. Ungeprueftes Uebernehmen war ein
        # Fehler: faellt jemand aus und wird die Luecke neu besetzt, kann die
        # Ersatzzuweisung mit einer fixierten Zuweisung am Folgetag die
        # Ruhezeit verletzen. Nicht uebernehmbare Dienste werden freigegeben
        # und weiter unten regulaer neu besetzt.
        for (e, dd), s in fixed.items():
            if dd == d and (e, d) not in assignments and eligible(e, d, s):
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
                if pick is None and soft_night and s == "N":
                    # Zweiter Versuch: Richtwert fuer Nachtdienste zuruecknehmen,
                    # bevor der Dienst unbesetzt bleibt.
                    relaxed = sorted(
                        (e for e in st.index
                         if int(st.loc[e, "ppug_countable"]) == 1
                         and e not in placed
                         and eligible(e, d, s, relax_night=True)),
                        key=lambda e: score(e, d))
                    for e in relaxed:
                        is_fach = st.loc[e, "ppug_category"] == "Pflegefachkraft"
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
                      runtime_s=time.perf_counter() - t0,
                      info={"gutschrift_min": gutschrift})


# --------------------------------------------------------------------------
# Optimierungsbasierter Planer: gemischt-ganzzahliges Modell (MILP)
# --------------------------------------------------------------------------
#
# Methodenwahl (siehe DATENKONZEPT / Hausarbeit): Das Problem ist eine
# Zuordnung von Personen zu Diensten unter harten Regeln mit mehreren
# konkurrierenden Zielen. Es gibt keine zu lernende Zielvariable und keine
# historischen Planentscheidungen als Trainingsdaten - Machine Learning hat
# hier keinen Ansatzpunkt. Mathematische Optimierung und Constraint
# Programming sind die einschlaegigen Verfahren (Burke et al. 2004;
# Van den Bergh et al. 2013). Umgesetzt ist ein MILP, gelöst mit HiGHS über
# scipy.optimize.milp - im Gegensatz zur Greedy-Heuristik betrachtet es alle
# 28 Tage gleichzeitig statt Tag fuer Tag.
#
# Alle Besetzungsziele sind weich modelliert (Strafterme), alle rechtlichen
# und vertraglichen Grenzen hart. Dadurch ist das Modell immer loesbar: im
# schlimmsten Fall liefert es einen Plan mit ausgewiesenen Luecken statt gar
# keinen Plan.

WEIGHTS = {
    "ppug": 10000.0,   # je Kraft unter der gesetzlichen Untergrenze (PpUGV)
    "under": 1000.0,   # je Kraft unter der fachlichen Sollbesetzung
    "over": 20.0,      # je Kraft ueber der Sollbesetzung
    "fair": 0.02,      # je Minute Abweichung von der Zielarbeitszeit
    "wish": 5.0,       # je Gewichtspunkt eines nicht erfuellten Dienstwunsches
    "night": 30.0,     # je Nachtdienst ueber dem Richtwert
    "weekend": 30.0,   # je Wochenende ueber dem Richtwert
    "azubi": 10.0,     # Anreiz, Ausbildungsplaetze tatsaechlich zu besetzen
    "keep": 200.0,     # je beibehaltener Zuweisung bei reaktiver Umplanung
}


def plan_milp(ctx: Context, scenario: str,
              manual_absences: set[tuple[str, date]] | None = None,
              fixed: dict[tuple[str, date], str] | None = None,
              reference: "PlanResult | None" = None,
              time_limit_s: float = 60.0, mip_gap: float = 0.01,
              weights: dict | None = None,
              basisplan=None) -> PlanResult:
    """
    Optimierungsbasierte Planung ueber den gesamten Horizont.

    `reference` schaltet die reaktive Umplanung ein: beibehaltene Zuweisungen
    werden belohnt, sodass der Optimierer den bestehenden Plan nur dort
    aufbricht, wo es sich lohnt (Planstabilitaet als Zielgroesse statt als
    Zufallsprodukt). `fixed` haelt Zuweisungen zusaetzlich hart fest.

    `basisplan` ist der Dienstplan, der bei der Krankmeldung gilt; aus ihm
    wird die Krankheitsgutschrift berechnet. Ohne Angabe gilt `reference`
    als Basisplan.
    """
    import numpy as np
    import scipy.sparse as sp
    from scipy.optimize import Bounds, LinearConstraint, milp

    t0 = time.perf_counter()
    W = {**WEIGHTS, **(weights or {})}
    manual = set(manual_absences or set())
    blocked = ctx.unavailable | scenario_absences(ctx, scenario) | manual
    gutschrift = krankheitsgutschrift(ctx, scenario, manual,
                                      basisplan if basisplan is not None else reference)
    st, days, dates = ctx.staff, ctx.days, ctx.plan_dates
    net = {s: ctx.shifts[s]["net"] for s in SHIFT_IDS}
    cap_eff = effective_capacity(ctx)

    countable = [e for e in st.index if int(st.loc[e, "ppug_countable"]) == 1]
    helpers = [e for e in countable if st.loc[e, "ppug_category"] == "Pflegehilfskraft"]
    fachkraefte = [e for e in countable if st.loc[e, "ppug_category"] == "Pflegefachkraft"]
    azubis = [e for e in st.index if st.loc[e, "role_group"] == "Auszubildende"]

    # ---- Variablen indizieren -------------------------------------------
    idx: dict = {}

    def var(key) -> int:
        if key not in idx:
            idx[key] = len(idx)
        return idx[key]

    for e in st.index:
        for d in dates:
            for s in SHIFT_IDS:
                var(("x", e, d, s))
    for d in dates:
        for s in SHIFT_IDS:
            var(("under", d, s))
            var(("ppug", d, s))
            var(("fach", d, s))
            var(("over", d, s))
    weekend_keys = sorted({d.isocalendar()[1] for d in dates if d.weekday() >= 5})
    for e in st.index:
        var(("dev", e))
        var(("nslack", e))
        var(("wslack", e))
        for k in weekend_keys:
            var(("wk", e, k))
    n = len(idx)

    lb = np.zeros(n)
    ub = np.ones(n)
    integrality = np.ones(n)
    c = np.zeros(n)

    # ---- Zielarbeitszeit je Person (Fairness) ---------------------------
    # Gutgeschriebene Krankheitszeit zaehlt wie gearbeitete Zeit. Die Summe
    # aus Ist und Gutschrift ist deshalb Bedarf plus Gutschrift - daraus
    # ergibt sich die gleichmaessige Auslastung, an der sich jede Person misst.
    demand_min = sum(int(days.loc[d, f"required_{s}"]) * net[s]
                     for d in dates for s in SHIFT_IDS)
    cap_total = sum(cap_eff[e] for e in countable) or 1.0
    credit_total = sum(gutschrift.get(e, 0) for e in countable)
    load = (demand_min + credit_total) / cap_total
    target = {e: cap_eff[e] * load for e in countable}

    # ---- Schranken und Zielkoeffizienten --------------------------------
    for e in st.index:
        row = st.loc[e]
        for d in dates:
            for s in SHIFT_IDS:
                j = idx[("x", e, d, s)]
                allowed = ((e, d) not in blocked
                           and not (s == "N" and not int(row["night_eligible"]))
                           and not (int(row["is_ward_lead"]) and s != "F"))
                if not allowed:
                    ub[j] = 0.0
                if e in azubis:
                    c[j] -= W["azubi"]
    for d in dates:
        for s in SHIFT_IDS:
            need = int(days.loc[d, f"required_{s}"])
            ub[idx[("under", d, s)]] = need
            ub[idx[("ppug", d, s)]] = int(days.loc[d, f"ppug_min_{s}"])
            ub[idx[("fach", d, s)]] = int(days.loc[d, f"min_fachkraft_{s}"])
            ub[idx[("over", d, s)]] = 4
            c[idx[("under", d, s)]] = W["under"]
            c[idx[("ppug", d, s)]] = W["ppug"]
            c[idx[("fach", d, s)]] = W["ppug"]
            c[idx[("over", d, s)]] = W["over"]
    for e in st.index:
        j = idx[("dev", e)]
        ub[j], integrality[j] = np.inf, 0
        c[j] = W["fair"] if e in countable else 0.0
        jn = idx[("nslack", e)]
        ub[jn], c[jn] = len(dates), W["night"]
        jw = idx[("wslack", e)]
        ub[jw], c[jw] = len(weekend_keys), W["weekend"]

    # Dienstwuensche (weiche Nebenbedingung, analog INRC-II S4)
    plan_rows = ctx.df[ctx.df["period"] == "plan"]
    for r in plan_rows.itertuples():
        w_off = getattr(r, "request_off_weight", None)
        if pd.notna(w_off) and w_off != "":
            for s in SHIFT_IDS:
                c[idx[("x", r.employee_id, r.date, s)]] += W["wish"] * float(w_off)
        w_on = getattr(r, "request_on_weight", None)
        s_on = str(getattr(r, "request_on_shift", "") or "")
        if pd.notna(w_on) and w_on != "" and s_on in SHIFT_IDS:
            c[idx[("x", r.employee_id, r.date, s_on)]] -= W["wish"] * float(w_on)

    # Reaktive Umplanung: Beibehalten belohnen
    if reference is not None:
        for (e, d), s in reference.assignments.items():
            if d in days.index and (e, d) not in blocked:
                c[idx[("x", e, d, s)]] -= W["keep"]

    # Harte Fixierungen
    for (e, d), s in (fixed or {}).items():
        if d in days.index and (e, d) not in blocked:
            lb[idx[("x", e, d, s)]] = 1.0

    # ---- Nebenbedingungen ------------------------------------------------
    rows: list[int] = []
    cols: list[int] = []
    vals: list[float] = []
    rlb: list[float] = []
    rub: list[float] = []
    r = 0

    def add_row(terms, low, high):
        nonlocal r
        for j, v in terms:
            rows.append(r)
            cols.append(j)
            vals.append(v)
        rlb.append(low)
        rub.append(high)
        r += 1

    # (1) hoechstens ein Dienst je Person und Tag
    for e in st.index:
        for d in dates:
            add_row([(idx[("x", e, d, s)], 1.0) for s in SHIFT_IDS], -np.inf, 1.0)

    for d in dates:
        for s in SHIFT_IDS:
            crew = [(idx[("x", e, d, s)], 1.0) for e in countable]
            need = int(days.loc[d, f"required_{s}"])
            # (2) Besetzung = Soll - Unterbesetzung + Ueberbesetzung
            add_row(crew + [(idx[("under", d, s)], 1.0), (idx[("over", d, s)], -1.0)],
                    need, need)
            # (3) gesetzliche Untergrenze (weich, aber sehr hoch bestraft)
            add_row(crew + [(idx[("ppug", d, s)], 1.0)],
                    int(days.loc[d, f"ppug_min_{s}"]), np.inf)
            # (4) Hoechstanteil Pflegehilfskraefte
            if helpers:
                add_row([(idx[("x", e, d, s)], 1.0) for e in helpers],
                        -np.inf, int(days.loc[d, f"max_hilfskraft_{s}"]))
            # (4b) Mindestzahl Pflegefachkraefte. Ergibt sich rechnerisch schon
            # aus (4), wird aber explizit modelliert, damit das Modell genau
            # das erzwingt, was evaluate() spaeter prueft - sonst kann eine
            # gleichwertige Optimalloesung die Pruefung reissen.
            if fachkraefte:
                add_row([(idx[("x", e, d, s)], 1.0) for e in fachkraefte]
                        + [(idx[("fach", d, s)], 1.0)],
                        int(days.loc[d, f"min_fachkraft_{s}"]), np.inf)
            # (5) Ausbildungsplaetze
            if azubis:
                add_row([(idx[("x", e, d, s)], 1.0) for e in azubis],
                        -np.inf, int(days.loc[d, f"azubi_slots_{s}"]))

    for e in st.index:
        row = st.loc[e]
        # (6) unzulaessige Schichtfolgen (Ruhezeit, ArbZG § 5)
        for i in range(len(dates) - 1):
            for s1 in SHIFT_IDS:
                for s2 in ctx.shifts[s1]["forbidden_next"]:
                    add_row([(idx[("x", e, dates[i], s1)], 1.0),
                             (idx[("x", e, dates[i + 1], s2)], 1.0)], -np.inf, 1.0)
        # Anschluss an die Vorperiode
        last_hist = dates[0] - timedelta(days=1)
        s_prev = ctx.history.get((e, last_hist))
        if s_prev:
            for s2 in ctx.shifts[s_prev]["forbidden_next"]:
                ub[idx[("x", e, dates[0], s2)]] = 0.0

        # (7) maximale Dienstfolge, inkl. Auslaufen der Historie
        L = int(row["max_consecutive_shifts"]) + 1
        timeline = [(("hist", d) if d < dates[0] else ("plan", d))
                    for d in ctx.hist_dates + dates]
        for start in range(len(timeline) - L + 1):
            window = timeline[start:start + L]
            if not any(kind == "plan" for kind, _ in window):
                continue
            const = sum(1 for kind, d in window
                        if kind == "hist" and (e, d) in ctx.history)
            terms = [(idx[("x", e, d, s)], 1.0)
                     for kind, d in window if kind == "plan" for s in SHIFT_IDS]
            add_row(terms, -np.inf, float(L - 1 - const))

        # (8) vertragliche Hoechstarbeitszeit im Horizont; gutgeschriebene
        # Krankheitszeit zaehlt mit (Arbeitszeitkonto, nicht ArbZG)
        add_row([(idx[("x", e, d, s)], float(net[s])) for d in dates for s in SHIFT_IDS],
                -np.inf, float(row["max_total_minutes"]) - gutschrift.get(e, 0))

        # (9) Nachtdienste (weicher Richtwert)
        add_row([(idx[("x", e, d, "N")], 1.0) for d in dates]
                + [(idx[("nslack", e)], -1.0)], -np.inf, float(row["max_night_shifts"]))

        # (10) Wochenenden (weicher Richtwert)
        for k in weekend_keys:
            for d in dates:
                if d.weekday() >= 5 and d.isocalendar()[1] == k:
                    for s in SHIFT_IDS:
                        add_row([(idx[("x", e, d, s)], 1.0), (idx[("wk", e, k)], -1.0)],
                                -np.inf, 0.0)
        add_row([(idx[("wk", e, k)], 1.0) for k in weekend_keys]
                + [(idx[("wslack", e)], -1.0)], -np.inf, float(row["max_weekends"]))

        # (11) Fairness: Betrag der Abweichung von der Zielarbeitszeit
        if e in countable:
            work = [(idx[("x", e, d, s)], float(net[s])) for d in dates for s in SHIFT_IDS]
            ziel = target[e] - gutschrift.get(e, 0)
            add_row(work + [(idx[("dev", e)], -1.0)], -np.inf, ziel)
            add_row(work + [(idx[("dev", e)], 1.0)], ziel, np.inf)

    A = sp.coo_array((vals, (rows, cols)), shape=(r, n)).tocsr()
    res = milp(c=c, constraints=[LinearConstraint(A, np.array(rlb), np.array(rub))],
               integrality=integrality, bounds=Bounds(lb, ub),
               options={"time_limit": time_limit_s, "mip_rel_gap": mip_gap,
                        "presolve": True, "disp": False})

    assignments: dict[tuple[str, date], str] = {}
    open_slots: list[dict] = []
    info = {"status": int(res.status), "message": str(res.message),
            "variablen": n, "nebenbedingungen": r,
            "gutschrift_min": gutschrift,
            "zielfunktionswert": float(res.fun) if res.x is not None else None,
            "mip_gap": float(getattr(res, "mip_gap", float("nan")))}
    if res.x is not None:
        x = np.asarray(res.x)
        for e in st.index:
            for d in dates:
                for s in SHIFT_IDS:
                    if x[idx[("x", e, d, s)]] > 0.5:
                        assignments[(e, d)] = s
        for d in dates:
            for s in SHIFT_IDS:
                miss = int(round(x[idx[("under", d, s)]]))
                for k in range(miss):
                    open_slots.append({"date": d, "shift_id": s, "slot": k + 1,
                                       "reason": "im Optimum nicht besetzbar"})

    return PlanResult(method="MILP-Optimierung (HiGHS)", scenario=scenario,
                      assignments=assignments, open_slots=open_slots,
                      runtime_s=time.perf_counter() - t0, info=info)


# --------------------------------------------------------------------------
# Unabhaengige Bewertung
# --------------------------------------------------------------------------

def evaluate(ctx: Context, result: PlanResult, basisplan=None,
             manual_absences: set[tuple[str, date]] | None = None) -> dict:
    """
    Prueft den fertigen Plan gegen die Regeln aus dem Datensatz.

    `basisplan` ist der Dienstplan, der bei den Krankmeldungen galt. Aus ihm
    berechnet die Pruefung die Krankheitsgutschrift selbst - unabhaengig vom
    Planer, der sie nicht selbst behaupten darf. Ohne Basisplan (Szenario S0
    oder reine Erstplanung) gibt es keine Gutschrift.
    """
    st = ctx.staff
    a = result.assignments
    gutschrift = krankheitsgutschrift(ctx, result.scenario, manual_absences, basisplan)
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
        minutes = sum(ctx.shifts[s]["net"] for _, s in own) + gutschrift.get(e, 0)
        if minutes > int(st.loc[e, "max_total_minutes"]):
            hours_v += 1
            add("Arbeitszeit", f"{e}: {minutes / 60:.1f} h ueber Vertragsobergrenze "
                               f"(inkl. Krankheitsgutschrift)", mitarbeiter=e)
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
    # Sollzeit (siehe effective_capacity). Gutgeschriebene Krankheitszeit
    # zaehlt wie gearbeitete Zeit (Entgeltausfallprinzip) - sonst erschiene
    # eine kranke Person als unterausgelastet.
    dev, hours_detail, rel_load = [], [], []
    cap_eff = effective_capacity(ctx)
    for e in countable_ids:
        gearbeitet = sum(ctx.shifts[s]["net"] for (emp, _), s in a.items() if emp == e)
        gut = gutschrift.get(e, 0)
        minutes = gearbeitet + gut
        soll = cap_eff[e]
        if soll > 0:
            dev.append(abs(minutes - soll) / soll)
            rel_load.append(minutes / soll)
            hours_detail.append({"employee_id": e, "ist_min": gearbeitet,
                                 "gutschrift_min": gut,
                                 "soll_min": round(soll),
                                 "abweichung_min": round(minutes - soll),
                                 "abweichung_pct": round((minutes - soll) / soll * 100, 1)})

    # Lastverteilung: wie gleichmaessig ist die Auslastung ueber die Belegschaft?
    # Die mittlere Abweichung oben misst das Niveau (der Bedarf liegt unter der
    # Kapazitaet), die Streuung hier misst die Verteilungsgerechtigkeit - erst
    # sie unterscheidet zwei Plaene mit gleicher Besetzungsquote.
    if rel_load:
        mean_load = sum(rel_load) / len(rel_load)
        var = sum((v - mean_load) ** 2 for v in rel_load) / len(rel_load)
        load_stats = {"auslastung_mittel": mean_load,
                      "auslastung_streuung": var ** 0.5,
                      "auslastung_min": min(rel_load),
                      "auslastung_max": max(rel_load),
                      "auslastung_spanne": max(rel_load) - min(rel_load)}
    else:
        load_stats = {"auslastung_mittel": 0.0, "auslastung_streuung": 0.0,
                      "auslastung_min": 0.0, "auslastung_max": 0.0,
                      "auslastung_spanne": 0.0}

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
        "krankheitsgutschrift_min": sum(gutschrift.values()),
        **load_stats,
        "planungszeit_s": result.runtime_s,
        "verfahren": result.method,
        "verstoesse": viol,
    }


def stability(reference: PlanResult, current: PlanResult) -> dict:
    """Planstabilitaet: wie stark weicht der angepasste Plan vom Ausgangsplan ab?"""
    # Bezugsgroesse ist die Vereinigung beider Plaene: nur so bleibt das Mass
    # zwischen 0 und 1, auch wenn der neue Plan andere Personen einsetzt als
    # der alte. Gezaehlt wird je (Person, Tag) - ein verschobener Dienst ist
    # eine Aenderung, ein unveraenderter Dienst ist Stabilitaet.
    keys = set(reference.assignments) | set(current.assignments)
    changed = sum(1 for k in keys
                  if reference.assignments.get(k) != current.assignments.get(k))
    base = max(len(keys), 1)
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
