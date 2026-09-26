# StormRoute

## Full-Stack Explainable AI for Weather-Aware Travel Safety

**Project type:** Carolina Data Challenge 2026 - Natural Science Track  
**Theme:** AI for Social Good  
**Team size:** 3  
**Submission:** Code, visualizations, files, and DevPost entry  
**Presentation:** 7 minutes plus 2 minutes of Q&A  
**Document status:** Authoritative project assignment and delivery specification

---

## 1. Project Summary

StormRoute is a public-facing website that assigns a **0-100 Weather Safety Score** to a proposed road trip, identifies the route segment contributing the most weather exposure, and recommends concrete changes the traveler can make to improve the score.

For each request, StormRoute evaluates alternate routes and departure times. It then explains the safest practical change in terms a traveler can act on:

> **Leave four hours later: 54 → 81 (+27).** This avoids the peak modeled flood-hazard window in Haywood County without increasing drive time.

The initial system is limited to flood-related hazards in North Carolina. It is a decision-support prototype, not a navigation system, crash predictor, or guarantee of safety.

### 1.1 Social-good objective

The purpose of StormRoute is to help travelers reduce their exposure to severe weather before beginning a trip. The project converts technical weather information into three understandable outputs:

1. A trip-level Weather Safety Score
2. A clear explanation of the most concerning route segment
3. A specific route or departure-time recommendation

Official weather warnings, road closures, and emergency instructions always override StormRoute.

### 1.2 Technical objective

The project must demonstrate an end-to-end data-science and software-engineering workflow:

- multi-source data ingestion
- temporal and geospatial feature engineering
- rare-event classification
- probability calibration
- leakage-resistant evaluation
- route-time alignment
- counterfactual optimization
- explainable AI
- API design
- full-stack web development
- testing, caching, deployment, and documentation

---

## 2. Team and Ownership

### 2.1 Mason - Product and AI lead

Mason owns the project scope, machine-learning pipeline, score definition, recommendation algorithm, backend integration, and final narrative.

Primary responsibilities:

- define labels, features, splits, and leakage rules
- implement baseline and final models
- calibrate probabilities
- implement segment and trip scoring
- implement counterfactual recommendation ranking
- expose scoring through FastAPI with the CS lead
- integrate workstreams and lead the presentation

### 2.2 CS major - Geospatial and website lead

The CS major owns route processing, spatial joins, external service clients, the React website, caching, and demo reliability.

Primary responsibilities:

- obtain and cache route alternatives
- sample route geometry and calculate arrival times
- assign route samples to counties
- implement React/TypeScript user experience
- integrate the frontend with FastAPI
- implement NWS and routing clients
- create the production build and offline demo mode

### 2.3 Econ/Stats major - Evaluation and impact lead

The Econ/Stats major owns data-quality analysis, climatology verification, model evaluation, statistical visuals, social-impact framing, and submission documentation.

This is the teammate's first hackathon. Tasks must be bounded, testable, and attached to visible deliverables.

Primary responsibilities:

- audit data completeness and label prevalence
- independently verify the climatology baseline
- calculate evaluation metrics from exported predictions
- create calibration and precision-recall visuals
- compare performance across county groups
- draft the data card, limitations, DevPost impact sections, and citations
- conduct short usability tests using a prepared script

### 2.4 Decision authority

- Mason resolves scope and model decisions.
- The CS major resolves frontend and deployment decisions.
- The Econ/Stats major may block publication of an unsupported statistical claim.
- Any change to a shared data schema requires agreement from all three members.

---

## 3. Users and User Stories

### 3.1 Primary user

An everyday traveler deciding whether to change a route or departure time because of severe weather.

### 3.2 Secondary users

- evacuees comparing travel windows
- family members helping someone plan a trip
- community organizations communicating weather exposure
- transportation planners exploring historical patterns

### 3.3 Required user stories

**US-01:** As a traveler, I can enter an origin, destination, and departure time so that I can assess a proposed trip.

**US-02:** As a traveler, I can see a 0-100 Weather Safety Score and plain-language band so that I can understand the overall result.

**US-03:** As a traveler, I can see the most concerning route segment and expected arrival time so that I know where the modeled exposure occurs.

**US-04:** As a traveler, I can compare alternate routes and departure times so that I can improve the trip.

**US-05:** As a traveler, I can see the score improvement and time cost of every recommendation so that I can make an informed trade-off.

