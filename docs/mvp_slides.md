# MVP slide outline (5 slides, about 90 seconds of talking plus the live page)

Verified wording for the offline historical replay. Numerical claims below trace to
`artifacts/demo/prototype_result.json` or `reports/eda/eda_findings.md`. This is a
Markdown outline; the final rendered deck still needs a visual check.

## 1. The problem
- Flood-related conditions can differ along a trip and across time.
- This historical replay compares two Asheville-to-Charlotte routes for **one** departure:
  27 Sep 2024, 12:00 EDT (16:00 UTC). It does not compare departure-time options.

## 2. What we built (live: `artifacts/demo/results.html`)
- Provisional routes split into county stretches with estimated arrival times.
- A prototype hazard indicator per stretch: the higher of trailing rainfall and active NWS
  county-coded flood-product tiers. Levels: Lower, Elevated, High, Severe concern.
- The HTML page places retained official alerts above the advisory. An alert can raise
  the level, never lower it.

## 3. The result
- Both routes: **Severe concern**. Buncombe is the first of several Severe stretches;
  its 24-hour rainfall window ending 12:00 UTC totals 232.6 mm (rounded to 233 mm),
  and flash flood warnings are active. Neither route has a lower indicator level.
- The rule advises considering a delay and following official warnings and road closures.
- The replay reads cached files and produces byte-identical output on repeated offline runs.

## 4. What this is not
- A **rule**, not a trained model, flood probability, or validated score. Its rainfall
  thresholds are illustrative round numbers.
- ERA5 rainfall was retrieved in 2026. Later stretches use rain through 18:00 UTC,
  two hours after departure. One sample point represents each county; no road closure
  or passability is assessed.
- Ninety-two zone-coded alert rows are not mapped to counties, and original alert
  expiry can miss extensions known before departure. GSP-66 raises Mecklenburg to
  Severe despite only 43.9 mm of 24-hour rainfall at its 18:00 UTC window.
- This indicator does not establish whether any road is open or safe.

## 5. What is real, and what comes next
- The **draft** EDA includes 2,220 qualifying NC reports and 1,499 positive
  county-windows out of 1,461,200 (2015–2024). A ten-record source check is a
  preliminary check; Mason's confirmation and the EDA gate decision remain open.
- Next: close that gate; build the historical county × six-hour weather table with
  as-of availability checks; define baselines and acceptance criteria before training;
  select on 2022, calibrate on 2023, then run one frozen 2024 test. The 53 and 78
  positives in 2022 and 2023 constrain interpretation. Check route sensitivity to
  weather points, county joins, alerts, and storms before live-planning claims.
