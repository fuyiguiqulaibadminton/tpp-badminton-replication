# -*- coding: utf-8 -*-
"""
04_rq3_noncompletion.py
=======================
RQ3 (Dataset B): in-match retirement (RET) and pre-match walkover (WO) rates,
the discipline x round TPP / retirement matrix (Table 6), the event-level
2018-vs-2025 TPP table (Table 5), and the cell-level Spearman association.

Conventions (see manuscript section 3.2):
  RET% denominator = completed + retired matches (walk-overs excluded)
  WO%  denominator = all scheduled draw entries
"""
import os
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import common as C

tour = C.load_world_tour()
tpp = C.tour_tpp_sample(tour)
L = []

n_comp = int((tour["status"] == "完赛").sum())
n_ret = int((tour["status"] == "RET").sum())
n_wo = int((tour["status"] == "WO").sum())
ret_pct = 100 * n_ret / (n_comp + n_ret)
wo_pct = 100 * n_wo / len(tour)
L.append(f"completed {n_comp}, RET {n_ret}, WO {n_wo}")
L.append(f"overall in-match retirement rate = {ret_pct:.2f}%")
L.append(f"overall pre-match walkover rate  = {wo_pct:.2f}%")

L.append("")
L.append("RET% by discipline (denominator completed+RET):")
disc_rows = []
for k in ["MS", "WS", "MD", "WD", "XD"]:
    sub = tour[tour["discipline"] == k]
    c = int((sub["status"] == "完赛").sum()); r = int((sub["status"] == "RET").sum())
    disc_rows.append((k, 100 * r / (c + r)))
    L.append(f"  {k}: {100*r/(c+r):.2f}%")

# ------------------------------------------------- discipline x round matrix
rounds = ["R32", "R16", "QF", "SF", "Final"]
discs5 = ["MS", "WS", "MD", "WD", "XD"]
mat_tpp = pd.DataFrame(index=discs5, columns=rounds, dtype=float)   # full precision
mat_ret = pd.DataFrame(index=discs5, columns=rounds, dtype=float)
mat_n = pd.DataFrame(index=discs5, columns=rounds, dtype=int)
for k in discs5:
    for rd in rounds:
        cell = tour[(tour["discipline"] == k) & (tour["round"] == rd)]
        cc = cell[cell["status"] == "完赛"]
        cc = cc[cc["duration"].notna() & cc["Pts"].notna() & (cc["Pts"] > 0)]
        rr = int((cell["status"] == "RET").sum())
        mat_tpp.loc[k, rd] = 60 * cc["duration"].sum() / cc["Pts"].sum()
        mat_ret.loc[k, rd] = 100 * rr / (len(cc) + rr)
        mat_n.loc[k, rd] = len(cc)

# Spearman on the FULL-PRECISION cell values (rounding is only for display)
flat = pd.DataFrame({"TPP": mat_tpp.values.flatten().astype(float),
                     "RET": mat_ret.values.flatten().astype(float)})
rho, p = spearmanr(flat["TPP"], flat["RET"])
L.append("")
L.append(f"discipline x round cells = {len(flat)}; Spearman rho = {rho:.2f} "
         "(descriptive only; the cells are aggregated from the same matches and are not independent)")
L.append("minimum completed-match cell n = %d" % int(mat_n.values.min()))

# write Table 6 (TPP rounded to 1 decimal / RET% rounded to 1 decimal)
t6 = mat_tpp.round(1).astype(str) + " / " + mat_ret.round(1).astype(str)
t6.insert(0, "discipline", t6.index)
t6.to_csv(os.path.join(C.DER, "Table6_TPP_retirement_matrix.csv"),
          index=False, encoding="utf-8-sig")

# ------------------------------------------------- event-level table (Table 5)
def agg_tpp(g):
    return 60 * g["duration"].sum() / g["Pts"].sum()

L.append("")
L.append("TPP by event level, 2018 vs 2025 (aggregate | match-level mean):")
t5rows = []
for lv in ["Super 300", "Super 500", "Super 750", "Super 1000"]:
    row = {"level": lv}
    for y in (2018, 2025):
        g = tpp[(tpp["level"] == lv) & (tpp["year"] == y)]
        row[f"{y}_aggregate"] = round(agg_tpp(g), 1)
        row[f"{y}_match_mean"] = round((60 * g["duration"] / g["Pts"]).mean(), 1)
    t5rows.append(row)
    L.append(f"  {lv}: 2018 {row['2018_aggregate']} (agg) / {row['2018_match_mean']} (mean)"
             f" -> 2025 {row['2025_aggregate']} (agg) / {row['2025_match_mean']} (mean)")
pd.DataFrame(t5rows).to_csv(os.path.join(C.DER, "Table5_level_TPP.csv"),
                            index=False, encoding="utf-8-sig")

# eight-year TPP by level (text quotes the match-level means 30.4/31.3/33.3/32.8)
L.append("")
L.append("Eight-year TPP by level (aggregate | match-level mean):")
for lv in ["Super 300", "Super 500", "Super 750", "Super 1000"]:
    g = tpp[tpp["level"] == lv]
    L.append(f"  {lv}: {agg_tpp(g):.1f} (agg) / {(60*g['duration']/g['Pts']).mean():.1f} (mean)")

C.write_lines("04_RQ3_noncompletion.txt", L)
print("\nTable 6 (TPP / RET%):\n", t6.to_string(index=False))
