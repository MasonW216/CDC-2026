# Frontend handoff — Jeffrey branch (2026-09-27)

## Where things stand

`Jeffrey` is well ahead of `main` (`main` is stuck at `3f0cbba`, before the rebrand). This branch has:

1. The project renamed **PIVOT**, with the real brand mark wired in (`frontend/src/assets/pivot-icon.png`, `pivot-logo-full.png`, used by `components/PivotLogo.tsx`).
2. A full Uber-inspired visual pass: black/white chrome, bold pill buttons, a black header, a hero map with floating chrome (zoom, legend, status), custom trip-endpoint markers. Tokens live in `frontend/src/styles.css`.
3. `/` restored as a single-page sidebar + map planner (`pages/PlannerPage.tsx`), not a separate form → results flow.
4. Mason's real pages kept and reachable at their own routes: `/results` (`PrototypeResultsPage.tsx`), `/case-studies/helene` (`HeleneCaseStudyPage.tsx`), `/route` (`LiveRoutePage.tsx`, a dev-only live preview — hits the rate-limited public OSRM server directly, never use it for the staged demo).

Latest commit: `b2292cc`, pushed to `origin/Jeffrey`.

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

- Nothing else queued on the frontend right now — the Uber rebrand was the active task and it's complete and verified (lint, tests, build, and a real-browser Playwright pass with zero console errors in both light and dark mode).
- `main` has not been touched. Merging `Jeffrey` → `main` is a team decision, not something done unilaterally here.
