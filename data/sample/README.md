# Sample fixtures

Tiny, tracked, fully public fixtures. They exist so the EDA notebook, the unit
tests, and CI all run in a fresh clone with **no download and no network**.

Selected with `STORMROUTE_DATA_MODE=sample` (see `configs/data.yaml`).

These files are hand-authored. They are not a random sample: every row is here
to exercise a specific failure mode. If you change a row, update this table and
the test that depends on it.

## `storm_events_sample.csv`

NOAA Storm Events *details* column subset, 15 rows.

| `EVENT_ID` | What it is there to test |
|---|---|
| 600001 | The ordinary case: county-coded NC Flood, damage as `25.00K` |
| 600002 | Spans midnight (22:30 → 03:30 next day); damage written as `75K` with no decimal; empty crop damage |
| 600003 | **Spans a year boundary** (2019-12-31 21:00 → 2020-01-01 04:00); damage as `2.5M` |
| 600004 | Debris Flow, and begins and ends **exactly on six-hour window boundaries** (06:00 → 12:00) |
| 600005 | **Zone-coded** (`CZ_TYPE=Z`) with no coordinates — cannot be assigned to a county without a crosswalk |
| 600006 | Non-qualifying event type (`Thunderstorm Wind`) — must be filtered out |
| 600007 | `Heavy Rain` — **not** a qualifying hazard under the locked definition; guards against the specification conflict recorded in [ADR 0000](../../docs/adr/0000-specification-precedence.md) |
| 600008 | South Carolina — must be removed by the state filter |
| 600009 | Begins exactly at `00:00` on a window boundary |
| 600010 | **Empty** `DAMAGE_PROPERTY` string |
| 600011 | Helene-period event spanning **multiple days and many windows**; large damage (`150.00M`), non-zero injuries and deaths |
| 600012 | Appears **twice, identically** — exercises duplicate-`EVENT_ID` detection and de-duplication |
| 600013 | **Missing end time** |
| 600014 | Short event crossing midnight inside a single window (23:50 → 00:10) |

County FIPS must be assembled as `STATE_FIPS + CZ_FIPS` and kept as a **string**:
`021` is Buncombe, not the integer 21. Reading this file without
`dtype=str` silently destroys the leading zero, which is exactly the bug
`tests/data/test_noaa.py` exists to catch.

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
