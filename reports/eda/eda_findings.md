# EDA Findings — North Carolina Flood-Event Target

> **Status: not started.** Structure only. Complete after the full-data run of
> [`01_storm_events_eda.ipynb`](../../notebooks/01_storm_events_eda.ipynb).
> Every number below must be reproducible from that notebook.

| | |
|---|---|
| Notebook run date | _TBD_ |
| Data mode | _TBD (must be `full` for the gate)_ |
| Source files | _TBD — resolved filenames from `data/data_manifest.yaml`_ |
| Git commit | _TBD_ |

---

## Executive summary

_TBD — no more than 250 words. State whether the label is constructible, how
rare the positive class is, which features are usable, and the gate decision._

---

## Data-quality table

| Check | Requirement | Result | Pass |
|---|---|---|---|
| Unique `EVENT_ID` after cleaning | 0 duplicates | _TBD_ | ☐ |
| Timestamps timezone-aware UTC | 100% | _TBD_ | ☐ |
| Daylight-saving conversions tested | covered | _TBD_ | ☐ |
| County FIPS preserve leading zeroes | 100 counties, 5-char strings | _TBD_ | ☐ |
| Hazard filter exactly Flood / Flash Flood / Debris Flow | exact | _TBD_ | ☐ |
| Events with unresolved geography | counted and documented | _TBD_ | ☐ |
| Manually spot-checked records | ≥ 10 | _TBD_ | ☐ |
| Weather coverage by county and year | reported | _TBD_ | ☐ |
| Positive rate by year, month, county, event type | reported | _TBD_ | ☐ |
| Damage strings parsed with unit tests | covered | _TBD_ | ☐ |

---

## Headline counts

| Quantity | Value |
|---|---|
| NOAA records, all states, 2015–2024 | _TBD_ |
| After North Carolina filter | _TBD_ |
| After hazard filter | _TBD_ |
| Excluded — unresolved geography | _TBD_ |
| County-windows generated | _TBD_ |
| Positive county-windows | _TBD_ |
| Positive rate | _TBD_ |
| Positives in train / selection / calibration / test | _TBD_ / _TBD_ / _TBD_ / _TBD_ |

---

## Figures

| | |
|---|---|
| Events by year | [`eda_events_by_year.png`](../../outputs/figures/eda_events_by_year.png) |
| Event-type counts | [`eda_event_type_counts.png`](../../outputs/figures/eda_event_type_counts.png) |
| Monthly seasonality | [`eda_monthly_seasonality.png`](../../outputs/figures/eda_monthly_seasonality.png) |
| County choropleth | [`eda_county_choropleth.png`](../../outputs/figures/eda_county_choropleth.png) |
| Missingness | [`eda_missingness.png`](../../outputs/figures/eda_missingness.png) |
| Class imbalance | [`eda_class_imbalance.png`](../../outputs/figures/eda_class_imbalance.png) |
| Precipitation vs events | [`eda_precipitation_event_comparison.png`](../../outputs/figures/eda_precipitation_event_comparison.png) |

---

## Decisions

| Decision | Choice | Justification |
|---|---|---|
| Label | _TBD_ | |
| Geography and zone-coded events | _TBD_ | |
| Years and splits | _TBD_ | |
| Features accepted | _TBD_ | |
| Features rejected | _TBD_ | |
| Weather source | _TBD_ | |

## Leakage audit

| Candidate feature | Known before departure / contemporaneous / after event | Decision |
|---|---|---|
| _TBD_ | | |

---

## Unresolved risks

1. _TBD_

---

## Gate decision

**☐ Proceed ☐ Change scope ☐ Stop**

_TBD — rationale._

| Role | GitHub handle | Date |
|---|---|---|
| Decision (Product and AI lead) | _TBD_ | |
| Reviewer — interpretations and claims (Econ/Stats) | _TBD_ | |
| Reviewer — fresh-Codespace execution (CS) | _TBD_ | |