**US-06:** As a traveler, I can inspect the weather evidence and official alerts behind a segment score so that the recommendation is explainable.

**US-07:** As a traveler, I am clearly told when no acceptable option was found so that the system does not pressure me to proceed.

**US-08:** As a judge or recruiter, I can inspect the methodology, evaluation, and limitations so that I can assess the project's technical quality.

---

## 4. Scope

### 4.1 Required scope

- Geography: North Carolina, with a cached Asheville-to-Knoxville showcase route
- Hazards: Flood, Flash Flood, and Heavy Rain
- Prediction unit: county x six-hour window
- Historical period: 2015-2024
- Final holdout: calendar year 2024
- Website: React/TypeScript frontend and FastAPI backend
- Primary demo: cached Hurricane Helene replay
- Recommendations: alternate routes and two-hour departure increments over 12 hours

### 4.2 Out of scope

- nationwide routing
- crash-probability prediction
- exact road-flooding prediction
- personalized advice based on vehicle or driver characteristics
- authentication or user accounts
- crowdsourced reports or social-media data
- LLM-generated travel advice
- autonomous rerouting
- emergency dispatch
- a mobile application

### 4.3 Stretch scope

Stretch work begins only after all required acceptance tests pass:

1. second non-hurricane flood replay
2. live NWS forecast and alert mode
3. Social Vulnerability Index planner overlay
4. a second hazard family

---

## 5. System Architecture

```text
NOAA Storm Events ───────┐
                        ├─> Data pipeline ─> County-window feature table
Historical weather ─────┘                         │
                                                  v
                                   Train / calibrate / evaluate
                                                  │
                                                  v
                                           Model artifact
                                                  │
Routing service ─> Route geometry ────────────────┤
NWS service ─────> Forecasts and alerts ──────────┤
                                                  v
                                    FastAPI scoring service
                                                  │
                                                  v
                                  React/TypeScript website
```

### 5.1 Technology stack

**Data and modeling**

- Python
- Pandas or Polars
- GeoPandas and Shapely
- Scikit-learn
- Parquet for processed tables
- Joblib for the final model artifact

**Backend**

- FastAPI
- Pydantic
- HTTPX
- file-based JSON cache

**Frontend**

- React
- TypeScript
- Vite
- React Leaflet
- Recharts
- Tailwind CSS or a small custom CSS design system

**Testing**

- Pytest
- Vitest
- one end-to-end browser smoke test if time permits

### 5.2 Deployment model

The React frontend must compile to static files served by FastAPI. The final prototype therefore has one deployable service and one public URL.

The website must also support a cached replay mode that does not depend on external services during judging.

---

## 6. Data Specification

### 6.1 Required data sources

#### DS-01: NOAA Storm Events

Purpose:

- create flood-related labels
- identify event times and counties
- support impact and bias audits

Required files:

- event details
- event locations, where useful
- event fatalities for analysis only

Outcome fields such as damage, injuries, and deaths must not be used as predictors.

#### DS-02: Historical hourly weather

Preferred source: ERA5-Land or another documented hourly archive with consistent North Carolina coverage.

Required variables:

- precipitation
- temperature
- wind speed
- wind gust, if available
- soil-water or soil-moisture proxy, if reliably available

The selected provider and variable definitions must be recorded in the data card.

#### DS-03: County boundaries

Purpose:

- convert event and route locations to county FIPS
- display county context

The geographic vintage must be pinned and documented.

#### DS-04: Route geometry

Purpose:

- generate the primary and alternate routes
- obtain distance and expected travel duration

All showcase routes must be cached.

#### DS-05: NWS forecasts and alerts

Purpose:

- provide current or scenario weather evidence
- enforce conservative official-alert floors

Live access is a bonus. The primary replay must use saved responses or prepared scenario records.

### 6.2 Processed tables

#### `events.parquet`

```text
event_id: string
county_fips: string
begin_utc: timestamp
end_utc: timestamp
event_type: categorical
injuries: integer
deaths: integer
property_damage_usd: float
source_year: integer
```

#### `county_windows.parquet`

```text
county_fips: string
window_start_utc: timestamp
window_end_utc: timestamp
label_flood_event: boolean
precip_1h: float
precip_3h: float
precip_6h: float
precip_24h: float
antecedent_precip_3d: float
antecedent_precip_7d: float
temperature: float
wind_speed: float
wind_gust: float | null
soil_water: float | null
latitude: float
longitude: float
elevation: float | null
month_sin: float
month_cos: float
hour_sin: float
hour_cos: float
historical_event_rate: float
split: train | validation | test
```

