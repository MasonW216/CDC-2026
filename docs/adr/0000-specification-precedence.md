# ADR 0000 — Specification precedence

- **Status:** Accepted
- **Date:** 2026-09-26
- **Deciders:** StormRoute team (to be ratified by all three members in the scaffold PR)

## Context

Two documents define this project:

- [`project_specification.md`](../project_specification.md) — the original
  product and technical specification (previously the root README).
- [`build_guide.md`](../build_guide.md) — the repository and delivery guide,
  written later, which locks definitions and milestone order.

They disagree in several places. Leaving the conflicts unresolved would let each
teammate implement a different project, and the difference would surface as a
bug late — most likely in the label, which invalidates everything downstream.

## Decision

**Where the two documents conflict, the build guide wins.** The specification
remains the reference for anything the build guide does not address (user
stories, band descriptions, recommendation-ranking detail, safety language).

Resolved conflicts:

| Item | Specification | Build guide — **adopted** | Why the build guide is right |
|---|---|---|---|
| Third hazard type | Heavy Rain | **Debris Flow** | Heavy Rain is a precipitation report, not a hazard outcome; including it would label rain as flooding and inflate the positive class with events that did not threaten roads. Debris Flow is a direct road hazard in the mountain counties. |
| Positive label | Event *overlaps* the window: `begin < window_end AND end > window_start` | **Event *begins* in the window: `window_start <= begin < window_end`** | Each event labels exactly one window. Under overlap, a zero-duration event exactly on a boundary labels no window at all, and 231 of the 2,220 qualifying 2015–2024 events have zero duration. Recorded in [ADR 0001](0001-county-six-hour-target.md). |
| Showcase route | Asheville → Knoxville, TN | **Asheville → Charlotte** | A North-Carolina-only model cannot honestly score a route whose second half is in Tennessee. |
| Trip aggregation | `0.70 × max + 0.30 × time-weighted mean` of segment risk | **Cumulative hazard weighted by exposure time** | The weighted-max form changes when an interval is split into smaller pieces, so the score depends on sampling density rather than on the trip. Cumulative hazard is additive in exposure time, which makes it invariant to splitting and monotone in both probability and duration. |
| Where the alert floor applies | Per segment, before aggregation | **Once, to the trip, after aggregation** | Follows from the aggregation change; applying floors per segment inside a cumulative-hazard sum would double-count exposure. |
| Final model and calibration | Gradient-boosted trees, unconstrained; isotonic *or* Platt calibration | **Monotonic gradient-boosted classifier (XGBoost); sigmoid (Platt) calibration** | Monotonic constraints are what make the model defensible: more rain can never mean less hazard. Isotonic calibration overfits on one year of rare positives. |
| Temporal splits | train 2015–2022; selection *and* calibration 2023; test 2024 | **train 2015–2021, selection 2022, calibration 2023, test 2024** | Using 2023 for both hyperparameter selection and calibration fits two things to one year; separate years keep the calibration estimate honest. |
| API paths | `/api/trips/score`, `/api/demo/helene`, `/api/method`, `/api/health` | **`/api/v1/trips/score`, `/api/v1/scenarios[/{id}]`, `/api/v1/methodology`, `/health`** | Versioned from day one; scenarios generalize beyond one storm. |
| Repository layout | `ml/`, `api/`, `web/` | **`src/stormroute/`, `backend/`, `frontend/`** | Installable, testable package separated from the transport layer. |

Retained from the specification, because the build guide does not contradict
them:

- §7.6 fixed alert budget of the **top 1%** of county-windows, plus secondary
  metrics (event-level recall, expected calibration error) —
  [`configs/model.yaml`](../../configs/model.yaml);
- §7.8 model-selection rule, including the **fallback to calibrated logistic
  regression or climatology** if the boosted model fails it;
- §8.1 alert floors (0.00 / 0.35 / 0.50 / 0.80 / 0.98), §8.4 score bands, and
  §9.4 recommendation rules — [`configs/scoring.yaml`](../../configs/scoring.yaml);
- §12.2 required and prohibited safety language;
- §12.4 Social Vulnerability Index restrictions.

## Consequences

- `configs/`, the tests, and every doc follow the adopted column.
- `data/sample/storm_events_sample.csv` includes a Heavy Rain record (event
  600007) specifically so a test fails if Heavy Rain ever re-enters the filter.
- The specification is not edited to match: it is a historical record. This
  ADR is the bridge.
- Any future conflict is resolved by a new ADR, not by quietly editing either
  document.
