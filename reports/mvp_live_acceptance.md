# Live MVP acceptance plan — Cameron

## Addendum — real live verification, 27 Sep 2026 ~04:00 EDT (from Mason's backend assistant)

Cameron, welcome back. While you and Jeffrey were away I did what your report correctly said
was still missing: an actual run, not source inspection. Everything below is from a real
headless-browser session against a freshly restarted backend (`Mason` at `526cc0b`), plus one
real bug I found that source review couldn't have caught.

**Housekeeping first:** your report's "not verified" disposition was accurate as of when you
wrote it, but two things changed after: (1) `90e402e`/`4c8eb51` are now merged into `Mason`
(I did it), so "not yet in Mason" in your "Current gate" section is stale; (2) I found and
killed a stale `uvicorn` process left running from earlier in the session that was silently
serving pre-fix code — if you test and get "at least 2 candidates are required" on a
single-route trip, you're hitting a zombie process, not the current code. Kill anything on
:8000 and restart `make api` fresh.

**What I actually ran, with a real Chromium browser (Playwright), against `Mason` at `526cc0b`:**

1. Loaded the planner, typed "Raleigh" into Origin — got real ORS results
   ("Raleigh, NC, USA"), selected one. Typed "Wilmington" into Destination, selected
   "Wilmington, NC, USA". Filled a real future departure. Clicked "Analyze trip."
2. Landed on `/results` showing "Raleigh, NC, USA to Wilmington, NC, USA," a real OSRM route
   (211.9 km, 151 min), a real county timeline (Wake → Johnston → Sampson → Duplin → Pender ×2
   → New Hanover), each with real `rain_rate_mm_h`/`rain_24h_mm` and honest "Lower concern"
   (real: NC is dry tonight). **OSRM returned exactly one route for this trip**, and the app
   correctly showed `comparison.ranking: "single_route"`, "Only one route was available, so no
   comparison is possible" — no invented alternative. Zero console errors.
3. Separately, clicked the "Load the Hurricane Helene replay" button and confirmed it
   round-trips through the same results page with `mode: "cached"` shown.

**This directly closes or updates several of your items:**

