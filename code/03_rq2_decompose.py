# -*- coding: utf-8 -*-
"""
03_rq2_decompose.py
===================
RQ2 (Dataset B): decompose the 2018 -> 2025 change in mean match duration with
the initial-weight identity

    Delta T = (S0/60) Delta TPP  +  (TPP0/60) Delta S  +  (Delta TPP * Delta S / 60)

Confidence intervals come from a pairs bootstrap that resamples whole EVENTS
(tournaments) within each endpoint year, so matches nested in the same
tournament are kept together (10,000 replicates). An iid match-level bootstrap
is run only as a comparison (it is narrower and is not used in the text).
Repeated for each discipline.
"""
import os
import numpy as np
import pandas as pd
import common as C

d = C.tour_tpp_sample(C.load_world_tour())
d = d.rename(columns={"event": "event"})
rng = np.random.default_rng(C.SEED)
L = [f"Tour TPP-usable completed matches n = {len(d)} (paper 25,928)"]


def yearly(x):
    g = x.groupby("year")
    T = g["duration"].sum()
    S = g["Pts"].sum()
    n = g.size()
    return T, S, n


T, S, n = yearly(d)
for y in (2018, 2025):
    L.append(f"  {y}: n={n[y]}, mean duration={T[y]/n[y]:.3f} min, "
             f"aggregate TPP={60*T[y]/S[y]:.4f}, mean points={S[y]/n[y]:.4f}")


def decompose(T0, T1, S0, S1):
    tpp0, tpp1 = 60 * T0 / S0, 60 * T1 / S1
    dtpp, ds = tpp1 - tpp0, S1 - S0
    a = (S0 / 60) * dtpp
    b = (tpp0 / 60) * ds
    c = dtpp * ds / 60
    return a, b, c, dtpp, ds


mT0, mT1 = T[2018] / n[2018], T[2025] / n[2025]
mS0, mS1 = S[2018] / n[2018], S[2025] / n[2025]
a, b, cc, dtpp, ds = decompose(mT0, mT1, mS0, mS1)
tot = mT1 - mT0
L.append("")
L.append("POINT ESTIMATES 2018 -> 2025")
L.append(f"  Delta T = {tot:.3f} min")
L.append(f"  TPP component {a:.3f} ({a/tot*100:.1f}%) | scoring-frequency {b:.3f} "
         f"({b/tot*100:.1f}%) | interaction {cc:.3f} ({cc/tot*100:.1f}%)")
L.append(f"  Delta TPP = {dtpp:.3f} s/point ; Delta S = {ds:.3f} points")

cl = d.groupby(["year", "event"]).agg(
    T=("duration", "sum"), S=("Pts", "sum"), k=("duration", "size")).reset_index()
L.append("")
L.append("events per year: " + str({y: int((cl['year'] == y).sum())
                                    for y in sorted(d['year'].unique())}))

B = 10000


def bootstrap(mode):
    A, BB, CC, SH = [], [], [], []
    if mode == "cluster":
        c0 = cl[cl["year"] == 2018].reset_index(drop=True)
        c1 = cl[cl["year"] == 2025].reset_index(drop=True)
    m0 = d[d["year"] == 2018]
    m1 = d[d["year"] == 2025]
    for _ in range(B):
        if mode == "cluster":
            s0 = c0.iloc[rng.integers(0, len(c0), len(c0))]
            s1 = c1.iloc[rng.integers(0, len(c1), len(c1))]
            T0 = s0["T"].sum() / s0["k"].sum(); T1 = s1["T"].sum() / s1["k"].sum()
            S0 = s0["S"].sum() / s0["k"].sum(); S1 = s1["S"].sum() / s1["k"].sum()
        else:
            x0 = m0.iloc[rng.integers(0, len(m0), len(m0))]
            x1 = m1.iloc[rng.integers(0, len(m1), len(m1))]
            T0, T1 = x0["duration"].mean(), x1["duration"].mean()
            S0, S1 = x0["Pts"].mean(), x1["Pts"].mean()
        za, zb, zc, _, _ = decompose(T0, T1, S0, S1)
        t = T1 - T0
        A.append(za); BB.append(zb); CC.append(zc)
        SH.append(100 * za / t if t != 0 else np.nan)
    ci = lambda v: np.percentile(v, [2.5, 97.5])
    return ci(A), ci(BB), ci(CC), ci(pd.Series(SH).dropna())


