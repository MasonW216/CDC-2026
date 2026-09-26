# ADR 0005 — Weather provider: ERA5-Land point time series + ASOS stations

- **Status:** Proposed (data already retrieved 2026-09-26; awaiting approval)
- **Date:** 2026-09-26
- **Proposed by:** Jeffrey
- **Resolves:** `weather.provider: TODO` in `configs/data.yaml`; `access_method: TBD` for `era5_land_hourly` in `data/data_manifest.yaml`

## Context

`configs/data.yaml` requires hourly precipitation, temperature, wind speed,
**wind gust**, and shallow and deep soil moisture for every county, 2015-2024,
and leaves the provider open (ERA5-Land directly or via Open-Meteo).

Options tested on 2026-09-26:

| Option | Result |
|---|---|
| Open-Meteo archive API (free tier) | Works, but 10,000 weighted calls/day; one county-decade costs ~260, so 100 counties take ~3 days |
| CDS ERA5-Land **gridded** (`reanalysis-era5-land`, NetCDF) | Queued jobs; large files; needs regridding and area-averaging per county |
| CDS ERA5-Land **point time series** (`reanalysis-era5-land-timeseries`) | **All 105 locations x 10 years retrieved in under an hour**, CSV, no queue problems |
| IEM ASOS archive | NC network, hourly, includes gusts, visibility, and present-weather codes |

ERA5-Land has **no wind-gust variable**, so gusts need a second source.

## Decision (proposed)

1. **ERA5-Land hourly point time series** from the Copernicus CDS
   (`reanalysis-era5-land-timeseries`), one request per county at the county's
   **Census Gazetteer internal point** (nearest 0.1 degree grid cell).
   Variables retrieved: `2m_temperature` (`t2m`, K), `total_precipitation`
   (`tp`, m per hour, de-accumulated), `snow_depth` (`sde`, m),
   `10m_u_component_of_wind` / `10m_v_component_of_wind` (`u10`, `v10`, m/s),
   `volumetric_soil_water_level_1` (`swvl1`, m3/m3). 87,672 hourly rows per
   county, 2015-01-01 00:00 to 2024-12-31 23:00 UTC, no missing values.
2. **IEM ASOS** (Iowa Environmental Mesonet, NC network, routine + special
   reports) for `wind_gust`, and as evidence for freezing rain, snow, fog, and
   thunder (present-weather codes) if ADR 0004 is accepted. Each county uses
   the nearest station with data in the window within 75 km, otherwise the
   feature is missing and flagged; distance to station is recorded.
3. **Soil moisture deep:** retrieve `volumetric_soil_water_level_2` the same
   way (one more short run) or drop `soil_moisture_deep` from
   `required_variables`. Team decision.

Raw layout (ignored by Git, shared outside the repo):

```text
data/raw/weather/era5_land_timeseries/{county_fips}.csv   # t2m, tp, sde, u10, v10
data/raw/weather/era5_land_soil/{county_fips}.csv         # swvl1
data/raw/weather/asos/                                     # IEM ASOS CSV(s)
```

## Consequences

- **A point is not a county average.** A single 9 km cell stands in for the
  whole county, which under-represents large or mountainous counties. State
  it in the data card; if time allows, add 2-3 points per large county and
  average.
- The `expected_file_pattern` in the manifest changes from
  `era5_land_{variable}_{year}.nc` to per-county CSVs.
- Unit conversions are part of `src/stormroute/data/weather.py`: `t2m - 273.15`,
  `tp * 1000` for mm, wind speed `sqrt(u10^2 + v10^2)`.
- ASOS values: `M` is missing, `T` (trace) is 0. Gusts are only reported when
  gusty, so "no gust reported" is not "gust = 0"; use `max(gust, wind speed)`.
- Retrieval script to be ported into `scripts/fetch_weather.py` so
  `make download` reproduces it (a working prototype exists outside the repo).
- The same Copernicus Licence attribution applies (README section 13).

## Alternatives considered

- **Open-Meteo:** same underlying reanalysis, but too slow on the free tier for
  the deadline.
- **Gridded CDS + area-average:** more faithful county averages, much slower to
  retrieve and process. Worth revisiting after the hackathon.
- **ASOS only:** measured, but many counties have no station.
