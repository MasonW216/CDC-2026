# Responsible AI

> **Owner:** Cameron (Econ/Stats) · **Reviewer:** Mason · **Milestone:** 8
>
> The six safety statements and the language rules below are **decided now**
> and apply from the first line of product code. The evaluation sections are
> completed in Milestone 8.

## Intended use

StormRoute helps a traveler in North Carolina **compare** routes and departure
times to **reduce exposure** to modeled flood hazard, based on available
weather data. It is a decision-support prototype.

## Not intended for

- deciding whether a specific road is passable
- predicting crashes, injuries, or deaths
- emergency response, dispatch, or evacuation routing
- autonomous navigation
- any use outside North Carolina
- any judgment about an individual based on who they are

## Required safety statements

These appear in the app, the README, the model card, and the presentation.

1. **No reported event does not prove safe road conditions.** The model learns
   from reports. Absence of a report is absence of a report.
2. **County resolution cannot identify whether a particular road is flooded.**
3. **The model is not a crash predictor.** The score is a comparative
   weather-hazard exposure index.
4. **Reanalysis evaluation is retrospective and differs from live forecast
   inputs.** Future reanalysis metrics describe performance on retrospective
   inputs; they do not establish live forecast accuracy. See
   [ADR 0003](adr/0003-reanalysis-live-forecast-boundary.md).
5. **Recommendations never override road closures, evacuation orders, or NWS
   guidance.** Official guidance is shown above any model recommendation.
6. **Demographic or vulnerability data do not change an individual trip score.**

## Language

| Use | Never use |
|---|---|
| Weather Safety Score | guaranteed safe |
| comparative decision index | zero risk |
| lower modeled weather risk | the safest route |
| reduce exposure | the model knows the road will flood |
| based on available weather data | probability of surviving the trip |

## Social Vulnerability Index

SVI may appear only in aggregate evaluation and impact analysis. It never
enters the feature matrix, never lowers the score of a trip through a
vulnerable community, and is never used to route travelers away from one.
Required enforcement belongs in `tests/data/test_no_leakage.py`, currently a
placeholder. The restriction is established; production enforcement remains
unverified.

## Current evidence limits

The [data card](data_card.md) records what has actually been verified. Real Census
boundaries are available, but completed analysis checks use synthetic event
fixtures. Their rates, impacts, and maps must not be presented as historical
findings. Feature-timing requirements are documented; production leakage tests,
real-data performance, and usability sessions remain pending. Planned mitigations
below are requirements, not claims that the application already implements them.

## Known sources of bias

| Source | Effect | Mitigation |
|---|---|---|
| Uneven reporting across counties | Low-reporting (often rural) counties may look lower-hazard than they are | Slice evaluation; confidence panel flags sparse-reporting counties |
| Reporting changes over time | Trends may reflect reporting, not weather | Temporal-coverage analysis in the EDA |
| One dominant storm in the test year | Helene can dominate 2024 metrics | Report all-2024 and Helene separately, plus a non-hurricane period |
| `historical_event_rate` feature | Can encode reporting bias as hazard | Evaluated with and without |

## Evaluation slices — _TBD (Milestone 8)_

| Slice | PR-AUC | Brier | Recall @ 1% | n positives |
|---|---|---|---|---|
| Statewide | | | | |
| Rural counties | | | | |
| More populous counties | | | | |
| Mountain | | | | |
| Piedmont | | | | |
| Coastal | | | | |
| Sparse historical reporting | | | | |
| Helene period | | | | |
| Non-hurricane flood period | | | | |
| High rain, no reported event | | | | |

Weak slices are reported as prominently as strong ones.

## Usability sessions — _TBD (Milestone 8)_

At least three people who did not build the app each attempt to:

1. identify the trip score;
2. identify the riskiest segment;
3. explain the recommended action;
4. state the score improvement and time cost; and
5. find the official warning and the limitation information.

| Participant | Task failures | Misunderstandings | Interface change made |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |

## Claim audit — _TBD (Milestone 8)_

Every public claim (README, DevPost, slides, site) is listed with its source
metric file or citation. A claim without one is removed.

| Claim | Where it appears | Evidence |
|---|---|---|
| | | |
