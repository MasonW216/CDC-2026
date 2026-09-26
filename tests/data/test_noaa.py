"""NOAA parsing and hazard filtering.

Must cover, using data/sample/storm_events_sample.csv:
  * county FIPS keep leading zeroes and stay strings (event 600001, 600002);
  * damage strings parse: `25.00K`, `75K`, `2.5M`, `150.00M`, empty (600010);
  * timestamps are timezone-aware UTC, including events crossing midnight
    (600002) and a year boundary (600003);
  * a missing end time (600013) is handled explicitly, not coerced;
  * duplicate EVENT_IDs are detected and de-duplicated (600012 appears twice);
  * hazard filtering keeps exactly Flood, Flash Flood, and Debris Flow --
    Thunderstorm Wind (600006) and Heavy Rain (600007) are dropped;
  * the state filter drops South Carolina (600008);
  * zone-coded events (600005) are either resolved or counted as excluded,
    never silently assigned to a county.
"""

# TODO(milestone-1): implement. See docs/build_guide.md.
