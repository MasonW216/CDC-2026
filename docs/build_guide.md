# StormRoute GitHub Repository and Delivery Guide

**Project:** StormRoute — Explainable AI for Weather-Aware Travel Safety  
**Competition:** Carolina Data Challenge 2026, Natural Science Track  
**Theme:** AI for Social Good  
**Team:** Three people  
**Primary geography:** North Carolina  
**Primary hazards:** Flood, Flash Flood, and Debris Flow  
**Status:** Repository creation and implementation instructions  

---

## 1. Purpose of this guide

This document defines how the team will create, organize, build, verify, and present StormRoute in a professional GitHub repository.

It is deliberately more specific than a general project plan. A teammate should be able to open this document and determine:

- which files and folders to create
- what belongs in each file
- which work must happen first
- which teammate owns each deliverable
- what each Git commit and pull request should contain
- what evidence is required before moving to the next milestone
- how to run the project in GitHub Codespaces
- how the final repository should look to judges and recruiters

The required order is:

```text
Repository scaffold
        ↓
Reproducible data download
        ↓
EDA notebook and verification gate
        ↓
Production data pipeline
        ↓
Baselines and final model
        ↓
Risk scoring and recommendations
        ↓
API and website
        ↓
Evaluation, accessibility, and demo hardening
        ↓
Release, DevPost, and presentation
```

**No production modeling or application code should begin until the EDA verification gate in Milestone 2 is approved.** Repository setup and minimal data-download utilities are allowed before that gate because they are required to make the EDA reproducible.

---

## 2. Locked project definition

StormRoute is a web application that:

1. accepts a North Carolina origin, destination, and departure time;
2. compares candidate routes and departure times;
3. assigns each trip a 0–100 Weather Safety Score;
4. identifies the route segment with the greatest modeled flood-hazard exposure;
5. recommends a route or departure-time change that improves the score; and
6. shows the improvement, travel-time cost, supporting weather evidence, and official alerts.

The machine-learning model estimates the probability that a reported Flood, Flash Flood, or Debris Flow event begins in a North Carolina county during a six-hour window. The score is a comparative weather-hazard exposure index. It is not a crash probability or guarantee of safety.

### 2.1 Canonical definitions

All code and documentation must use these definitions unless the entire team approves a documented change:

| Item | Locked definition |
|---|---|
| Geography | North Carolina |
| Historical period | 2015–2024 |
| Prediction unit | County × six-hour window |
| Positive label | At least one Flood, Flash Flood, or Debris Flow event begins in the county-window |
| Training | 2015–2021 |
| Model selection | 2022 |
| Calibration | 2023 |
| Final test | 2024, untouched until final evaluation |
| Main model | Monotonic gradient-boosted classifier with sigmoid calibration |
| Baselines | County-month climatology and logistic regression |
| Route aggregation | Cumulative-hazard aggregation weighted by time exposed |
| Live authority | Official NWS alerts may raise risk, never lower it |

### 2.2 Explicitly out of scope

- nationwide coverage
- exact road-flooding prediction
- crash, injury, or fatality prediction
- personalized judgments based on driver demographics
- autonomous navigation or emergency dispatch
- user accounts
- crowdsourced or social-media reports
- LLM-generated safety advice

---

## 3. Create the GitHub repository

### 3.1 Repository settings

Create one public repository named:

```text
stormroute
```

Use this description:

```text
Explainable AI that helps North Carolina travelers compare routes and departure times to reduce flood-hazard exposure.
```

Recommended GitHub topics:

```text
ai-for-social-good
data-science
machine-learning
fastapi
react
geospatial
weather
explainable-ai
carolina-data-challenge
```

Initialize the repository without generated application code. Add the files from Milestone 0 in one scaffold pull request.

### 3.2 Access and protection

- Add all three teammates as collaborators.
- Protect `main` after the first scaffold merge.
- Require a pull request before merging.
- Require at least one teammate approval.
- Require the continuous-integration checks to pass.
- Block force pushes and branch deletion on `main`.
- Enable secret scanning and dependency alerts.
- Enable Issues and GitHub Projects.

If branch protection is unavailable under the repository plan, the team must still follow the same rules manually.

### 3.3 GitHub Project board

Create one project board with these columns:

```text
Backlog → Ready → In Progress → Review → Verified → Done
```

Every issue must contain:

- one owner
- one milestone
- a short user or technical outcome
- an explicit acceptance checklist
- links to its pull request and evidence

Labels:

```text
area:data
area:eda
area:model
area:geospatial
area:api
area:frontend
area:docs
area:presentation
priority:must
priority:should
priority:stretch
blocked
bug
```

### 3.4 Branch and merge rules

Use short-lived branches:

```text
eda/noaa-profile
data/county-windows
model/calibrated-xgb
geo/route-sampling
api/trip-score
web/results-page
docs/model-card
fix/<short-description>
```

Rules:

1. Do not commit directly to `main` after Milestone 0.
2. Keep one logical outcome per pull request.
3. Rebase or update the branch before requesting final review.
4. Squash-merge ordinary feature branches.
5. Never commit API keys, `.env` files, raw downloads, caches, or large generated data.
6. Never merge a notebook that fails when executed from a fresh Codespace.

### 3.5 Commit format

Use Conventional Commit-style messages:

```text
chore(repo): scaffold Codespaces development environment
data(noaa): add reproducible Storm Events download
eda(storms): profile NC flood labels from 2015 to 2024
feat(model): train calibrated monotonic hazard classifier
feat(scoring): aggregate county-window risks across a route
feat(web): display score and actionable recommendation
test(api): cover alert-floor behavior
docs(model): publish evaluation and limitations
fix(data): preserve leading zeroes in county FIPS
```

A commit should leave the branch runnable. Avoid messages such as `updates`, `stuff`, `final`, or `fixes`.

---

## 4. Required repository structure

