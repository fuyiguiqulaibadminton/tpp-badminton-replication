# -*- coding: utf-8 -*-
"""
25_coverage_idle_curve.py
=========================
Build the continuous coverage-idle frontier for session planning. The standard
posture scales the independence SD by a multiplier z; sweeping z over a grid
gives the empirical coverage and the mean idle (slack) at each point, so event
organisers can pick a point on the curve rather than only one of three discrete
postures. No new data are required: the inputs are the calibrated session table
from 21_calibrate_session_buffer.py.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import common as C

PDF_META = {"CreationDate": r"D:20260101000000+08'00'",
            "ModDate": r"D:20260101000000+08'00'"}

cal = pd.read_csv(os.path.join(C.DER, "Session_buffer_calibration.csv"))
over = cal["over_mean"].to_numpy()
ind_sd = cal["ind_sd"].to_numpy()

# Sweep the SD multiplier z from 0 to 2.6 on a fine grid.
zs = np.round(np.arange(0.0, 2.6001, 0.05), 3)
rows = []
for z in zs:
    buf = z * ind_sd
    coverage = float((over <= buf).mean())
    idle = float(np.clip(buf - over, 0, None).mean())
    rows.append(dict(z=z, buffer_min=round(buf.mean(), 3),
                     coverage=round(coverage, 4), mean_idle=round(idle, 3)))
curve = pd.DataFrame(rows)
curve.to_csv(os.path.join(C.DER, "Session_coverage_idle_curve.csv"),
             index=False, encoding="utf-8-sig")

# Anchor the three reported postures for the figure.
tight_cov = float((over <= 0).mean())
std = curve.iloc[(curve["z"] - 1.645).abs().argmin()]
cons_buf = cal["sumP95_buffer"].to_numpy()
cons_cov = float((over <= cons_buf).mean())
cons_idle = float(np.clip(cons_buf - over, 0, None).mean())

fig, ax = plt.subplots(figsize=(9, 5.6))
ax.plot(curve["mean_idle"], curve["coverage"] * 100, "-", color="#2c74b3",
        lw=2.0, label="Coverage-idle frontier (z x independence SD)")
points = [
    (0.0, tight_cov * 100, "Tight (no buffer)", "#d95f5f"),
    (std["mean_idle"], std["coverage"] * 100, "Standard (z=1.645)", "#e8913a"),
    (cons_idle, cons_cov * 100, "Conservative (sum P95)", "#6ab565"),
]
for x, y, lab, c in points:
    ax.scatter(x, y, s=85, color=c, edgecolor="black", zorder=4)
    ax.annotate(lab, xy=(x, y), xytext=(x + 6, y - 5), fontsize=10.5,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#999"))
ax.set_xlabel("Mean idle time per session (min)", fontsize=13)
ax.set_ylabel("Coverage (%; sessions finishing within window)", fontsize=13)
ax.set_ylim(45, 101)
ax.tick_params(labelsize=12)
ax.grid(True, color="#ccc", lw=0.8, alpha=0.8)
ax.legend(loc="lower right", fontsize=11, framealpha=0.95)
fig.tight_layout()
out_dir = os.path.join(C.FIG, "recomputed")
fig.savefig(os.path.join(out_dir, "Figure7_coverage_idle.png"), dpi=300)
fig.savefig(os.path.join(out_dir, "Figure7_coverage_idle.pdf"), metadata=PDF_META)
plt.close(fig)

lines = ["coverage-idle frontier (n=%d sessions); selected z points:" % len(cal)]
for z in (0.0, 0.5, 1.0, 1.28, 1.645, 2.0, 2.58):
    r = curve.iloc[(curve["z"] - z).abs().argmin()]
    lines.append("  z=%.2f coverage=%.4f mean_idle=%.1f min" %
                 (r["z"], r["coverage"], r["mean_idle"]))
lines.append("conservative (sum P95) coverage=%.4f mean_idle=%.1f min" %
             (cons_cov, cons_idle))
C.write_lines("25_coverage_idle_curve.txt", lines)