#### `predictions_2024.parquet`

```text
county_fips: string
window_start_utc: timestamp
y_true: boolean
climatology_probability: float
logistic_probability: float
boosted_probability: float
final_calibrated_probability: float
```

#### `demo_routes.geojson`

```text
route_id: string
sample_order: integer
latitude: float
longitude: float
county_fips: string
cumulative_minutes: float
distance_km: float
geometry: Point | LineString
```

### 6.3 Label definition

A county-window is positive when at least one NOAA event meeting all of the following conditions overlaps it:

- event type is Flood, Flash Flood, or Heavy Rain
- event geography maps to the county
- event start is earlier than the window end
- event end is later than the window start

Formally:

```text
overlap = event_begin < window_end AND event_end > window_start
```

A negative label means **no qualifying reported event**. It does not mean safe weather.

### 6.4 Data-quality requirements

**DQ-01:** Event IDs are unique after cleaning.

**DQ-02:** All timestamps are stored in UTC internally.

**DQ-03:** Daylight-saving conversions are covered by tests.

**DQ-04:** Event overlaps are verified against at least ten hand-checked records.

**DQ-05:** Missing weather coverage is reported by county and year.

**DQ-06:** Positive rate is reported by year, month, county, and event type.

**DQ-07:** Records excluded because of unresolved geography are counted and documented.

**DQ-08:** Property-damage strings are parsed with unit tests, even though they are not model features.

---

## 7. Machine-Learning Specification

### 7.1 Prediction task

Predict the probability that a county will have a reported flood-related event during a six-hour window, conditional on location, season, and weather variables.

### 7.2 Temporal split

- Training: 2015-2022
- Validation, hyperparameter selection, and calibration: 2023
- Final test: 2024

No random train-test split is permitted for the final results.

No 2024 observation, transformation fit, calibration fit, or tuning result may affect training.

### 7.3 Models

#### M-01: Climatology baseline

Smoothed historical event rate by county and month.

Purpose: represent the performance available from place and season alone.

#### M-02: Logistic-regression baseline

Regularized logistic regression using the final feature set.

Purpose: provide an interpretable weather-informed baseline.

#### M-03: Gradient-boosted model

Gradient-boosted decision trees using the same time split.

Purpose: capture nonlinear precipitation, antecedent-condition, geography, and seasonal interactions.

#### M-04: Probability calibration

Calibrate the selected model using 2023 only. Isotonic regression or Platt scaling may be used. The selected method must be justified by validation-set calibration and sample size.

### 7.4 Feature rules

Allowed features:

- weather quantities
- lagged and accumulated precipitation
- season and time
- county coordinates and terrain context
- historical event rate calculated without future years

Prohibited features:

- damage amount
- injuries or fatalities
- event narrative
- event end time as an input
- any value created after the prediction window
- 2024 target-derived aggregates

### 7.5 Train-serve skew statement

If historical weather inputs are observations or reanalysis while live inputs are forecasts, the system has train-serve skew.

For the competition:

- the Helene replay must be labeled a retrospective weather-informed replay unless archived forecasts are used
- the model evaluation measures hazard classification under historical weather conditions, not complete real-time forecast accuracy
- production deployment would require training and testing on archived forecast fields issued before each prediction time

### 7.6 Required metrics

**Primary**

- PR-AUC
- Brier score
- calibration curve
- recall at a fixed alert budget, initially the top 1% of county-windows

**Secondary**

- ROC-AUC
- precision at the selected operating point
- event-level recall
- expected calibration error

Accuracy must not be used as the primary success metric.

### 7.7 Confidence intervals

Calculate 95% confidence intervals by resampling storm episodes or calendar months. Do not bootstrap individual county-window rows as if they were independent.

### 7.8 Model-selection rule

The final model must:

1. outperform climatology on PR-AUC or recall at the fixed alert budget
2. match or improve climatology on Brier score after calibration
3. pass the no-temporal-leakage test
4. produce stable results under reasonable feature and threshold sensitivity checks

If the boosted model does not meet these conditions, use calibrated logistic regression or climatology. The website must not imply that a more complex model is better without evidence.

---