Create the following structure. Files marked **generated** are produced by scripts or notebooks; files marked **ignored** should exist locally but should not normally be committed.

```text
stormroute/
├── .devcontainer/
│   └── devcontainer.json
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   ├── data_task.yml
│   │   └── feature_request.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── dependabot.yml
│   └── workflows/
│       ├── ci.yml
│       └── notebook.yml
├── artifacts/
│   ├── models/
│   │   ├── .gitkeep
│   │   └── model_manifest.json
│   └── demo/
│       ├── demo_routes.geojson
│       ├── demo_scores.json
│       └── demo_weather.json
├── backend/
│   ├── README.md
│   ├── pyproject.toml
│   ├── src/
│   │   └── stormroute_api/
│   │       ├── __init__.py
│   │       ├── main.py
│   │       ├── config.py
│   │       ├── dependencies.py
│   │       ├── schemas.py
│   │       ├── routes/
│   │       │   ├── __init__.py
│   │       │   ├── health.py
│   │       │   ├── score.py
│   │       │   └── scenarios.py
│   │       └── services/
│   │           ├── __init__.py
│   │           ├── model_service.py
│   │           ├── route_service.py
│   │           ├── weather_service.py
│   │           └── cache_service.py
│   └── tests/
│       ├── test_health.py
│       ├── test_score_contract.py
│       └── test_demo_scenario.py
├── configs/
│   ├── data.yaml
│   ├── model.yaml
│   ├── scoring.yaml
│   └── demo.yaml
├── data/
│   ├── README.md
│   ├── data_manifest.yaml
│   ├── raw/                       # ignored except .gitkeep
│   │   └── .gitkeep
│   ├── interim/                   # ignored except .gitkeep
│   │   └── .gitkeep
│   ├── processed/                 # ignored except .gitkeep
│   │   └── .gitkeep
│   └── sample/
│       ├── storm_events_sample.csv
│       ├── county_windows_sample.csv
│       └── README.md
├── docs/
│   ├── architecture.md
│   ├── data_card.md
│   ├── model_card.md
│   ├── risk_methodology.md
│   ├── responsible_ai.md
│   ├── demo_runbook.md
│   ├── presentation_outline.md
│   ├── devpost_draft.md
│   ├── references.md
│   └── adr/
│       ├── 0001-county-six-hour-target.md
│       ├── 0002-calibrated-boosted-model.md
│       └── 0003-reanalysis-live-forecast-boundary.md
├── frontend/
│   ├── README.md
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── public/
│   │   └── stormroute-mark.svg
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── styles.css
│   │   ├── components/
│   │   │   ├── TripForm.tsx
│   │   │   ├── SafetyScore.tsx
│   │   │   ├── RouteMap.tsx
│   │   │   ├── SegmentDetail.tsx
│   │   │   ├── RecommendationCard.tsx
│   │   │   ├── AlertBanner.tsx
│   │   │   ├── ConfidencePanel.tsx
│   │   │   └── MethodologyDrawer.tsx
│   │   ├── pages/
│   │   │   ├── PlannerPage.tsx
│   │   │   ├── ResultsPage.tsx
│   │   │   └── MethodologyPage.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── types/
│   │   │   └── trip.ts
│   │   ├── fixtures/
│   │   │   └── demoScore.json
│   │   └── test/
│   │       ├── SafetyScore.test.tsx
│   │       └── RecommendationCard.test.tsx
│   └── e2e/
│       └── demo-flow.spec.ts
├── notebooks/
│   ├── README.md
│   ├── 01_storm_events_eda.ipynb
│   ├── 02_weather_feature_validation.ipynb
│   └── 03_model_evaluation.ipynb
├── outputs/
│   ├── figures/
│   │   ├── .gitkeep
│   │   └── README.md
│   ├── metrics/
│   │   ├── .gitkeep
│   │   └── README.md
│   └── predictions/               # ignored except small demo extracts
│       └── .gitkeep
├── reports/
│   └── eda/
│       ├── README.md
│       └── eda_findings.md
├── scripts/
│   ├── download_noaa.py
│   ├── download_boundaries.py
│   ├── fetch_weather.py
│   ├── build_county_windows.py
│   ├── train_model.py
│   ├── evaluate_model.py
│   ├── cache_demo.py
│   └── verify_repository.py
├── src/
│   └── stormroute/
│       ├── __init__.py
│       ├── config.py
│       ├── data/
│       │   ├── __init__.py
│       │   ├── noaa.py
│       │   ├── weather.py
│       │   ├── geography.py
│       │   └── validation.py
│       ├── features/
│       │   ├── __init__.py
│       │   ├── windows.py
│       │   ├── rolling_weather.py
│       │   ├── terrain.py
│       │   └── climatology.py
│       ├── modeling/
│       │   ├── __init__.py
│       │   ├── baselines.py
│       │   ├── train.py
│       │   ├── calibrate.py
│       │   ├── evaluate.py
│       │   └── explain.py
│       ├── routing/
│       │   ├── __init__.py
│       │   ├── client.py
│       │   ├── sampling.py
│       │   └── spatial_join.py
│       └── scoring/
│           ├── __init__.py
│           ├── segment.py
│           ├── aggregate.py
│           ├── alerts.py
│           └── recommendations.py
├── tests/
│   ├── conftest.py
│   ├── data/
│   │   ├── test_noaa.py
│   │   ├── test_windows.py
│   │   └── test_no_leakage.py
│   ├── modeling/
│   │   ├── test_splits.py
│   │   ├── test_calibration.py
│   │   └── test_model_contract.py
│   ├── routing/
│   │   ├── test_sampling.py
│   │   └── test_spatial_join.py
│   └── scoring/
│       ├── test_aggregation.py
│       ├── test_alert_floor.py
│       └── test_recommendations.py
├── .editorconfig
├── .env.example
├── .gitattributes
├── .gitignore
├── .pre-commit-config.yaml
├── CITATION.cff
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── Makefile
├── README.md
├── SECURITY.md
├── pyproject.toml
└── uv.lock
```

