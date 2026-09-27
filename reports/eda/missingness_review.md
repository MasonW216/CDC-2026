# Section 3: North Carolina source missingness

Prepared for PR #18's Econ/Stats missingness deliverable. Notebook section 3
already contains the table and figure implementation on Cameron's branch;
the PR's Mason branch still contains its placeholder. This task executes that
implementation on the actual release and supplies the real-data artifacts.

## Results

Population: **14,688 North Carolina source records**, all hazards, 2015-2024,
before hazard filtering and deduplication. All 25 inspected fields use this same
denominator. Missing means null, empty, or whitespace-only. Literal zero counts
as observed; malformed nonblank values are not counted as missing.

| Source field | Missing records | Missing percentage |
|---|---:|---:|
| BEGIN_LAT | 3,729 | 25.39% |
| BEGIN_LON | 3,729 | 25.39% |
| DAMAGE_PROPERTY | 1,626 | 11.07% |
| Each of the remaining 22 inspected fields | 0 | 0.00% |

The [complete 25-field table and source hashes](../../outputs/metrics/eda_missingness.json)
and [missingness figure](../../outputs/figures/eda_missingness.png) are tracked
artifacts. The executed notebook displays the complete table.

Missing coordinates do not automatically invalidate county-coded events; county
assignment uses the documented geographic codes. Coordinate gaps may depend on
hazard/geography type and should not be filled from another row without evidence.
Missing damage is unreported, not zero. Damage is a descriptive outcome, excluded
from predictors. This table does not assess weather completeness or establish
that nonblank fields are valid.

These results do not conflict with the cleaned-event table's zero missing cells:
that table retains only the three qualifying flood hazards and a different set
of columns. This analysis changes no source values and does not exclude records.

## Reproduce and review

From the repository root, with notebook dependencies installed:

```powershell
.\.venv\Scripts\python.exe scripts/run_missingness_review.py --mode full
.\.venv\Scripts\python.exe scripts/run_missingness_review.py --mode sample
```

Full mode checks the pinned release archive's SHA-256, extracts exactly one
details file per configured year into a temporary directory, and runs notebook
sections 1-3 in a fresh kernel. The executed copy records the extracted source
hashes. Temporary extraction paths expire when execution finishes; reproduce via
the script rather than rerunning that executed copy. Canonical download files
and records are not overwritten.

Sample mode uses the tracked fixture and writes figures/metrics into separate
`sample/` directories. Executed copies are saved locally at
`outputs/executed/missingness_full.ipynb` and `missingness_sample.ipynb`.
The tracked notebook remains output-free. Both modes passed; this is a scoped
section 3 verification, not a full notebook run or approval of the EDA gate.

For PR #18, incorporate the missingness subsection from Cameron's notebook
section 3 together with these artifacts. No PR was modified by this task.
