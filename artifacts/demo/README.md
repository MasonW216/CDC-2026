# Cached demo scenario

Frozen inputs and outputs for the stage demo. Tracked in Git on purpose: the
presentation must work with the network down.

| File | Contains |
|---|---|
| `demo_routes.geojson` | Sampled candidate routes with county and arrival time per point |
| `demo_weather.json` | Weather inputs and official NWS alert payloads |
| `demo_scores.json` | Scored responses, exactly as the API returns them |

**Producer:** `make demo-cache` → [`scripts/cache_demo.py`](../../scripts/cache_demo.py),
configured by [`configs/demo.yaml`](../../configs/demo.yaml).

The scenario is **Asheville → Charlotte**, entirely inside North Carolina, during
the Hurricane Helene period. See
[ADR 0000](../../docs/adr/0000-specification-precedence.md) for why it is not
Asheville → Knoxville.

## Rules

- Never hand-edit these files. Regenerate them.
- After regenerating, copy the expected scores into
  [`docs/demo_runbook.md`](../../docs/demo_runbook.md) in the same commit.
- Checksums are recorded in each file and verified by `make verify`.
- Keep them small. If a file grows past a few hundred kilobytes, the sampling is
  too dense.

_Currently placeholders: valid, empty structures only._
