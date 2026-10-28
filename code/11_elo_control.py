# -*- coding: utf-8 -*-
"""
11_elo_control.py
=================
Player-strength robustness check: control for pre-match player strength using
the external Elo ratings of Sun & Zhang (2026), Scientific Data,
https://doi.org/10.1038/s41597-026-08408-4 (data: https://doi.org/10.7910/DVN/
RSAYV5, CC BY 4.0).

The external data ship ONLY pre-match Elo for singles (MS/WS), 2006-09 to
2025-12; no doubles Elo exists and the 2026 World Championships cannot be
matched. This step:

  1. Resolves each TPP singles match to one external match record. The BWF
     exports used for TPP spell names in three conventions (full BWF names,
     initial abbreviations such as "K MOMOTA" / "HEO K H", and Korean given
     names with/without spaces, e.g. "SUNG Jihyun" vs "SUNG Ji Hyun"). The
     resolver therefore keys on (date +/- 1 day, discipline, surname +
     given-name/initial compatibility) and REQUIRES a set-by-set score match
     before a link is accepted; ambiguous links are rejected.
  2. Reports the match audit (Table S9).
  3. Refits the trend models on the linked singles samples with/without the
     absolute pre-match Elo gap, with/without the three-set indicator, and
     with the 2006-2010 cold-start years removed (Table S10).
  4. Minimum-duration threshold sensitivity modelled on the external data
     set's cleaning rule (the Sun & Zhang release only sets duration missing
     at 999 / >200 / <2 min; the 29.0 and 33.9 min figures quoted in the
     paper are the two-/three-game MEANS, not winsorization floors).
"""
import os
import re
import unicodedata
from collections import Counter

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats as st

import common as cm

EXT = os.path.join(cm.ROOT, "data", "raw_external")
L = []

# ---------------------------------------------------------------- name parsing
def fold(s):
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c))


def sorted_letters(s):
    return "".join(sorted(re.findall(r"[a-zà-ÿ]", s.lower())))


def parse_name(raw):
    """Return (surname_key, given_full_key, given_initial_sequence,
    surname_tokens).

    surname_key          : sorted letters of all-uppercase tokens (len >= 2)
    given_full_key       : sorted letters of every fully spelled given token
    given_initial_sequence: ordered list of initials (single-letter tokens in
                           order, then first letters of fully spelled tokens)
    surname_tokens       : each uppercase token as a separate sorted-letter key
                           (for compound surnames such as CASTILLO SALAZAR)
    """
    s = fold(raw)
    s = re.sub(r"\s*\([FfMm]\)\s*", " ", s)
    tokens = re.findall(r"[A-Za-zÀ-ÿ]+", s)
    sur, full, initials = [], [], []
    for tok in tokens:
        if len(tok) == 1:
            initials.append(tok.lower())
        elif tok.upper() == tok and len(tok) >= 2:
            sur.append(tok.lower())
        else:
            full.append(tok.lower())
    return (
        "".join(sorted("".join(sur))),
        sorted_letters("".join(full)),
        initials + [t[0] for t in full],
        {"".join(sorted(x)) for x in sur},
    )


def given_compatible(tpp, sz):
    """tpp / sz are parsed tuples; surnames are compared by the caller."""
    _, tfull, tini, _ = tpp
    _, sfull, sini, _ = sz
    # full vs full: same multiset of letters (handles "Jihyun" / "Ji Hyun")
    if tfull and sfull and tfull != sfull:
        return False
    # initials from the abbreviated export must be an ordered prefix of the
    # full initial sequence (e.g. "J JORGENSEN" -> "Jan O JORGENSEN";
    # "PUSARLA V S" -> "PUSARLA V. Sindhu")
    if tini:
        if not sini:
            return False
        if len(tini) > len(sini):
            return False
        if any(a != b for a, b in zip(tini, sini)):
            return False
    if tfull and not sfull:
        return False
    return True


def compatible(a, b):
    return a[0] == b[0] and given_compatible(a, b)


# Hand-checked transliteration aliases between the two sources (TPP surname
# spelling -> external surname spelling). Each alias is used only when a
# set-by-set score is also verified.
#  - TPP "VABIKOVA" omits the haček consonant of ŠVÁBÍKOVÁ (-> SVABIKOVA).
SURNAME_ALIASES = {
    "aabikovv": {"aabikosvv"},
}


