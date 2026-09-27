"""Sample a route into points with expected arrival times.

Samples each route every 5-10 km and at county boundaries, then computes
cumulative travel minutes so every sample carries the time the traveler is
expected to be there. Arrival time is what maps a sample onto a six-hour
prediction window, so an error here silently misprices the whole trip.

Each sample describes the stretch of road from itself to the next sample.
Samples are placed at:
  * the route start and end;
  * every `spacing_km` along the route;
  * every county-boundary crossing, so no stretch spans two counties; and
  * every six-hour window boundary the trip crosses, so no stretch spans two
    prediction windows.

Distances are measured in `crs_area` (EPSG:5070). Travel time comes from the
router's per-edge durations, interpolated linearly within an edge.
"""

from __future__ import annotations

from datetime import datetime

import geopandas as gpd
import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import LineString, Point

from stormroute.config import load_config
from stormroute.data.geography import AREA_CRS, COUNTY_CRS
from stormroute.routing.client import CandidateRoute
from stormroute.routing.spatial_join import county_for_points

WINDOW_HOURS: int = load_config("scoring")["aggregation"]["window_hours"]
MIN_SPACING_KM, MAX_SPACING_KM = load_config("scoring")["routing"]["sample_spacing_km"]

# `demo_routes.geojson` columns from build guide §6.3, plus the two time columns
# that depend on the departure time (proposed schema addition).
SAMPLE_COLUMNS = [
    "route_id",
    "sample_order",
    "latitude",
    "longitude",
    "county_fips",
    "cumulative_minutes",
    "segment_minutes",
    "distance_km",
    "arrival_utc",
    "window_start_utc",
]
_MIN_GAP_M = 1.0  # breakpoints closer than this are the same place

_TO_AREA = Transformer.from_crs(COUNTY_CRS, AREA_CRS, always_xy=True)
_FROM_AREA = Transformer.from_crs(AREA_CRS, COUNTY_CRS, always_xy=True)


def _utc(moment: datetime | pd.Timestamp) -> pd.Timestamp:
    stamp = pd.Timestamp(moment)
    if stamp.tzinfo is None:
        raise ValueError(f"{moment!r} has no timezone; pass a timezone-aware time")
    return stamp.tz_convert("UTC")


def window_start_utc(moment: datetime | pd.Timestamp) -> pd.Timestamp:
    """Return the start of the six-hour UTC window containing `moment`.

    Windows are half-open and anchored at 00:00, 06:00, 12:00, and 18:00 UTC,
    the same rule the label pipeline uses (ADR 0001).
    """
    return _utc(moment).floor(f"{WINDOW_HOURS}h")


def _county_crossings(
    line: LineString,
    vertex_m: np.ndarray,
    counties_area: gpd.GeoDataFrame,
    vertices: gpd.GeoSeries,
) -> list[float]:
    """Distances along the route at which it crosses a county boundary.

    Only edges whose endpoints lie in different counties (or one outside) are
    intersected with the boundaries, which keeps this fast on long routes and
    finds every crossing even when a route revisits the same place.
    """
    labels = county_for_points(vertices, counties_area).fillna("").to_numpy()
    changed = np.flatnonzero(labels[:-1] != labels[1:])
    if changed.size == 0:
        return []
    boundaries = counties_area.boundary.union_all()
    coords = np.asarray(line.coords)
    crossings: list[float] = []
    for k in changed:
        start = coords[k]
        hit = LineString([start, coords[k + 1]]).intersection(boundaries)
        for part in getattr(hit, "geoms", [hit]):
            for x, y in part.coords:
                crossings.append(vertex_m[k] + float(np.hypot(x - start[0], y - start[1])))
    return crossings


def sample_route(
    route: CandidateRoute,
    departure_utc: datetime | pd.Timestamp,
    counties: gpd.GeoDataFrame,
    spacing_km: float = MIN_SPACING_KM,
) -> pd.DataFrame:
    """Sample `route` for a trip leaving at `departure_utc`.

    Returns one row per sample with the `SAMPLE_COLUMNS`. `county_fips` is the
    county of the stretch starting at that sample (None outside every county),
    `segment_minutes` the time to the next sample, and `distance_km` the
    cumulative distance from the start.

    Raises:
        ValueError: for a naive departure time or spacing outside the
            configured range.
    """
    if not MIN_SPACING_KM <= spacing_km <= MAX_SPACING_KM:
        raise ValueError(
            f"sample spacing {spacing_km} km is outside the configured "
            f"{MIN_SPACING_KM}-{MAX_SPACING_KM} km range"
        )
    departure = _utc(departure_utc)

    lons, lats = np.asarray(route.coordinates).T
    xs, ys = _TO_AREA.transform(lons, lats)
    line = LineString(np.column_stack([xs, ys]))
    vertex_m = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(xs), np.diff(ys)))])
    vertex_s = np.concatenate([[0.0], np.cumsum(route.edge_seconds)])
    total_m, total_s = float(vertex_m[-1]), float(vertex_s[-1])

    counties_area = counties.to_crs(AREA_CRS)
    vertices = gpd.GeoSeries([Point(x, y) for x, y in zip(xs, ys, strict=True)], crs=AREA_CRS)

    breakpoints = [*np.arange(0.0, total_m, spacing_km * 1000.0), total_m]
    breakpoints += _county_crossings(line, vertex_m, counties_area, vertices)
    boundary = window_start_utc(departure) + pd.Timedelta(hours=WINDOW_HOURS)
    while (offset_s := (boundary - departure).total_seconds()) < total_s:
        breakpoints.append(float(np.interp(offset_s, vertex_s, vertex_m)))
        boundary += pd.Timedelta(hours=WINDOW_HOURS)

    ordered = np.sort(np.clip(breakpoints, 0.0, total_m))
    keep = np.concatenate([[True], np.diff(ordered) > _MIN_GAP_M])
    distance_m = ordered[keep]
    distance_m[-1] = total_m  # the end survives de-duplication exactly
    seconds = np.interp(distance_m, vertex_m, vertex_s)

    points = [line.interpolate(d) for d in distance_m]
    sample_lons, sample_lats = _FROM_AREA.transform([p.x for p in points], [p.y for p in points])

    # Each stretch is labeled by its midpoint along the road; the final sample
    # (a zero-length stretch) by its own position.
    mid_m = np.append((distance_m[:-1] + distance_m[1:]) / 2, distance_m[-1])
    mid_s = np.append((seconds[:-1] + seconds[1:]) / 2, seconds[-1])
    midpoints = gpd.GeoSeries([line.interpolate(d) for d in mid_m], crs=AREA_CRS)

    arrival = departure + pd.to_timedelta(seconds, unit="s")
    stretch_time = departure + pd.to_timedelta(mid_s, unit="s")
    minutes = seconds / 60.0
    return pd.DataFrame(
        {
            "route_id": route.route_id,
            "sample_order": np.arange(len(distance_m)),
            "latitude": sample_lats,
            "longitude": sample_lons,
            "county_fips": county_for_points(midpoints, counties_area).to_numpy(),
            "cumulative_minutes": minutes,
            "segment_minutes": np.append(np.diff(minutes), 0.0),
            "distance_km": distance_m / 1000.0,
            "arrival_utc": arrival,
            "window_start_utc": stretch_time.floor(f"{WINDOW_HOURS}h"),
        }
    )[SAMPLE_COLUMNS]
