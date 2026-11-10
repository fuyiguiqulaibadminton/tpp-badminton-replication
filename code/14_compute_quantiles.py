# -*- coding: utf-8 -*-
"""
14_compute_quantiles.py
=======================
Discipline-by-round empirical quantiles of TPP and match duration (Table S13).
Writes the cell lookup table that every session-planning script uses.
"""
import os
import pandas as pd
import common as C

df = pd.read_csv(os.path.join(C.DER, "Tour_TPP_sample_n25928.csv"))
disc = ["MS", "WS", "MD", "WD", "XD"]
rnds = ["R32", "R16", "QF", "SF", "Final"]
rows = []
for di in disc:
    for r in rnds:
        g = df[(df.discipline == di) & (df["round"] == r)]
        if len(g) == 0:
            continue
        rows.append(dict(discipline=di, round=r, n=len(g),
                         mean_TPP=round(g.TPP.mean(), 1),
                         P90_TPP=round(g.TPP.quantile(.90), 1),
                         P95_TPP=round(g.TPP.quantile(.95), 1),
                         mean_dur=round(g.duration.mean(), 1),
                         P90_dur=round(g.duration.quantile(.90), 1),
                         P95_dur=round(g.duration.quantile(.95), 1)))
out = pd.DataFrame(rows)
out.to_csv(os.path.join(C.DER, "TableS13_cell_quantiles.csv"),
           index=False, encoding="utf-8-sig")

C.write_lines("14_compute_quantiles.txt", [
    "Table S13 cell quantiles: %d cells" % len(out),
    "overall mean points/match: %.2f" % df.Pts.mean()])
print(out.to_string(index=False))
