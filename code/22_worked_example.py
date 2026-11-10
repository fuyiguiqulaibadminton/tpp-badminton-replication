# -*- coding: utf-8 -*-
"""
22_worked_example.py
====================
Worked two-final session and the empirical tertile classification. Prints the
residual standard deviations and the standard buffer calculation behind the
38.5 min figure in section 5.3, so the number can be recomputed from the data.
"""
import os
import pandas as pd
import numpy as np
import common as C

df = pd.read_csv(os.path.join(C.DER, "Tour_TPP_sample_n25928.csv"))
df["cm"] = df.groupby(["discipline", "round"]).duration.transform("mean")
df["r"] = df.duration - df.cm
cv = df.groupby(["discipline", "round"]).r.var()

vMS = cv[("MS", "Final")]
vWD = cv[("WD", "Final")]
std_buf = 1.645 * np.sqrt(vMS + vWD)

q = pd.read_csv(os.path.join(C.DER, "TableS13_cell_quantiles.csv"))
q["bp95"] = (q.P95_dur - q.mean_dur).round(1)
c1, c2 = np.quantile(q.bp95, 1 / 3), np.quantile(q.bp95, 2 / 3)

lines = [
    "cell residual SD: MS Final=%.2f min, WD Final=%.2f min" % (
        np.sqrt(vMS), np.sqrt(vWD)),
    "residual variance: MS Final=%.2f, WD Final=%.2f" % (vMS, vWD),
    "standard independence buffer = 1.645*sqrt(%.2f+%.2f) = %.1f min" % (
        vMS, vWD, std_buf),
    "standard window = 116.8+15+%.1f = %.1f min" % (
        std_buf, 116.8 + 15 + std_buf),
    "tight=131.8  conservative=193.8",
    "tertile cutpoints %.1f / %.1f" % (c1, c2)]
for tier, cond in [
        ("A high", q.bp95 >= c2),
        ("B mid", (q.bp95 >= c1) & (q.bp95 < c2)),
        ("C low", q.bp95 < c1)]:
    sub = q[cond]
    lines.append("%s n=%d cells: %s" % (
        tier, len(sub), list(zip(sub.discipline, sub["round"], sub.bp95))))
C.write_lines("22_worked_example.txt", lines)
