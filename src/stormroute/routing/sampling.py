"""Sample a route into points with expected arrival times.

Samples each route every 5-10 km and at county boundaries, then computes
cumulative travel minutes so every sample carries the time the traveler is
expected to be there. Arrival time is what maps a sample onto a six-hour
prediction window, so an error here silently misprices the whole trip.
"""

# TODO(milestone-5): implement. See docs/build_guide.md.
