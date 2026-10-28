# Time-per-Point (TPP) in Elite Badminton — Reproducibility Package

**Companion to:** *TPP_manuscript.docx* (main manuscript, named copy; located in this folder). Submission set also includes *TPP_manuscript_anonymous.docx* (double-blind manuscript for review), *TPP_title_page.docx* (separate title page) and *TPP_supplementary_material.docx* (supplementary material, Tables S1-S12, Figure S1 and supplementary notes).

## Contents

The numbered analysis scripts in `code/` (steps 1-13) reproduce every statistic
and every figure from the two source workbooks, and the manuscript files above
are the final versions. The pipeline covers sample construction, the trend and
slope-break models, the match-duration decomposition, the discipline-and-round
structural profile, the player-strength and recording-artefact robustness
checks, and all supplementary tables; the figures are produced by step 8.

This bundle reproduces **every statistic and every figure** in the manuscript
from the two source workbooks, end to end, with a single command. It uses **only
public BWF match-result data and the officially recorded match duration — no
video, no rally/pause annotation, and no proprietary broadcast timing.**

---

## 1. The measure

**Time per Point (TPP)**, in seconds per point, is

```
TPP = 60 × MATCH DURATION (minutes) / total points scored (S)
```

where `MATCH DURATION` is the duration field recorded in the public BWF /
tournament-software results and `S` is the total points scored (sum of the six
game-score cells, or the official derived total-points column where supplied).

TPP is a **composite competition-clock metric**. Per point it bundles rally play,
between-rally pauses (shuttle retrieval, towelling, challenge review,
preparation) and rule-mandated breaks (11-point intervals, inter-game intervals,
medical stoppages). It **cannot separate rally time from pause time**, it is not
broadcast duration (no pre/post-match production or advertising), and it is not a
direct measure of spectator experience. Figure 1 is an **operational schematic
only**; the internal start/stop rules of the BWF duration field are not publicly
documented, so the components in that figure are not independently validated.

Two TPP summaries are used and are always kept distinct:

* **Aggregate TPP** = `60 × Σduration / Σpoints` over a group (the headline
  measure; weights every point equally).
* **Match-level mean TPP** = the mean of per-match `60·duration/points`
  (weights every match equally).

They differ slightly (whole Tour: aggregate ≈ 32.0 s/point, match mean ≈ 31.6).

---

## 2. Repository layout

```
TPP_Reproducibility_Package/
├─ TPP_manuscript.docx               # the named manuscript (file not for review)
├─ TPP_manuscript_anonymous.docx     # the double-blind manuscript
├─ TPP_supplementary_material.docx   # supplementary material (Tables S1-S12, Figure S1)
├─ TPP_title_page.docx               # separate title page
├─ requirements.txt                  # pinned dependency versions
├─ README.md                         # this file
├─ LICENSE                           # code licence (MIT)
├─ data/
│  ├─ raw/                           # the two BWF source workbooks (read-only inputs)
│  │  ├─ WorldChampionships_2005-2026_n4250.xlsx
│  │  └─ WorldTour_Super300-1000_2018-2025_n26597.xlsx
│  ├─ raw_external/                  # external singles Elo dataset (CC BY 4.0, read-only)
│  │  ├─ matches.xlsx / players.xlsx / tournaments.xlsx
│  │  └─ SOURCE_AND_LICENSE.txt      # citation, DOI, licence and attribution
│  └─ derived/                       # analysis-ready CSV tables written by the code
├─ code/
│  ├─ common.py                      # paths, column map, loaders, TPP formula, seed
│  ├─ 01_build_samples.py            # sample construction, exclusions, Table 1
│  ├─ 02_rq1_trend.py                # RQ1 segmented regression, bootstrap, TOST
│  ├─ 03_rq2_decompose.py            # RQ2 duration decomposition + event bootstrap
│  ├─ 04_rq3_noncompletion.py        # RQ3 structural profile; descriptive non-completion, Tables 5 & 6
│  ├─ 05_rq4_alternatives.py         # RQ4 alternatives, net TPP, rest negative control (Table S5)
│  ├─ 06_tableS1_logistic.py         # Supplementary Table S1 logistic model
│  ├─ 07_tableS2_validity.py         # Supplementary Table S2 validity anchors
│  ├─ 08_make_figures.py             # regenerates all seven figures
│  ├─ 09_composition_ledger.py       # composition standardisation + Table 8 robustness summary
│  ├─ 10_sensitivity.py              # knot sensitivity, retirement worst case, MDE, recording-change simulation (Tables S6–S8)
│  ├─ 11_elo_control.py              # external Elo merge/audit + Elo-controlled models (Tables S9–S10)
│  ├─ 12_extra_sensitivity.py        # trend excluding 2026 + P1/P99 winsorization (Table S11)
│  ├─ 13_subperiod_sensitivity.py    # same-rules post-COVID subperiod slopes (Table S12)
│  └─ run_all.py                     # runs steps 1–13 in order
├─ figures/                          # exact manuscript figures (authoritative copies)
│  └─ recomputed/                    # figures regenerated from raw data by step 8
└─ outputs/                          # plain-text logs of every computed statistic
```

