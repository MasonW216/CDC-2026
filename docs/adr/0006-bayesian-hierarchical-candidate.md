# ADR 0006 — Add a hierarchical Bayesian logistic model as a candidate

- **Status:** Proposed
- **Date:** 2026-09-26
- **Proposed by:** Jeffrey
- **Relation to ADR 0002:** adds a candidate; does not replace the selection rule

## Context

ADR 0002 proposes a monotonic XGBoost classifier and rejects deep models. Two
needs are not fully met by it:

1. **Sparse counties.** Many counties have few or no flood onsets in the
   training years. Trees and plain logistic regression either ignore county
   identity or overfit it; climatology smoothing is ad hoc.
2. **Uncertainty for the `confidence` field.** The API returns a confidence
   value, but a point probability alone does not say how sure the model is.

## Decision (proposed)

Evaluate a **hierarchical Bayesian logistic regression** alongside the existing
candidates, under the **same** Milestone 4 selection rule
(`configs/model.yaml`, spec section 7.8):

- **County random intercepts** with partial pooling: data-poor counties borrow
  strength from the state, instead of a hand-tuned climatology smoother.
- **Sign-constrained priors** (for example half-normal) on every rainfall and
  soil-moisture coefficient, so **more rain can never lower hazard**. This meets
  ADR 0002's monotonicity requirement by construction.
- **Posterior predictive intervals** feed the `confidence` field (for example,
  interval width mapped to High / Moderate / Low).
- **Scale:** keep every positive row and a random fraction of negatives, and
  add `log(sampling fraction)` as an offset so probabilities stay unbiased. Fit
  with PyMC (NUTS if it finishes within the Milestone 4 time box, otherwise
  ADVI). Sigmoid calibration on 2023, as for every candidate.
- **Tie-break:** if the Bayesian model and XGBoost are within their bootstrap
  intervals on PR-AUC and Brier, prefer the one with better calibration, then
  the simpler one.

## Consequences

- One more candidate to fit and evaluate in Milestone 4; if it cannot be fitted
  in the time box, it is dropped and ADR 0002 stands unchanged.
- Adds `pymc` (and optionally `bambi`) to the modeling dependencies.
- The model card reports which candidate won and why, with the intervals.

## Alternatives considered

- **Deep or sequence models:** rejected for the same reasons as ADR 0002
  (0.1-0.4% positive rate, weak explainability).
- **Replacing XGBoost outright:** not proposed. The selection rule, not
  preference, decides.
