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

Latest commit: `6537ce0`, on `Jeffrey` (not yet pushed this session — push before opening/refreshing draft PR #17).

## How to run it

```
make api                # backend on :8000
cd frontend && npm run dev   # frontend on :5173, open http://localhost:5173
```

`make lint`, backend `uv run pytest -q` (not re-run this session, only frontend touched), and frontend `npm run test -- --run` / `npm run build` all pass clean on this branch as of `6537ce0`.

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
