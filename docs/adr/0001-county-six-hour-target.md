# ADR 0001 — County × six-hour prediction target

- **Status:** Proposed — to be confirmed or amended by the Milestone 2 EDA gate
- **Date:** 2026-09-26

## Context

A traveler's decision is about *where* and *when*. The label has to be fine
enough to distinguish a morning departure from an afternoon one, and coarse
enough that NOAA reports can actually support it.

NOAA Storm Events are reported by county (or forecast zone) with begin and end
times. They are event records, not a classification dataset: a table of events
has no negatives, so it cannot train a classifier on its own.

## Decision

Predict, for every North Carolina county and every six-hour window anchored at
00:00 UTC from 2015 through 2024, whether at least one **Flood, Flash Flood, or
Debris Flow** event overlaps the window:

```text
positive  ⇔  ∃ event: event_begin < window_end AND event_end > window_start
```

## Alternatives considered

- **Point or road-segment level.** Reports are not located precisely enough, and
  claiming road-level prediction would be dishonest. Rejected.
- **County × day.** Too coarse: cannot separate the departure times the
  recommendation engine is meant to compare. Rejected.
- **County × hour.** Label noise dominates — reported begin times are
  approximate — and positives become vanishingly rare. Rejected.
- **Event onset only** (rather than overlap). Under-labels long events that are
  most dangerous mid-duration. Open question for the EDA; the overlap rule is
  the default.

## Consequences

- Roughly 100 counties × 4 windows/day × ~3,650 days ≈ 1.46 million rows. The
  positive rate will be small; metrics and evaluation are chosen for severe
  imbalance.
- A negative label means **no qualifying reported event**, not safe conditions.
- Zone-coded events need a zone-to-county crosswalk. Unresolvable events are
  excluded and counted.
- The EDA gate must confirm that each temporal split contains positives.
