# -*- coding: utf-8 -*-
"""
02_rq1_trend.py
===============
RQ1 (Dataset A): segmented (piecewise) regression of match-level TPP at the
World Championships, 2006-2026, with a knot at 2017. Reports:

  * pre-2018 slope beta1, post-2018 slope increment beta2, post slope beta1+beta2
  * R^2 / adjusted R^2 and a Chow test against a single continuous slope
  * a pairs cluster bootstrap that resamples whole YEARS (10,000 replicates),
    giving a 95% CI and two-sided bootstrap p for the post-2018 slope
  * an annual-aggregation regression as a small-number-of-clusters robustness
  * the TOST equivalence check against +/-0.30, +/-0.25 and +/-0.20 s/year

The year-cluster bootstrap only reduces Monte-Carlo error as the replicate count
rises; the fundamental limitation is the small number of year clusters (16),
which is why the annual aggregation is also reported.
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import common as cm

d = cm.wc_rq1_sample(cm.load_world_championships())
L = []
L.append(f"RQ1 segmented regression, n = {len(d)}")

# Primary segmented model (Table 2): discipline + round fixed effects. The
# three-set (is_decider) covariate is reported from a separate augmented model
# below so that the slopes, Chow test and R^2 refer to one specification.
F_MAIN = "TPP ~ year_c + yc_post + C(discipline) + C(round)"
F_NULL = "TPP ~ year_c + C(discipline) + C(round)"
m = smf.ols(F_MAIN, data=d).fit(cov_type="cluster", cov_kwds={"groups": d["year"]})
b1, b2 = m.params["year_c"], m.params["yc_post"]
post = b1 + b2
# delta-method SE for the post-2018 slope beta1 + beta2
vcv = m.cov_params()
se_post = np.sqrt(vcv.loc["year_c", "year_c"] + vcv.loc["yc_post", "yc_post"]
                  + 2 * vcv.loc["year_c", "yc_post"])
L.append(f"beta1 (2006-2017 slope) = {b1:.3f} (cluster SE {m.bse['year_c']:.3f})")
L.append(f"beta2 (slope change)    = {b2:.3f} (cluster SE {m.bse['yc_post']:.3f})")
L.append(f"post-2018 slope beta1+beta2 = {post:.3f} (cluster SE {se_post:.3f})")
L.append(f"R^2 = {m.rsquared:.4f} ; adjusted R^2 = {m.rsquared_adj:.4f}")

# Augmented model adding the three-set (is_decider) control (separate statistic)
maug = smf.ols("TPP ~ year_c + yc_post + three + C(discipline) + C(round)",
               data=d).fit(cov_type="cluster", cov_kwds={"groups": d["year"]})
L.append(f"augmented model: three-set (is_decider) = {maug.params['three']:.2f} "
         f"(cluster SE {maug.bse['three']:.2f}); slope change robust at "
         f"{maug.params['yc_post']:.3f}")

# Chow test: single-slope model vs segmented model
m0 = smf.ols(F_NULL, data=d).fit()
from statsmodels.stats.anova import anova_lm
av = anova_lm(m0, m)
F, pF = av["F"][1], av["Pr(>F)"][1]
L.append(f"Chow test single vs segmented slope: F({int(av['df_diff'][1])}, "
         f"{int(av['df_resid'][1])}) = {F:.1f}, p = {pF:.3g}")

# -------------------------------------------------- year cluster bootstrap
years = sorted(d["year"].unique())
by_year = {y: d[d["year"] == y] for y in years}
pre = [y for y in years if y < 2018]
post = [y for y in years if y >= 2018]
rng = np.random.default_rng(cm.SEED)


def one_replicate():
    while True:
        sel = rng.choice(years, size=len(years), replace=True)
        if any(s in pre for s in sel) and any(s in post for s in sel):
            break
    samp = pd.concat([by_year[y] for y in sel])
    mm = smf.ols(F_MAIN, data=samp).fit()
    return mm.params["year_c"] + mm.params["yc_post"]


B = 10000
v = np.array([one_replicate() for _ in range(B)])
lo, hi = np.percentile(v, [2.5, 97.5])
p_boot = min(2 * min(np.mean(v <= 0), np.mean(v >= 0)), 1)
L.append(f"Year-cluster bootstrap ({B:,} resamples): post-slope 95% CI "
         f"[{lo:.2f}, {hi:.2f}], two-sided p = {p_boot:.2f}")

# -------------------------------------------------- annual aggregation check
agg = d.groupby("year").agg(T=("duration", "sum"), S=("Pts", "sum")).reset_index()
agg["TPP"] = 60 * agg["T"] / agg["S"]
agg["year_c"] = agg["year"] - 2017
agg["yc_post"] = agg["year_c"] * (agg["year"] >= 2018).astype(int)
ma = smf.ols("TPP ~ year_c + yc_post", data=agg).fit()
pa = ma.params["year_c"] + ma.params["yc_post"]
L.append("Annual-aggregation regression: beta1 = %.2f (SE %.2f), beta2 = %.2f "
         "(SE %.2f), post slope = %.2f"
         % (ma.params["year_c"], ma.bse["year_c"], ma.params["yc_post"],
            ma.bse["yc_post"], pa))
# annual-aggregation bootstrap CI for the post slope (years)
ay = agg["year"].values
rng2 = np.random.default_rng(cm.SEED + 1)
pv = []
for _ in range(B):
    idx = rng2.integers(0, len(agg), len(agg))
    s = agg.iloc[idx]
    if s["year"].min() >= 2018 or s["year"].max() < 2018:
        continue
    mm = smf.ols("TPP ~ year_c + yc_post", data=s).fit()
    pv.append(mm.params["year_c"] + mm.params["yc_post"])
pv = np.array(pv)
L.append("Annual-aggregation post-slope 95%% CI = [%.2f, %.2f]"
         % tuple(np.percentile(pv, [2.5, 97.5])))

# -------------------------------------------------- TOST equivalence margins
L.append("TOST: match-level year-cluster CI [%.2f, %.2f]" % (lo, hi))
for margin in (0.30, 0.25, 0.20):
    holds = (lo > -margin) and (hi < margin)
    L.append(f"  equivalence within +/-{margin:.2f} s/year: "
             f"{'YES' if holds else 'NO (lower/upper bound outside)'}")

cm.write_lines("02_RQ1_trend.txt", L)
