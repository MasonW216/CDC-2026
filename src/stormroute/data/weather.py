"""Load hourly reanalysis weather and align it to county-hours.

Turns raw ERA5-Land output into a county-by-hour table that
`features.rolling_weather` can consume.

This module is the train-serve boundary: it reads retrospective reanalysis,
while a live deployment would read forecasts. Any change to the variable set
or aggregation here invalidates the model card's coverage claims. See
`docs/adr/0003-reanalysis-live-forecast-boundary.md`.
"""

# TODO(milestone-3): implement. See docs/build_guide.md.
