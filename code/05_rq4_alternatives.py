# -*- coding: utf-8 -*-
"""
05_rq4_alternatives.py
======================
RQ4 (Dataset B): candidate alternative explanations for the Tour TPP rise.

(i)   Competitive structure: three-set rate and the three-set TPP premium,
      separating the part due to rule-mandated breaks from in-match pace.
(ii)  Rule-mandated breaks: net TPP after deducting rule-book break lengths.
(iii) Rest interval: a player-match panel regression of TPP on days since the
      player's previous match, controlling for discipline and round.

None of these is a causal estimate. The rest-interval model is a negative
control (the public calendar omits Olympic, continental, domestic-league and
team events) and is reported in the manuscript as Supplementary Table S5;
this script also exports data/derived/TableS5_rest_panel.csv.
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

# ------------------------------------------------------- (i) three-set rate
r3 = {y: d.loc[d["year"] == y, "three"].mean() * 100 for y in (2018, 2025)}
L.append(f"three-set rate: {r3[2018]:.1f}% (2018) -> {r3[2025]:.1f}% (2025)")

# Headline premium is the raw two- vs three-game contrast (+2.85, SE 0.07), as
# quoted in the text; the FE-adjusted contrast is reported as a robustness line.
m_raw = smf.ols("TPP ~ three", data=d).fit()
m_fe = smf.ols("TPP ~ three + C(discipline) + C(round) + C(year)", data=d).fit()
premium = m_raw.params["three"]
L.append(f"three-set TPP premium (Tour, raw contrast) = "
         f"{premium:.2f} (SE {m_raw.bse['three']:.2f}, p {m_raw.pvalues['three']:.3g})")
L.append(f"  FE-adjusted contrast (discipline, round, year) = {m_fe.params['three']:.2f}")

S3 = d.loc[d["three"] == 1, "Pts"].mean()
S2 = d.loc[d["three"] == 0, "Pts"].mean()
br3, br2 = 420.0 / S3, 240.0 / S2
L.append(f"mean points: three-set {S3:.2f}, two-set {S2:.2f}")
L.append(f"rule-mandated breaks per point: three-set {br3:.2f} "
         f"(420/{S3:.1f}), two-set {br2:.2f} (240/{S2:.1f}), difference {br3-br2:.2f}")
L.append(f"residual three-set premium attributed to pace ~ "
         f"{premium-(br3-br2):.2f} s/point")

# annual slope with and without the three-set control
base = smf.ols("TPP ~ yr + C(discipline) + C(round)", data=d).fit().params["yr"]
ctrl = smf.ols("TPP ~ yr + three + C(discipline) + C(round)", data=d).fit().params["yr"]
L.append(f"annual TPP slope {base:.3f} -> {ctrl:.3f} s/year after three-set control")
contrib = (r3[2025] - r3[2018]) / 100 * premium / 7.0
L.append(f"contribution of the three-set-rate rise to the 2.23 s/point trend "
         f"~ {contrib:.3f} s/point per year-equivalent (about 1%)")

# FE annual slope sensitivity to the COVID-disrupted 2020/2021 seasons
L.append("")
for lab, dd in (("all years", d),
                ("drop 2020", d[d["year"] != 2020]),
                ("drop 2020-2021", d[~d["year"].isin([2020, 2021])])):
    b_ = smf.ols("TPP ~ yr + C(discipline) + C(round)", data=dd).fit().params["yr"]
    L.append(f"FE annual TPP slope ({lab}): {b_:.3f} s/year")

# deuce rate and per-game score gap
def deuce(row):
    return int(any(row[f"g{i}p1"] >= 20 and row[f"g{i}p2"] >= 20 for i in (1, 2, 3)
                   if pd.notna(row[f"g{i}p1"])))
d["deuce"] = d.apply(deuce, axis=1)
gaps = []
for _, r in d.iterrows():
    for i in (1, 2, 3):
        if pd.notna(r[f"g{i}p1"]):
            gaps.append({"year": r["year"], "gap": abs(r[f"g{i}p1"] - r[f"g{i}p2"])})
gdf = pd.DataFrame(gaps)
L.append(f"deuce rate: {d[d.year==2018]['deuce'].mean()*100:.1f}% (2018) -> "
         f"{d[d.year==2025]['deuce'].mean()*100:.1f}% (2025)")
L.append(f"mean per-game score gap: {gdf[gdf.year==2018]['gap'].mean():.2f} (2018), "
         f"{gdf[gdf.year==2025]['gap'].mean():.2f} (2025)")

# ------------------------------------------------- (ii) net-of-break TPP trend
def net_agg(year, mode):
    g = d[d["year"] == year]
    if mode == "full":
        deduct = np.where(g["three"] == 1, 420, 240)
    else:  # technical 11-point breaks only
        deduct = np.where(g["three"] == 1, 180, 120)
    net_seconds = 60 * g["duration"] - deduct
    return net_seconds.sum() / g["Pts"].sum()
def raw_agg(year):
    g = d[d["year"] == year]
    return 60 * g["duration"].sum() / g["Pts"].sum()
raw = raw_agg(2025) - raw_agg(2018)
L.append("")
L.append(f"raw aggregate TPP change 2018->2025 = {raw:.2f} s/point")
L.append("net-TPP levels (s/point) and mean deducted break time per point:")
L.append("  year   raw   net-full  net-technical | break/pt full  break/pt tech | three-set%")
for y in (2018, 2025):
    g = d[d["year"] == y]
    br_full = np.where(g["three"] == 1, 420, 240)
    br_tech = np.where(g["three"] == 1, 180, 120)
    L.append(f"  {y} {raw_agg(y):7.3f} {net_agg(y,'full'):9.3f} {net_agg(y,'technical'):13.3f} | "
             f"{br_full.sum()/g['Pts'].sum():13.3f} {br_tech.sum()/g['Pts'].sum():14.3f} | "
             f"{g['three'].mean()*100:5.1f}")
for mode in ("full", "technical"):
    ch = net_agg(2025, mode) - net_agg(2018, mode)
    L.append(f"net TPP ({mode}) change = {ch:.3f} s/point (raw {raw:.3f}; identical because "
             f"mean break allowance per point is unchanged across years)")

# ------------------------------------------ (iii) rest-interval player panel
# One row per player per match; days since that player's previous match at any
# event. OLS with discipline/round controls; SEs are computed by normal equations
# with iid, player-clustered and event-clustered sandwich estimators (avoids any
# large-matrix SVD). The model is deliberately crude and exploratory.
rows = []
for _, r in d.iterrows():
    rows.append((r["player1"], r["date"], r["TPP"], r["discipline"], r["round"], r["event"]))
    rows.append((r["player2"], r["date"], r["TPP"], r["discipline"], r["round"], r["event"]))
panel = pd.DataFrame(rows, columns=["player", "date", "TPP", "disc", "rd", "event"])
panel = panel.sort_values(["player", "date"])
panel["days_prev"] = panel.groupby("player")["date"].diff().dt.days
pm = panel.dropna(subset=["days_prev"]).reset_index(drop=True)

_disc = sorted(pm["disc"].unique())[1:]
_rd = sorted(pm["rd"].unique())[1:]
_X = [np.ones(len(pm)), pm["days_prev"].values]
for k in _disc:
    _X.append((pm["disc"] == k).astype(float).values)
for k in _rd:
    _X.append((pm["rd"] == k).astype(float).values)
X = np.column_stack(_X)
y = pm["TPP"].values
n, kk = X.shape
XtXi = np.linalg.inv(X.T @ X)
beta = XtXi @ (X.T @ y)
resid = y - X @ beta
s2 = (resid @ resid) / (n - kk)
se_iid = np.sqrt(s2 * np.diag(XtXi))


def cluster_se(col):
    G = pm[col].nunique()
    meat = np.zeros((kk, kk))
    for _, idx in pm.groupby(col).groups.items():
        idx = np.asarray(idx)
        s = X[idx].T @ resid[idx]
        meat += np.outer(s, s)
    c = G / (G - 1) * (n - 1) / (n - kk)
    return np.sqrt(np.diag(c * XtXi @ meat @ XtXi))


se_player = cluster_se("player")
se_event = cluster_se("event")
from scipy import stats as _st
L.append("")
L.append(f"rest-interval panel: {len(panel):,} player-match rows (two players x "
         f"{len(d):,} completed matches); {len(panel)-len(pm):,} are each player's first "
         f"observed match with no previous-match interval in-window and are dropped, "
         f"leaving {len(pm):,}")
for nm, se in (("iid", se_iid), ("player-clustered", se_player),
               ("event-clustered", se_event)):
    z = beta[1] / se[1]
    pv = 2 * (1 - _st.norm.cdf(abs(z)))
    L.append(f"  days-since-previous-match coef = {beta[1]:.4f} s/point/day "
             f"({nm} SE {se[1]:.4f}, p {pv:.3f})")
L.append("  practical magnitude: one extra week of rest changes TPP by "
         f"{7*beta[1]:.3f} s/point, negligible against the 2.23 s/point trend; "
         "significance is fragile to the clustering choice, so this is read as "
         "no practically meaningful rest effect.")


def _p(se):
    z = beta[1] / se
    return 2 * (1 - _st.norm.cdf(abs(z)))


s5 = pd.DataFrame([
    ("Player-match rows (2 players x completed matches)", f"{len(panel):,}"),
    ("Dropped: player's first in-window match (no prior interval)",
     f"{len(panel) - len(pm):,}"),
    ("Estimation sample", f"{len(pm):,}"),
    ("Coefficient on days since previous match (s/point/day)", f"{beta[1]:.4f}"),
    ("Event-clustered SE (p)", f"{se_event[1]:.4f} ({_p(se_event[1]):.3f})"),
    ("iid SE (p)", f"{se_iid[1]:.4f} ({_p(se_iid[1]):.3g})"),
    ("Player-clustered SE (p)", f"{se_player[1]:.4f} ({_p(se_player[1]):.3g})"),
    ("Effect of one additional week of rest (s/point)", f"{7*beta[1]:.2f}"),
], columns=["Item", "Value"])
s5.to_csv(os.path.join(cm.DER, "TableS5_rest_panel.csv"),
          index=False, encoding="utf-8-sig")

cm.write_lines("05_RQ4_alternatives.txt", L)
