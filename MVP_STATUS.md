# MVP status

Last updated 27 Sep 2026, 04:00 EDT, from a fresh backend restart plus a real headless-browser
run against it. This supersedes the "late evening" version: the product changed from a fixed
Helene replay to a **live, arbitrary-trip planner**, per the team brief that superseded the
original MVP plan. Verified by running it, not by reading it.

## What runs today — live-verified, not just claimed

| Piece | State |
|---|---|
| Geocoding (`GET /api/v1/geocode/*`) | Live, real ORS key. Verified: typed "Raleigh" in a real browser, got real results ("Raleigh, NC, USA"). |
| Routing (OSRM) | Live. Accepts 1 route as a normal result now, not an error (fixed 27 Sep 03:xx). Route IDs are content-derived hashes, stable across independent fetches by the score endpoint and the map preview. |
| Live forecast + alerts (Open-Meteo, NWS) | Live, no API key needed. Cache fallback with a documented freshness policy: a fallback older than 3h (forecast) / 30min (alerts) is refused, never served as current. |
| `POST /api/v1/trips/score` | Live and working, `mode=live` and `mode=cached_replay` both verified. Real request → real OSRM + forecast + alerts → real scored response, ~1s. |
| `GET /api/v1/methodology` | Live. The honest methodology statement, versioned with the scoring module so it can't drift. |
| React planner → results flow | **Live-verified in a real headless browser tonight**, both paths: the "Load the Hurricane Helene replay" button (`mode=cached_replay`, offline-safe) and a typed arbitrary trip (`mode=live`). Zero console errors either way. Screenshots on file. **The button is mislabeled** — see Known limits. |
| Frontend checks | `npm run typecheck`, `npm run lint`, `npm test` (51/51), `npm run build` (production) all pass, run tonight, not assumed. |
| Backend checks | `pytest` 294 passed, `ruff` clean, `mypy` clean. |
| Trained model, calibration, held-out evaluation | **None. Not part of the MVP.** The EDA gate is still open. See `docs/model_card.md`'s top section for exactly what is and isn't shipped. |

## What the score is

`prototype-score/1`, specified in full in `docs/prototype_score_spec.md`. A 0–100 index per
route (higher = more indicated concern), built from live rainfall forecast and NWS alerts. Not
a probability, not a trained model, not validated. Every claim in the UI must say "prototype."

## Known limits (say them out loud)

- Forecasts are uncertain. One rainfall point per county. No road-closure or passability input.
- A missing alert doesn't mean none exists; an alert issued after the request isn't seen.
- `minutes_at_or_above_50` (exposure duration) is in the API response but **not yet shown**
  in the current results screen — the index itself is a maximum, not duration-weighted.
- `age_minutes` (how old the forecast/alerts are) is in the API response but **not yet shown**
  in the current results screen — only `from_cache` and the request time are displayed.
- Real conditions tonight (27 Sep 2026) are dry statewide with no inland flood alerts, so a
  live trip will honestly show "Lower concern" and a tie. That's the correct result, not a bug.
  The Helene replay is the example of what "Severe concern" looks like.
- The planner's disclaimer text still unconditionally says "this demo replays archived
  Hurricane Helene conditions... not a live forecast," even on the live (typed-trip) path.
  That's stale wording from before the live path existed and should be split before the demo.
- **Found tonight: the "Load the Hurricane Helene replay" button does not load Hurricane
  Helene.** `mode=cached_replay` replays `artifacts/demo/saved_trip_request.json`, which is a
  contemporary trip I saved tonight (departure `2026-09-27T10:00Z`, real dry conditions,
  `Lower concern`) — this is the brief's "cache one contemporary trip for a demo fallback,"
  correctly separate from historical Helene reanalysis, which must never feed the live flow.
  The button's *label* is just wrong: it should say something like "Load saved trip (offline
  demo)," not "Hurricane Helene." The real Helene Severe-concern example only exists as the
  separate standalone page `artifacts/demo/results.html`. This is a one-line label fix for
  Jeffrey, but worth catching before a judge clicks it expecting to see flooding.

## Run it

Two terminal tabs, from the repo root:

```bash
make api                        # backend on :8000, needs .env with ORS_API_KEY
cd frontend && npm run dev      # frontend on :5173, proxies /api to :8000
```

Open http://localhost:5173. Both the demo button and a typed trip work.

## Demo plan

Live trip first (proves the real pipeline; honestly ties tonight since NC is dry), then, if a
severe example is wanted, the standalone Helene page (`artifacts/demo/results.html`) as its
own clearly separate artifact — not the in-app "saved trip" button, which is the offline
fallback for a *contemporary* trip and currently also shows a dry tie. This matches the
brief's fallback order (live → saved contemporary replay → Helene as a separate case study,
never a silent substitute for an arbitrary trip).

## Owners and open items

- **Jeffrey:** split the planner disclaimer (see Known limits); the "PIVOT" rebrand and new
  gauge UI are in progress — needs a visible "prototype" label near any 0–100 display, since
  CLAUDE.md's "Weather Safety Score" language is reserved for the future calibrated model, not
  tonight's rule. Consider surfacing `age_minutes` and `minutes_at_or_above_50`.
- **Cameron:** `reports/mvp_live_acceptance.md` has a live-verification addendum from tonight;
  several of the "pending" items there are now independently confirmed — see the addendum at
  the top of that file for exactly which ones and what's still open.
- **Mason:** decide the rebrand scope with Jeffrey; approve or amend the prototype-label
  requirement before the gauge screen ships.
