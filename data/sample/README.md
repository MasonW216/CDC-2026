# Sample fixtures

Tiny, tracked, fully public fixtures. They exist so the EDA notebook, the unit
tests, and CI all run in a fresh clone with **no download and no network**.

Selected with `STORMROUTE_DATA_MODE=sample` (see `configs/data.yaml`).

These files are hand-authored. They are not a random sample: every row is here
to exercise a specific failure mode. If you change a row, update this table and
the test that depends on it.

## `storm_events_sample.csv`

NOAA Storm Events *details* column subset, 16 rows, in the **exact format NCEI
publishes**: `CZ_FIPS`, `BEGIN_DAY`, and `BEGIN_TIME` are not zero-padded
(`21`, `8`, `0`), exactly as in the real 2024 file.

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

Ten model-ready rows matching the `county_windows.parquet` schema in
[docs/data_card.md](../../docs/data_card.md): five positive and five negative,
spanning the mountain (Buncombe, Haywood, Transylvania), Piedmont (Mecklenburg,
Alamance, Wake), and coastal (New Hanover, Carteret, Onslow) regions, and
covering all four split labels.

The positive rate here (50%) is **deliberately unrealistic**. It keeps the
fixture small and readable. The real positive rate is rare-event scale, is
measured in Milestone 2, and is reported in
[reports/eda/eda_findings.md](../../reports/eda/eda_findings.md). Never quote a
rate computed from this file.

## Rules

- Public, already-published values only. Never a private or re-identifiable record.
- Keep both files under a few kilobytes.
- Preserve the real column names and types of the upstream source.
- A fixture change and its test change belong in the same pull request.
