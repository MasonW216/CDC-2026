"""Evaluate models and export metrics and figures.

Computes PR-AUC, Brier score, log loss, calibration curves, and recall and
precision at a fixed alert budget, with bootstrap confidence intervals
resampled by storm episode -- county-windows within one storm are correlated,
so row-wise resampling would report intervals that are too narrow.

PR-AUC is the headline. ROC-AUC is appendix material under severe class
imbalance.

Writes `outputs/metrics/*.json` and the prediction table, so the evaluation
notebook can be reproduced without refitting anything.
"""

# TODO(milestone-4): implement. See docs/build_guide.md.
