"""County-window grid construction and labeling.

Must cover:
  * the grid has 100 counties x 4 windows per day for every day in range;
  * windows are anchored at 00:00 UTC;
  * the overlap rule is exactly `begin < window_end AND end > window_start`;
  * an event exactly on a boundary (600004, 06:00-12:00) lands in the windows
    the rule specifies and no others;
  * an event spanning a year boundary (600003) labels windows in both years;
  * a multi-day event (600011) labels every window it overlaps;
  * split labels are assigned by calendar year and never overlap.
"""

# TODO(milestone-3): implement. See docs/build_guide.md.
