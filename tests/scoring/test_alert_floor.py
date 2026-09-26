"""Official alerts may only raise risk.

Asserts each severity applies its configured floor; that the most severe
intersecting alert wins; that no alert combination can improve a score; and
that the floors used by the code equal the floors in configs/scoring.yaml --
so policy cannot drift away from documentation unnoticed.
"""

# TODO(milestone-5): implement. See docs/build_guide.md.