### 4.1 Files that must not be committed

The root `.gitignore` must exclude:

```text
.env
.venv/
node_modules/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
data/raw/*
data/interim/*
data/processed/*
outputs/predictions/*
artifacts/cache/
*.log
.DS_Store
```

Add negation rules so `.gitkeep`, README files, sample data, final figures, final metrics, and the small cached demo artifacts remain tracked.

Never put data under a teammate's Downloads path in code or notebooks. Every path must resolve relative to the repository root or through configuration.

---

## 5. GitHub Codespaces setup

### 5.1 Development environment

The Codespace must provide:

- Python 3.11
- Node.js 20
- Git and GitHub CLI
- GDAL-compatible geospatial libraries
- JupyterLab and notebook support
- ports 8000 and 5173
- recommended VS Code extensions for Python, Jupyter, Ruff, ESLint, Prettier, and GitHub Actions

`.devcontainer/devcontainer.json` must:

- use a pinned Microsoft Python devcontainer image;
- install Node through a devcontainer feature;
- run `make setup` after container creation;
- forward FastAPI on port 8000;
- forward Vite on port 5173; and
- set no real secrets.

### 5.2 Environment variables

Commit `.env.example` with names and safe placeholders only:

```text
STORMROUTE_ENV=development
STORMROUTE_DATA_DIR=data
STORMROUTE_MODEL_PATH=artifacts/models/stormroute_model.joblib
NWS_USER_AGENT=StormRoute/0.1 contact@example.com
ROUTING_BASE_URL=https://router.project-osrm.org
VITE_API_BASE_URL=http://localhost:8000
```

Each developer copies it locally to `.env`. Real contact information, paid API tokens, or deployment credentials belong in Codespaces secrets or repository environment secrets.

### 5.3 Required root commands

The root `Makefile` must expose a small, memorable interface:

```text
make setup          Install Python, notebook, and frontend dependencies
make download       Download/version required source data
make eda            Execute the EDA notebook from top to bottom
make data           Build the production county-window table
make train          Train baselines and the candidate final model
make evaluate       Evaluate and export final metrics/figures
make api            Start FastAPI on port 8000
make web            Start Vite on port 5173
make test           Run Python and frontend tests
make lint           Run formatters, linters, and type checks
make verify         Run the complete repository verification suite
make demo-cache     Rebuild the offline presentation scenario
```

The README must show these commands in the same order. Do not make judges learn several unrelated setup procedures.

### 5.4 Dependency policy

- Define the Python package, runtime dependencies, development dependencies, Ruff, Pytest, and type-checker settings in the root `pyproject.toml`.
- Lock Python dependencies in `uv.lock`.
- Define frontend dependencies in `frontend/package.json` and lock them in `frontend/package-lock.json`.
- Pin major versions. Do not use unbounded dependencies.
- Run Dependabot weekly for Python, npm, and GitHub Actions.

---

## 6. Data management contract

### 6.1 Required sources

`data/data_manifest.yaml` is the source of truth for datasets. Each entry must contain:

- dataset name
- publisher
- source URL
- years and geography
- access date
- license or public-use statement
- local raw path
- expected file pattern
- checksum when practical
- pipeline script that uses it

Required entries:

1. NOAA Storm Events details, 2015–2024
2. NOAA Storm Events locations, 2015–2024 if used
3. ERA5-Land hourly weather accessed directly or through a documented API
4. 2024 Census TIGER/Line North Carolina county boundaries
5. NWS forecast and alert API documentation
6. OpenStreetMap/OSRM routing source and attribution

Optional entries:

7. USGS 3DEP elevation
8. CDC/ATSDR Social Vulnerability Index for evaluation only

### 6.2 Data layers

```text
data/raw/        Immutable downloaded source files
data/interim/    Cleaned source-specific tables and temporary joins
data/processed/  Model-ready county-window and route tables
data/sample/     Tiny, de-identified or public fixtures tracked by Git
```

Rules:

- Never edit a raw file manually.
- A script must be able to recreate every interim and processed file.
- Large files remain outside Git.
- Small sample fixtures must preserve schemas and edge cases.
- Every processed table must contain a creation timestamp and source-version metadata in a sidecar JSON or Parquet metadata.

### 6.3 Canonical schemas

`events.parquet`:

```text
event_id
episode_id
county_fips
begin_utc
end_utc
event_type
source
injuries
deaths
property_damage_usd
```

`county_windows.parquet`:

```text
county_fips
window_start_utc
label_flood_event
precip_1h
precip_3h
precip_6h
precip_24h
precip_72h
max_precip_intensity
temperature
wind_speed
wind_gust
soil_moisture_shallow
soil_moisture_deep
elevation_mean
slope_mean
month_sin
month_cos
```

`predictions_2024.parquet`:

```text
county_fips
window_start_utc
y_true
climatology_probability
logistic_probability
raw_model_probability
calibrated_probability
split
```

`demo_routes.geojson`:

```text
route_id
sample_order
latitude
longitude
county_fips
cumulative_minutes
segment_minutes
distance_km
```

Schema changes require:

1. an updated schema in this guide or `docs/data_card.md`;
2. updated validation tests;
3. notification to all three teammates; and
4. a pull request labeled `area:data`.

---

## 7. Milestone 0 — Professional repository scaffold

### Owner

CS major, reviewed by Mason.

### Create

- root governance and configuration files
- `.devcontainer/devcontainer.json`
- empty directory structure with `.gitkeep` files
- Python package skeleton
- frontend Vite/React/TypeScript skeleton
- GitHub issue and pull-request templates
- basic CI that checks formatting and imports

### Required first pull request

