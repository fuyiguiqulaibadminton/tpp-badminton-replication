# -*- coding: utf-8 -*-
"""
09_composition_ledger.py
========================
Composition standardisation for the decomposition (Section 4.3) and the
robustness summary (Section 4.6).

(1) Point-weighted shift-share standardisation of the 2018->2025 aggregate Tour
    TPP change by discipline, round and event level. Aggregate TPP_t =
    sum_g w_{t,g} * m_{t,g}, with w the group share of total points and m the
    group aggregate TPP (60*sumT/sumS). Exact split:
        within  = sum_g w0_g (m1_g - m0_g)      (mix held at 2018 weights)
        between = sum_g (w1_g - w0_g) * m1_g    (composition/mix)
        within + between = total Delta TPP.
    The composition-standardised change equals `within`.

(2) Table 7 (Table7_attribution_ledger.csv): a *narrative* robustness summary
    for manuscript Table 8. Rows are separate robustness checks and are NOT
    additive; this is a synthesis, not a statistically estimated residual
    decomposition.
"""
import os
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import common as cm

d = cm.tour_tpp_sample(cm.load_world_tour())
d["date"] = pd.to_datetime(d["date"], errors="coerce")
d["yr"] = d["year"] - 2018
L = []

# ------------------------------------------------ (1) shift-share by grouping
def gm(year, group):
    g = d[d["year"] == year].groupby(group).agg(T=("duration", "sum"), S=("Pts", "sum"))
    m = 60 * g["T"] / g["S"]
    w = g["S"] / g["S"].sum()
    return m, w

def split(group):
    m0, w0 = gm(2018, group)
    m1, w1 = gm(2025, group)
    idx = sorted(set(m0.index) | set(m1.index))
    m0 = m0.reindex(idx); m1 = m1.reindex(idx)
    w0 = w0.reindex(idx, fill_value=0.0); w1 = w1.reindex(idx, fill_value=0.0)
    total = float((w1 * m1).sum() - (w0 * m0).sum())
    within = float((w0 * (m1 - m0)).sum())
    between = float(((w1 - w0) * m1).sum())
    return total, within, between, m0, m1, w0, w1

comp_rows = []
detail = []
for group in ("discipline", "round", "level"):
    total, within, between, m0, m1, w0, w1 = split(group)
    comp_rows.append({"grouping": group, "total_delta_TPP": round(total, 3),
                      "within_2018weights": round(within, 3),
                      "between_mix": round(between, 3)})
    L.append(f"{group:10s} total={total:.3f} within={within:.3f} between={between:.3f}")
    if group == "level":
        for g in m0.index:
            detail.append({"level": g, "TPP_2018": round(m0[g], 2),
                           "TPP_2025": round(m1[g], 2),
                           "point_weight_2018_pct": round(100 * w0[g], 1),
                           "point_weight_2025_pct": round(100 * w1[g], 1)})

comp = pd.DataFrame(comp_rows)
comp.to_csv(os.path.join(cm.DER, "Composition_standardization.csv"),
            index=False, encoding="utf-8-sig")
lvl = pd.DataFrame(detail)
lvl.to_csv(os.path.join(cm.DER, "Composition_level_detail.csv"),
           index=False, encoding="utf-8-sig")

# ------------------------------------------- (2) Table 7 ledger components
base = smf.ols("TPP ~ yr + C(discipline) + C(round)", data=d).fit().params["yr"]
ctrl = smf.ols("TPP ~ yr + three + C(discipline) + C(round)", data=d).fit().params["yr"]
drop20 = smf.ols("TPP ~ yr + C(discipline) + C(round)",
                 data=d[d["year"] != 2020]).fit().params["yr"]
drop2021 = smf.ols("TPP ~ yr + C(discipline) + C(round)",
                   data=d[~d["year"].isin([2020, 2021])]).fit().params["yr"]

def raw_agg(year):
    g = d[d["year"] == year]
    return 60 * g["duration"].sum() / g["Pts"].sum()

def net_agg(year, mode):
    g = d[d["year"] == year]
    deduct = np.where(g["three"] == 1, 420, 240) if mode == "full" else \
             np.where(g["three"] == 1, 180, 120)
    return (60 * g["duration"] - deduct).sum() / g["Pts"].sum()

raw_ch = raw_agg(2025) - raw_agg(2018)
net_full = net_agg(2025, "full") - net_agg(2018, "full")
net_tech = net_agg(2025, "technical") - net_agg(2018, "technical")

cd = {r["grouping"]: r for r in comp_rows}

# rest negative-control weekly magnitude (player-match panel)
rows = []
for _, r in d.iterrows():
    rows.append((r["player1"], r["date"], r["TPP"], r["discipline"], r["round"]))
    rows.append((r["player2"], r["date"], r["TPP"], r["discipline"], r["round"]))
panel = pd.DataFrame(rows, columns=["player", "date", "TPP", "disc", "rd"])
panel = panel.sort_values(["player", "date"])
panel["days_prev"] = panel.groupby("player")["date"].diff().dt.days
pm = panel.dropna(subset=["days_prev"])
rest_b = smf.ols("TPP ~ days_prev + C(disc) + C(rd)", data=pm).fit().params["days_prev"]
weekly = 7 * rest_b

ledger = [
    ("Analysis check", "Estimate", "Reading"),
    ("Raw annual slope, discipline + round fixed effects (s/point/year)",
     f"{base:.3f}", "Baseline 2018-2025 trend"),
    ("  + three-set indicator", f"{ctrl:.3f}", "Three-set structure ~1% of trend"),
    ("  excluding 2020 / excluding 2020-2021", f"{drop20:.3f} / {drop2021:.3f}",
     "COVID seasons do not drive the slope"),
    ("Raw 2018 -> 2025 aggregate Delta TPP (s/point)", f"+{raw_ch:.2f}", "Total rise"),
    ("  net of rule breaks (net-full / net-technical)",
     f"+{net_full:.2f} / +{net_tech:.2f}", "Mandated breaks cancel in the difference"),
    ("  composition standardised to 2018 weights: discipline / round / level",
     f"+{np.round(cd['discipline']['within_2018weights'], 2):.2f} / "
     f"+{np.round(cd['round']['within_2018weights'], 2):.2f} / "
     f"+{np.round(cd['level']['within_2018weights'], 2):.2f}",
     f"mix terms {np.round(cd['discipline']['between_mix'], 2):+.2f} / "
     f"{np.round(cd['round']['between_mix'], 2):+.2f} / "
     f"{np.round(cd['level']['between_mix'], 2):+.2f}"),
    ("  rest interval, per additional week of rest", f"{weekly:.2f}",
     "Negative control (Table S5)"),
    ("Unexplained composite per-point clock time", f"~ +{raw_ch:.1f} (the full rise)",
     "Rally/pause mechanism requires video coding"),
]
led = pd.DataFrame(ledger[1:], columns=ledger[0])
led.to_csv(os.path.join(cm.DER, "Table7_attribution_ledger.csv"),
           index=False, encoding="utf-8-sig")
L.append("")
L.append("Table 7 ledger:")
L.extend(["  " + " | ".join(r) for r in ledger])
cm.write_lines("09_composition_ledger.txt", L)
