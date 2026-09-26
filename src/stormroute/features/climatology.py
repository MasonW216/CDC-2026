"""Compute smoothed county-month climatology.

Serves two distinct purposes that must not be confused:

  1. the climatology *baseline* the final model has to beat; and
  2. the optional `historical_event_rate` feature.

Both are fit on training years only. The historical-rate feature is evaluated
with and without, because it can encode county reporting bias rather than
physical hazard.
"""

# TODO(milestone-3): implement. See docs/build_guide.md.