---

## 3. Data sources and provenance

* **Source:** public BWF tournament results as published on the BWF /
  tournament-software results platform (bwfbadminton.com / tournamentsoftware).
* **Retrieval date:** **27 September 2026.**
* **No video or broadcast timing is used anywhere.**

| Dataset | File | Coverage | Draws | Matches |
|---|---|---|---|---|
| A — World Championships | `WorldChampionships_2005-2026_n4250.xlsx` | 2005–2026 | all five disciplines | **4,250** |
| B — World Tour | `WorldTour_Super300-1000_2018-2025_n26597.xlsx` | 2018–2025, Super 300/500/750/1000 main draws | all five disciplines | **26,597** |

Combined: **30,847 elite matches**, of which **30,059** have a usable TPP input.

### External data (step 11 only)

Step 11 additionally reads the open dataset of **Sun, M. & Zhang, F. (2026)**,
*A relational dataset of international badminton singles matches with ranking
and Elo measures, 2006–2025*, **Scientific Data**,
https://doi.org/10.1038/s41597-026-08408-4 (data: Harvard Dataverse
https://doi.org/10.7910/DVN/RSAYV5, **CC BY 4.0**), shipped verbatim in
`data/raw_external/` (`matches.xlsx`, `players.xlsx`, `tournaments.xlsx`; see
`SOURCE_AND_LICENSE.txt` for the full citation and licence). The Elo ratings
are the data authors' **model estimates, not BWF official statistics**, cover
men's and women's **singles only** (2006–09 to 2025–12), and are used solely
for the player-strength robustness check. Doubles have no Elo, and the 2026
World Championships cannot be matched because the external data end in 2025.

### Data dictionary (analysis field names)

| Field | Meaning / unit |
|---|---|
| `year`, `date` | season year; match date |
| `discipline` | MS, WS, MD, WD, XD |
| `round` | R64, R32, R16, QF, SF, Final |
| `event`, `level` | tournament name; World Tour tier (Super 300/500/750/1000) — Dataset B |
| `player1`, `player2` | the two players/pairs |
| `duration` | recorded `MATCH DURATION` in whole minutes |
| `duration_text` | duration as displayed in the source |
| `status` | `完赛` completed, `RET` in-match retirement, `WO` pre-match walk-over |
| `g1p1,g1p2,…,g3p2` | six game-score cells (points for each side in games 1–3) |
| `points` | official derived total-points column (Dataset B) |
| `S` | total points = sum of the six game-score cells |
| `Pts` | points used for TPP: official `points` (B) or `S` (A) |
| `games`, `three` | number of games played; 1 if a three-game (deciding) match |
| `TPP` | `60·duration/Pts`, seconds per point |

---

## 4. Sample flow and exclusions

**Dataset A — World Championships (4,250):**
4,250 total → −79 walkovers → −36 retirements → **4,135 completed**.
Of these, **263** are 2005 side-out-scoring matches (kept for descriptive
display only, excluded from trend modelling) and **4** completed matches have an
implausibly short recorded duration (<10 min) and are excluded. The RQ1
rally-point analysis sample is **n = 3,868**.

**Dataset B — World Tour (26,597):**
26,597 total → −274 walkovers → −392 retirements → **25,931 completed**;
of the completed matches, 1 lacks a usable duration (2023 Arctic Open men's
doubles final) and 2 lack game scores (2022 Korea Open men's doubles
quarter-finals), giving the Tour TPP analysis sample **n = 25,928**.

**Closure:** 30,847 = 4,250 + 26,597; usable TPP inputs 30,059 = 25,928 (Tour) +
3,868 (WC rally-point) + 263 (2005 side-out, descriptive). This is Figure 7.

