"""Route sampling and arrival times.

Asserts spacing stays within 5-10 km, that a sample is emitted at every county
boundary crossing, that cumulative minutes increase monotonically and match the
route duration, and that arrival times map to the correct six-hour window
including across a window boundary and across midnight UTC.
"""

from datetime import UTC, datetime

import numpy as np
import pandas as pd
import pytest

from stormroute.routing.sampling import SAMPLE_COLUMNS, sample_route, window_start_utc

DEPARTURE = datetime(2024, 9, 27, 13, 0, tzinfo=UTC)


def ts(text: str) -> pd.Timestamp:
    return pd.Timestamp(text)


# --- window_start_utc ------------------------------------------------------------


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        ("2024-09-27T05:59:59Z", "2024-09-27T00:00:00Z"),
        ("2024-09-27T06:00:00Z", "2024-09-27T06:00:00Z"),
        ("2024-09-27T23:59:00Z", "2024-09-27T18:00:00Z"),
        ("2024-09-27T12:00:00-04:00", "2024-09-27T12:00:00Z"),  # 16:00 UTC
        ("2025-01-01T00:00:00Z", "2025-01-01T00:00:00Z"),
    ],
)
def test_window_start_is_anchored_at_00_06_12_18_utc(moment, expected):
    assert window_start_utc(ts(moment)) == ts(expected)


def test_naive_timestamps_are_rejected():
    with pytest.raises(ValueError, match="timezone"):
        window_start_utc(pd.Timestamp("2024-09-27T12:00:00"))


# --- sample_route ----------------------------------------------------------------


@pytest.fixture
def samples(route, counties):
    return sample_route(route, DEPARTURE, counties)


def test_columns_are_the_canonical_route_sample_columns(samples):
    assert list(samples.columns) == SAMPLE_COLUMNS


def test_first_and_last_samples_are_the_route_endpoints(samples, route):
    first, last = samples.iloc[0], samples.iloc[-1]
    assert (first["longitude"], first["latitude"]) == pytest.approx(route.coordinates[0])
    assert (last["longitude"], last["latitude"]) == pytest.approx(route.coordinates[-1])


def test_no_gap_between_samples_exceeds_ten_km(samples):
    assert samples["distance_km"].diff().dropna().max() <= 10.0


def test_regular_spacing_is_within_five_to_ten_km(route, counties):
    samples = sample_route(route, DEPARTURE, counties, spacing_km=8.0)
    assert 5.0 <= samples["distance_km"].diff().dropna().max() <= 10.0


def test_spacing_outside_the_configured_range_is_rejected(route, counties):
    with pytest.raises(ValueError, match="spacing"):
        sample_route(route, DEPARTURE, counties, spacing_km=20.0)


@pytest.mark.parametrize("boundary_lon", [-82.0, -81.6, -81.3, -81.0])
def test_a_sample_falls_on_every_county_boundary(samples, boundary_lon):
    assert np.isclose(samples["longitude"], boundary_lon, atol=1e-6).any()


def test_cumulative_minutes_are_monotonic_and_match_the_route_duration(samples, route):
    minutes = samples["cumulative_minutes"]
    assert minutes.iloc[0] == 0
    assert minutes.is_monotonic_increasing
    assert minutes.iloc[-1] == pytest.approx(route.duration_s / 60)


def test_segment_minutes_are_time_to_the_next_sample(samples, route):
    expected = samples["cumulative_minutes"].shift(-1) - samples["cumulative_minutes"]
    assert np.allclose(samples["segment_minutes"].iloc[:-1], expected.iloc[:-1])
    assert samples["segment_minutes"].iloc[-1] == 0
    assert samples["segment_minutes"].sum() == pytest.approx(route.duration_s / 60)


def test_arrival_is_departure_plus_cumulative_minutes(samples):
    expected = pd.Timestamp(DEPARTURE) + pd.to_timedelta(samples["cumulative_minutes"], unit="min")
    assert (samples["arrival_utc"] - expected).abs().max() < pd.Timedelta(seconds=1)
    assert str(samples["arrival_utc"].dt.tz) == "UTC"


def test_a_sample_is_emitted_at_a_window_boundary_crossed_mid_trip(route, counties):
    # The route takes 66 minutes; leaving at 05:30 UTC crosses 06:00 UTC.
    departure = datetime(2024, 9, 27, 5, 30, tzinfo=UTC)
    samples = sample_route(route, departure, counties)
    boundary = pd.Timestamp("2024-09-27T06:00:00Z")
    assert ((samples["arrival_utc"] - boundary).abs() < pd.Timedelta(seconds=1)).any()
    before = samples[samples["arrival_utc"] < boundary - pd.Timedelta(seconds=1)]
    after = samples[samples["arrival_utc"] >= boundary - pd.Timedelta(seconds=1)]
    assert (before["window_start_utc"] == pd.Timestamp("2024-09-27T00:00:00Z")).all()
    assert (after["window_start_utc"] == boundary).all()


def test_window_mapping_across_midnight_utc(route, counties):
    departure = datetime(2024, 12, 31, 23, 30, tzinfo=UTC)
    samples = sample_route(route, departure, counties)
    assert set(samples["window_start_utc"]) == {
        pd.Timestamp("2024-12-31T18:00:00Z"),
        pd.Timestamp("2025-01-01T00:00:00Z"),
    }


def test_naive_departure_is_rejected(route, counties):
    with pytest.raises(ValueError, match="timezone"):
        sample_route(route, datetime(2024, 9, 27, 13, 0), counties)


def test_sample_order_is_sequential(samples):
    assert samples["sample_order"].tolist() == list(range(len(samples)))
