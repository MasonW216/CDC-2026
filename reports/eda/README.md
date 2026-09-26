# EDA report

The written evidence trail for the Milestone 2 gate.

[`eda_findings.md`](eda_findings.md) summarizes what
[`notebooks/01_storm_events_eda.ipynb`](../../notebooks/01_storm_events_eda.ipynb)
found, the decisions it supports, and the risks it leaves open — for a reader
who will not run the notebook.

[`spot_check_candidates.csv`](spot_check_candidates.csv) lists the events a
**person** must check against NOAA's event pages and NWS products, as the gate
requires. The notebook's section 4 selects them deterministically, weighted
toward the open question of whether NCEI's summer times are really `EST-5`. Fill
in the blank reviewer columns and summarize the results in `eda_findings.md`.
Re-running the notebook in full mode regenerates the list, so record results
before re-running.

Its conclusions must match the notebook's final cell exactly. If the full
production data in Milestone 3 changes a conclusion, update the report and
note the change; do not silently let the two diverge.
