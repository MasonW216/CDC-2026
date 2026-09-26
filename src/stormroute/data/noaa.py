"""Parse NOAA Storm Events records into the canonical events table.

Reads the raw annual detail files from `data/raw/noaa_storm_events/` and
produces `events.parquet` as specified in `docs/data_card.md`.

Contract:
  * county FIPS are strings assembled as STATE_FIPS + CZ_FIPS; leading zeroes
    are preserved (`021` is Buncombe, not 21);
  * timestamps are constructed timezone-aware and stored in UTC;
  * original EVENT_ID values survive unchanged;
  * hazard filtering is exactly Flood, Flash Flood, and Debris Flow;
  * damage strings such as `2.5M` and `75K` are parsed with unit tests, even
    though damage is never a model feature;
  * records that cannot be assigned to a county are excluded AND counted.

State and hazard filtering happen here as an explicit transformation step, not
during download, so the raw layer stays a faithful copy of the source.
"""

# TODO(milestone-1): implement. See docs/build_guide.md.
