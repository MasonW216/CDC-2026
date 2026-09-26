# EDA Findings — North Carolina Flood-Event Target

> **Status: draft for the Milestone 2 gate.** Sections owned by Mason (1–5, 9–12) are
> complete. Sections 3 (missingness) and 6–8 belong to the Econ/Stats major, and the gate
> decision is pending. Every number here comes from a full-data run of
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
selection year has only 53, and yearly counts swing with single storms: Florence in 2018
had 295, Helene in 2024 had 272, and 2022 had 53.

Data quality is strong where it was tested. Event IDs are unique, every qualifying event is
county-coded, and parsed timestamps agree exactly with NOAA's own date-time text. Two issues
remain open. First, NOAA labels every North Carolina time `EST-5`, and 81.7% of events fall
in daylight-saving months, so a manual spot check must confirm these are really standard
time. Second, through Open-Meteo, ERA5-Land has no precipitation or wind. A combined product
supplies them from coarser ERA5 with complete coverage.

Trailing rainfall features read no future hours. Windows where an event began show far more
prior rainfall: a median of 23.0 mm over the previous 24 hours, against 0.1 mm otherwise.
The leakage audit found the configured feature list consistent.

**Draft recommendation:** proceed, once the team chooses the weather source and completes
the spot check and the remaining descriptive sections.

---

## Data-quality table

| Check | Requirement | Result | Pass |
|---|---|---|---|
| Unique `EVENT_ID` after cleaning | 0 duplicates | 0 duplicates in 639,467 rows | ☑ |
| Timestamps timezone-aware UTC | 100% | 100%; fixed offset from `CZ_TIMEZONE` | ☑ |
| Timestamps match NCEI's own date-time text | — | 2,220 of 2,220 begin and end times | ☑ |
| Daylight-saving handling | covered by tests | Fixed offset tested; whether `EST-5` holds in summer is **open** | ☐ |
| County FIPS preserve leading zeroes | 5-character strings, NC only | All 2,220 events validated | ☑ |
| Hazard filter exactly Flood / Flash Flood / Debris Flow | exact | Exact; 887 other water-related reports excluded | ☑ |
| Events with unresolved geography | counted and documented | 0: every qualifying event is county-coded | ☑ |
| Manually spot-checked records | ≥ 10 | Candidates selected; **checks not yet done** | ☐ |
| Weather coverage by county and year | reported | 3 representative points, 10 years, 100% (`era5_seamless`); all 100 counties in Milestone 3 | ◐ |
| Positive rate by year, month, county, event type | reported | By split, month, and county (section 9); by type below | ☑ |
| Damage strings parsed with unit tests | covered | `tests/data/test_noaa.py` | ☑ |
| Field missingness | reported | **Pending (Econ/Stats, section 3)** | ☐ |

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

| Figure | Owner | Status |
|---|---|---|
| [`eda_event_type_counts.png`](../../outputs/figures/eda_event_type_counts.png) | Mason | ☑ |
| [`eda_class_imbalance.png`](../../outputs/figures/eda_class_imbalance.png) | Mason | ☑ |
| [`eda_precipitation_event_comparison.png`](../../outputs/figures/eda_precipitation_event_comparison.png) | Mason | ☑ |
| `eda_events_by_year.png` | Econ/Stats | ☐ |
| `eda_monthly_seasonality.png` | Econ/Stats | ☐ |
| `eda_county_choropleth.png` | Econ/Stats (needs issue #3) | ☐ |
| `eda_missingness.png` | Econ/Stats | ☐ |

---

## Decisions

| Decision | Choice | Justification |
|---|---|---|
| Label | Onset rule: `window_start <= begin < window_end` | Build guide §2.1; [ADR 0001](../../docs/adr/0001-county-six-hour-target.md). Overlap would add 1,662 ongoing windows but leave 17 events unlabeled |
| Hazards | Flood, Flash Flood, Debris Flow | [ADR 0000](../../docs/adr/0000-specification-precedence.md). Heavy Rain (411) excluded; **Coastal Flood (66) exclusion needs team confirmation** |
| Geography | County-coded events only | All 2,220 qualifying events are county-coded, so no zone-to-county crosswalk is needed |
| Years and splits | Train 2015–21 · select 2022 · calibrate 2023 · test 2024 | Every split has positives; selection is thin (53) |
| Features accepted | 15 configured, plus `historical_event_rate` conditional | Leakage audit, section 11 |
| Features rejected | 10 candidate groups | See the leakage audit below |
| Weather source | **Open: team decision** | Via Open-Meteo, ERA5-Land lacks precipitation and wind; `era5_seamless` fills them from ERA5 (~28 km) while temperature and soil moisture stay ERA5-Land (~9 km). Alternative: ERA5-Land precipitation directly from Copernicus (account and API key) |

## Leakage audit

| Candidate | Availability | Decision |
|---|---|---|
| Trailing precipitation sums (1–72 h), trailing 6 h max intensity | Known before departure | Keep: perturbation test passes |
| Temperature, wind, gusts, soil moisture at window start | Known before departure | Keep |
| Elevation, slope | Known before departure (static) | Keep |
| Month encodings | Known before departure | Keep |
| `historical_event_rate` | Known before departure if fit on 2015–2021 | Conditional; may encode reporting bias |
| Rain during the window; other NOAA reports in the window | Contemporaneous | Reject |
| Centred or whole-period aggregates | Future-derived | Reject |
| Injuries, deaths, damage, narratives, end time, duration, episode ID, magnitude, flood cause, source | Known only after the event | Reject |
| Social Vulnerability Index | Known before departure | Reject by policy |

The remaining risk is **train-serve skew**, not leakage. Features come from reanalysis, which
a live deployment would not have, so evaluated performance is an upper bound
([ADR 0003](../../docs/adr/0003-reanalysis-live-forecast-boundary.md)).

---

## Unresolved risks

1. **Summer timestamps.** 1,813 events (81.7%) begin in daylight-saving months. If NOAA's
   `EST-5` is really clock time, they are one hour late in UTC. The spot check of
   [`spot_check_candidates.csv`](spot_check_candidates.csv) settles it.
2. **Weather source and resolution.** A team decision; see above.
3. **Thin, storm-driven splits.** Selection has 53 positives, and single storms dominate
   2018, 2020, and 2024. Model selection on 2022 will be noisy, so Milestone 4 must report
   grouped bootstrap intervals.
4. **Reporting bias.** Urban Wake County has the most positive windows (76); remote,
   mountainous Graham County has none in ten years. A negative label means *no report*, not
   *no hazard*. The Econ/Stats geography section should examine this.
5. **Weather checked at 3 points.** These are city coordinates, not county centroids. All 100
   counties come in Milestone 3, after the boundaries land (issue #3).
6. **Terrain features unchecked** until the boundaries and elevation data exist.
7. **UTC year boundary.** Events from the evening of 31 December 2014, in the 2014 file (not
   downloaded), would begin on 1 January 2015 in UTC. The effect is a few hours of data.
8. **Pending descriptive sections** (3 missingness, 6–8) could still surface a reporting
   break that affects the splits.

---

## Gate decision

**☐ Proceed ☐ Change scope ☐ Stop**

_TBD: recorded by Mason after both reviews._ Draft recommendation: **proceed**, conditional
on the weather-source decision, the spot check, the Coastal Flood decision, and the
Econ/Stats sections.

| Role | GitHub handle | Date |
|---|---|---|
| Decision (Product and AI lead) | _TBD_ | |
| Reviewer: interpretations and claims (Econ/Stats) | _TBD_ | |
| Reviewer: fresh-Codespace execution (CS) | _TBD_ | |
