"""Turn a cached route and the cached Helene inputs into `SegmentInput` objects.

Reads only local files. The route fixture is a list of county stretches:

    {"county_fips": "37021", "arrival_utc": "2024-09-27T16:05:00+00:00"}

`arrival_utc` is when the traveler is expected to enter that stretch. The rainfall
windows end at the start of the six-hour UTC window containing the arrival, so no
rainfall after that instant is used.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from stormroute.scoring.prototype import AlertInput, SegmentInput

WINDOW_HOURS = 6


def _utc(text: str) -> datetime:
    stamp = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)
    return stamp.astimezone(UTC)


def window_start(moment: datetime) -> datetime:
    """Start of the six-hour UTC window (00, 06, 12, 18) containing `moment`."""
    return moment.replace(
        hour=moment.hour - moment.hour % WINDOW_HOURS, minute=0, second=0, microsecond=0
    )


def load_inputs(path: Path) -> dict[str, Any]:
    """Load the cached Helene inputs file."""
    return json.loads(path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def _init_expiry(row: Mapping[str, str]) -> datetime:
    """Original expiry (`utc_init_expire`, `YYYYMMDDHHMM`), the only one known at issuance.

    The archive's `utc_expire` is the final value, which can include an extension or
    cancellation issued after the decision time. Using it would leak the future. The
    cost is that a warning extended before departure is treated as expired at its
    original time, which can under-count; rainfall still applies.
    """
    text = row.get("utc_init_expire") or ""
    if len(text) == 12 and text.isdigit():
        return datetime.strptime(text, "%Y%m%d%H%M").replace(tzinfo=UTC)
    return _utc(row["utc_expire"])


def _alert(row: Mapping[str, str]) -> AlertInput:
    return AlertInput(
        phenomena=row["phenomena"],
        significance=row["significance"],
        eventid=f"{row['wfo']}-{row['eventid']}",
        issued_utc=_utc(row["utc_issue"]),
        expires_utc=_init_expiry(row),
        known_utc=_utc(row["utc_prodissue"]),
    )


def _trailing(
    mm: Sequence[float | None], times: Sequence[str], end: datetime, hours: int
) -> float | None:
    """Sum of hourly values ending at `end` back `hours` hours; None if any is missing.

    `math.fsum` is exactly rounded, so Python 3.11 and 3.12 agree (3.12's built-in `sum`
    compensates and 3.11's does not); rounding to 0.01 mm removes the residue.
    """
    wanted = [(end - timedelta(hours=k)).strftime("%Y-%m-%dT%H:%M") for k in range(hours)]
    index = {t: i for i, t in enumerate(times)}
    if any(t not in index for t in wanted):
        return None
    values = [mm[index[t]] for t in wanted]
    if any(v is None for v in values):
        return None
    return round(math.fsum(v for v in values if v is not None), 2)


def build_segments(
    route: Sequence[Mapping[str, str]], inputs: Mapping[str, Any]
) -> list[SegmentInput]:
    """One `SegmentInput` per route stretch, with rainfall and county alerts attached."""
    times = inputs["precipitation"]["times_utc"]
    mm = inputs["precipitation"]["mm"]
    by_county: dict[str, list[AlertInput]] = {}
    for row in inputs["alerts"]["rows"]:
        fips = "37" + row["ugc"][3:]
        by_county.setdefault(fips, []).append(_alert(row))
    segments = []
    for stretch in route:
        arrival = _utc(stretch["arrival_utc"])
        start = window_start(arrival)
        series = mm.get(stretch["county_fips"])
        segments.append(
            SegmentInput(
                county_fips=stretch["county_fips"],
                arrival_utc=arrival,
                window_start_utc=start,
                precip_24h_mm=_trailing(series, times, start, 24) if series else None,
                precip_72h_mm=_trailing(series, times, start, 72) if series else None,
                alerts=tuple(by_county.get(stretch["county_fips"], ())),
            )
        )
    return segments
