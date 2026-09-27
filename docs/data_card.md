# Data Card

> **Owner:** Cameron (Econ/Stats) · **Reviewer:** Mason
>
> **Evidence status:** Census boundaries verified; event analyses tested on
> synthetic fixtures. Full-data findings and EDA approval remain pending.
> Schema notes clarify current semantics; no columns or types are changed.

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
| `end_utc` | timestamp[UTC] | May be missing; duration and overlap comparison only. Not used by the locked onset label; never a feature |
| `event_type` | category | Flood · Flash Flood · Debris Flow |
| `source` | string | Reporting source |
| `injuries` | int | Nullable combined direct/indirect count; descriptive only |
| `deaths` | int | Nullable combined direct/indirect count; descriptive only |
| `property_damage_usd` | float | Nominal reported USD; missing is not zero; descriptive only |

### `county_windows.parquet`

| Column | Type | Known before departure? |
|---|---|---|
| `county_fips` | string(5) | yes |
| `window_start_utc` | timestamp[UTC] | yes |
| `label_flood_event` | bool | — target |
| `precip_1h`, `precip_3h`, `precip_6h`, `precip_24h`, `precip_72h` | float, mm | Conditional: trailing valid times and source publication/issue-time checks |
| `max_precip_intensity` | float, mm/h | Conditional: trailing valid times and source publication/issue-time checks |
| `temperature` | float, °C | Conditional: check source publication/issue time |
| `wind_speed`, `wind_gust` | float, m/s | Conditional: check source publication/issue time |
| `soil_moisture_shallow`, `soil_moisture_deep` | float, m³/m³ | Conditional: check source publication/issue time |
| `elevation_mean` | float, m | Conditional: verify source vintage |
| `slope_mean` | float, degrees | Conditional: verify source vintage |
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
event end time, episode ID. These are requirements, not verified production
enforcement: [the leakage test file](../tests/data/test_no_leakage.py) is still a
placeholder. The EDA feature-timing audit documents required evidence; it does
not prove the eventual feature pipeline is leakage-free.

## Quality and evidence status

Reviewed against this checkout on 2026-09-26. Sample checks establish execution
and arithmetic behavior only, not historical coverage or predictive performance.

| Check | Verified scope | Still pending |
|---|---|---|
| County inventory | Real 2024 Census archive; 100 unique NC county FIPS and valid geometry | Production spatial-join review |
| Event IDs, hazard filtering, UTC parsing | Ingestion tests and synthetic notebook execution | Full NOAA run and manual source spot checks |
| Unresolved geography | Exclusion counts implemented; synthetic cases exercised | Real exclusion totals and geography decision |
| Counts, missingness, duration, impacts | Sample analyses execute and export denominators/provenance | Real estimates and interpretation review |
| County-window grid | EDA experiment constructs 146,400 windows for 100 counties in leap year 2020 | Full production table, coverage, and leakage validation |
| Independent climatology arithmetic | Fixture: 5 training windows, 3 positives, 4 county-month groups; held-out-label isolation checked | Mason's full table, coverage checks, smoothing and unseen-group policy |
| Weather coverage and timing | Requirements documented in the leakage audit | Provider choice, availability, units, valid/issue-time alignment |
| Positive-label frequency | Synthetic experiment only | Historical positive rates and split adequacy |
| EDA gate | Not approved by this documentation update | Full-data notebook, conclusions, and required reviewers |

Evidence and reproduction:

- [Data manifest](../data/data_manifest.yaml): Census filename, retrieval
  timestamp, and checksum. The county archive was retrieved on 2026-09-26.
- [Boundary fixture provenance](../data/sample/nc_counties_2024.json): source
  checksum, simplification method, and derived-file checksum.
- [Boundary tests](../tests/data/test_geography.py): inventory and corruption checks.
- [EDA notebook](../notebooks/01_storm_events_eda.ipynb): run
  `STORMROUTE_DATA_MODE=sample make eda` in the documented Bash/Codespaces setup.
- [Independent climatology review](../notebooks/independent_climatology_review.ipynb):
  run with the command in [notebooks/README.md](../notebooks/README.md).
- [Metrics documentation](../outputs/metrics/README.md): export definitions.
  Sample artifacts are regenerated under ignored `outputs/metrics/sample/`;
  they are not committed historical findings.

`outputs/metrics/data_quality.json` remains a planned production artifact, not
present evidence. NOAA full-data findings, weather coverage, and the EDA gate
must not be marked complete based on sample runs.

## Known limitations

- **Reports are not hazard truth.** No report does not imply no flooding or safe
  roads. Reporting access and practices can affect geographic and temporal counts.
- **Fixtures are synthetic.** Their positive rates, missingness, damage, and
  casualty totals cannot support claims about actual North Carolina impacts.
- **County geography is coarse.** A real county map does not identify flooded
  roads. Area-normalized counts do not adjust for road exposure or population.
- **Boundary vintage and simplification matter.** Historical years use 2024
  boundaries. The offline fixture is simplified for display only; area summaries
  use Census `ALAND`, not simplified polygon measurements.
- **Exclusions change the analyzed population.** Zone/marine-coded events are
  excluded and counted under current ingestion; no unresolved county is guessed.
- **Timing needs source review.** Ingestion applies NOAA's recorded fixed UTC
  offset. Summer-time interpretation needs a manual source check. Onset labels
  do not capture every window during an ongoing event.
- **Impacts are post-event estimates.** Damage is nominal USD, and reported
  injuries/deaths are not traveler-specific. Missing components can leave combined
  counts unknown; missing is not zero.
- **Reanalysis is retrospective.** Valid timestamps alone do not prove live
  availability. Publication lag and forecast issue time must be checked.
  Reanalysis results do not establish live accuracy or a proven numerical bound.
- **Climatology coverage is unresolved.** An unobserved county-month has no
  estimate, not zero hazard. Historical-rate features may encode reporting bias
  and need past-only construction.
- **Helene comparisons are date-based.** The exploratory window is not causal
  attribution, and counts over unequal periods are not comparable hazard rates.

## Handoff for full-data review

Mason supplies prepared event/county-window inputs and source/QA evidence.
Cameron checks counts, missingness, denominators, climatology arithmetic, and
interpretations, then updates this card and the EDA findings report with linked
full-run evidence. Weather feasibility and required EDA reviews remain separate
prerequisites. No model results, subgroup performance, or usability findings
have been established by this card.