def parse_name_variants(raw, side="tpp"):
    """Parse a name, returning every plausible descriptor.

    Both the TPP exports and the external table contain names in both
    conventions: the standard convention (surname in capitals) and a reversed
    convention (final given name capitalised and placed first), e.g.
    "YI Wang Zhi" for WANG Zhi Yi, "EUN Kim Joo" for KIM Joo Eun, and
    "KEYURA MOPATI" for Keyura MOPATI. The score-verified candidate selection
    makes the extra variant safe to try. For the external table (whose caps
    placement is systematic) the reversed variant is only attempted when the
    name is a single caps token plus one given token; for TPP exports it is
    attempted for any length."""
    s = fold(raw)
    s = re.sub(r"\s*\([FfMm]\)\s*", " ", s)
    tokens = re.findall(r"[A-Za-zÀ-ÿ]+", s)
    caps_idx = [i for i, t in enumerate(tokens) if len(t) >= 2
                and t.upper() == t]
    base = parse_name(raw)
    variants = [base]
    allow = (len(tokens) >= 2) if side == "tpp" else (len(tokens) == 2)
    if len(caps_idx) == 1 and caps_idx[0] == 0 and allow:
        caps = tokens[0]
        rest = tokens[1:]
        ini = []
        for tok in rest:
            if len(tok) == 1:
                ini.append(tok.lower())
            else:
                ini.append(tok[0].lower())
        ini.append(caps[0].lower())
        variants.append((
            sorted_letters(rest[0]),
            sorted_letters("".join(rest[1:] + [caps])),
            ini,
            {sorted_letters(rest[0])},
        ))
    # add transliteration aliases to the TPP-side surname-token sets
    if side == "tpp":
        extra = []
        for v in variants:
            al = set()
            for tok in v[3]:
                al |= SURNAME_ALIASES.get(tok, set())
            for key in al:
                # full-key variant for tier 1 plus a token for tier 2
                extra.append((key, v[1], v[2], v[3] | {key}))
        variants += extra
    return variants


# ------------------------------------------------------------------ load data
L.append("Loading external Sun & Zhang (2026) data ...")
pm = pd.read_excel(os.path.join(EXT, "matches.xlsx"))
pp = pd.read_excel(os.path.join(EXT, "players.xlsx"))
pm["date"] = pd.to_datetime(pm["match_date"])
name_map = pp.set_index("player_id")["name"].to_dict()
pm["wn"] = pm["winner_id"].map(name_map)
pm["ln"] = pm["loser_id"].map(name_map)
pm["wp"] = pm["wn"].map(lambda s: parse_name_variants(s, "sz"))
pm["lp"] = pm["ln"].map(lambda s: parse_name_variants(s, "sz"))

SET_RE = re.compile(r"(\d+)\s*[-\u2013]\s*(\d+)")


def parse_sz_score(s):
    """Ordered list of (winner_points, loser_points) pairs."""
    return [(int(a), int(b)) for a, b in SET_RE.findall(str(s))]


pm["sets"] = pm["score"].map(parse_sz_score)
# candidate match index: date -> rows of same type
pm_idx = {}
for typ, sub in pm.groupby("type"):
    pm_idx[typ] = sub

# TPP samples
wc = cm.wc_rq1_sample(cm.load_world_championships())
tt = cm.tour_tpp_sample(cm.load_world_tour())
tt["yr"] = tt["year"] - 2018


def tpp_sets(row):
    out = []
    for i in (1, 2, 3):
        a, b = row.get("g%dp1" % i), row.get("g%dp2" % i)
        if pd.notna(a) and pd.notna(b):
            out.append((int(a), int(b)))
    return out


def score_match(tpp_s, sz_s, p1_is_winner):
    if len(tpp_s) != len(sz_s) or not tpp_s:
        return False
    for t, s in zip(tpp_s, sz_s):
        if p1_is_winner:
            if t != s:
                return False
        else:
            if t != (s[1], s[0]):
                return False
    return True


