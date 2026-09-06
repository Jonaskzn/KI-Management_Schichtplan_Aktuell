#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CarePlan - Prototyp zur KI-gestuetzten Personal- und Schichtplanung in der Pflege.

Diese Datei ist reine Oberflaeche. Die gesamte Planungs- und Bewertungslogik
liegt in planner.py und ist dort ohne laufende App testbar (test_planner.py).

Datengrundlage ist schichtplan_datensatz.csv: Stammdaten, Belegung, Bedarf,
Historie, Wuensche, Ausfallszenarien und das Regelwerk. Im Code stehen keine
Grenzwerte - Ruhezeit, Hoechstarbeitszeit, Verhaeltniszahlen und
Qualifikationsvorgaben kommen aus dem Datensatz.

Es werden keine personenbezogenen und keine Gesundheitsdaten verarbeitet:
Mitarbeitende sind pseudonyme IDs, Ausfaelle reine Verfuegbarkeitsereignisse.
"""

from __future__ import annotations

import io
import os
from datetime import date

import pandas as pd
import streamlit as st

import planner as P

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "schichtplan_datensatz.csv")
REFERENCE_SCENARIO = "S0 - keine kurzfristigen Ausfaelle"

st.set_page_config(page_title="CarePlan | Schichtplanung", page_icon="+", layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root { --ink:#16202a; --muted:#60707c; --teal:#087f7b; --mint:#dff4ed; --coral:#e76f51; --line:#dce5e5; }
html, body, [class*="css"] { font-family:'DM Sans', sans-serif; color:var(--ink); }
h1, h2, h3 { font-family:'Space Grotesk', sans-serif; letter-spacing:0; }
.hero { padding:1.5rem 0 .8rem; border-bottom:1px solid var(--line); margin-bottom:1.2rem; }
.eyebrow { color:var(--teal); text-transform:uppercase; font-size:.72rem; font-weight:700; letter-spacing:.12em; }
.hero h1 { font-size:2.25rem; margin:.25rem 0 .3rem; }
.hero p { color:var(--muted); margin:0; font-size:1rem; }
.metric { background:#f3f8f6; border-left:4px solid var(--teal); padding:.8rem 1rem; min-height:96px; }
.metric strong { display:block; font-family:'Space Grotesk'; font-size:1.75rem; }
.metric span { color:var(--muted); font-size:.8rem; }
.metric.warn { background:#fff5ed; border-left-color:var(--coral); }
.notice { background:#fff5ed; border-left:4px solid var(--coral); padding:.7rem .9rem; margin:.35rem 0; color:#713b2b; }
.source { color:var(--muted); font-size:.78rem; }
</style>""", unsafe_allow_html=True)

