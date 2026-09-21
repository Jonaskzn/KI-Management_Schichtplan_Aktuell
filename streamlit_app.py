#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CarePlan - Prototyp zur KI-gestuetzten Personal- und Schichtplanung in der Pflege.

Diese Datei ist reine Oberflaeche. Die gesamte Planungs- und Bewertungslogik
liegt in planner.py und ist dort ohne laufende App testbar (test_planner.py).

Zwei Verfahren stehen auf identischer Datengrundlage nebeneinander:
  - regelbasierte Greedy-Heuristik (Baseline, entspricht der Excel-Planung)
  - MILP-Optimierung ueber den gesamten Horizont (HiGHS via scipy)

Datengrundlage ist schichtplan_datensatz.csv. Im Code stehen keine Grenzwerte -
Ruhezeit, Hoechstarbeitszeit, Verhaeltniszahlen und Qualifikationsvorgaben
kommen aus dem Datensatz.

Es werden keine personenbezogenen und keine Gesundheitsdaten verarbeitet:
Mitarbeitende sind pseudonyme IDs, Ausfaelle reine Verfuegbarkeitsereignisse.
"""

from __future__ import annotations

import hashlib
import importlib
import io
import os
from datetime import date

import pandas as pd
import streamlit as st

import planner as P

# Streamlit Community Cloud laedt nach einem neuen Commit zwar streamlit_app.py
# neu, behaelt aber unter Umstaenden das bereits importierte Modul planner im
# Speicher. Dann trifft die neue Oberflaeche auf die alte Planungslogik - mit
# einem TypeError als Folge. Deshalb wird planner neu geladen, sobald sich der
# Inhalt der Datei geaendert hat. Der Stand (Pruefsumme) ist Teil jedes
# Cache-Schluessels - Plaene einer alten Planungslogik werden nie wiederverwendet.
_PLANNER_API = 2


def _planner_aktualisieren() -> None:
    with open(P.__file__, "rb") as fh:
        stand = hashlib.sha1(fh.read()).hexdigest()
    if getattr(P, "_geladener_stand", None) != stand:
        importlib.reload(P)
        P._geladener_stand = stand


HIER = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(HIER, "schichtplan_datensatz.csv")
REFERENCE_SCENARIO = "S0 - keine kurzfristigen Ausfaelle"
METHODS = {
    "Regelbasiert (Baseline)": "greedy",
    "MILP-Optimierung": "milp",
}

# Gewicht fuer Lastausgleich in der Zielfunktion (je Minute Abweichung von der
# Zielarbeitszeit). Der Standardwert 0,02 steht gegen keep = 200 je beibehaltener
# Zuweisung - Lastausgleich faellt damit praktisch nicht ins Gewicht. Der zweite
# Wert dreht die Priorisierung um. Wirkung quantifiziert in ERGEBNISSE.md 4.5.
PRIORITAETEN = {
    "Planungsruhe (Standard)": 0.02,
    "Ausgewogen": 0.1,
    "Verteilungsgerechtigkeit": 1.0,
}

st.set_page_config(page_title="CarePlan | Schichtplanung", page_icon="+", layout="wide")

_planner_aktualisieren()
if getattr(P, "API_VERSION", 0) < _PLANNER_API:
    st.error("Die Planungslogik (planner.py) ist aelter als die Oberflaeche "
             "(streamlit_app.py). Bitte beide Dateien aus demselben Stand ins "
             "Repository laden und die App ueber 'Manage app' -> 'Reboot app' "
             "neu starten.")
    st.stop()

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
</style>""", unsafe_allow_html=True)

