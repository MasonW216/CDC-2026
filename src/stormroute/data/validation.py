"""Assert the data contracts every table must satisfy.

Shared checks invoked by the pipeline and by tests: schema and dtype
conformance, unique event identifiers, timezone-aware timestamps, county FIPS
shape, value ranges, and missingness thresholds from `configs/data.yaml`.

Failures raise. A pipeline that silently emits a table violating its contract
is worse than one that stops.
"""

# TODO(milestone-1): implement. See docs/build_guide.md.
