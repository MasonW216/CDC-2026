"""Hurricane Helene case study: a standalone historical demo page's data.

    GET /api/v1/demo/helene

Returns the `prototype-score/1` response for the Helene Asheville-Charlotte replay,
`mode: "historical_case_study"`, scored by the exact same rule as a live trip
(`stormroute.scoring.historical_case_study.helene_case_study`). No request body, no network,
deterministic: every call returns byte-identical JSON.

Not part of the live trip flow and not reachable from `POST /api/v1/trips/score` --
historical reanalysis rainfall must never feed a live-mode request, per the MVP brief. This
is a separate page's data source precisely so the two can never be confused in the UI.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from stormroute.scoring.historical_case_study import helene_case_study

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])


@router.get("/helene")
def helene() -> dict[str, Any]:
    """Return the Helene case study response, computed fresh from cached inputs each call."""
    try:
        return helene_case_study()
    except (OSError, KeyError, ValueError) as error:
        raise HTTPException(
            status_code=503, detail=f"Helene case study data unavailable: {error}"
        ) from error
