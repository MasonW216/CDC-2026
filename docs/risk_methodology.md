# Risk Methodology — the Weather Safety Score

> The formula, policy values, and invariants below are **decided** and match
> [`configs/scoring.yaml`](../configs/scoring.yaml). If this document and that
> file ever disagree, it is a bug. Change both in the same pull request.
>
> Implementation status: not yet built (Milestone 5).

## What the score is — and is not

The Weather Safety Score is a **comparative decision index** from 0 to 100 that
summarizes modeled flood-hazard exposure along a trip, based on available weather
data. Higher is lower modeled exposure.

It is **not** a probability of a crash, of injury, or of arriving safely. It does
not know whether a specific road is flooded. The top band is never called "safe".

## From probabilities to a score

The model provides a calibrated probability `p_i` that a qualifying flood event is
reported in a given county during a given six-hour window. A route passes through
a sequence of such (county, window) intervals.

For each **unique** interval `i` on the route:

```text
h_i          = -ln(1 - clamp(p_i, 0, 0.999))                 # per-window hazard
H_route      = Σ (segment_hours_i / 6) × h_i                 # exposure-weighted total
R_data       = 1 - exp(-H_route)                             # modeled trip risk
R_trip       = max(R_data, highest_official_alert_floor)     # official alerts as a floor
safety_score = round(100 × (1 - R_trip))
```

### Why hazard space

Probabilities do not add; hazards do. Converting each window's probability into a
hazard rate lets exposure accumulate linearly with time spent in it. Two things
follow, and both are tested:

- **Splitting invariance.** Spending three hours in one window gives the same
  score whether it is represented as one three-hour piece or six thirty-minute
  pieces. The score depends on the trip, not on how densely it was sampled.
- **Monotonicity.** More probability or more time in a risky window can only
  lower the score.

The clamp at 0.999 keeps the hazard finite.

### Why a max with the alert floor

Official National Weather Service products carry information the model does not
have. They are applied as a **floor** on trip risk, so they can only raise it:

| Most severe official product on the route | Risk floor |
|---|---:|
| None | 0.00 |
| Watch | 0.35 |
| Advisory | 0.50 |
| Warning | 0.80 |
| Emergency | 0.98 |

These are **product-policy values chosen by the team, not learned
probabilities.** A sensitivity analysis will report how scores and
recommendations change as they vary. _(TBD — Milestone 5.)_

## Bands

| Score | Band | Required response |
|---:|---|---|
| 85–100 | Lower modeled weather risk | Show ordinary cautions and official-alert status |
| 70–84 | Use caution | Explain the main exposure and the best available improvement |
| 50–69 | High caution | Lead with a safer route or departure time |
| 0–49 | Delay or avoid | Do not recommend proceeding; show official guidance first |

## Recommendations

Candidates: the requested trip on 2–3 alternative routes, and departures at +2,
+4, +6, +8, +10, and +12 hours.

1. Score every candidate.
2. Keep the non-dominated set over (higher score, lower added time).
3. Show at most three: the largest improvement, the best low-cost improvement
   (≤ 30 added travel minutes or ≤ 2 hours' delay), and any official-warning
   action.
4. Recommend a change only if it improves the score by **at least 5 points**.
5. Every recommendation shows before score, after score, the delta, and the
   time cost together.
6. If nothing qualifies: *"No lower-exposure option found. Consider delaying the
   trip and follow official National Weather Service guidance and road closures."*
7. Recommendations never override a road closure, evacuation order, or warning.

The full candidate table is retained so a reviewer can reconstruct any choice.

## Invariants (tests)

| Invariant | Test |
|---|---|
| Zero risk on every interval → exactly 100 | `tests/scoring/test_aggregation.py` |
| Score is an integer in [0, 100] | `tests/scoring/test_aggregation.py` |
| Raising any probability never raises the score | `tests/scoring/test_aggregation.py` |
| More time in a risky interval never raises the score | `tests/scoring/test_aggregation.py` |
| Splitting an interval changes nothing | `tests/scoring/test_aggregation.py` |
| A short high-risk segment is not hidden by a long low-risk route | `tests/scoring/test_aggregation.py` |
| Each alert applies its floor; an alert can never improve a score | `tests/scoring/test_alert_floor.py` |
| Code floors equal config floors | `tests/scoring/test_alert_floor.py` |
| The current trip is never its own alternative | `tests/scoring/test_recommendations.py` |
| Displayed delta = after − before | `tests/scoring/test_recommendations.py` |
| Sub-5-point changes are not recommended | `tests/scoring/test_recommendations.py` |

## Worked example

_TBD — Milestone 5. A fully worked Helene-replay trip, from segment probabilities
to the displayed score, reproducible by hand from `artifacts/demo/demo_scores.json`._

## Known limitations of the method

- County resolution: exposure is attributed to a county-window, not a road.
- A negative label means *no report*, not *no hazard*; low-reporting counties
  may be under-scored.
- The six-hour window is coarse relative to flash-flood onset.
- Alert floors are policy, not measurement.