**Branch:** `chore/repository-scaffold`  
**PR title:** `chore: scaffold StormRoute repository and Codespace`  
**Squash commit:** `chore(repo): scaffold reproducible Codespaces environment`

### Acceptance criteria

- A fresh Codespace completes `make setup` without manual repair.
- `python -c "import stormroute"` succeeds.
- The FastAPI health endpoint returns HTTP 200.
- The Vite placeholder page loads on port 5173.
- `make lint` and `make test` pass.
- No secrets or local absolute paths appear in tracked files.
- The README states that EDA is the first scientific milestone.

### Deliverable

A clean repository that is ready for data work but contains no unvalidated model or product claims.

---

## 8. Milestone 1 — Reproducible source data for EDA

### Owners

- Mason: NOAA download and label scope
- Econ/Stats major: manifest and source documentation
- CS major: county-boundary download and file-path reliability

### Create

- `data/data_manifest.yaml`
- `data/README.md`
- `scripts/download_noaa.py`
- `scripts/download_boundaries.py`
- `src/stormroute/data/noaa.py`
- `src/stormroute/data/geography.py`
- `src/stormroute/data/validation.py`
- small tracked fixtures in `data/sample/`
- unit tests for parsing dates, county FIPS, event types, and damage strings

### NOAA download behavior

The downloader must:

1. identify annual 2015–2024 detail files;
2. store source files in `data/raw/noaa_storm_events/`;
3. record the resolved filenames and access time;
4. filter North Carolina only in a separate transformation step;
5. preserve original event IDs;
6. never overwrite a differing file silently; and
7. support a `--sample` mode for CI and notebook smoke tests.

### Pull requests

1. `data(noaa): add versioned Storm Events ingestion`
2. `data(geo): add North Carolina county boundaries`
3. `test(data): validate event times, FIPS, and hazard filters`

### Acceptance criteria

- One command downloads or locates the required source files.
- The process works in a new Codespace.
- The sample dataset is sufficient to execute every EDA section.
- Checks verify unique event IDs and valid timestamps.
- All 100 North Carolina county FIPS codes preserve leading zeroes.
- Hazard filtering is exactly Flood, Flash Flood, and Debris Flow.

### Deliverable

A reproducible, documented, and tested input layer for the EDA notebook.

---

## 9. Milestone 2 — EDA notebook, report, and mandatory verification gate

This milestone must be completed and approved before production modeling, scoring, API, or website features begin.

### Primary notebook

Create:

```text
notebooks/01_storm_events_eda.ipynb
```

The notebook must read like an analytical narrative, not a scratchpad. Use Markdown before each analytical section to state the question being tested and a short conclusion after each result.

### Required notebook sections

#### 1. Objective and scope

- State the traveler-safety problem.
- Define the prediction unit and positive label.
- State the geography and years.
- State that fatalities and damage are descriptive outcomes, not model inputs.

#### 2. Reproducibility information

- Print the data-manifest version or source filenames.
- Print the analysis timestamp and package versions.
- Set plotting style and random seed.
- Resolve paths from the repository root.

#### 3. Schema and first-pass inspection

- dimensions, columns, and data types
- sample records
- duplicate `EVENT_ID` count
- missingness table
- unique values for `STATE`, `CZ_TYPE`, and `EVENT_TYPE`

#### 4. Time-field validation

- construct timezone-aware beginning and ending timestamps
- count invalid or missing timestamps
- test events spanning midnight or year boundaries
- document the UTC conversion rule

#### 5. Hazard and geography filters

- show counts before and after the North Carolina filter
- show counts before and after the three-event-type filter
- distinguish county-coded, zone-coded, and coordinate-located events
- report events that cannot be assigned confidently to a county

#### 6. Temporal coverage

- annual event counts, 2015–2024
- monthly seasonality
- event duration distribution
- reporting gaps or abrupt changes
- Hurricane Helene period highlighted without treating one storm as the whole dataset

#### 7. Geographic distribution

- events by county
- normalized event rate by county and year
- North Carolina choropleth
- counties with zero reported qualifying events
- discussion of reporting bias and county-size effects

#### 8. Descriptive impact analysis

- injuries, deaths, and property damage distributions
- median and upper-tail damage by event type
- explicit warning that these variables occur after the event and cannot be predictors
- one chart that connects the project to traveler safety without sensationalizing harm

#### 9. Label construction experiment

- generate all county × six-hour windows for at least one complete year
- assign positive labels according to the locked definition
- calculate the positive rate
- demonstrate why event rows alone cannot train a classifier
- show class imbalance by month and county

#### 10. Weather-feature feasibility check

- retrieve a small ERA5-Land/Open-Meteo sample for at least three counties
- include a mountain, Piedmont, and coastal county
- verify hourly precipitation, soil moisture, temperature, and wind availability
- test 3-, 6-, 24-, and 72-hour rolling precipitation calculations
- compare feature timestamps with event timestamps

#### 11. Leakage audit

- list every candidate feature
- classify it as known before departure, contemporaneous, or known only after the event
- reject injuries, deaths, damage, narratives, event end time, and future-derived aggregates
- identify the reanalysis-versus-live-forecast limitation

#### 12. EDA conclusions and model decisions

The final notebook cell must answer:

1. Is the proposed label constructible?
2. Is the positive class large enough for the proposed temporal splits?
3. Which features are available consistently?
4. Which fields are excluded and why?
5. Which data-quality risks remain?
6. Does the team proceed, change scope, or stop?

### Required EDA figures

Export presentation-quality PNG or SVG files with stable names:

```text
outputs/figures/eda_events_by_year.png
outputs/figures/eda_event_type_counts.png
outputs/figures/eda_monthly_seasonality.png
outputs/figures/eda_county_choropleth.png
outputs/figures/eda_missingness.png
outputs/figures/eda_class_imbalance.png
outputs/figures/eda_precipitation_event_comparison.png
```

