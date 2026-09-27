# Status: Mason's workstream

**As of 2026-09-26.** Drafted with Claude Code for Mason. Every fact below was checked against Git,
GitHub, or a test run today. This is a snapshot, not a tracker: once the GitHub issues exist, update
or delete it. If you like the format, add `status_cs.md` and `status_econ.md` beside it.

## In one minute

- The **EDA gate** (issue #6) is not closed. My part of the notebook is done and CI is green on
  **[PR #18](https://github.com/MasonW216/CDC-2026/pull/18)** (draft).
- The gate needs four things I can't do alone: the Econ/Stats sections, a **human spot check** of 10
  events, two reviewer approvals, and then my proceed / change / stop decision.
- **Three ADRs need everyone's vote:** [issue #19](https://github.com/MasonW216/CDC-2026/issues/19).
  ADR 0005 (weather) blocks Milestone 3.
- Milestone 3 onward stays blocked until the gate closes.

## Done

| What | Where | Evidence |
|---|---|---|
| NOAA Storm Events download, 2015–2024, with checksums and a "never overwrite a changed file" rule | `scripts/download_noaa.py`, `src/stormroute/data/noaa.py` | on `main`; re-download gave identical checksums |
| Events parsing and validation (county FIPS padded, UTC times, exact hazard filter, every excluded row counted) | `noaa.py`, `validation.py`, `tests/data/test_noaa.py` | on `main`; 69 tests |
| Label rule fixed to the build guide's **onset** rule | `configs/data.yaml`, ADR 0000/0001 | on `main` |
| EDA notebook sections 1–5 and 9–12 | `notebooks/01_storm_events_eda.ipynb` | PR #18; runs clean on full data and sample data; CI notebook job green; all 2,220 parsed times match NOAA's own date-time text |
| Written findings report | `reports/eda/eda_findings.md` | PR #18 |
| 3 of 7 EDA figures | `outputs/figures/` | PR #18 |
| Feature leakage audit (17 candidate groups) | notebook section 11 | config and audit agree |
| 10 spot-check candidates chosen | `reports/eda/spot_check_candidates.csv` | **0 of 10 checked so far** |
| Review of ADRs 0005–0007 | [issue #19](https://github.com/MasonW216/CDC-2026/issues/19) | numbers in ADR 0004 re-derived and match |
| 26-issue seed for the board | `docs/issue_backlog.md` | issues not created yet |

**Headline numbers** (full data, onset rule): 2,220 qualifying events; **1,499 of 1,461,200**
county-windows positive (0.103%); positives by split **1,096 / 53 / 78 / 272** (train / select /
calibrate / test). The 2022 selection year is thin. After merging current `main`, 190 tests pass.

## Decisions made this week

- **Label:** a window is positive when an event *begins* in it (ADR 0001). Overlap would leave 17 events unlabeled.
- **Hazards:** Flood, Flash Flood, Debris Flow. **Coastal Flood stays excluded** (tide-driven, zone-reported).
- **Weather:** Copernicus ERA5-Land, gusts from ERA5, because Open-Meteo's ERA5-Land has no rainfall or wind. Method: ADR 0005 (proposed).
- **Times:** NOAA's `EST-5` all year is NWS policy (NWSI 10-1605 §2.3), so the fixed offset is correct. The spot check verifies compliance.

## Waiting on

| Item | Owner | What's needed |
|---|---|---|
| EDA section 3 (missingness) and sections 6–8, plus 4 figures: `eda_events_by_year`, `eda_monthly_seasonality`, `eda_county_choropleth`, `eda_missingness` | Econ/Stats (Cameron) | The county map can start now; boundaries are on `main` |
| Spot check of 10 events | Anyone | Fill the blank columns in `spot_check_candidates.csv`. One event is already matched to an NWS report, as a worked example |
| Fresh-Codespace run of PR #18 | CS (Jeffrey) | `make setup`, `make eda`; report any failure |
| Two approvals, then the gate decision | Cameron, Jeffrey, then Mason | Reviewers tick the checklist in the PR |
| Votes on ADR 0005, 0006, 0007 | All three | Comment on issue #19 |
| Where the ADR 0005 weather files live | Jeffrey | Share them and port the retrieval into `scripts/fetch_weather.py` |
| Review of [PR #14](https://github.com/MasonW216/CDC-2026/pull/14) (source provenance) | Mason | Planned next |

## Plan

**Now, before the gate**
1. Mason: do or hand off the spot check, review PR #14, finish ADR votes.
2. Mason: record the gate decision in notebook section 12 and `eda_findings.md` once both reviews are in.

**After the gate closes** (issues #7–#9, Milestone 3)
3. Weather fetch for all 100 counties, ported from the ADR 0005 retrieval and reproducible from `make download`.
4. Build the county × six-hour label table (`data/processed/county_windows.parquet`) with the onset rule and split labels.
5. Rolling weather features with a test proving no feature reads the future.

**Then** Milestone 4 (climatology, logistic regression, boosted model, calibration on 2023, one evaluation on 2024), then scoring and recommendations (#15–#17). Nothing here starts early.

## Open questions

1. **Routing is on `main` while the gate is open.** The backlog lists #14 as blocked by #6, and `CLAUDE.md` says no production code lands before the gate. County boundaries and the route sampler don't depend on any model, so I'd suggest we treat them as a pre-gate exception and note that in PR #18. Agree, or hold?
2. **ADR 0004** was marked Accepted by PR #16. Did all three of us agree?
3. **Who creates the 26 issues**, labels and milestones, and turns on branch protection for `main`? Protection needs a repo admin, and it is currently off.
4. **Hackathon clock:** `.claude/event.json` has `start_utc: null`, so the `/status` skill can't measure gates. Who sets it?

## Heads-up

- `main` was force-pushed once today to remove an accidental commit of raw NOAA files and `.pyc` files (commit `6cd46db`). If your local `main` still shows that commit, check `git log` for anything unpushed, then `git fetch && git reset --hard origin/main`.
- `pyproject.toml` caps `numpy` below 2.5, because pandas 2.3 emits a deprecation warning our tests treat as an error. Lift it with pandas 3.
- Sample fixtures in `data/sample/` follow NOAA's real format (unpadded county codes and times). `data/sample/README.md` says why each row exists.
- `make eda` writes its executed copy to the ignored `outputs/executed/`; the tracked notebook stays output-free.
- Please don't commit anything under `data/raw/`. That's what caused the force-push.
