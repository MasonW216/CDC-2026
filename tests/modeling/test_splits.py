"""Temporal splits are immutable and disjoint.

Asserts train 2015-2021, selection 2022, calibration 2023, test 2024; that the
four sets share no row; that each contains positive examples; and that no code
path can reassign a split after the table is built.
"""

# TODO(milestone-4): implement. See docs/build_guide.md.
