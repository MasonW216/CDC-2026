# Metrics

Machine-readable results. Every number quoted in the README, model card,
slides, or DevPost entry must trace to a file here.

| File | Produced by | Milestone |
|---|---|---|
| `eda_missingness.json` | `make eda`, section 3 | 2 |
| `eda_event_counts.json` | `make eda`, section 6 | 2 |
| `eda_event_durations.json` | `make eda`, section 6 | 2 |
| `eda_reporting_coverage.json` | `make eda`, section 6 | 2 |
| `eda_helene_comparison.json` | `make eda`, section 6 | 2 |
| `eda_reported_impacts.json` | `make eda`, section 8 | 2 |
| `eda_geographic_distribution.json` | `make eda`, section 7 | 2 |
| `eda_label_experiment.json` | `make eda`, section 9 | 2 |
| `data_quality.json` | `make data` | 3 |
| `model_comparison.json` | `make evaluate` | 4 |
| `final_test_metrics.json` | `make evaluate` | 4 |

`final_test_metrics.json` is written **once**, from the untouched 2024 test year,
after modeling is finished. Any decision made after reading it would invalidate it.

The EDA missingness export records the NC source-row denominator, missing counts
and fractions by field, data mode, source filenames and SHA-256 checksums, and
the run's Git commit. Blank means null, empty, or whitespace-only; zero is not
missing. Counts precede hazard filtering and deduplication. A zero-row input has
null fractions, not a claim of zero missingness.

Sample-mode EDA writes to `outputs/metrics/sample/` and
`outputs/figures/sample/`, which are ignored. These synthetic results must not
be used as population findings. Full-data missingness results remain pending.

The event-count export provides annual, pooled-month, observed-county, and hazard
totals for unique cleaned events beginning within the configured UTC period.
Each breakdown reconciles to the same event total. It also records events
excluded at the UTC period boundaries, source checksums, mode, and Git commit.
County FIPS remain strings. Absent counties are not inferred to have zero
reports without a complete county inventory. Full-data counts remain pending.

The duration export uses the same retained events and UTC onset period as the
count export. It separates missing ends, recorded zero durations, and positive
durations. Summary hours (minimum, median, 90th/95th percentiles, maximum) include
zeros and exclude missing ends; statistics are null when none are known.
Quantiles use linear interpolation. Disjoint duration bins reconcile to the
known-duration count and produce `eda_event_durations.png`. Intervals are not
clipped at midnight or year end. These descriptive report durations are neither
predictors nor measurements of road closure. Full-data findings remain pending.

The reporting-coverage export includes every UTC calendar month, consecutive
zero-report runs, and annual count and percent changes. Percent changes are
null for the first year or a zero previous-year count. Annual source-file
coverage is separate and unassessed (`null`) in sample mode. The corresponding
`eda_reporting_coverage.png` marks months with no retained reports. These are
exploratory diagnostics, not tests of reporting completeness or flood absence.

The Helene comparison uses the exploratory onset window September 25, 2024
00:00 UTC (inclusive) to September 30 00:00 UTC (exclusive). It partitions
retained events into that window, the rest of 2024, and 2015–2023, with hazard
counts and distinct observed counties for each group. Shares use all 2024 or
all study-period reports as explicit denominators; empty denominators produce
null shares. The chart is `eda_helene_comparison.png`. Unequal observation
periods prevent interpreting totals as relative hazard rates, and dates alone
do not establish Helene attribution. Full-data findings remain pending.

The impact export summarizes injuries, deaths, and nominal property-damage USD
overall and by hazard, including known/missing/zero/positive counts, reported
totals, median, 90th/95th percentiles, and maximum. Unknown values are excluded
from statistics; groups without known values have null statistics. Injury/death
totals are unknown if either direct or indirect counts are missing. The chart
`eda_reported_impacts.png` contrasts zero, positive, and unknown outcomes.
These post-event outcomes are not model inputs or traveler-specific risk
estimates. Full-data findings remain pending.

The geographic export includes all 100 counties and every configured county-year,
zero-report counties, reports per study year, and land-area-normalized frequencies.
It uses Census `ALAND` square meters, not simplified polygon area. Source hashes
and boundary provenance accompany the results. `eda_county_choropleth.png` maps
reports per 1,000 land km2 per study year. Sample geometry is derived from real
Census data; sample events remain synthetic. Frequencies are not road-risk
estimates and do not establish reporting completeness.

The label experiment builds all 146,400 county-six-hour windows in training year
2020, labels qualifying UTC onsets, and reports monthly and county class balance.
It compares the literal overlap predicate separately, retaining the locked onset
definition. Missing end times do not affect onset labels and are counted in the
comparison metadata. `eda_class_imbalance.png` displays monthly positive fractions
and the distribution of county positive fractions. Sample rates are synthetic,
and negative labels do not establish safe conditions. This is an EDA experiment,
not a production training table or approval of the EDA gate.
