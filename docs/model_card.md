# Model Card — StormRoute Flood-Hazard Classifier

> **Owner:** Mason · **Independent evaluation:** Econ/Stats major · **Milestone:** 4
>
> Planned model design; no trained-model performance is established. Every metric is _TBD_ until the single final
> evaluation on 2024. No number enters this card without a matching entry in
> `outputs/metrics/`.

## What is actually shipped right now, versus this card

**This entire card describes a planned, not-yet-built model.** It is a design document for
Milestone 4, gated behind the EDA review (issue #6), and nothing below this section is
running in the product today.

What the live product runs tonight is a different, much simpler thing:
**`prototype-score/1`** (`src/stormroute/scoring/concern.py`, specified in full in
[`prototype_score_spec.md`](prototype_score_spec.md), and returned as plain text by
`GET /api/v1/methodology`). It is:

- **A fixed, published formula, not a trained model.** `segment_index = round(max(100 *
  min(1, max(rain_rate_mm_h / 20, rain_24h_mm / 100)), alert_floor))`. There are no
  learned weights, no training data, and no fitted parameters anywhere in it. Every number
  it can produce is reproducible by hand from the formula and the raw forecast/alert
  response -- see the worked example in `prototype_score_spec.md`.
- **Not this card's classifier, early or otherwise.** It does not use, and was not derived
  from, the NOAA Storm Events labels, the EDA in `reports/eda/`, or any file under
  `data/processed/`. Those exist for the *future* model this card describes.
- **Not validated for predictive accuracy**, because it does not predict anything: it is a
  team-authored comparison index, "higher means more indicated concern," checked only for
  internal consistency (an alert or worse rain cannot lower it; see
  `tests/scoring/test_concern.py`), not against outcomes.
- **Team-authored on top of external data.** The upstream weather forecast (Open-Meteo) and
  official alerts (NWS) are third-party sources StormRoute reads as-is; the formula that
  turns them into an index is the only part StormRoute wrote.

A judge or reviewer comparing the two: everything from "Model details" onward is the
research plan this prototype exists to eventually replace, once a real feature table,
chronological splits, and a held-out 2024 test exist (Priority 3 of the MVP scoring
assignment, `docs/prototype_score_spec.md`'s companion investigation). The prototype does
not get promoted to that role just by being live tonight.

## Model details

| | |
|---|---|
| Task | Probability that a reported Flood, Flash Flood, or Debris Flow event begins in a NC county during a six-hour window |
| Family | Gradient-boosted trees (XGBoost), monotone-increasing in rainfall and soil moisture |
| Calibration | Sigmoid (Platt), fit on 2023 only |
| Baselines | Smoothed county-month climatology · regularized logistic regression |
| Version | _TBD — from `artifacts/models/model_manifest.json`_ |
| Git SHA | _TBD_ |
| Decision records | [ADR 0001](adr/0001-county-six-hour-target.md) · [ADR 0002](adr/0002-calibrated-boosted-model.md) · [ADR 0003](adr/0003-reanalysis-live-forecast-boundary.md) |

## Intended use

- **Users:** travelers in North Carolina and the people helping them plan.
- **Decision:** which route or departure time reduces modeled flood-hazard exposure.
- **Output:** a probability per county-window, aggregated into the Weather Safety
  Score as described in [risk_methodology.md](risk_methodology.md).

## Prohibited uses

Crash, injury, or survival prediction. Road-level passability. Emergency
dispatch or evacuation routing. Use outside North Carolina. Any use that
conditions on who a traveler is.

## Data

| Split | Years | Purpose |
|---|---|---|
| Train | 2015–2021 | Fit |
| Selection | 2022 | Hyperparameters, model choice |
| Calibration | 2023 | Sigmoid calibration |
| Test | 2024 | One final evaluation, untouched until then |

Features and exclusions: see [data_card.md](data_card.md).

## Metrics — _TBD_

Planned intervals are 95% bootstrap intervals resampled by storm episode;
no intervals have been computed or validated yet.

| Model | PR-AUC | Brier | Log loss | Recall @ top 1% | Precision @ top 1% |
|---|---|---|---|---|---|
| Climatology | | | | | |
| Logistic regression | | | | | |
| Boosted, raw | | | | | |
| **Boosted, calibrated** | | | | | |

Secondary: event-level recall, expected calibration error. ROC-AUC in the
appendix only.

**Adoption rule:** the boosted model ships only if it beats climatology on PR-AUC
or recall at the budget, matches or beats it on Brier after calibration, passes
the leakage tests, and is stable under sensitivity checks. Otherwise calibrated
logistic regression or climatology ships. _Outcome: TBD._

## Slices — _TBD_

See [responsible_ai.md](responsible_ai.md#evaluation-slices--tbd-milestone-8).

## Explanations

- **Global:** permutation feature importance; a small number of partial-dependence plots.
- **Local:** calibrated probability, alert status, top contributing features,
  arrival time, confidence and missing-data status.

## Limitations and risks

- **Reporting bias.** The model learns what gets reported.
- **Train-serve skew.** Planned training uses reanalysis; live use would see forecasts.
  Retrospective metrics do not establish live performance or a numerical bound
  on it. Archived-forecast evaluation is required before live-accuracy claims.
- **Resolution.** County × six hours; says nothing about a specific road.
- **Onset label.** A window is positive only if an event *begins* in it; later
  windows of a still-ongoing flood are negative.
- **Test-year concentration.** Helene may dominate 2024.
- **Rare positives.** Wide intervals are expected and will be reported, not hidden.

## Human responsibility

The traveler decides. Official NWS guidance, road closures, and evacuation
orders always take precedence over this model.
