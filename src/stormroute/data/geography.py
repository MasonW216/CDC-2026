"""Resolve county identities and geometry for North Carolina.

Loads Census TIGER/Line boundaries, restricts to STATEFP 37, and provides the
canonical county lookup used by both the label pipeline and the route spatial
join -- one shared definition of "which county is this", so training
geography and serving geography cannot drift apart.

Also owns the zone-to-county crosswalk for NOAA zone-coded events. Events
that cannot be resolved confidently are reported, never guessed.

Expects exactly 100 counties. A different count is an error, not a warning.
"""

# TODO(milestone-1): implement. See docs/build_guide.md.
