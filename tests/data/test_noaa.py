"""NOAA parsing, filtering, validation, and download safety.

Expected values come from data/sample/storm_events_sample.csv; its README
explains why each row exists. All fixture times are EST-5, so UTC = local + 5h.
"""

import hashlib
import math
from pathlib import Path

import httpx
import pandas as pd
import pytest

from stormroute.data.noaa import (
    DownloadRecord,
    SourceFile,
    active_detail_files,
    clean_events,
    download_file,
    load_events,
    parse_damage,
    parse_listing,
    parse_utc_offset,
    plan_downloads,
    read_details,
)
from stormroute.data.validation import EVENTS_COLUMNS, DataContractError, validate_events

HAZARDS = ["Flood", "Flash Flood", "Debris Flow"]


def utc(text: str) -> pd.Timestamp:
    return pd.Timestamp(text, tz="UTC")


@pytest.fixture(scope="module")
def raw(storm_events_sample: Path) -> pd.DataFrame:
    return read_details([storm_events_sample])


@pytest.fixture(scope="module")
def cleaned(raw: pd.DataFrame) -> tuple[pd.DataFrame, object]:
    return clean_events(raw, source_files=["storm_events_sample.csv"])


@pytest.fixture(scope="module")
def events(cleaned: tuple[pd.DataFrame, object]) -> pd.DataFrame:
    return cleaned[0].set_index("event_id", drop=False)


# ---------------------------------------------------------------------------
# Field parsers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "dollars"),
    [
        ("25.00K", 25_000.0),
        ("75K", 75_000.0),
        ("2.5M", 2_500_000.0),
        ("150.00M", 150_000_000.0),
        ("1B", 1_000_000_000.0),
        ("0.00K", 0.0),
        ("12", 12.0),
        ("2.5m", 2_500_000.0),
        (" 1.00K ", 1_000.0),
    ],
)
def test_parse_damage(text: str, dollars: float) -> None:
    assert parse_damage(text) == dollars


@pytest.mark.parametrize("text", ["", "   ", None])
def test_empty_damage_is_not_reported_rather_than_zero(text: str | None) -> None:
    assert math.isnan(parse_damage(text))


@pytest.mark.parametrize("text", ["abc", "1.2X", "-5K", "K", "1,000K"])
def test_unparseable_damage_raises(text: str) -> None:
    with pytest.raises(ValueError, match="Unparseable"):
        parse_damage(text)


@pytest.mark.parametrize(
    ("field", "hours"), [("EST-5", -5), ("EDT-4", -4), ("CST-6", -6), (" EST-5 ", -5)]
)
def test_parse_utc_offset(field: str, hours: int) -> None:
    assert parse_utc_offset(field) == pd.Timedelta(hours=hours)


@pytest.mark.parametrize("field", ["EST", "", "UTC+5", "est-5"])
def test_timezone_without_explicit_offset_raises(field: str) -> None:
    with pytest.raises(ValueError, match="explicit UTC offset"):
        parse_utc_offset(field)


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------


def test_read_details_keeps_every_field_as_published(raw: pd.DataFrame) -> None:
    by_id = raw.drop_duplicates().set_index("EVENT_ID")
    assert by_id.loc["600015", "CZ_FIPS"] == "083", "default parsing would turn this into 83"
    assert by_id.loc["600001", "CZ_FIPS"] == "21", "NCEI publishes county codes unpadded"
    assert by_id.loc["600009", "BEGIN_TIME"] == "0"
    assert by_id.loc["600010", "DAMAGE_PROPERTY"] == ""


# ---------------------------------------------------------------------------
# Filtering and counts
# ---------------------------------------------------------------------------


def test_every_filtering_step_is_counted(cleaned: tuple[pd.DataFrame, object]) -> None:
    report = cleaned[1]
    assert report.to_dict() == {
        "source_files": ["storm_events_sample.csv"],
        "rows_read": 16,
        "rows_in_state": 15,  # South Carolina removed
        "rows_qualifying_type": 13,  # Thunderstorm Wind and Heavy Rain removed
        "exact_duplicates_removed": 1,
        "excluded_unresolved_geography": {"Z": 1},
        "excluded_invalid_begin": 0,
        "excluded_invalid_end": 0,
        "excluded_end_before_begin": 0,
        "missing_end_kept": 1,
        "zero_duration": 1,
        "events_out": 11,
    }


