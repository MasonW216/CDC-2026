# Next steps for the three of us

Written 2026-09-26. This is the single list of what each person does next. It replaces
any earlier per-person status notes.

## Where we are

- All work from Mason, Cameron, and Jeffrey is on one branch, `Mason`. The old `Cameron`
  and `Jeffrey` branches are deleted; their final states are kept as tags
  `archive/cameron`, `archive/jeffrey`, `archive/mason`.
- `main` does not have this work yet. It lands through the EDA gate pull request (PR #18).
- The EDA notebook is done and runs in full and sample mode. All 7 required figures exist.
- **The EDA gate (#6) is open.** Nothing from Milestone 3 onward (production weather
  fetch, county-window table, features, model, scoring, API, website) starts until it
  closes. This is a hard rule in CLAUDE.md.

## What must happen to close the gate

Four things, all human. Each has one owner.

| # | What | Owner | Done when |
|---|---|---|---|
| 1 | Spot-check 10 events against an independent source | Mason | `reports/eda/spot_check_candidates.csv` has `reviewer`, `county_matches`, `utc_time_matches_nws_product` filled for all 10 rows |
| 2 | Review the Econ/Stats sections of the notebook (3 and 6–8): do the numbers and claims hold? | Jeffrey | Written approval or a list of changes on PR #18 |
| 3 | Review the rest of the notebook (sections 1–2, 4–5, 9–12) and run it from scratch in a fresh Codespace | Cameron | Written approval on PR #18, plus a note that `make eda` ran clean |
| 4 | Record proceed / change scope / stop | Mason | Notebook section 12 and `reports/eda/eda_findings.md` state the decision |

Cameron wrote sections 3 and 6–8, so Cameron cannot review them. Mason wrote the rest,
so Mason cannot approve them. That is why the review is crossed. Two approvals are
required (build guide §9).

## Mason

1. Push `Mason` and reopen PR #18.
2. Spot-check the 10 events (item 1). For each: open the `ncei_event_page` link, confirm
   the county, then confirm the time against an independent record such as the Iowa
   Environmental Mesonet local storm reports. Record any mismatch in `notes`; two events
   (663370 and 666045, both October 2016) test the daylight-saving assumption.
3. Update PR #18: tick "every exported figure exists (7 of 7)", update the test count, and
   say that Cameron's and Jeffrey's work is merged in.
4. After both approvals, record the gate decision (item 4).
5. Vote on the three proposed ADRs (0005, 0006, 0007) in the vote issue.

## Cameron

1. Fetch and switch to `Mason`: `git fetch --all --prune && git switch Mason && git pull`.
2. Read `reports/eda/eda_findings.md` and notebook sections 1–2, 4–5, 9–12.
3. Run the notebook in a fresh Codespace with `make eda`, then check that it finishes
   without errors and that the figures in `outputs/figures/` match the notebook.
4. Post your approval or requested changes on PR #18.
5. **Check the merge choices Mason made in your sections**, and object if wrong:
   - Your class-imbalance figure was renamed `eda_class_imbalance_2020` to avoid a name clash.
   - Both versions of sections 9 and 11 were kept, with yours labelled as yours.
   - Wording was aligned to your "results do not establish live accuracy" correction.
6. Vote on ADRs 0005–0007.

## Jeffrey

1. Fetch and switch to `Mason` as above.
2. Review notebook sections 3 and 6–8 (Cameron's): the missingness table, seasonality,
   geography, and reported-impacts claims. Re-derive at least two numbers independently.
3. Post your approval or requested changes on PR #18.
4. **Decide about your web commits** (planner page and geocoding). They are now on
   `Mason`, but CLAUDE.md says no website code lands before the gate closes. Either the
   team agrees they are exempt, or they are held back. Please raise it in the PR.
5. Vote on ADRs 0005–0007; Mason's conditions for 0005 and 0007 are in the vote issue.
6. Before doing anything else, confirm nothing unpushed exists on your machine that is not
   in `archive/jeffrey`.

## After the gate closes

These are blocked until the gate closes. Each starts from a fresh branch off `main`,
named `area/short-description`.

- Milestone 3: fetch hourly weather per ADR 0005 (with a de-accumulation test), build the
  county × six-hour table, add rolling features with leakage tests.
- Milestone 4: climatology and logistic baselines, monotonic boosted model, calibration.

Owners for these are not assigned yet. Decide them in the PR discussion once the gate
closes.

## Housekeeping

- Turn on branch protection for `main` (currently off): require a PR and one approval.
- Everyone works on short-lived branches from `main` after PR #18 merges. Merge PRs as
  merge commits so each person's history stays visible.
- Do not delete `Mason` or the archive tags until PR #18 is merged into `main`.
- Still open: a Copernicus account and API key for the weather retrieval, and who sets
  `start_utc` in `.claude/event.json`.