st.markdown('<div class="hero"><div class="eyebrow">CarePlan / Prototyp 03</div>'
            '<h1>Schichtplanung, die mitdenkt.</h1>'
            '<p>28-Tage-Planung auf Basis von Belegung, Qualifikation und Arbeitszeitrecht '
            '&ndash; regelbasierte Planung und Optimierung im direkten Vergleich.</p></div>',
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
        payload = upload.getvalue()
        source_label = f"Upload: {upload.name}"
    elif os.path.exists(DATA_FILE):
        with open(DATA_FILE, "rb") as fh:
            payload = fh.read()
        source_label = os.path.basename(DATA_FILE)
    else:
        st.error("schichtplan_datensatz.csv wurde nicht gefunden. "
                 "Datei ins Repository legen oder oben hochladen.")
        st.stop()
    df = load_bytes(payload)
    data_key = hashlib.sha1(payload).hexdigest()[:12]
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
    st.caption(f"Station: {ctx.ward.get('ward_name', '?')} &middot; Quelle: "
               f"{source_label} &middot; Version "
               f"{ctx.ward.get('dataset_version', '?')} &middot; Seed "
               f"{ctx.ward.get('seed', '?')}", unsafe_allow_html=True)

    st.markdown("### Planung")
    method_label = st.selectbox(
        "Verfahren", list(METHODS),
        help="Baseline: transparente Regelheuristik, Tag fuer Tag - entspricht "
             "dem Vorgehen einer manuellen Excel-Planung. MILP: Optimierung "
             "ueber alle 28 Tage gleichzeitig.")
    method = METHODS[method_label]
    scenario = st.selectbox(
        "Ausfallszenario", list(P.SCENARIOS),
        help="Anonymisierte Verfuegbarkeitsereignisse aus dem Datensatz. "
             "Es werden keine Gesundheitsdaten verarbeitet.")
    reactive = st.toggle(
        "Reaktiv umplanen", value=True,
        help="An: der Referenzplan wird als Ausgangspunkt genutzt, Aenderungen "
             "werden minimiert (Planstabilitaet). Aus: der Plan wird "
             "vollstaendig neu gerechnet.")
    if method == "milp":
        prio_label = st.radio(
            "Priorität der Optimierung",
            list(PRIORITAETEN), index=0,
            help="Stellt das Gewicht fuer Lastausgleich in der Zielfunktion "
                 "(je Minute Abweichung von der Zielarbeitszeit, gegen 200 je "
                 "beibehaltener Zuweisung). "
                 "Planungsruhe (0,02): nur Luecken fuellen - hoechste "
                 "Planstabilitaet, eine geerbte Schieflage bleibt bestehen. "
                 "Ausgewogen (0,1): deutlich gleichmaessigere Auslastung bei "
                 "rund einem Prozentpunkt weniger Stabilitaet - im Mittel der beste "
                 "Kompromiss. Verteilungsgerechtigkeit (1,0): die Last wird im "
                 "ganzen Monat neu verteilt, dafuer mehr geaenderte Dienste. "
                 "Die Prioritaet wirkt auf die Anpassung bei Ausfaellen; der "
                 "Ausgangsplan ist fuer alle drei Stufen derselbe. "
                 "Gemessene Wirkung in ERGEBNISSE.md, Abschnitt 4.5.")
        prio = PRIORITAETEN[prio_label]
        time_limit = st.slider("Rechenzeit je Plan (Sekunden)", 5, 120, 30, step=5,
                               help="Abbruchgrenze fuer den Solver. Wird die "
                                    "Grenze erreicht, liefert er die beste bis "
                                    "dahin gefundene Loesung.")
    else:
        prio_label, prio = list(PRIORITAETEN)[0], PRIORITAETEN[list(PRIORITAETEN)[0]]
        time_limit = 30

    st.markdown("### Zusaetzlicher Ausfall")
    emp = st.selectbox("Mitarbeitende", list(ctx.staff.index),
                       format_func=lambda e: f"{e} ({ctx.staff.loc[e, 'role']})")
    day = st.selectbox("Tag", ctx.plan_dates, format_func=lambda d: d.strftime("%a, %d.%m.%Y"))
    duration = st.slider("Dauer in Tagen", 1, 7, 1)
    c1, c2 = st.columns(2)
    if c1.button("Ausfall melden", use_container_width=True):
        for offset in range(duration):
            i = ctx.plan_dates.index(day) + offset
            if i < len(ctx.plan_dates):
                st.session_state.manual.add((emp, ctx.plan_dates[i].isoformat()))
        st.rerun()
    if c2.button("Zuruecksetzen", use_container_width=True):
        st.session_state.manual = set()
        st.rerun()
    if st.session_state.manual:
        st.caption(f"{len(st.session_state.manual)} manuelle Ausfalltage aktiv")

manual = {(e, date.fromisoformat(d)) for e, d in st.session_state.manual}
manual_key = tuple(sorted(st.session_state.manual))


# --------------------------------------------------------------------------
# Planung (mit Zwischenspeicher, damit der Solver nicht bei jedem Klick laeuft)
# --------------------------------------------------------------------------

def compute(method: str, scenario: str, manual_set, reference=None, limit=30,
            fair: float | None = None, basisplan=None):
    """
    `reference` ist die Vorlage fuer die reaktive Umplanung, `basisplan` der
    Dienstplan, der bei den Krankmeldungen galt - aus ihm wird die
    Krankheitsgutschrift berechnet. Bei der vollstaendigen Neuplanung gibt es
    keine Vorlage, der Basisplan fuer die Gutschrift bleibt aber derselbe.
    """
    if method == "greedy":
        return P.plan_greedy(ctx, scenario, manual_absences=manual_set,
                             fixed=reference.assignments if reference else None,
                             basisplan=basisplan)
    weights = None
    if fair is not None and fair != P.WEIGHTS["fair"]:
        weights = dict(P.WEIGHTS)
        weights["fair"] = float(fair)
    return P.plan_milp(ctx, scenario, manual_absences=manual_set,
                       reference=reference, time_limit_s=float(limit),
                       weights=weights, basisplan=basisplan)


@st.cache_resource(show_spinner=False)
def _planspeicher() -> dict:
    """
    Gemeinsamer Zwischenspeicher fuer alle Sitzungen der App-Instanz. Ein einmal
    gerechneter Plan steht damit auch nach einem Neuladen der Seite oder in
    einem zweiten Browserfenster sofort zur Verfuegung. Plaene werden nach der
    Berechnung nicht mehr veraendert und koennen deshalb geteilt werden.
    """
    return {}


def cached(key, factory):
    store = _planspeicher()
    key = (getattr(P, "_geladener_stand", ""),) + tuple(key)
    if key not in store:
        if len(store) > 400:          # Obergrenze gegen unbegrenztes Wachstum
            store.clear()
        store[key] = factory()
    return store[key]


def ausgangsplan(m: str, limit: float):
    return compute(m, REFERENCE_SCENARIO, set(), limit=limit)


def ladehinweis(m: str) -> str:
    if m == "milp":
        return (f"Ausgangsplan der Optimierung wird berechnet - das dauert bis zu "
                f"{time_limit} Sekunden ...")
    return "Ausgangsplan wird berechnet ..."


# Der Ausgangsplan (S0) wird immer mit den Standardgewichten erstellt - unabhaengig
# von der gewaehlten Prioritaet. Sonst ginge jede Prioritaet von einem anderen
# Ausgangsplan aus, und die Planstabilitaet waere zwischen den Prioritaeten nicht
# vergleichbar: Gleiche Ausfaelle treffen in verschiedenen Plaenen
# unterschiedlich viele Dienste. Die Prioritaet wirkt auf die Anpassung.
ref_key = (data_key, method, "REF", (), time_limit)
with st.spinner(ladehinweis(method)):
    reference = cached(ref_key, lambda: ausgangsplan(method, time_limit))

cur_key = (data_key, method, scenario, manual_key, reactive, time_limit, prio)
is_reference = (scenario == REFERENCE_SCENARIO and not manual)
if is_reference and not reactive:
    current = reference
else:
    with st.spinner("Plan wird berechnet ..."):
        current = cached(cur_key, lambda: compute(
            method, scenario, manual, reference if reactive else None, time_limit,
            fair=prio, basisplan=reference))

kpi = P.evaluate(ctx, current, basisplan=reference, manual_absences=manual)
stab = P.stability(reference, current)


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
metric(cols[4], f"{kpi['auslastung_spanne']:.0%}", "Spanne der Auslastung")
metric(cols[5], "Referenz" if is_reference else f"{stab['planstabilitaet']:.0%}",
       "Planstabilitaet", warn=not is_reference and stab["planstabilitaet"] < 0.8)

info_bits = [f"Verfahren: {current.method}",
             f"Planungszeit {kpi['planungszeit_s']:.2f} s",
             f"{len(ctx.plan_dates)} Tage",
             f"{kpi['soll_dienste']} Soll-Dienste",
             "reaktive Umplanung" if reactive else "vollstaendige Neuplanung"]
if method == "milp":
    info_bits.append(f"Priorität: {prio_label}")
if current.info:
    info_bits.append(f"Modell: {current.info.get('variablen', '?')} Variablen / "
                     f"{current.info.get('nebenbedingungen', '?')} Nebenbedingungen")
st.caption(" &middot; ".join(info_bits), unsafe_allow_html=True)

if not is_reference:
    st.info(f"Gegenueber dem Referenzplan wurden **{stab['geaenderte_zuweisungen']} "
            f"Zuweisungen** geaendert. Je niedriger dieser Wert bei gleicher "
            f"Besetzungsquote, desto stabiler der Plan fuer die Mitarbeitenden.")

tabs = st.tabs(["Dienstplan", "Verfahrensvergleich", "Bedarf & Besetzung",
                "Pruefhinweise", "Arbeitszeit", "Mitarbeitende", "Daten & Regeln"])


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
        st.dataframe(matrix.style.map(lambda v: f"background-color: {colors.get(v, '')}"),
                     use_container_width=True, height=760)
    except Exception:                                       # noqa: BLE001
        st.dataframe(matrix, use_container_width=True, height=760)
    st.caption("Der Export enthaelt den vollstaendigen Eingabedatensatz plus die "
               "Spalte assigned_shift - ein Artefakt fuer die spaetere Auswertung.")


# --------------------------------------------------------------------------
with tabs[1]:
    st.markdown("**Beide Verfahren auf identischer Datengrundlage**, gleiches "
                "Szenario, gleiche Regeln. Das ist der Kern der Evaluation.")
    MODI = {
        "End-to-End: jedes Verfahren plant und repariert selbst": "self",
        "Gemeinsamer Ausgangsplan: Regelbasiert": "greedy",
        "Gemeinsamer Ausgangsplan: MILP-Optimierung": "milp",
    }
    modus_label = st.radio(
        "Welcher Vergleich?", list(MODI.keys()), index=0,
        help="End-to-End beantwortet die Leitfrage: Excel-Welt gegen KI-Welt, "
             "jedes Verfahren erstellt den Monatsplan selbst und passt ihn "
             "selbst an. Die beiden anderen Modi sind die Methodenkontrolle - "
             "sie lassen beide Verfahren denselben Plan reparieren und zeigen, "
             "dass das Ergebnis nicht an unterschiedlichen Ausgangsplaenen "
             "haengt.")
    modus = MODI[modus_label]

    if st.button("Vergleich rechnen", type="primary"):
        st.session_state["compare_key"] = (data_key, scenario, manual_key,
                                           time_limit, modus, prio)

    if st.session_state.get("compare_key") == (data_key, scenario, manual_key,
                                               time_limit, modus, prio):
        rows = []
        for label, m in METHODS.items():
            ref_m = m if modus == "self" else modus
            with st.spinner(f"{label} ..."):
                m_ref = cached((data_key, ref_m, "REF", (), time_limit),
                               lambda r=ref_m: ausgangsplan(r, time_limit))
                m_cur = cached((data_key, m, scenario, manual_key, ref_m, time_limit,
                                prio),
                               lambda m=m, r=m_ref: compute(m, scenario, manual, r,
                                                            time_limit, fair=prio,
                                                            basisplan=r))
            k = P.evaluate(ctx, m_cur, basisplan=m_ref, manual_absences=manual)
            s = P.stability(m_ref, m_cur)
            rows.append({
                "Verfahren": label,
                "Besetzungsquote": f"{k['besetzungsquote']:.1%}",
                "offene Dienste": k["offene_slots"],
                "Untergrenzenverstoesse": k["untergrenzen_verstoesse"],
                "harte Regelverstoesse": k["harte_verstoesse"],
                "weiche Abweichungen": k["weiche_abweichungen"],
                "Streuung Auslastung": round(k["auslastung_streuung"], 3),
                "Spanne Auslastung": f"{k['auslastung_spanne']:.1%}",
                "Hilfskraftanteil": f"{k['hilfskraftanteil']:.1%}",
                "Planstabilitaet": f"{s['planstabilitaet']:.1%}",
                "geaenderte Zuweisungen": s["geaenderte_zuweisungen"],
                "Planungszeit (s)": round(k["planungszeit_s"], 2),
            })
        st.dataframe(pd.DataFrame(rows).set_index("Verfahren").T,
                     use_container_width=True)
        if modus == "self":
            st.caption(
                "**End-to-End-Vergleich.** Jedes Verfahren erstellt den "
                "Monatsplan selbst und passt ihn selbst an - so, wie es in der "
                "jeweiligen Welt tatsaechlich liefe. Das ist der Vergleich, den "
                "die Leitfrage stellt. Planstabilitaet ist hier gegen zwei "
                "verschiedene Ausgangsplaene gemessen; lesen Sie sie deshalb "
                "immer zusammen mit den absolut geaenderten Zuweisungen - nur "
                "wenn beide zugunsten desselben Verfahrens ausfallen, ist die "
                "Aussage belastbar.")
        else:
            ref_name = ("Regelbasiert" if modus == "greedy" else "MILP-Optimierung")
            st.caption(
                f"**Methodenkontrolle.** Beide Verfahren reparieren denselben "
                f"Ausgangsplan ({ref_name}). Das prueft, ob ein Unterschied im "
                "End-to-End-Vergleich nur an der Qualitaet der Ausgangsplaene "
                "haengt. Achtung bei der Interpretation: Erbt ein Verfahren "
                "einen Plan mit offenen Diensten und Regelverstoessen, kann es "
                "diese nur beheben, indem es Zuweisungen aendert - eine "
                "niedrige Zahl geaenderter Zuweisungen ist dann kein Qualitaets"
                "merkmal, sondern Untaetigkeit.")
        st.caption(
            "Streuung und Spanne der Auslastung messen, wie gleichmaessig die "
            "Arbeit ueber die Belegschaft verteilt ist - erst sie unterscheiden "
            "zwei Plaene mit gleicher Besetzungsquote.")
        if prio == 0.02:
            st.caption(
                f"**Priorität steht auf „{prio_label}“.** Das Gewicht fuer "
                "Lastausgleich betraegt 0,02 je Minute gegen 200 je beibehaltener "
                "Zuweisung - die Optimierung fuellt deshalb vor allem Luecken und "
                "verteilt eine geerbte Schieflage nicht neu. Auf „Verteilungs"
                "gerechtigkeit“ umgestellt sinkt die Spanne der Auslastung "
                "deutlich, die Planstabilitaet dafuer um rund 1 bis 3 "
                "Prozentpunkte (ERGEBNISSE.md, Abschnitt 4.5). Die Stufe "
                "„Ausgewogen“ erreicht im Mittel eine deutlich bessere "
                "Lastverteilung als die Heuristik, ohne Stabilitaet einzubuessen.")
    else:
        st.caption("Der Vergleich rechnet beide Verfahren durch und braucht je nach "
                   "Rechenzeitgrenze einige Sekunden.")


# --------------------------------------------------------------------------
with tabs[2]:
    rows = []
    for d in ctx.plan_dates:
        day = ctx.days.loc[d]
        for s in P.SHIFT_IDS:
            crew = [e for (e, dd), sh in current.assignments.items() if dd == d and sh == s]
            countable = [e for e in crew if int(ctx.staff.loc[e, "ppug_countable"]) == 1]
            fach = [e for e in countable
                    if ctx.staff.loc[e, "ppug_category"] == "Pflegefachkraft"]
            rows.append({
                "Datum": d.strftime("%a %d.%m."), "Schicht": s,
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
    st.line_chart(cover.groupby("Datum", sort=False)[["Soll", "Besetzt"]].sum())
    st.caption("Untergrenze nach PpUGV § 6 (Tag 10:1, Nacht 22:1); Soll aus dem "
               "Pflegeaufwand nach PPR-2.0-Logik. Die Untergrenze ist eine harte "
               "Restriktion, das Soll eine Qualitaetskennzahl.")


# --------------------------------------------------------------------------
with tabs[3]:
    viol = kpi["verstoesse"]
    if not viol:
        st.success("Alle Dienste konnten unter den hinterlegten Regeln besetzt werden.")
    else:
        hard = [v for v in viol if "weich" not in v["art"]]
        soft = [v for v in viol if "weich" in v["art"]]
        if hard:
            st.markdown(f"**{len(hard)} harte Befunde**")
            for v in hard[:60]:
                st.markdown(f'<div class="notice"><strong>{v["art"]}</strong> &middot; '
                            f'{v["hinweis"]}</div>', unsafe_allow_html=True)
            if len(hard) > 60:
                st.caption(f"... und {len(hard) - 60} weitere")
        else:
            st.success("Keine harten Regelverstoesse.")
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
with tabs[4]:
    m1, m2, m3 = st.columns(3)
    metric(m1, f"{kpi['auslastung_mittel']:.0%}", "mittlere Auslastung")
    metric(m2, f"{kpi['auslastung_streuung']:.3f}", "Streuung (Standardabweichung)")
    metric(m3, f"{kpi['auslastung_min']:.0%} – {kpi['auslastung_max']:.0%}",
           "geringste / hoechste Auslastung")
    hours = pd.DataFrame(kpi["arbeitszeit_detail"])
    if not hours.empty:
        hours = hours.join(ctx.staff[["role", "employment_pct"]], on="employee_id")
        show = hours.assign(**{
            "Ist (h)": (hours["ist_min"] / 60).round(1),
            "Gutschrift Krankheit (h)": (hours["gutschrift_min"] / 60).round(1),
            "Soll (h)": (hours["soll_min"] / 60).round(1),
            "Abweichung (h)": (hours["abweichung_min"] / 60).round(1),
        })[["employee_id", "role", "employment_pct", "Ist (h)",
            "Gutschrift Krankheit (h)", "Soll (h)",
            "Abweichung (h)", "abweichung_pct"]].rename(columns={
                "employee_id": "ID", "role": "Rolle", "employment_pct": "Umfang",
                "abweichung_pct": "Abweichung (%)"})
        st.dataframe(show.sort_values("Abweichung (%)"), use_container_width=True,
                     hide_index=True)
        st.bar_chart(hours.set_index("employee_id")["abweichung_pct"])
    st.caption("Soll = Vertragskapazitaet im Horizont, anteilig um geplante "
               "Abwesenheiten gekuerzt. Krankheitsbedingt ausgefallene Dienste "
               "werden mit ihrer Dauer laut Ausgangsplan gutgeschrieben und "
               "zaehlen wie gearbeitete Zeit (Entgeltausfallprinzip, § 4 Abs. 1 "
               "EFZG) - niemand muss Krankheit nacharbeiten. Auszubildende sind "
               "nicht enthalten, da sie nach PpUGV § 2 nicht auf die Besetzung "
               "angerechnet werden.")
    st.markdown(f"Pflegehilfskraft-Anteil an den Diensten: "
                f"**{kpi['hilfskraftanteil']:.1%}** "
                f"(Grenze nach PpUGV: {kpi['hilfskraft_grenze']:.0%})")


# --------------------------------------------------------------------------
with tabs[5]:
    people = ctx.staff[["role", "role_group", "skills", "employment_pct",
                        "weekly_hours", "night_eligible", "ppug_category",
                        "max_night_shifts", "time_account_start_min"]].copy()
    blocked = ctx.unavailable | P.scenario_absences(ctx, scenario) | manual
    people["Dienste im Plan"] = [
        sum(1 for (e, _), _s in current.assignments.items() if e == idx)
        for idx in people.index]
    people["Abwesenheit im Horizont"] = [
        sum(1 for d in ctx.plan_dates if (idx, d) in blocked) for idx in people.index]
    st.dataframe(people, use_container_width=True, height=560)
    st.caption(f"{len(ctx.staff)} pseudonyme Mitarbeitende. "
               "Keine Klarnamen, keine Ausfallgruende, keine Gesundheitsdaten.")


# --------------------------------------------------------------------------
with tabs[6]:
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

#### Die beiden Verfahren

**Regelbasiert (Baseline).** Geht Tag fuer Tag und Schicht fuer Schicht vor
(Nachtdienst zuerst, weil dort die wenigsten Personen infrage kommen) und waehlt
jeweils die am wenigsten ausgelastete Person, die **alle harten Regeln** erfuellt.
Geprueft werden bei jeder einzelnen Zuweisung: Abwesenheit und Krankmeldung,
hoechstens ein Dienst je Person und Tag, Nachtdiensteignung, Stationsleitung nur
im Fruehdienst, maximale Dienstfolge, vertragliche Hoechstarbeitszeit, Ruhezeit
nach ArbZG §5 sowie die PpUGV-Vorgaben zu Fachkraftquote, Hilfskraftanteil und
Anrechenbarkeit von Auszubildenden. Findet sich niemand, der alle Regeln
erfuellt, bleibt der Dienst **offen** - die Baseline bricht keine Regel, um eine
Luecke zu schliessen.

*Weiche* Ziele kennt sie dagegen fast keine: Lastausgleich steckt in der
Auswahlregel, der Wochenend-Richtwert nur als Tiebreaker, Dienstwuensche gar
nicht. Genau das ist der Unterschied zur Optimierung - eine Excel-Planung hat
keine Zielfunktion, sondern eine Reihenfolge und eine Faustregel, und kann
konkurrierende Ziele deshalb nicht gegeneinander abwaegen.

**MILP-Optimierung.** Formuliert die gesamte Periode als gemischt-ganzzahliges
Programm und loest es mit HiGHS. Alle rechtlichen und vertraglichen Grenzen sind
harte Nebenbedingungen; Unterbesetzung, ungleiche Lastverteilung, unerfuellte
Wuensche sowie Wochenend- und Nachtdienstverteilung gehen gewichtet in die
Zielfunktion ein. Weil das Modell alle 28 Tage gleichzeitig betrachtet, kann es
eine heute unguenstige Zuweisung in Kauf nehmen, wenn sie den Gesamtplan
verbessert.

Zur Methodenwahl: Das Problem hat keine zu lernende Zielvariable und keine
historischen Planentscheidungen als Trainingsdaten - Machine Learning hat hier
keinen Ansatzpunkt. Einschlaegig sind mathematische Optimierung und Constraint
Programming (Burke et al. 2004; Van den Bergh et al. 2013).

Ist das dann KI? Umgangssprachlich nicht - das Modell lernt nichts. Fachlich
schon: Suche, Constraint-Erfuellung und Scheduling gehoeren seit den Anfaengen
zum Kern der KI (Russell & Norvig 2021). Ausfuehrlich in `ERGEBNISSE.md`,
Abschnitt 7.1.

#### Methodischer Hinweis

Die Bewertung in `evaluate()` prueft den fertigen Plan unabhaengig vom Planer
nach. Ein Verfahren darf seine eigene Regelkonformitaet nicht selbst behaupten -
sonst waere der KPI-Vergleich zirkulaer.

Damit der Vergleich fair bleibt, behandeln **beide** Verfahren denselben
Richtwert gleich: Der Nachtdienst-Richtwert ist eine gesetzte Annahme, keine
gesetzliche Grenze, und wird von `evaluate()` als weiche Abweichung gezaehlt.
Die Heuristik darf ihn deshalb ueberschreiten, bevor ein Dienst unbesetzt
bleibt - genau wie das MILP, das ihn mit einem Strafgewicht statt einer harten
Schranke modelliert.
""", unsafe_allow_html=True)
