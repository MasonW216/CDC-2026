"""Plain-language methodology statement for the prototype weather-concern index.

    GET /api/v1/methodology

Static content, not derived from a request: the same honest statement every time,
matching `docs/prototype_score_spec.md` word for word on the rule and limitations, so
the two never drift apart silently (`test_methodology.py` checks that alignment).

This is the "honest methodology statement" the MVP brief asks Mason to supply, for the
frontend's methodology page (currently a placeholder in `App.tsx`) and for the
presentation. It describes tonight's prototype rule only, not the eventual calibrated,
historical model.
"""

from __future__ import annotations

from fastapi import APIRouter

from stormroute.scoring.concern import (
    ACCUM_FULL_SCALE_MM,
    HORIZON_HOURS,
    LIMITATIONS,
    RATE_FULL_SCALE_MM_H,
    SCHEMA_VERSION,
    SCORE_NAME,
    SEVERE_INDEX,
    TIE_POINTS,
)

router = APIRouter(prefix="/api/v1", tags=["methodology"])

SUMMARY = (
    "StormRoute lets a traveler enter a trip and see the fastest driving route alongside "
    "the route with the lowest indicated weather concern at the times they would travel. "
    "For this MVP, the score is a transparent prototype rule using forecast conditions and "
    "official alerts. We show the source, timing, and coverage of those inputs. We have "
    "not established that the index predicts road flooding or prevents harm."
)

WHAT_IT_IS_NOT = (
    "Not a probability of road flooding, a guarantee of safety, or proof of reduced "
    "crashes, deaths, or property damage. Not a trained or calibrated model: the "
    "eventual research plan is a calibrated, historical flood-event model evaluated on "
    "held-out years, which is not yet implemented or validated. A retrospective replay "
    "(for example, of Hurricane Helene) shows how the prototype ranked tested routes, "
    "not what would have happened to travelers."
)

RULE_STEPS: tuple[str, ...] = (
    "For each county stretch of a route, read the forecast peak rainfall rate and the "
    "24-hour trailing accumulation, and any official NWS flood watch, advisory, or "
    "warning valid at the traveler's estimated arrival there.",
    f"Rain component: scaled to 100 at {RATE_FULL_SCALE_MM_H:.0f} mm/h peak rate or "
    f"{ACCUM_FULL_SCALE_MM:.0f} mm over 24 hours, whichever is higher.",
    "Alert component: a fixed floor per official product (watch, advisory, warning, "
    "emergency), from configs/scoring.yaml, times 100.",
    "Segment index: the higher of the two components. An official alert or heavier "
    "rain can only raise it, never lower it.",
    "Route index: the highest segment index on that route. A stretch with no usable "
    "forecast is not assessed (index is null), never scored as low concern.",
    f"Comparison: routes within {TIE_POINTS} points are called a tie, with no lower-"
    f"concern claim. A route index of {SEVERE_INDEX} or above on every route keeps the "
    f"delay advice visible even when there is no better alternative.",
)

COVERAGE = (
    f"Forecasts are read up to {HORIZON_HOURS} hours ahead. A route outside North "
    "Carolina, or an arrival beyond that horizon, is reported as unassessed coverage, "
    "not silently scored. Alerts come from the National Weather Service; a failed "
    "alert fetch is reported, not treated as 'no alerts'."
)


@router.get("/methodology")
def methodology() -> dict[str, object]:
    """Return the fixed methodology statement."""
    return {
        "schema_version": SCHEMA_VERSION,
        "score_name": SCORE_NAME,
        "summary": SUMMARY,
        "what_it_is_not": WHAT_IT_IS_NOT,
        "rule_steps": list(RULE_STEPS),
        "coverage": COVERAGE,
        "limitations": list(LIMITATIONS),
        "spec_document": "docs/prototype_score_spec.md",
    }
