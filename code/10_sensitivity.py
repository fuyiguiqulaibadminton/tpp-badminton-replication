# -*- coding: utf-8 -*-
"""
10_sensitivity.py
=================
Robustness and sensitivity supplements (all computed from public fields, no
video):

  Table S6  segmented World Championships trend with the knot placed at 2017,
            2018 and 2019 (break-point choice sensitivity)
  Table S7  year-by-year World Tour retirement / walk-over rates and a
            worst-case Tour trend that includes all 392 retired matches at
            their partial TPP
  Table S8  recording-change simulation: add +/-1, +/-2, +/-3 min to every
            match recorded after 2018 (uniform = level shift) or ramping the
            extra minutes linearly from 0 in 2018 to delta in 2025 (= slope
            shift), for both the Tour annual slope and the WC post-2018 slope
  MDE       minimum detectable post-2018 annual slope (two-sided alpha = .05,
            power = .80) from the annual-aggregation fit
  envelope  how many extra unobserved stoppage episodes per match the +2.23
            s/point Tour rise would correspond to if it were pure added clock
"""
import os
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats as st
import common as cm

L = []

# ============================================================ Table S6: knots
wc = cm.wc_rq1_sample(cm.load_world_championships())

def knot_fit(knot):
    d = wc.copy()
    d["yc"] = d["year"] - knot
    d["post"] = (d["year"] > knot).astype(int)
    d["ycpost"] = d["yc"] * d["post"]
    m = smf.ols("TPP ~ yc + ycpost + C(discipline) + C(round)", data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d["year"]})
    v = m.cov_params()
    se_post = np.sqrt(v.loc["yc", "yc"] + v.loc["ycpost", "ycpost"]
                      + 2 * v.loc["yc", "ycpost"])
    post = m.params["yc"] + m.params["ycpost"]
    p = 2 * (1 - st.norm.cdf(abs(post / se_post)))
    # annual aggregation
    agg = d.groupby("year").agg(T=("duration", "sum"), S=("Pts", "sum")).reset_index()
    agg["TPP"] = 60 * agg["T"] / agg["S"]
    agg["yc"] = agg["year"] - knot
    agg["post"] = (agg["year"] > knot).astype(int)
    agg["ycpost"] = agg["yc"] * agg["post"]
    ma = smf.ols("TPP ~ yc + ycpost", data=agg).fit()
    va = ma.cov_params()
    se_a = np.sqrt(va.loc["yc", "yc"] + va.loc["ycpost", "ycpost"]
                   + 2 * va.loc["yc", "ycpost"])
    post_a = ma.params["yc"] + ma.params["ycpost"]
    return dict(knot=knot, pre=m.params["yc"], post_match=post, se_match=se_post,
                p_match=p, post_annual=post_a, se_annual=se_a)

s6 = pd.DataFrame([knot_fit(k) for k in (2017, 2018, 2019)])
L.append("Table S6: break-point sensitivity (post-knot slope, s/year)")
for _, r in s6.iterrows():
    L.append(f"  knot {int(r['knot'])}: pre {r['pre']:.3f} | post {r['post_match']:.3f} "
             f"(match cluster SE {r['se_match']:.3f}, p {r['p_match']:.3f}) | "
             f"annual post {r['post_annual']:.3f} (SE {r['se_annual']:.3f})")
s6out = s6.round(3)
s6out.to_csv(os.path.join(cm.DER, "TableS6_knot_sensitivity.csv"),
             index=False, encoding="utf-8-sig")

# ============================================ Table S7: annual non-completion
tour = cm.load_world_tour()
tpp = cm.tour_tpp_sample(tour)
tpp["yr"] = tpp["year"] - 2018
rows = []
for y in range(2018, 2026):
    g = tour[tour["year"] == y]
    c = int((g["status"] == "完赛").sum())
    r = int((g["status"] == "RET").sum())
    w = int((g["status"] == "WO").sum())
    rows.append(dict(year=y, total=len(g), completed=c, RET=r, WO=w,
                     RET_pct=round(100 * r / (c + r), 2),
                     WO_pct=round(100 * w / len(g), 2)))
s7 = pd.DataFrame(rows)
s7.to_csv(os.path.join(cm.DER, "TableS7_annual_noncompletion.csv"),
          index=False, encoding="utf-8-sig")
L.append("")
L.append("Table S7: annual RET% / WO% (Tour)")
L.append("  " + s7.to_string(index=False).replace("\n", "\n  "))

# worst-case Tour trend: include all 392 retired matches at partial TPP
t = tour[tour["status"].isin(["完赛", "RET"])].copy()
t["tpp_use"] = np.where(t["status"] == "RET", 60 * t["duration"] / t["S"],
                        60 * t["duration"] / t["Pts"])
