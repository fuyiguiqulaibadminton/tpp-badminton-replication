# -*- coding: utf-8 -*-
"""
01_build_samples.py
===================
Clean the two raw workbooks, construct the analysis samples, and write the
derived datasets that every later script uses. Also prints the sample-flow
closure (the numbers behind Figure 7).
"""
import os
import pandas as pd
import common as C

wc = C.load_world_championships()
tour = C.load_world_tour()

# ---------------------------------------------------------------- Dataset A
A_total = len(wc)
A_wo = int((wc["status"] == "WO").sum())
A_ret = int((wc["status"] == "RET").sum())
A_comp = wc[wc["status"] == "完赛"]
A_2005 = int((A_comp["year"] == 2005).sum())
A_comp_rp = A_comp[A_comp["year"] >= 2006]
A_impl = int((A_comp_rp["duration"] < 10).sum())          # 4 implausible durations
A_rq1 = len(A_comp_rp) - A_impl

# ---------------------------------------------------------------- Dataset B
B_total = len(tour)
B_wo = int((tour["status"] == "WO").sum())
B_ret = int((tour["status"] == "RET").sum())
B_comp = tour[tour["status"] == "完赛"]
B_no_tpp = int((B_comp["duration"].isna() | B_comp["Pts"].isna()
                | (B_comp["Pts"] <= 0)).sum())
B_tpp = len(B_comp) - B_no_tpp

lines = []
lines.append("=== Dataset A: World Championships 2005-2026 ===")
lines.append(f"total {A_total} | WO {A_wo} | RET {A_ret} | completed {len(A_comp)}")
lines.append(f"completed 2005 side-out (descriptive) {A_2005} | "
             f"implausible duration (<10 min) {A_impl} | RQ1 rally-point n = {A_rq1}")
lines.append("")
lines.append("=== Dataset B: World Tour Super 300-1000, 2018-2025 ===")
lines.append(f"total {B_total} | WO {B_wo} | RET {B_ret} | completed {len(B_comp)}")
lines.append(f"completed missing/unusable TPP input {B_no_tpp} | TPP sample n = {B_tpp}")
lines.append("")
lines.append("=== Closure ===")
lines.append(f"combined elite matches = {A_total + B_total} (paper 30,847)")
lines.append(f"usable TPP inputs = {B_tpp + A_rq1 + A_2005} "
             f"= {B_tpp} Tour + {A_rq1} WC rally-point + {A_2005} side-out (paper 30,059)")
C.write_lines("01_sample_flow.txt", lines)

# ------------------------------------------------------- derived data sets
rq1 = C.wc_rq1_sample(wc)
tpp_b = C.tour_tpp_sample(tour)

# Table 1: aggregate / mean / median TPP by World Championship year
comp_valid = wc[(wc["status"] == "完赛") & wc["duration"].notna()
                & (wc["Pts"] > 0) & (wc["duration"] >= 10)].copy()
comp_valid["TPP"] = C.tpp(comp_valid["duration"], comp_valid["Pts"])
rows = []
for y, g in comp_valid.groupby("year"):
    rows.append(dict(year=int(y), n=len(g),
                     agg_TPP=round(60 * g["duration"].sum() / g["Pts"].sum(), 1),
                     mean_TPP=round(g["TPP"].mean(), 1),
                     median_TPP=round(g["TPP"].median(), 1)))
table1 = pd.DataFrame(rows)
table1.to_csv(os.path.join(C.DER, "Table1_WC_annual_TPP.csv"),
              index=False, encoding="utf-8-sig")

rq1.to_csv(os.path.join(C.DER, "WC_RQ1_sample_n3868.csv"),
           index=False, encoding="utf-8-sig")
tpp_b.to_csv(os.path.join(C.DER, "Tour_TPP_sample_n25928.csv"),
             index=False, encoding="utf-8-sig")

# Full status-labelled master (used by RQ3 / Table S1)
tour.to_csv(os.path.join(C.DER, "Tour_all_status_n26597.csv"),
            index=False, encoding="utf-8-sig")
wc.to_csv(os.path.join(C.DER, "WC_all_n4250.csv"),
          index=False, encoding="utf-8-sig")

print("\nDerived datasets written to", C.DER)
print(table1.to_string(index=False))