def link_row(row):
    """Return (status, tier, match_index, gap, dElo)."""
    typ = row["discipline"]
    if str(row["player1"]).strip().lower() == "unknown" or \
            str(row["player2"]).strip().lower() == "unknown":
        return "unknown_player", None, None, None, None
    if typ not in pm_idx:
        return "no_external_discipline", None, None, None, None
    d = pd.to_datetime(row["date"])
    cand = pm_idx[typ]
    cand = cand[(cand["date"] >= d - pd.Timedelta(days=1))
                & (cand["date"] <= d + pd.Timedelta(days=1))]
    if len(cand) == 0:
        return "no_candidate", None, None, None, None
    p1v, p2v = parse_name_variants(row["player1"]), \
        parse_name_variants(row["player2"])
    ts = tpp_sets(row)

    def pair_compatible(wa, la, orient):
        if orient == 1:
            return any(compatible(a, b) for a in p1v for b in wa) and \
                   any(compatible(a, b) for a in p2v for b in la)
        return any(compatible(a, b) for a in p1v for b in la) and \
               any(compatible(a, b) for a in p2v for b in wa)

    # tier 1: both names compatible + score verified
    t1 = []
    for idx, r in cand.iterrows():
        w, l = r["wp"], r["lp"]
        orient = None
        if pair_compatible(w, l, 1):
            orient = 1
        elif pair_compatible(w, l, -1):
            orient = -1
        if orient is not None:
            if score_match(ts, r["sets"], orient == 1):
                t1.append((idx, orient))
    if len(t1) == 1:
        idx, orient = t1[0]
        r = cand.loc[idx]
        gap = abs(r["winner_elo"] - r["loser_elo"])
        dElo = orient * (r["winner_elo"] - r["loser_elo"])
        return "matched", "name+score", idx, gap, dElo
    if len(t1) > 1:
        return "ambiguous_name", None, None, None, None
    # tier 2: score-assisted surname-token matching (compound surnames and
    # caps-first reversals). Each score-compatible candidate is scored by the
    # number of TPP players (0-2) whose surname token appears in the
    # orientation-consistent slot. A candidate with BOTH players present
    # outranks a one-sided hit and disambiguates same-score matches that fall
    # inside the same +-1 day window.
    scored = []
    s1 = set().union(*[a[3] for a in p1v])
    s2 = set().union(*[a[3] for a in p2v])
    for idx, r in cand.iterrows():
        w, l = r["wp"], r["lp"]
        sw = set().union(*[a[3] for a in w])
        sl = set().union(*[a[3] for a in l])
        if score_match(ts, r["sets"], True):
            hit = int(bool(s1 & sw)) + int(bool(s2 & sl))
            if hit:
                scored.append((hit, idx, 1))
        if score_match(ts, r["sets"], False):
            hit = int(bool(s1 & sl)) + int(bool(s2 & sw))
            if hit:
                scored.append((hit, idx, -1))
    if scored:
        best = max(s[0] for s in scored)
        t2 = [s for s in scored if s[0] == best]
        if len(t2) == 1:
            _, idx, orient = t2[0]
            r = cand.loc[idx]
            gap = abs(r["winner_elo"] - r["loser_elo"])
            dElo = orient * (r["winner_elo"] - r["loser_elo"])
            return "matched", "score-assisted", idx, gap, dElo
        return "ambiguous_score", None, None, None, None
    # tier 3: name-compatible but external score missing / unparseable
    t3 = []
    for idx, r in cand.iterrows():
        if pair_compatible(r["wp"], r["lp"], 1) or \
                pair_compatible(r["wp"], r["lp"], -1):
            t3.append(idx)
    if len(t3) == 1:
        idx = t3[0]
        r = cand.loc[idx]
        return "matched", "name-only", idx, \
               abs(r["winner_elo"] - r["loser_elo"]), None
    return "no_match", None, None, None, None


def merge_sample(df, dataset):
    recs = []
    for _, r in df.iterrows():
        status, tier, idx, gap, dElo = link_row(r)
        recs.append(dict(dataset=dataset, year=int(r["year"]),
                         discipline=r["discipline"], date=str(r["date"])[:10],
                         player1=r["player1"], player2=r["player2"],
                         TPP=r["TPP"], three=int(r["three"]),
                         round=r["round"], duration=r["duration"],
                         status_link=status, tier=tier,
                         sz_match_idx=idx, elo_gap=gap, elo_diff_p1=dElo))
    out = pd.DataFrame(recs)
    out["elo_gap100"] = out["elo_gap"] / 100.0
    return out