t = t[t["tpp_use"].notna() & np.isfinite(t["tpp_use"]) & (t["S"] > 0)].copy()
t["yr"] = t["year"] - 2018
base = smf.ols("TPP ~ yr + C(discipline) + C(round)", data=tpp).fit().params["yr"]
wc_slope = smf.ols("tpp_use ~ yr + C(discipline) + C(round)", data=t).fit().params["yr"]
L.append("")
L.append(f"Tour annual slope: completed only {base:.3f} (n={len(tpp):,}); "
         f"including 392 retirements at partial TPP {wc_slope:.3f} (n={len(t):,})")

# ============================================================ MDE (power)
agg = wc.groupby("year").agg(T=("duration", "sum"), S=("Pts", "sum")).reset_index()
agg["TPP"] = 60 * agg["T"] / agg["S"]
agg["year_c"] = agg["year"] - 2017
agg["yc_post"] = agg["year_c"] * (agg["year"] >= 2018).astype(int)
ma = smf.ols("TPP ~ year_c + yc_post", data=agg).fit()
v = ma.cov_params()
se_ann = np.sqrt(v.loc["year_c", "year_c"] + v.loc["yc_post", "yc_post"]
                 + 2 * v.loc["year_c", "yc_post"])
df = int(ma.df_resid)
mde = (st.t.ppf(0.975, df) + st.t.ppf(0.80, df)) * se_ann
# match-level cluster alternative (0.056)
m2 = smf.ols("TPP ~ year_c + yc_post + C(discipline) + C(round)", data=wc).fit(
    cov_type="cluster", cov_kwds={"groups": wc["year"]})
vm = m2.cov_params()
se_match = np.sqrt(vm.loc["year_c", "year_c"] + vm.loc["yc_post", "yc_post"]
                   + 2 * vm.loc["year_c", "yc_post"])
mde_match = (st.norm.ppf(0.975) + st.norm.ppf(0.80)) * se_match
L.append("")
L.append(f"Minimum detectable post-2018 slope (two-sided alpha .05, 80% power): "
         f"annual-aggregation SE {se_ann:.3f}, df {df}, MDE {mde:.2f} s/year; "
         f"match-level cluster SE {se_match:.3f}, MDE {mde_match:.2f} s/year")

# ===================================================== stoppage envelope (Tour)
Sbar = tpp["Pts"].mean()
per_year = 2.23 / 7 * Sbar
cum = 2.23 * Sbar
L.append("")
L.append(f"Stoppage envelope: mean points/match {Sbar:.1f}; to produce the +2.23 "
         f"s/point rise a clock would have to add {per_year:.1f} s/match per year, "
         f"{cum:.0f} s = {cum/60:.2f} min/match cumulatively by 2025")
for label, sec in (("hawkeye-style review (~10 s)", 10),
                   ("extended towel/ball change (~30 s)", 30),
                   ("medical time-out (~60 s)", 60)):
    L.append(f"  equivalent to an extra {cum/sec:.1f} {label} episodes per match")

# ================================================ Table S8: recording-change sim
sim_rows = []
def tour_slope(df):
    return smf.ols("TPP ~ yr + C(discipline) + C(round)", data=df).fit().params["yr"]

for delta in (-3, -2, -1, 1, 2, 3):
    d = tpp.copy()
    d["yr"] = d["year"] - 2018
    # uniform level shift: same extra minutes in every Tour year 2018-2025
    du = d.copy()
    du["TPP"] = du["TPP"] + 60 * delta / du["Pts"]
    # ramped: 0 in 2018 -> delta minutes by 2025 (held thereafter)
    dr = d.copy()
    fac = np.minimum((dr["year"] - 2018) / 7.0, 1.0)
    dr["TPP"] = dr["TPP"] + 60 * delta * fac / dr["Pts"]
    sim_rows.append(dict(series="Tour annual slope", delta_min=delta,
                         uniform_shift=round(tour_slope(du), 3),
                         ramped_shift=round(tour_slope(dr), 3)))

def wc_post(df):
    m = smf.ols("TPP ~ year_c + yc_post + C(discipline) + C(round)", data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df["year"]})
    return m.params["year_c"] + m.params["yc_post"]

for delta in (-3, -2, -1, 1, 2, 3):
    d = wc.copy()
    du = d.copy()
    du["TPP"] = du["TPP"] + 60 * delta / du["Pts"]
    dr = d.copy()
    facw = np.minimum((dr["year"] - 2018) / 7.0, 1.0)
    dr["TPP"] = dr["TPP"] + 60 * delta * facw / dr["Pts"]
    sim_rows.append(dict(series="WC post-2018 slope", delta_min=delta,
                         uniform_shift=round(wc_post(du), 3),
                         ramped_shift=round(wc_post(dr), 3)))

s8 = pd.DataFrame(sim_rows)
s8.to_csv(os.path.join(cm.DER, "TableS8_recording_change_sim.csv"),
          index=False, encoding="utf-8-sig")
L.append("")
L.append("Table S8: recording-change simulation (baseline Tour 0.295, WC post -0.092)")
L.append("  " + s8.to_string(index=False).replace("\n", "\n  "))

cm.write_lines("10_sensitivity.txt", L)
