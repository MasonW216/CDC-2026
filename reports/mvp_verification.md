# Cameron's MVP verification sheet

Checked 27 September 2026 against the cached Helene inputs and provisional routes
on `Mason`. This is an **offline historical replay**, not an as-of-departure
forecast or a verified road-safety recommendation. The result JSON and self-contained
HTML fallback are reproducible; the React results screen and final rendered slide
deck are not yet available for sign-off.

**Verifier disposition:** use the static HTML only as a clearly labeled
historical-rule demonstration. Do not present either route as a lower-hazard
alternative or claim a live planner until the availability, route geometry, and
React integration gaps below are resolved.

## Inputs and route sequence

Departure is **27 September 2024, 12:00 EDT = 16:00 UTC**. Rainfall values are
**millimeters per hour ending at the stated UTC hour**. The input has 100 county
point series × 144 hourly timestamps (23 September 00:00 through 28 September
23:00 UTC), with no missing or negative values. The cached input's embedded
SHA-256 matches its compact JSON payload when the hash field is excluded.
All 15 route stretches have a
matching FIPS/name and nondecreasing arrival times. Repeated counties reflect a
new six-hour arrival window, not a second county crossing.

| Route | County stretches in fixture order; arrival UTC → six-hour window start UTC |
|---|---|
| `route_0`, 154.3 min | Buncombe `37021` 16:00→12:00; Henderson `37089` 16:19→12:00; Polk `37149` 16:40→12:00; Rutherford `37161` 17:03→12:00; Cleveland `37045` 17:21→12:00; Gaston `37071` 17:54→12:00 and 18:00→18:00; Mecklenburg `37119` 18:18→18:00. |
| `route_1`, 167.3 min | Buncombe `37021` 16:00→12:00; McDowell `37111` 16:23→12:00; Burke `37023` 16:53→12:00; Catawba `37035` 17:23→12:00 and 18:00→18:00; Lincoln `37109` 18:00→18:00; Mecklenburg `37119` 18:16→18:00. |

I checked FIPS/name consistency against the independent county-point names in the
input file. The fixture does **not** retain the route polyline or county sampling
trace, so this does not independently prove the road crosses those counties in
that order. Jeffrey's frozen fixture and geometry need a separate map check.
Small 0.1-minute/kilometer differences between rounded stretch sums and route
totals are consistent with per-stretch rounding.

## Independent hand calculation

I read the JSON arrays directly in PowerShell, without importing
`stormroute.scoring`. The 12:00 UTC timestamp is array index 108 (zero-based).
For Buncombe arriving at 16:00 UTC, the 24 hourly values at indices 85–108
(26 September 13:00 through 27 September 12:00) total **232.6 mm**. The 72
values at indices 37–108 (24 September 13:00 through 27 September 12:00)
total **325.6 mm**. To repeat the arithmetic:

```powershell
$inputData = Get-Content artifacts/demo/prototype_inputs_helene.json -Raw | ConvertFrom-Json
$endIndex = [array]::IndexOf($inputData.precipitation.times_utc, '2024-09-27T12:00')
($inputData.precipitation.mm.'37021'[($endIndex-23)..$endIndex] | Measure-Object -Sum).Sum
($inputData.precipitation.mm.'37021'[($endIndex-71)..$endIndex] | Measure-Object -Sum).Sum
```

The team's illustrative 24-hour tier boundaries are 25/50/100 mm; the 72-hour
boundaries are 75/150/250 mm. Buncombe exceeds both top boundaries, so the
maximum is **Severe concern**, even before its active flood warnings. The
narration's 233 and 326 mm are whole-millimeter rounding, not different totals.

Mecklenburg enters at about 18:17–18:18 UTC, so its window starts 18:00 UTC.
The 24 hourly values from 26 September 19:00 through 27 September 18:00 total
**43.9 mm** (Elevated rainfall tier); the corresponding 72 values from 24
September 19:00 total **73.8 mm** (below the first 72-hour tier). Its **Severe**
label comes from flash flood warning **GSP-66**, not from rainfall. That warning
was issued at 26 September 21:54 UTC; its *original* expiry is 28 September
00:30 UTC, while the final archive expiry is 30 September 01:45 UTC. The
prototype uses the original expiry, and the warning is active at both route
arrivals. The later expiry must not be presented as the departure-time record.

## What was knowable at departure

| Input | Finding |
|---|---|
| Hourly rain | **Not available as shown.** The Open-Meteo ERA5 replay was retrieved on 27 September 2026. Even aside from reanalysis publication delay, the 18:00 UTC window uses rain through 18:00, two hours *after* the 16:00 departure. This affects late Gaston, Catawba, Lincoln, and Mecklenburg stretches. It is historical context, not a departure-time observation or forecast. |
| Alerts | 347 county-coded FA/FF/FL rows are retained. The rule now requires both product and event issuance at or before departure and original expiry after arrival. Ninety-six rows have a product timestamp after departure and cannot count. Two archive rows have an event issue time after departure despite an earlier product timestamp; the explicit event-issue check excludes them. |
| Alert coverage | Ninety-two zone-coded rows were excluded from county mapping. Thirteen retained rows have an original expiry by departure but a later final archived expiry; without revision history, we cannot say which extensions were known before departure. This can understate alerts. Final archived cancellation/expiry statuses likewise do not establish what was known at the chosen departure. |
| Route and county weather | The provisional routes came from a public OSRM response and simplified county boundaries, but their underlying geometry is absent from this fixture. Each county's rain is one sample point; it does not establish conditions on every road in that county. No live road-closure input is included. |

