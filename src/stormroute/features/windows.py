"""Generate the county x six-hour window grid and its labels.

Builds the complete cross product of North Carolina counties and six-hour
windows anchored at 00:00 UTC for 2015-2024, then labels each window using the
locked onset rule:

    window_start <= event_begin < window_end

Windows are half-open, so every event labels exactly one window. Edge cases that
must be covered by tests: events beginning exactly on a window boundary
(including zero-duration events), events beginning just before midnight or the
year boundary, and multi-window events, which label only their first window.

Also assigns the immutable `split` column by calendar year, so no later shuffle
can leak the 2024 test period into fitting.
"""

# TODO(milestone-3): implement. See docs/build_guide.md.
