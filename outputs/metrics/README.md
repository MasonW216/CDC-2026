# Metrics

Machine-readable results. Every number quoted in the README, model card,
slides, or DevPost entry must trace to a file here.

| File | Produced by | Milestone |
|---|---|---|
| `eda_missingness.json` | `make eda`, section 3 | 2 |
| `eda_event_counts.json` | `make eda`, section 6 | 2 |
| `eda_event_durations.json` | `make eda`, section 6 | 2 |
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
