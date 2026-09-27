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

## Claim audit - initial documentation review

**Owner:** Cameron (Econ/Stats). **Required reviewer:** Mason, pending.
**Review date:** 2026-09-26. Scope: current README, model card, risk methodology,
demo runbook, data card, and the reanalysis ADR they reference. This is an initial
documentation review, not Milestone 8 completion or approval of a release.

| Claim reviewed | Location | Evidence / finding | Disposition |
|---|---|---|---|
| Product already compares trips and reduces exposure | [README](../README.md) | No validated application or impact evidence; [model manifest](../artifacts/models/model_manifest.json) remains a skeleton | Changed to intended behavior and planned capabilities; reduced harm not demonstrated |
| Repository contains no data pipeline code | [README](../README.md) | [NOAA ingestion](../src/stormroute/data/noaa.py) and [boundary loader](../src/stormroute/data/geography.py) now exist | Updated status to ingestion/sample EDA development; gate pending |
| Most flood-related exposure comes from pre-trip decisions | [README](../README.md) | No supporting evidence in repository references | Removed the empirical assertion; retained the project's pre-trip decision focus |
| A four-hour delay improves score from 54 to 81 | [README](../README.md) | Explicit illustrative example; no matching evaluated trip artifact | Retained only as a labeled illustration, never a measured benefit |
| A calibrated boosted model is already available | [Model card](model_card.md) | Manifest has no trained artifact checksum or results | Clarified planned design and pending metrics; adoption rule unchanged |
| Reanalysis metrics bound live performance | [Model card](model_card.md), [ADR 0003](adr/0003-reanalysis-live-forecast-boundary.md) | No archived-forecast evaluation or bound established | Removed the bound; documented that retrospective evaluation does not establish live accuracy |
| Scoring invariants are already tested | [Risk methodology](risk_methodology.md) | [Aggregation tests](../tests/scoring/test_aggregation.py) are placeholders | Changed to required implementation tests; no passing-test claim |
| Window probability describes any ongoing event | [Risk methodology](risk_methodology.md) | [Locked data config](../configs/data.yaml) uses onset | Clarified event beginning within the window; formulas unchanged |
| Offline replay and fallback are demonstrated | [Demo runbook](demo_runbook.md), README | Runbook and artifact templates do not establish a successful rehearsal | Explicit planned/unverified status; CS rehearsal evidence required |
| Maps and sample summaries establish real impacts | [Data card](data_card.md) | Real Census geometry; [event fixtures](../data/sample/README.md) are synthetic | Kept explicit separation; no historical or traveler-specific impact claim |
| Feature restrictions are enforced by production tests | [Data card](data_card.md), this document | [Leakage tests](../tests/data/test_no_leakage.py) remain a placeholder | Already corrected: requirements documented, enforcement pending |
| Alert floors are measured probabilities | [Risk methodology](risk_methodology.md) | [Scoring config](../configs/scoring.yaml) defines team policy values | Existing policy disclaimer retained; sensitivity analysis pending |

### Publication checks still required

- Repeat this audit after full-data findings and model results exist. Every
  performance claim needs a matching reproducible metric file and denominator.
- Mason reviews the scientific wording and the removal of the unsupported
  live-performance bound; no reviewer sign-off is implied here.
- Audit the actual rendered site, final slides, and DevPost submission when they
  exist. This review does not certify their content, usability, or runtime safety.
- Keep the illustrative score example labeled. Replace it with a measured result
  only when the versioned demo artifacts and verification evidence support it.
- Verify official-alert precedence, offline behavior, and recovery steps through
  implementation tests and rehearsal; written requirements alone are not evidence.
