# Issue Backlog — seed for the GitHub Project board

> **This file is a one-time seed, not a tracker.** Paste each issue below into
> GitHub (the issue forms in `.github/ISSUE_TEMPLATE/` have the same fields),
> then treat GitHub as the source of truth and delete this file. Keeping both
> would let them drift apart.
>
> Owners use roles, not handles. Replace them with GitHub handles when you
> create the issues. Numbering follows [build guide §20](build_guide.md), so
> "Blocked by #6" means the EDA gate.

## One-time board setup

**Milestones:** `0 - Repository scaffold` · `1 - Reproducible source data` ·
`2 - EDA gate` · `3 - Production data pipeline` · `4 - Baselines, model, calibration` ·
`5 - Routing, scoring, recommendations` · `6 - FastAPI service` · `7 - React website` ·
`8 - Responsible AI and final evaluation` · `9 - Demo, documentation, release`

**Labels:** `area:data` `area:eda` `area:model` `area:geospatial` `area:api`
`area:frontend` `area:docs` `area:presentation` `priority:must` `priority:should`
`priority:stretch` `blocked` `bug`

**Board columns:** Backlog → Ready → In Progress → Review → Verified → Done

**Rule:** issues #7–#26 carry the `blocked` label until #6 closes. Documentation
drafting may proceed; unsupported analytical claims may not.

---

## Milestone 0 — Repository scaffold

### #1 Scaffold Codespaces repository
- **Owner:** CS major · **Reviewer:** Mason · **Labels:** `area:docs` `priority:must`
- **Outcome:** a fresh Codespace runs `make setup`, `make lint`, and `make test` without manual repair.
- **Status note:** a draft scaffold exists on branch `chore/repository-scaffold`. The CS major reviews it as a proposal and owns the final shape.
- **Acceptance**
  - [ ] Fresh Codespace completes `make setup`
  - [ ] `uv.lock` and `frontend/package-lock.json` generated and committed
  - [ ] `python -c "import stormroute"` succeeds
  - [ ] FastAPI `/health` returns 200
  - [ ] Vite placeholder page loads on port 5173
  - [ ] `make lint` and `make test` pass; CI green including the frontend job
  - [ ] No secrets or absolute local paths tracked
  - [ ] Team has read and accepted [ADR 0000](adr/0000-specification-precedence.md)
  - [ ] Branch protection enabled on `main` after merge
- **Evidence:** CI run link; screenshot of `/health` and the Vite page in a Codespace.

---

## Milestone 1 — Reproducible source data

### #2 Add NOAA source manifest and downloader
- **Owner:** Mason (downloader, parsing) · Econ/Stats major (manifest, source documentation) · **Reviewer:** Econ/Stats major · **Labels:** `area:data` `priority:must`
- **Outcome:** one command downloads the 2015–2024 NOAA detail files reproducibly; a tested module turns them into clean North Carolina flood events.
- **Acceptance**
  - [ ] `make download` fetches or locates all ten annual files
  - [ ] Resolved filenames, checksums, and access times are recorded
  - [ ] A file that differs from its record is never overwritten silently
  - [ ] `--sample` mode works with no network
  - [ ] Hazard filter is exactly Flood, Flash Flood, Debris Flow
  - [ ] County FIPS keep leading zeroes; timestamps are timezone-aware UTC
  - [ ] Unique event IDs verified; duplicates reported
  - [ ] `data/data_manifest.yaml` updated with access date and resolved files (Econ/Stats)
- **Evidence:** test output; download record; before/after filter counts.

### #3 Add North Carolina county boundaries
- **Owner:** CS major · **Reviewer:** Mason · **Labels:** `area:data` `area:geospatial` `priority:must`
- **Outcome:** a script downloads 2024 TIGER/Line counties and a module exposes exactly 100 NC counties keyed by 5-character FIPS.
- **Acceptance**
  - [ ] `scripts/download_boundaries.py` implemented and wired into `make download`
  - [ ] `stormroute.data.geography` returns 100 counties, FIPS as strings
  - [ ] Works in a fresh Codespace; paths resolve from the repo root
  - [ ] Test asserts the county count and FIPS format
