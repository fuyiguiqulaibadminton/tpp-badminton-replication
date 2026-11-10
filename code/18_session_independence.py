# -*- coding: utf-8 -*-
"""
18_session_independence.py
==========================
Intra-session dependence of duration residuals after the cell composition is
removed (A4): ICC of residuals and raw durations, lag-1 correlation and the
variance components behind the independence assumption.
"""
import os
import pandas as pd
import numpy as np
import common as C

m = pd.read_csv(os.path.join(C.DER, "Session_matches.csv"))
q = pd.read_csv(os.path.join(C.DER, "TableS13_cell_quantiles.csv"))
lk = q.set_index(["discipline", "round"])["mean_dur"]
m = m.join(lk, on=["discipline", "round"]).dropna(subset=["mean_dur"])
m["resid"] = m.duration - m.mean_dur

def icc1(x, g):
    x = x.to_numpy()
    g = g.to_numpy()
    N = len(x)
    kg = len(np.unique(g))
    gm = x.mean()
    groups = pd.DataFrame({"g": g, "x": x}).groupby("g")
    ng = groups.size()
    mg = groups.x.mean()
    ssb = (ng * (mg - gm) ** 2).sum()
    ssw = ((x - mg.reindex(g).to_numpy()) ** 2).sum()
    msb = ssb / (kg - 1)
    msw = ssw / (N - kg)
    n_adj = (N - (ng ** 2).sum() / N) / (kg - 1)
    return (msb - msw) / (msb + (n_adj - 1) * msw)

m = m.sort_values(["session_id"]).reset_index(drop=True)
lag = []
for sid, g in m.groupby("session_id"):
    r = g.resid.to_numpy()
    if len(r) > 1:
        lag.append(pd.DataFrame({"a": r[:-1], "b": r[1:]}))
lag = pd.concat(lag)
res = dict(
    ICC_residual=icc1(m.resid, m.session_id),
    ICC_raw_duration=icc1(m.duration, m.session_id),
    lag1_residual_corr=lag.a.corr(lag.b),
    var_session_mean_resid=m.groupby("session_id").resid.mean().var(ddof=1),
    var_match_resid=m.resid.var(ddof=1))
out = pd.DataFrame([res])
out.to_csv(os.path.join(C.DER, "Session_independence.csv"),
           index=False, encoding="utf-8-sig")
C.write_lines("18_session_independence.txt",
              ["%s = %.4f" % (k, v) for k, v in res.items()])