* **Retirement rate denominator** = completed + retired matches (walkovers
  excluded): overall **1.49%**.
* **Walkover rate denominator** = all scheduled draw entries: overall **1.03%**.
* All 392 Tour retirements carry both an elapsed time and partial game scores, so
  a partial TPP can be computed; because it is truncated at abandonment it is
  **biased and is not used for inference** (only in the exploratory Table S1).

---

## 5. Computing environment and installation

* The package was verified on **Python 3.13.16 (Windows)**; it also runs on
  Python 3.10+. The exact versions used for verification are pinned in
  `requirements.txt` (pandas 3.0.6, numpy 2.5.4, scipy 1.18.1,
  statsmodels 0.15.0, matplotlib 3.11.2, openpyxl 3.1.5; plus python-docx 1.2.0,
  lxml 6.1.3 and PyMuPDF 2.0 for the document/PDF inspection helpers). Small
  version differences are not expected to change any reported result.
* No compilation, no network access at run time (everything reads `data/raw`).

To reproduce the exact verification environment:

```bash
python -m pip install -r requirements.txt
```

Or install only the packages needed to run the analysis pipeline:

```bash
pip install pandas numpy scipy statsmodels matplotlib openpyxl
```

---

## 6. How to reproduce

From the `code/` directory (paths are resolved relative to the scripts, so you
can run from anywhere):

```bash
python run_all.py
```

This runs steps 1–13 in order, writing analysis tables to `data/derived/`,
statistical logs to `outputs/`, and regenerated figures to `figures/recomputed/`.
Individual steps can also be run on their own, e.g. `python 03_rq2_decompose.py`
(run step 1 first so the derived samples exist; step 11 additionally requires
the `data/raw_external/` workbooks and openpyxl).

**Randomness:** every bootstrap uses the fixed seed **20261008** (`common.SEED`);
the RQ1 and RQ2 bootstraps each use **10,000** resamples. Re-running gives the
same intervals to within printed rounding. Increasing the resample count only
reduces Monte-Carlo error and does not change any conclusion.

---

## 7. Analysis steps and methods

* **Step 1 — `01_build_samples.py`.** Loads both workbooks, maps columns, builds
  total points (`S`), game count and three-game indicator, applies the exclusions
  in §4, verifies the count closure, and writes Table 1 (annual WC TPP) and the
  analysis samples.
* **Step 2 — RQ1 (`02_rq1_trend.py`).** Match-level segmented OLS of TPP at the
  World Championships (n = 3,868), knot at 2017, with discipline and round fixed
  effects: `TPP ~ (year−2017) + (year−2017)·Post2017 + discipline + round`.
  Reports β1 (2006–17 slope), β2 (slope change), β1+β2 (post-2018 slope) with
  **year-cluster-robust SEs**, R², a Chow test, a **pairs year-cluster bootstrap
  (10,000)** for the post-slope CI/p, an annual-aggregation robustness fit, and
  **TOST equivalence** at ±0.30, ±0.25 and ±0.20 s/year. A separate augmented
  model reports the three-set (`is_decider`) coefficient.
* **Step 3 — RQ2 (`03_rq2_decompose.py`).** Decomposes the 2018→2025 change in
  mean Tour match duration into a TPP (clock-time-per-point) component, a
  scoring-frequency (points-per-match) component and their interaction, overall
  and by discipline. Uncertainty uses an **event-clustered bootstrap (10,000)**
  that resamples whole tournaments; an iid match-level bootstrap is printed only
  as a narrower comparison. It also writes the year-by-year decomposition inputs
  (n, mean duration, aggregate TPP, mean points) to `TableS4_annual_TST.csv`
  (manuscript Table S4).
* **Step 4 — RQ3 (`04_rq3_noncompletion.py`).** The **structural TPP profile**
  across disciplines, event tiers (Table 5) and rounds (discipline × round TPP
  matrix, Table 6; Figure 5), reporting both aggregate and match-mean TPP.
  In-match **non-completion is descriptive only, not a research question**:
  retirement and walk-over rates, the discipline × round TPP/retirement matrix
  with a cell-level Spearman correlation (Figure 6), and the exploratory
  logistic model (Table S1) are reported as sample characteristics.
