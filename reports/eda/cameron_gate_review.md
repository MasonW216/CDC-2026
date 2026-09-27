# Cameron's EDA gate review

Reviewed PR #18 branch `Mason` at `c7876bc61e5311c7441a0d615e65db126f710d95`,
September 26, 2026 (America/New_York). Contribution branch:
`eda/cameron-gate-review`; intended PR base: `Mason`. Scope was agreed with Mason
before branching. Earlier missing sections and all seven required figures already
existed on the reviewed branch; the PR description was stale.

**Recommendation: change scope to retrospective reported-event feasibility;
request changes before approving the gate.** The label is constructible, and its
rarity alone does not justify stopping. The evidence does not establish statewide
live prediction quality, adequate split power, or road-level hazard probabilities.
This is an analytical recommendation, not Mason's team decision or an independent
approval of Cameron's own sections. Jeffrey's review remains required.

## Evidence checked

- Downloaded the exact ten NOAA releases and matched all recorded SHA-256 hashes.
- Executed every notebook cell from fresh kernels in sample and full modes on
  Windows/Python 3.11.9. Both passed, including the independent split reconciliation.
  An initial full-run kernel startup timed out before executing cells; retry with
  an isolated IPython profile passed. This is **not a fresh-Codespace verification**.
- Independently rebuilt bins from published start-time text plus the fixed UTC
  offset, using retained event IDs. Counts match: 1,096 / 53 / 78 / 272 positives
  in train / selection / calibration / test, across 1,461,200 total windows.
- Re-exported all figures. The four requested files exist; sample outputs are
  isolated from full outputs. Counts, missingness, sparse counties, and episode
  concentration are summarized in `eda_findings.md` with denominators and limits.
- Python tests: 211 passed, two optional external-service tests skipped. One
  FastAPI/Starlette dependency deprecation warning. Ruff lint/format and Mypy pass.
  Frontend checks and fresh-Codespace execution have not been certified here.

## Requested fixes in Mason's sections / PR

1. **Reconcile section 11's contradictory availability claims.** `s11-audit` and
   `s11-end` call all retained weather features known at departure and say the
   remaining risk is not leakage. `s11-cameron-intro` correctly explains retrospective
   publication. Valid-time perturbation tests cannot establish issue-time availability.
   Retain conditional historical eligibility and require actual issue-time checks for
   live forecasts. Remove the stale statement that section 10 has not been completed.
   A county event rate fit on all 2015–2021 labels is not past-only for early training
   rows; require out-of-time construction and source publication lag checks.
2. **Revise section 12's positive-count verdict.** “Yes, thin in places” infers
   adequacy from nonzero counts. Selection has only 53 positive windows in 28 reported
   episodes, calibration 78 in 49. State that adequacy remains unestablished; a single
   changed detection shifts recall by 1.89 or 1.28 percentage points. Avoid tuning
   flexible calibration or selecting many alternatives on these small samples.
3. **Keep weather conclusions at their measured scale.** The rainfall comparison is
   for three city-point series, not statewide county coverage. A single grid cell is
   not a county average; no county point proves road inundation. Correct statewide or
   live-availability language in the PR body. The report has been corrected here.
4. **Protect the manual-review sheet.** `s04-spotcheck-pick` unconditionally writes
   blank reviewer columns in full mode. Preserve existing human evidence by event ID
   or export new candidates separately. This review runner saved and restored the
   original sheet; none of its human-review fields was fabricated or marked complete.
5. **Complete the ten human source checks and crossed reviews.** Matching NOAA's two
   timestamp representations is internal consistency, not independent source validation.
   A ten-record spot check cannot certify all 1,813 daylight-saving-month records.
   Record discrepancies and their effect. Jeffrey reviews Cameron's sections; Cameron's
   fresh-Codespace check and Mason's signed gate decision remain outstanding.
6. **Update stale integration claims.** All figures and sections are present. The
   whole-year totals 295 and 272 cannot be attributed to Florence and Helene. The
   report now distinguishes annual counts, episode concentration, and the exploratory
   Helene date window. Reconcile superseded prose in the old scoped review reports.
7. **Resolve pre-gate web scope before merge.** `docs/NEXT_STEPS.md` identifies web
   and geocoding commits already included in PR #18. The team must resolve that scope
   against the gate rule; this EDA contribution does not approve those changes.

## Checklist and conditional handoff

- [x] Agree contribution scope; branch from `Mason` and target `Mason`.
- [x] Missingness, temporal, geographic sections and four figures exist and rerun.
- [x] State denominators, missing meanings, exclusions, sparse-county limitations.
- [x] Independently check split positives, dependence, and leakage claims.
- [x] Restart and execute the complete notebook in full and sample modes locally.
- [x] Update findings and document requested fixes.
- [ ] Contribution merged into `Mason`; review its resulting head after integration.
- [ ] Jeffrey independently reviews Cameron's sections.
- [ ] Fresh-Codespace execution and ten human source checks recorded.
- [ ] Mason records the team proceed/change-scope/stop decision.
- [ ] PR #18 passes the gate and merges into `main`.
- [ ] After a team **proceed** decision, branch `evaluation/protocol` from updated `main`.

The later evaluation protocol must be written and approved before training. Compare
climatology, regularized logistic regression, and the candidate on the same 2022 rows;
specify PR-AUC definition and prevalence reference, Brier comparison, calibration
diagnostics, an operational alert budget and precision/recall criteria, and fixed
county/season/storm slices. Prespecify paired grouped uncertainty, including negative
time blocks, and report undefined or underpowered slices honestly. Use 2023 only for
the prespecified calibration procedure; freeze all preprocessing, model, calibration,
thresholds, slices, and acceptance criteria before the single 2024 model test. Report
53 and 78 positives as interpretation constraints. Numerical operational acceptance
thresholds need a team decision, not invention after results. This handoff is not an
approved evaluation protocol and does not authorize model training.
