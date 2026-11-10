# -*- coding: utf-8 -*-
"""
23_holdout_drift.py
===================
Diagnose why the standard-buffer coverage falls from 91.3% in-sample to 83.7%
on the 2023-2025 holdout. Training (2018-2022) and holdout (2023-2025) match
characteristics are compared, and counterfactual coverage separates the role of
the cell-mean drift from the residual-variance change. No new data are needed.
"""
import os
import numpy as np
import pandas as pd
import common as C

df = pd.read_csv(os.path.join(C.DER, "Tour_TPP_sample_n25928.csv"))
df = df.dropna(subset=["场地"]).copy()
df["year"] = pd.to_numeric(df.year)
train = df[df.year <= 2022].copy()
test = df[df.year >= 2023].copy()

summary = pd.DataFrame({
    "metric": ["matches", "duration mean (min)", "duration SD (min)",
               "TPP mean (s/point)", "TPP SD (s/point)",
               "three-set rate", "mean points per match"],
    "train_2018_2022": [len(train), round(train.duration.mean(), 3),
                        round(train.duration.std(ddof=1), 3),
                        round(train.TPP.mean(), 3), round(train.TPP.std(ddof=1), 3),
                        round((train.games == 3).mean(), 4),
                        round(train.Pts.mean(), 3)],
    "holdout_2023_2025": [len(test), round(test.duration.mean(), 3),
                          round(test.duration.std(ddof=1), 3),
                          round(test.TPP.mean(), 3), round(test.TPP.std(ddof=1), 3),
                          round((test.games == 3).mean(), 4),
                          round(test.Pts.mean(), 3)]})

def cell_mean(d):
    return d.groupby(["discipline", "round"]).duration.mean()

def cell_var(d):
    x = d.copy()
    gm = x.groupby(["discipline", "round"]).duration.transform("mean")
    x["r"] = x.duration - gm
    return x.groupby(["discipline", "round"]).r.var(ddof=1)

mu_tr, mu_te = cell_mean(train), cell_mean(test)
va_tr, va_te = cell_var(train), cell_var(test)

rows = []
for _, g in test.groupby(["event", "date", "场地"]):
    gg = g.copy()
    gg["mu_tr"] = gg.join(mu_tr.rename("v"), on=["discipline", "round"])["v"]
    gg["mu_te"] = gg.join(mu_te.rename("v"), on=["discipline", "round"])["v"]
    gg["va_tr"] = gg.join(va_tr.rename("v"), on=["discipline", "round"])["v"]
    gg["va_te"] = gg.join(va_te.rename("v"), on=["discipline", "round"])["v"]
    if gg[["mu_tr", "mu_te", "va_tr", "va_te"]].isna().any().any():
        continue
    rows.append(dict(realized=gg.duration.sum(), mu_tr=gg.mu_tr.sum(),
                     mu_te=gg.mu_te.sum(), va_tr=gg.va_tr.sum(),
                     va_te=gg.va_te.sum()))
r = pd.DataFrame(rows)

def coverage(mu, va):
    win = r[mu] + 1.645 * np.sqrt(r[va])
    return round((r.realized <= win).mean(), 4)

cf = pd.DataFrame([
    {"calibration": "A train mean + train var (frozen)", "coverage": coverage("mu_tr", "va_tr")},
    {"calibration": "B holdout mean + train var (mean refreshed)", "coverage": coverage("mu_te", "va_tr")},
    {"calibration": "C train mean + holdout var (var refreshed)", "coverage": coverage("mu_tr", "va_te")},
    {"calibration": "D holdout mean + holdout var (fully recalibrated)", "coverage": coverage("mu_te", "va_te")}])

summary.to_csv(os.path.join(C.DER, "Session_holdout_drift_summary.csv"),
               index=False, encoding="utf-8-sig")
cf.to_csv(os.path.join(C.DER, "Session_holdout_drift_counterfactual.csv"),
          index=False, encoding="utf-8-sig")

lines = ["holdout sessions=%d" % len(r), "", "Period comparison:"]
lines += summary.to_string(index=False).splitlines()
lines += ["", "Counterfactual standard coverage on holdout sessions:"]
lines += cf.to_string(index=False).splitlines()
lines += ["", "Mean cell-mean drift=%.2f min; sum residual variance ratio=%.3f" % (
    (mu_te - mu_tr).mean(), va_te.sum() / va_tr.sum())]
C.write_lines("23_holdout_drift.txt", lines)