## 8. Weather Safety Score

### 8.1 Segment risk

```text
segment_risk = max(
    calibrated_hazard_probability,
    official_alert_floor
)
```

Initial policy floors:

```text
No alert   0.00
Watch      0.35
Advisory   0.50
Warning    0.80
Emergency  0.98
```

These are product-policy values, not learned probabilities. Store them in configuration and report a sensitivity analysis.

### 8.2 Trip risk

```text
trip_risk =
    0.70 x maximum segment risk
  + 0.30 x time-weighted mean segment risk
```

### 8.3 Weather Safety Score

```text
weather_safety_score = round(100 x (1 - trip_risk))
```

The result is a comparative index, not a probability of avoiding a crash.

### 8.4 Bands

| Score | Band | Required response |
|---:|---|---|
| 85-100 | Lower modeled weather risk | Display ordinary cautions and official-alert status |
| 70-84 | Use caution | Explain main exposure and best available improvement |
| 50-69 | High caution | Lead with a safer route or departure time |
| 0-49 | Delay or avoid | Do not recommend proceeding; display official guidance |

The highest band must not be labeled “Safe.”

### 8.5 Score tests

- always between 0 and 100
- decreases or remains unchanged when an alert floor increases
- does not hide a short high-risk segment inside a long low-risk route
- produces the same output for the same versioned inputs
- exposes component values for explanation and debugging

---

## 9. Route and Recommendation Engine

### 9.1 Route processing

For every candidate route:

1. request geometry and travel duration
2. sample the path approximately every 5-10 km
3. calculate cumulative arrival time
4. map samples to county FIPS
5. map arrival times to six-hour prediction windows
6. attach model probability and official-alert floor
7. merge adjacent samples with equivalent risk context into display segments

### 9.2 Candidate generation

Evaluate:

- 2-3 candidate routes
- requested departure time
- departure +2, +4, +6, +8, +10, and +12 hours

Expected candidate count: 14-21 depending on route availability.

### 9.3 Recommendation ranking

Rank candidates on two objectives:

- maximize Weather Safety Score
- minimize waiting and additional travel time

Return the non-dominated Pareto frontier, then select no more than three user-facing recommendations:

1. largest score improvement
2. best low-cost improvement
3. official-warning action

### 9.4 Recommendation rules

- minimum displayed improvement: 5 points
- low-cost recommendation: no more than 30 added travel minutes or 2 hours of delay
- every recommendation includes old score, new score, delta, time cost, reduced exposure, and confidence
- recommendations never override an official closure, evacuation order, or warning
- if no meaningful improvement exists, return “No lower-exposure option found; delay the trip and follow official guidance.”

### 9.5 Recommendation acceptance test

Given a fixed scenario, the engine must produce an auditable table containing every candidate, score, time cost, dominant hazard, and selection status. A reviewer must be able to reproduce why a recommendation was chosen.

---

## 10. Backend API

### 10.1 `POST /api/trips/score`

Request:

```json
{
  "origin": {
    "label": "Asheville, NC",
    "lat": 35.5951,
    "lon": -82.5515
  },
  "destination": {
    "label": "Knoxville, TN",
    "lat": 35.9606,
    "lon": -83.9207
  },
  "departure_time": "2024-09-27T08:00:00-04:00",
  "mode": "replay"
}
```

Minimum response:

```json
{
  "trip_id": "helene-0800",
  "score": 54,
  "band": "High caution",
  "confidence": "Moderate",
  "primary_hazard": "Flash flood",
  "routes": [],
  "worst_segment": {},
  "recommendations": [],
  "official_guidance": [],
  "data_timestamp": "2024-09-27T12:00:00Z",
  "model_version": "stormroute-0.1"
}
```

### 10.2 `GET /api/demo/helene`

Returns the fully cached primary scenario without an external request.

### 10.3 `GET /api/method`

Returns model version, data sources, split dates, primary metrics, known limitations, and scoring-policy version.

### 10.4 `GET /api/health`

Returns backend status, model-load status, cache status, and data version.

### 10.5 API requirements

- Pydantic validation for all requests and responses
- explicit time-zone handling
- external request timeouts
- useful error messages
- structured logs without personal data
- model loaded once at startup
- cached fallback for the demo scenario

---

## 11. Website Requirements

### 11.1 Page 1 - Home

Required content:

