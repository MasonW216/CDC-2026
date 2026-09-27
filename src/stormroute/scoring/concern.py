"""Prototype weather-concern index, `prototype-score/1`. Pure functions, no network.

Implements docs/prototype_score_spec.md. Read that first: it defines the rule, the
coverage requirements, and the comparison outcomes. The index is a 0-100 team-defined
comparison index (higher = more indicated weather concern), not a probability and not a
validated score. The wire shape is mirrored in frontend/src/types/score.ts.

Guarantees the tests pin down:
  * the index is a maximum, so no alert and no heavier rain can lower it;
  * a stretch with missing forecast hours is unassessed (index None), never 0;
  * splitting a stretch into pieces cannot change the route index;
  * the same inputs always give the same output.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from stormroute.scoring.county_prior import load_county_components
from stormroute.scoring.live_forecast import Alert, AlertData, ForecastData

SCHEMA_VERSION = "prototype-score/1"
SCORE_NAME = "Prototype weather-concern index (0-100, higher means more indicated concern)"
RATE_FULL_SCALE_MM_H = 20.0
ACCUM_FULL_SCALE_MM = 100.0
TIE_POINTS = 5
SEVERE_INDEX = 80
HORIZON_HOURS = 72
CONCERN_MINUTES_THRESHOLD = 50
HOUR = timedelta(hours=1)

LIMITATIONS: tuple[str, ...] = (
    "Prototype rule, not a calibrated flood probability or a validated score.",
    "Forecasts are uncertain and can be wrong.",
    "The index does not know road closures, drainage, or terrain.",
    "No official alert seen does not mean none exists; alerts issued later are not seen.",
    "One forecast point per county.",
)


@dataclass(frozen=True)
class Stretch:
    """One county stretch of a route, from the routing code."""

    county_fips: str | None
    county_name: str
    arrival_utc: datetime
    minutes: float
    km: float


@dataclass(frozen=True)
class RouteInput:
    """A candidate route as the scorer needs it."""

    route_id: str
    duration_minutes: float
    distance_km: float
    stretches: Sequence[Stretch]


def band(index: int | None) -> str:
    """Plain-language band for an index. No band is called safe."""
    if index is None:
        return "Not assessed"
    if index >= SEVERE_INDEX:
        return "Severe concern"
    if index >= 50:
        return "High concern"
    if index >= 25:
        return "Elevated concern"
    return "Lower concern"


def _hour_key(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:00")


def _floor_hour(moment: datetime) -> datetime:
    return moment.astimezone(UTC).replace(minute=0, second=0, microsecond=0)


def _ceil_hour(moment: datetime) -> datetime:
    floored = _floor_hour(moment)
    return floored if floored == moment.astimezone(UTC) else floored + HOUR


def overlapped_hours(stretch: Stretch) -> tuple[datetime, datetime]:
    """First and last hourly accumulation stamps that intersect the stretch.

    Open-Meteo stamps each value with the END of its hour, so the accumulations that
    overlap (arrival, arrival + minutes] are stamped from the next hour boundary after
    arrival to the hour boundary at or after departure from the county.
    """
    first = _floor_hour(stretch.arrival_utc) + HOUR
    last = max(first, _ceil_hour(stretch.arrival_utc + timedelta(minutes=stretch.minutes)))
    return first, last


def _rain_terms(
    hourly: Mapping[str, float | None], first: datetime, last: datetime
) -> tuple[float, float] | str:
    """(peak mm/h over the stretch, mm over the 24 h ending at `last`) or a reason string."""
    span = int((last - first) / HOUR) + 1
    peak_values = [hourly.get(_hour_key(first + k * HOUR)) for k in range(span)]
    trail_values = [hourly.get(_hour_key(last - k * HOUR)) for k in range(24)]
    if any(v is None for v in peak_values):
        return "no forecast for some hours of this stretch"
    if any(v is None for v in trail_values):
        return "no forecast for the 24 hours before this stretch"
    peak = max(v for v in peak_values if v is not None)
    accum = math.fsum(v for v in trail_values if v is not None)
    return round(peak, 2), round(accum, 2)


def _alert_overlaps(alert: Alert, start: datetime, end: datetime) -> bool:
    begins = alert.effective_utc
    finishes = alert.expires_utc
    return (begins is None or begins <= end) and (finishes is None or finishes > start)


def alert_dict(alert: Alert) -> dict[str, Any]:
    """Wire form of an alert."""
    return {
        "event": alert.event,
        "floor": alert.floor,
        "headline": alert.headline,
        "effective_utc": alert.effective_utc.isoformat() if alert.effective_utc else None,
        "expires_utc": alert.expires_utc.isoformat() if alert.expires_utc else None,
        "id": alert.id,
    }


def score_segment(
    stretch: Stretch,
    forecast: ForecastData | None,
    alerts: AlertData,
    requested_at: datetime,
) -> dict[str, Any]:
    """Index one stretch. Missing forecast gives index None; an alert can still raise it."""
    start = stretch.arrival_utc
    end = stretch.arrival_utc + timedelta(minutes=stretch.minutes)
    used = sorted(
        (
            a
            for a in alerts.alerts
            if stretch.county_fips in a.county_fips and _alert_overlaps(a, start, end)
        ),
        key=lambda a: (-a.floor, a.id),
    )
    alert_component = max((a.floor for a in used), default=0)
    # A real Bayesian hierarchical (Beta-Binomial) fit on the 2015-2024 NOAA Storm Events
    # history, per county (see county_prior.py). Descriptive, not predictive; can only
    # raise a segment's index, exactly like an alert, and is capped well below the live
    # signal's own ceiling (see MAX_COMPONENT in that module).
    county_component = (
        load_county_components().get(stretch.county_fips, 0.0) if stretch.county_fips else 0.0
    )
    base: dict[str, Any] = {
        "county_fips": stretch.county_fips,
        "county_name": stretch.county_name,
        "arrival_utc": stretch.arrival_utc.astimezone(UTC).isoformat(),
        "minutes": round(stretch.minutes, 1),
        "km": round(stretch.km, 1),
        "alerts": [alert_dict(a) for a in used],
        "rain_rate_mm_h": None,
        "rain_24h_mm": None,
        # Exact hourly stamps the two rain terms were read from (Open-Meteo, UTC), for
        # an audit trail; null together with the rain terms when there is a gap.
        "rain_peak_window_utc": None,
        "rain_24h_window_utc": None,
        # The Bayesian historical-rate term, always present (it needs no live forecast),
        # 0 for a county at or below the state's historical average.
        "county_prior_component": round(county_component, 1),
    }
    gap: str | None = None
    rain_component: float | None = None
    if stretch.county_fips is None:
        gap = "outside North Carolina coverage"
    elif forecast is None or stretch.county_fips not in forecast.hourly:
        gap = "no forecast for this county"
    else:
        first, last = overlapped_hours(stretch)
        if last > requested_at + timedelta(hours=HORIZON_HOURS):
            gap = f"arrival is beyond the {HORIZON_HOURS} hour forecast horizon"
        else:
            terms = _rain_terms(forecast.hourly[stretch.county_fips], first, last)
            if isinstance(terms, str):
                gap = terms
            else:
                base["rain_rate_mm_h"], base["rain_24h_mm"] = terms
                base["rain_peak_window_utc"] = [first.isoformat(), last.isoformat()]
                base["rain_24h_window_utc"] = [
                    (last - timedelta(hours=23)).isoformat(),
                    last.isoformat(),
                ]
                rain_component = 100 * min(
                    1.0, max(terms[0] / RATE_FULL_SCALE_MM_H, terms[1] / ACCUM_FULL_SCALE_MM)
                )
    alert_text = (
        "; ".join(sorted({a.event for a in used})) + " in effect"
        if used
        else "no official flood product in effect"
    )
    history_text = (
        f"; county's 2015-2024 history runs above the state average ({county_component:.0f}-point "
        "historical adjustment)"
        if county_component > 0
        else ""
    )
    if rain_component is None:
        # Missing forecast: an alert or the historical rate alone still raises a lower
        # bound, never a full score.
        index = (
            round(max(alert_component, county_component))
            if (used or county_component > 0)
            else None
        )
        status = "unassessed"
        reason = f"Forecast unavailable ({gap}); {alert_text}{history_text}. Not assessed."
        if used or county_component > 0:
            reason = f"Forecast unavailable ({gap}); {alert_text}{history_text}. Lower bound only."
    else:
        index = round(max(rain_component, alert_component, county_component))
        status = "assessed"
        reason = (
            f"Forecast peak {base['rain_rate_mm_h']} mm/h and {base['rain_24h_mm']} mm over "
            f"the prior 24 h; {alert_text}{history_text}."
        )
    base.update(status=status, index=index, band=band(index), reason=reason)
    return base


def score_route(
    route: RouteInput,
    forecast: ForecastData | None,
    alerts: AlertData,
    requested_at: datetime,
) -> dict[str, Any]:
    """Score every stretch; the route index is the highest assessed stretch index."""
    segments = [score_segment(s, forecast, alerts, requested_at) for s in route.stretches]
    scored = [s for s in segments if s["index"] is not None]
    unassessed = [s for s in segments if s["status"] == "unassessed"]
    complete = not unassessed and alerts.ok
    index = max((s["index"] for s in scored), default=None)
    if not scored:
        status = "unassessed"
    elif complete:
        status = "assessed"
    else:
        status = "partial"
    worst = max(scored, key=lambda s: (s["index"], -segments.index(s))) if scored else None
    seen: dict[str, dict[str, Any]] = {}
    for seg in segments:
        for alert in seg["alerts"]:
            seen.setdefault(alert["id"], alert)
    minutes_high = round(
        math.fsum(s["minutes"] for s in scored if s["index"] >= CONCERN_MINUTES_THRESHOLD),
        1,
    )
    reasons: list[str] = []
    if worst:
        reasons.append(f"Highest concern in {worst['county_name']}: {worst['reason']}")
    if minutes_high:
        reasons.append(f"About {minutes_high:.0f} minutes at High concern or above.")
    if unassessed:
        names = ", ".join(sorted({s["county_name"] for s in unassessed}))
        reasons.append(f"Not assessed: {names}. The index is a lower bound.")
    if not alerts.ok:
        reasons.append("Official alert data was unavailable, so alerts are not reflected.")
    return {
        "route_id": route.route_id,
        "duration_minutes": round(route.duration_minutes, 1),
        "distance_km": round(route.distance_km, 1),
        "status": status,
        "index": index,
        "band": band(index),
        "is_lower_bound": status == "partial",
        "minutes_at_or_above_50": minutes_high,
        "highest_concern_segment": worst,
        "segments": segments,
        "alerts": sorted(seen.values(), key=lambda a: (-a["floor"], a["id"])),
        "reasons": reasons,
        "contributing_factors": _contributing_factors(scored),
    }


def _contributing_factors(scored: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Up to 3 highest-index stretches, tagged by what actually drove each one.

    Built only from fields the rule already computed for that stretch -- never a fixed
    marketing list. A `kind` other than "rain", "alert", or "historical" must not be
    invented; the frontend maps `kind` to an icon, so a new factor needs a new field here
    first, not a guess on the UI side (e.g. no "saturated ground" without a real
    soil-moisture input, which this rule does not read).
    """
    factors = []
    for seg in sorted(scored, key=lambda s: -s["index"])[:3]:
        if seg["index"] <= 0:
            continue
        rain_component = 100 * min(
            1.0,
            max(
                (seg["rain_rate_mm_h"] or 0) / RATE_FULL_SCALE_MM_H,
                (seg["rain_24h_mm"] or 0) / ACCUM_FULL_SCALE_MM,
            ),
        )
        alert_component = max((a["floor"] for a in seg["alerts"]), default=0)
        history_component = seg.get("county_prior_component") or 0
        ranked = sorted(
            (
                ("alert", alert_component if seg["alerts"] else -1),
                ("rain", rain_component),
                ("historical", history_component),
            ),
            key=lambda pair: pair[1],
            reverse=True,
        )
        kind = ranked[0][0]
        if kind == "alert":
            label = sorted({a["event"] for a in seg["alerts"]})[0]
        elif kind == "historical":
            label = f"County history, {seg['county_name']}"
        else:
            label = f"Heavy rainfall, {seg['county_name']}"
        factors.append(
            {
                "kind": kind,
                "county_name": seg["county_name"],
                "label": label,
                "detail": seg["reason"],
                "arrival_utc": seg["arrival_utc"],
                "index": seg["index"],
            }
        )
    return factors


