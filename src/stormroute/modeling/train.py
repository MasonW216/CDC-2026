"""Train the monotonic gradient-boosted hazard classifier.

Fits on 2015-2021 and selects hyperparameters on 2022 only. Monotonic
constraints from `configs/model.yaml` guarantee that more rainfall or wetter
soil can never reduce the modeled hazard, which is what makes the model
defensible to a judge rather than merely accurate.

2024 is not read here. Not for early stopping, not for a sanity check.
"""

# TODO(milestone-4): implement. See docs/build_guide.md.
