"""Download Census TIGER/Line county boundaries.

Makefile target : make download
Milestone       : 1
Reads           : data/data_manifest.yaml
Writes          : data/raw/census_tiger/

Restricting to STATEFP 37 happens downstream in stormroute.data.geography.
Exactly 100 North Carolina counties are expected; any other count is an error.
"""

# TODO(milestone-1): implement. See docs/build_guide.md.
