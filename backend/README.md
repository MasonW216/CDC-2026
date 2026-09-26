# StormRoute API

FastAPI service that turns a trip request into a Weather Safety Score, an
explanation, and ranked alternatives.

**Status: scaffold.** Every module here is a documented stub. The service is
built in Milestone 6, after the EDA gate, the data pipeline, the model, and the
scoring engine exist. See [docs/build_guide.md](../docs/build_guide.md).

## Run

```bash
make api     # uvicorn on http://localhost:8000
```

Interactive OpenAPI docs at `http://localhost:8000/docs`.

## Planned endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness, plus whether the model artifact and demo assets are present |
| `GET` | `/api/v1/scenarios` | List the cached replay scenarios |
| `GET` | `/api/v1/scenarios/{scenario_id}` | One frozen scenario, no network required |
| `POST` | `/api/v1/trips/score` | Score a trip and return alternatives |
| `GET` | `/api/v1/methodology` | Data sources, model summary, score formula, limitations |

### Example request

```json
{
  "origin": {"label": "Asheville, NC", "lat": 35.5951, "lon": -82.5515},
  "destination": {"label": "Charlotte, NC", "lat": 35.2271, "lon": -80.8431},
  "departure_time": "2024-09-27T12:00:00-04:00",
  "mode": "cached_replay"
}
```

## Layout

```text
src/stormroute_api/
  main.py            app creation, routers, CORS, static frontend
  config.py          settings from the environment
  dependencies.py    request-scoped model, cache, and services
  schemas.py         the versioned wire contract
  routes/            health, score, scenarios
  services/          model, route, weather/alerts, cache
tests/               health, score contract, offline demo replay
```

## Design rules

- **No scoring logic here.** Formulas live in `stormroute.scoring`. This layer
  is transport: validation, versioning, caching, errors, logging. A formula
  duplicated across both packages is a formula that will diverge.
- **Every response is versioned** with the model and data version it came from.
- **A score never ships without its meaning** — band, confidence, and
  limitations travel with it.
- **Official alerts outrank the model.** An alert can only raise risk.
- **Cached replay must work with the network off.** That is a test, not an
  aspiration: see [tests/test_demo_scenario.py](tests/test_demo_scenario.py).
- **CORS is an explicit allowlist**, never `*`.
- **Secrets never appear** in a response or a log line.
