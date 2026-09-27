"""Prototype hazard indicator for the MVP replay. Not a model, not a probability.

A transparent rule over two inputs per route segment:

  * trailing rainfall (mm) at the county over the 24 and 72 hours before the segment's
    six-hour arrival window, from ERA5 reanalysis; and
  * official NWS flood products (FA, FF, FL) that were already issued at the decision
    time and are valid at the segment's arrival.

The output is an ordered concern level, not a probability and not a validated score.
The rainfall thresholds are round numbers chosen by the team for this demo. They are
not calibrated against NC flood reports and have no held-out evaluation.

Contract
--------
Input  (`SegmentInput`): county_fips, arrival_utc, window_start_utc, precip_24h_mm,
       precip_72h_mm (None means missing), alerts (list of `AlertInput`).
Output (`SegmentAssessment`): level (0 to 3, or None when nothing can be assessed),
       label, reason, sources, data_status, and the alerts that were used.

Rules that the tests pin down
-----------------------------
  * Official alerts and rainfall combine by maximum: an alert can raise the level and
    never lower it.
  * Missing rainfall never produces "Lower concern": with no alert the level is None.
  * Only alerts issued at or before the decision time count (no hindsight).
  * The same inputs always give the same output. Nothing here touches the network.

Replay caveat: ERA5 is published days after the fact, so a replay uses rainfall a
traveler would not have had at departure. Alerts use their original expiry, so an
extension issued before departure is missed, but none from after it leaks in. The
output states both.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

LABELS: dict[int, str] = {
    0: "Lower concern",
    1: "Elevated concern",
    2: "High concern",
    3: "Severe concern",
}

# (minimum mm, level). Illustrative thresholds, not calibrated.
PRECIP_24H_TIERS: tuple[tuple[float, int], ...] = ((100.0, 3), (50.0, 2), (25.0, 1))
PRECIP_72H_TIERS: tuple[tuple[float, int], ...] = ((250.0, 3), (150.0, 2), (75.0, 1))

PRODUCT_NAMES: dict[tuple[str, str], str] = {
    ("FF", "W"): "Flash Flood Warning",
    ("FL", "W"): "Flood Warning",
    ("FA", "W"): "Areal Flood Warning",
    ("FA", "Y"): "Flood Advisory",
    ("FL", "Y"): "Flood Advisory",
    ("FF", "Y"): "Flash Flood Advisory",
    ("FA", "A"): "Flood Watch",
    ("FL", "A"): "Flood Watch",
    ("FF", "A"): "Flash Flood Watch",
}
ALERT_LEVELS: dict[tuple[str, str], int] = {
    ("FF", "W"): 3,
    ("FL", "W"): 2,
    ("FA", "W"): 2,
    ("FA", "Y"): 1,
    ("FL", "Y"): 1,
    ("FF", "Y"): 1,
    ("FA", "A"): 1,
    ("FL", "A"): 1,
    ("FF", "A"): 1,
}

ADVISORY: dict[int, str] = {
    0: (
        "The available data show no elevated indicator on this route. This is not a "
        "guarantee. Official warnings and road closures take priority."
    ),
    1: (
        "Some flood-related conditions are present. Monitor official NWS products and "
        "DriveNC road closures, and allow extra time."
    ),
    2: (
        "Higher flood-related concern on part of this route. Consider a later departure "
        "or a different route, and check DriveNC road closures before leaving."
    ),
    3: (
        "Official flood warnings or extreme rainfall on part of this route. Consider "
        "delaying or reducing travel through the affected counties, and follow official "
        "guidance and road closures."
    ),
}

REPLAY_CAVEAT = (
    "Replay of a past storm using reanalysis rainfall and archived alerts. A traveler "
    "would not have had this rainfall at departure time. Alerts use their original "
    "expiry, so a warning extended before departure counts as expired. Prototype rule, "
    "not a calibrated probability or a validated score."
)


@dataclass(frozen=True)
class AlertInput:
    """One county-coded NWS flood product."""

    phenomena: str
    significance: str
    eventid: str
    issued_utc: datetime
    expires_utc: datetime
    known_utc: datetime  # when the product first reached the public (product issuance)


@dataclass(frozen=True)
class SegmentInput:
    """Everything the indicator needs for one stretch of road in one county."""

    county_fips: str
    arrival_utc: datetime
    window_start_utc: datetime
    precip_24h_mm: float | None
    precip_72h_mm: float | None
    alerts: Sequence[AlertInput] = field(default_factory=tuple)


@dataclass(frozen=True)
class SegmentAssessment:
    """The indicator's answer for one segment, with the reason shown to users."""

    county_fips: str
    arrival_utc: str
    window_start_utc: str
    level: int | None
    label: str
    reason: str
    sources: list[str]
    data_status: str
    precip_24h_mm: float | None
    precip_72h_mm: float | None
    alerts_used: list[str]