- **Evidence:** test output; a quick plot of the 100 counties.
- **Unblocks:** the EDA choropleth (#5, section 7) and route spatial joins (#14).

### #4 Create sample data fixtures
- **Owner:** Mason · **Reviewer:** Econ/Stats major · **Labels:** `area:data` `priority:must`
- **Outcome:** tiny tracked fixtures let every EDA section and every data test run with no download.
- **Status note:** first versions exist in `data/sample/`. The remaining work is to confirm they cover every EDA section once the notebook exists.
- **Acceptance**
  - [ ] Every edge case in `data/sample/README.md` is exercised by a test
  - [ ] The EDA notebook executes end to end in sample mode
  - [ ] Fixtures stay under a few kilobytes and contain public data only

---

## Milestone 2 — EDA gate

### #5 Build and execute Storm Events EDA notebook
- **Owner:** Mason (sections 1–5, 9–11) · Econ/Stats major (sections 3's missingness table, 6–8) · both draft section 12 · **Reviewer:** CS major · **Labels:** `area:eda` `priority:must`
- **Blocked by:** #2; section 7 also needs #3
- **Outcome:** `notebooks/01_storm_events_eda.ipynb` answers the six gate questions with reproducible evidence.
- **Acceptance**
  - [ ] Restart-and-run-all succeeds on full data and in sample mode
  - [ ] All seven `outputs/figures/eda_*.png` exported to the figure standard
  - [ ] Class imbalance quantified; every split contains positives
  - [ ] Leakage audit classifies every candidate feature
  - [ ] ≥ 10 event records manually spot-checked against NOAA event pages
  - [ ] `reports/eda/eda_findings.md` completed
- **Evidence:** figures; headline counts; notebook run date and source versions.
- **Note:** the section split is a proposal for the team to confirm.

### #6 Review and approve EDA gate
- **Owner:** Mason (records decision) · **Reviewers:** Econ/Stats major (interpretations and claims), CS major (fresh-Codespace execution) · **Labels:** `area:eda` `priority:must`
- **Blocked by:** #5
- **Outcome:** a recorded proceed / change scope / stop decision.
- **Acceptance**
  - [ ] PR `eda: validate North Carolina flood-event target and features` approved by two teammates
  - [ ] Every gate condition in build guide §9 met, or a decision issue opened
  - [ ] Decision and reviewer handles recorded in `eda_findings.md`
- **Closing this issue unblocks #7–#26.**

---

## Milestone 3 — Production data pipeline

### #7 Fetch historical hourly weather
- **Owner:** Mason · **Reviewer:** Econ/Stats major · **Labels:** `area:data` `priority:must` `blocked`
- **Blocked by:** #6
- **Acceptance**
  - [ ] `scripts/fetch_weather.py` retrieves all required variables for 100 counties, 2015–2024
  - [ ] Resumable; completed county-years are skipped
  - [ ] Coverage gaps recorded by county and year
  - [ ] Manifest updated with source, access method, and date

### #8 Build county × six-hour labels
- **Owner:** Mason · **Reviewer:** Econ/Stats major · **Labels:** `area:data` `priority:must` `blocked`
- **Blocked by:** #6
- **Acceptance**
  - [ ] Full 100-county × six-hour grid, 2015–2024, anchored at 00:00 UTC
  - [ ] Labels follow the locked onset rule (`window_start <= begin < window_end`)
  - [ ] Tests: midnight, year-end, exact boundary, multi-window events
  - [ ] Split column assigned by calendar year; splits disjoint
  - [ ] Row count equals expected count after documented exclusions

### #9 Add rolling weather features and leakage tests
- **Owner:** Mason · **Reviewer:** Econ/Stats major · **Labels:** `area:data` `priority:must` `blocked`
- **Blocked by:** #6, #7, #8
- **Acceptance**
  - [ ] 1/3/6/24/72-hour features read only hours at or before window start
  - [ ] Perturbing future hours leaves every feature unchanged (tested)
  - [ ] No post-event field and no SVI field in the feature matrix (tested)
  - [ ] `make data` rebuilds `county_windows.parquet` from raw inputs
  - [ ] `outputs/metrics/data_quality.json` written; `docs/data_card.md` updated
  - [ ] `notebooks/02_weather_feature_validation.ipynb` executes

---

## Milestone 4 — Baselines, model, calibration

### #10 Train climatology baseline
- **Owner:** Mason · **Independent check:** Econ/Stats major computes climatology separately and compares · **Labels:** `area:model` `priority:must` `blocked`
- **Blocked by:** #9
- **Acceptance**
  - [ ] Smoothed county-month rate fit on training years only
  - [ ] Two independent calculations agree

### #11 Train logistic-regression baseline
- **Owner:** Mason · **Reviewer:** Econ/Stats major · **Labels:** `area:model` `priority:must` `blocked`
- **Blocked by:** #9
- **Acceptance**
  - [ ] Regularized model on the final feature set, fit on training years
  - [ ] Evaluated on 2022 with the same metrics as every other model

### #12 Train monotonic boosted model
- **Owner:** Mason · **Reviewer:** Econ/Stats major · **Labels:** `area:model` `priority:must` `blocked`
- **Blocked by:** #10, #11
- **Acceptance**
  - [ ] Monotonic constraints from `configs/model.yaml` applied
  - [ ] Hyperparameters chosen on 2022 only; 2024 never read
  - [ ] Monotonicity spot checks pass
  - [ ] Manifest records class, versions, features, constraints, hyperparameters, data version, SHA, checksum

### #13 Calibrate and evaluate on temporal holdouts
- **Owner:** Mason (calibration) · Econ/Stats major (independent evaluation) · **Labels:** `area:model` `priority:must` `blocked`
- **Blocked by:** #12
- **Acceptance**
  - [ ] Sigmoid calibration fit on 2023 only; Brier does not materially worsen
  - [ ] Single final evaluation on 2024: PR-AUC, Brier, log loss, calibration curve, recall and precision at top 1%
  - [ ] Bootstrap intervals grouped by storm episode
  - [ ] Adoption rule applied; fallback used if the boosted model fails it
  - [ ] Comparisons: baselines, raw vs calibrated, all-2024 vs Helene, rural vs populous, with/without historical rate
  - [ ] `notebooks/03_model_evaluation.ipynb` reproduces all numbers from saved predictions
  - [ ] `docs/model_card.md` completed

---

## Milestone 5 — Routing, scoring, recommendations

### #14 Sample candidate routes and assign counties
- **Owner:** CS major · **Reviewer:** Mason · **Labels:** `area:geospatial` `priority:must` `blocked`
- **Blocked by:** #6, #3
- **Acceptance**
  - [ ] Two or more candidate routes per trip
  - [ ] Samples every 5–10 km and at county boundaries, with arrival times
  - [ ] Spatial join to NC counties; out-of-state portions flagged, not snapped
  - [ ] Repeated samples collapse per (county, window)

### #15 Implement cumulative-hazard trip score
- **Owner:** Mason · **Reviewer:** CS major · **Labels:** `area:model` `priority:must` `blocked`
- **Blocked by:** #13
- **Acceptance**
  - [ ] Formula matches `docs/risk_methodology.md` and `configs/scoring.yaml` exactly
  - [ ] Invariant tests: zero risk → 100; monotone in probability and time; splitting-invariant; deterministic

### #16 Add official-alert policy floors
- **Owner:** Mason · **Reviewer:** CS major · **Labels:** `area:model` `priority:must` `blocked`
- **Blocked by:** #15
- **Acceptance**
  - [ ] Each severity applies its configured floor
  - [ ] Tested: an alert can never improve a score
  - [ ] Code floors equal config floors (tested)

### #17 Rank route and departure-time recommendations
- **Owner:** Mason · **Reviewer:** CS major · **Labels:** `area:model` `priority:must` `blocked`
- **Blocked by:** #14, #16
- **Acceptance**
  - [ ] Candidates: routes × departures +2 … +12 h
  - [ ] Recommend only at ≥ 5-point improvement; never the current trip
  - [ ] Score delta and time cost always reported; deltas equal displayed-score differences
  - [ ] "No safer option found" path tested
  - [ ] Full candidate table retained for audit

### #21 Add cached Helene-era replay
- **Owner:** CS major · **Reviewer:** Mason · **Labels:** `area:geospatial` `area:api` `priority:must` `blocked`
- **Blocked by:** #17
- **Acceptance**
  - [ ] `make demo-cache` freezes Asheville → Charlotte routes, weather, alerts, scores
  - [ ] Artifacts checksummed; expected values copied into `docs/demo_runbook.md`
  - [ ] Replay works with the network disabled

---

## Milestone 6 — FastAPI service

### #18 Build FastAPI score endpoint
- **Owner:** CS major + Mason · **Reviewer:** Econ/Stats major · **Labels:** `area:api` `priority:must` `blocked`
- **Blocked by:** #17
- **Acceptance**
  - [ ] Endpoints: `/health`, `/api/v1/scenarios[/{id}]`, `/api/v1/trips/score`, `/api/v1/methodology`
  - [ ] Pydantic contracts; OpenAPI at `/docs`
  - [ ] Invalid coordinates and timestamps → helpful 422
  - [ ] Cached mode works offline; `/health` reports artifact availability
  - [ ] Request IDs in logs; no secrets in responses or logs; CORS allowlist

---

## Milestone 7 — React website

### #19 Build trip planner page
- **Owner:** CS major · **Reviewers:** Mason (product), Econ/Stats major (usability) · **Labels:** `area:frontend` `priority:must` `blocked`
- **Blocked by:** #6 (can build against `demoScore.json` before #18)
- **Acceptance**
  - [ ] Origin, destination, departure, analyze button, visible safety disclaimer
  - [ ] Keyboard navigable; labeled inputs; inline validation

### #20 Build results map and explanation panels
- **Owner:** CS major · **Reviewers:** Mason, Econ/Stats major · **Labels:** `area:frontend` `priority:must` `blocked`
- **Blocked by:** #19; live data needs #18
- **Acceptance**
  - [ ] Score with band and meaning; segment-colored map; worst segment and arrival
  - [ ] Official alerts above the recommendation, visually distinct
  - [ ] Before/after score, delta, and time cost shown together
  - [ ] Loading, empty, success, partial-data, and failure states
  - [ ] Risk never encoded by color alone; WCAG AA contrast; mobile width works
  - [ ] Component tests and the Playwright demo flow pass

---

## Milestone 8 — Responsible AI and final evaluation

### #22 Complete responsible-AI and subgroup audit
- **Owner:** Econ/Stats major · **Reviewer:** Mason · **Labels:** `area:docs` `priority:must` `blocked`
- **Blocked by:** #13
- **Acceptance**
  - [ ] Slice table: statewide, rural/populous, mountain/Piedmont/coastal, sparse reporting, Helene, non-hurricane event, high rain without a report
  - [ ] Weak slices reported as prominently as strong ones
  - [ ] Claim audit: every public claim has a source or metric
  - [ ] `docs/responsible_ai.md` completed

### #23 Conduct usability tests
- **Owner:** Econ/Stats major · **Reviewer:** Mason · **Labels:** `area:frontend` `priority:must` `blocked`
- **Blocked by:** #20
- **Acceptance**
  - [ ] Three people who did not build the app complete the five tasks
  - [ ] Misunderstandings recorded; interface fixes filed as issues and closed

---

## Milestone 9 — Demo, documentation, release

### #24 Write README, DevPost, and presentation
- **Owners:** Mason (narrative, presentation), Econ/Stats major (DevPost, citations, claim check), CS major (screenshots, demo) · **Labels:** `area:docs` `area:presentation` `priority:must` `blocked`
- **Blocked by:** #13, #20
- **Acceptance**
  - [ ] README sections 2, 7, 9, 12 filled; no remaining TBD
  - [ ] DevPost draft complete with final commit SHA
  - [ ] Seven-minute talk rehearsed at least three times, timed

### #25 Run final clean-Codespace verification
- **Owner:** CS major · **Reviewer:** Mason · **Labels:** `area:docs` `priority:must` `blocked`
- **Blocked by:** #24
- **Acceptance**
  - [ ] Clean clone in a fresh Codespace: `make setup`, `make test`, `make verify` pass
  - [ ] EDA notebook executes; demo works offline
  - [ ] Every item in the build guide §16 release checklist ticked

### #26 Tag the competition release
- **Owner:** Mason · **Reviewers:** all · **Labels:** `area:docs` `priority:must` `blocked`
- **Blocked by:** #25
- **Acceptance**
  - [ ] Tag `v1.0.0-cdc2026`, title "StormRoute — Carolina Data Challenge 2026 Submission"
  - [ ] Release links model manifest, metrics, EDA report, DevPost, and demo URL