st.markdown('<div class="hero"><div class="eyebrow">CarePlan / Prototyp 02</div>'
            '<h1>Schichtplanung, die mitdenkt.</h1>'
            '<p>28-Tage-Planung auf Basis von Belegung, Qualifikation und Arbeitszeitrecht '
            '&ndash; mit messbarer Reaktion auf kurzfristige Ausf&auml;lle.</p></div>',
            unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Daten laden
# --------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_bytes(payload: bytes) -> pd.DataFrame:
    return P.load_dataset(io.BytesIO(payload))


with st.sidebar:
    st.markdown("### Datengrundlage")
    upload = st.file_uploader(
        "Eigenen Datensatz verwenden (CSV)", type="csv",
        help="Optional. Ohne Upload wird schichtplan_datensatz.csv aus dem "
             "Repository geladen - so ist jeder Lauf reproduzierbar.")

try:
    if upload is not None:
        df = load_bytes(upload.getvalue())
        source_label = f"Upload: {upload.name}"
    elif os.path.exists(DATA_FILE):
        with open(DATA_FILE, "rb") as fh:
            df = load_bytes(fh.read())
        source_label = os.path.basename(DATA_FILE)
    else:
        st.error("schichtplan_datensatz.csv wurde nicht gefunden. "
                 "Datei ins Repository legen oder oben hochladen.")
        st.stop()
    ctx = P.build_context(df)
except P.DatasetError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:                                   # noqa: BLE001
    st.error(f"Der Datensatz konnte nicht gelesen werden: {exc}")
    st.stop()


# --------------------------------------------------------------------------
# Steuerung
# --------------------------------------------------------------------------

if "manual" not in st.session_state:
    st.session_state.manual = set()

with st.sidebar:
    st.caption(f"Quelle: {source_label} &middot; Version "
               f"{ctx.ward.get('dataset_version', '?')} &middot; Seed "
               f"{ctx.ward.get('seed', '?')}", unsafe_allow_html=True)

    st.markdown("### Planung")
    scenario = st.selectbox(
        "Ausfallszenario", list(P.SCENARIOS),
        help="Anonymisierte Verfuegbarkeitsereignisse aus dem Datensatz. "
             "Es werden keine Gesundheitsdaten verarbeitet.")
    reactive = st.toggle(
        "Reaktiv umplanen", value=True,
        help="An: der Referenzplan wird festgehalten, nur betroffene Dienste "
             "werden neu besetzt (Planstabilitaet). Aus: der Plan wird "
             "vollstaendig neu gerechnet.")

    st.markdown("### Zusaetzlicher Ausfall")
    emp = st.selectbox("Mitarbeitende", list(ctx.staff.index),
                       format_func=lambda e: f"{e} ({ctx.staff.loc[e, 'role']})")
    day = st.selectbox("Tag", ctx.plan_dates, format_func=lambda d: d.strftime("%a, %d.%m.%Y"))
    duration = st.slider("Dauer in Tagen", 1, 7, 1)
    c1, c2 = st.columns(2)
    if c1.button("Ausfall melden", use_container_width=True):
        for offset in range(duration):
            idx = ctx.plan_dates.index(day) + offset
            if idx < len(ctx.plan_dates):
                st.session_state.manual.add((emp, ctx.plan_dates[idx].isoformat()))
        st.rerun()
    if c2.button("Zuruecksetzen", use_container_width=True):
        st.session_state.manual = set()
        st.rerun()
    if st.session_state.manual:
        st.caption(f"{len(st.session_state.manual)} manuelle Ausfalltage aktiv")

manual = {(e, date.fromisoformat(d)) for e, d in st.session_state.manual}

# Referenzplan ohne kurzfristige Ausfaelle - Bezugspunkt fuer die Stabilitaet
reference = P.plan_greedy(ctx, REFERENCE_SCENARIO)
fixed = reference.assignments if reactive else None
current = P.plan_greedy(ctx, scenario, manual_absences=manual, fixed=fixed)

kpi = P.evaluate(ctx, current)
kpi_ref = P.evaluate(ctx, reference)
stab = P.stability(reference, current)
is_reference = (scenario == REFERENCE_SCENARIO and not manual)


# --------------------------------------------------------------------------
# Kennzahlen
# --------------------------------------------------------------------------

def metric(col, value, label, warn=False):
    col.markdown(f'<div class="metric{" warn" if warn else ""}"><strong>{value}</strong>'
                 f'<span>{label}</span></div>', unsafe_allow_html=True)


cols = st.columns(6)
metric(cols[0], f"{kpi['besetzungsquote']:.0%}", "Besetzungsquote")
metric(cols[1], kpi["offene_slots"], "offene Dienste", warn=kpi["offene_slots"] > 0)
metric(cols[2], kpi["untergrenzen_verstoesse"], "Untergrenze (PpUGV)",
       warn=kpi["untergrenzen_verstoesse"] > 0)
metric(cols[3], kpi["harte_verstoesse"], "harte Regelverstoesse",
       warn=kpi["harte_verstoesse"] > 0)
metric(cols[4], f"{kpi['arbeitszeitabweichung']:.0%}", "Arbeitszeitabweichung")
metric(cols[5], "Referenz" if is_reference else f"{stab['planstabilitaet']:.0%}",
       "Planstabilitaet", warn=not is_reference and stab["planstabilitaet"] < 0.8)

st.caption(f"Verfahren: {current.method} &middot; Planungszeit "
           f"{kpi['planungszeit_s']:.2f} s &middot; {len(ctx.plan_dates)} Tage &middot; "
           f"{kpi['soll_dienste']} Soll-Dienste &middot; "
           f"{'reaktive Umplanung' if reactive else 'vollstaendige Neuplanung'}",
           unsafe_allow_html=True)

if not is_reference:
    st.info(f"Gegenueber dem Referenzplan wurden **{stab['geaenderte_zuweisungen']} "
            f"Zuweisungen** geaendert. Je niedriger dieser Wert bei gleicher "
            f"Besetzungsquote, desto stabiler der Plan fuer die Mitarbeitenden.")

tabs = st.tabs(["Dienstplan", "Bedarf & Besetzung", "Pruefhinweise",
                "Arbeitszeit", "Mitarbeitende", "Daten & Regeln"])


# --------------------------------------------------------------------------
with tabs[0]:
    left, right = st.columns([3, 1])
    left.markdown("**Dienstplan** &nbsp; F = Fruehdienst, S = Spaetdienst, "
                  "N = Nachtdienst, &ndash; = geplante Abwesenheit",
                  unsafe_allow_html=True)
    export = P.export_frame(ctx, current)
    right.download_button("Plan als CSV", export.to_csv(index=False).encode("utf-8"),
                          "schichtplan_ergebnis.csv", "text/csv",
                          use_container_width=True)

    matrix = current.matrix(ctx)
    colors = {"F": "#dff4ed", "S": "#fdf3e3", "N": "#e6e9f5", "–": "#f2f2f2"}
    try:
        styled = matrix.style.map(lambda v: f"background-color: {colors.get(v, '')}")
        st.dataframe(styled, use_container_width=True, height=760)
    except Exception:                                       # noqa: BLE001
        st.dataframe(matrix, use_container_width=True, height=760)
    st.caption("Der Export enthaelt den vollstaendigen Eingabedatensatz plus die "
               "Spalte assigned_shift - ein Artefakt fuer die spaetere Auswertung.")


# --------------------------------------------------------------------------
with tabs[1]:
    rows = []
    for d in ctx.plan_dates:
        day = ctx.days.loc[d]
        for s in P.SHIFT_IDS:
            crew = [e for (e, dd), sh in current.assignments.items() if dd == d and sh == s]
            countable = [e for e in crew
                         if int(ctx.staff.loc[e, "ppug_countable"]) == 1]
            fach = [e for e in countable
                    if ctx.staff.loc[e, "ppug_category"] == "Pflegefachkraft"]
            rows.append({
                "Datum": d.strftime("%a %d.%m."),
                "Schicht": s,
                "Patienten": int(day["census_1200" if s != "N" else "census_0000"]),
                "Untergrenze": int(day[f"ppug_min_{s}"]),
                "Soll": int(day[f"required_{s}"]),
                "Besetzt": len(countable),
                "davon Fachkraft": len(fach),
                "Azubis": len(crew) - len(countable),
                "Delta": len(countable) - int(day[f"required_{s}"]),
            })
    cover = pd.DataFrame(rows)
    st.dataframe(cover, use_container_width=True, hide_index=True, height=520)
    st.markdown("**Besetzung je Tag** (Summe ueber alle drei Schichten)")
    per_day = cover.groupby("Datum", sort=False)[["Soll", "Besetzt"]].sum()
    st.line_chart(per_day)
    st.caption("Untergrenze nach PpUGV § 6 (Tag 10:1, Nacht 22:1); Soll aus dem "
               "Pflegeaufwand nach PPR-2.0-Logik. Die Untergrenze ist eine harte "
               "Restriktion, das Soll eine Qualitaetskennzahl.")


# --------------------------------------------------------------------------
with tabs[2]:
    viol = kpi["verstoesse"]
    if not viol:
        st.success("Alle Dienste konnten unter den hinterlegten Regeln besetzt werden.")
    else:
        hard = [v for v in viol if "weich" not in v["art"]]
        soft = [v for v in viol if "weich" in v["art"]]
        st.markdown(f"**{len(hard)} harte Befunde**")
        for v in hard[:60]:
            st.markdown(f'<div class="notice"><strong>{v["art"]}</strong> &middot; '
                        f'{v["hinweis"]}</div>', unsafe_allow_html=True)
        if len(hard) > 60:
            st.caption(f"... und {len(hard) - 60} weitere")
        if soft:
            with st.expander(f"{len(soft)} weiche Abweichungen "
                             "(Wochenend- und Nachtdienstverteilung)"):
                for v in soft:
                    st.write(f"{v['art']}: {v['hinweis']}")
    if current.open_slots:
        st.markdown("**Nicht besetzbare Dienste**")
        st.dataframe(pd.DataFrame(current.open_slots), use_container_width=True,
                     hide_index=True)


# --------------------------------------------------------------------------
with tabs[3]:
    hours = pd.DataFrame(kpi["arbeitszeit_detail"])
    if not hours.empty:
        hours = hours.join(ctx.staff[["role", "employment_pct"]], on="employee_id")
        hours["Ist (h)"] = (hours["ist_min"] / 60).round(1)
        hours["Soll (h)"] = (hours["soll_min"] / 60).round(1)
        hours["Abweichung (h)"] = (hours["abweichung_min"] / 60).round(1)
        show = hours[["employee_id", "role", "employment_pct", "Ist (h)",
                      "Soll (h)", "Abweichung (h)", "abweichung_pct"]]
        show = show.rename(columns={"employee_id": "ID", "role": "Rolle",
                                    "employment_pct": "Umfang",
                                    "abweichung_pct": "Abweichung (%)"})
        st.dataframe(show.sort_values("Abweichung (%)"), use_container_width=True,
                     hide_index=True)
        st.bar_chart(hours.set_index("employee_id")["abweichung_pct"])
    st.caption("Soll = Vertragskapazitaet im Horizont, anteilig um geplante "
               "Abwesenheiten gekuerzt. Auszubildende sind nicht enthalten, da sie "
               "nach PpUGV § 2 nicht auf die Besetzung angerechnet werden.")
    st.markdown(f"Pflegehilfskraft-Anteil an den Diensten: "
                f"**{kpi['hilfskraftanteil']:.1%}** "
                f"(Grenze nach PpUGV: {kpi['hilfskraft_grenze']:.0%})")


# --------------------------------------------------------------------------
with tabs[4]:
    people = ctx.staff[["role", "role_group", "skills", "employment_pct",
                        "weekly_hours", "night_eligible", "ppug_category",
                        "max_night_shifts", "time_account_start_min"]].copy()
    people["Dienste im Plan"] = [
        sum(1 for (e, _), _s in current.assignments.items() if e == idx)
        for idx in people.index]
    absent_now = {e for (e, _) in (ctx.unavailable | P.scenario_absences(ctx, scenario)
                                   | manual)}
    people["Abwesenheit im Horizont"] = [
        sum(1 for d in ctx.plan_dates
            if (idx, d) in (ctx.unavailable | P.scenario_absences(ctx, scenario) | manual))
        for idx in people.index]
    st.dataframe(people, use_container_width=True, height=560)
    st.caption(f"{len(ctx.staff)} pseudonyme Mitarbeitende, davon "
               f"{len(absent_now)} mit Abwesenheitstagen im Szenario. "
               "Keine Klarnamen, keine Ausfallgruende, keine Gesundheitsdaten.")


# --------------------------------------------------------------------------
with tabs[5]:
    st.markdown("#### Station")
    st.table(pd.DataFrame([ctx.ward]).T.rename(columns={0: "Wert"}))

    st.markdown("#### Schichtarten")
    st.table(pd.DataFrame([
        {"Schicht": s,
         "Beginn": ctx.shifts[s]["start"].strftime("%H:%M"),
         "Ende": ctx.shifts[s]["end"].strftime("%H:%M"),
         "Nettominuten": ctx.shifts[s]["net"],
         "unzulaessige Folgeschicht": ", ".join(ctx.shifts[s]["forbidden_next"]) or "-"}
        for s in P.SHIFT_IDS]))

    st.markdown("#### Regelwerk aus dem Datensatz")
    st.table(pd.DataFrame([{"Parameter": k, "Wert": v} for k, v in ctx.rules.items()]))

    st.markdown("""
#### Rechtsgrundlagen

- **Ruhezeit:** mindestens 11 Stunden zwischen zwei Diensten (§ 5 Abs. 1 ArbZG).
  Daraus folgen die gesperrten Schichtfolgen Spaet&rarr;Frueh und Nacht&rarr;Frueh/Spaet.
- **Arbeitszeit:** werktaeglich 8 Stunden, auf 10 nur mit Ausgleich (§ 3 ArbZG);
  Pausen 30 bzw. 45 Minuten (§ 4 ArbZG); Nachtarbeit § 6 ArbZG.
- **Mindestbesetzung:** Verhaeltniszahlen und maximaler Pflegehilfskraftanteil
  nach § 6 PpUGV in Verbindung mit der Anlage.
- **Qualifikation:** Pflegekraft = Pflegefachkraft oder Pflegehilfskraft (§ 2 PpUGV).
  Auszubildende werden eingeplant, aber nicht auf die Untergrenze angerechnet.
- **Vertragsrahmen:** 38,5 Wochenstunden (§ 6 TVoeD-K), 30 Urlaubstage (§ 26 TVoeD-K).

#### Methodischer Hinweis

Der hier eingesetzte Planer ist eine **transparente Greedy-Heuristik** und dient als
regelbasierte Referenz (Baseline). Er ist ausdruecklich kein KI-Verfahren. Der
Vergleich mit einem optimierungsbasierten Ansatz ist der naechste Schritt; die
Schnittstelle in `planner.py` ist dafuer vorbereitet.

Die Bewertung in `evaluate()` prueft den fertigen Plan unabhaengig vom Planer nach.
Ein Verfahren darf seine eigene Regelkonformitaet nicht selbst behaupten.
""", unsafe_allow_html=True)