def test_exactly_the_expected_events_survive(events: pd.DataFrame) -> None:
    expected = {f"6000{n:02d}" for n in (1, 2, 3, 4, 9, 10, 11, 12, 13, 14, 15)}
    assert set(events["event_id"]) == expected


def test_hazard_filter_is_exactly_the_locked_three(events: pd.DataFrame) -> None:
    assert set(events["event_type"]) <= set(HAZARDS)
    assert list(events["event_type"].cat.categories) == HAZARDS


def test_heavy_rain_never_qualifies(events: pd.DataFrame) -> None:
    """Guards the precedence decision in docs/adr/0000-specification-precedence.md."""
    assert "600007" not in events.index


def test_zone_coded_event_is_excluded_not_guessed(events: pd.DataFrame) -> None:
    assert "600005" not in events.index


def test_output_schema_and_dtypes(events: pd.DataFrame) -> None:
    assert tuple(events.columns) == EVENTS_COLUMNS
    assert events["county_fips"].dtype == "string"
    assert events["event_id"].dtype == "string"
    assert str(events["begin_utc"].dtype) == "datetime64[ns, UTC]"
    assert str(events["end_utc"].dtype) == "datetime64[ns, UTC]"
    assert events["injuries"].dtype == "Int64"
    validate_events(events.reset_index(drop=True), HAZARDS)


# ---------------------------------------------------------------------------
# County FIPS
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("event_id", "fips"),
    [("600001", "37021"), ("600002", "37001"), ("600003", "37087"), ("600015", "37083")],
)
def test_county_fips_are_padded_five_character_strings(
    events: pd.DataFrame, event_id: str, fips: str
) -> None:
    assert events.loc[event_id, "county_fips"] == fips


# ---------------------------------------------------------------------------
# Timestamps
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("event_id", "begin", "end"),
    [
        ("600001", "2016-08-12 19:30", "2016-08-12 22:00"),  # ordinary
        ("600002", "2017-09-09 03:30", "2017-09-09 08:30"),  # crosses local midnight
        ("600003", "2019-12-31 23:00", "2020-01-01 09:00"),  # crosses the UTC year
        ("600004", "2018-08-15 06:00", "2018-08-15 12:00"),  # exact window boundaries
        ("600009", "2022-06-06 05:00", "2022-06-06 11:00"),  # BEGIN_TIME "0"
        ("600014", "2024-03-16 04:50", "2024-03-16 05:10"),  # END_TIME "10"
        ("600015", "2021-06-03 06:00", "2021-06-03 06:00"),  # zero duration
    ],
)
def test_utc_conversion(events: pd.DataFrame, event_id: str, begin: str, end: str) -> None:
    assert events.loc[event_id, "begin_utc"] == utc(begin)
    assert events.loc[event_id, "end_utc"] == utc(end)


def test_missing_end_time_is_kept_as_nat_not_coerced(events: pd.DataFrame) -> None:
    assert pd.isna(events.loc["600013", "end_utc"])
    assert events.loc["600013", "begin_utc"] == utc("2015-09-29 20:00")


# ---------------------------------------------------------------------------
# Outcomes (descriptive only)
# ---------------------------------------------------------------------------


def test_direct_and_indirect_casualties_are_summed(events: pd.DataFrame) -> None:
    assert events.loc["600011", "injuries"] == 15
    assert events.loc["600011", "deaths"] == 5


def test_damage_is_parsed_and_empty_stays_missing(events: pd.DataFrame) -> None:
    assert events.loc["600011", "property_damage_usd"] == 150_000_000.0
    assert events.loc["600002", "property_damage_usd"] == 75_000.0
    assert math.isnan(events.loc["600010", "property_damage_usd"])


# ---------------------------------------------------------------------------
# Rejections
# ---------------------------------------------------------------------------


def _one_row(raw: pd.DataFrame, event_id: str) -> pd.DataFrame:
    return raw[raw["EVENT_ID"] == event_id].drop_duplicates().reset_index(drop=True)


