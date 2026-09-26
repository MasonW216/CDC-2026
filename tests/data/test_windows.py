"""County-window grid construction and labeling.

Must cover:
  * the grid has 100 counties x 4 windows per day for every day in range;
  * windows are anchored at 00:00 UTC;
  * the onset rule is exactly `window_start <= begin < window_end`;
  * an event beginning exactly on a boundary (600004, 06:00 UTC) labels the
    window starting there, not the one ending there;
  * a zero-duration boundary event (600015) labels exactly one window;
  * an event spanning the year boundary (600003) labels only its 2019 window;
  * a multi-day event (600011) labels only the window it begins in;
  * split labels are assigned by calendar year and never overlap.

Implemented now: consistency checks on the tracked fixture, so it cannot
contradict the locked rule before `stormroute.features.windows` exists.
"""

import math
from pathlib import Path

import pandas as pd
import pytest

from stormroute.config import load_config
from stormroute.data.noaa import load_events

WINDOW = pd.Timedelta(hours=6)

# TODO(milestone-3): test stormroute.features.windows against the contract above.


@pytest.fixture(scope="module")
def windows(sample_dir: Path) -> pd.DataFrame:
    frame = pd.read_csv(sample_dir / "county_windows_sample.csv", dtype={"county_fips": str})
    for column in ("window_start_utc", "window_end_utc"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    return frame


@pytest.fixture(scope="module")
def events() -> pd.DataFrame:
    return load_events("sample")[0]


def onset_label(events: pd.DataFrame, fips: str, start: pd.Timestamp) -> bool:
    """The locked rule, stated independently of production code."""
    begins = events.loc[events["county_fips"] == fips, "begin_utc"]
    return bool(((begins >= start) & (begins < start + WINDOW)).any())


def test_every_fixture_label_follows_the_onset_rule(
    windows: pd.DataFrame, events: pd.DataFrame
) -> None:
    for row in windows.itertuples():
        expected = onset_label(events, row.county_fips, row.window_start_utc)
        assert row.label_flood_event == expected, (
            f"{row.county_fips} {row.window_start_utc}: labeled {row.label_flood_event}, "
            f"onset rule says {expected}"
        )


def test_zero_duration_boundary_event_labels_only_the_window_starting_there(
    windows: pd.DataFrame,
) -> None:
    halifax = windows[windows["county_fips"] == "37083"].set_index("window_start_utc")
    assert not halifax.loc[pd.Timestamp("2021-06-03 00:00", tz="UTC"), "label_flood_event"]
    assert halifax.loc[pd.Timestamp("2021-06-03 06:00", tz="UTC"), "label_flood_event"]


def test_windows_are_six_hours_anchored_at_midnight_utc(windows: pd.DataFrame) -> None:
    assert ((windows["window_end_utc"] - windows["window_start_utc"]) == WINDOW).all()
    assert windows["window_start_utc"].dt.hour.isin([0, 6, 12, 18]).all()
    assert (windows["window_start_utc"].dt.minute == 0).all()


def test_split_matches_the_calendar_year(windows: pd.DataFrame) -> None:
    year_to_split = {
        year: name
        for name, spec in load_config("model")["splits"].items()
        if isinstance(spec, dict)
        for year in spec["years"]
    }
    expected = windows["window_start_utc"].dt.year.map(year_to_split)
    assert (windows["split"] == expected).all()


def test_month_encoding(windows: pd.DataFrame) -> None:
    angle = 2 * math.pi * windows["window_start_utc"].dt.month / 12
    assert (windows["month_sin"] - angle.map(math.sin)).abs().max() < 1e-3
    assert (windows["month_cos"] - angle.map(math.cos)).abs().max() < 1e-3
