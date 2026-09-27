# Frontend handoff — Jeffrey branch (2026-09-27)

## Where things stand

`Jeffrey` is well ahead of `main` (`main` is stuck at `3f0cbba`, before the rebrand). This branch has:

1. The project renamed **PIVOT**, with the real brand mark wired in (`frontend/src/assets/pivot-icon.png`, `pivot-logo-full.png`, used by `components/PivotLogo.tsx`).
2. A full Uber-inspired visual pass: black/white chrome, bold pill buttons, a black header, a hero map with floating chrome (zoom, legend, status), custom trip-endpoint markers. Tokens live in `frontend/src/styles.css`.
3. `/` restored as a single-page sidebar + map planner (`pages/PlannerPage.tsx`), not a separate form → results flow.
4. Mason's real pages kept and reachable at their own routes: `/results` (`PrototypeResultsPage.tsx`), `/case-studies/helene` (`HeleneCaseStudyPage.tsx`), `/route` (`LiveRoutePage.tsx`, a dev-only live preview — hits the rate-limited public OSRM server directly, never use it for the staged demo).

Latest commit: `b2292cc`, pushed to `origin/Jeffrey`. This handoff was then merged with
Mason's branch (see the addendum below) into `integration/mason-into-jeffrey`.

## How to run it

```
make api                # backend on :8000
cd frontend && npm run dev   # frontend on :5173, open http://localhost:5173
```

`make lint`, backend `uv run pytest -q`, and frontend `npm run test -- --run` / `npm run build` all pass clean on this branch as of `b2292cc`.

## What NOT to touch without flagging it to the team first

- **Product-safety colors**: `--level-0..3-bg/-fg`, `--level-none-bg/-fg`, `--route-current`, `--route-recommended` in `styles.css`. These are colorblind-safe risk semantics (a color is never the only signal — every colored element pairs with a text label). Don't repurpose them for brand decoration.
- **Product language**: "Weather Safety Score" / "comparative decision index" / "lower modeled weather risk" — and never "safe route," "guaranteed safe," or similar. The disclaimers throughout the sidebar and map pages are worded carefully; don't edit the copy without checking `docs/build_guide.md` (or the CDC2026 CLAUDE.md) first.
- Canonical schemas (build guide §6.3) and repo structure (§4) — flag any change, don't just make it.

## Known gaps, not yet fixed

1. **Route-geometry/score matching**: `PlannerPage.tsx` and `LiveRoutePage.tsx` each independently call `GET /api/v1/routing/route` (geometry) and `POST /api/v1/trips/score` (score), then match results by `route_id` string. This only works because both calls query OSRM the same way for the same coordinates — it's not a guaranteed-stable contract. Tracked in code comments in both files; revisit once the backend ships a combined or verified-stable-ID response (backend team's own Priority 1 item).
2. **`/route`'s "similar risk" case**: when routes tie, they render in the black primary color rather than a distinct neutral — pre-existing logic in `LiveRoutePage.tsx`'s `routeColor()`, not touched during the Uber restyle. Worth a look if it reads as "this route is recommended" by mistake.
3. **`/route` at very short viewports** (~860px tall): the map area has a 420px minimum height, so the page scrolls slightly. Fine for a dev preview; would want a fix before using this page live in front of judges (it isn't currently part of the staged demo path anyway).

## What's still open / not started

- The Uber rebrand itself was the active task and it's complete and verified (lint, tests, build, and a real-browser Playwright pass with zero console errors in both light and dark mode).
- `main` has not been touched. Merging into `main` is a team decision, not something done unilaterally here.

---

# Addendum — merged with Mason's branch, 27 Sep 2026, ~09:30 EDT

Written for: Cameron and Jeffrey. This branch (`Jeffrey`) diverged from Mason's before a
large chunk of backend work landed there, so merging brought in real changes beyond just
this section — read it before assuming `Jeffrey`'s backend is still what it was at `b2292cc`.

## What Mason's branch added, now merged in

- **CORS handling, request-context middleware, and the `GET /api/v1/geography/counties`
  endpoint** (`backend/src/stormroute_api/{cors,request_context}.py`,
  `routes/geography.py`) — none of this existed on `Jeffrey` before the merge.
- **A real interactive map UI**: `RouteMap.tsx` (county choropleth by band, real OSRM road
  geometry, click/hover popups), `ContributingFactorChips.tsx`, `AlertSummary.tsx`,
  `RouteComparisonChart.tsx` (recharts bar chart). These render on `/results` and
  `/case-studies/helene` via `ScoreDisplay.tsx`'s `RouteCard`, alongside PIVOT's
  `RiskGauge` — both coexist; `RiskGauge` gives the at-a-glance number, the map/chips give
  the detail underneath it.
- **A real Bayesian county-history term in the live score**
  (`src/stormroute/scoring/county_prior.py`): a Beta-Binomial conjugate hierarchical fit
  on the 2,220 real NOAA Storm Events (2015-2024) the EDA already validated, entering
  `score_segment`'s formula as a third, capped, never-lowering term:
  `segment_index = round(max(rain_component, alert_component, county_prior_component))`.
  Descriptive, not predictive — see `prototype_score_spec.md`'s "County history term"
  section for the full honesty caveats. `SegmentScore.county_prior_component` (always
  present) and `ContributingFactor.kind: 'historical'` are the new wire-contract fields;
  `types/score.ts` merged both in cleanly with no conflict.
- `docs/model_card.md` corrected — it previously claimed the live formula had "no fitted
  parameters" and didn't use the NOAA data, both now false for this one term.

## Merge conflicts and how they were resolved

- **`ScoreDisplay.tsx`, `PlannerPage.tsx`, `PlannerPage.test.tsx`, `styles.css`**: both
  branches touched these independently (PIVOT's redesign vs. the map/chips work). Resolved
  by keeping PIVOT's structure and layout and re-adding the map/chip components inside it
  as an additional detail section under `RiskGauge`, not replacing it.
- **`PrototypeResultsPage.test.tsx`**: deleted on `Jeffrey` (superseded by its own test
  restructuring), modified on `Mason`. Kept Mason's version since it exercises the map/chip
  rendering `Jeffrey` didn't have tests for yet — worth a look to see if it should be
  reconciled with `Jeffrey`'s newer test patterns.
- This file (`handoff.md`): both branches had independently written one. Combined rather
  than picking one — both describe real, still-relevant work.

## Verified after the merge

See the bottom of this file's own commit for the actual command output — re-run
`PYTHONPATH=src:backend/src .venv/bin/python -m pytest -q` and, from `frontend/`,
`npm run typecheck && npm run lint && npm test -- --run && npm run build` before trusting
this branch for the demo; don't assume the pre-merge verification on either parent branch
still holds after a merge this size.

## Known follow-ups, not done in this merge

- **Bundle size**: recharts alone is used once (`RouteComparisonChart`); a dynamic
  `import()` for that one chart would shrink the initial bundle if it matters for the demo
  machine's load time. Not urgent.
- **`/route` (the dev-only live OSRM preview page)** was left untouched by both branches'
  work — different component (`LiveRouteMap`), different job.
- Mobile/dark-mode was spot-checked on the Helene page only pre-merge, not exhaustively on
  every new component post-merge; worth a fresh pass if time allows.
- `main` still has not been touched. Merging this integration branch into `main` (or
  pointing the DevPost submission at it directly) is a decision for the team, not made
  unilaterally here.
