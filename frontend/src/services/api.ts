/**
 * Typed client for the StormRoute API.
 *
 * Wraps fetch against VITE_API_BASE_URL with explicit timeouts and typed errors.
 *
 * Every call must distinguish loading, empty, success, partial-data, and failure,
 * because the UI is required to render all five honestly -- 'partial data' is a
 * real state here, not an edge case: a route can leave the modeled geography.
 *
 * TODO(milestone-7): implement. See docs/build_guide.md.
 */
