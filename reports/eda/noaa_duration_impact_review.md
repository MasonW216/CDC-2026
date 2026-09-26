# NOAA duration and impact review

Owner: Cameron (Econ/Stats). Input: the 2,220 saved cleaned NOAA records from
the 2026-09-26 release, covering 2015-2024. This is descriptive quality review,
not an approved change to event labels or weather features.

## Ready-to-use files

`data/interim/noaa_descriptive/events_review.csv` contains every original event
and field, plus duration in hours and boolean review flags. The equivalent
`events_review.parquet` preserves types. `review_queue.csv` contains the 311
distinct records with at least one flag. These generated files are ignored by
Git; reproduce them with the command in [the count report](noaa_real_event_counts.md).

Original event values are unchanged. The script verifies all original columns
against the canonical table and verifies the annotated Parquet after writing.
Review flags are for analysts, not prediction inputs or approved exclusions.

## Results

All four reviewed fields have 2,220 nonmissing, nonnegative values.

| Field | Zero-valued records | Median | Maximum | Upper-tail flags |
|---|---:|---:|---:|---:|
| Duration (hours) | 231 | 2.5833 | 193.5 | 23 |
| Reported injuries | 2,215 | 0 | 4 | 5 |
| Reported deaths | 2,162 | 0 | 15 | 58 |
| Reported property damage (nominal USD) | 1,232 | 0 | 300,000,000 | 23 |

The sums of recorded impacts are 8 injuries, 142 deaths, and $3,155,355,110 in
property damage. Injuries/deaths combine direct and indirect source counts under
the existing cleaner. These are sums of retained event records, not independently
verified unique victims or a complete accounting of economic losses. Damage is
not inflation-adjusted and is not traveler-specific loss. Recorded zeros are
preserved; they do not establish exhaustive measurement of impacts.

## Flag policy and what to do with it

- `review_zero_duration`: onset and end coincide (231 records). Keep these
  records: the project's label uses onset, so a zero duration does not invalidate
  a qualifying event. Do not invent an end time.
- `review_upper_tail_*`: positive values at or above that field's empirical 99th
  percentile across all 2,220 rows, with linear quantile interpolation and ties
  included. Thresholds are approximately 85.0025 hours, 0 injuries, 1 death, and
  $31,863,000 damage. For sparse injury counts the threshold is zero, so all five
  positive records are flagged. Ties mean these are not exactly 1% of records.
- `review_any`: any of the above flags. Flags overlap, so their counts must not
  be added to estimate distinct records. The union is 311 records.

These thresholds prioritize manual inspection only. Flood durations and impacts
can legitimately be extreme. Do not clip, winsorize, delete, or impute values on
the basis of these flags. Compare a flagged record's `event_id` with source
documentation before proposing a correction; keep that evidence in the QA trail.
An unflagged row is not independently verified or guaranteed error-free.

## Remaining limitations

NOAA summer timestamp interpretation still needs external verification. No
weather values were repaired or inferred, and Currituck remains deferred.
Impact columns are outcomes and must not enter predictive features; duration
also uses the eventual event end and should remain descriptive here.

Full numerical summaries, flags policy, and file hashes are stored in
[`noaa_real_event_counts.json`](../../outputs/metrics/noaa_real_event_counts.json).
The independent count and duration/impact milestones are now prepared for review.
