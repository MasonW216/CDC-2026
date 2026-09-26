"""Fetch candidate route geometry and durations.

Thin OSRM client returning two or three candidate routes with geometry and
travel duration.

Network behavior is the point of failure on stage, so: explicit timeouts, typed
responses, and a cached replay path that needs no network at all. The public
OSRM demo server is rate limited and must never be a live dependency during
judging.
"""

# TODO(milestone-5): implement. See docs/build_guide.md.
