# Metrics

Machine-readable results. Every number quoted in the README, model card,
slides, or DevPost entry must trace to a file here.

| File | Produced by | Milestone |
|---|---|---|
| `data_quality.json` | `make data` | 3 |
| `model_comparison.json` | `make evaluate` | 4 |
| `final_test_metrics.json` | `make evaluate` | 4 |

`final_test_metrics.json` is written **once**, from the untouched 2024 test year,
after modeling is finished. Any decision made after reading it would invalidate it.

_No metrics exist yet._
