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
accumulation over the hour before T, as Open-Meteo reports it (UTC).

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

The route index is a maximum, so splitting a stretch into pieces cannot change it.
It does not reward a long exposure over a short one; report `minutes_at_or_above_50` next
to it.

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

## Comparison

- `single_route`: OSRM returned one route. No alternative is invented.
- `unavailable`: any route is not `assessed`.
- `tie`: index difference under 5 points. Say so; do not name a lower-concern route.
- `distinguishable`: difference of 5 points or more. Name the lower-concern route, the added
  minutes against the fastest route, and the index difference.
- If the lower index is still 80 or above: "neither route avoids the warnings or heavy
  rain; check official guidance or consider delaying."

The fastest route is the smallest `duration_minutes`; a tie in minutes goes to the first
route returned.

## Fixed limitations to display

Forecasts are uncertain and can be wrong. The index does not know road closures, drainage,
or terrain. A missing alert is not a guarantee that none exists. Alerts issued after the
request are not seen. One forecast point per county. Not a calibrated flood probability.
