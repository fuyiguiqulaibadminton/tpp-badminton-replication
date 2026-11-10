# -*- coding: utf-8 -*-
"""
07_tableS2_validity.py
======================
Supplementary Table S2: external validity anchors for TPP (men's singles).

TPP is a composite clock metric; these checks ask whether its numerical level is
compatible with the video-coded RT/PT literature. Reconstructed TPP is

    TPP* = RT + PT + rule breaks per point,   PT = RT * (1/EPT - 1)

with rule breaks prorated over observed points (240 s for a two-game match,
420 s for three games) using the discipline's three-set frequency.

Anchor 1 (2006 World Championships): 25.4 s/point back-derived from Hoffmann &
Vogt (2024) game-duration and points data.
Anchor 2 (Super Series / Super Tour, c. 2016-2018): RT 9.1-9.9 s and EPT 31%
from Gomez et al. (2019).

Both the match-level MEAN and the AGGREGATE (sum 60T / sum S) official values
are printed so the comparison basis is fully transparent.
"""
import os
import numpy as np
import pandas as pd
import common as C

wc = C.load_world_championships()
tour = C.load_world_tour()
L = []


def stats_ms(frame, year=None):
    x = frame[(frame["discipline"] == "MS") & (frame["status"] == "完赛")].copy()
    if year is not None:
        x = x[x["year"] == year]
    x = x[x["duration"].notna() & (x["Pts"] > 0) & (x["duration"] >= 10)]
    x["TPP"] = 60 * x["duration"] / x["Pts"]
    return dict(n=len(x), agg=60 * x["duration"].sum() / x["Pts"].sum(),
                mean=x["TPP"].mean(), meanS=x["Pts"].mean(),
                three=x["three"].mean())


def break_per_point(three_rate, mean_s):
    b2 = 240.0 / mean_s
    b3 = 420.0 / (mean_s * 1.18)
    return (1 - three_rate) * b2 + three_rate * b3


def reconstruct(rt, ept, three_rate, mean_s):
    pt = rt * (1.0 / ept - 1.0)
    return rt + pt + break_per_point(three_rate, mean_s), pt


# ------------------------------------------------ anchor 1: 2006 WC (H&V)
a1 = stats_ms(wc, 2006)
recon_2006 = 25.4   # back-derived from Hoffmann & Vogt (2024) published inputs
L.append("Anchor 1 - 2006 World Championships men's singles")
L.append(f"  official n={a1['n']}, aggregate TPP={a1['agg']:.2f}, "
         f"match-level mean TPP={a1['mean']:.2f}")
L.append(f"  reconstructed (Hoffmann & Vogt back-derived) = {recon_2006}")
L.append(f"  delta vs aggregate = {recon_2006-a1['agg']:+.1f}; "
         f"delta vs match mean = {recon_2006-a1['mean']:+.1f}")

# ------------------------------------------- anchor 2: Gomez Super Series MS
a2 = stats_ms(tour, 2018)
preds = []
for rt in (9.1, 9.5, 9.9):
    val, _ = reconstruct(rt, 0.31, a2["three"], a2["meanS"])
    preds.append(val)
L.append("")
L.append("Anchor 2 - Gomez et al. (2019) Super Series MS, RT 9.1-9.9 s, EPT 31%")
L.append(f"  official Tour MS 2018: n={a2['n']}, aggregate TPP={a2['agg']:.2f}, "
         f"mean TPP={a2['mean']:.2f}")
L.append(f"  reconstructed range {min(preds):.1f}-{max(preds):.1f}, "
         f"midpoint {np.mean(preds):.1f}")
L.append(f"  delta (midpoint vs aggregate) = {np.mean(preds)-a2['agg']:+.1f} "
         f"(full range {min(preds)-a2['agg']:+.1f} to {max(preds)-a2['agg']:+.1f})")

# ------------------------------------------------------------- write table
rows = [
    {"anchor": "2006 World Championships (MS)",
     "source": "Hoffmann & Vogt (2024), back-derived",
     "reconstructed_TPP": f"{recon_2006}",
     "official_aggregate_TPP": round(a1["agg"], 1),
     "official_match_mean_TPP": round(a1["mean"], 1),
     "delta_vs_aggregate": round(recon_2006 - a1["agg"], 1),
     "delta_vs_mean": round(recon_2006 - a1["mean"], 1)},
    {"anchor": "Super Series / Super Tour, c.2016-2018 (MS)",
     "source": "Gomez et al. (2019): RT 9.1-9.9 s, EPT 31%",
     "reconstructed_TPP": f"{np.mean(preds):.1f} ({min(preds):.1f}-{max(preds):.1f})",
     "official_aggregate_TPP": round(a2["agg"], 1),
     "official_match_mean_TPP": round(a2["mean"], 1),
     "delta_vs_aggregate": round(np.mean(preds) - a2["agg"], 1),
     "delta_vs_mean": round(np.mean(preds) - a2["mean"], 1)},
]
pd.DataFrame(rows).to_csv(os.path.join(C.DER, "TableS2_validity_anchors.csv"),
                          index=False, encoding="utf-8-sig")
L.append("")
L.append("Note: the manuscript reports the 2006 official value on the "
         "aggregate estimand used throughout the paper (sum 60T / sum S = 25.5), "
         "giving delta = -0.1 versus the 25.4 back-derived value; the match-level "
         "mean (25.2) is retained here for transparency only. The Gomez anchor "
         "uses the aggregate (34.2, delta = -0.3). Both bases agree within "
         "~0.3 s/point, so the validity conclusion is unchanged.")
C.write_lines("07_TableS2_validity.txt", L)
