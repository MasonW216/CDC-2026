"""Train the baselines and the calibrated final model.

Makefile target : make train
Milestone       : 4
Reads           : data/processed/county_windows.parquet, configs/model.yaml
Writes          : artifacts/models/stormroute_model.joblib,
                  artifacts/models/model_manifest.json

Runs the locked sequence: climatology, logistic regression, monotonic boosted
model, then sigmoid calibration on 2023. The 2024 split is never loaded by
this script.
"""

# TODO(milestone-4): implement. See docs/build_guide.md.
