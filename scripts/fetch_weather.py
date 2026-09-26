"""Retrieve hourly ERA5-Land weather for North Carolina counties.

Makefile target : make data (prerequisite)
Milestone       : 3
Reads           : configs/data.yaml, data/data_manifest.yaml
Writes          : data/raw/weather/

Long running and rate limited, so it must be resumable: completed county-years
are skipped on re-run. Coverage gaps are recorded by county and year rather
than filled in silently.
"""

# TODO(milestone-3): implement. See docs/build_guide.md.
