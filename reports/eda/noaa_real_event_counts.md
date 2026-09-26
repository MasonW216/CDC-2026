# Real NOAA event counts: Cameron's independent analysis

The saved cleaned NOAA data are usable for descriptive event analysis: **2,220
records**, **10 columns**, zero missing cells, and unique event IDs. The CSV and
Parquet agree after restoring documented data types, and both match their saved
provenance hashes. No source values were changed by this analysis.

## Where the usable data are

- Individual cleaned records: `data/interim/events.csv` (Excel-readable) and
  `data/interim/events.parquet` (typed Python input).
- Four generated summary tables: `data/interim/noaa_descriptive/`, containing
  `counts_by_year.csv`, `counts_by_month.csv`, `counts_by_county_fips.csv`, and
  `counts_by_event_type.csv`.
- [Tracked results and input/output hashes](../../outputs/metrics/noaa_real_event_counts.json).
- [Four-panel count chart](../../outputs/figures/noaa_real_event_counts.png).

Each summary includes `event_count` and `share_of_retained_events`; the share's
denominator is 2,220. Each table independently sums to 2,220. All 100 NC counties
appear in the county table, including a zero-report row for FIPS 37075. There are
99 counties with retained reports. This does not remove any county from scope.
County identifiers should be imported as text in Excel; use the Parquet version
for typed analysis. Generated data tables remain locally ignored by Git; the
small tracked JSON includes all four tables for colleagues to inspect.

## Findings and interpretation

| Event type | Records | Share |
|---|---:|---:|
| Flash Flood | 1,665 | 75.00% |
| Flood | 535 | 24.10% |
| Debris Flow | 20 | 0.90% |

The highest annual count is 2024 (440), followed by 2020 (399) and 2018 (362).
These are reported event records, not independent storms or estimates of flood
probability. Multiple county records may describe the same larger storm.
County totals are not normalized for area, population, reporting practices, or
travel exposure; the chart's top counties are not a road-risk ranking.

Year and month use cleaned **UTC onset**. Month pools the ten years 2015-2024;
it is not a per-year average or a calendar-month exposure-adjusted rate. The
NOAA summer-time interpretation still needs independent external verification.
Zero reports do not demonstrate no flooding or safe roads.

This milestone verifies the existing clean event exports and produces real-data
counts. Weather measurements, missing deep moisture, and Currituck's weather
gap remain unchanged. These files are not a model-ready county-window table.
The existing sample notebook results remain sample results; this separate report
does not approve the EDA gate. The accompanying
[duration and impact review](noaa_duration_impact_review.md) documents the next
completed checks and annotated exports.

## Reproduce from the repository root (PowerShell)

```powershell
.\.venv\Scripts\python.exe scripts/summarize_cleaned_events.py
```

Requires the existing local cleaned files and `events.provenance.json`. The
script fails if hashes, schema, row totals, missingness, CSV/Parquet agreement,
or grouping totals do not match expectations. It overwrites only its own summary
outputs, review copies, and chart; raw data and canonical cleaned event files are
read-only inputs.