- project name and social-good message
- origin and destination inputs
- departure time input
- “Calculate Weather Safety Score” action
- “Replay Hurricane Helene” action
- short score disclaimer

Primary headline:

> Safer decisions before the road.

### 11.2 Page 2 - Trip result

Required components:

- `SafetyScore`
- `RouteMap`
- `TripSummary`
- `RecommendationCard`
- `DepartureFrontier`
- `EvidencePanel`
- `OfficialGuidance`
- `DataStatus`

The initial viewport must show the score, map, worst segment, and at least one recommendation without requiring excessive scrolling.

### 11.3 Page 3 - Method and impact

Required content:

- model comparison
- calibration plot
- data-flow diagram
- route-time explanation
- social-good impact
- intended use and prohibited use
- known limitations
- team contributions

### 11.4 Required visualizations

1. segment-colored route map
2. Weather Safety Score versus departure time
3. calibration curve comparing final model with ideal calibration
4. local explanation for the worst segment

Every chart title must state its conclusion rather than only naming its variables.

### 11.5 Accessibility

- color is never the only hazard indicator
- risk states include icons and text labels
- keyboard-accessible controls
- readable contrast
- descriptive chart and map text
- no flashing or celebratory effects
- plain-language explanation for technical terms

### 11.6 Website reliability

- cached demo loads without internet
- errors do not produce a blank page
- every live result shows a data timestamp
- replay and live modes are visibly distinct
- presentation route opens directly to the cached demo
- website works at desktop presentation resolution and mobile width

---

## 12. Explainability and Responsible AI

### 12.1 Required explanations

**Global explanation**

- permutation feature importance
- a small number of partial-dependence plots

**Local explanation**

- calibrated probability
- alert status
- primary contributing features
- arrival time
- confidence and missing-data status

### 12.2 Required safety language

Use:

- “Weather Safety Score”
- “comparative decision index”
- “lower modeled weather risk”
- “reduce exposure”
- “based on available weather data”

Do not use:

- “guaranteed safe”
- “zero risk”
- “the safest route”
- “the model knows the road will flood”
- “probability of surviving the trip”

### 12.3 Model card requirements

- intended users
- intended decision
- data and date range
- model and calibration method
- metrics and confidence intervals
- prohibited uses
- reporting and geographic bias
- train-serve skew
- official-warning override
- human responsibility

### 12.4 Social vulnerability

Social Vulnerability Index data may appear only in an aggregate planner or impact analysis. It must not lower the score of trips through vulnerable communities or be used to reroute travelers away from them.

---

## 13. Testing Requirements

### 13.1 Data tests

- event interval overlap
- unique event IDs
- county FIPS format
- UTC conversion
- daylight-saving behavior
- damage parser
- missing-weather summaries
- split boundaries

### 13.2 Model tests

- no 2024 rows in training or calibration
- probabilities between 0 and 1
- deterministic predictions for a fixed artifact
- calibration transform fitted on validation only
- baseline and final metrics generated from identical test rows

### 13.3 Score tests

- score between 0 and 100
- alert floor monotonicity
- maximum-segment contribution
- configured weight sum equals 1
- recommendation minimum-delta rule
- no-good-option behavior

### 13.4 API tests

- valid replay request
- invalid coordinates
- invalid or ambiguous time zone
- missing model artifact
- external timeout with cached fallback
- response schema

### 13.5 Frontend tests

- score and band render correctly
- recommendation updates comparison state
- official warning remains visible
- API error displays a useful message
- replay/live label displays correctly

### 13.6 End-to-end acceptance test

Starting from the Helene replay button, a user must be able to:

1. load the original trip
2. see its score and route
3. inspect the worst segment
4. open the recommendations
5. apply a route or departure change
6. see the score, map, explanation, and time cost update together

---

## 14. Repository Requirements

```text
stormroute/
  README.md
  PROJECT_ASSIGNMENT.md
  pyproject.toml
  package.json
  configs/
    scoring.yaml
    hazards.yaml
    scenarios.yaml
  data/
    raw/                 # ignored
    interim/             # ignored
    processed/           # ignored
  ml/
    ingest_events.py
    build_windows.py
    weather_features.py
    train.py
    calibrate.py
    evaluate.py
    artifacts/
  api/
    main.py
    schemas.py
    services/
      scoring.py
      recommendations.py
      routing.py
      weather.py
      cache.py
  web/
    src/
      components/
      pages/
      api/
      styles/
  tests/
    data/
    model/
    api/
    scoring/
  outputs/
    figures/
    metrics/
    demo/
  docs/
    data_card.md
    model_card.md
    devpost.md
    pitch.md
```

