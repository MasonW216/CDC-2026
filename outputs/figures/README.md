# Figures

Presentation-quality figures with **stable filenames**, so the README, slides,
DevPost entry, and reports can link to them without breaking.

Every figure must have a descriptive title, labeled axes with units, a legend if
needed, a data-source note, colorblind-safe colors, and resolution adequate for
a projected slide.

Committed PNG/SVG files here are final artifacts. Scratch plots stay local.

## EDA — Milestone 2 (`01_storm_events_eda.ipynb`)

| File | Shows |
|---|---|
| `eda_events_by_year.png` | Qualifying events per year, 2015–2024 |
| `eda_event_type_counts.png` | Counts by event type, before and after filtering |
| `eda_monthly_seasonality.png` | Seasonality by month |
| `eda_county_choropleth.png` | Normalized event rate by North Carolina county |
| `eda_missingness.png` | Field-level missingness |
| `eda_class_imbalance.png` | Positive-window rate by month and county |
| `eda_precipitation_event_comparison.png` | Rolling precipitation against event timing |

## Model — Milestone 4 (`03_model_evaluation.ipynb`)

| File | Shows |
|---|---|
| `model_precision_recall.png` | Precision–recall curves, all models |
| `model_calibration.png` | Reliability curves, raw vs calibrated |
| `model_comparison.png` | Climatology vs logistic vs boosted, with intervals |
| `model_feature_importance.png` | Feature importance |
| `model_helene_case_study.png` | Model behavior through the Helene period |

_No figures exist yet._
