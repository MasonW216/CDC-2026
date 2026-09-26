"""Assign route samples to North Carolina counties.

Joins sampled points to county polygons from `data.geography`, collapses
consecutive samples sharing a (county, window) pair into one interval, and
flags any portion of the route falling outside the modeled geography.

Coverage is reported, never quietly ignored: a trip leaving North Carolina is
partially unmodeled and the user must be told so.
"""

# TODO(milestone-5): implement. See docs/build_guide.md.
