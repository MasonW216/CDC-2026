"""Shared FastAPI dependencies.

Provides request-scoped access to the loaded model, the cache, and the service
objects. The model artifact is loaded once at startup, not per request: a
several-hundred-millisecond load inside the request path would be visible on
stage.
"""

# TODO(milestone-6): implement. See docs/build_guide.md.
