# ADR 0001 — County × six-hour prediction target

- **Status:** Accepted: onset rule locked by the build guide; the EDA reports its effect
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
Debris Flow** event **begins** in the window:

```text
positive  ⇔  ∃ event: window_start <= event_begin < window_end
```

This is the build guide's locked definition (§2.1). The project specification
used an overlap rule instead; [ADR 0000](0000-specification-precedence.md)
records the precedence.

## Alternatives considered

- **Point or road-segment level.** Reports are not located precisely enough, and
  claiming road-level prediction would be dishonest. Rejected.
- **County × day.** Too coarse: cannot separate the departure times the
  recommendation engine is meant to compare. Rejected.
- **County × hour.** Label noise dominates — reported begin times are
  approximate — and positives become vanishingly rare. Rejected.
- **Overlap** (`event_begin < window_end AND event_end > window_start`), the
  project specification's rule. It labels every window a long event touches,
  which better reflects an ongoing flood. Rejected as the locked rule because:
  - a zero-duration event exactly on a window boundary labels **no** window.
    231 of the 2,220 qualifying NC events in 2015–2024 have zero duration;
  - reported end times are less reliable than begin times;
  - long events would dominate the positive class.

  The EDA's label experiment (notebook section 9) computes both rules and
  reports the difference, so the cost of the choice is measured, not assumed.

## Consequences

- Roughly 100 counties × 4 windows/day × ~3,650 days ≈ 1.46 million rows. The
  positive rate will be small; metrics and evaluation are chosen for severe
  imbalance.
- A negative label means **no qualifying event began** in the window, not safe
  conditions. A flood that began in an earlier window and is still ongoing does
  **not** make the later window positive. This is the main cost of the onset
  rule, and it must be stated in the model card.
- Event end time is never needed for labeling. Events with a missing end time
  remain usable.
- Zone-coded events need a zone-to-county crosswalk. Unresolvable events are
  excluded and counted.
- The EDA gate must confirm that each temporal split contains positives.
