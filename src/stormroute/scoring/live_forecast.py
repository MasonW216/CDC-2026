"""Live forecast and alert adapters for the prototype weather-concern index.

Two narrow readers, both HTTP GETs with no API key:

  * Open-Meteo forecast API: hourly precipitation at one point per county, UTC.
  * NWS `api.weather.gov` active alerts for North Carolina, matched to counties by SAME code.

Every successful response is written to a cache directory with its retrieval time. When
the network fails, the newest cached response is used and labelled `from_cache`, so the
demo survives conference wifi, and the screen can show how old the data is. With no cache
either, the failure is raised as `ForecastError` / reported in `AlertData.error`; a caller
must then decline a confident ranking rather than treat missing data as low concern.

Freshness policy: a fallback used because a *live* fetch just failed is only served if it
is younger than `MAX_FORECAST_FALLBACK_AGE` / `MAX_ALERTS_FALLBACK_AGE`; older than that,
it is treated the same as no cache at all, so a stale forecast is never presented as
current. This never applies to an explicit `offline=True` call (a saved demo replay,
which is allowed to stay old on purpose -- see `stormroute.scoring.trip.replay_saved_trip`).

Not the historical pipeline (ADR 0005): reanalysis rainfall is never fed through here.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
NWS_ALERTS_URL = "https://api.weather.gov/alerts/active"
USER_AGENT = "StormRoute-CDC2026 (student research prototype)"
PAST_DAYS = 2
FORECAST_DAYS = 5
TIMEOUT = httpx.Timeout(10.0, read=30.0)

# How old a *fallback* cache (a live fetch just failed) may be before it is refused.
# Hourly forecasts and frequently-updated alerts justify different limits; both are
# generous enough to survive a short outage but short enough that "current" stays true.
MAX_FORECAST_FALLBACK_AGE = timedelta(hours=3)
MAX_ALERTS_FALLBACK_AGE = timedelta(minutes=30)

# NWS flood products in scope for v1, and the floor each sets (configs/scoring.yaml x 100).
ALERT_FLOORS: dict[str, int] = {
    "Flash Flood Warning": 80,
    "Flood Warning": 80,
    "Flash Flood Watch": 35,
    "Flood Watch": 35,
    "Flood Advisory": 50,
    "Flash Flood Advisory": 50,
}
EMERGENCY_FLOOR = 98


class ForecastError(RuntimeError):
    """The forecast could not be fetched and no cached copy exists."""


@dataclass(frozen=True)
class Alert:
    """One official flood product affecting one or more counties."""

    id: str
    event: str
    floor: int
    headline: str | None
    effective_utc: datetime | None
    expires_utc: datetime | None
    county_fips: tuple[str, ...]


@dataclass(frozen=True)
class ForecastData:
    """Hourly precipitation per county. Keys are `YYYY-MM-DDTHH:00` UTC; values are mm."""

    hourly: dict[str, dict[str, float | None]]
    retrieved_utc: datetime
    from_cache: bool
    source: str = "Open-Meteo forecast API (best-match model), hourly precipitation"


@dataclass(frozen=True)
class AlertData:
    """Active flood alerts, or the reason they are missing."""

    alerts: tuple[Alert, ...]
    retrieved_utc: datetime
    ok: bool
    error: str | None = None
    from_cache: bool = False
    unmapped: int = 0
    source: str = "NWS api.weather.gov active alerts, NC"
    raw_count: int = field(default=0)


def _now() -> datetime:
    return datetime.now(UTC)


def _cache_file(cache_dir: Path, kind: str, key: str) -> Path:
    digest = hashlib.sha256(key.encode()).hexdigest()[:16]
    return cache_dir / f"{kind}_{digest}.json"


def _write_cache(path: Path, payload: Any, retrieved: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {"retrieved_utc": retrieved.isoformat(), "payload": payload}
    path.write_text(json.dumps(body, separators=(",", ":")), encoding="utf-8")


def _read_cache(path: Path) -> tuple[Any, datetime] | None:
    if not path.exists():
        return None
    body = json.loads(path.read_text(encoding="utf-8"))
    return body["payload"], datetime.fromisoformat(body["retrieved_utc"])


def _get_json(url: str, params: dict[str, str], client: httpx.Client | None) -> Any:
    owns = client is None
    http = client or httpx.Client(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
    try:
        reply = http.get(url, params=params)
        reply.raise_for_status()
        return reply.json()
    finally:
        if owns:
            http.close()


def parse_forecast(payload: Any, fips_in_order: list[str]) -> dict[str, dict[str, float | None]]:
    """Open-Meteo answers with a list for several points and a dict for one."""
    series = payload if isinstance(payload, list) else [payload]
    if len(series) != len(fips_in_order):
        raise ForecastError(f"forecast returned {len(series)} points for {len(fips_in_order)}")
    result: dict[str, dict[str, float | None]] = {}
    for fips, point in zip(fips_in_order, series, strict=True):
        hourly = point["hourly"]
        result[fips] = dict(zip(hourly["time"], hourly["precipitation"], strict=True))
    return result


def fetch_forecast(
    points: dict[str, tuple[float, float]],
    *,
    cache_dir: Path,
    offline: bool = False,
    client: httpx.Client | None = None,
    now: datetime | None = None,
    max_fallback_age: timedelta = MAX_FORECAST_FALLBACK_AGE,
) -> ForecastData:
    """Hourly precipitation for `{county_fips: (lat, lon)}`.

    `now` is the reference time for both a fresh fetch's `retrieved_utc` and the
    freshness check below; defaults to the real clock. Pass the request's own
    `requested_at` for a reproducible check in tests and to keep the age reported in
    the response consistent with the rest of that scoring pass.

    Raises:
        ForecastError: offline with no cache; the network failed with no cache; or
            (live attempt only, never for an explicit `offline=True` replay) the only
            cache available is older than `max_fallback_age`.
    """
    reference = now or _now()
    fips = sorted(points)
    params = {
        "latitude": ",".join(f"{points[f][0]:.4f}" for f in fips),
        "longitude": ",".join(f"{points[f][1]:.4f}" for f in fips),
        "hourly": "precipitation",
        "past_days": str(PAST_DAYS),
        "forecast_days": str(FORECAST_DAYS),
        "timezone": "UTC",
    }
    path = _cache_file(cache_dir, "forecast", json.dumps(params, sort_keys=True))
    if not offline:
        try:
            payload = _get_json(OPEN_METEO_URL, params, client)
            hourly = parse_forecast(payload, fips)
            _write_cache(path, payload, reference)
            return ForecastData(hourly, reference, from_cache=False)
        except (httpx.HTTPError, KeyError, ValueError, ForecastError) as error:
            failure = f"{type(error).__name__}: {error}"
    else:
        failure = "offline mode"
    cached = _read_cache(path)
    if cached is None:
        raise ForecastError(f"no forecast available ({failure}) and no cached copy")
    payload, retrieved = cached
    if not offline:
        age = reference - retrieved
        if age > max_fallback_age:
            raise ForecastError(
                f"cached forecast is {age} old, older than the {max_fallback_age} "
                f"freshness policy for a live fallback ({failure})"
            )
    return ForecastData(parse_forecast(payload, fips), retrieved, from_cache=True)


def _stamp(text: str | None) -> datetime | None:
    if not text:
        return None
    return datetime.fromisoformat(text).astimezone(UTC)


def parse_alerts(payload: Any) -> tuple[tuple[Alert, ...], int, int]:
    """Keep flood products only. Returns (alerts, unmapped flood alerts, total features)."""
    features = payload.get("features", [])
    kept: list[Alert] = []
    unmapped = 0
    for feature in features:
        props = feature.get("properties", {})
        event = props.get("event")
        if event not in ALERT_FLOORS:
            continue
        same = props.get("geocode", {}).get("SAME") or []
        counties = tuple(sorted({"37" + code[-3:] for code in same if code.startswith("037")}))
        if not counties:
            unmapped += 1
            continue
        threat = (props.get("parameters") or {}).get("flashFloodDamageThreat") or []
        floor = EMERGENCY_FLOOR if "CATASTROPHIC" in threat else ALERT_FLOORS[event]
        kept.append(
            Alert(
                id=str(props.get("id") or feature.get("id")),
                event=str(event),
                floor=floor,
                headline=props.get("headline"),
                effective_utc=_stamp(props.get("onset") or props.get("effective")),
                expires_utc=_stamp(props.get("ends") or props.get("expires")),
                county_fips=counties,
            )
        )
    return tuple(kept), unmapped, len(features)


def fetch_alerts(
    *,
    cache_dir: Path,
    offline: bool = False,
    client: httpx.Client | None = None,
    now: datetime | None = None,
    max_fallback_age: timedelta = MAX_ALERTS_FALLBACK_AGE,
) -> AlertData:
    """Active NC flood alerts. Never raises: a failure comes back as `ok=False`.

    See `fetch_forecast` for `now` and the freshness policy this applies to a fallback
    from a failed live attempt (never to an explicit `offline=True` replay).
    """
    reference = now or _now()
    params = {"area": "NC"}
    path = _cache_file(cache_dir, "alerts", json.dumps(params))
    failure = "offline mode"
    if not offline:
        try:
            payload = _get_json(NWS_ALERTS_URL, params, client)
            alerts, unmapped, total = parse_alerts(payload)
            _write_cache(path, payload, reference)
            return AlertData(alerts, reference, True, None, False, unmapped, raw_count=total)
        except (httpx.HTTPError, KeyError, ValueError) as error:
            failure = f"{type(error).__name__}: {error}"
    cached = _read_cache(path)
    if cached is None:
        return AlertData((), reference, False, f"no alert data ({failure}) and no cached copy")
    payload, retrieved = cached
    if not offline:
        age = reference - retrieved
        if age > max_fallback_age:
            return AlertData(
                (),
                reference,
                False,
                f"cached alerts are {age} old, older than the {max_fallback_age} "
                f"freshness policy for a live fallback ({failure})",
                from_cache=True,
            )
    alerts, unmapped, total = parse_alerts(payload)
    return AlertData(alerts, retrieved, True, None, True, unmapped, raw_count=total)