Every figure must include:

- descriptive title
- labeled axes and units
- readable legend if needed
- data-source note
- colorblind-safe colors
- adequate resolution for slides

### Required written report

Create `reports/eda/eda_findings.md` with:

- an executive summary of no more than 250 words
- a data-quality table
- the seven required figures or links to them
- decisions about label, geography, years, and features
- an unresolved-risk list
- signatures or GitHub handles of the two reviewers

### Notebook verification

`make eda` must execute the notebook from top to bottom in a clean kernel and fail on any exception. The notebook workflow must run against the small sample in CI. The full-data notebook can run manually in Codespaces and should be rerun whenever ingestion logic changes.

Verification checklist:

- [ ] Restart kernel and run all cells successfully.
- [ ] No hidden state or out-of-order execution counts.
- [ ] No hard-coded local paths.
- [ ] No unexplained warnings.
- [ ] Every exported figure exists.
- [ ] All displayed counts are reproducible from code.
- [ ] At least ten event records are manually spot-checked.
- [ ] County FIPS and timestamps are independently reviewed.
- [ ] The Econ/Stats major verifies interpretations and claims.
- [ ] The CS major verifies execution in a fresh Codespace.
- [ ] Mason records the final proceed/change/stop decision.

### Gate pull request

**Branch:** `eda/storm-events-profile`  
**PR title:** `eda: validate North Carolina flood-event target and features`  
**Squash commit:** `eda(storms): verify data quality and modeling feasibility`

The pull-request description must include:

- notebook run date
- source-data versions
- headline event and positive-window counts
- links to every exported figure
- reviewer checklist
- documented decisions or deviations

### Gate acceptance criteria

The team may continue only if:

- the label is reproducibly constructible;
- temporal and county fields pass checks;
- class imbalance is quantified;
- the proposed split contains positives in every relevant period;
- weather features can be aligned without using future information;
- limitations are documented; and
- two teammates approve the pull request.

If any condition fails, open a decision issue and modify the scope before building the model or app.

### Deliverable

A verified EDA notebook, seven reusable visuals, and a written evidence trail supporting the modeling plan.

---

## 10. Milestone 3 — Production data and feature pipeline

### Owner

Mason, with data-quality review from the Econ/Stats major.

### Create

- reusable transformations under `src/stormroute/data/` and `src/stormroute/features/`
- `scripts/fetch_weather.py`
- `scripts/build_county_windows.py`
- `configs/data.yaml`
- `notebooks/02_weather_feature_validation.ipynb`
- data-contract and leakage tests
- updated `docs/data_card.md`

### Required implementation

1. Normalize NOAA records and county identities.
2. Build all 100 county × six-hour windows for 2015–2024.
3. Create labels without using event outcomes as predictors.
4. Retrieve or load hourly weather consistently.
5. calculate rolling precipitation using only values available at or before the prediction timestamp;
6. add temporal and static terrain features;
7. assign immutable split labels by calendar year; and
8. write model-ready Parquet with deterministic column order and types.

### Required tests

- window boundaries at midnight and year-end
- events exactly on a six-hour boundary
- events spanning multiple windows
- no overlap of training, selection, calibration, and test periods
- rolling features never read future hours
- all 2024 observations remain excluded from fitting operations
- reasonable value ranges and missingness thresholds

### Pull requests and commits

```text
feat(data): build county-by-six-hour event labels
feat(features): add leakage-safe rolling weather features
test(data): enforce temporal split and feature contracts
docs(data): publish source, schema, and limitation card
```

### Acceptance criteria

- `make data` rebuilds the table from raw inputs.
- The schema matches the data contract.
- Row counts equal expected county-window counts after documented exclusions.
- A data-quality summary is written to `outputs/metrics/data_quality.json`.
- The weather-validation notebook executes successfully.
- EDA findings are updated if full production data changes an earlier conclusion.

### Deliverable

`data/processed/county_windows.parquet` plus tests, metadata, and a complete data card.

---

## 11. Milestone 4 — Baselines, model, calibration, and evaluation

### Owners

- Mason: modeling and calibration
- Econ/Stats major: independent evaluation and interpretation

### Create

- `src/stormroute/modeling/` modules
- `scripts/train_model.py`
- `scripts/evaluate_model.py`
- `configs/model.yaml`
- `notebooks/03_model_evaluation.ipynb`
- `outputs/metrics/model_comparison.json`
- final evaluation figures
- `artifacts/models/model_manifest.json`
- `docs/model_card.md`

### Required model sequence

1. Smoothed county-month climatology
2. Logistic regression
3. Monotonic gradient-boosted classifier
4. Sigmoid calibration using 2023 only
5. Final evaluation using untouched 2024 data

Do not tune against the 2024 test results.

### Required metrics

- PR-AUC
- Brier score
- log loss
- calibration curve
- recall at a fixed alert budget
- false-positive rate or precision at that budget
- bootstrap confidence intervals grouped by storm episode or month

ROC-AUC may appear in an appendix but must not be the headline result.

### Required comparisons

- climatology vs logistic regression vs boosted model
- raw vs calibrated boosted probabilities
- all 2024 vs the Helene period
- rural vs more populous counties
- model with and without county historical event-rate feature

### Required artifacts

```text
outputs/figures/model_precision_recall.png
outputs/figures/model_calibration.png
outputs/figures/model_comparison.png
outputs/figures/model_feature_importance.png
outputs/figures/model_helene_case_study.png
outputs/metrics/model_comparison.json
outputs/metrics/final_test_metrics.json
artifacts/models/stormroute_model.joblib
artifacts/models/model_manifest.json
```

The model manifest must record:

- model class and library version
- training, selection, calibration, and test dates
- features and monotonic constraints
- hyperparameters
- data-manifest version
- Git commit SHA
- evaluation metrics
- artifact checksum

