# -*- coding: utf-8 -*-
"""
28_wild_cluster_bootstrap.py
============================
Wild cluster bootstrap for the two slope tests under few clusters.

  * World Championships post-2018 slope (G = 16 year clusters)
  * World Tour annual slope (G = 8 year clusters)

For each model we report the CRVE Wald statistic and its wild-cluster-bootstrap
p-value under two weight sets: Rademacher (two-point) and Webb (six-point). The
Webb weights are additionally reported because G = 8 on the Tour and the annual
cluster sizes are highly unequal (879 vs 4,442 matches). B = 9,999, fixed seed
(common.SEED); null-restricted residuals and a CRVE Wald statistic are used.

Outputs:
  data/derived/Wild_cluster_bootstrap.csv
  outputs/28_wild_cluster_bootstrap.txt
"""
import os
import numpy as np
import pandas as pd

import common as c

B = 9999
RADEMACHER = np.array([-1.0, 1.0])
WEBB = np.array([-np.sqrt(1.5), -1.0, 0.0, 0.0, 1.0, np.sqrt(1.5)])


def design(df, cols):
    X = pd.get_dummies(df[cols], columns=[x for x in cols if x not in ("year_c", "yc_post", "year")],
                       drop_first=True, dtype=float)
    return np.column_stack([np.ones(len(df))] + [X[x].values for x in X.columns]), list(X.columns)


def wild_boot(y, X, groups, R, weight_set, B, seed):
    n, k = X.shape
    XtXi = np.linalg.inv(X.T @ X)
    beta = XtXi @ X.T @ y
    gids = np.unique(groups)
    G = len(gids)
    lab = np.searchsorted(gids, groups)
    rows = [np.where(lab == g)[0] for g in range(G)]

    def crve_wald(b, u):
        meat = np.zeros((k, k))
        for ix in rows:
            s = X[ix].T @ u[ix]
            meat += np.outer(s, s)
        corr = G / (G - 1) * (n - 1) / (n - k)
        V = XtXi @ meat @ XtXi * corr
        rb = R @ b
        se = np.sqrt(R @ V @ R.T).item()
        return (rb.item() / se) ** 2

    beta_t = beta - XtXi @ R.T @ (np.linalg.inv(R @ XtXi @ R.T) @ (R @ beta))
    u_t = y - X @ beta_t
    W0 = crve_wald(beta, y - X @ beta)

    rng = np.random.default_rng(seed)
    Ws = np.empty(B)
    for b in range(B):
        w = rng.choice(weight_set, G)
        ustar = u_t * w[lab]
        ystar = X @ beta_t + ustar
        bs = XtXi @ X.T @ ystar
        Ws[b] = crve_wald(bs, ystar - X @ bs)
    return G, W0, float(np.mean(Ws >= W0))


rows = []
logs = ["Wild cluster bootstrap (B=%d, seed=%d)" % (B, c.SEED), ""]

# --- World Championships post-2018 slope (G = 16) ---
wc = pd.read_csv(os.path.join(c.DER, "WC_RQ1_sample_n3868.csv"))
Xw, names = design(wc, ["year_c", "yc_post", "discipline", "round"])
Rw = np.zeros((1, Xw.shape[1]))
Rw[0, names.index("year_c") + 1] = 1
Rw[0, names.index("yc_post") + 1] = 1
logs.append("World Championships post-2018 slope:")
for wname, wset in (("Rademacher", RADEMACHER), ("Webb", WEBB)):
    G, W0, p = wild_boot(wc["TPP"].values, Xw, wc["year"].values, Rw, wset, B, c.SEED)
    rows.append({"model": "World Championships post-2018 slope", "G": G,
                 "weights": wname, "CRVE_Wald": W0, "wild_p": p})
    logs.append("  G=%d %s: Wald=%.3f, wild p=%.4f" % (G, wname, W0, p))
logs.append("")

# --- World Tour annual slope (G = 8) ---
tour = pd.read_csv(os.path.join(c.DER, "Tour_TPP_sample_n25928.csv"))
tour["year_c"] = tour["year"] - 2018
Xt, names2 = design(tour, ["year_c", "discipline", "round"])
Rt = np.zeros((1, Xt.shape[1]))
Rt[0, names2.index("year_c") + 1] = 1
logs.append("World Tour annual slope:")
for wname, wset in (("Rademacher", RADEMACHER), ("Webb", WEBB)):
    G, W0, p = wild_boot(tour["TPP"].values, Xt, tour["year"].values, Rt, wset, B, c.SEED)
    rows.append({"model": "World Tour annual slope", "G": G,
                 "weights": wname, "CRVE_Wald": W0, "wild_p": p})
    logs.append("  G=%d %s: Wald=%.3f, wild p=%.4f" % (G, wname, W0, p))

pd.DataFrame(rows).to_csv(os.path.join(c.DER, "Wild_cluster_bootstrap.csv"), index=False)
c.write_lines("28_wild_cluster_bootstrap.txt", logs)
print("Saved Wild_cluster_bootstrap.csv and 28_wild_cluster_bootstrap.txt")
