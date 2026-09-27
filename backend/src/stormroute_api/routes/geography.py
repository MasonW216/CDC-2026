"""North Carolina county boundaries, for map styling on the client.

    GET /api/v1/geography/counties

Serves `data/sample/nc_counties_2024.geojson` as-is: 100 features, `Polygon` geometry,
property `GEOID` is the 5-character county FIPS string -- the exact same value as
`SegmentScore.county_fips` in the score response, so the frontend can join a scored
segment to its county shape with no server-side spatial logic at all. Read once at import
time (module-level cache): the file never changes at runtime, so there is nothing to
recompute per request.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter

from stormroute.config import REPO_ROOT

router = APIRouter(prefix="/api/v1/geography", tags=["geography"])

_COUNTIES_FILE = REPO_ROOT / "data" / "sample" / "nc_counties_2024.geojson"
_counties_cache: dict[str, Any] | None = None


def _load_counties() -> dict[str, Any]:
    global _counties_cache
    if _counties_cache is None:
        _counties_cache = json.loads(_COUNTIES_FILE.read_text(encoding="utf-8"))
    return _counties_cache


@router.get("/counties")
def counties() -> dict[str, Any]:
    """Return the NC county boundary GeoJSON FeatureCollection, unchanged."""
    return _load_counties()
