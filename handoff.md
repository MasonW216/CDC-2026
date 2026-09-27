# Frontend handoff — Jeffrey branch (2026-09-27)

## Where things stand

`Jeffrey` is well ahead of `main` (`main` is stuck at `3f0cbba`, before the rebrand). This branch has:

1. The project renamed **PIVOT**, with the real brand mark wired in (`frontend/src/assets/pivot-icon.png`, `pivot-logo-full.png`, used by `components/PivotLogo.tsx`).
2. A visual pass with a slate-storm ink chrome (not flat black), Space Grotesk for headings/the score numeral, Public Sans for body text, and uppercase labels dialed back to one deliberate use (`.section-title`). Tokens live in `frontend/src/styles.css`.
3. `/` restored as a single-page sidebar + map planner (`pages/PlannerPage.tsx`), not a separate form → results flow.
4. Mason's real pages kept and reachable at their own routes: `/results` (`PrototypeResultsPage.tsx`), `/case-studies/helene` (`HeleneCaseStudyPage.tsx`, see below), `/route` (`LiveRoutePage.tsx`, a dev-only live preview — hits the rate-limited public OSRM server directly, never use it for the staged demo).
5. `/methodology` and `/about` are real pages now, not placeholders — `pages/MethodologyPage.tsx` documents the actual `prototype-score/1` rule (thresholds, alert floors, bands, sourced from `docs/prototype_score_spec.md`/`configs/scoring.yaml`) and clearly separates it from the not-yet-built production Weather Safety Score model; `pages/AboutPage.tsx` covers the project, team roles, and data sources.
6. `/case-studies/helene` was redesigned headline-first and interactive: a hero verdict, a route switcher (tabs), a spotlight on the segment that drove the score, a clickable rail of every county stretch, and — new — an actual county choropleth map (`components/HeleneCountyMap.tsx`): real NC county boundaries (`frontend/public/nc_counties.geojson`, copied from `data/sample/nc_counties_2024.geojson`, Census TIGER), each county the route passes through colored yellow/orange/red by its concern level using the existing `--level-N-fg` tokens. Hover a county for a tooltip (name, band, rainfall); click one to sync with the county rail below. The full data table, known limits, and provenance are behind `<details>` instead of always open.
7. The header search bar is gone entirely (`components/HeaderSearchBar.tsx` and `contexts/HeaderSearchContext.tsx` were deleted). It duplicated the planner's own Origin field and did nothing on any other page — removed rather than left half-useful.
8. Content pages (Helene, Methodology, About, Prototype results) now have real side padding via a shared `.content-page` class — `.pivot-main` itself carries no padding, so text was running edge to edge before this.

Latest commit: `a52c31e`, pushed to `origin/Jeffrey`. Draft PR #17 should pick it up and run
CI. This handoff was then merged with Mason's branch (see the addenda below, one per merge
round) into `integration/mason-into-jeffrey`.

## How to run it

```
make api                # backend on :8000
cd frontend && npm run dev   # frontend on :5173, open http://localhost:5173
```

`make lint`, backend `uv run pytest -q` (not re-run this session, only frontend touched), and frontend `npm run test -- --run` / `npm run build` all pass clean on this branch as of `bb96db0`.

## What NOT to touch without flagging it to the team first

- **Product-safety colors**: `--level-0..3-bg/-fg`, `--level-none-bg/-fg`, `--route-current`, `--route-recommended` in `styles.css`. These are colorblind-safe risk semantics (a color is never the only signal — every colored element pairs with a text label, including the new county map's hover tooltip). Don't repurpose them for brand decoration.
- **Product language**: "Weather Safety Score" / "comparative decision index" / "lower modeled weather risk" — and never "safe route," "guaranteed safe," or similar. The disclaimers throughout the sidebar and map pages are worded carefully; don't edit the copy without checking `docs/build_guide.md` (or the CDC2026 CLAUDE.md) first.
- Canonical schemas (build guide §6.3) and repo structure (§4) — flag any change, don't just make it.

## Known gaps, not yet fixed

1. **Route-geometry/score matching**: `PlannerPage.tsx`, `LiveRoutePage.tsx`, and now `HeleneCaseStudyPage.tsx` each independently call `GET /api/v1/routing/route` (geometry) and a score endpoint, then match results by `route_id` string. This only works because both calls query OSRM the same way for the same coordinates — it's not a guaranteed-stable contract. Tracked in code comments; revisit once the backend ships a combined or verified-stable-ID response (backend team's own Priority 1 item).
2. **The Helene map's route line and geometry are live, not historical**: `HeleneCountyMap.tsx` fetches today's OSRM road geometry for the case study's real origin/destination — it does not and cannot show which roads were actually closed during the September 2024 storm. The page's copy and code comments say this explicitly; don't let a future edit imply otherwise.
3. **`/route`'s "similar risk" case**: when routes tie, they render in the primary chrome color rather than a distinct neutral — pre-existing logic in `LiveRoutePage.tsx`'s `routeColor()`, still untouched. Worth a look if it reads as "this route is recommended" by mistake.
4. **`/route` at very short viewports** (~860px tall): the map area has a 420px minimum height, so the page scrolls slightly. Fine for a dev preview; would want a fix before using this page live in front of judges (it isn't currently part of the staged demo path anyway).

## What's still open / not started

- Nothing else queued on the frontend right now.
- `main` has not been touched. Merging `Jeffrey` → `main` is a team decision, not something done unilaterally here.

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

---

# Addendum 2 — re-merged Jeffrey's newest 4 commits, 27 Sep 2026, ~09:50 EDT

Jeffrey kept working after the first merge (`085a5ca`): `b5bc7c2`, `6537ce0`, `bb96db0`,
`a52c31e`, landing `/about`, a real `/methodology` page, and a full rewrite of
`/case-studies/helene` (headline gauge, route tabs, click-to-reveal county rail, a new
`HeleneCountyMap.tsx`). None of it touched backend or `src/`, so this was a clean,
low-risk incremental merge on top of the integration branch.

- **`/case-studies/helene` no longer uses `ScoreDisplay.tsx`'s shared `RouteCard`** — it
  has its own bespoke layout and its own `HeleneCountyMap.tsx` now, replacing `RouteMap`/
  `ContributingFactorChips`/`AlertSummary` on that one page specifically. Those shared
  components are not dead code — `/results` still uses them via `RouteCard` — they're just
  no longer rendered on the Helene page. Jeffrey's newest UX won on that page, same
  precedent as the first merge.
- **One real bug this merge would have introduced, fixed during resolution**: the new
  `HeleneCaseStudyPage.tsx` defines its own `FACTOR_ICON` map for `contributing_factors`
  icons, typed `Record<'rain' | 'alert', string>` — written before the Bayesian merge
  landed `'historical'` as a third `kind`. Left as-is, this would have been a `tsc`
  compile error the moment both changes met (indexing a two-key `Record` with a
  three-value union). Fixed by adding `historical: '🕰️'` to that map, matching the glyph
  `ContributingFactorChips.tsx` already uses.
- `styles.css` auto-merged cleanly this round (no manual resolution needed, unlike the
  first merge).
- Jeffrey's own handoff note says **Draft PR #17** exists for `origin/Jeffrey` and should
  pick up CI — this integration branch is separate from that PR; worth flagging to Jeffrey
  so the two don't get confused about which one is the deploy target.
- Re-verified after this merge: see this file's own commit message for the actual test
  output — don't assume the first merge's verification still holds.
