# -*- coding: utf-8 -*-
"""
19_baseline_compare.py
======================
Compare the TPP cell-P95 rule against two baselines (A5): a mean schedule with
no buffer, and the previous-year same-cell P95. Reports coverage and absolute
error on the same reconstructed sessions.
"""
import os
import pandas as pd
import numpy as np
import common as C

m = pd.read_csv(os.path.join(C.DER, "Session_matches.csv"))
m["year"] = pd.to_datetime(m.date).dt.year
raw = pd.read_csv(os.path.join(C.DER, "Tour_TPP_sample_n25928.csv"))
raw["year"] = pd.to_numeric(raw.year)

cell = raw.groupby(["discipline", "round"]).duration.agg(
    cellmean="mean", cellp95=lambda x: np.quantile(x, .95))
yr = raw.groupby(["year", "discipline", "round"]).duration.apply(
    lambda x: np.quantile(x, .95)).rename("yrp95").reset_index()
yr["prev_year"] = yr.year + 1
prev = yr.rename(columns={"yrp95": "lastyear_p95"})[
    ["prev_year", "discipline", "round", "lastyear_p95"]]

m = m.merge(cell, on=["discipline", "round"])
m = m.merge(prev, left_on=["year", "discipline", "round"],
            right_on=["prev_year", "discipline", "round"], how="left")

def agg(col):
    return m.groupby("session_id").apply(
        lambda g: g[col].sum(), include_groups=False)

realized = m.groupby("session_id").duration.sum()
base = pd.DataFrame({
    "realized": realized, "mean": agg("cellmean"),
    "tpp_p95": agg("cellp95"), "lastyear_p95": agg("lastyear_p95")}).dropna()

out = []
for name, col in [("1 mean (no buffer)", "mean"),
                  ("2 last-year cell P95", "lastyear_p95"),
                  ("3 TPP rule cell P95", "tpp_p95")]:
    over = base.realized - base[col]
    out.append(dict(baseline=name, sessions=len(base),
                    coverage=round((over <= 0).mean(), 4),
                    mean_overrun=round(over.mean(), 2),
                    mae=round(over.abs().mean(), 2),
                    mean_idle=round((-over).clip(lower=0).mean(), 2)))
o = pd.DataFrame(out)
o.to_csv(os.path.join(C.DER, "Session_baseline_compare.csv"),
         index=False, encoding="utf-8-sig")
lines = ["baseline comparison sessions=%d" % len(base)]
lines += o.to_string(index=False).splitlines()
C.write_lines("19_baseline_compare.txt", lines)