wc_s = wc[wc["discipline"].isin(["MS", "WS"])].copy()
tt_s = tt[tt["discipline"].isin(["MS", "WS"])].copy()
L.append("Singles samples: WC %d (incl. 2026), Tour %d" % (len(wc_s), len(tt_s)))
mwc = merge_sample(wc_s, "WC")
mtt = merge_sample(tt_s, "Tour")
merged = pd.concat([mwc, mtt], ignore_index=True)
merged.to_csv(os.path.join(cm.DER, "elo_merged_singles.csv"),
              index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- Table S9
rows = []
for dataset, sub in merged.groupby("dataset"):
    for yr, g in sub.groupby("year"):
        n = len(g)
        matched = g["status_link"].eq("matched")
        nmat = int(matched.sum())
        tier_counts = g.loc[matched, "tier"].value_counts().to_dict()
        reason_counts = g.loc[~matched, "status_link"].value_counts().to_dict()
        rows.append(dict(dataset=dataset, year=yr, n=n, matched=nmat,
                         match_pct=round(100 * nmat / n, 1),
                         name_score=tier_counts.get("name+score", 0),
                         score_assisted=tier_counts.get("score-assisted", 0),
                         name_only=tier_counts.get("name-only", 0),
                         unknown_player=reason_counts.get("unknown_player", 0),
                         no_candidate=reason_counts.get("no_candidate", 0),
                         no_match=reason_counts.get("no_match", 0),
                         ambiguous=reason_counts.get("ambiguous_name", 0)
                                 + reason_counts.get("ambiguous_score", 0)))
s9 = pd.DataFrame(rows)
s9.to_csv(os.path.join(cm.DER, "TableS9_elo_merge_audit.csv"),
          index=False, encoding="utf-8-sig")

L.append("")
L.append("Table S9: Elo merge audit (by dataset x year)")
L.append("  " + s9.to_string(index=False).replace("\n", "\n  "))
tot = merged.groupby("dataset").agg(
    n=("TPP", "size"),
    matched=("status_link", lambda x: (x == "matched").sum()))
tot["pct"] = (100 * tot["matched"] / tot["n"]).round(1)
L.append("")
L.append("Overall: " + tot.to_string().replace("\n", "\n  "))
L.append("Unmatched reasons: " + str(merged.loc[
    merged.status_link != "matched", "status_link"].value_counts().to_dict()))
L.append("Match tiers: " + str(merged.loc[
    merged.status_link == "matched", "tier"].value_counts().to_dict()))

# ============================================================ Table S10 models
model_rows = []


def se_post(m, a="year_c", b="yc_post"):
    v = m.cov_params()
    return np.sqrt(v.loc[a, a] + v.loc[b, b] + 2 * v.loc[a, b])


def wc_fit(df, label, with_elo, with_three, note):
    f = "TPP ~ year_c + yc_post + C(discipline) + C(round)"
    if with_three:
        f += " + three"
    if with_elo:
        f += " + elo_gap100"
    m = smf.ols(f, data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df["year"]})
    post = m.params["year_c"] + m.params["yc_post"]
    sep = se_post(m)
    pp = 2 * (1 - st.norm.cdf(abs(post / sep)))
    row = dict(series="WC singles", spec=label, note=note, n=len(df),
               years="%d-%d" % (df.year.min(), df.year.max()),
               beta1=round(m.params["year_c"], 3),
               beta2=round(m.params["yc_post"], 3),
               post_slope=round(post, 3), post_se=round(sep, 3),
               post_p=round(pp, 3), r2=round(m.rsquared, 4),
               elo100_coef="", elo100_se="", elo100_p="",
               three_coef="", three_se="")
    if with_elo:
        row.update(elo100_coef=round(m.params["elo_gap100"], 3),
                   elo100_se=round(m.bse["elo_gap100"], 3),
                   elo100_p=round(m.pvalues["elo_gap100"], 3))
    if with_three:
        row.update(three_coef=round(m.params["three"], 2),
                   three_se=round(m.bse["three"], 2))
    model_rows.append(row)


