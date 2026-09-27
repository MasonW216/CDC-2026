"""Pydantic request model for the trip score endpoint.

The response is the `prototype-score/1` contract from
`stormroute.scoring.concern` / `stormroute.scoring.trip`, mirrored for the frontend in
`frontend/src/types/score.ts`. It is returned as a plain dict (FastAPI serializes it
as-is): the scoring module is the single source of truth for that shape, so it is not
re-declared here as a second Pydantic model that could drift from it.

This supersedes the milestone-6 production `ScoreResponse` sketch (0-100 calibrated
Weather Safety Score, model/data version, confidence report) that the docstring here
used to describe. That contract returns once a trained, calibrated model exists
(see docs/build_guide.md); tonight's endpoint serves the prototype index instead, per
the MVP brief.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Location(BaseModel):
    """A named point: a label for display plus WGS84 coordinates."""

    label: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class TripRequest(BaseModel):
    """Body of `POST /api/v1/trips/score`. Mirrors `frontend/src/types/trip.ts`."""

    origin: Location
    destination: Location
    departure_time: datetime
    mode: Literal["live", "cached_replay"] = "live"

    @field_validator("departure_time")
    @classmethod
    def _tz_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError(
                "departure_time must include a UTC offset, e.g. ...+00:00 or ...-04:00"
            )
        return value