* **Step 5 — RQ4 (`05_rq4_alternatives.py`).** Three-set frequency and the
  three-set TPP premium (raw and fixed-effect-adjusted), rule-break per-point
  accounting, net TPP after deducting rule-book break lengths, deuce rate and
  score-gap checks, and a player-match **rest-interval negative-control panel**
  (OLS with discipline/round controls; iid, player-clustered and
  event-clustered SEs). Because the public calendar omits Olympic, continental,
  domestic-league and team events, this panel is a negative control (manuscript
  Supplementary Table S5), not a complete rest model; it writes
  `TableS5_rest_panel.csv`.
* **Step 6 — Table S1 (`06_tableS1_logistic.py`).** Logistic model of in-match
  retirement on partial TPP with discipline/round fixed effects and a three-set
  control (n = 26,320); flagged as exploratory because partial TPP is truncated.
* **Step 7 — Table S2 (`07_tableS2_validity.py`).** External validity anchors for
  men's-singles TPP against video-coded RT/PT studies (Hoffmann & Vogt 2024/2026;
  Gómez et al. 2019), reconstructing `TPP* = RT + PT + rule breaks per point`.
* **Step 8 — `08_make_figures.py`.** Regenerates Figures 1–7 into
  `figures/recomputed/`.
* **Step 9 — `09_composition_ledger.py`.** A point-weighted shift-share split of
  the 2018→2025 aggregate TPP change into within-group and between-group
  (composition/mix) terms for discipline, round and event level (the two terms
  sum exactly to the aggregate change; the composition-standardised change is
  the within term at fixed 2018 weights). It writes `Composition_standardization.csv`,
  `Composition_level_detail.csv` and the manuscript **Table 8** robustness
  summary `Table7_attribution_ledger.csv` (the CSV filename is kept
  stable for continuity). Table 8 consolidates the
  separate robustness checks; its rows are **not additive** and it is a synthesis,
  not a statistically estimated residual decomposition.
* **Step 10 — sensitivity checks (`10_sensitivity.py`).** Writes
  `TableS6_knot_sensitivity.csv` (World Championships segmented fit with the knot
  at 2017/2018/2019), `TableS7_annual_noncompletion.csv` (year-by-year RET/WO
  rates and a worst-case Tour trend that includes all 392 retirements at partial
  TPP), and `TableS8_recording_change_sim.csv` (uniform and ramped ±1–3 minute
  recording-change shifts for both series). It also prints the minimum detectable
  post-2018 slope (two-sided α = .05, 80% power) and the unobserved-stoppage
  envelope (extra seconds per match per year implied by the +2.23 s/point rise).
* **Step 11 — Elo control (`11_elo_control.py`).** Resolves each TPP singles
  match (MS/WS) to one external match record of Sun and Zhang (2026) using
  discipline, date (±1 day), both players (accent-folded, tolerant of the BWF
  full-name/initial and Eastern/Western name-order conventions) and a game-by-game
  score verification in both orientations; a link is accepted only with a unique
  score-compatible candidate. It writes the linked panel
  (`elo_merged_singles.csv`), the match audit (`TableS9_elo_merge_audit.csv`,
  manuscript Table S9) and the refit models (`TableS10_elo_control_models.csv`,
  Table S10): both trend models with/without the absolute pre-match Elo gap,
  with/without the three-set indicator, on 2011-onward (Elo cold-start) and
  COVID-excluded subsets, plus a minimum-duration threshold sensitivity modelled
  on the external release's cleaning rules.
* **Step 12 — extra sensitivity (`12_extra_sensitivity.py`).** Writes
  `TableS11_extra_sensitivity.csv` (manuscript Table S11): (i) the
  all-discipline World Championships segmented fit excluding the 2026 matches
  (n = 3,609), which aligns the main trend with the Elo-controlled singles
  models that cannot link 2026; and (ii) a legacy P1/P99 winsorization, clipping
  match-level TPP at its 1st/99th percentile within each sample
  (17.70–47.75 s/point for the World Championships, 20.00–46.79 for the Tour),
  compared line by line with the full-sample slopes. The main analysis keeps the
  full sample; the winsorized line is a literal before/after comparison.
* **Step 13 — same-rules subperiod sensitivity (`13_subperiod_sensitivity.py`).** Refits the main World Tour specification (TPP ~ year with discipline and round fixed effects; year-clustered standard errors) on two unchanged-rules post-COVID subwindows and writes `TableS12_subperiod_sensitivity.csv` (manuscript Table S12). The full-window row reproduces the 0.295 s/year baseline; the subwindow rows are exploratory (five or four year clusters) and test whether the rise is confined to the COVID seasons or the panel start.