def test_conflicting_rows_sharing_an_event_id_raise(raw: pd.DataFrame) -> None:
    twin = _one_row(raw, "600001").assign(DAMAGE_PROPERTY="99.00K")
    with pytest.raises(DataContractError, match="share EVENT_ID"):
        clean_events(pd.concat([_one_row(raw, "600001"), twin]))


def test_invalid_begin_is_excluded_and_counted(raw: pd.DataFrame) -> None:
    bad = _one_row(raw, "600001").assign(BEGIN_DAY="31", BEGIN_YEARMONTH="201602")
    events, report = clean_events(bad)
    assert events.empty
    assert report.excluded_invalid_begin == 1


def test_end_before_begin_is_excluded_and_counted(raw: pd.DataFrame) -> None:
    bad = _one_row(raw, "600001").assign(END_TIME="1000")
    events, report = clean_events(bad)
    assert events.empty
    assert report.excluded_end_before_begin == 1


def test_missing_raw_columns_raise(raw: pd.DataFrame) -> None:
    with pytest.raises(DataContractError, match="missing columns"):
        clean_events(raw.drop(columns=["CZ_TIMEZONE"]))


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@pytest.fixture
def valid(events: pd.DataFrame) -> pd.DataFrame:
    return events.reset_index(drop=True).copy()


def test_validation_rejects_duplicate_event_ids(valid: pd.DataFrame) -> None:
    broken = pd.concat([valid, valid.iloc[[0]]], ignore_index=True)
    with pytest.raises(DataContractError, match="not unique"):
        validate_events(broken, HAZARDS)


def test_validation_rejects_non_nc_or_unpadded_fips(valid: pd.DataFrame) -> None:
    valid.loc[0, "county_fips"] = "3721"
    valid.loc[1, "county_fips"] = "37002"  # even numbers are not NC counties
    with pytest.raises(DataContractError, match="not a North Carolina county") as error:
        validate_events(valid, HAZARDS)
    assert "3721" in str(error.value) and "37002" in str(error.value)


def test_validation_rejects_naive_timestamps(valid: pd.DataFrame) -> None:
    valid["begin_utc"] = valid["begin_utc"].dt.tz_localize(None)
    with pytest.raises(DataContractError, match="timezone-aware UTC"):
        validate_events(valid, HAZARDS)


def test_validation_rejects_end_before_begin(valid: pd.DataFrame) -> None:
    valid.loc[0, "end_utc"] = valid.loc[0, "begin_utc"] - pd.Timedelta(hours=1)
    with pytest.raises(DataContractError, match="precedes"):
        validate_events(valid, HAZARDS)


def test_validation_rejects_other_hazards(valid: pd.DataFrame) -> None:
    valid["event_type"] = valid["event_type"].cat.add_categories("Heavy Rain")
    valid.loc[0, "event_type"] = "Heavy Rain"
    with pytest.raises(DataContractError, match="locked hazard list"):
        validate_events(valid, HAZARDS)


def test_validation_reports_every_failure_at_once(valid: pd.DataFrame) -> None:
    valid.loc[0, "county_fips"] = "99999"
    valid.loc[1, "injuries"] = -1
    with pytest.raises(DataContractError) as error:
        validate_events(valid, HAZARDS)
    assert len(error.value.failures) == 2


def test_validation_rejects_wrong_columns(valid: pd.DataFrame) -> None:
    with pytest.raises(DataContractError, match="columns must be exactly"):
        validate_events(valid.drop(columns=["source"]), HAZARDS)


# ---------------------------------------------------------------------------
# Source files and download safety
# ---------------------------------------------------------------------------

LISTING = """
<a href="StormEvents_details-ftp_v1.0_d2015_c20250101.csv.gz">x</a>
<a href="StormEvents_details-ftp_v1.0_d2015_c20260323.csv.gz">x</a>
<a href="StormEvents_details-ftp_v1.0_d2016_c20260323.csv.gz">x</a>
<a href="StormEvents_locations-ftp_v1.0_d2016_c20260323.csv.gz">x</a>
"""


def test_parse_listing_picks_the_newest_details_file_per_year() -> None:
    sources = parse_listing(LISTING, [2015, 2016])
    assert sources[2015].filename == "StormEvents_details-ftp_v1.0_d2015_c20260323.csv.gz"
    assert sources[2016].creation_date == "20260323"
    assert sources[2016].url.endswith("/csvfiles/" + sources[2016].filename)