### Pull requests and commits

```text
feat(model): establish climatology and logistic baselines
feat(model): train monotonic flood-hazard classifier
feat(model): calibrate probabilities on 2023 holdout
test(model): validate artifact schema and deterministic inference
docs(model): report 2024 evaluation and limitations
```

### Acceptance criteria

- The boosted model provides a defensible improvement over climatology.
- Calibration improves or does not materially worsen Brier score.
- Probability outputs are finite and within `[0, 1]`.
- Monotonicity spot checks pass for constrained rainfall and soil features.
- The evaluation notebook can be reproduced from saved predictions.
- No result is described as crash risk.
- Test-period limitations are explicit.

### Deliverable

A versioned, calibrated model artifact with independent evaluation, presentation-ready plots, and a recruiter-readable model card.

---

## 12. Milestone 5 — Route processing, scoring, and recommendations

### Owners

- CS major: route geometry and county joins
- Mason: risk aggregation and recommendations

### Create

- routing and scoring packages under `src/stormroute/`
- `configs/scoring.yaml`
- `configs/demo.yaml`
- `scripts/cache_demo.py`
- cached route and weather artifacts
- unit tests for every scoring rule
- `docs/risk_methodology.md`
- architecture decision records 0001–0003

### Required route behavior

- obtain at least two candidate routes
- sample routes every 5–10 km and at county boundaries
- calculate expected arrival time per sample
- spatially join samples to North Carolina counties
- collapse repeated samples in the same county-window
- cache the complete stage-demo route response

Use an all-North-Carolina primary demo route, such as Asheville to Charlotte. A route crossing Tennessee cannot be presented as fully covered by a North Carolina-only model.

### Required scoring behavior

For each unique interval:

```text
h_i = -ln(1 - clamp(p_i, 0, 0.999))
H_route = sum((segment_hours_i / 6) * h_i)
R_data = 1 - exp(-H_route)
R_trip = max(R_data, highest_official_alert_floor)
safety_score = round(100 * (1 - R_trip))
```

The recommendation engine must compare:

- candidate routes
- departure times in two-hour increments over the next 12 hours
- score improvement
- additional travel time
- official-alert implications

Recommend a change only when it improves the score by at least five points. If no acceptable alternative exists, display a clear `No safer option found` result and direct the traveler to official guidance.

### Critical tests

- zero risk produces score 100
- increasing segment probability cannot improve the score
- increasing time in a risky interval cannot improve the score
- splitting an identical interval into smaller pieces does not change the result
- a warning or emergency raises risk to its policy floor
- an official alert can never improve a score
- the current trip is never recommended as its own alternative
- score deltas equal the difference between displayed scores

### Pull requests and commits

```text
feat(geo): sample routes and assign county arrival windows
feat(scoring): add cumulative-hazard route aggregation
feat(scoring): enforce official NWS alert floors
feat(recommend): rank route and departure counterfactuals
test(scoring): verify invariants and recommendation thresholds
```

### Acceptance criteria

- One cached trip returns a score, weakest segment, explanation, and ranked alternatives.
- Every displayed score is reproducible from saved input probabilities.
- The recommended alternative reports both score improvement and travel-time cost.
- Methodology documentation matches the code exactly.

### Deliverable

A fully tested Python scoring engine and one stable offline demonstration scenario.

---

## 13. Milestone 6 — FastAPI service

### Owners

Mason and the CS major.

### Required endpoints

```text
GET  /health
GET  /api/v1/scenarios
GET  /api/v1/scenarios/{scenario_id}
POST /api/v1/trips/score
GET  /api/v1/methodology
```

### Score request

```json
{
  "origin": {"label": "Asheville, NC", "lat": 35.5951, "lon": -82.5515},
  "destination": {"label": "Charlotte, NC", "lat": 35.2271, "lon": -80.8431},
  "departure_time": "2024-09-27T12:00:00-04:00",
  "mode": "cached_replay"
}
```

### Score response requirements

- model and data version
- safety score and plain-language band
- modeled route risk before and after alert policy
- worst segment and expected arrival time
- primary contributing factors
- official alerts intersecting the route
- alternative routes and departure times
- recommendation with score delta and time cost
- confidence/coverage indicator
- warnings and limitations

### Engineering requirements

- Pydantic request and response models
- `/docs` OpenAPI page
- consistent error responses
- request timeout handling
- no secrets in responses or logs
- cached fallback for every stage-demo dependency
- structured logs with request IDs
- CORS limited to expected local/deployed frontend origins

### Pull requests and commits

```text
feat(api): expose versioned trip-scoring contract
feat(api): serve cached replay scenarios
test(api): cover scoring, validation, and fallback behavior
```

### Acceptance criteria

- Contract tests pass.
- Invalid coordinates and timestamps return helpful HTTP 422 errors.
- Cached demo mode works with network access disabled.
- A complete response is produced fast enough for a live demonstration.
- `/health` reports model and demo-artifact availability.

### Deliverable

A documented and tested API connecting the model, routing, weather, alerts, and frontend.

---

## 14. Milestone 7 — React website

### Owner

CS major, with product review from Mason and usability review from the Econ/Stats major.

### Required pages

#### Planner page

- origin
- destination
- departure date and time
- analyze-trip button
- concise safety disclaimer

#### Results page

- large Weather Safety Score
- plain-language score band
- route map colored by segment exposure
- worst segment and arrival time
- primary contributing weather factors
- official-alert banner
- recommended change
- exact before/after score and travel-time cost
- alternative options
- confidence and limitations

#### Methodology page

- data sources
- model and calibration summary
- score formula
- evaluation metrics
- social-good intent
- limitations and emergency disclaimer
- links to data card, model card, and GitHub repository

### Required product behavior

