"""Scoring endpoint request and response contract.

Covers: a valid request returns every required response field; out-of-range
coordinates, a non-NC origin, and malformed timestamps return 422 with a useful
message; the response always carries model and data versions; a score is never
returned without its band, limitations, and confidence indicator.
"""

# TODO(milestone-6): implement. See docs/build_guide.md.
