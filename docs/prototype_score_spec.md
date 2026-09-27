# Prototype weather-concern index: specification v1

Version `prototype-score/1`. Written before the code. Change it here first, bump the
version, then change the code and `frontend/src/types/score.ts` together.

## What it is, and is not

An index from 0 to 100 for **comparing route options under the same rule and data**.
Higher means more indicated weather concern. It is not a probability of road flooding, a
guarantee of safety, a validated score, or evidence of reduced harm. Show it with the label
"prototype". It is a team policy, not a learned quantity.

## Inputs, per county stretch of a route

A stretch is one county, entered at `arrival_utc`, lasting `minutes`. The routing code
supplies it.

| Input | Source | Definition |
|---|---|---|
| `rain_rate_mm_h` | Open-Meteo forecast API | Peak hourly precipitation over the hours the stretch overlaps |
| `rain_24h_mm` | same | Sum of hourly precipitation over the 24 h ending at the last overlapped hour |
| official alerts | NWS `api.weather.gov` active alerts | Flood products valid at any time during the stretch, matched by county (SAME code) |

Forecast point: one representative point per county. Precipitation at hour T is the
accumulation over the hour before T, as Open-Meteo reports it (UTC). Each stretch reports
`rain_peak_window_utc` and `rain_24h_window_utc`, the exact hourly stamps `rain_rate_mm_h`
and `rain_24h_mm` were read from, for an audit trail back to the raw forecast; both `null`
together with the rain terms when there is a coverage gap.

**Route identity.** `route_id` is derived from a route's own content (distance, duration, a
sample of its geometry), not its position in an OSRM response. Two independent OSRM calls
for the same trip (the score endpoint and the map preview each fetch separately) are not
guaranteed to return alternatives in the same order; a content-derived ID means the same
physical route gets the same ID from either call, so `route_id` reliably links a scored
route to the geometry drawn on the map. A UI must match routes between the two endpoints by
this ID, never by array position.

## Rule

```
rain_component  = 100 * min(1, max(rain_rate_mm_h / 20, rain_24h_mm / 100))
alert_component = highest floor among valid flood products, else 0
segment_index   = round(max(rain_component, alert_component))
route_index     = max(segment_index over assessed stretches)
```

Alert floors are `configs/scoring.yaml` `alerts.floors` times 100:
Flood Watch / Flash Flood Watch 35, Flood Advisory 50, Flood Warning and Flash Flood
Warning 80, Flash Flood Emergency 98. An alert can only raise a stretch's index: the index is a
maximum, so no alert and no worse weather can lower it. Coastal flood products are out of
scope for v1 (ADR 0004: flood hazards only).

Bands: 0-24 Lower concern, 25-49 Elevated concern, 50-79 High concern, 80-100 Severe concern.
No band is called "safe".

**Worked example.** Peak rain 5 mm/h, prior-24-hour rain 30 mm, an active Flood Watch
(floor 35):

```
rain_component  = 100 * min(1, max(5 / 20, 30 / 100)) = 100 * min(1, max(0.25, 0.30)) = 30
alert_component = 35
segment_index   = round(max(30, 35)) = 35
```

The alert, not the rain, sets the index here; this is the ordinary case, not a special one.

The route index is a maximum, so splitting a stretch into pieces cannot change it. **It is
not duration-weighted**: a 5-minute stretch through a Severe county and a 3-hour stretch
through the same county contribute the same route index. `minutes_at_or_above_50` is
reported alongside it as separate exposure-duration context, never folded into the index
itself; a UI must not describe the index as accounting for how long the concern lasts.

## Coverage and missing data

A stretch is **assessed** only if forecast hours cover it and the 24 h before it. Otherwise it
is `unassessed` with a reason, and its index is `null`, never 0. Departure must be in the
future and its arrival hours within 72 h of the request (`horizon_hours`), and the route
must lie in North Carolina. A route is:

- `assessed`: every stretch assessed and alerts fetched;
- `partial`: some stretch unassessed, or the alert feed failed;
- `unassessed`: nothing could be assessed.

A `partial` or `unassessed` route makes the comparison `unavailable` (no confident ranking).
`route_index` for a partial route is a lower bound: report it as such, never as the score.

**Freshness policy.** When a live fetch fails and a cached response is used instead, that
cache is only served if it is younger than 3 hours (forecast) or 30 minutes (alerts);
older than that, it is refused exactly as if no cache existed (forecast: `ForecastError`,
all dependent stretches unassessed; alerts: `ok: false` with an explanatory `error`, same
as a live alert-service failure). This never applies to an explicit saved-replay request
(`offline=True`, e.g. `replay_saved_trip`), which may stay old on purpose for
reproducibility. `coverage.forecast.age_minutes` and `coverage.alerts.age_minutes` report
the age directly so a UI does not have to compute it, and `retrieved_utc` remains the
timestamp to display.

