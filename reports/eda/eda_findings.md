# EDA Findings — North Carolina Flood-Event Target

> **Status: draft for the Milestone 2 gate.** All notebook sections are now implemented:
> Mason's (1–5, 9–12) and Cameron's (3's missingness block and 6–8). Cameron's sections still
> need a second person's review, and the gate decision is pending. Every number here comes from a full-data run of
> [`01_storm_events_eda.ipynb`](../../notebooks/01_storm_events_eda.ipynb). If a number here
> and the notebook ever disagree, the notebook is right and this file is stale.

| | |
|---|---|
| Notebook run date | 2026-09-26 |
| Data mode | `full` |
| Storm Events files | 10 NCEI details files, 2015–2024; resolved filenames and SHA-256 in the download record and notebook section 2 |
| Weather sample | Open-Meteo archive API, `era5_seamless` 2014-12-29 to 2024-12-31 and `era5_land` 2024, accessed 2026-09-26 |
| Git commit of results | `229b91c` (sections 1–11) |

---

## Executive summary

StormRoute's label is a reported Flood, Flash Flood, or Debris Flow event beginning in a
North Carolina county during a six-hour window, and NOAA Storm Events data can build it.
Across 2015–2024, 2,220 qualifying events produce 1,499 positive windows out of 1,461,200
(0.103%, about 1 in 974). Every temporal split contains positives. However, the 2022
selection year has only 53 positives and calibration has 78. The 295 positives in 2018
and 272 in 2024 are whole-year totals, not counts attributable to Florence or Helene.
Episode concentration must be measured separately before attributing annual variation.

Data quality is strong where it was tested. Event IDs are unique, every qualifying event is
county-coded, and parsed timestamps agree exactly with NOAA's own date-time text. NOAA labels
every North Carolina time `EST-5`, including the 81.7% of events in daylight-saving months;
NWS policy requires standard time year-round, so the conversion is correct, and a manual spot
check will confirm preparers complied. Through Open-Meteo, ERA5-Land lacks precipitation and
wind, so Milestone 3 will fetch ERA5-Land directly from Copernicus.

In the three-point weather sample, positive windows have median trailing 24-hour rainfall
of 23.0 mm versus 0.1 mm for negatives. This alignment check is not a statewide estimate
or model evaluation. Trailing valid times do not establish that reanalysis was published
before departure; the notebook's two leakage audits still need reconciliation.

**Review recommendation: change scope** to a retrospective reported-event feasibility
experiment until feature availability and evaluation evidence support broader claims.
The team gate remains open; this recommendation is not Mason's decision.

---

## Data-quality table

| Check | Requirement | Result | Pass |
|---|---|---|---|
| Unique `EVENT_ID` after cleaning | 0 duplicates | 0 duplicates in 639,467 rows | ☑ |
| Timestamps timezone-aware UTC | 100% | 100%; fixed offset from `CZ_TIMEZONE` | ☑ |
| Timestamps match NCEI's own date-time text | — | 2,220 of 2,220 begin and end times | ☑ |
| Daylight-saving handling | covered by tests | Fixed offset tested; standard time year-round is NWS policy (NWSI 10-1605 §2.3); compliance spot check pending | ◐ |
| County FIPS preserve leading zeroes | 5-character strings, NC only | All 2,220 events validated | ☑ |
| Hazard filter exactly Flood / Flash Flood / Debris Flow | exact | Exact; 887 other water-related reports excluded | ☑ |
| Events with unresolved geography | counted and documented | 0: every qualifying event is county-coded | ☑ |
| Manually spot-checked records | ≥ 10 | Candidates selected; **checks not yet done** | ☐ |
| Weather coverage by county and year | reported | 3 representative points, 10 years, 100% (`era5_seamless`); all 100 counties in Milestone 3 | ◐ |
| Positive rate by year, month, county, event type | reported | By split, month, and county (section 9); by type below | ☑ |
| Damage strings parsed with unit tests | covered | `tests/data/test_noaa.py` | ☑ |
| Field missingness | reported | Delivered (Cameron, notebook section 3); awaiting second-person review | ◐ |

---

## Headline counts

| Quantity | Value |
|---|---|
| NOAA records, all states, 2015–2024 | 639,467 |
| After North Carolina filter | 14,688 |
| After hazard filter | 2,220 (Flash Flood 1,665 · Flood 535 · Debris Flow 20) |
| Excluded for unresolved geography | 0 |
| Excluded for invalid timestamps | 0 |
| Zero-duration events (end = begin) | 231 (10.4%); 17 exactly on a window boundary |
| County-windows generated | 1,461,200 (100 counties × 14,612 windows) |
| Positive county-windows | 1,499 (1.48 events per positive window; up to 11 in one) |
| Positive rate | 0.103% (about 1 in 974) |
| Positives: train / selection / calibration / test | 1,096 / 53 / 78 / 272 |
| Positive rate: train / selection / calibration / test | 0.107% / 0.036% / 0.053% / 0.186% |
| Counties with no positives | 1 (Graham) |

Positive windows by year: 2015 141 · 2016 167 · 2017 71 · 2018 295 · 2019 85 ·
2020 262 · 2021 75 · 2022 53 · 2023 78 · 2024 272.

---

## Figures

### Reproduced descriptive findings and denominators

The full run independently reproduces the section 3 and sections 6–8 deliverables.
Section numbering changed during integration: seasonality is in section 6,
geography in section 7, and reported impacts in section 8.

- **Missingness:** all 14,688 NC source rows, before hazard filtering or deduplication,
  are the denominator for each of 25 inspected fields. BEGIN_LAT and BEGIN_LON each
  have 3,729 missing values (25.39%); DAMAGE_PROPERTY has 1,626 (11.07%). The other
  22 inspected fields have none. Null, empty, and whitespace-only values are missing;
  zero is observed, and malformed nonblank values require separate validation.
  County codes can still locate a record without point coordinates. Unknown damage
  is not zero and is never a predictor. See `eda_missingness.png` below.
- **Time:** 2,220 unique retained qualifying reports are counted by UTC onset;
  none fall outside the configured UTC period. 2024 has 440 reports, 2020 has 399,
  and 2018 has 362. September has 465 reports pooled over ten years. Monthly totals
  are not adjusted for month length and do not measure independent storm frequency.
  Annual files exist for all ten years, but 35 of 120 months have no retained reports;
  this does not establish either complete reporting or an interruption in reporting.
  See `eda_events_by_year.png` and `eda_monthly_seasonality.png` below.
- **Geography:** the inventory contains all 100 counties and 1,000 county-years;
  426 county-years have zero reports. Graham has zero reports over the study period;
  Washington and Tyrrell each have one, Pamlico three. Wake has 156 reports, New
  Hanover 90, and Brunswick 87. These are event counts, not positive windows.
  The map divides counts by ten study years and Census land area in units of
  1,000 km². Neither this normalization nor a zero count proves low hazard.
  Reporting access, county size, and physical hazard vary together; these data
  alone cannot identify which explains the differences. See `eda_county_choropleth.png`.

### Independent split and episode check

Section 6 reconstructs timestamps from the published date-time text and integer-hour
bins, independently of section 9's grid membership method. Both methods agree for
all splits. This checks the retained IDs, not the truth of NOAA reports or all
ingestion exclusions. Full source hashes and annual episode results are in
[`eda_split_episode_review.json`](../../outputs/metrics/eda_split_episode_review.json).

| Split | County-windows | Positive windows | Prevalence | Distinct reported episodes |
|---|---:|---:|---:|---:|
| Train, 2015–2021 | 1,022,800 | 1,096 | 0.10716% | 354 |
| Selection, 2022 | 146,000 | 53 | 0.03630% | 28 |
| Calibration, 2023 | 146,000 | 78 | 0.05342% | 49 |
| Test, 2024 | 146,400 | 272 | 0.18579% | 71 |

One changed true-positive decision moves selection recall by 1/53 = 1.89 percentage
points, or calibration recall by 1/78 = 1.28 points. Positive windows are not
independent trials. The largest episode by report count contributes 46/362 reports
in 2018 (12.71%), 65/399 in 2020 (16.29%), and 56/440 in 2024 (12.73%). Its positive
windows represent 46/295, 30/262, and 52/272 of the respective yearly positives.
These figures do not establish named-storm dominance: a storm can span episodes.
The exploratory September 25–29, 2024 UTC window contains 89/440 reports (20.23%);
date membership is not causal attribution to Helene.

No model or threshold was selected from these summaries. The 2024 labels have been
inspected descriptively, so 2024 is not an unseen-label dataset; reserve its model
performance for one frozen final evaluation. Predefine storm/episode groups and
negative-window time blocks before fitting models. Grouped uncertainty must include
negative windows and cannot pretend distinct episodes are necessarily independent.

| Figure | Owner | Status |
|---|---|---|
| [`eda_event_type_counts.png`](../../outputs/figures/eda_event_type_counts.png) | Mason | ☑ |
| [`eda_class_imbalance.png`](../../outputs/figures/eda_class_imbalance.png) | Mason | ☑ |
| [`eda_precipitation_event_comparison.png`](../../outputs/figures/eda_precipitation_event_comparison.png) | Mason | ☑ |
| [`eda_events_by_year.png`](../../outputs/figures/eda_events_by_year.png) | Cameron | ☑ |
| [`eda_monthly_seasonality.png`](../../outputs/figures/eda_monthly_seasonality.png) | Cameron | ☑ |
| [`eda_county_choropleth.png`](../../outputs/figures/eda_county_choropleth.png) | Cameron | ☑ |
| [`eda_missingness.png`](../../outputs/figures/eda_missingness.png) | Cameron | ☑ |

Cameron also produced extra figures (durations, reporting coverage, Helene comparison, reported
impacts, and a one-year label check, `eda_class_imbalance_2020.png`); see their reviews in this folder.

---

## Decisions

| Decision | Choice | Justification |
|---|---|---|
| Label | Onset rule: `window_start <= begin < window_end` | Build guide §2.1; [ADR 0001](../../docs/adr/0001-county-six-hour-target.md). Overlap would add 1,662 ongoing windows but leave 17 events unlabeled |
| Hazards | Flood, Flash Flood, Debris Flow | [ADR 0000](../../docs/adr/0000-specification-precedence.md). Heavy Rain (411) excluded. Coastal Flood (66) excluded by decision on 2026-09-26: tides and surge drive it, which rainfall and soil features cannot explain, and NWS reports it by zone. Official Coastal Flood Warnings still raise trip risk through the alert floor |
| Geography | County-coded events only | All 2,220 qualifying events are county-coded, so no zone-to-county crosswalk is needed |
| Years and splits | Train 2015–21 · select 2022 · calibrate 2023 · test 2024 | Every split has positives; selection is thin (53) |
| Features accepted | 15 configured, plus `historical_event_rate` conditional | Leakage audit, section 11 |
| Features rejected | 10 candidate groups | See the leakage audit below |
| Weather source | ERA5-Land from the Copernicus Climate Data Store; gusts from ERA5 (decided 2026-09-26) | Via Open-Meteo, ERA5-Land lacks precipitation and wind, and `era5_seamless` would supply them from ERA5 (~28 km). Fetching directly keeps rainfall on the ~9 km grid, which matters most in the mountains. ERA5-Land has no gust variable. **Retrieval method** (CDS point time series at each county's internal point) is [ADR 0005](../../docs/adr/0005-weather-provider-era5-land-timeseries-asos.md), proposed and awaiting approval |
| Hazard scope | Flooding only for this gate | Phase 1 of [ADR 0004](../../docs/adr/0004-multi-hazard-scope.md): winter and wind/severe are not modeled until the flood model passes Milestone 4 |

## Leakage audit

| Candidate | Availability | Decision |
|---|---|---|
| Trailing precipitation sums (1–72 h), trailing 6 h max intensity | Historical valid times; reanalysis published retrospectively | Conditional for retrospective work; the perturbation test does not establish live availability |
| Temperature, wind, gusts, soil moisture at window start | Historical valid times; issue/publication time unverified | Conditional for retrospective work; verify hourly support and forecast issue times for live use |
| Elevation, slope | Known before departure (static) | Keep |
| Month encodings | Known before departure | Keep |
| `historical_event_rate` | Only previously published reports available at each training timestamp | Conditional; use past-only training estimates, train-only smoothing, then freeze for later splits; may encode reporting bias |
| Rain during the window; other NOAA reports in the window | Contemporaneous | Reject |
| Centred or whole-period aggregates | Future-derived | Reject |
| Injuries, deaths, damage, narratives, end time, duration, episode ID, magnitude, flood cause, source | Known only after the event | Reject |
| Social Vulnerability Index | Known before departure | Reject by policy |

Both availability leakage and train-serve skew need explicit checks. Reanalysis is not
available at the historical decision time. The retrospective experiment is permissible
under [ADR 0003](../../docs/adr/0003-reanalysis-live-forecast-boundary.md), but cannot establish
live forecast accuracy. A full-training-period county event rate also leaks future labels
into earlier training rows unless constructed out of time.

---

## Unresolved risks

1. **Standard-time compliance.** [NWS Instruction 10-1605](https://www.weather.gov/media/directives/010_pdfs/pd01016005curr.pdf)
   §2.3 requires local standard time "throughout the year" (the 2007 version says the same),
   so `EST-5` is correct by policy. Only 13 narratives quote a zoned time, too few to test
   compliance, and none shows clock time entered as the start. The spot check of
   [`spot_check_candidates.csv`](spot_check_candidates.csv) remains uncompleted. Checking
   ten candidates cannot establish compliance for all 1,813 daylight-saving-month events
   (81.7%); it can detect specific discrepancies.
2. **Weather retrieval not yet reproducible in the repo.** ADR 0005 awaits approval, and its
   county time series were retrieved by a prototype outside the repo. Milestone 3 must port
   that into `scripts/fetch_weather.py` so `make download` reproduces it.
3. **Thin, dependent splits.** Selection has 53 positives and calibration 78. Nonzero
   counts do not establish adequate power. Measure episode concentration rather than
   inferring named-storm dominance from annual totals; uncertainty must respect dependence.
4. **Reporting bias.** Urban Wake County has the most positive windows (76); remote,
   mountainous Graham County has none in ten years. A negative label means *no report*, not
   *no hazard*. The Econ/Stats geography section should examine this.
5. **Weather checked at 3 points, and a point is not a county.** The EDA used city
   coordinates. ADR 0005 uses one ERA5-Land cell per county, which under-represents large or
   mountainous counties; its own consequences section says so.
6. **Terrain features unchecked.** County boundaries have landed, but no elevation data
   (USGS 3DEP) has been retrieved yet.
7. **UTC year boundary.** Events from the evening of 31 December 2014, in the 2014 file (not
   downloaded), would begin on 1 January 2015 in UTC. The effect is a few hours of data.
8. **Cameron's sections need a second reader.** Sections 3 (missingness) and 6–8 are in, but
   nobody besides their author has checked their interpretations for a reporting break that
   would affect the splits. Cameron's independent event counts and 2020 label check do match
   this report exactly (2,220 events; 262 positive windows from 399 events in 2020).

---

## Gate decision

**☐ Proceed ☐ Change scope ☐ Stop**

_TBD: recorded by Mason after both reviews._ The independent review recommends **change
scope** to retrospective feasibility and requests fixes before gate approval; see
[`cameron_gate_review.md`](cameron_gate_review.md). This does not change the locked label
or split years. The weather source and Coastal Flood were decided on 2026-09-26.

| Role | GitHub handle | Date |
|---|---|---|
| Decision (Product and AI lead) | _TBD_ | |
| Reviewer: interpretations and claims (Econ/Stats) | _TBD_ | |
| Reviewer: fresh-Codespace execution (CS) | _TBD_ | |
