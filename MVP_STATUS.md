# MVP status (Saturday 26 Sep 2026, late evening)

Written from Mason's checkout of `Mason` (which contains `main`, Cameron's and Jeffrey's
work). Verified by running it, not by reading it.

## What runs today

| Piece | State |
|---|---|
| Routing (OSRM client, route sampling, county join) | Runs. Two real Asheville to Charlotte routes come back and split into county stretches with arrival times. |
| County boundaries | Sample fixture (simplified, about 1 km coarse) runs offline. |
| EDA notebook and NOAA event ingestion | Runs, 227 tests pass. Not part of the demo path. |
| Prototype hazard indicator (new) | Runs offline. `scripts/run_prototype.py` writes `artifacts/demo/prototype_result.json`, identical on repeat runs. |
| Cached Helene inputs (new) | `artifacts/demo/prototype_inputs_helene.json`: rainfall for all 100 counties and county-coded NWS flood products. |
| Backend score endpoint | **Stub.** `routes/score.py` is 12 lines, no scoring. |
| Results screen | **Not built.** `frontend/src/fixtures/demoScore.json` is an empty placeholder. |
| Trained model, calibration, held-out evaluation | **None.** Not part of the MVP. |

## What the indicator is

A rule, not a model. Highest of (trailing rainfall tier, active NWS flood product tier), per
county stretch. Levels: Lower / Elevated / High / Severe concern. The thresholds are round
numbers picked by the team. It is not a probability, not calibrated, and not validated.
Label it "prototype hazard indicator" everywhere.

## Contract for the results screen (Jeffrey)

Read `artifacts/demo/prototype_result.json`. Example of one segment in and out:
`artifacts/demo/prototype_contract_example.json`.

Per route: `trip_label`, `highest_concern_segment` (county, arrival, reason), `advisory`,
`segments[]` (each with `county_name`, `arrival_utc`, `label`, `reason`, `sources`,
`data_status`, `alerts_used`), `duration_minutes`, `distance_km`, `replay_caveat`.
Top level: `comparison` (two routes, same rule, same inputs), `inputs_provenance`.

Show `replay_caveat` and `inputs_provenance` on screen. Official alerts appear above the
recommendation.

## Known limits (say them out loud)

- Replay of a past storm. Rainfall is ERA5 reanalysis, which a traveler would not have had at
  departure. NWS alerts use their original expiry and only those issued before departure.
- 92 zone-coded alert rows are not mapped to counties, so some watches are missing.
- One rainfall point per county.
- Both routes come out "Severe concern" for a 12:00 departure, so the comparison offers no
  better alternative. That is the honest result, not a bug.
- The route fixture (`prototype_routes_provisional.json`) is mine. Jeffrey's frozen fixture
  replaces it: pass `--routes` to `scripts/run_prototype.py`.

## Run it

```bash
PYTHONPATH=src .venv/bin/python scripts/run_prototype.py
```

Needs no network. `scripts/build_prototype_inputs.py` rebuilds the cached inputs and does.

## Demo command and owner

Proposed, to agree at the huddle: integration owner Jeffrey, demo command to be added here
once the results screen exists, feature freeze 06:00.