- use fixture JSON before API integration
- handle loading, empty, success, partial-data, and failure states
- work at common laptop and mobile widths
- support keyboard navigation
- never encode safety using color alone
- meet reasonable contrast standards
- show official guidance above model-generated recommendations when alerts exist

### Pull requests and commits

```text
feat(web): build trip planner and results layout
feat(web): visualize route risk and weakest segment
feat(web): compare recommended route and departure changes
feat(web): add methodology, confidence, and safety guidance
test(web): cover core scoring and recommendation views
```

### Acceptance criteria

- A first-time user can understand the result without explanation from the team.
- The current and recommended trips are visually comparable.
- The score is never shown without its meaning and limitations.
- The end-to-end demo works from the planner through the results page.
- The cached scenario continues working if external APIs fail.
- Automated accessibility and browser smoke tests pass.

### Deliverable

A polished, accessible website that turns the analysis into a useful traveler decision.

---

## 15. Milestone 8 — Responsible AI, final evaluation, and social-good evidence

### Owner

Econ/Stats major, reviewed by Mason.

### Create or finish

- `docs/responsible_ai.md`
- `docs/data_card.md`
- `docs/model_card.md`
- performance slice tables
- usability-test notes
- final statistical figures
- source and claim audit

### Required evaluations

- statewide performance
- rural versus more populous counties
- mountain, Piedmont, and coastal regions
- counties with sparse historical event reporting
- Helene and at least one non-hurricane event
- one high-rain period without a reported qualifying event

### Required responsible-AI statements

- No reported event does not prove safe road conditions.
- County resolution cannot identify whether a particular road is flooded.
- The model is not a crash predictor.
- Reanalysis evaluation is retrospective and differs from live forecast inputs.
- Recommendations never override road closures, evacuation orders, or NWS guidance.
- Demographic or vulnerability data do not change an individual trip score.

### Usability check

Ask at least three people who did not build the app to complete these tasks:

1. identify the trip score;
2. identify the riskiest segment;
3. explain the recommended action;
4. state the score improvement and time cost; and
5. find the official warning and limitation information.

Record misunderstandings and correct the interface before release.

### Pull requests and commits

```text
analysis(fairness): audit performance across NC county groups
docs(ai): document intended use and safety limitations
fix(web): clarify score meaning after usability review
```

### Acceptance criteria

- Every public claim has a source or corresponding metric.
- Slice results are shown even if they reveal weaknesses.
- The user interface clearly separates model evidence from official alerts.
- Three usability sessions are documented.

### Deliverable

A credible responsible-AI package and evidence that the product communicates risk safely.

---

## 16. Milestone 9 — Demo, documentation, and release

### Owners

- Mason: narrative and presentation
- CS major: demo reliability and deployment
- Econ/Stats major: DevPost text, citations, and claim checking

### Finish these files

#### `README.md`

Required sections:

1. one-sentence value proposition
2. product screenshot or short GIF
3. problem and social-good motivation
4. key capabilities
5. architecture diagram
6. data and model summary
7. evaluation results
8. local/Codespaces quick start
9. demo instructions
10. repository structure
11. limitations and safety statement
12. team roles
13. data citations and license

#### `docs/demo_runbook.md`

Include:

- exact click sequence
- expected scores and visible outputs
- which services must be running
- cached/offline fallback steps
- reset instructions
- owner of each recovery action

#### `docs/presentation_outline.md`

Plan the seven minutes:

```text
0:00–0:45  Human problem and social-good stakes
0:45–1:30  Data and why the score is needed
1:30–2:30  Model, calibration, and defensibility
2:30–4:30  Live traveler workflow and recommendation
4:30–5:30  Evaluation and comparison with baselines
5:30–6:20  Responsible AI and limitations
6:20–7:00  Impact, next steps, and closing
```

#### `docs/devpost_draft.md`

Include:

- inspiration
- what it does
- how it was built
- data sources
- technical challenges
- accomplishments
- lessons learned
- responsible-AI boundaries
- next steps
- repository and demo links

### Release checklist

- [ ] Clean clone succeeds in a fresh Codespace.
- [ ] `make setup`, `make test`, and `make verify` pass.
- [ ] The EDA notebook executes successfully.
- [ ] The final model and metrics match the model card.
- [ ] Demo assets are cached and checksummed.
- [ ] External APIs can fail without breaking the stage demo.
- [ ] No secret, private data, or local path is committed.
- [ ] All figures are legible on presentation slides.
- [ ] Source attribution is visible in the app and README.
- [ ] The repository has an OSI-compatible license chosen by the team.
- [ ] The final commit SHA is recorded in the DevPost draft.
- [ ] The team runs the seven-minute presentation at least three times.

### Final commits

```text
docs(readme): publish reproducible project overview
chore(demo): freeze verified competition scenario
docs(devpost): finalize submission narrative and citations
chore(release): prepare StormRoute v1.0 competition release
```

Create a GitHub release:

```text
Tag: v1.0.0-cdc2026
Title: StormRoute — Carolina Data Challenge 2026 Submission
```

Attach or link:

- final model manifest
- key metric file
- EDA findings report
- presentation PDF if permitted
- DevPost URL
- deployed demo URL

### Deliverable

A reproducible public release that can be evaluated in seven minutes and understood later by a technical recruiter.

---

## 17. Continuous integration requirements

### `.github/workflows/ci.yml`

Run on every pull request and push to `main`:

1. install locked Python dependencies;
2. run Ruff formatting and lint checks;
3. run Python type checks where configured;
4. run Python unit tests with coverage;
5. install frontend dependencies with `npm ci`;
6. run TypeScript checks;
7. run frontend unit tests;
8. build the production frontend; and
9. scan tracked files for obvious secrets or forbidden data paths.

### `.github/workflows/notebook.yml`

Run when notebooks, sample data, ingestion modules, or notebook dependencies change:

