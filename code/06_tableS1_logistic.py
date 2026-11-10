# -*- coding: utf-8 -*-
"""
06_tableS1_logistic.py
======================
Supplementary Table S1: logistic regression of in-match retirement (1/0) on TPP
with discipline and round fixed effects and a three-set control (World Tour).

All 392 retirements have both a recorded elapsed time and partial game scores;
their TPP is computed as 60 * elapsed minutes / points played to abandonment.
Because partial TPP is truncated at the retirement moment, this estimate is
biased and is NOT used for inference (the cell-level Spearman result in RQ3 is
the more reliable descriptive statistic).
"""
import os
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import common as cm

t = cm.load_world_tour()
t = t[t["status"].isin(["完赛", "RET"])].copy()
# completed: full TPP ; retired: partial TPP from elapsed time / points played
t["tpp_use"] = np.where(t["status"] == "RET", 60 * t["duration"] / t["S"],
                        60 * t["duration"] / t["Pts"])
t["ret"] = (t["status"] == "RET").astype(int)
t = t[t["tpp_use"].notna() & (t["S"] > 0)]
L = [f"logistic n = {len(t)} (completed {int((t.status=='完赛').sum())} + "
     f"RET {int(t['ret'].sum())})"]

m = smf.logit("ret ~ tpp_use + three + C(discipline) + C(round)", data=t).fit(disp=0)
ci = m.conf_int()
rows = []
L.append("")
L.append("predictor | b | SE | z | p | OR | 95% CI")
for name in m.params.index:
    b = m.params[name]; se = m.bse[name]; z = b/se; p = m.pvalues[name]
    OR = np.exp(b); lo, hi = np.exp(ci.loc[name])
    rows.append(dict(predictor=name, b=round(b, 3), SE=round(se, 3),
                     z=round(z, 2), p=round(p, 3), OR=round(OR, 3),
                     CI=f"[{lo:.3f}, {hi:.3f}]"))
    L.append(f"{name} | {b:.3f} | {se:.3f} | {z:.2f} | {p:.3g} | {OR:.3f} | [{lo:.3f}, {hi:.3f}]")
L.append("")
L.append(f"Pseudo R^2 (McFadden) = {m.prsquared:.3f}")

pd.DataFrame(rows).to_csv(os.path.join(cm.DER, "TableS1_logistic.csv"),
                          index=False, encoding="utf-8-sig")
cm.write_lines("06_TableS1_logistic.txt", L)