## Real-data behavior checks

These use the actual cached routes and rainfall/alerts, with changes made only
to temporary copies. The repeat-run check blocked Python socket connections;
physical Wi-Fi was **not** switched off on this machine. The reproducible tests
are in [`tests/scoring/test_prototype_real_data.py`](../tests/scoring/test_prototype_real_data.py).

| Case | Result | Evidence |
|---|---|---|
| Remove Lincoln `37109` rainfall (no active county alert) | **PASS** | Its route-1 stretch becomes `Not assessed`, `level=null`, `data_status=missing_weather`, and appears in `unassessed_segments`; never `Lower concern`. |
| Add a pre-departure test flash flood warning to Catawba `37035` | **PASS** | Both Catawba stretches rise from High (level 2) to Severe (level 3); no level falls. The added warning is a synthetic test perturbation, not a real archived warning. |
| Run `scripts/run_prototype.py` twice with socket connections blocked | **PASS** | The two output files are byte-identical. This proves deterministic offline replay on this checkout, not that the full browser workflow works offline. |

After Jeffrey's `math.fsum` fix reached `Mason`, I reran the **exact** script
twice with socket connections denied, writing to
`artifacts/demo/prototype_result.json` both times. On local Python 3.11.9,
each run produced SHA-256
`5ed8dba762744bd63453528ca735b658120327316c1f4021bf7d6df01a627bbc`:
**byte-identical**. The frontend fixture remains a byte copy. No Codespace was
available in this environment, so a fresh Codespace run is still outstanding;
this check also does not prove Python 3.12 behavior. Physical Wi-Fi was not
switched off because the socket block enforced the no-network condition inside
the process without disrupting the shared machine.

Repository checks on Windows/Python 3.11.9: **232 passed, 2 optional network
tests skipped**, one dependency deprecation warning; Ruff format/lint and Mypy
passed. The React build and full browser workflow were not run on this machine.

## Claim audit and disposition

- The checked-in result previously called `route_0` a
  `lower_indicated_concern_route` despite both routes being level 3. Corrected:
  the field and time gain are null on a tie, and the note says no lower-concern
  alternative was found. Route 0 is **13.0 minutes shorter**, not less hazardous
  by this indicator.
- [`docs/mvp_narration.md`](../docs/mvp_narration.md) now states the window end,
  that Buncombe is the **first of several** Severe stretches, the tie, and the
  retrospective input caveat. It agrees with the result JSON. The planner's
  visible disclaimer now calls this a historical replay. The future-model
  [`presentation_outline.md`](../docs/presentation_outline.md) is marked as
  unsuitable for this MVP. All five sections of the
  [MVP slide outline](../docs/mvp_slides.md) were checked. Slide 4 contains the
  limitations; slide 5 states the next-step plan and the small 2022/2023 counts.
- The generated [HTML results page](../artifacts/demo/results.html) agrees with
  the cached JSON on route levels, durations, county order, first tied top-level
  stretch, rainfall reasons, alert list, and provenance. It puts the retained
  county-coded alerts above each advisory. “Rainfall status: complete” means
  both rainfall totals exist, not that alert coverage or road conditions are
  complete. The two explicit negative cautions using “safe” are appropriate;
  neither labels a route safe. The page was checked against its rendered text
  and visually in headless Chrome (1100-pixel desktop viewport); the county
  order, alert-above-advisory layout, and caveats are visible. A keyboard and
  presenting-laptop browser check remain pending.
- The Markdown slide outline is present, but no rendered deck exists in the
  repository. The React results screen exists on Jeffrey's branch but had not
  reached `Mason` at this check. Its comparison code still assumes non-null
  route IDs and `extra_minutes`; after the corrected tie result lands, it would
  show “null is 0 minutes shorter than null.” This is a blocking integration
  fix. The screen also calls rainfall-only `complete` status “Complete data,”
  and says “based on available weather data” without saying the rain is
  retrospective. Label those “Rainfall totals available” and “cached historical
  rainfall,” qualify the alert list as retained county-coded products, and use
  the same Route 0/Route 1 identifiers as the fallback page. These are findings
  from code review, not a run of the React screen.
- The React `demoScore.json` remains a placeholder and the backend score
  endpoint a stub. The complete browser click path **cannot be approved** until
  Jeffrey's screen and frozen route fixture reach `Mason`, the tie bug is fixed,
  and the actual workflow is exercised offline.
- The MVP may be presented as an **illustrative offline historical replay** of
  a rule. It must not be called a safe route, flood probability, AI prediction,
  validated score, measured performance, or a lower-hazard route comparison.
  The EDA gate, weather table, baselines, calibration, 2024 final test, and
  route sensitivity checks remain next steps, not completed evidence.
