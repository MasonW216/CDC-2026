# Model Card — StormRoute Flood-Hazard Classifier

> **Owner:** Mason · **Independent evaluation:** Econ/Stats major · **Milestone:** 4
>
> Structure and fixed facts only. Every metric is _TBD_ until the single final
> evaluation on 2024. No number enters this card without a matching entry in
> `outputs/metrics/`.

## Model details

| | |
|---|---|
| Task | Probability that a Flood, Flash Flood, or Debris Flow event is reported in a NC county during a six-hour window |
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

Intervals are 95% bootstrap intervals resampled by storm episode.

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
- **Train-serve skew.** Trained on reanalysis; live use would see forecasts.
  Metrics are an upper bound on live performance.
- **Resolution.** County × six hours; says nothing about a specific road.
- **Test-year concentration.** Helene may dominate 2024.
- **Rare positives.** Wide intervals are expected and will be reported, not hidden.

## Human responsibility

The traveler decides. Official NWS guidance, road closures, and evacuation
orders always take precedence over this model.
