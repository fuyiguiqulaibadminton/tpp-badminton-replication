# -*- coding: utf-8 -*-
"""
12_extra_sensitivity.py
=======================
Additional sensitivity checks (public fields only, no video):

  1. Excluding the 2026 World Championships from the RQ1 segmented fit
     (the external Elo merge cannot cover 2026; this shows the main
     all-discipline trend is reported both with and without 2026).
  2. A legacy P1/P99 winsorization line: clip match-level TPP at its 1st and
     99th percentile within each analysis sample and refit the WC segmented
     and Tour annual slopes, compared with the full-sample (unwinsorized)
     slopes reported in the paper. This is a literal winsorization
     before/after comparison; the main analysis keeps the full sample.
"""
import os
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats as st
import common as cm

L = []
rows = []

wc = cm.wc_rq1_sample(cm.load_world_championships())
tour = cm.tour_tpp_sample(cm.load_world_tour())
tour["yr"] = tour["year"] - 2018


def wc_fit(d, label):
    m = smf.ols("TPP ~ year_c + yc_post + C(discipline) + C(round)", data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d["year"]})
    v = m.cov_params()
    b1, b2 = m.params["year_c"], m.params["yc_post"]
    post = b1 + b2
    se = np.sqrt(v.loc["year_c", "year_c"] + v.loc["yc_post", "yc_post"]
                 + 2 * v.loc["year_c", "yc_post"])
    p = 2 * (1 - st.norm.cdf(abs(post / se)))
    rows.append(dict(series="WC", check=label, n=len(d),
                     beta1=round(b1, 3), beta2=round(b2, 3),
                     post_or_annual=round(post, 3), SE=round(se, 3),
                     p=round(p, 3), winsor_lo="", winsor_hi=""))
    L.append(f"WC {label}: n={len(d)}  beta1={b1:.3f}  beta2={b2:.3f}  "
             f"post={post:.3f} (SE {se:.3f}, p {p:.3f})")
    return post


def tour_fit(d, label):
    m = smf.ols("TPP ~ yr + C(discipline) + C(round)", data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d["year"]})
    slope = m.params["yr"]
    rows.append(dict(series="Tour", check=label, n=len(d),
                     beta1="", beta2="",
                     post_or_annual=round(slope, 3),
                     SE=round(m.bse["yr"], 3),
                     p=round(m.pvalues["yr"], 4),
                     winsor_lo="", winsor_hi=""))
    L.append(f"Tour {label}: n={len(d)}  annual slope={slope:.3f} "
             f"(SE {m.bse['yr']:.3f}, p {m.pvalues['yr']:.4g})")
    return slope


# ---------------------------------------------------------- A-6: exclude 2026
n2026 = int((wc["year"] == 2026).sum())
L.append(f"RQ1 sample n={len(wc)}; 2026 matches in sample = {n2026}")
wc_fit(wc, "full sample 2006-2026 (main)")
wc_fit(wc[wc["year"] <= 2025].copy(), "excluding 2026")

# --------------------------------------------- B-17: P1/P99 winsorize and refit
for name, d, fitkind in (("WC", wc, "wc"), ("Tour", tour, "tour")):
    lo, hi = d["TPP"].quantile(0.01), d["TPP"].quantile(0.99)
    clipped = d["TPP"].clip(lo, hi)
    nlo = int((d["TPP"] < lo).sum())
    nhi = int((d["TPP"] > hi).sum())
    L.append(f"{name} P1/P99 bounds: [{lo:.2f}, {hi:.2f}]  "
             f"clipped low {nlo}, high {nhi}")
    d2 = d.copy()
    d2["TPP"] = clipped
    if fitkind == "wc":
        m = smf.ols("TPP ~ year_c + yc_post + C(discipline) + C(round)",
                    data=d2).fit(cov_type="cluster",
                                 cov_kwds={"groups": d2["year"]})
        v = m.cov_params()
        post = m.params["year_c"] + m.params["yc_post"]
        se = np.sqrt(v.loc["year_c", "year_c"] + v.loc["yc_post", "yc_post"]
                     + 2 * v.loc["year_c", "yc_post"])
        p = 2 * (1 - st.norm.cdf(abs(post / se)))
        rows.append(dict(series="WC", check="P1/P99 winsorized", n=len(d2),
                         beta1=round(m.params["year_c"], 3),
                         beta2=round(m.params["yc_post"], 3),
                         post_or_annual=round(post, 3), SE=round(se, 3),
                         p=round(p, 3),
                         winsor_lo=round(lo, 2), winsor_hi=round(hi, 2)))
        L.append(f"WC P1/P99 winsorized: post={post:.3f} (SE {se:.3f}, p {p:.3f})")
    else:
        m = smf.ols("TPP ~ yr + C(discipline) + C(round)", data=d2).fit(
            cov_type="cluster", cov_kwds={"groups": d2["year"]})
        slope = m.params["yr"]
        rows.append(dict(series="Tour", check="P1/P99 winsorized", n=len(d2),
                         beta1="", beta2="", post_or_annual=round(slope, 3),
                         SE=round(m.bse["yr"], 3),
                         p=round(m.pvalues["yr"], 4),
                         winsor_lo=round(lo, 2), winsor_hi=round(hi, 2)))
        L.append(f"Tour P1/P99 winsorized: slope={slope:.3f} "
                 f"(SE {m.bse['yr']:.3f}, p {m.pvalues['yr']:.4g})")

# baseline full-sample Tour slope line for the same table
tour_fit(tour, "full sample (main)")

out = pd.DataFrame(rows)
out.to_csv(os.path.join(cm.DER, "TableS11_extra_sensitivity.csv"),
           index=False, encoding="utf-8-sig")
L.append("")
L.append("Table S11 rows:")
L.append(out.to_string(index=False))
cm.write_lines("12_extra_sensitivity.txt", L)