1. create a clean environment;
2. execute `01_storm_events_eda.ipynb` using sample mode;
3. execute later notebooks when they exist;
4. fail on exceptions; and
5. upload executed notebooks and figures as workflow artifacts.

The full dataset does not belong in CI. CI proves that the notebooks are executable; the full-data verification is recorded in the EDA pull request and reports.

### Minimum testing targets

- near-total coverage for scoring formulas and alert policy
- direct tests for every leakage rule
- direct tests for API contracts
- component tests for score and recommendation displays
- one end-to-end cached demo flow

Do not chase an arbitrary overall coverage percentage while critical safety logic remains untested.

---

## 18. Team ownership and pull-request review map

| Workstream | Primary owner | Required reviewer | Evidence |
|---|---|---|---|
| Repository/Codespaces | CS major | Mason | Fresh Codespace run |
| NOAA ingestion | Mason | Econ/Stats | QA table and unit tests |
| EDA notebook | Mason + Econ/Stats | CS major | Clean execution and figures |
| County-window pipeline | Mason | Econ/Stats | Schema and leakage tests |
| Model and calibration | Mason | Econ/Stats | Evaluation notebook and model card |
| Routing/geospatial | CS major | Mason | Route map and spatial spot checks |
| Scoring/recommendations | Mason | CS major | Invariant tests and cached output |
| FastAPI | CS major + Mason | Econ/Stats | OpenAPI and contract test |
| React website | CS major | Mason | End-to-end demo |
| Statistical evaluation | Econ/Stats | Mason | Reproducible metric files |
| Responsible AI | Econ/Stats | Mason | Claim audit |
| DevPost/presentation | All | All | Timed rehearsal |

### Beginner-friendly Econ/Stats assignments

Each assignment should have a prepared input file, expected output format, and reviewer:

- event counts by year, month, county, and type
- missingness and data-quality table
- independent climatology calculation
- metrics calculated from exported prediction files
- calibration and precision-recall charts
- rural/urban and regional performance comparisons
- data card, citations, limitations, and DevPost drafting
- three structured usability tests

Do not assign this teammate the repository bootstrap, deployment debugging, external API integration, or unbounded model tuning.

---

## 19. Pull-request definition of done

A pull request is ready to merge only when:

- its issue and acceptance criteria are linked;
- it contains one coherent outcome;
- new code includes appropriate tests;
- data or model changes include updated documentation;
- generated outputs are reproducible;
- notebook cells execute in order;
- CI passes;
- no secrets, raw data, or personal paths are present;
- screenshots or metric evidence are attached when behavior is visual or analytical;
- a non-author teammate has reviewed it; and
- the branch has no unresolved conversations.

Use this pull-request summary format:

```text
## Outcome
What now works or what was learned.

## Evidence
Tests, figures, screenshots, or metrics.

## Data/model impact
Schemas, source versions, splits, or artifacts changed.

## Risks and limitations
Known gaps and follow-up issues.

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No secrets or raw data committed
- [ ] Acceptance criteria met
```

---

## 20. Recommended issue sequence

Create these issues immediately and attach them to milestones:

1. Scaffold Codespaces repository
2. Add NOAA source manifest and downloader
3. Add North Carolina county boundaries
4. Create sample data fixtures
5. Build and execute Storm Events EDA notebook
6. Review and approve EDA gate
7. Fetch historical hourly weather
8. Build county × six-hour labels
9. Add rolling weather features and leakage tests
10. Train climatology baseline
11. Train logistic-regression baseline
12. Train monotonic boosted model
13. Calibrate and evaluate on temporal holdouts
14. Sample candidate routes and assign counties
15. Implement cumulative-hazard trip score
16. Add official-alert policy floors
17. Rank route and departure-time recommendations
18. Build FastAPI score endpoint
19. Build trip planner page
20. Build results map and explanation panels
21. Add cached Helene-era replay
22. Complete responsible-AI and subgroup audit
23. Conduct usability tests
24. Write README, DevPost, and presentation
25. Run final clean-Codespace verification
26. Tag the competition release

Issues 7–26 remain blocked until Issue 6, the EDA gate, is closed. Documentation drafting may proceed, but unsupported analytical claims may not be added.

---

## 21. What makes this repository internship-quality

The repository should make these capabilities visible without requiring a judge or recruiter to read every file:

- **Data science:** defensible target construction, imbalance-aware metrics, calibration, temporal validation, and explainability
- **AI engineering:** artifact versioning, inference contracts, monotonic constraints, and model-service integration
- **Software engineering:** modular packages, tests, CI, typed interfaces, code review, and reproducible environments
- **Data engineering:** versioned ingestion, immutable raw data, schemas, validation, and Parquet pipelines
- **Product thinking:** a real traveler decision, measurable counterfactual recommendation, and understandable trade-offs
- **Responsible AI:** careful claims, official-alert precedence, subgroup evaluation, and explicit limitations
- **Communication:** polished EDA, readable documentation, stable visuals, and a concise live demo

The final résumé bullet should be supported directly by repository evidence. A defensible example is:

> Built an explainable full-stack weather-risk platform using NOAA event data and hourly reanalysis; trained and calibrated a temporally validated gradient-boosted model, converted county-window probabilities into route-level exposure scores, and generated route/departure counterfactuals through FastAPI and React.

Do not include a performance percentage in the résumé bullet until the untouched 2024 evaluation is complete and documented.

---

## 22. Immediate first assignment

After Milestone 0 is merged, open Issue 2 and begin only the work required for the first notebook:

1. implement the NOAA 2015–2024 downloader;
2. filter North Carolina Flood, Flash Flood, and Debris Flow records;
3. validate identifiers and timestamps;
4. create a small tracked sample;
5. create `notebooks/01_storm_events_eda.ipynb`; and
6. complete the Milestone 2 verification checklist.

The team should not start model tuning, API endpoints, or final website implementation until that notebook is executed, reviewed, and merged.