### 14.1 README requirements

- problem and social-good purpose
- website screenshot or GIF
- architecture diagram
- data sources
- setup and run commands
- reproducibility instructions
- measured results
- limitations
- team contributions

---

## 15. Deliverables

### D-01: Project setup and contracts

**Owner:** Mason  
**Contributors:** all  
**Outputs:** repository, task board, schemas, branch conventions  
**Acceptance:** all teammates can describe the same scope and use the same schemas

### D-02: Verified event dataset

**Owner:** Econ/Stats major  
**Support:** Mason  
**Outputs:** `events.parquet`, QA report, event chart  
**Acceptance:** ten manually verified labels and documented exclusions

### D-03: County-window feature table

**Owner:** Mason  
**Outputs:** `county_windows.parquet`, build script, data tests  
**Acceptance:** all split and leakage tests pass

### D-04: Model comparison

**Owner:** Mason  
**Evaluation owner:** Econ/Stats major  
**Outputs:** trained models, predictions, metric table  
**Acceptance:** final-model rule in Section 7.8 is applied honestly

### D-05: Evaluation package

**Owner:** Econ/Stats major  
**Outputs:** PR curve, calibration plot, confidence intervals, subgroup audit  
**Acceptance:** every chart includes sample size, split, and conclusion title

### D-06: Route engine

**Owner:** CS major  
**Outputs:** cached routes, route sampler, county joins, arrival-time calculation  
**Acceptance:** ten route points manually spot-checked

### D-07: Safety score

**Owner:** Mason  
**Outputs:** versioned scoring config, score module, tests  
**Acceptance:** all Section 8.5 tests pass

### D-08: Recommendation engine

**Owner:** Mason  
**Support:** CS major  
**Outputs:** candidate table, Pareto ranking, recommendations  
**Acceptance:** recommendation choice is reproducible from exported candidates

### D-09: Backend API

**Owners:** Mason and CS major  
**Outputs:** FastAPI application and cached replay endpoints  
**Acceptance:** API test suite passes and demo works without external services

### D-10: Website

**Owner:** CS major  
**Content contributors:** Mason and Econ/Stats major  
**Outputs:** three pages and required components  
**Acceptance:** end-to-end test in Section 13.6 passes

### D-11: Responsible-AI documentation

**Owner:** Econ/Stats major  
**Review:** Mason  
**Outputs:** data card, model card, limitations, citations  
**Acceptance:** no unsupported safety or causal claim remains

### D-12: Submission package

**Owner:** Econ/Stats major  
**Contributors:** all  
**Outputs:** DevPost text, repository, GIF/video, four visuals  
**Acceptance:** every required link and file opens on the presentation laptop

### D-13: Presentation

**Owner:** Mason  
**Contributors:** all  
**Outputs:** seven-slide deck, cached demo, Q&A sheet  
**Acceptance:** two rehearsals finish between 6:30 and 6:40

---

## 16. Milestones and Gates

### Gate A - Feasibility

**Deadline:** approximately T+4 hours

Required proof:

- one route point
- one county FIPS
- one arrival time
- one six-hour window
- one verified NOAA label

If this join does not work, stop website and model expansion until fixed.

### Gate B - Model viability

**Deadline:** approximately T+8 hours

Required proof:

- climatology, logistic, and initial boosted predictions
- 2024 metric comparison
- one model probability attached to one route segment

If the boosted model does not beat climatology, continue with the simpler model and strengthen the product and evaluation.

### Gate C - Vertical slice

**Deadline:** approximately T+13 hours

Required proof:

- website loads cached trip
- score is calculated
- route is colored
- worst segment is explained
- one recommendation changes score and time

After Gate C, freeze new required features.

### Gate D - Submission candidate

**Deadline:** approximately T+20 hours

Required proof:

- all required tests pass
- DevPost draft complete
- README complete
- seven-slide deck complete
- cached demo and backup recording complete

Remaining time is reserved for rehearsal, clarity, and reliability.

---

## 17. Presentation Specification

### 17.1 Timing

