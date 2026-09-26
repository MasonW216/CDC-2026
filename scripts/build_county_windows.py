"""Build the model-ready county x six-hour window table.

Makefile target : make data
Milestone       : 3
Reads           : data/raw/, configs/data.yaml
Writes          : data/processed/county_windows.parquet,
                  outputs/metrics/data_quality.json

Composes stormroute.features.windows, .rolling_weather, .terrain, and
.climatology. Emits deterministic column order and dtypes, plus provenance
(creation timestamp, source versions, Git commit) so a table can always be
traced back to the inputs that produced it.
"""

# TODO(milestone-3): implement. See docs/build_guide.md.
