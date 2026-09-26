"""Assert the data contracts every table must satisfy.

Shared checks invoked by the pipeline and by tests: schema and dtype
conformance, unique event identifiers, timezone-aware timestamps, county FIPS
shape, value ranges, and missingness thresholds from `configs/data.yaml`.

Failures raise. A pipeline that silently emits a table violating its contract
is worse than one that stops. Each validator collects every failure before
raising, so one run shows the whole problem.

Implemented so far: the events table (Milestone 1). County-window checks
arrive with Milestone 3.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

# North Carolina's 100 counties are exactly the odd numbers 001-199.
NC_COUNTY_FIPS: frozenset[str] = frozenset(f"37{code:03d}" for code in range(1, 200, 2))

# Canonical column order of `events.parquet`; see docs/data_card.md.
EVENTS_COLUMNS: tuple[str, ...] = (
    "event_id",
    "episode_id",
    "county_fips",
    "begin_utc",
    "end_utc",
    "event_type",
    "source",
    "injuries",
    "deaths",
    "property_damage_usd",
)


class DataContractError(ValueError):
    """A table violates its documented contract."""

    def __init__(self, failures: Sequence[str]) -> None:
        """Store every failure and format them as one readable message."""
        self.failures = list(failures)
        super().__init__("Data contract violated:\n  - " + "\n  - ".join(self.failures))


def _is_utc(series: pd.Series) -> bool:
    return isinstance(series.dtype, pd.DatetimeTZDtype) and str(series.dtype.tz) == "UTC"


def validate_events(events: pd.DataFrame, allowed_event_types: Sequence[str]) -> None:
    """Check the canonical events table from `stormroute.data.noaa`.

    Raises:
        DataContractError: listing every violated rule.
    """
    failures: list[str] = []

    if tuple(events.columns) != EVENTS_COLUMNS:
        failures.append(f"columns must be exactly {list(EVENTS_COLUMNS)}, got {list(events.columns)}")
        raise DataContractError(failures)

    ids = events["event_id"]
    if ids.isna().any():
        failures.append(f"{int(ids.isna().sum())} event_id value(s) are missing")
    duplicated = ids[ids.duplicated()].unique()
    if len(duplicated):
        failures.append(f"event_id is not unique: {sorted(duplicated)[:10]}")

    fips = events["county_fips"]
    if not pd.api.types.is_string_dtype(fips):
        failures.append(f"county_fips must be strings, got {fips.dtype}")
    else:
        unknown = sorted(set(fips.dropna()) - NC_COUNTY_FIPS)
        if unknown:
            failures.append(f"county_fips not a North Carolina county: {unknown[:10]}")
        if fips.isna().any():
            failures.append(f"{int(fips.isna().sum())} county_fips value(s) are missing")

    for column in ("begin_utc", "end_utc"):
        if not _is_utc(events[column]):
            failures.append(f"{column} must be timezone-aware UTC, got {events[column].dtype}")
    if _is_utc(events["begin_utc"]):
        if events["begin_utc"].isna().any():
            failures.append(f"{int(events['begin_utc'].isna().sum())} begin_utc value(s) missing")
        if _is_utc(events["end_utc"]):
            backwards = events["end_utc"].notna() & (events["end_utc"] < events["begin_utc"])
            if backwards.any():
                failures.append(
                    f"end_utc precedes begin_utc for event(s) "
                    f"{sorted(events.loc[backwards, 'event_id'])[:10]}"
                )

    unexpected_types = sorted(set(events["event_type"].dropna()) - set(allowed_event_types))
    if unexpected_types:
        failures.append(f"event_type outside the locked hazard list: {unexpected_types}")

    for column in ("injuries", "deaths", "property_damage_usd"):
        negative = events[column].dropna() < 0
        if negative.any():
            failures.append(f"{column} has {int(negative.sum())} negative value(s)")

    if failures:
        raise DataContractError(failures)
