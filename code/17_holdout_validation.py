# -*- coding: utf-8 -*-
"""
17_holdout_validation.py
========================
Forward validation (A3). Cell quantiles and residual variances are fitted on
2018-2022 and their coverage is tested on 2023-2025, without refitting.
"""
import os
import pandas as pd
import numpy as np
import common as C

df = pd.read_csv(os.path.join(C.DER, "Tour_TPP_sample_n25928.csv"))
df = df.dropna(subset=["场地"]).copy()
df["year"] = pd.to_numeric(df.year)

def cell_q(d):
    return d.groupby(["discipline", "round"]).duration.agg(
        mean="mean", p90=lambda x: np.quantile(x, .9),
        p95=lambda x: np.quantile(x, .95))

def cell_var(d):
    d = d.copy()
    gm = d.groupby(["discipline", "round"]).duration.transform("mean")
    d["r"] = d.duration - gm
    return d.groupby(["discipline", "round"]).r.var()

train = df[df.year <= 2022]
test = df[df.year >= 2023]
q = cell_q(train)
cv = cell_var(train)

rows = []
for _, g in test.groupby(["event", "date", "场地"]):
    gg = g.join(q, on=["discipline", "round"]).join(
        cv.rename("cellvar"), on=["discipline", "round"])
    if gg[["mean", "p90", "p95"]].isna().any().any():
        continue
    realized = gg.duration.sum()
    base = gg["mean"].sum()
    rows.append(dict(n=len(gg), realized=realized, mean=base,
                     p90=gg.p90.sum(), p95=gg.p95.sum(),
                     std=base + 1.645 * np.sqrt(gg.cellvar.sum())))
r = pd.DataFrame(rows)

out = []
for name, col in [("mean", "mean"), ("P90", "p90"), ("P95", "p95"),
                  ("standard_ind", "std")]:
    over = r.realized - r[col]
    out.append(dict(test_tier=name, sessions=len(r),
                    coverage=round((over <= 0).mean(), 4),
                    mean_overrun=round(over.mean(), 2),
                    mean_idle=round((-over).clip(lower=0).mean(), 2)))
o = pd.DataFrame(out)
o.to_csv(os.path.join(C.DER, "Session_holdout_coverage.csv"),
         index=False, encoding="utf-8-sig")
lines = ["forward holdout sessions=%d" % len(r)]
lines += o.to_string(index=False).splitlines()
C.write_lines("17_holdout_validation.txt", lines)
