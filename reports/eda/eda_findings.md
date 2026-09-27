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
selection year has only 53, and yearly counts swing with single storms: Florence in 2018
had 295, Helene in 2024 had 272, and 2022 had 53.

Data quality is strong where it was tested. Event IDs are unique, every qualifying event is
county-coded, and parsed timestamps agree exactly with NOAA's own date-time text. NOAA labels
every North Carolina time `EST-5`, including the 81.7% of events in daylight-saving months;
NWS policy requires standard time year-round, so the conversion is correct, and a spot check
of ten events found no hour-off error: four summer and autumn events matched independent
local storm reports to the minute. Through Open-Meteo, ERA5-Land lacks precipitation and
wind, so Milestone 3 will fetch ERA5-Land directly from Copernicus.

Trailing rainfall features read no future hours. Windows where an event began show far more
prior rainfall: a median of 23.0 mm over the previous 24 hours, against 0.1 mm otherwise.
The leakage audit found the configured feature list consistent.

**Draft recommendation:** proceed, once the second-person reviews are complete.

---

## Data-quality table

| Check | Requirement | Result | Pass |
|---|---|---|---|
| Unique `EVENT_ID` after cleaning | 0 duplicates | 0 duplicates in 639,467 rows | ☑ |
| Timestamps timezone-aware UTC | 100% | 100%; fixed offset from `CZ_TIMEZONE` | ☑ |
| Timestamps match NCEI's own date-time text | — | 2,220 of 2,220 begin and end times | ☑ |
| Daylight-saving handling | covered by tests | Fixed offset tested; standard time year-round is NWS policy (NWSI 10-1605 §2.3); compliance spot check: 4 of 4 testable daylight-saving events matched to the minute (see Spot check) | ◐ |
| County FIPS preserve leading zeroes | 5-character strings, NC only | All 2,220 events validated | ☑ |
| Hazard filter exactly Flood / Flash Flood / Debris Flow | exact | Exact; 887 other water-related reports excluded | ☑ |
| Events with unresolved geography | counted and documented | 0: every qualifying event is county-coded | ☑ |
| Manually spot-checked records | ≥ 10 | 10 checked; 5 times confirmed, 2 not testable, 2 not verified, 1 inconclusive; **Mason to confirm** | ◐ |
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
a live deployment would not have, so retrospective results cannot establish live forecast
accuracy ([ADR 0003](../../docs/adr/0003-reanalysis-live-forecast-boundary.md)).

---

## Spot check

Ten events from [`spot_check_candidates.csv`](spot_check_candidates.csv), checked for county
and onset time against independent records: NWS local storm reports (LSRs) from the Iowa
Environmental Mesonet, and Census 2024 county boundaries. Three of them are summer events
(590930 June 2015, 904861 June 2020, 1197141 July 2024). The CSV records the event ID,
county, type, published and UTC onset, source, and notes for each. The first pass was done
by a Claude session, so it is marked `claude-precheck`; **Mason must confirm it** and put a
handle in the `reviewer` column before this item is ticked.

| Result | Events |
|---|---|
| Onset time matches an LSR to the minute | 590930, 904861, 1197141, 926146 (all in daylight-saving months); 610221 (December control) |
| Not testable: Flood entry is a hand-off from a Flash Flood entry | 663370, 663509 |
| Not verified: no independent report in the window | 666045, 787208 |
| Inconclusive: gauge-based, hour not settled | 1216934 |

- **Timezone.** Four events in June, July and October match LSRs exactly under the fixed
  `EST-5` offset. An hour-off error (clock time entered as daylight time) would show as a
  60-minute miss; none did.
- **County.** All ten `CZ_FIPS` match the named county. Eight reported points fall inside that
  county. Two fall just outside: 663509 by 440 m (in Nash, reported Edgecombe) and 787208 by
  2.7 km (in Duplin, reported Wayne). The pipeline uses `CZ_FIPS`, which NOAA records as
  the county-coded authority, so labels are unaffected.
- **Hand-off finding.** 663370 and 663509 begin exactly one minute after a Flash Flood entry
  in the same county ends, and 86 of 535 Flood events (16%) do. Their onset is a
  bookkeeping change, not a new flood. Under the onset rule, 62 positive windows (4.1% of
  1,499) exist only because of such a hand-off; 21 of them are in the 2024 test year. This
  does not change the gate decision: ADR 0001 fixes the label. Milestone 4 should report
  metrics with and without these windows.

---

## Unresolved risks

1. **Standard-time compliance.** [NWS Instruction 10-1605](https://www.weather.gov/media/directives/010_pdfs/pd01016005curr.pdf)
   §2.3 requires local standard time "throughout the year" (the 2007 version says the same),
   so `EST-5` is correct by policy. Only 13 narratives quote a zoned time, too few to test
   compliance. The [spot check](#spot-check) tested it on four daylight-saving events and found
   no hour-off error, but four of 1,813 events is a small sample, not proof of compliance.
2. **Weather retrieval not yet reproducible in the repo.** ADR 0005 awaits approval, and its
   county time series were retrieved by a prototype outside the repo. Milestone 3 must port
   that into `scripts/fetch_weather.py` so `make download` reproduces it.
3. **Thin, storm-driven splits.** Selection has 53 positives, and single storms dominate
   2018, 2020, and 2024. Model selection on 2022 will be noisy, so Milestone 4 must report
   grouped bootstrap intervals.
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

_TBD: recorded by Mason after both reviews._ Draft recommendation: **proceed**, conditional
on your confirmation of the spot check and the two second-person reviews. The weather source and Coastal Flood were
decided on 2026-09-26 (see Decisions).

| Role | GitHub handle | Date |
|---|---|---|
| Decision (Product and AI lead) | _TBD_ | |
| Reviewer: interpretations and claims (Econ/Stats) | _TBD_ | |
| Reviewer: fresh-Codespace execution (CS) | _TBD_ | |