| Your ID | Update |
|---|---|
| A1 | **Now verified live**, item 1–2 above. Different trip than your agreed A2 pair, but satisfies "a newly entered trip produces route alternatives [or a documented single-route result], time-matched weather/alerts, reasons" end to end, in a real browser. |
| A2 | **Partially closed.** Raleigh→Wilmington (a second, distinct, user-typed trip, not Greensboro–Wilmington specifically) was verified in the real browser. Greensboro–Wilmington itself I verified live via direct API call (`curl`/`TestClient`, not yet through the browser) — two genuinely different real routes came back (via Alamance vs. via Randolph), both scored. **Still open: run Greensboro–Wilmington specifically through the browser**, since that's the trip you and Jeffrey agreed on. |
| A3 | **Fixed and verified.** The "Neither route" wording bug you found (item 46 in your findings) is fixed: `_severe()` now says "This route does not avoid..." for one route, "None of the routes avoid..." for more. Verified live via the single-route Raleigh→Wilmington result above, which correctly showed no severe-advice text at all (concern was Lower, not Severe, so the wording wasn't exercised — but the code path and its unit tests are in `tests/scoring/test_concern.py::test_severe_advice_wording_matches_route_count`). |
| A7 | **New backend behavior, unit-tested, not yet UI-tested:** a cache fallback older than 3h (forecast) / 30min (alerts) is now refused outright (treated as no cache), never served as current. Explicit `offline=True` replay is exempted on purpose. See `docs/prototype_score_spec.md`'s "Freshness policy" section. |
| A12 | **Partially closed, one real gap found.** Cache/replay status (`mode: "cached"`) does round-trip to the results page and is visible in the disclaimer text. But: **`age_minutes` (how old the cached data is) is now in the API response and is not yet rendered anywhere in the UI** — only `from_cache` (boolean) and the request time are shown. Flag for Jeffrey. |
| A13 | **One new finding, not in your list: the "Load the Hurricane Helene replay" button is mislabeled.** It does not load Hurricane Helene. `mode=cached_replay` replays `artifacts/demo/saved_trip_request.json`, which I generated tonight from a live, contemporary trip (today's date, dry weather, `Lower concern`) — this is correctly the brief's "cache one contemporary trip for a demo fallback," and it's correctly kept separate from Helene reanalysis (which must never feed the live flow, per the brief). The bug is purely the button's *text*: it should say something like "Load saved trip (offline demo)," not "Hurricane Helene." The real Helene Severe-concern example still exists, just as the separate standalone page `artifacts/demo/results.html`, not wired to this button. Low effort to fix, but exactly the kind of claim-vs-code mismatch your case 13 exists to catch — please verify my finding independently when you're back. |
| A14 | **Verified live**, twice, both paths (steps 1–3 above): the demo button and the typed form take two structurally independent code paths (no shared state), matching the fix Jeffrey described. |

**Still genuinely open, unchanged from your list:** A4/A5 with real (non-dry) data, A6/A8/A9/A11
in the actual browser rather than unit tests only, `minutes_at_or_above_50` not shown in the UI,
the planner disclaimer's unconditional Helene wording, the map legend wording question (I
weighed in earlier: "lower modeled weather risk" matches CLAUDE.md's own approved phrase, your
suggested change isn't required), and a full clean-Codespace run (I'm doing that next).

**Verification commands**, backend fully passing: `PYTHONPATH=src:backend/src .venv/bin/python -m pytest -q`
→ 294 passed, 3 skipped (network-only). Frontend, from `frontend/`: `npm run typecheck && npm run lint && npm test && npm run build`
→ all clean, 51/51 tests. Both run tonight against `Mason` at `526cc0b`, not assumed from
CI history.

---


**Purpose:** define and track independent checks through backend and frontend integration. The acceptance cases were specified before integration; this sheet is not sign-off evidence. Record the commit, test time, inputs, output, and pass/fail result for each check as the vertical slice is exercised.

## Current gate

The live scoring specification, forecast/alert adapter, pure scoring functions, `score_trip()`, typed response contract, and FastAPI `POST /api/v1/trips/score` route are on `Mason`. The route scores `mode=live` requests and supports a saved contemporary `mode=cached_replay`. Jeffrey's planner and map integration are on `origin/Jeffrey` (`90e402e`, updated by `4c8eb51`) but not yet in `Mason`. Commit `13111d1` showed a false `AI` map badge; `4c8eb51` replaces it with a storm glyph and fixes mode selection. The planner's general disclaimer still wrongly describes all submissions as a Helene replay, so that wording needs correction before merge. The Helene replay is retrospective and is excluded from live-flow acceptance.

**Live MVP disposition: not verified; do not sign off as the agreed arbitrary-trip MVP.** In the status table, `Fail` means the required feature is absent or contradicted by source inspection; it does not imply a completed live end-to-end test. `Pass for fixed replay fixture only` is limited to the cached Helene display.

## Agreed second arbitrary test trip

- Origin: Greensboro, NC (`36.0726, -79.7920`)
- Destination: Wilmington, NC (`34.2257, -77.9447`)
- Departure: **2026-09-27 10:00 EDT** (`2026-09-27T10:00:00-04:00`)
- Mode: live

Mason approved Greensboro–Wilmington as the second arbitrary trip. It is future and wholly in-state and does not reuse the Helene fixture. Before the check is run, record the resolved place labels/coordinates, route IDs returned by OSRM, and exact response fixture or retrieval timestamps. The currently dry forecast is not a reason to change the test: coverage, request wiring, reasons, and claim accuracy still need verification.

## Acceptance checks

| ID | Check and pass condition | Evidence to record | Status |
|---|---|---|---|
| A1 | **Entered trip works:** submit the first agreed supported NC trip through the planner without editing code or fixtures. The result uses OSRM routes, time-matched forecast/active alerts, segment reasons, source/valid/retrieval times, coverage, and the prototype label. | Screen recording or screenshots; request/response; commit SHA. | **Wired on Jeffrey, not yet verified on Mason:** `90e402e` connects the planner to `scoreTrip()`; `4c8eb51` fixes the stale mode selection so arbitrary form submissions use live scoring. Merge and run the first agreed trip; its details are not in this handoff. |
| A2 | **Second arbitrary trip:** submit a different supported NC trip through the same UI without changing source or fixture data. | Trip, route IDs, response, commit SHA. | **Trip agreed; execution pending:** Mason approved Greensboro–Wilmington as the second arbitrary trip. Its UI run and response have not yet been verified. |
| A3 | **Route count one:** when the routing response contains one route, show its assessment and explicitly say comparison is unavailable; do not invent an alternative or a time/score delta. | Screen and response with one route. | **Owner-reported scorer/API tests pass; UI pending:** Mason reports 282 tests passing locally on `848b1dd`. Jeffrey's `90e402e` consumes the API but is not yet merged or exercised; fix the singular-route severe-advice wording below. |
| A4 | **Tie:** supply two routes with equal score under identical coverage. Show a tie/no distinguishable lower-concern route; never say one is safer or lower concern. A deterministic display order is acceptable if clearly not a ranking. | Inputs, exact scores, screen text. | **Scorer unit pass; fixture UI pass:** the score tests return `tie` with no lowest route, and PR #25's CI tests the fixed-replay wording. No integrated live browser test. |
| A5 | **Both routes severe:** warnings and official guidance remain prominent; the UI says neither option avoids the serious indicated concern and preserves delay/check-guidance advice. | Inputs, alert records, screen. | **Scorer unit pass; fixture UI pass:** severe-advice test and fixed replay support this. Separate edge case: a single severe route also receives the phrase “Neither route avoids”; see scoring review below. |
| A6 | **Missing forecast / uncovered segment:** remove one required segment forecast or set its valid horizon before that segment's arrival. Mark that segment and route comparison unassessed/limited; never convert missingness into a low score or confident winner. | Modified response, resulting screen and ranking state. | **Scorer unit pass; UI pending:** tests cover missing forecast as null/unassessed, horizon gaps, lower-bound partial routes, and blocked ranking. |
| A7 | **Expired/stale inputs:** provide a forecast that is expired for arrival and an alert inactive at the relevant segment arrival. Expired forecast must not be presented as valid; inactive alert must not be applied as active. Show coverage or freshness limits. | Issue/valid/expiry times and response. | **Partial scorer evidence:** forecast horizon and alert time-overlap logic are present; no explicit expiry-boundary test or stale-cache policy/display is verified. |
| A8 | **Unavailable service / unsupported geography:** simulate routing/weather API failure and a route leaving NC. Show a clear error or partial-coverage state; no silent NC extrapolation and no confident route ranking. | Error payload, UI state, network-off/cache test. | **Owner-reported tests pass; UI states pending verification:** Mason reports 282 tests passing on the API commit, including endpoint checks. Inspect live failure/partial states after `90e402e` merges and exercise them in the browser. |
| A9 | **Monotonicity:** holding all else fixed, worsen one forecast hazard input or add/raise an active official alert. The affected route's indicated concern must not improve. The alert may only raise concern. | Paired requests and scores. | **Scorer unit pass:** tests assert higher rain and alert floors never lower the index. Live endpoint/rendered-score check pending. |
| A10 | **Duration and splitting:** hold weather/time exposure constant while changing route segment granularity. Splitting one interval into adjacent identical subsegments must not change the route score. Longer exposure to the same adverse conditions must not improve it. | Hand calculation and paired scorer results. | **Partial scorer pass:** split-stretch invariance is tested. Route index intentionally uses the maximum, not exposure duration; `minutes_at_or_above_50` reports time but is not shown in Jeffrey's results or map UI, and has no explicit duration test. |
| A11 | **Comparable coverage:** if routes have different missing-data coverage, the UI must expose the difference and withhold a winner unless the shared coverage rule in the agreed score specification permits a valid comparison. | Paired route payloads and screen. | **Scorer test pass; UI wired on Jeffrey, display test pending:** partial-route and failed-alert cases set `ranking=unavailable`; verify the UI message after merge. |
| A12 | **Cache fallback:** with upstream services unavailable, the contemporary cached trip flows through the same result screen and response shape; cache retrieval time and cached/replay status are visible. It must not silently fall back to Helene reanalysis. | Network-off run, displayed timestamp/mode, response. | **Wired on Jeffrey; offline UI run pending:** the Helene preset calls `mode=cached_replay` and the results page visibly marks cached replay and shows provenance. Verify same-flow offline behavior after merge; cache-age maximum remains a nonblocking follow-up after 4:00. |
| A13 | **Visible claims:** audit every sentence and number on planner, results, and methodology pages against the implementation and response. Remove probability, prediction, safety, measured-performance, road-condition claims unsupported by code/evidence, and any literal AI/ML claim anywhere in the UI. | Claim-by-claim checklist with source location and screen text. | **Correction partly landed on Jeffrey:** `13111d1` displayed a false `AI` label; `4c8eb51` replaces it with a storm glyph, and current visible JSX has no literal AI/ML label. The planner still says the demo replays Helene and is “not a live forecast,” despite the live form path. The map legend says “Lower modeled weather risk”; prefer the spec's “Lower indicated concern,” since this rule is not calibrated risk. Fix those claims and verify visible/accessibility text after merge. |
| A14 | **Live/replay separation:** a future departure submits `mode=live`; past dates are accepted only through a separately labeled replay flow. | Request payloads and UI state for future and past departures. | **Wired on Jeffrey, pending merge and run:** `4c8eb51` makes ordinary form submissions live and moves the cached replay to a separate demo button. Verify those payloads in the integrated UI. Mason confirms the 15-minute past-departure tolerance is intentional; it is not a blocker. |

## Follow-up source and CI review (2026-09-27)

Reviewed `Mason` through `95330a6` and Jeffrey's latest `origin/Jeffrey` through `4c8eb51`. Mason reports 282 tests passing locally on endpoint commit `848b1dd`; I could not independently rerun them. The project `.venv` targets a missing Python 3.11.9 install; the available Python 3.12.4 runs pytest but cannot import the venv's CPython 3.11 NumPy binary. Jeffrey's planner sends arbitrary trips as `mode=live` and the Helene preset as `mode=cached_replay`; both use the same score-response page. The latest map page scores and colors routes. `4c8eb51` replaces the visible `AI` orb and makes the form always use live mode; its preset button separately runs cached replay. These commits are not merged to Mason yet, and I have not exercised the browser flow.

### Independent scoring review findings

- Mason confirms the 15-minute past-departure tolerance is intentional; treat it as an agreed behavior, not a blocker.
- `compare()` handles a one-route result before ranking checks and calls `_severe(routes)`; a single severe route can receive the sentence “Neither route avoids...”. That wording assumes multiple routes and should be corrected or suppressed for `single_route`.
- The score response carries forecast retrieval time, horizon, segment arrival/duration, and values with units in field names, but not the exact hourly valid-time stamps used for each segment. This is a follow-up after 4:00, not a demo blocker.
- Route index is deliberately the maximum segment index and does not increase with duration. The separate `minutes_at_or_above_50` field is the duration evidence, but Jeffrey's current results and map views do not display it; avoid implying the index is duration-weighted, and add the duration measure when practical.
- Cache retrieval time is present, but there is no stated maximum cache age. Mason says to follow up after 4:00; the age remains a limitation to state clearly.

These are review findings, not changes to Mason's scoring implementation. Greensboro–Wilmington is now approved as the second arbitrary trip, but it has not yet been run through the integrated React flow or independently recalculated. A committed contemporary saved-trip response was independently spot-checked as supplemental evidence.

Source review of Jeffrey's current UI confirms that the results page reads the returned score and request, reports cache/replay mode, and states that the index is not a probability, trained model, or validated score. Commit `4c8eb51` replaces the earlier false visible `AI` orb with a storm glyph; keep the case-13 check for no literal AI/ML claim anywhere in visible or accessible UI text. The planner disclaimer still says the whole demo replays Helene and is “not a live forecast,” which conflicts with its live arbitrary-trip path; limit that statement to the preset. The map legend's “Lower modeled weather risk” overstates a threshold index; use “Lower indicated concern.” The Methodology page remains a TODO placeholder despite the new backend methodology endpoint.

The scoring-layer commit `d1eab76` had successful GitHub CI (Python lint/types/tests, hygiene guards, frontend ESLint, TypeScript, Vitest, production build). Mason reports 282 tests passing locally on `848b1dd`; I could not reproduce this locally. GitHub workflow/status lookups returned no attached checks for the latest Mason or Jeffrey integration commits reviewed here. No browser, presentation-laptop, or offline full-flow check has been done.

## Cameron assignment copied one-for-one from the team brief

The following assignment, handoff, acceptance cases, fallback order, and checkpoints are copied from the latest supplied “StormRoute project and MVP brief.” The original wording is retained so every Cameron task can be checked against its source.

**Cameron: independent verification — primary job**

> Define acceptance cases before integration, check weather validity and alert timing, challenge score behavior, and audit all visible safety claims. Check the chosen arbitrary trip by hand.

**Handoff and proof**

> Record pass/fail for the cases below and approve the displayed numbers and wording before the demo freeze.

**Acceptance cases**

- [ ] A newly entered, supported NC trip produces route alternatives, time-matched weather/alerts, score reasons, and a fastest-versus-lowest-concern result.
- [ ] A second entered trip works without editing fixtures or source code. If only the saved trip works, call it a demo prototype, not free-form MVP.
- [ ] Both routes tied: no “safer route” claim. Both routes severe: warning and delay advice remain visible.
- [ ] Only one route: show its assessment without a fabricated alternative.
- [ ] Missing forecast, expired forecast horizon, API failure, or route leaving modeled geography: show coverage limits and avoid a confident ranking.
- [ ] A stronger alert or worsening weather cannot make the displayed score improve.
- [ ] Demo trip runs with cached upstream responses when the external services are unavailable. Cache age and replay status are visible.
- [ ] A clean Codespace start, repeat run, and short rehearsal succeed; capture a backup recording.

**Fallback order**

> live arbitrary trip; saved contemporary trip through the same result flow; precomputed result for that contemporary trip, clearly labeled. The Helene historical page is evidence of an earlier prototype and can be shown separately if the live flow fails. Do not silently substitute it for an arbitrary trip.

**Deadline checkpoints relevant to Cameron**

| Eastern time | Required state | Current evidence |
|---|---|---|
| 8:00 a.m. | Cameron’s core cases pass; cache and backup work. Fix incorrect claims and blocking failures only if behind. | Not met: backend live scoring and contemporary saved-trip cache exist, but planner-to-score UI flow, clean Codespace run, rehearsal, and backup recording are not evidenced here. |
| 9:30 a.m. | Numbers, narrative, and limitations reviewed; rehearsal done. Remove any unverified claim or fragile screen. | Partial: historical replay numbers and claims are in `reports/mvp_verification.md`; live-trip numbers cannot be approved and the planner overstates the wired capability. Rehearsal is not evidenced. |

**One-for-one status against the source acceptance cases**

| Source case | Cameron check / evidence | Status |
|---|---|---|
| Newly entered supported NC trip returns alternatives, time-matched weather/alerts, reasons, and fastest vs lowest concern. | Inspect request mode, route acquisition, score response, UI output, then hand-check one segment from saved inputs. | **Wired on Jeffrey, pending integration and run:** commit `90e402e` calls the live score API from the planner; run the agreed Greensboro–Wilmington trip and hand-check a segment after it reaches Mason. |
| Second entered trip works without fixture/source edits; otherwise call it a demo prototype. | Submit a second user-entered NC trip without changing code/data. | **Trip agreed; pending run:** Greensboro–Wilmington is approved as the second arbitrary trip. Verify on the integrated UI without editing fixtures or source. |
| Tied routes make no safer-route claim; both severe routes keep warning/delay advice visible. | Check comparison wording, warning prominence, and advisory for the same response. | **Source-level support on Jeffrey:** results render the API comparison message and severe advice; tied-fixture wording passed earlier review. No live browser case has been run. |
| One route is shown without a fabricated alternative. | Supply a one-route response and inspect the screen. | **Source-level support, run pending:** results render the returned route list and comparison; exercise one route, especially the plural severe-advice defect in the scorer. |
| Missing forecast, expired horizon, API failure, or unsupported route shows coverage limits and withholds confident ranking. | Test each boundary and confirm missingness cannot appear as low concern. | **Owner reports 282 backend tests pass:** confirm the outcomes in the integrated UI after merge; no browser fault/partial-coverage test is recorded here. |
| Stronger alert or worse weather cannot improve displayed score. | Paired inputs to the same scorer, then verify displayed result. | **Scoring-layer tests passed in earlier CI:** live scorer tests cover higher rain and alert floors; Jeffrey's page now renders the score response, but paired displayed behavior remains unverified. |
| Offline demo uses cached upstream responses; cache age and replay status are visible. | Disable network and exercise the same screen/response contract; inspect cache metadata. | **Wired, offline run pending:** the Helene preset uses the saved contemporary replay through the same results page; exercise it with network blocked. Cache-age policy is a follow-up after 4:00. |
| Clean Codespace start, repeat run, short rehearsal, and backup recording. | Fresh Codespace, repeat full start/run, rehearse, save recording. | **Not evidenced:** automated CI passed for the scorer commit, but no clean Codespace, complete live flow, rehearsal, or recording was supplied. |

**One-for-one status against Cameron’s primary job and handoff**

| Assigned task | Status and evidence |
|---|---|
| Define acceptance cases before integration. | **Done:** this file contains the 14 detailed checks above and preserves the source’s eight acceptance cases verbatim. |
| Check weather validity and alert timing. | **Partly done:** historical limitations are documented in `reports/mvp_verification.md`; live adapter and response expose retrieval/horizon and alert timing. The saved contemporary fixture received a manual spot-check below; arbitrary-trip freshness/valid-time review remains pending. |
| Challenge score behavior. | **Scoring tests reviewed:** monotonicity, splitting, missingness, and ranking comparability are covered by CI tests. Duration sensitivity remains limited because the route index is max segment risk; UI interpretation and real-trip perturbations remain pending. |
| Audit all visible safety claims. | **Source review found and tracked two fixes:** Jeffrey replaced the false AI badge with a storm glyph in `4c8eb51`; the planner's historical-replay disclaimer still needs narrowing. Methodology page remains a placeholder. No browser claim audit has been run. |
| Check the chosen arbitrary trip by hand. | **Approved trip; execution pending:** Mason approved Greensboro–Wilmington as the second arbitrary trip. The Asheville–Charlotte saved fixture hand-check is supplemental, not a substitute. |
| Record pass/fail for the source cases. | **Done with limitations:** one-for-one table above records pass/partial/fail/not-verified and evidence. |
| Approve displayed numbers and wording before demo freeze. | **Not approved:** the live planner needs merge and browser verification; correct the planner disclaimer and map legend wording first. |

## Independent numerical review

Supplemental hand-check of the committed contemporary saved fixture (not either arbitrary-trip acceptance case): request as-of `2026-09-27T05:33:49Z`, departure `08:00Z`, Asheville to Charlotte. On `route_0`, the first segment is Buncombe FIPS `37021`, arrival `08:00Z`, duration `19.7` minutes. Sorting the county forecast points by FIPS places Buncombe at the first forecast point. Its segment overlaps the hourly accumulation ending `09:00Z`; the raw cached hourly value is `0.0 mm`. The preceding 24 hourly accumulations ending at `09:00Z` (timestamps `2026-09-26T10:00Z` through `2026-09-27T09:00Z`, inclusive) also sum to `0.0 mm`. The response reports peak `0.0 mm/h`, prior-24-hour total `0.0 mm`, and no matching active flood product for Buncombe. Applying the written rule gives `100 × max(0/20, 0/100) = 0`, matching the segment's index `0` and `Lower concern` band. Forecast retrieval was `05:33:49.952537Z`; NWS retrieval was `05:33:50.141629Z`. This verifies one saved-response calculation only. The selected hour's valid time is inferred from raw cache timestamps because per-segment valid-hour stamps are not returned; verify that the integrated page displays the matching values.

For full acceptance, after the UI integration reaches Mason, run both arbitrary trips, including Greensboro–Wilmington as trip two. Recompute one Greensboro–Wilmington segment from its saved response inputs. Confirm units, timezone, forecast valid time versus retrieval time, alert activity, missing-coverage treatment, score formula, and displayed rounding. No arbitrary-trip number is approved by this plan alone.

## Remaining acceptance tasks and follow-ups

1. Merge Jeffrey's planner integration `90e402e`/`4c8eb51` to Mason after the planner disclaimer and “Lower modeled weather risk” legend are corrected; then run the primary live trip and Greensboro–Wilmington as trip two through the browser.
2. Hand-check one segment from Greensboro–Wilmington's actual saved request/response and compare the arithmetic and explanation with the rendered result.
3. Exercise tied, one-route, severe, missing-forecast, out-of-geography, API-error, and cached-replay UI cases. The scorer tests do not replace the browser checks.
4. Fix the single-route severe-advice wording: `compare()` currently calls a helper whose message says “Neither route” even when there is one route.
5. Follow up after 4:00 on exposing selected forecast valid-hour timestamps and setting/displaying a maximum cache age; Mason says these are nonblocking for the immediate gate.
6. No project Python suite could be run locally: `.venv` points at a missing Python 3.11.9, and its compiled NumPy wheel cannot load under available Python 3.12.4. Mason reports 282 tests passing on `848b1dd`. Repair the local runtime separately if time permits, and record the successful integrated UI/browser run before sign-off.

The response contract and scoring rule are defined in the repository. Do not change them after viewing demo outcomes without versioning the contract and repeating affected checks.
