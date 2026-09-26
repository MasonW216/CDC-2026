# ADR 0004 — Extend the hazard scope beyond flooding (phased)

- **Status:** Proposed
- **Date:** 2026-09-26
- **Proposed by:** Jeffrey
- **Requires:** all three members' approval; does not change anything before the flood model passes Milestone 4

## Context

The product is called a **Weather** Safety Score, but the locked label
(`configs/data.yaml`) covers only Flood, Flash Flood, and Debris Flow. A judge
or user who asks "what about ice on I-40?" gets no answer.

Evidence from NOAA Storm Events, 2015-2024 (computed 2026-09-26 from the
NCEI details and fatalities files, onset rule, times converted from the
`CZ_TIMEZONE` fixed offsets):

| Family (NOAA event types) | NC events | Geography | NC onset windows | Rate | Episodes | Train 15-21 / Sel 22 / Cal 23 / Test 24 |
|---|---:|---|---:|---:|---:|---|
| Flooding (Flood, Flash Flood, Debris Flow) | 2,220 | all county-coded | 1,499 | 0.10% | 502 | 1,096 / 53 / 78 / 272 |
| Winter (Winter Storm, Winter Weather, Heavy Snow, Ice Storm, Sleet, Blizzard, Freezing Fog) | 2,103 | **all zone-coded** | 2,071 (zone-windows, before crosswalk) | ~0.14% | 259 | 1,716 / 244 / **25** / 86 |
| Wind and severe (Thunderstorm Wind, Tornado, High Wind, Strong Wind, Hail) | 8,774 | 8,196 county, 578 zone | 5,339 | 0.37% | 1,623 | 3,595 / 619 / 592 / 531 |

National in-vehicle deaths per 1,000 events (fatalities file, 2015-2024):
tropical 17.9, dense fog 13.2, **flooding 6.4, winter 5.6**, wind/severe 0.7.
Nationally, winter caused 531 in-vehicle deaths vs. 558 for flooding.

## Decision (proposed)

Extend in **phases**, so the flood pipeline and its gates are never put at risk:

1. **Phase 1 (unchanged):** flooding exactly as locked in `configs/data.yaml`,
   ADR 0001, and ADR 0002. Nothing in this ADR starts until the flood model
   passes the Milestone 4 selection rule.
2. **Phase 2:** add **winter** and **wind/severe** as separate binary labels,
   same onset rule, same county x 6-hour unit, same splits, each with its own
   climatology baseline and selection rule. A family that fails its rule ships
   as climatology, or is dropped from the score and shown as alerts only.
3. **All phases:** tropical systems and dense fog are **alert-only** (too few NC
   events to model: 41 tropical episodes; 1 dense-fog event in ten years).
   The existing alert floors already cover any NWS product on the route.

**Combining families in the score** stays inside the accepted cumulative-hazard
method (`docs/risk_methodology.md`): convert each family's probability to a
hazard and weight it by severity before summing.

```text
h_i = sum over families f of  w_f * -ln(1 - clamp(p_f,i))
```

Initial severity weights, proportional to national in-vehicle deaths per 1,000
events, normalized to flooding = 1.00: **flooding 1.00, winter 0.88,
wind/severe 0.11**. These are product policy, stored in `configs/scoring.yaml`,
with a sensitivity analysis, like the alert floors. Splitting invariance and
monotonicity still hold because the sum is linear in each hazard.

## Consequences

- Winter needs the zone-to-county crosswalk (`zone_to_county_strategy`, still
  TODO) because every NC winter event is zone-coded.
- **Winter has only 25 positive onset windows in the 2023 calibration year.**
  Platt calibration on 25 positives is fragile; winter must report its sample
  size and is the family most likely to fall back to climatology.
- Weather features grow: freezing hours, precipitation at or below 0 C, snow
  depth change, wind gusts (see ADR 0005).
- `label_flood_event` stays the flood label name; new columns
  `label_winter_event` and `label_wind_event` are added, never renamed.
- Model card, data card, and risk methodology gain a per-family section.

## Alternatives considered

- **Flood only (status quo).** Simplest and safest for the deadline; weaker
  answer to "what about snow and ice?"
- **All families at once.** Rejected: triples modeling work before the flood
  model is proven.
- **One multi-class model.** Rejected: families co-occur (a hurricane brings
  wind and flood), so they are not mutually exclusive.