---

## 8. Expected results (key reproduced values)

**Sample closure:** 30,847 total; 30,059 usable TPP inputs; RQ1 n = 3,868; Tour
TPP n = 25,928.

**RQ1 — World Championships (Table 2; year-cluster SEs):** β1 = 0.751
(SE 0.088); β2 = −0.843 (SE 0.135); post-2018 slope = −0.092 (SE 0.056, normal
p = .10); R² = 0.476; Chow F(1, 3856) = 302.6; three-set control (augmented
model) +2.63 (SE 0.16), with β1/β2 robust at 0.74/−0.82. The preferred
year-cluster bootstrap (10,000) gives the post-slope 95% CI ≈ [−0.23, +0.04],
p ≈ .15. TOST equivalence holds at ±0.30 and ±0.25 s/year, not at ±0.20. (The
annual-aggregation robustness fit gives β1 ≈ 0.77, β2 ≈ −0.90, post ≈ −0.12 with
bootstrap 95% CI [−0.26, +0.02].)

**RQ2 — World Tour decomposition:** Δ mean duration = **+3.37 min** (42.49 →
45.86). TPP component **3.10 min (92%)**, event-cluster 95% CI [1.82, 4.28];
scoring-frequency 0.24 min (7%) [−0.38, 0.87]; interaction ≈ 0.02 min; TPP share
92% [75%, 117%]. Δ aggregate TPP = +2.23 s/point; Δ points/match = +0.48.
(iid bootstrap share [81%, 107%] shown for comparison.) Year-by-year inputs are
in `data/derived/TableS4_annual_TST.csv` (manuscript Table S4), e.g. mean duration
42.49→45.86 min and aggregate TPP 30.51→32.74 over 2018→2025.

