# -*- coding: utf-8 -*-
"""
24_dependence_perturbation.py
=============================
Sensitivity of the standard-buffer coverage to the intra-session residual
dependence. The one-way random-effects session common variance is estimated
from the data, then stressed to one, two and three times its observed value
while the match-level variance is held fixed. Coverage under the frozen
independence-assumption buffer is measured by Monte Carlo simulation on the
holdout sessions. No new data are required.
"""
import os
import numpy as np
import pandas as pd
import common as C

# one-way random-effects variance components on reconstructed sessions
m = pd.read_csv(os.path.join(C.DER, "Session_matches.csv"))
q = pd.read_csv(os.path.join(C.DER, "TableS13_cell_quantiles.csv"))
m = m.join(q.set_index(["discipline", "round"])["mean_dur"].rename("md"),
           on=["discipline", "round"]).dropna(subset=["md"])
m["resid"] = m.duration - m.md
x = m.resid.to_numpy()
g = m.session_id.to_numpy()
N, kg = len(x), len(np.unique(g))
gd = pd.DataFrame({"g": g, "x": x}).groupby("g")
ng, mg = gd.size(), gd.x.mean()
ssb = (ng * (mg - x.mean()) ** 2).sum()
ssw = ((x - mg.reindex(g).to_numpy()) ** 2).sum()
msb = ssb / (kg - 1)
msw = ssw / (N - kg)
n_adj = (N - (ng ** 2).sum() / N) / (kg - 1)
sig2_e = msw
sig2_c = (msb - msw) / n_adj

# frozen train-period cell residual variances and holdout sessions
df = pd.read_csv(os.path.join(C.DER, "Tour_TPP_sample_n25928.csv"))
df = df.dropna(subset=["场地"]).copy()
df["year"] = pd.to_numeric(df.year)
train = df[df.year <= 2022]
gm = train.groupby(["discipline", "round"]).duration.transform("mean")
tr = train.copy()
tr["r"] = tr.duration - gm
cellvar = tr.groupby(["discipline", "round"]).r.var(ddof=1)
test = df[df.year >= 2023]
sessions = []
for _, gg0 in test.groupby(["event", "date", "场地"]):
    gg0 = gg0.join(cellvar.rename("cv"), on=["discipline", "round"])
    if not gg0.cv.isna().any():
        sessions.append(gg0.cv.to_numpy())

rng = np.random.default_rng(C.SEED)
R = 4000
scenarios = [("independence", 0.0), ("observed 1x", sig2_c),
             ("2x", 2 * sig2_c), ("3x", 3 * sig2_c)]
out_rows = []
for name, sc in scenarios:
    exceed, total = 0, 0
    for cv in sessions:
        k = len(cv)
        c = rng.normal(0, np.sqrt(sc), R)
        e = rng.normal(0, np.sqrt(cv), (R, k))
        tot = k * c + e.sum(axis=1)
        buf = 1.645 * np.sqrt(cv.sum())
        exceed += int((tot > buf).sum())
        total += R
    out_rows.append({"scenario": name,
                     "session common var": round(sc, 4),
                     "coverage": round(1 - exceed / total, 4)})
o = pd.DataFrame(out_rows)
o.to_csv(os.path.join(C.DER, "Session_dependence_perturbation.csv"),
         index=False, encoding="utf-8-sig")
lines = ["sig2_c=%.4f sig2_e=%.4f ICC=%.4f holdout sessions=%d R=%d" % (
    sig2_c, sig2_e, sig2_c / (sig2_c + sig2_e), len(sessions), R)]
lines += o.to_string(index=False).splitlines()
C.write_lines("24_dependence_perturbation.txt", lines)
