# -*- coding: utf-8 -*-
"""
run_all.py
==========
Reproduces every number and figure in the manuscript, in order. Run from the
code/ directory (or from anywhere; paths are resolved relative to this file):

    python run_all.py

Outputs:
  data/derived/  analysis-ready CSV tables (Tables 1-8, S1-S14 and the
                 session reconstruction and calibration tables)
  outputs/       plain-text logs of every computed statistic
  figures/recomputed/  regenerated PNG + PDF copies of Figures 1-7 and Figure S1

Step 11 (11_elo_control.py) additionally requires the external tables
matches.xlsx / players.xlsx / tournaments.xlsx under data/raw_external/
(Sun & Zhang, 2026, Harvard Dataverse, CC BY 4.0); see
data/raw_external/SOURCE_AND_LICENSE.txt.
"""
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

STEPS = [
    "01_build_samples.py",
    "02_rq1_trend.py",
    "03_rq2_decompose.py",
    "04_rq3_noncompletion.py",
    "05_rq4_alternatives.py",
    "06_tableS1_logistic.py",
    "07_tableS2_validity.py",
    "08_make_figures.py",
    "09_composition_ledger.py",
    "10_sensitivity.py",
    "11_elo_control.py",
    "12_extra_sensitivity.py",
    "13_subperiod_sensitivity.py",
    "14_compute_quantiles.py",
    "15_build_sessions.py",
    "16_backtest_sessions.py",
    "17_holdout_validation.py",
    "18_session_independence.py",
    "19_baseline_compare.py",
    "20_bootstrap_quantile_ci.py",
    "21_calibrate_session_buffer.py",
    "22_worked_example.py",
    "23_holdout_drift.py",
    "24_dependence_perturbation.py",
    "25_coverage_idle_curve.py",
    "28_wild_cluster_bootstrap.py",
]

for i, step in enumerate(STEPS, 1):
    print("\n" + "=" * 78)
    print(f"STEP {i}/{len(STEPS)}: {step}")
    print("=" * 78)
    runpy.run_path(os.path.join(HERE, step), run_name="__main__")

print("\nAll steps finished. See outputs/ for statistics and data/derived/ for tables.")
