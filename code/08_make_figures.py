# -*- coding: utf-8 -*-
"""
08_make_figures.py
==================
Regenerates all seven figures from the raw data (Fig 1, 2, 3, 4, 5, 6, 7).
Outputs are written to figures/recomputed/ so the exact manuscript copies in
figures/ are never overwritten; the two sets should agree visually.

Fig 1 is an operational schematic (not a validated decomposition).
Fig 2 fits the piecewise line on the annual aggregates with the knot at 2017.
Fig 4/6 use the bootstrap point/CI values produced by 03_rq2_decompose.py.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch
import common as C

OUT = os.path.join(C.FIG, "recomputed")
os.makedirs(OUT, exist_ok=True)
g = C.GAMECOLS

# ============================================================ FIGURE 1
fig, ax = plt.subplots(figsize=(11, 4.2)); ax.set_xlim(0, 11); ax.set_ylim(0, 4.2); ax.axis("off")
ax.text(5.5, 3.85, "Total match time T (minutes, BWF MATCH DURATION field)",
        ha="center", va="center", fontsize=17, fontweight="bold")
ax.add_patch(FancyBboxPatch((0.35, 1.55), 10.3, 1.55,
             boxstyle="round,pad=0.02,rounding_size=0.12", facecolor="#e6e6e6", edgecolor="black", lw=1.4))
for x, w, c, txt, tc, fs in [(0.75, 3.0, "#d95f5f", "Rally\nplay", None, 12.5),
                         (3.75, 3.9, "#5b94bf", "Between-rally pauses\n(retrieval, towelling,\nchallenges, preparation)", "white", 11),
                         (7.65, 2.9, "#6ab565", "Rule breaks\n(11-pt, inter-game,\nmedical)", "white", 11)]:
    ax.add_patch(Rectangle((x, 1.75), w, 1.15, facecolor=c, edgecolor="none"))
    ax.text(x + w/2, 2.325, txt, ha="center", va="center", fontsize=fs,
            color=tc if tc else "white")
for x in [2.25, 5.7, 9.1]:
    ax.add_patch(FancyArrowPatch((x, 1.25), (x, 1.5), arrowstyle="-|>",
                 mutation_scale=14, color="#777", lw=1.3))
ax.add_patch(FancyBboxPatch((0.9, 0.22), 9.2, 0.66,
             boxstyle="round,pad=0.02,rounding_size=0.08", facecolor="#fff7dc", edgecolor="#f2b600", lw=1.6))
ax.text(5.5, 0.55, r"S points scored  ->  TPP = 60T / S  (seconds per point, official recorded match clock)",
        ha="center", va="center", fontsize=13, style="italic")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "Figure1_TPP_schematic.png"), dpi=300)
fig.savefig(os.path.join(OUT, "Figure1_TPP_schematic.pdf")); plt.close(fig)

# ============================================================ FIGURE 2
df = C.load_world_championships()
df["S"] = df[g].fillna(0).sum(axis=1)
dd = df[(df["status"] == "完赛") & (df["year"] >= 2006) & (df["duration"] >= 10) & (df["duration"] <= 180)]
agg = dd.groupby("year").apply(lambda z: 60*z["duration"].sum()/z["S"].sum()).reset_index()
agg.columns = ["year", "tpp"]
years, tpp = agg.year.values, agg.tpp.values
yc = years - 2017; ycp = yc*(years >= 2018).astype(int)
X = np.column_stack([np.ones_like(years, dtype=float), yc, ycp])
b0, b1, b2 = np.linalg.lstsq(X, tpp, rcond=None)[0]
fig, ax = plt.subplots(figsize=(9, 4.8))
ax.add_patch(Rectangle((2004.7, 23.2), 1.25, 11.6, color="#e8e8e8", zorder=0))
ax.text(2005.32, 25.6, "side-out\nscoring\nexcluded", ha="center", va="center", fontsize=9, color="#777")
ax.axvline(2017.5, color="#999", ls=":", lw=1.4)
ax.text(2017.38, 25.0, "2017/2018\nslope break", fontsize=10, color="#777", ha="right")
ax.plot(years, tpp, "-o", color="black", lw=1.8, ms=8, label="Observed aggregate TPP", zorder=3)
ax.plot(np.linspace(2006.3, 2017, 200), b0 + b1*(np.linspace(2006.3, 2017, 200)-2017), "--", color="red", lw=2.4, zorder=2)
ax.plot(np.linspace(2017, 2026, 300), b0 + (b1+b2)*(np.linspace(2017, 2026, 300)-2017),
        "--", color="red", lw=2.4, label="Piecewise linear fit", zorder=2)
ax.set_xlim(2004.5, 2027); ax.set_ylim(23.2, 34.8)
ax.set_xlabel("Year", fontsize=14); ax.set_ylabel("TPP (s/point)", fontsize=14)
ax.tick_params(labelsize=13); ax.grid(True, color="#ccc", lw=0.8, alpha=0.8)
ax.legend(loc="lower right", framealpha=0.9, fontsize=13)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "Figure2_WC_trend.png"), dpi=300)
fig.savefig(os.path.join(OUT, "Figure2_WC_trend.pdf")); plt.close(fig)

# ============================================================ FIGURE 3
tour = C.tour_tpp_sample(C.load_world_tour())
ta = tour.groupby("year").apply(lambda z: 60*z["duration"].sum()/z["Pts"].sum())
yrs = np.array(ta.index, dtype=float); vals = ta.values
vd = dict(zip(yrs.astype(int), vals))
slope = np.polyfit(yrs, vals, 1)[0]
fig, ax = plt.subplots(figsize=(9, 4.8))
for y, v in zip(yrs, vals):
    ax.scatter(y, v, s=70, facecolors="white" if y == 2020 else "#2c74b3",
               edgecolors="#2c74b3", zorder=3)
ax.plot(yrs, vals, "-", color="#2c74b3", lw=1.6, zorder=2)
xx = np.linspace(2018, 2025, 50)
ax.plot(xx, np.polyval(np.polyfit(yrs, vals, 1), xx), "--", color="red", lw=2,
        label=f"Linear fit: +{slope:.2f} s/yr")
ax.annotate("empty-stadium\nsample, n=879", xy=(2020, vd[2020]), xytext=(2020.2, 31.2),
            fontsize=9, color="#777")
ax.set_xlabel("Year", fontsize=14); ax.set_ylabel("Aggregate TPP (s/point)", fontsize=14)
ax.tick_params(labelsize=13); ax.grid(True, color="#ccc", lw=0.8, alpha=0.8)
ax.legend(fontsize=12)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "Figure3_Tour_trend.png"), dpi=300)
fig.savefig(os.path.join(OUT, "Figure3_Tour_trend.pdf")); plt.close(fig)

# ============================================================ FIGURE 4
labels = ["TPP component\n(higher clock time\nper point)", "Scoring-frequency component\n(more points\nper match)", "Interaction"]
v4 = [3.10, 0.24, 0.02]; lo4 = [1.82, -0.38, -0.03]; hi4 = [4.28, 0.87, 0.07]
colors = ["#d95f5f", "#5b94bf", "#6ab565"]
err = [[v-l for v, l in zip(v4, lo4)], [h-v for v, h in zip(v4, hi4)]]
fig, ax = plt.subplots(figsize=(8.4, 5.2)); x = np.arange(3)
ax.bar(x, v4, width=0.6, color=colors, edgecolor="black", zorder=3)
ax.errorbar(x, v4, yerr=err, fmt="none", ecolor="black", capsize=7, lw=1.6, zorder=4)
for i, v in enumerate(v4):
    ax.text(i, v + err[1][i] + 0.12, f"{v:.2f}", ha="center", fontsize=13, fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=12)
ax.set_ylabel("Minutes", fontsize=14); ax.set_ylim(0, 4.9)
ax.grid(True, axis="y", color="#ccc", zorder=0)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "Figure4_decomposition.png"), dpi=300)
fig.savefig(os.path.join(OUT, "Figure4_decomposition.pdf")); plt.close(fig)

# ============================================================ FIGURE 5
rounds = ["R32", "R16", "QF", "SF", "Final"]; discs = ["MS", "WS", "MD", "WD", "XD"]
M = np.zeros((5, 5))
for i, k in enumerate(discs):
    for j, rd in enumerate(rounds):
        cc = tour[(tour["discipline"] == k) & (tour["round"] == rd)]
        M[i, j] = 60*cc["duration"].sum()/cc["Pts"].sum()
fig, ax = plt.subplots(figsize=(9, 5.6))
im = ax.imshow(M, cmap="YlOrRd", aspect="auto")
ax.set_xticks(range(5)); ax.set_xticklabels(rounds, fontsize=12)
ax.set_yticks(range(5)); ax.set_yticklabels(["Men's Singles", "Women's Singles",
           "Men's Doubles", "Women's Doubles", "Mixed Doubles"], fontsize=11)
for i in range(5):
    for j in range(5):
        ax.text(j, i, f"{M[i, j]:.1f}", ha="center", va="center", fontsize=11)
cb = fig.colorbar(im, ax=ax); cb.set_label("TPP (s/point)", fontsize=12)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "Figure5_heatmap.png"), dpi=300)
fig.savefig(os.path.join(OUT, "Figure5_heatmap.pdf")); plt.close(fig)

# ============================================================ FIGURE 6
data = {
 "MS": ("#d95f5f", "o", [(34.9, 2.6), (36.2, 1.4), (37.5, 2.6), (38.9, 2.6), (40.0, 0.6)]),
 "WS": ("#e8913a", "s", [(30.4, 2.2), (31.8, 1.7), (33.6, 2.0), (35.3, 2.9), (36.7, 2.3)]),
 "MD": ("#4a7db5", "^", [(28.5, 1.3), (29.6, 0.7), (30.8, 0.1), (31.6, 0.3), (32.4, 1.1)]),
 "WD": ("#5aa85a", "D", [(31.4, 1.6), (33.8, 1.3), (36.8, 0.9), (39.3, 1.4), (40.8, 0.6)]),
 "XD": ("#9b6bb5", "v", [(27.7, 1.2), (29.2, 0.4), (30.9, 0.6), (32.6, 0.3), (33.4, 0.0)])}
fig, ax = plt.subplots(figsize=(9, 5.6))
for k, (c, mk, pts) in data.items():
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    ax.plot(xs, ys, "-", color=c, lw=1.5, alpha=0.7, zorder=2)
    ax.scatter(xs, ys, marker=mk, color=c, s=70, edgecolor="black", label=k, zorder=3)
ax.axvline(31.6, color="#888", ls=":", lw=1.6); ax.axhline(1.49, color="#888", ls=":", lw=1.6)
ax.text(31.6, 3.55, "overall mean TPP = 31.6", rotation=90, va="top", ha="right",
        fontsize=9.5, color="#666", bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.7))
ax.text(34.2, 1.62, "overall retirement = 1.49%", fontsize=9.5, color="#666",
        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.7))
ax.set_xlabel("TPP (s/point)", fontsize=14); ax.set_ylabel("Retirement rate (%)", fontsize=14)
ax.set_xlim(26.5, 41.5); ax.set_ylim(-0.2, 3.6)
ax.grid(True, color="#ccc", alpha=0.8)
ax.legend(title="Discipline", ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.11),
          fontsize=12, title_fontsize=12, frameon=False)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "Figure6_TPP_retirement.png"), dpi=300, bbox_inches="tight")
fig.savefig(os.path.join(OUT, "Figure6_TPP_retirement.pdf"), bbox_inches="tight"); plt.close(fig)

# ============================================================ FIGURE 7
fig, ax = plt.subplots(figsize=(11, 7)); ax.set_xlim(0, 11); ax.set_ylim(0, 7); ax.axis("off")
def box(x, y, w, h, text, fc, fs=11.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                 facecolor=fc, edgecolor="black", lw=1.3))
    ax.text(x+w/2, y+h/2, text, ha="center", va="center", fontsize=fs)
def arrow(x, y1, y2):
    ax.annotate("", xy=(x, y2), xytext=(x, y1), arrowprops=dict(arrowstyle="-|>", lw=1.4, color="#555"))
def excl(x, y, t):
    ax.text(x, y, t, ha="left", va="center", fontsize=10.5, color="#b03030")
cx = 2.6
box(cx-1.7, 6.1, 3.4, 0.7, "World Championships 2005-2026\nn = 4,250 matches", "#dfe9f5")
arrow(cx, 6.1, 5.75); excl(cx+1.85, 5.92, "-79 walkovers")
box(cx-1.7, 5.05, 3.4, 0.7, "n = 4,171", "#eef3fa"); arrow(cx, 5.05, 4.7); excl(cx+1.85, 4.87, "-36 retirements")
box(cx-1.7, 4.0, 3.4, 0.7, "Completed matches n = 4,135", "#eef3fa"); arrow(cx, 4.0, 3.65)
excl(cx+1.85, 3.82, "-263 side-out (2005, descriptive only)")
box(cx-1.7, 2.95, 3.4, 0.7, "Completed rally-point n = 3,872", "#eef3fa"); arrow(cx, 2.95, 2.6)
excl(cx+1.85, 2.77, "-4 implausible durations")
box(cx-1.7, 1.85, 3.4, 0.75, "Trend-analysis sample\nn = 3,868", "#d9ecd4")
cx = 7.9
box(cx-2.0, 6.1, 4.0, 0.7, "World Tour Super 300-1000 2018-2025\nn = 26,597 matches", "#fdeede", fs=10.5)
arrow(cx, 6.1, 5.75); excl(cx+2.05, 5.92, "-274 walkovers")
box(cx-2.0, 5.05, 4.0, 0.7, "n = 26,323", "#fdf3e8"); arrow(cx, 5.05, 4.7); excl(cx+2.05, 4.87, "-392 retirements")
box(cx-2.0, 4.0, 4.0, 0.7, "Completed matches n = 25,931", "#fdf3e8"); arrow(cx, 4.0, 3.65)
excl(cx+2.05, 3.82, "-3 missing/unusable TPP inputs")
box(cx-2.0, 2.95, 4.0, 0.75, "Tour TPP analysis sample\nn = 25,928", "#f3e0c8")
ax.text(5.5, 1.05, "Combined: 30,847 elite matches; 30,059 with a usable TPP input\n"
        "(25,928 Tour + 3,868 WC rally-point + 263 side-out, descriptive only)",
        ha="center", va="center", fontsize=12, fontweight="bold")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "Figure7_sample_flow.png"), dpi=300)
fig.savefig(os.path.join(OUT, "Figure7_sample_flow.pdf")); plt.close(fig)

print("All seven figures regenerated into", OUT)
