"""Compute rolling precipitation and antecedent-moisture features.

Produces the 1, 3, 6, 24, and 72-hour precipitation accumulations and related
intensity features for each county-window.

The one invariant that matters: a feature for a window starting at time T may
read only observations at or before T. Never a future hour, never a centered
window, never a whole-period aggregate. This is the most likely place for
leakage to enter the project unnoticed.
"""

# TODO(milestone-3): implement. See docs/build_guide.md.