| Time | Content | Owner |
|---|---|---|
| 0:00-0:45 | Traveler-safety problem | Mason |
| 0:45-1:20 | Space-time insight | Mason |
| 1:20-2:20 | Model and validation | Mason + Econ/Stats |
| 2:20-3:00 | Route and recommendation engine | CS major |
| 3:00-4:30 | Website demonstration | CS major |
| 4:30-5:40 | Evaluation, calibration, and limitations | Econ/Stats major |
| 5:40-6:30 | Social impact and next steps | Econ/Stats major |
| 6:30-7:00 | Close | Mason |

### 17.2 Required demonstration sequence

1. Load Helene replay.
2. Show original score and route.
3. Select the worst segment.
4. Explain the evidence.
5. Open recommendations.
6. Apply the best practical change.
7. Show score improvement and time cost.
8. End with official-guidance language.

### 17.3 Q&A preparation

Prepare answers to:

- Why is this an index rather than crash probability?
- How was temporal leakage prevented?
- Why PR-AUC and calibration?
- Why were these scoring weights selected?
- How does the recommendation optimizer work?
- What happens when every option is dangerous?
- What would be required for real deployment?

---

## 18. DevPost Specification

The DevPost entry must include:

1. Problem and affected users
2. Social-good purpose
3. What StormRoute does
4. How it was built
5. Model and baseline results
6. Website screenshots or GIF
7. Challenges and technical decisions
8. Responsible-AI limitations
9. Team contributions
10. Future work
11. Repository and live website links

The DevPost story should be skimmable. Technical depth belongs in linked documentation and the repository.

---

## 19. Risk Register

| Risk | Impact | Mitigation | Owner |
|---|---|---|---|
| Historical weather download is slow | Model blocked | Start with fewer years/counties; cache immediately | Mason |
| Route API unavailable | Demo blocked | Save GeoJSON at Gate A | CS major |
| NWS API unavailable | Live mode blocked | Cached replay is primary | CS major |
| Positive labels too sparse | Weak model | Combine three flood-related event types; use rare-event metrics | Mason |
| Boosted model does not beat baseline | AI claim weakened | Use calibrated simpler model and emphasize honest comparison | Mason |
| Reanalysis/forecast mismatch | Overclaiming | Label replay retrospective and document train-serve skew | Econ/Stats |
| Website integration delayed | Incomplete product | Use fixture JSON early; freeze at Gate C | CS major |
| First-time teammate becomes blocked | Lost capacity | Assign bounded outputs and 15-minute escalation rule | All |
| Live presentation failure | Lost judging impact | Cached mode, screenshots, and backup video | CS major |
| Scope expansion | Missed submission | Stretch work prohibited before minimum completion | Mason |

---

## 20. Definition of Done

StormRoute is complete only when all statements below are true.

### Data and model

- [ ] NOAA labels are reproducible.
- [ ] Weather features and exclusions are documented.
- [ ] Temporal leakage tests pass.
- [ ] The 2024 holdout remains untouched until final evaluation.
- [ ] Baseline and final model are evaluated on identical rows.
- [ ] Probabilities are calibrated and reported with appropriate metrics.

### Scoring and recommendations

- [ ] Score is always 0-100.
- [ ] Official alerts create conservative floors.
- [ ] Worst segment remains visible in trip aggregation.
- [ ] At least 14 route-time candidates are evaluated.
- [ ] Recommendations include score delta and time cost.
- [ ] “No acceptable option” behavior works.

### Website

- [ ] Home, result, and method pages are complete.
- [ ] Required four visualizations are present.
- [ ] Helene replay works without internet.
- [ ] Score, route, explanation, and recommendation update together.
- [ ] Errors and missing data are handled clearly.
- [ ] Accessibility requirements are satisfied.

### Documentation and submission

- [ ] README is reproducible.
- [ ] Data card and model card are complete.
- [ ] DevPost entry is complete.
- [ ] Team contributions are explicit.
- [ ] Code and final files are submitted.
- [ ] Seven-slide deck is complete.
- [ ] Two timed rehearsals are complete.
- [ ] Backup screenshots and video are available.

---

## 21. Final Product Statement

> StormRoute is a full-stack explainable-AI platform that protects travelers by converting severe-weather data into a trip-level Weather Safety Score, identifying the route segment creating the greatest concern, and recommending measurable route or departure-time changes that reduce modeled exposure.

The project succeeds when the traveler receives an understandable action, the judge can verify the evidence behind it, and the team can defend every technical and safety claim.