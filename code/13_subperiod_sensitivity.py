# -*- coding: utf-8 -*-
"""
13_subperiod_sensitivity.py
===========================
Recording-artefact robustness check (public fields only, no video).

The Tour panel 2018-2025 spans the COVID-disrupted seasons 2020-2021. To
address the possibility that the Tour trend is driven by a software/reporting
change or by the pandemic seasons rather than a persistent per-point-clock
increase, we refit the *exact* main Tour specification
    TPP ~ year + C(discipline) + C(round), year-clustered SE
on two same-rules subwindows:
    2021-2025 (rules unchanged since the 2018 service-height reform;
               includes the partial 2021 calendar, n=1,485 matches in raw)
    2022-2025 (full post-pandemic calendars only)
These subwindows are exploratory: with only 5 or 4 year clusters, clustered
inference is underpowered, so they are not used as primary evidence.
"""
import os
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import common as cm

L = []
tour = cm.tour_tpp_sample(cm.load_world_tour())


def tour_fit(d, label):
    d = d.copy()
    d["yr"] = d["year"] - d["year"].min()
    m = smf.ols("TPP ~ yr + C(discipline) + C(round)", data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d["year"]})
    slope = m.params["yr"]
    se = m.bse["yr"]
    p = m.pvalues["yr"]
    years = sorted(d["year"].unique())
    first = d.loc[d["year"] == years[0], "TPP"].mean()
    last = d.loc[d["year"] == years[-1], "TPP"].mean()
    row = dict(check=label, window=f"{years[0]}-{years[-1]}",
               n=len(d), year_clusters=len(years),
               slope=round(slope, 3), SE=round(se, 3), p=round(p, 4),
               mean_TPP_first=round(first, 2), mean_TPP_last=round(last, 2))
    L.append(
        f"Tour {label} ({years[0]}-{years[-1]}): n={len(d)}, "
        f"clusters={len(years)}, slope={slope:.3f} (SE {se:.3f}, p={p:.4g}), "
        f"mean TPP {first:.1f}->{last:.1f}")
    return row


rows = []
# main specification, full window (for within-table comparison)
rows.append(tour_fit(tour, "full 2018-2025 (main)"))
rows.append(tour_fit(tour[tour["year"] >= 2021].copy(),
                     "2021-2025 same-rules subwindow"))
rows.append(tour_fit(tour[tour["year"] >= 2022].copy(),
                     "2022-2025 full post-pandemic subwindow"))

out = pd.DataFrame(rows)
out.to_csv(os.path.join(cm.DER, "TableS12_subperiod_sensitivity.csv"),
           index=False, encoding="utf-8-sig")
L.append("")
L.append("Table S12 rows:")
L.append(out.to_string(index=False))
L.append("")
L.append("Note: exploratory subwindows with 5 / 4 year clusters; clustered SE "
         "underpowered. Specification identical to the main Tour fit "
         "(discipline + round fixed effects, year-clustered SE).")
cm.write_lines("13_subperiod_sensitivity.txt", L)
print("\n".join(L))
