# -*- coding: utf-8 -*-
"""
common.py
=========
Shared paths, column mapping and loaders for the Time-per-Point (TPP) study.

Data are public BWF tournament results (tournamentsoftware.com / bwfbadminton.com),
downloaded 27 September 2026. Two raw workbooks are shipped under data/raw:

  * WorldChampionships_2005-2026_n4250.xlsx   (Dataset A, n = 4,250)
  * WorldTour_Super300-1000_2018-2025_n26597.xlsx (Dataset B, n = 26,597)

All analysis is reproducible without any video annotation.
"""
import os
import pandas as pd
import numpy as np

# ----------------------------------------------------------------------------
# Paths (everything is relative to the package root, so the bundle is portable)
# ----------------------------------------------------------------------------
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
RAW = os.path.join(ROOT, "data", "raw")
DER = os.path.join(ROOT, "data", "derived")
FIG = os.path.join(ROOT, "figures")
OUT = os.path.join(ROOT, "outputs")
for _d in (DER, FIG, OUT):
    os.makedirs(_d, exist_ok=True)

# Fixed random seed for every bootstrap (used throughout the manuscript).
SEED = 20261008

# Six game-score columns -> uniform English names.
GAMECOLS = ["g1p1", "g1p2", "g2p1", "g2p2", "g3p1", "g3p2"]

_BASE_RENAME = {
    "年份": "year", "日期": "date", "项目": "discipline", "轮次": "round",
    "选手1": "player1", "选手2": "player2",
    "时长": "duration", "时长原文": "duration_text", "状态": "status",
    "第1局_P1": "g1p1", "第1局_P2": "g1p2",
    "第2局_P1": "g2p1", "第2局_P2": "g2p2",
    "第3局_P1": "g3p1", "第3局_P2": "g3p2",
}
_WC_FILE = "WorldChampionships_2005-2026_n4250.xlsx"
_TOUR_FILE = "WorldTour_Super300-1000_2018-2025_n26597.xlsx"


def _finalise(df, has_points_col):
    df = df.copy()
    # Total points scored: use the official derived column when present,
    # otherwise sum the six game-score cells.
    df["S"] = df[GAMECOLS].fillna(0).sum(axis=1)
    df["games"] = df[GAMECOLS].notna().sum(axis=1) / 2
    df["three"] = (df["games"] == 3).astype(int)
    if has_points_col:
        df["Pts"] = df["points"]
    else:
        df["Pts"] = df["S"]
    return df


def load_world_championships():
    """Dataset A (n=4,250), all BWF World Championships 2005-2026."""
    df = pd.read_excel(os.path.join(RAW, _WC_FILE)).rename(columns=_BASE_RENAME)
    return _finalise(df, has_points_col=False)


def load_world_tour():
    """Dataset B (n=26,597), World Tour Super 300-1000 main draws 2018-2025."""
    rename = dict(_BASE_RENAME)
    rename.update({"比赛名称": "event", "赛事级别": "level",
                   "总得分": "points", "TPP": "tpp_reported"})
    df = pd.read_excel(os.path.join(RAW, _TOUR_FILE)).rename(columns=rename)
    return _finalise(df, has_points_col=True)


def tpp(duration_min, points):
    """TPP = 60 * match duration (min) / total points, in seconds per point."""
    return 60.0 * duration_min / points


def wc_rq1_sample(wc):
    """Completed rally-point (>=2006) World Championship matches with a plausible
    recorded duration (>=10 min). This is the RQ1 regression sample, n = 3,868."""
    d = wc[(wc["status"] == "完赛") & (wc["year"] >= 2006)
           & wc["duration"].notna() & (wc["Pts"] > 0)
           & (wc["duration"] >= 10)].copy()
    d["TPP"] = tpp(d["duration"], d["Pts"])
    d["year_c"] = d["year"] - 2017
    d["post"] = (d["year"] >= 2018).astype(int)
    d["yc_post"] = d["year_c"] * d["post"]
    return d


def tour_tpp_sample(tour):
    """Completed Tour matches with usable duration and total points, n = 25,928."""
    d = tour[(tour["status"] == "完赛") & tour["duration"].notna()
             & tour["Pts"].notna() & (tour["Pts"] > 0)].copy()
    d["TPP"] = tpp(d["duration"], d["Pts"])
    return d


def write_lines(name, lines):
    """Write a list of strings to outputs/<name> and also print them."""
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(str(x) for x in lines))
    print("\n".join(str(x) for x in lines))
    return path