def compare(routes: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Fastest versus lowest-concern route, per the spec's comparison outcomes."""
    if not routes:
        return _comparison("no_routes", None, None, None, None, "No route was found.", None)
    fastest = min(routes, key=lambda r: (r["duration_minutes"], routes.index(r)))
    if len(routes) == 1:
        return _comparison(
            "single_route",
            fastest["route_id"],
            None,
            0.0,
            None,
            "Only one route was available, so no comparison is possible.",
            _severe(routes),
        )
    if any(r["status"] != "assessed" for r in routes):
        return _comparison(
            "unavailable",
            fastest["route_id"],
            None,
            None,
            None,
            "Weather or alert data is missing for at least one route, so no confident "
            "ranking is given.",
            _severe(routes),
        )
    lowest = min(routes, key=lambda r: (r["index"], r["duration_minutes"], routes.index(r)))
    difference = fastest["index"] - lowest["index"]
    severe = _severe(routes)
    if abs(fastest["index"] - lowest["index"]) < TIE_POINTS and all(
        abs(r["index"] - lowest["index"]) < TIE_POINTS for r in routes
    ):
        return _comparison(
            "tie",
            fastest["route_id"],
            None,
            0.0,
            0,
            "The routes show similar indicated concern (within "
            f"{TIE_POINTS} points), so this index does not favor one.",
            severe,
        )
    extra = round(lowest["duration_minutes"] - fastest["duration_minutes"], 1)
    if lowest["route_id"] == fastest["route_id"]:
        message = (
            "The fastest route also shows the lowest indicated concern "
            f"({fastest['index']} against {max(r['index'] for r in routes)})."
        )
    else:
        message = (
            f"{lowest['route_id']} shows lower indicated concern ({lowest['index']} against "
            f"{fastest['index']}) and takes {abs(extra):.0f} minutes "
            f"{'longer' if extra > 0 else 'less'} than the fastest route, "
            f"{fastest['route_id']}."
        )
    return _comparison(
        "distinguishable",
        fastest["route_id"],
        lowest["route_id"],
        extra,
        difference,
        message,
        severe,
    )


def _severe(routes: Sequence[dict[str, Any]]) -> str | None:
    indexes = [r["index"] for r in routes if r["index"] is not None]
    if not indexes or min(indexes) < SEVERE_INDEX:
        return None
    subject = "This route does not avoid" if len(routes) == 1 else "None of the routes avoid"
    return (
        f"{subject} the warnings or heavy rain. Check official guidance and road closures, "
        "or consider delaying."
    )


def _comparison(
    ranking: str,
    fastest: str | None,
    lowest: str | None,
    extra: float | None,
    difference: int | None,
    message: str,
    severe: str | None,
) -> dict[str, Any]:
    return {
        "ranking": ranking,
        "fastest_route_id": fastest,
        "lowest_concern_route_id": lowest,
        "extra_minutes": extra,
        "index_difference": difference,
        "message": message,
        "severe_advice": severe,
    }
