# ADR 0002 — Calibrated monotonic gradient-boosted model

- **Status:** Proposed — to be confirmed in Milestone 4
- **Date:** 2026-09-26

## Context

The model's output is not displayed directly: it is converted to a hazard and
summed over a route. That makes two properties non-negotiable.

1. **Calibration.** A probability that is not a probability makes the route
   arithmetic meaningless.
2. **Physical monotonicity.** If more rain ever lowers modeled hazard, a judge
   will find it and the project loses credibility — and a traveler could be told
   a wetter window is better.

## Decision

- Gradient-boosted trees (XGBoost) with **monotone increasing constraints** on
  every rainfall and soil-moisture feature (`configs/model.yaml`).
- **Sigmoid (Platt) calibration** fit on 2023 only.
- Must beat both a smoothed **county-month climatology** and a **logistic
  regression** on PR-AUC and Brier score, with bootstrap intervals grouped by
  storm episode, to be adopted.

## Alternatives considered

- **Logistic regression alone.** Monotone and calibrated by construction but
  cannot capture thresholds and interactions such as saturated soil plus
  intense rain. Kept as a baseline.
- **Unconstrained boosting.** Likely marginally higher PR-AUC, but can learn
  non-physical reversals from sparse data. Rejected.
- **Isotonic calibration.** Needs more positives than one calibration year is
  likely to provide; overfits. Revisit only if the EDA shows ample 2023
  positives.
- **Deep or sequence models.** Unjustified for the data volume and would weaken
  explainability. Rejected.

If the boosted model fails that bar, the project ships calibrated logistic
regression, or climatology, instead (project specification §7.8;
`selection_rule` in `configs/model.yaml`). A more complex model is never
presented as better without the evidence.

## Consequences

- Hyperparameters are chosen on 2022 only. 2024 is read once, at the end.
- Monotonicity is spot-checked in `tests/modeling/test_calibration.py`.
- The manifest records constraints, versions, splits, and checksum so a result
  can always be traced to the artifact that produced it.
