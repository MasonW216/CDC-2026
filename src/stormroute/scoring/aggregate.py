"""Aggregate segment hazards into one trip score.

The locked aggregation, weighted by time exposed:

    h_i          = -ln(1 - clamp(p_i, 0, 0.999))
    H_route      = sum((segment_hours_i / 6) * h_i)
    R_data       = 1 - exp(-H_route)
    R_trip       = max(R_data, highest_official_alert_floor)
    safety_score = round(100 * (1 - R_trip))

Invariants that `tests/scoring/test_aggregation.py` must enforce:
  * zero risk everywhere produces exactly 100;
  * the score is always within [0, 100];
  * raising any segment probability can never raise the score;
  * spending longer in a risky interval can never raise the score;
  * splitting one interval into smaller identical pieces changes nothing;
  * identical versioned inputs produce an identical score.

The result is a comparative weather-hazard exposure index. It is not a crash
probability and not a guarantee of safety.
"""

# TODO(milestone-5): implement. See docs/build_guide.md.
