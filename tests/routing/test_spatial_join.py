"""County assignment for sampled route points.

Asserts known coordinates land in the expected county, that a point outside
North Carolina is flagged as outside the modeled geography rather than snapped
to the nearest county, that consecutive samples in one (county, window) collapse
into a single interval, and that coverage fraction is reported.
"""

from datetime import UTC, datetime

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point

from stormroute.data.geography import load_sample_counties
from stormroute.routing.sampling import sample_route
from stormroute.routing.spatial_join import (
    INTERVAL_COLUMNS,
    collapse_intervals,
    county_for_points,
    modeled_fraction,
)

DEPARTURE = datetime(2024, 9, 27, 13, 0, tzinfo=UTC)


def points(*lat_lon: tuple[float, float]):
    return gpd.GeoSeries([Point(lon, lat) for lat, lon in lat_lon], crs="EPSG:4326")


# --- county_for_points -----------------------------------------------------------


def test_known_nc_coordinates_land_in_the_expected_county():
    counties = load_sample_counties()
    found = county_for_points(points((35.5951, -82.5515), (35.2271, -80.8431)), counties)
    assert found.tolist() == ["37021", "37119"]  # Buncombe, Mecklenburg


def test_point_outside_north_carolina_is_not_snapped():
    counties = load_sample_counties()
    knoxville = (35.9606, -83.9207)
    found = county_for_points(points(knoxville), counties)
    assert found.isna().all()


# --- sampled route ---------------------------------------------------------------


@pytest.fixture
def samples(route, counties):
    return sample_route(route, DEPARTURE, counties)


def test_each_stretch_takes_the_county_it_lies_in(samples):
    inside = samples[samples["longitude"] < -81.6 - 1e-6]
    assert (inside["county_fips"] == "37001").all()


def test_stretch_beyond_the_modeled_geography_is_flagged(samples):
    outside = samples[samples["longitude"] > -81.0 + 1e-6]
    assert not outside.empty
    assert outside["county_fips"].isna().all()


# --- collapse_intervals ----------------------------------------------------------


def test_intervals_are_unique_per_route_county_and_window(samples):
    intervals = collapse_intervals(samples)
    assert list(intervals.columns) == INTERVAL_COLUMNS
    key = intervals[["route_id", "county_fips", "window_start_utc"]].astype(str)
    assert not key.duplicated().any()


def test_intervals_preserve_total_time_and_distance(samples, route):
    intervals = collapse_intervals(samples)
    assert intervals["exposure_minutes"].sum() == pytest.approx(route.duration_s / 60)
    assert intervals["distance_km"].sum() == pytest.approx(samples["distance_km"].iloc[-1])


def test_intervals_follow_route_order_and_flag_outside_portions(samples):
    intervals = collapse_intervals(samples)
    assert intervals["county_fips"].tolist()[:3] == ["37001", "37003", "37005"]
    assert intervals["in_modeled_geography"].tolist() == [True, True, True, False]


def test_repeated_visits_to_a_county_window_collapse_into_one_interval(route, counties):
    # Drive the route out and back: every county-window is visited twice.
    out = back = route
    coordinates = out.coordinates + tuple(reversed(back.coordinates))[1:]
    round_trip = type(out)(
        route_id="route_0",
        coordinates=coordinates,
        edge_seconds=out.edge_seconds + back.edge_seconds,
        edge_meters=out.edge_meters + back.edge_meters,
        duration_s=2 * out.duration_s,
        distance_m=2 * out.distance_m,
    )
    samples = sample_route(round_trip, DEPARTURE, counties)
    intervals = collapse_intervals(samples)
    assert len(intervals) == 4
    assert intervals["exposure_minutes"].sum() == pytest.approx(round_trip.duration_s / 60)


def test_modeled_fraction_is_the_share_of_distance_inside_the_counties(samples):
    fraction = modeled_fraction(collapse_intervals(samples))
    assert fraction == pytest.approx(1.0 / 1.1, rel=0.02)


def test_entry_time_is_the_first_arrival_in_the_interval(samples):
    intervals = collapse_intervals(samples)
    assert intervals["entry_utc"].iloc[0] == pd.Timestamp(DEPARTURE)
    assert intervals["entry_utc"].is_monotonic_increasing
