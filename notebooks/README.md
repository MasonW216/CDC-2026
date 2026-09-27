# Notebooks

Analysis notebooks, run in order. Each one reads like a short paper: Markdown
states the question before every analytical section and the conclusion after it.

| Notebook | Milestone | Purpose | Blocked until |
|---|---|---|---|
| [`01_storm_events_eda.ipynb`](01_storm_events_eda.ipynb) | 2 | EDA and the **verification gate** | Milestone 1 data layer |
| [`02_weather_feature_validation.ipynb`](02_weather_feature_validation.ipynb) | 3 | Validate the production feature table | EDA gate approved |
| [`03_model_evaluation.ipynb`](03_model_evaluation.ipynb) | 4 | Reproduce every metric from saved predictions | Model trained |

## Running

Cameron's [independent climatology review](independent_climatology_review.ipynb)
is a separate sample-only arithmetic cross-check, not a model implementation.
It uses the prepared county-window fixture, counts training positives and
denominators independently, and checks that held-out labels cannot affect them.
Mason reviews the results. Full-data verification awaits his prepared table;
this notebook does not choose smoothing or approve the EDA gate.

```bash
uv run jupyter nbconvert --to notebook --execute notebooks/independent_climatology_review.ipynb --output-dir outputs/executed
```

```bash
make eda                                   # 01, full data, in place
STORMROUTE_DATA_MODE=sample make eda       # 01, tracked fixtures only — what CI runs
```

In Codespaces, open a notebook and pick the `.venv` kernel.

## Rules

1. **Restart and run all before you commit.** Execution counts must be
   sequential. A notebook that only works with hidden state is broken.
2. **No absolute paths.** Resolve everything from the repository root through
   `stormroute.config`.
3. **No stored outputs in Git.** `nbstripout` strips them at commit; CI rejects
   any that slip through. Figures worth keeping are exported to
   `outputs/figures/` with the stable names listed there.
4. **Reusable logic moves into `src/stormroute/`.** A function you want in two
   notebooks, or in the pipeline, belongs in the package with a test.
5. **Every displayed count must be reproducible from code in the notebook.**
   No numbers typed into Markdown by hand.
6. **No unexplained warnings.** Fix it, or say in Markdown why it is safe.
7. **Every figure** has a descriptive title, labeled axes with units, a legend if
   needed, a data-source note, colorblind-safe colors, and slide resolution.

## Sample mode vs. full mode

CI proves the notebooks *execute*; it does not prove the *findings*. The tracked
fixtures are hand-built to hit edge cases and have an intentionally unrealistic
positive rate. Full-data verification is evidence recorded in the EDA pull
request and in [`reports/eda/eda_findings.md`](../reports/eda/eda_findings.md).
Re-run the full-data notebook whenever ingestion logic changes.
