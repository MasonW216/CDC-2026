# MVP slide outline (5 slides, about 90 seconds of talking plus the live app)

Rewritten 27 Sep 2026 for the live-first product (the brief that superseded the Helene-only
plan). Every claim below was checked against a real run tonight, not assumed. Numbers trace to
a real live response (`curl`/browser, 27 Sep, ~03:53–04:00 UTC) or `artifacts/demo/saved_trip_response.json`
for the Helene example.

## 1. The problem
- A traveler's flood-related weather exposure depends on the route and the time they travel.
- StormRoute lets a traveler enter **any** origin, destination, and future departure in North
  Carolina, and compares the fastest route with the route showing the lowest indicated concern.

## 2. What we built (live demo: type a real trip into the planner)
- Real routing (OSRM), real forecast (Open-Meteo), real official alerts (NWS), scored live.
- A prototype 0–100 weather-concern index per route: the higher of trailing rainfall and active
  NWS flood-product severity, per county stretch the traveler passes through.
- Official alerts shown above any recommendation. An alert or worse rain can only raise the
  index, never lower it.
- One route from OSRM is a normal result, not an error: shown on its own, no invented
  alternative.

## 3. The result, live, tonight
- Real tonight's forecast: North Carolina is dry statewide with no inland flood alerts, so a
  live trip honestly scores "Lower concern" and the comparison correctly reports a tie with no
  invented winner. That is the honest result of the actual live pipeline, not a placeholder.
- The app's own "saved trip" offline-fallback button (per the brief: a contemporary trip cached
  for when the network drops, not a historical replay) also shows this same dry, honest result
  today, since it was cached from today's real conditions.
- The Severe-concern Hurricane Helene example (Asheville–Charlotte, Buncombe County 233 mm/24h,
  active flash flood warnings) is a **separate, standalone artifact**
  (`artifacts/demo/results.html`), not wired into the live app's buttons — historical reanalysis
  rainfall is deliberately kept out of the live trip flow, per the brief. Present it as its own
  page if a severe example is needed on stage.

## 4. What this is not
- A **rule**, not a trained model, not a calibrated flood probability, not a validated score.
  Thresholds (20 mm/h, 100 mm/24h, alert floors) are team policy, stated in
  `docs/prototype_score_spec.md`.
- One forecast point per county. No road-closure or passability input. A missing alert is not
  a guarantee none exists.
- It does not say a road is open or safe, and never overrides an official NWS warning.

## 5. What is real, and what comes next
- Real tonight: live geocoding, live routing, live forecast and alerts, a documented scoring
  rule with a freshness policy on cached fallbacks, and an offline-safe replay for the demo
  floor. Independently verified end to end in a real browser, not assumed.
- Also real, separately: a reviewed exploration of ten years of NC flood reports (2,220
  qualifying events, 1,499 positive county-windows of 1,461,200), still gated on team sign-off.
- Next: close that review gate, build the historical county × six-hour weather table with
  as-of availability checks, define baselines before training, select on 2022, calibrate on
  2023, run one frozen 2024 test — before any number is called a risk.
