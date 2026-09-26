"""Evaluate on the untouched 2024 test year and export results.

Makefile target : make evaluate
Milestone       : 4
Reads           : artifacts/models/, data/processed/county_windows.parquet
Writes          : outputs/predictions/predictions_2024.parquet,
                  outputs/metrics/model_comparison.json,
                  outputs/metrics/final_test_metrics.json,
                  outputs/figures/model_*.png

Run once, when modeling is finished. Tuning against its output is the one
thing that would invalidate every headline number in the submission.
"""

# TODO(milestone-4): implement. See docs/build_guide.md.
