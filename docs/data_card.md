# Data Card

> **Owner:** Econ/Stats major · **Reviewer:** Mason
>
> Canonical schemas are **locked** below. Counts, coverage, and quality results
> are _TBD_ until Milestones 1–3.

## Summary

| | |
|---|---|
| Geography | North Carolina, 100 counties |
| Period | 2015–2024 |
| Unit | county × six-hour window, anchored at 00:00 UTC |
| Label | ≥ 1 Flood, Flash Flood, or Debris Flow event begins in the window (`window_start <= begin < window_end`) |
| Sources | NOAA Storm Events · ERA5-Land · Census TIGER/Line 2024 · (optional) USGS 3DEP |
| Registry | [`data/data_manifest.yaml`](../data/data_manifest.yaml) |

## Sources

See the manifest for URLs, licenses, access dates, resolved filenames, and
checksums. Summary:

| Dataset | Role | License |
|---|---|---|
| NOAA Storm Events details | Labels | Public domain |
| ERA5-Land hourly | Weather features | Copernicus Licence (attribution) |
| TIGER/Line counties 2024 | County geometry | Public domain |
| USGS 3DEP (optional) | Terrain features | Public domain |
| NWS API | Live alerts (serving only) | Public domain |
| OSRM / OpenStreetMap | Routes (serving only) | ODbL — attribution required |
| CDC/ATSDR SVI (optional) | Evaluation only, never a feature | Public domain |

## Canonical schemas

Changing a schema requires an update here, updated validation tests, notice to
all three teammates, and a pull request labeled `area:data`.

### `events.parquet`

| Column | Type | Notes |
|---|---|---|
| `event_id` | string | Original NOAA `EVENT_ID`, unchanged |
| `episode_id` | string | NOAA `EPISODE_ID`; used for grouped bootstrap, never a feature |
| `county_fips` | string(5) | `STATE_FIPS + CZ_FIPS`, leading zeroes kept |
| `begin_utc` | timestamp[UTC] | |
| `end_utc` | timestamp[UTC] | Used for labeling only, never a feature |
| `event_type` | category | Flood · Flash Flood · Debris Flow |
| `source` | string | Reporting source |
| `injuries` | int | Descriptive only |
| `deaths` | int | Descriptive only |
| `property_damage_usd` | float | Parsed from strings such as `2.5M`; descriptive only |

### `county_windows.parquet`

| Column | Type | Known before departure? |
|---|---|---|
| `county_fips` | string(5) | yes |
| `window_start_utc` | timestamp[UTC] | yes |
| `label_flood_event` | bool | — target |
| `precip_1h`, `precip_3h`, `precip_6h`, `precip_24h`, `precip_72h` | float, mm | yes — trailing windows only |
| `max_precip_intensity` | float, mm/h | yes — trailing |
| `temperature` | float, °C | yes |
| `wind_speed`, `wind_gust` | float, m/s | yes |
| `soil_moisture_shallow`, `soil_moisture_deep` | float, m³/m³ | yes |
| `elevation_mean` | float, m | yes — static |
| `slope_mean` | float, degrees | yes — static |
| `month_sin`, `month_cos` | float | yes |

Plus metadata carried alongside: `split` (train · selection · calibration · test)
and provenance (creation time, source versions, Git SHA).

### `predictions_2024.parquet`

| Column | Type |
|---|---|
| `county_fips` | string(5) |
| `window_start_utc` | timestamp[UTC] |
| `y_true` | bool |
| `climatology_probability` | float |
| `logistic_probability` | float |
| `raw_model_probability` | float |
| `calibrated_probability` | float |
| `split` | string |

### `demo_routes.geojson`

One Point feature per route sample, with properties: `route_id`,
`sample_order`, `latitude`, `longitude`, `county_fips`, `cumulative_minutes`,
`segment_minutes`, `distance_km`.

## Exclusions

Post-event fields are never features: injuries, deaths, damage, narratives,
event end time, episode ID. Enforced by `tests/data/test_no_leakage.py`.

## Quality — _TBD (Milestones 1–3)_

| Check | Result |
|---|---|
| Unique event IDs | |
| Timezone-aware UTC timestamps | |
| 100 counties with 5-character FIPS | |
| Events excluded for unresolved geography | |
| Weather coverage by county and year | |
| Positive rate by year / month / county / type | |
| Expected vs actual county-window row count | |

Machine-readable results: `outputs/metrics/data_quality.json`.

## Known limitations

- Labels are **reports**, shaped by who reports and where.
- Zone-coded NOAA events need a crosswalk; some cannot be placed.
- Reanalysis is retrospective; live use would see forecasts.
- County averages hide within-county variation, which is large in the mountains.
