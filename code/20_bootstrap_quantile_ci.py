# -*- coding: utf-8 -*-
"""
20_bootstrap_quantile_ci.py
===========================
Bootstrap confidence intervals for the cell P90/P95 durations and the P95 buffer
(A6). Uses 10,000 resamples per cell with the fixed seed, matching the bootstrap
count used elsewhere in the study.
"""
import os
import pandas as pd
import numpy as np
import common as C

df = pd.read_csv(os.path.join(C.DER, "Tour_TPP_sample_n25928.csv"))
rng = np.random.default_rng(C.SEED)
B = 10000
rows = []
for (dsc, rnd), g in df.groupby(["discipline", "round"]):
    x = g.duration.to_numpy()
    n = len(x)
    mean = x.mean()
    idx = rng.integers(0, n, size=(B, n))
    samp = x[idx]
    p90 = np.quantile(samp, .9, axis=1)
    p95 = np.quantile(samp, .95, axis=1)
    buf = p95 - mean

    def ci(a):
        return np.quantile(a, .025), np.quantile(a, .975)

    a90, b90 = ci(p90)
    a95, b95 = ci(p95)
    ab, bb = ci(buf)
    rows.append(dict(discipline=dsc, round=rnd, n=n,
                     P95=round(np.quantile(x, .95), 1),
                     P95_CI="%.1f to %.1f" % (a95, b95),
                     P95_CI_halfwidth=round((b95 - a95) / 2, 1),
                     P90_CI_halfwidth=round((b90 - a90) / 2, 1),
                     BufferP95_CI_halfwidth=round((bb - ab) / 2, 1)))
o = pd.DataFrame(rows)
o.to_csv(os.path.join(C.DER, "Session_bootstrap_quantile_ci.csv"),
         index=False, encoding="utf-8-sig")
lines = o[["discipline", "round", "n", "P95", "P95_CI",
           "P95_CI_halfwidth"]].to_string(index=False).splitlines()
lines.append("max P95 CI half-width = %.1f min" % o.P95_CI_halfwidth.max())
C.write_lines("20_bootstrap_quantile_ci.txt", lines)
