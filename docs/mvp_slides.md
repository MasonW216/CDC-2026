# MVP slide outline (5 slides, about 90 seconds of talking plus the live page)

Text is draft. Every number comes from `artifacts/demo/prototype_result.json` or
`reports/eda/eda_findings.md`. Cameron checks each claim before 08:00.

## 1. The problem
- Flooding on North Carolina roads depends on where you are and when you get there.
- StormRoute compares routes and departure times by flood-related weather exposure.
- Onscreen: the Asheville to Charlotte route, Hurricane Helene replay, 27 Sep 2024, 12:00 EDT.

## 2. What we built (live: `artifacts/demo/results.html`)
- Route split into county stretches with expected arrival times.
- A prototype hazard indicator per stretch: the higher of trailing rainfall and active NWS
  flood products. Levels: lower, elevated, high, severe concern.
- Official alerts shown above the advisory. Alerts can raise the level, never lower it.

## 3. The result
- Both routes: severe concern. Highest-concern stretch: Buncombe (233 mm in the prior 24 h,
  active flash flood warnings).
- Advisory: consider delaying travel; check official warnings and DriveNC closures.
- Same saved scenario, same output, no external services.

## 4. What this is not
- Not a trained model, a probability, or a validated score.
- Rainfall is reanalysis a traveler would not have had at departure. Thresholds are our own
  round numbers. Some zone-coded watches are missing. One rainfall point per county.
- It does not say a road is open or safe.

## 5. What is real, and what comes next
- Real: ten years of NC flood reports (2,220 events, 1,499 positive county-windows out of
  1,461,200), a reviewed exploration with a spot check of ten events, and an as-of alert rule.
- Next, in order: close the review gate, build the historical weather table, baselines,
  calibration, a held-out 2024 test, route-level sensitivity checks.
