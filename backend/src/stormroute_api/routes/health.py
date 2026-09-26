"""Liveness and readiness endpoint.

    GET /health

Reports service status plus whether the model artifact and the cached demo
assets are actually present. A health check that returns 200 while the demo
assets are missing would hide the exact failure this endpoint exists to catch.
"""

# TODO(milestone-6): implement. See docs/build_guide.md.