def _tier(value: float | None, tiers: tuple[tuple[float, int], ...]) -> int | None:
    if value is None:
        return None
    return next((level for floor, level in tiers if value >= floor), 0)


def active_alerts(
    alerts: Sequence[AlertInput], arrival_utc: datetime, decision_utc: datetime
) -> list[AlertInput]:
    """Alerts known at the decision time and valid at arrival, recognised products only."""
    return [
        a
        for a in alerts
        if (a.phenomena, a.significance) in ALERT_LEVELS
        and a.known_utc <= decision_utc
        and a.issued_utc <= arrival_utc < a.expires_utc
    ]


def assess_segment(segment: SegmentInput, decision_utc: datetime) -> SegmentAssessment:
    """Apply the rule to one segment. Pure: same inputs, same output."""
    rain_levels = [
        lvl
        for lvl in (
            _tier(segment.precip_24h_mm, PRECIP_24H_TIERS),
            _tier(segment.precip_72h_mm, PRECIP_72H_TIERS),
        )
        if lvl is not None
    ]
    rain_missing = segment.precip_24h_mm is None or segment.precip_72h_mm is None
    rain_level = max(rain_levels) if rain_levels else None

    used = active_alerts(segment.alerts, segment.arrival_utc, decision_utc)
    alert_level = max((ALERT_LEVELS[(a.phenomena, a.significance)] for a in used), default=0)

    sources: list[str] = []
    parts: list[str] = []
    if rain_levels:
        sources.append("ERA5 reanalysis rainfall (Open-Meteo)")
        parts.append(
            f"rainfall {_fmt(segment.precip_24h_mm)} mm in the prior 24 h and "
            f"{_fmt(segment.precip_72h_mm)} mm in the prior 72 h"
        )
    if used:
        sources.append("NWS flood products (IEM archive)")
        names = sorted({PRODUCT_NAMES[(a.phenomena, a.significance)] for a in used})
        parts.append("active " + ", ".join(names))

    if rain_level is None and not used:
        level: int | None = None
        status = "missing_weather"
        reason = "No rainfall data for this county and no active flood product: not assessed."
    else:
        level = max(rain_level or 0, alert_level)
        status = "complete" if not rain_missing else "partial_weather"
        reason = "; ".join(parts).capitalize() + "."
    return SegmentAssessment(
        county_fips=segment.county_fips,
        arrival_utc=segment.arrival_utc.isoformat(),
        window_start_utc=segment.window_start_utc.isoformat(),
        level=level,
        label=LABELS[level] if level is not None else "Not assessed",
        reason=reason,
        sources=sources,
        data_status=status,
        precip_24h_mm=segment.precip_24h_mm,
        precip_72h_mm=segment.precip_72h_mm,
        alerts_used=[
            f"{PRODUCT_NAMES[(a.phenomena, a.significance)]} (event {a.eventid})" for a in used
        ],
    )


def _fmt(value: float | None) -> str:
    return "unknown" if value is None else f"{value:.0f}"


def assess_trip(segments: Sequence[SegmentInput], decision_utc: datetime) -> dict[str, Any]:
    """Assess every segment; the trip level is the highest segment level.

    A segment that could not be assessed never pulls the trip level down and is
    reported in `unassessed_segments`.
    """
    assessed = [assess_segment(s, decision_utc) for s in segments]
    known = [a for a in assessed if a.level is not None]
    if known:
        worst = max(known, key=lambda a: (a.level or 0, -_order(a, assessed)))
        level: int | None = worst.level
    else:
        worst, level = None, None
    unassessed = [a.county_fips for a in assessed if a.level is None]
    return {
        "indicator_name": "Prototype hazard indicator",
        "trip_level": level,
        "trip_label": LABELS[level] if level is not None else "Not assessed",
        "highest_concern_segment": asdict(worst) if worst else None,
        "advisory": ADVISORY[level]
        if level is not None
        else (
            "Not enough data to assess this route. Check official NWS products and "
            "DriveNC road closures."
        ),
        "unassessed_segments": unassessed,
        "segments": [asdict(a) for a in assessed],
        "decision_time_utc": decision_utc.isoformat(),
        "replay_caveat": REPLAY_CAVEAT,
    }


def _order(target: SegmentAssessment, all_: Sequence[SegmentAssessment]) -> int:
    """Position of a segment along the route, so ties go to the earliest one."""
    return next(i for i, a in enumerate(all_) if a is target)
