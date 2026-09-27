"""Assign route samples to North Carolina counties.

Joins sampled points to county polygons from `data.geography`, collapses
consecutive samples sharing a (county, window) pair into one interval, and
flags any portion of the route falling outside the modeled geography.

Coverage is reported, never quietly ignored: a trip leaving North Carolina is
partially unmodeled and the user must be told so.
"""

from __future__ import annotations

import geopandas as gpd
import pandas as pd

INTERVAL_COLUMNS = [
    "route_id",
    "interval_order",
    "county_fips",
    "window_start_utc",
    "entry_utc",
    "exposure_minutes",
    "distance_km",
    "in_modeled_geography",
]
_OUTSIDE = "__outside__"


def county_for_points(points: gpd.GeoSeries, counties: gpd.GeoDataFrame) -> pd.Series:
    """Return the county FIPS containing each point, or None outside every county.

    A point outside the modeled geography is never snapped to the nearest county.

    Raises:
        ValueError: if a point falls inside more than one county (overlapping
            polygons would double-count exposure).
    """
    frame = gpd.GeoDataFrame(geometry=points.to_crs(counties.crs).reset_index(drop=True))
    joined = gpd.sjoin(frame, counties[["county_fips", "geometry"]], how="left", predicate="within")
    if joined.index.duplicated().any():
        raise ValueError("a point falls inside more than one county; county polygons overlap")
    fips = joined["county_fips"].reindex(frame.index)
    return pd.Series(
        [value if isinstance(value, str) else None for value in fips],
        index=frame.index,
        dtype=object,
    )


def collapse_intervals(samples: pd.DataFrame) -> pd.DataFrame:
    """Collapse route samples into one row per (route, county, window).

    Each sample describes the stretch from itself to the next sample, so the last
    sample of a route (a zero-length stretch) contributes nothing. Repeated
    visits to the same county-window, consecutive or not, are summed into one
    interval, ordered by first entry.
    """
    stretches = []
    for _, route in samples.groupby("route_id", sort=False):
        route = route.sort_values("sample_order")
        segment_km = route["distance_km"].shift(-1) - route["distance_km"]
        stretches.append(route.assign(segment_km=segment_km).iloc[:-1] if len(route) > 1 else route)
    frame = pd.concat(stretches).assign(
        segment_km=lambda df: df["segment_km"].fillna(0.0),
        county_key=lambda df: df["county_fips"].fillna(_OUTSIDE),
    )

    intervals = (
        frame.groupby(["route_id", "county_key", "window_start_utc"], sort=False)
        .agg(
            entry_utc=("arrival_utc", "min"),
            exposure_minutes=("segment_minutes", "sum"),
            distance_km=("segment_km", "sum"),
        )
        .reset_index()
        .sort_values(["route_id", "entry_utc"], kind="stable")
    )
    in_model = intervals["county_key"] != _OUTSIDE
    intervals["county_fips"] = [None if key == _OUTSIDE else key for key in intervals["county_key"]]
    intervals["in_modeled_geography"] = in_model
    intervals["interval_order"] = intervals.groupby("route_id").cumcount()
    return intervals[INTERVAL_COLUMNS].reset_index(drop=True)


def modeled_fraction(intervals: pd.DataFrame) -> float:
    """Share of route distance that lies inside the modeled geography (0 to 1)."""
    total = float(intervals["distance_km"].sum())
    if total <= 0:
        return 0.0
    inside = float(intervals.loc[intervals["in_modeled_geography"], "distance_km"].sum())
    return inside / total
