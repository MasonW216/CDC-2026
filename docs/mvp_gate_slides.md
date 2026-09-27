# MVP replay: limitations and next steps

These are slide-ready words for the September 2026 MVP. The repository does not
yet contain a presentation deck; copy these into the deck and verify the final
rendered slide before presenting.

## Slide: What the Helene replay can show

- **A prototype indicator, not a forecast.** Round rainfall and archived-alert
  tiers are not a trained model, flood probability, or validated score.
- **Both routes are Severe concern.** The shorter route is 13 minutes faster,
  but the indicator finds no lower-concern route. It does not know road closures.
- **Historical inputs limit the claim.** ERA5 rainfall was retrieved in 2026;
  later stretches include rain after the 2024 departure. One point represents
  each county. The provisional route geometry has not been independently checked.
- **Alerts are incomplete.** The archive uses original expiry; extensions made
  before departure can be missed. Ninety-two zone-coded rows are not assigned
  to counties. GSP-66 raises Mecklenburg to Severe despite modest rain.

Presenter note: follow current NWS warnings and DriveNC road closures. Do not
call this a safe route, live prediction, or measured improvement.

## Slide: Scientific next steps

1. Close the independently reviewed EDA gate and record proceed/change-scope/stop.
2. Build the historical county × six-hour weather table with an explicit
   departure-time availability audit and weather-to-county sensitivity checks.
3. Define and train climatology and logistic baselines before a candidate model;
   compare PR-AUC with prevalence, Brier score, useful precision/recall, and
   county/season/storm slices with uncertainty grouped by episode.
4. Use 2022 only for selection and 2023 for calibration; interpret both cautiously
   because they contain few positive county-windows. Keep 2024 untouched for one
   frozen final test.
5. Test route-level sensitivity to county assignment, weather point, alert
   coverage, and forecast versus reanalysis before making live-planning claims.
