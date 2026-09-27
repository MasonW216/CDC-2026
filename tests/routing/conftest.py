"""Synthetic geometry shared by the routing tests.

A straight east-west route along latitude 35.5 crosses three square "counties"
and then leaves the modeled geography, so every rule has a known answer.
"""

import geopandas as gpd
import pytest
from shapely.geometry import box

from stormroute.routing.client import CandidateRoute

# County edges (longitude). The route runs from -82.0 to -80.9, so the last
# 0.1 degree lies outside every county.
COUNTY_EDGES = [(-82.0, -81.6, "37001"), (-81.6, -81.3, "37003"), (-81.3, -81.0, "37005")]
ROUTE_START_LON = -82.0
ROUTE_END_LON = -80.9
EDGE_SECONDS = 36.0  # per 0.01 degree (~0.9 km), i.e. ~90 km/h


@pytest.fixture
def counties() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {
            "county_fips": [fips for _, _, fips in COUNTY_EDGES],
            "name": ["West", "Middle", "East"],
            "land_area_m2": [1, 1, 1],
        },
        geometry=[box(west, 35.0, east, 36.0) for west, east, _ in COUNTY_EDGES],
        crs="EPSG:4326",
    )


def straight_route(route_id: str = "route_0") -> CandidateRoute:
    steps = round((ROUTE_END_LON - ROUTE_START_LON) / 0.01)
    coordinates = tuple((ROUTE_START_LON + 0.01 * i, 35.5) for i in range(steps + 1))
    edge_seconds = tuple(EDGE_SECONDS for _ in range(steps))
    edge_meters = tuple(900.0 for _ in range(steps))
    return CandidateRoute(
        route_id=route_id,
        coordinates=coordinates,
        edge_seconds=edge_seconds,
        edge_meters=edge_meters,
        duration_s=sum(edge_seconds),
        distance_m=sum(edge_meters),
    )


@pytest.fixture
def route() -> CandidateRoute:
    return straight_route()
