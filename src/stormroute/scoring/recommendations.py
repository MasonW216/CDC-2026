"""Rank route and departure-time counterfactuals.

Scores candidate routes and departures at +2 through +12 hours, keeps the
non-dominated frontier over (higher score, lower time cost), and returns at
most three recommendations: largest improvement, best low-cost improvement,
and any official-warning action.

Rules:
  * recommend a change only when it gains at least 5 points;
  * always report both the score delta and the added travel or delay time;
  * never offer the current trip as its own alternative;
  * when nothing acceptable exists, say so plainly and point to official
    guidance rather than manufacturing an option;
  * never override a road closure, evacuation order, or NWS warning.

Every candidate considered must remain auditable, so a reviewer can reconstruct
why one recommendation won.
"""

# TODO(milestone-5): implement. See docs/build_guide.md.
