"""Convert a county-window probability into segment hazard.

For each unique (county, window) interval on a route:

    h_i = -ln(1 - clamp(p_i, 0, 0.999))

The clamp exists because a probability of exactly 1.0 sends the hazard to
infinity. Working in hazard space rather than probability space is what makes
exposure additive over time, which the aggregation step depends on.
"""

# TODO(milestone-5): implement. See docs/build_guide.md.
