# Section 6: annual counts and monthly seasonality

Cameron's next PR #18 deliverable: the two individual temporal count figures,
computed by the existing notebook section 6 from the pinned full NOAA release.
The complete section 6 has now passed scoped full-data and sample execution;
this does not approve the entire EDA gate.

## Findings

All **2,220 retained, unique flood-event records** begin within the configured
2015-2024 UTC period; zero records were excluded by this period filter. Year,
month, county, and hazard breakdowns each independently sum to 2,220.

| UTC onset year | Reports |
|---|---:|
| 2015 | 198 |
| 2016 | 245 |
| 2017 | 107 |
| 2018 | 362 |
| 2019 | 114 |
| 2020 | 399 |
| 2021 | 111 |
| 2022 | 89 |
| 2023 | 155 |
| 2024 | 440 |

| UTC onset month (pooled across ten years) | Reports |
|---|---:|
| January | 77 |
| February | 83 |
| March | 14 |
| April | 116 |
| May | 130 |
| June | 154 |
| July | 237 |
| August | 385 |
| September | 465 |
| October | 313 |
| November | 159 |
| December | 87 |

2024 has the largest annual count, followed by 2020 and 2018. September has
the largest pooled monthly count. These describe the retained reporting data;
they do not prove a long-term trend, reporting completeness, or independent
storm frequency. One storm can generate multiple county event records. Months
are pooled totals, not annual averages or rates adjusted for days of exposure.
No model selection or predictor tuning is performed with these descriptive data.

## Deliverables and validation

- [Annual figure](../../outputs/figures/eda_events_by_year.png).
- [Monthly figure](../../outputs/figures/eda_monthly_seasonality.png).
- [All breakdowns and source hashes](../../outputs/metrics/eda_event_counts.json).

The notebook retains the same UTC fixed-offset cleaning rules; no event values
or project scope were changed. Its count conclusion now reports the observed
peaks and the limits of interpretation. Full and sample scoped runs pass, with
sample artifacts kept separate. The runner executes sections 1-3, the cleaner,
and the section 6 count subsection; it does not overwrite the human spot-check
sheet or execute the remaining notebook sections. This does not certify a full
restart-and-run-all or replace the two reviewer approvals required by PR #18.

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run_missingness_review.py --task counts --mode full
.\.venv\Scripts\python.exe -X utf8 scripts/run_missingness_review.py --task counts --mode sample
```

Full mode requires the previously downloaded release archive, whose checksum
is verified before extracting temporary input files. Executed review copies are
saved under ignored `outputs/executed/counts_full.ipynb` and `counts_sample.ipynb`.
The runner's default task remains the section 3 missingness review.

Next PR deliverable: section 7's county choropleth and geographic interpretation.
The PR itself has not been edited or approved by this task.

## Completed duration, coverage, and Helene-period review

All 2,220 retained events have known, nonnegative duration: 231 record zero
hours and 1,989 record positive duration. Median duration is 2.5833 hours,
90th percentile 12 hours, 95th percentile 22.2508 hours, and maximum 193.5 hours.
Quantiles include recorded zeros. No duration was imputed, clipped, or used as
a predictor. These intervals do not measure road closures.

All ten expected annual source files are present. Of the 120 calendar months,
35 have no retained reports, arranged in 20 runs. The longest run is four months,
November 2016 through February 2017. Source-file availability does not establish
complete reporting; these zeros are not proof of missing source data or no flooding.

The largest absolute annual change is 2020 to 2021: 399 to 111 reports
(-288; -72.18%). The increases into 2020 and 2024 are each 285 reports
(+250.00% and +183.87%, respectively). These are descriptive changes, not
significance tests or evidence of a reporting-system change.

The selected window [2024-09-25 00:00 UTC, 2024-09-30 00:00 UTC) contains
89 onsets across 43 counties: 69 Flash Flood, 19 Flood, and 1 Debris Flow.
This is 20.23% of the 440 reports in 2024 and 4.01% of all 2,220 reports.
The remaining groups contain 351 reports in the rest of 2024 and 1,780 in
2015-2023. These mutually exclusive groups reconcile to the full population.
Their different observation durations prevent direct rate comparisons. Date
membership alone does not attribute a report to Helene. The held-out year is
used only for this descriptive analysis, not model selection.

Additional evidence:

- [Duration table](../../outputs/metrics/eda_event_durations.json) and
  [figure](../../outputs/figures/eda_event_durations.png).
- [Coverage and annual changes](../../outputs/metrics/eda_reporting_coverage.json)
  and [figure](../../outputs/figures/eda_reporting_coverage.png).
- [Helene-window comparison](../../outputs/metrics/eda_helene_comparison.json)
  and [figure](../../outputs/figures/eda_helene_comparison.png).

Reproduce the entire section 6, including its prerequisites, without regenerating
manual-review forms or running sections 7-12:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/run_missingness_review.py --task temporal --mode full
.\.venv\Scripts\python.exe -X utf8 scripts/run_missingness_review.py --task temporal --mode sample
```

Executed copies are `outputs/executed/temporal_full.ipynb` and
`temporal_sample.ipynb`. All figures use labeled units, source notes, the notebook
palette, stable names, and 200 dpi exports. Section 6 is prepared for teammate
review; integration into Mason's PR and the gate approvals remain outstanding.
