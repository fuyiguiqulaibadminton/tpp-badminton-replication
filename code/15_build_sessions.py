# -*- coding: utf-8 -*-
"""
15_build_sessions.py
====================
Reconstruct court-sessions from completed Tour matches (A1). Matches sharing an
event, date and physical court form one session. Eighty-two fixtures without a
court value are excluded, as stated in the Table S3 data dictionary.
"""
import os
import pandas as pd
import common as C

df = pd.read_csv(os.path.join(C.DER, "Tour_TPP_sample_n25928.csv"))
n0 = len(df)
df = df.dropna(subset=["场地"]).copy()
df["当日场序"] = pd.to_numeric(df["当日场序"], errors="coerce")
key = ["event", "date", "场地"]
df = df.sort_values(key + ["当日场序"])
df["session_id"] = df.groupby(key).ngroup()

rows = []
for sid, g in df.groupby("session_id"):
    rows.append(dict(session_id=sid, event=g.event.iloc[0], date=g.date.iloc[0],
                     court=g["场地"].iloc[0], n_matches=len(g),
                     realized_duration_min=round(g.duration.sum(), 1),
                     disciplines=";".join(sorted(g.discipline.unique())),
                     rounds=";".join(sorted(g["round"].unique()))))
sess = pd.DataFrame(rows).sort_values(["date", "event", "court"]).reset_index(drop=True)
sess["session_id"] = range(len(sess))

mout = df[["session_id", "event", "date", "场地", "当日场序",
           "discipline", "round", "duration", "Pts", "TPP"]].copy()
mout.to_csv(os.path.join(C.DER, "Session_matches.csv"),
            index=False, encoding="utf-8-sig")
sess.to_csv(os.path.join(C.DER, "Session_reconstructed.csv"),
            index=False, encoding="utf-8-sig")

C.write_lines("15_build_sessions.txt", [
    "rows in=%d, dropped missing court=%d, kept=%d" % (n0, n0 - len(df), len(df)),
    "sessions=%d  matches/session mean=%.2f median=%d p90=%.1f max=%d" % (
        len(sess), sess.n_matches.mean(), sess.n_matches.median(),
        sess.n_matches.quantile(.9), sess.n_matches.max()),
    "total realized duration min=%.0f" % sess.realized_duration_min.sum()])
