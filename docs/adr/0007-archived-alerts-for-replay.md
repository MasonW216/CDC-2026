# ADR 0007 — Archived NWS alerts for the Helene replay

- **Status:** Proposed (data already retrieved 2026-09-26)
- **Date:** 2026-09-26
- **Proposed by:** Jeffrey

## Context

The score applies official NWS products as a risk floor
(`configs/scoring.yaml`). The manifest lists the live NWS API as the alert
source, but `api.weather.gov` only serves **currently active** alerts. The
judged demo is a historical replay (ADR 0003), so it needs the alerts that were
active in September 2024.

## Decision (proposed)

Use the **Iowa Environmental Mesonet (IEM) VTEC archive** of NWS watches,
warnings, and advisories for replay scenarios:

- Retrieved 2026-09-26 via https://mesonet.agron.iastate.edu/request/gis/watchwarn.phtml,
  events **starting** 2024-09-22 00:00 to 2024-10-01 00:00 UTC, with follow-up
  statement polygons included.
- **NC:** 1,856 records (flood watch, flash flood warning, flood warning,
  tornado, tropical storm, wind, and others).
- **TN:** 884 records (retained in case a Tennessee scenario is added; the
  showcase route is NC-only per ADR 0000).
- Raw path: `data/raw/nws_alerts_archive/helene_{nc,tn}.zip` (shapefile + CSV).
- VTEC `SIG` maps to floors: `A` watch 0.35, `Y` advisory 0.50, `W` warning
  0.80, `IS_EMERGENCY` 0.98. A segment's floor uses alerts whose polygon
  contains the point and whose issue-to-expire interval covers the arrival time.

## Consequences

- `scripts/cache_demo.py` reads this archive (not the live API) when building
  replay scenarios; live mode still uses `api.weather.gov`.
- Start the retrieval window 2 days before the storm, since watches are often
  issued before rain begins.
- Add the dataset to `data/data_manifest.yaml`.
