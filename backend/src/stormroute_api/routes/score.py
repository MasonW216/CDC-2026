"""Trip scoring endpoint.

    POST /api/v1/trips/score

Validates the trip request, delegates to the routing, weather, and scoring
services, and returns the full explanation payload. Invalid coordinates or
timestamps return 422 with a message that says what to fix.

Accepts mode=cached_replay so the demo path never touches the network.
"""

# TODO(milestone-6): implement. See docs/build_guide.md.
