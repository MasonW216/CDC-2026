# Metrics

Machine-readable results. Every number quoted in the README, model card,
slides, or DevPost entry must trace to a file here.

| File | Produced by | Milestone |
|---|---|---|
| `eda_missingness.json` | `make eda`, section 3 | 2 |
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
