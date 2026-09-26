# Sample fixtures

Tiny, tracked, fully public fixtures. They exist so the EDA notebook, the unit
tests, and CI all run in a fresh clone with **no download and no network**.

Selected with `STORMROUTE_DATA_MODE=sample` (see `configs/data.yaml`).

These files are hand-authored. They are not a random sample: every row is here
to exercise a specific failure mode. If you change a row, update this table and
the test that depends on it.

## `storm_events_sample.csv`

NOAA Storm Events *details* column subset (30 of 51 columns), 16 rows, in the
**exact format NCEI publishes**: `CZ_FIPS`, `BEGIN_DAY`, and `BEGIN_TIME` are not
zero-padded (`21`, `8`, `0`), exactly as in the real 2024 file. `BEGIN_DATE_TIME`
and `END_DATE_TIME` are NCEI's own text rendering of the same local times; EDA
section 4 cross-checks the parsed timestamps against them.

All local times are `EST-5`, so **UTC = local + 5 hours**. A six-hour window
boundary (00, 06, 12, 18 UTC) is 19:00, 01:00, 07:00, or 13:00 local.

| `EVENT_ID` | What it is there to test |
|---|---|
| 600001 | The ordinary case: county-coded NC Flood, damage as `25.00K`, `CZ_FIPS` `21` → `37021` |
| 600002 | Crosses local midnight (22:30 → 03:30); both ends fall on 9 Sept in UTC. Damage `75K` with no decimal; empty crop damage; `CZ_FIPS` `1` → `37001` |
| 600003 | **Spans the UTC year boundary**: 2019-12-31 23:00 → 2020-01-01 09:00 UTC. Damage `2.5M` |
| 600004 | Debris Flow that begins and ends **exactly on UTC window boundaries** (06:00 → 12:00 UTC) |
| 600005 | **Zone-coded** (`CZ_TYPE=Z`) with no coordinates; cannot be placed in a county, so excluded and counted |
| 600006 | Non-qualifying event type (`Thunderstorm Wind`); filtered out |
| 600007 | `Heavy Rain`: **not** a qualifying hazard under the locked definition; guards the conflict recorded in [ADR 0000](../../docs/adr/0000-specification-precedence.md) |
| 600008 | South Carolina; removed by the state filter |
| 600009 | Begins at local midnight, published as `BEGIN_TIME` `0` → 05:00 UTC |
| 600010 | **Empty** `DAMAGE_PROPERTY`; must become NaN (not reported), not 0 |
| 600011 | Helene-period event spanning **multiple days and many windows**; `150.00M` damage; direct *and* indirect injuries (12 + 3) and deaths (4 + 1) |
| 600012 | Appears **twice, identically**; exact duplicate removed and counted |
| 600013 | **Missing end time**; kept with `end_utc` = NaT and counted |
| 600014 | Crosses local midnight (23:50 → 00:10, `END_TIME` `10`); in UTC it sits inside one window |
| 600015 | **Zero duration** (begin = end) **exactly on a UTC window boundary** (06:00 UTC). 102 of 440 qualifying NC events in 2024 have zero duration. Also the one row with a padded `CZ_FIPS` (`083`) |

County FIPS must be assembled as `STATE_FIPS + CZ_FIPS`, **padded**, and kept
as a **string**: NCEI publishes Buncombe as `21`, and it must become `37021`.
Reading this file without `dtype=str` would also turn `083` into 83. Both are
exactly the bugs `tests/data/test_noaa.py` exists to catch.

## `county_windows_sample.csv`

Twelve model-ready rows matching the `county_windows.parquet` schema in
[docs/data_card.md](../../docs/data_card.md): seven positive and five negative,
spanning the mountain (Buncombe, Haywood, Transylvania), Piedmont (Mecklenburg,
Alamance, Wake), and coastal plain (New Hanover, Carteret, Edgecombe, Halifax)
regions, and covering all four split labels.

Every label is consistent with `storm_events_sample.csv` under the locked onset
rule (`window_start <= event_begin < window_end`, UTC), and
`tests/data/test_windows.py` enforces it. Worth noting:

- Transylvania is positive in the **12:00** window: event 600012 begins at
  07:00 EST, which is 12:00 UTC.
- New Hanover is **negative** during event 600007 because Heavy Rain does not qualify.
- Halifax's zero-duration event 600015 at exactly 06:00 UTC makes the window
  **starting** at 06:00 positive and the window **ending** there negative.
- `month_sin` and `month_cos` are `sin(2π·month/12)` and `cos(2π·month/12)`.

The positive rate here (58%) is **deliberately unrealistic**. It keeps the
fixture small and readable. The real positive rate is rare-event scale, is
measured in Milestone 2, and is reported in
[reports/eda/eda_findings.md](../../reports/eda/eda_findings.md). Never quote a
rate computed from this file.

## `nc_counties_sample.geojson`

All 100 North Carolina counties from the 2024 Census TIGER/Line file, run
through `stormroute.data.geography` and then **heavily simplified** (Shapely
`simplify(0.01°)`, about 1 km, coordinates rounded to 4 decimals) so it stays
about 50 KB. It exists so the EDA choropleth and the route spatial-join tests
work in sample mode.

Columns match the canonical county table: `county_fips` (5-character string),
`name`, geometry in EPSG:4326. Borders are approximate: good for maps and for
routing tests at county scale, never for deciding which county a point near a
border is in. Regenerate from the real file rather than editing by hand.

## Rules

- Public, already-published values only. Never a private or re-identifiable record.
- Keep the CSV fixtures under a few kilobytes; the county GeoJSON is the one exception (~50 KB).
- Preserve the real column names and types of the upstream source.
- A fixture change and its test change belong in the same pull request.
