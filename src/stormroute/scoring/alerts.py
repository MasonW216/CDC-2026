"""Apply official NWS alert floors.

Raises modeled trip risk to the policy floor for the most severe official
product intersecting the route:

    none 0.00 | watch 0.35 | advisory 0.50 | warning 0.80 | emergency 0.98

These are product-policy values chosen by the team, not learned probabilities,
and must be reported as such with a sensitivity analysis.

One absolute rule: an official alert may only raise risk. There is no code path
in which the presence of an NWS alert improves a score.
"""

# TODO(milestone-5): implement. See docs/build_guide.md.
