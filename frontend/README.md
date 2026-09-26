# StormRoute web

React + TypeScript + Vite website: trip planner, results, and methodology.

**Status: scaffold.** Configuration is complete; every component, page, and
test is a documented stub. Built in Milestone 7, after the API contract exists.
See [docs/build_guide.md](../docs/build_guide.md).

## Run

```bash
make setup   # from the repository root; installs everything
make web     # http://localhost:5173
```

`/api` and `/health` are proxied to the API on port 8000 during development.
In production, FastAPI serves the built `dist/` directly: one service, one URL.

## Scripts

| Command | Does |
|---|---|
| `npm run dev` | Vite dev server on 5173 |
| `npm run build` | Type-check, then production build to `dist/` |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run lint` | ESLint, zero warnings allowed |
| `npm run test` | Vitest unit and component tests |
| `npm run test:e2e` | Playwright cached-demo flow |

## Layout

```text
src/
  main.tsx, App.tsx     entry point and routes
  pages/                Planner, Results, Methodology
  components/           score, map, segment, recommendation, alert, confidence, methodology
  services/api.ts       typed API client
  types/trip.ts         mirror of the backend wire contract
  fixtures/             demoScore.json — lets the UI be built before the API exists
  test/                 Vitest component tests
e2e/                    Playwright end-to-end demo flow
```

## Build order

1. Build every view against `src/fixtures/demoScore.json` first.
2. Switch to the live API only after the contract in `types/trip.ts` matches
   `backend/src/stormroute_api/schemas.py`.
3. Keep the fixture working forever: it is the fallback when the API is down.

## Non-negotiable product rules

These are acceptance criteria, not style preferences.

- **A score never appears without its meaning.** Band, what the number
  measures, and limitations are always on screen with it.
- **The top band is never called "Safe".** It is "Lower modeled weather risk".
- **Official guidance outranks the model.** When an NWS alert intersects the
  route, it renders above any recommendation, and looks different from model output.
- **Risk is never encoded by color alone.** Every level also has a label, icon,
  or pattern.
- **Every recommendation shows both the gain and the cost.** Before score, after
  score, delta, and added time — together.
- **"No safer option found" is a real result**, rendered with a pointer to
  official guidance, never as an empty state or an error.
- **All five data states render honestly:** loading, empty, success,
  partial-data, and failure.
- **Keyboard-navigable, WCAG AA contrast, works at laptop and phone widths.**
- **Attribution is visible:** © OpenStreetMap contributors, NOAA, NWS.
