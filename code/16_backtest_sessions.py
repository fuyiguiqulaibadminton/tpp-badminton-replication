# -*- coding: utf-8 -*-
"""
16_backtest_sessions.py
=======================
Hindcast session windows against the realized court-session durations (A2).
The fixed transition term cancels in the match-clock comparison, so coverage is
identical with or without transition time.
"""
import os
import pandas as pd
import common as C

m = pd.read_csv(os.path.join(C.DER, "Session_matches.csv"))
q = pd.read_csv(os.path.join(C.DER, "TableS13_cell_quantiles.csv"))
lk = q.set_index(["discipline", "round"])[["mean_dur", "P90_dur", "P95_dur"]]
m = m.join(lk, on=["discipline", "round"])
assert m[["mean_dur", "P90_dur", "P95_dur"]].notna().all().all(), "unmapped cells"

agg = m.groupby("session_id").agg(
    n=("duration", "size"), realized=("duration", "sum"),
    pred_mean=("mean_dur", "sum"), pred_p90=("P90_dur", "sum"),
    pred_p95=("P95_dur", "sum"))
for c in ["realized", "pred_mean", "pred_p90", "pred_p95"]:
    agg[c] = agg[c].round(1)
for t in (10, 15):
    for c in ["pred_mean", "pred_p90", "pred_p95"]:
        agg["win%02d_%s" % (t, c.split("_")[1])] = (
            agg[c] + (agg.n - 1) * t).round(1)
agg.to_csv(os.path.join(C.DER, "Session_backtest_detail.csv"),
           encoding="utf-8-sig")

def cov(pred):
    return (agg.realized <= agg[pred]).mean()

summary = []
for label, pc in [("mean", "pred_mean"), ("P90", "pred_p90"), ("P95", "pred_p95")]:
    over = agg.realized - agg[pc]
    summary.append(dict(tier=label, coverage=round(cov(pc), 4),
                        mean_overrun_all=round(over.mean(), 2),
                        mean_overrun_when_exceed=round(over[over > 0].mean(), 2),
                        pct_exceed_gt10=round((over > 10).mean(), 4),
                        pct_exceed_gt20=round((over > 20).mean(), 4),
                        mean_slack=round((-over).clip(lower=0).mean(), 2)))
s = pd.DataFrame(summary)
s.to_csv(os.path.join(C.DER, "Session_backtest_coverage.csv"),
         index=False, encoding="utf-8-sig")
lines = ["sessions=%d (match-clock coverage; fixed transition cancels)" % len(agg)]
lines += s.to_string(index=False).splitlines()
C.write_lines("16_backtest_sessions.txt", lines)
