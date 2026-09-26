"""Generate the county x six-hour window grid and its labels.

Builds the complete cross product of North Carolina counties and six-hour
windows anchored at 00:00 UTC for 2015-2024, then labels each window using the
locked overlap rule:

    event_begin < window_end AND event_end > window_start

Edge cases that must be covered by tests: events spanning midnight, events
spanning a year boundary, events landing exactly on a window boundary, and
events spanning several windows.

Also assigns the immutable `split` column by calendar year, so no later shuffle
can leak the 2024 test period into fitting.
"""

# TODO(milestone-3): implement. See docs/build_guide.md.