def test_parse_listing_raises_for_a_missing_year() -> None:
    with pytest.raises(LookupError, match=r"\[2017\]"):
        parse_listing(LISTING, [2016, 2017])


def _source(year: int = 2016, cdate: str = "20260323") -> SourceFile:
    return SourceFile(year, f"StormEvents_details-ftp_v1.0_d{year}_c{cdate}.csv.gz", cdate)


def _recorded(raw_dir: Path, source: SourceFile, content: bytes) -> DownloadRecord:
    (raw_dir / source.filename).write_bytes(content)
    record = DownloadRecord()
    record.add(source, hashlib.sha256(content).hexdigest(), len(content))
    return record


def test_plan_downloads_a_new_year(tmp_path: Path) -> None:
    [action] = plan_downloads({2016: _source()}, DownloadRecord(), tmp_path)
    assert action.kind == "download"


def test_plan_skips_a_verified_file(tmp_path: Path) -> None:
    record = _recorded(tmp_path, _source(), b"original")
    [action] = plan_downloads({2016: _source()}, record, tmp_path)
    assert action.kind == "skip"


def test_plan_refuses_a_file_that_differs_from_its_record(tmp_path: Path) -> None:
    record = _recorded(tmp_path, _source(), b"original")
    (tmp_path / _source().filename).write_bytes(b"tampered")
    [action] = plan_downloads({2016: _source()}, record, tmp_path)
    assert action.kind == "conflict"
    assert "differs" in action.reason


def test_plan_refuses_a_republished_year_unless_accepted(tmp_path: Path) -> None:
    record = _recorded(tmp_path, _source(cdate="20250101"), b"old")
    newer = {2016: _source(cdate="20260323")}
    [refused] = plan_downloads(newer, record, tmp_path)
    [accepted] = plan_downloads(newer, record, tmp_path, accept_republished=True)
    assert refused.kind == "conflict" and "re-published" in refused.reason
    assert accepted.kind == "download"


def test_plan_refuses_an_unrecorded_file_unless_adopted(tmp_path: Path) -> None:
    (tmp_path / _source().filename).write_bytes(b"from somewhere")
    [refused] = plan_downloads({2016: _source()}, DownloadRecord(), tmp_path)
    [adopted] = plan_downloads({2016: _source()}, DownloadRecord(), tmp_path, adopt_existing=True)
    assert refused.kind == "conflict"
    assert adopted.kind == "adopt"


def test_download_record_round_trips(tmp_path: Path) -> None:
    record = _recorded(tmp_path, _source(), b"content")
    record.save(tmp_path)
    loaded = DownloadRecord.load(tmp_path)
    assert loaded.active == {"2016": _source().filename}
    assert loaded.files[_source().filename]["sha256"] == hashlib.sha256(b"content").hexdigest()


def test_download_file_streams_and_checksums(tmp_path: Path) -> None:
    body = b"csv,content\n" * 1000
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=body))
    destination = tmp_path / "file.csv.gz"
    with httpx.Client(transport=transport) as client:
        sha256, size = download_file(client, "https://example.test/file.csv.gz", destination)
    assert destination.read_bytes() == body
    assert (sha256, size) == (hashlib.sha256(body).hexdigest(), len(body))
    assert not list(tmp_path.glob("*.part"))


def test_failed_download_leaves_nothing_behind(tmp_path: Path) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(503))
    destination = tmp_path / "file.csv.gz"
    with httpx.Client(transport=transport) as client, pytest.raises(httpx.HTTPStatusError):
        download_file(client, "https://example.test/file.csv.gz", destination)
    assert list(tmp_path.iterdir()) == []


def test_active_detail_files_requires_a_download(tmp_path: Path) -> None:
    record = _recorded(tmp_path, _source(), b"content")
    record.save(tmp_path)
    assert active_detail_files(tmp_path, [2016]) == [tmp_path / _source().filename]
    with pytest.raises(FileNotFoundError, match="make download"):
        active_detail_files(tmp_path, [2016, 2017])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def test_load_events_in_sample_mode_needs_no_download() -> None:
    events, report = load_events("sample")
    assert len(events) == 11
    assert report.source_files == ["storm_events_sample.csv"]