## Comparison

- `single_route`: OSRM returned one route -- a normal result (OSRM does not guarantee an
  alternative exists), not an error and not a reason to invent a second route. The routing
  layer only fails on zero routes.
- `unavailable`: any route is not `assessed`.
- `tie`: index difference under 5 points. Say so; do not name a lower-concern route.
- `distinguishable`: difference of 5 points or more. Name the lower-concern route, the added
  minutes against the fastest route, and the index difference.
- If the lowest index among the routes shown is still 80 or above: severe advice is
  attached regardless of ranking (including on a single route or an `unavailable` result),
  worded for how many routes there are -- "this route does not avoid..." for one, "none of
  the routes avoid..." for more than one.

The fastest route is the smallest `duration_minutes`; a tie in minutes goes to the first
route returned.

## Contributing factors (`contributing_factors`)

Up to 3 of a route's highest-index stretches, each tagged `kind: "rain"` or `kind: "alert"`
by which component actually set that stretch's index, for a UI icon or label. **A factor
can only be built from a field this rule already computes** (`rain_rate_mm_h`,
`rain_24h_mm`, the matched alerts): never a fixed list, never an input this rule does not
read. A UI must not invent a factor such as "saturated ground" unless a real soil-moisture
input is added here first, with its own row in the Inputs table above and its own test.

## Better departure (`better_departure`)

After scoring the requested departure, the same routes are rescored at later offsets
(1, 2, 3, 4, 6, 8, 10, 12 hours) by shifting every stretch's `arrival_utc` by that offset
and nothing else: drive time does not depend on time of day here (no live-traffic model),
so this needs no new OSRM call, and it reuses the one forecast and alert fetch already
made for the request. `null` unless an offset lowers the best fully-`assessed` route's
index by at least the tie margin (5 points) — the same margin `compare` uses, so "better"
means the same thing everywhere in this contract. Never recommends a departure that trades
a real number for a coverage gap: only offsets where the route is still fully `assessed`
are considered. Drive time (`duration_minutes`) does not change between offsets; say so
when displaying a delta.

## Route geometry (`RouteScore.geometry`)

Additive field: `[[lon, lat], ...] | null`, the real road polyline for that route (OSRM
convention, matching `GET /api/v1/routing/route`'s coordinate order). Does not affect the
score -- attached to an already-scored route as the last step of `build_response`, never
threaded into `RouteInput`/`Stretch`/`score_route`/`score_segment`.

- `mode: "live"`: taken directly from the OSRM data already fetched during scoring
  (`CandidateRoute.coordinates`) -- no second network call.
- `mode: "cached"` / `"historical_case_study"`: baked into the fixture JSON once, alongside
  `stretches`, under a `"geometry"` key per route (see `geometry_from_fixture`). These pages
  stay fully offline and deterministic; the geometry is real, just captured in advance.
- `null` means no real geometry is available for this route. A UI must fall back to a
  schematic line through the segment county centers and say so, never draw nothing and never
  claim a schematic line is the real road.

## County boundaries (`GET /api/v1/geography/counties`)

Serves `data/sample/nc_counties_2024.geojson` unchanged: 100 features, `Polygon` geometry,
property `GEOID` (5-character county FIPS) matching `SegmentScore.county_fips` exactly, so a
client joins a scored segment to its county shape with no server-side spatial logic. Static
data, cached in memory at import time, no request parameters.

## Historical case study (`GET /api/v1/demo/helene`)

A standalone, non-live demo page's data source: the Hurricane Helene (Sep 2024)
Asheville-Charlotte replay, scored by this exact rule (`build_response`, the same function
`score_trip` uses), fed ERA5 reanalysis rainfall and archived NWS alerts instead of live
Open-Meteo/NWS data. `mode: "historical_case_study"` is the only thing distinguishing it from
a live response -- same schema, same fields, same formula. `stormroute.scoring.trip` (the live
path) never imports this module; the dependency runs one way, enforced by
`tests/scoring/test_historical_case_study.py::test_never_mixes_into_a_live_response`.

Never reachable from `POST /api/v1/trips/score`: this is a deliberate second endpoint so a
live request can never be served historical reanalysis, per the brief ("historical reanalysis
rainfall is not a live forecast and must not be fed into the live trip flow"). A UI must
visually and textually distinguish this page from the live planner -- it is a case study, not
a trip result.

## Fixed limitations to display

Forecasts are uncertain and can be wrong. The index does not know road closures, drainage,
or terrain. A missing alert is not a guarantee that none exists. Alerts issued after the
request are not seen. One forecast point per county. Not a calibrated flood probability.
`better_departure` assumes traffic conditions do not change with departure time.