**RQ3 — structural profile (§4.4):** aggregate TPP rises through the draw in
every discipline (men's singles 34.9→40.0, mixed doubles 27.7→33.4 s/point from
R32 to Final; the women's doubles final is the single slowest cell at 40.8). All
four tiers rose over 2018–2025 — Super 300 +2.3, Super 500 +2.3, Super 750 +1.1,
Super 1000 +2.9 s/point; eight-year match-mean TPP by tier: Super 300 30.4,
Super 500 31.3, Super 750 33.3, Super 1000 32.8.

**Non-completion (descriptive only, §4.5; not a research question):** retirement
1.49%, walk-over 1.03%; retirement by discipline MS 2.24%, WS 2.11%, MD 0.92%,
WD 1.38%, XD 0.78%; across the 25 discipline × round cells Spearman ρ = 0.30
(descriptive only, no inferential test).

**RQ4 — attribution and robustness (§4.6; Table 8):** three-set frequency 31.9%→32.8%; raw three-set premium
+2.85 s/point (SE 0.07; +2.53 with fixed effects); rule breaks explain ≈0.42 of
this, leaving ≈2.4 s/point of pace; annual slope 0.295→0.294 after the three-set
control; the discipline/round-adjusted FE annual slope is **0.295 with all years,
0.298 excluding 2020 and 0.302 excluding 2020–2021**, so the COVID-disrupted
seasons do not drive the trend; deuce rate 18.7%→20.1%; mean per-game score gap
essentially flat (6.35→6.30 points). Net-of-break TPP changes by exactly the same
+2.23 s/point as raw TPP, because mean deducted break time per point is unchanged
across years (3.56 s/point for net-full in both 2018 and 2025); levels
(raw / net-full / net-technical) are 30.514 / 26.955 / 28.849 in 2018 and
32.743 / 29.183 / 31.081 in 2025, each rising +2.23. The rest-interval
negative-control panel (Supplementary Table S5; `TableS5_rest_panel.csv`) starts
from 51,856 player-match rows (two players × 25,928
matches) and retains **47,428 after dropping each player's first in-window match**
(no previous-match interval); the coefficient on days since previous match is
−0.0014 s/point/day (event-clustered SE 0.0005, p .003; iid/player-clustered SE
0.0002, p < .001): statistically distinguishable from zero but substantively
negligible, since one extra week of rest shifts TPP by only ≈0.01 s, two orders
of magnitude below the +2.23 trend.

**Composition standardisation and the Table 8 robustness summary (§4.3, §4.6;
`Composition_standardization.csv`, `Composition_level_detail.csv`,
`Table7_attribution_ledger.csv`):** a point-weighted shift-share split —
within-group change at fixed 2018 weights plus a between-group mix term, the two
summing exactly to the aggregate change — applied to the +2.23 s/point rise
gives within-discipline **+2.21** (mix +0.02), within-round **+2.25** (mix
−0.02) and within-event-level **+2.12** (mix +0.11; Super 1000 point share
12.2%→14.0%, Super 300 41.1%→34.4%). The largest single composition term is only
≈0.1 s/point, so essentially the entire +2.23 s/point remains a residual
per-point clock-time rise whose rally/pause mechanism requires video coding.
Table 8 lists these checks as separate, **non-additive** rows; it is a
synthesis, not a statistically estimated residual decomposition.

**Table S1 (logistic, n = 26,320):** partial TPP b = 0.021, OR 1.021
[1.000, 1.042]; three-set b = −1.28, OR 0.278 [0.204, 0.378]; McFadden
pseudo-R² = 0.042.

**Table S2 (validity, men's singles):** 2006 World Championships reconstructed
25.4 vs official aggregate 25.5 (match-mean 25.2); Gómez-era reconstructed
34.0 (32.7–35.2) vs official Tour-MS-2018 aggregate 34.2 — agreement within
≈0.3 s/point.

**Sensitivity checks (Tables S6–S8; `10_sensitivity.txt`):**
*Break-point sensitivity (Table S6):* post-knot World Championship slopes are
−0.09 (knot 2017), −0.16 (2018) and −0.27 (2019) s/year at match level
(annual-aggregation −0.12, −0.19, −0.31); none indicates a sustained rise.
*Retirement worst case (Table S7):* the Tour annual slope is 0.295 for
completed matches and 0.297 when all 392 retirements are included at partial
TPP (n = 26,320); annual RET% ranges 0.90–2.24% and WO% 0.34–2.89% (2022
spike after the COVID restart).
*Minimum detectable slope:* ≈0.26 s/year from the annual-aggregation fit
(SE 0.087, df 13; ≈0.16 s/year using the match-level cluster SE), at two-sided
α = .05 and 80% power.
*Unobserved-stoppage envelope:* with ≈83.7 points per match, the +2.23
s/point rise requires ≈26.7 extra recorded seconds per match per year and
≈187 s (3.11 min) cumulatively by 2025 — equivalent to an extra ~19 ten-second
reviews, ~6 thirty-second towel/ball-change episodes or ~3 sixty-second medical
time-outs per match.
*Recording-change simulation (Table S8):* uniform ±1–3 minute shifts change
only the level (Tour slope 0.295–0.296; World Championship post slope −0.09);
a ramped 0→3 minute shift over 2018–2025 would move the Tour slope to 0.62
(or −0.03) and the World Championship post slope to +0.22 (or −0.41), so only
a large monotonic multi-year drift could alter the conclusions.

**Elo control (singles only; Tables S9–S10; `11_elo_control.txt`):**
*Merge audit (Table S9):* all 10,484 World Tour singles matches link (100.0%);
World Championships 2007–2025 link at 100% each year (1,610/1,613 through 2025;
97.4% in 2006 with three unknown-player matches); the 124 matches of the 2026
World Championships cannot be linked (external data end in 2025). 11,374 links
match on name plus score and 720 score-assisted links resolve via the same score
verification.
*Models (Table S10):* World Championships singles (n = 1,610) post-2018 slope
0.017 (SE 0.068, p = .80) at baseline and 0.039 (SE 0.068, p = .56) with the
absolute pre-match Elo gap (per 100 points; Elo coefficient −0.434, SE 0.046,
p < .001); the 2011-onward subset gives 0.055 vs 0.078. World Tour singles
(n = 10,484) annual slope 0.379 (SE 0.036) at baseline and 0.379 (SE 0.035)
with the Elo gap (coefficient −0.306, SE 0.043); excluding 2020 or 2020–2021
or adding the three-set indicator leaves it at 0.374–0.377. Controlling for
player strength therefore does not change either trend.
*Threshold sensitivity:* the external release's duration cleaning removes
sentinel/extreme durations only (<2 and >200 min; the 29.0/33.9 min figures are
two-/three-game means, not thresholds); these rules remove 0 matches here, and an
18-minute floor removes 2 World Championships and 11 Tour matches without
changing the slopes (0.018 / 0.377 s/year).

**Extra sensitivity (Table S11; `12_extra_sensitivity.txt`):**
*Excluding 2026:* the all-discipline World Championships sample loses 259
matches (n = 3,868 → 3,609); the segmented fit gives β1 = 0.751, β2 = −0.842
and a post-2018 slope of −0.090 (cluster SE 0.068, p = .18), versus −0.092
(SE 0.056, p = .10) in the full sample.
*P1/P99 winsorization:* clipping 39 matches at each tail of the World
Championships sample (bounds 17.70/47.75) leaves the post-2018 slope at −0.088
(SE 0.054, p = .11); clipping 237 low and 260 high Tour matches (bounds
20.00/46.79) leaves the Tour annual slope at 0.289 (SE 0.040), versus the
full-sample 0.295 (SE 0.041). The main analysis retains the full sample.
**Same-rules subperiod sensitivity (Table S12; `13_subperiod_sensitivity.txt`):** refitting the main fixed-effects specification on unchanged-rules post-COVID windows leaves the Tour slope positive and significant: 2021-2025 0.231 s/year (cluster SE 0.077, p = .003, n = 17,260, five year clusters; mean TPP 31.7 to 32.4); 2022-2025 0.278 (SE 0.113, p = .013, n = 15,822, four year clusters; 31.4 to 32.4). The full 2018-2025 window reproduces 0.295 (SE 0.041), as in the manuscript.

Small differences in the second decimal relative to the manuscript arise from
rounding and from whether a value is quoted as aggregate or match-mean TPP; the
logs in `outputs/` print full precision and state which basis is used.

---

## 9. Figures

| Figure | File | Produced by |
|---|---|---|
| 1 | TPP operational schematic | `08_make_figures.py` |
| 2 | World Championships segmented trend, knot 2017 | step 2 data / step 8 |
| 3 | World Tour annual TPP, 2018–2025 (2020 open marker) | step 1 data / step 8 |
| 4 | +3.37 min decomposition with event-cluster CIs | step 3 / step 8 |
| 5 | discipline × round TPP heatmap | step 4 / step 8 |
| 6 | TPP × retirement rate by discipline and round | step 4 / step 8 |
| 7 | sample-flow diagram | step 1 counts / step 8 |

The copies in `figures/` are the exact manuscript figures; `figures/recomputed/`
contains fresh renderings from the raw data and should agree with them.

---

## 10. Known definitional caveats

1. **MATCH DURATION start/stop rules are not publicly documented.** If BWF's
   internal timing rules changed across tournament-software versions, the level
   of TPP could shift; a post-2017 level-shift check found no significant
   discontinuity, which does not fully rule out definitional drift.
2. **TPP cannot identify mechanisms.** It cannot separate rally time from pause
   time, nor attribute changes to tactics, physiology, challenges, medical
   stoppages, towelling or shuttle changes. All mechanism language in the paper
   is explicitly hypothetical.
3. **Partial TPP for retirements is truncated** at abandonment and is used only
   descriptively/exploratorily.
4. **2020 is a disrupted, empty-stadium season** (879 completed Tour matches vs
   ≈3,900 in 2018–2019) and is shown with an open marker; it is retained in the
   data but not interpreted as a normal season.

---

## 11. Data and code availability

The two BWF source workbooks, the external Elo tables and all scripts are
included here. During review the materials are available at an anonymised
GitHub repository; a persistent archive DOI (e.g. a GitHub release archived in
Zenodo) will be provided at the revision/acceptance stage and the anonymised
review-link in the manuscript will be replaced by it. The deposited archive will
have the same contents as this folder.

---

## 12. Licence

* **Code:** released under the MIT Licence (see `LICENSE`).
* **BWF-derived data:** derived from publicly accessible BWF match results; BWF
  and the tournament-software provider retain rights to the underlying records.
  This redistribution is for academic, non-commercial reproducibility; cite the
  manuscript and the original BWF source when reusing.
* **External Elo tables (`data/raw_external/`):** Sun & Zhang (2026), Harvard
  Dataverse, https://doi.org/10.7910/DVN/RSAYV5, licensed under
  **Creative Commons Attribution 4.0 International (CC BY 4.0)**; reuse must
  attribute Sun and Zhang and cite the data descriptor
  https://doi.org/10.1038/s41597-026-08408-4 (see `SOURCE_AND_LICENSE.txt`).