cia, cib, cic, cish = bootstrap("cluster")
L.append("")
L.append(f"EVENT-CLUSTER bootstrap 95% CI ({B:,} resamples)")
L.append(f"  TPP component {a:.3f} [{cia[0]:.3f}, {cia[1]:.3f}]")
L.append(f"  scoring-frequency {b:.3f} [{cib[0]:.3f}, {cib[1]:.3f}]")
L.append(f"  interaction {cc:.3f} [{cic[0]:.3f}, {cic[1]:.3f}]")
L.append(f"  TPP share {a/tot*100:.1f}% [{cish[0]:.0f}, {cish[1]:.0f}]")

cia2, cib2, cic2, cish2 = bootstrap("iid")
L.append("")
L.append("IID match-level bootstrap (comparison only; narrower)")
L.append(f"  TPP component {a:.3f} [{cia2[0]:.3f}, {cia2[1]:.3f}] ; "
         f"share [{cish2[0]:.0f}, {cish2[1]:.0f}]")

# ------------------------------------------------------------- by discipline
rows = []
L.append("")
L.append("BY DISCIPLINE (point estimate + event-cluster 95% CI)")
for disc in ["MS", "WS", "MD", "WD", "XD"]:
    xd = d[d["discipline"] == disc]
    xcl = xd.groupby(["year", "event"]).agg(
        T=("duration", "sum"), S=("Pts", "sum"), k=("duration", "size")).reset_index()
    Tx, Sx, nx = yearly(xd)
    za, zb, zc, zdtpp, zds = decompose(Tx[2018]/nx[2018], Tx[2025]/nx[2025],
                                      Sx[2018]/nx[2018], Sx[2025]/nx[2025])
    tt = Tx[2025]/nx[2025] - Tx[2018]/nx[2018]
    c0 = xcl[xcl["year"] == 2018].reset_index(drop=True)
    c1 = xcl[xcl["year"] == 2025].reset_index(drop=True)
    A2, SH2 = [], []
    for _ in range(B):
        s0 = c0.iloc[rng.integers(0, len(c0), len(c0))]
        s1 = c1.iloc[rng.integers(0, len(c1), len(c1))]
        T0 = s0["T"].sum()/s0["k"].sum(); T1 = s1["T"].sum()/s1["k"].sum()
        S0 = s0["S"].sum()/s0["k"].sum(); S1 = s1["S"].sum()/s1["k"].sum()
        q0, _, _, _, _ = decompose(T0, T1, S0, S1); t2 = T1 - T0
        A2.append(q0); SH2.append(100*q0/t2 if t2 != 0 else np.nan)
    ea = np.percentile(A2, [2.5, 97.5]); esh = np.percentile(pd.Series(SH2).dropna(), [2.5, 97.5])
    rows.append(dict(discipline=disc, dT_min=round(tt, 2), dTPP=round(zdtpp, 2),
                     dS=round(zds, 2), TPP_share_pct=round(100*za/tt),
                     TPP_component_CI=f"[{ea[0]:.2f}, {ea[1]:.2f}]",
                     share_CI=f"[{esh[0]:.0f}, {esh[1]:.0f}]"))
    L.append(f"  {disc}: dT {tt:.2f} | TPP component {za:.2f} [{ea[0]:.2f},{ea[1]:.2f}] "
             f"| share {100*za/tt:.0f}% [{esh[0]:.0f},{esh[1]:.0f}]")

pd.DataFrame(rows).to_csv(os.path.join(C.DER, "Table4_decomposition_by_discipline.csv"),
                         index=False, encoding="utf-8-sig")

# --------------------------------------------- Table S4: annual T/S/T inputs
s4rows = []
for y in sorted(d["year"].unique()):
    g = d[d["year"] == y]
    s4rows.append(dict(
        year=int(y), n=len(g),
        mean_duration_min=round(g["duration"].mean(), 2),
        aggregate_TPP_sp=round(60 * g["duration"].sum() / g["Pts"].sum(), 2),
        mean_total_points=round(g["Pts"].mean(), 2)))
pd.DataFrame(s4rows).to_csv(os.path.join(C.DER, "TableS4_annual_TST.csv"),
                            index=False, encoding="utf-8-sig")
L.append("")
L.append("Table S4 annual inputs written (year, n, mean duration min, aggregate TPP, mean points)")

C.write_lines("03_RQ2_decompose.txt", L)
