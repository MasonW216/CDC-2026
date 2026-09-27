# MVP narration draft (about 80 seconds)

Rewritten 27 Sep 2026 for the live-first product. Every claim checked against a real run
tonight (browser + API), not assumed. Rehearse before presenting — timing and exact phrasing
still need a run-through.

"StormRoute lets a traveler enter a trip — an origin, a destination, and a future departure
time anywhere in North Carolina — and see the fastest driving route alongside the route with
the lowest indicated weather concern at the times they'd actually travel.

[Type a real place into the planner, submit.] This is live: real routing from OpenStreetMap,
a real weather forecast, and real official flood alerts from the National Weather Service, all
fetched right now and scored by a transparent prototype rule. For each county a route passes
through, we look at the forecast rainfall and any active flood watch, advisory, or warning. The
higher of the two sets that stretch's indicated concern, from lower to severe. An alert can only
raise it — never lower it.

Tonight, North Carolina's forecast is dry statewide, so this live result honestly comes back as
lower concern on both routes, and the comparison correctly says it doesn't favor one — that's
the real pipeline telling the truth, not a placeholder.

To show what a higher-concern result looks like, here's a separate replay of Hurricane Helene:
Asheville to Charlotte, September 2024. Both routes come out at severe concern — Buncombe County
saw 233 millimeters of rain in 24 hours with active flash flood warnings — and the advisory is
to consider delaying and to check official guidance.

What this is not: it is not a trained model, not a calibrated flood probability, and not a
validated safety score. It's a transparent, published formula — the rainfall thresholds and
alert weights are our own stated policy, not learned from data. Historical reanalysis, like the
Helene replay, is never fed into the live trip flow; only real-time forecasts are. One point
stands in for a whole county, and this does not say a road is open or safe.

The next scientific step is the part already underway: a reviewed exploration of ten years of
North Carolina flood reports, then a historical weather table, baselines, calibration, and one
held-out test on 2024 — before any number here is called a risk."
