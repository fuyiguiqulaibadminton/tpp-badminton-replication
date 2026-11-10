# -*- coding: utf-8 -*-
"""
21_calibrate_session_buffer.py
==============================
Derive empirically calibrated session buffers and compare the three planning
postures (A2 calibration). Tight uses no buffer, standard uses 1.645 times the
independence standard deviation, conservative sums the cell P95 buffers.
"""
import os
import pandas as pd
import numpy as np
import common as C

det = pd.read_csv(os.path.join(C.DER, "Session_backtest_detail.csv"))
m = pd.read_csv(os.path.join(C.DER, "Session_matches.csv"))
q = pd.read_csv(os.path.join(C.DER, "TableS13_cell_quantiles.csv"))
lk = q.set_index(["discipline", "round"])["mean_dur"]
m = m.join(lk, on=["discipline", "round"]).dropna(subset=["mean_dur"])
m["resid"] = m.duration - m.mean_dur
cv = m.groupby(["discipline", "round"]).resid.var().rename("cellvar")
m = m.join(cv, on=["discipline", "round"])

sd = m.groupby("session_id").apply(
    lambda g: np.sqrt(g.cellvar.sum()), include_groups=False).rename("ind_sd")
det = det.merge(sd, on="session_id")
det["over_mean"] = det.realized - det.pred_mean
det["ind95_buffer"] = 1.645 * det.ind_sd
det["sumP95_buffer"] = det.pred_p95 - det.pred_mean

lines = ["session overrun vs mean (realized - sum means), empirical quantiles:"]
for p in [.5, .75, .9, .95]:
    lines.append("  P%-4s = %.1f min" % (int(p * 100), det.over_mean.quantile(p)))

def posture(bufcol):
    covered = (det.over_mean <= det[bufcol]).mean()
    slack = (det[bufcol] - det.over_mean).clip(lower=0).mean()
    return covered, slack

for name, col in [("independence 1.645SD (standard)", "ind95_buffer"),
                  ("sum of cell P95 (conservative)", "sumP95_buffer")]:
    covv, sl = posture(col)
    lines.append("%-34s coverage=%.4f mean idle slack=%.1f min" % (name, covv, sl))
lines.append("tight (no buffer) coverage=%.4f" % (det.over_mean <= 0).mean())

det.to_csv(os.path.join(C.DER, "Session_buffer_calibration.csv"),
           index=False, encoding="utf-8-sig")
C.write_lines("21_calibrate_session_buffer.txt", lines)