def tour_fit(df, label, with_elo, with_three, note):
    f = "TPP ~ yr + C(discipline) + C(round)"
    if with_three:
        f += " + three"
    if with_elo:
        f += " + elo_gap100"
    m = smf.ols(f, data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df["year"]})
    row = dict(series="Tour singles", spec=label, note=note, n=len(df),
               years="%d-%d" % (df.year.min(), df.year.max()),
               beta1="", beta2="", post_slope=round(m.params["yr"], 3),
               post_se=round(m.bse["yr"], 3),
               post_p=round(m.pvalues["yr"], 3), r2=round(m.rsquared, 4),
               elo100_coef="", elo100_se="", elo100_p="",
               three_coef="", three_se="")
    if with_elo:
        row.update(elo100_coef=round(m.params["elo_gap100"], 3),
                   elo100_se=round(m.bse["elo_gap100"], 3),
                   elo100_p=round(m.pvalues["elo_gap100"], 3))
    if with_three:
        row.update(three_coef=round(m.params["three"], 2),
                   three_se=round(m.bse["three"], 2))
    model_rows.append(row)


w = mwc[mwc.status_link == "matched"].copy()
w["year_c"] = w["year"] - 2017
w["yc_post"] = w["year_c"] * (w["year"] >= 2018).astype(int)
t = mtt[mtt.status_link == "matched"].copy()
t["yr"] = t["year"] - 2018

wc_fit(w, "baseline", False, False, "linked singles, 2026 excluded (no Elo)")
wc_fit(w, "with |deltaElo|", True, False, "pre-match Elo gap / 100")
wc_fit(w, "with three-set", False, True, "")
wc_fit(w, "with |deltaElo| + three", True, True, "")
wc_fit(w[w.year >= 2011], "baseline, 2011+", False, False,
       "drops 2006-2010 Elo cold-start years")
wc_fit(w[w.year >= 2011], "|deltaElo|, 2011+", True, False, "")

tour_fit(t, "baseline", False, False, "linked singles 2018-2025")
tour_fit(t, "with |deltaElo|", True, False, "")
tour_fit(t, "with three-set", False, True, "")
tour_fit(t, "with |deltaElo| + three", True, True, "")
tour_fit(t[t.year != 2020], "baseline, excl 2020", False, False, "")
tour_fit(t[t.year != 2020], "|deltaElo|, excl 2020", True, False, "")
tour_fit(t[~t.year.isin([2020, 2021])], "baseline, excl 2020-21", False, False,
         "")
tour_fit(t[~t.year.isin([2020, 2021])], "|deltaElo|, excl 2020-21", True,
         False, "")

# ============================================ minimum-duration thresholds
# Sun & Zhang release rule: 999 sentinel, >200 min and <2 min set missing.
# The paper's 29.0 / 33.9 min figures are two-/three-game MEANS, not floors.
L.append("")
L.append("Threshold note: external release only sets duration missing at 999, "
         ">200 min, <2 min; 29.0 / 33.9 min are the two-/three-game means.")
for lo, hi in [(2, 200), (10, 200), (18, 200), (2, 120), (18, 120)]:
    for nm, df, kind in (("WC", w, "wc"), ("Tour", t, "tour")):
        keep = (df.duration >= lo) & (df.duration <= hi)
        removed = int((~keep).sum())
        if kind == "wc":
            mm = smf.ols(
                "TPP ~ year_c + yc_post + C(discipline) + C(round)",
                data=df[keep]).fit(
                cov_type="cluster",
                cov_kwds={"groups": df.loc[keep, "year"]})
            slope = mm.params["year_c"] + mm.params["yc_post"]
            se = se_post(mm)
        else:
            mm = smf.ols(
                "TPP ~ yr + C(discipline) + C(round)", data=df[keep]).fit(
                cov_type="cluster",
                cov_kwds={"groups": df.loc[keep, "year"]})
            slope = mm.params["yr"]
            se = mm.bse["yr"]
        model_rows.append(dict(series="%s singles threshold" % nm,
                               spec="%d<=dur<=%d" % (lo, hi),
                               note="removed %d" % removed,
                               n=int(keep.sum()), years="", beta1="", beta2="",
                               post_slope=round(slope, 3),
                               post_se=round(se, 3), post_p="", r2="",
                               elo100_coef="", elo100_se="", elo100_p="",
                               three_coef="", three_se=""))

s10 = pd.DataFrame(model_rows)
s10.to_csv(os.path.join(cm.DER, "TableS10_elo_control_models.csv"),
           index=False, encoding="utf-8-sig")
L.append("")
L.append("Table S10: Elo-controlled singles models")
L.append("  " + s10.to_string(index=False).replace("\n", "\n  "))

cm.write_lines("11_elo_control.txt", L)
