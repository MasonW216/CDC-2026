# Demo Runbook

> **Owner:** CS major (reliability) · Mason (narrative) · **Milestone:** 9
>
> Skeleton. Expected values are filled in from `artifacts/demo/demo_scores.json`
> every time `make demo-cache` runs.

**Verification status:** this is a planned checklist. Offline operation, fallback
behavior, and the click sequence have not been demonstrated by the sample EDA.
Do not describe the demo as reliable or working offline until the CS owner
records a successful rehearsal with versioned artifacts.

## Before going on stage

| Check | Command / action | Owner |
|---|---|---|
| Services up | `make api` and `make web`, or the deployed URL | CS |
| Health green | `GET /health` reports model ✅ and demo artifacts ✅ | CS |
| Offline proof | Disable wifi; run the full click sequence once | CS |
| Browser | Fresh profile, zoom 100%, notifications off | CS |
| Backup | Screen recording of the full flow on the presenting laptop | CS |

## Click sequence

| # | Action | Expected on screen |
|---|---|---|
| 1 | Open planner | Form, safety disclaimer visible |
| 2 | Origin: Asheville, NC | |
| 3 | Destination: Charlotte, NC | |
| 4 | Departure: 2024-09-27 12:00 EDT | |
| 5 | Analyze trip | Score **_TBD_**, band **_TBD_** |
| 6 | Point to the alert banner | Official guidance above the recommendation |
| 7 | Point to worst segment | County **_TBD_**, arrival **_TBD_** |
| 8 | Point to recommendation | **_TBD_ → _TBD_ (+_TBD_)**, time cost **_TBD_** |
| 9 | Open methodology | Formula, sources, limitations |

## If something fails

| Failure | Recovery | Owner |
|---|---|---|
| API unreachable | Frontend falls back to `src/fixtures/demoScore.json` | CS |
| Map tiles fail | Segment list carries the same information | CS |
| Laptop fails | Backup laptop, same branch, cached mode | CS |
| Everything fails | Play the screen recording; narrate live | Mason |

## Reset

_TBD — exact steps to return to a clean planner state between runs._
