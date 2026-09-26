"""NOAA Storm Events: locate the source files and parse them into clean events.

Two halves, both specific to this one source:

**Source files.** Resolve the annual *details* files in the NCEI directory
listing, download them to `data/raw/noaa_storm_events/`, and keep a download
record of the exact filenames, checksums, and access times. NCEI re-publishes a
year by replacing its file with a new creation-date suffix (`_cYYYYMMDD`), so the
filename is part of the data version. A file on disk that differs from its record
is never overwritten silently. `scripts/download_noaa.py` is the command-line
entry point.

**Events.** Turn raw rows into the canonical events table in
`docs/data_card.md`. Contract:
  * state and hazard filtering happen here as explicit, counted steps, never
    during download, so the raw layer stays a faithful copy of the source;
  * hazard filtering is exactly the event types in `configs/data.yaml`;
  * county FIPS are 5-character strings assembled as STATE_FIPS + CZ_FIPS.
    NCEI does *not* zero-pad these fields (`21`, not `021`), so every code is
    padded explicitly;
  * zone-coded and marine events cannot be placed in a county without a
    crosswalk. They are excluded and counted by type, never guessed;
  * timestamps are timezone-aware UTC. NCEI records a fixed offset in
    `CZ_TIMEZONE` (`EST-5`). That offset is applied as written, with no
    daylight-saving lookup;
  * original EVENT_IDs survive unchanged. Exact duplicate rows are removed and
    counted. Two different rows sharing an EVENT_ID is an error;
  * damage strings (`25.00K`, `2.5M`) are parsed, but damage, injuries, and
    deaths are descriptive outcomes and must never become model features.

Open question for the Milestone 2 spot check: every North Carolina record
carries `EST-5`, including summer events. If NCEI's times are local clock time
(EDT in summer) rather than standard time, summer events are one hour late in
UTC. Check at least one summer event against its NWS product timestamp.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

import httpx
import pandas as pd

from stormroute.config import data_mode, data_path, load_config
from stormroute.data.validation import EVENTS_COLUMNS, DataContractError

# ---------------------------------------------------------------------------
# Source files
# ---------------------------------------------------------------------------

NCEI_DETAILS_URL = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
DETAILS_FILENAME = re.compile(
    r"StormEvents_details-ftp_v1\.0_d(?P<year>\d{4})_c(?P<cdate>\d{8})\.csv\.gz"
)
RECORD_FILENAME = "download_record.json"


@dataclass(frozen=True)
class SourceFile:
    """One annual details file as published by NCEI."""

    year: int
    filename: str
    creation_date: str

    @property
    def url(self) -> str:
        """Full download URL."""
        return NCEI_DETAILS_URL + self.filename


def parse_listing(listing_html: str, years: Iterable[int]) -> dict[int, SourceFile]:
    """Find the details file for each requested year in an NCEI directory listing.

    If NCEI ever lists two creation dates for one year, the newest wins.

    Raises:
        LookupError: a requested year has no details file in the listing.
    """
    newest: dict[int, SourceFile] = {}
    for match in DETAILS_FILENAME.finditer(listing_html):
        found = SourceFile(int(match["year"]), match[0], match["cdate"])
        current = newest.get(found.year)
        if current is None or found.creation_date > current.creation_date:
            newest[found.year] = found

    wanted = sorted(set(years))
    missing = [year for year in wanted if year not in newest]
    if missing:
        raise LookupError(f"NCEI listing has no details file for year(s) {missing}")
    return {year: newest[year] for year in wanted}


def sha256_of(path: Path) -> str:
    """Hex SHA-256 of a file, read in chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class DownloadRecord:
    """What was downloaded, when, and with which checksum.

    `active` maps each year to the one filename analysis should read, so a
    re-published year cannot silently change the data under a finished analysis.
    """

    files: dict[str, dict[str, Any]] = field(default_factory=dict)
    active: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, raw_dir: Path) -> DownloadRecord:
        """Read the record from `raw_dir`, or start an empty one."""
        path = raw_dir / RECORD_FILENAME
        if not path.exists():
            return cls()
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(files=payload.get("files", {}), active=payload.get("active", {}))

    def save(self, raw_dir: Path) -> Path:
        """Write the record to `raw_dir` and return its path."""
        path = raw_dir / RECORD_FILENAME
        payload = {"source": NCEI_DETAILS_URL, "files": self.files, "active": self.active}
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def add(self, source: SourceFile, sha256: str, size: int, note: str = "downloaded") -> None:
        """Record a verified file and make it the active file for its year."""
        self.files[source.filename] = {
            "year": source.year,
            "creation_date": source.creation_date,
            "url": source.url,
            "sha256": sha256,
            "bytes": size,
            "recorded_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "note": note,
        }
        self.active[str(source.year)] = source.filename


ActionKind = Literal["skip", "download", "adopt", "conflict"]


@dataclass(frozen=True)
class PlannedAction:
    """What the downloader will do for one year, and why."""

    kind: ActionKind
    source: SourceFile
    reason: str


def plan_downloads(
    sources: Mapping[int, SourceFile],
    record: DownloadRecord,
    raw_dir: Path,
    *,
    accept_republished: bool = False,
    adopt_existing: bool = False,
) -> list[PlannedAction]:
    """Decide, without touching the network, what to do for each year.

    Every path that could replace or ignore data the team already analysed is a
    `conflict` unless the caller opted in explicitly.
    """
    actions: list[PlannedAction] = []
    for year, source in sorted(sources.items()):
        path = raw_dir / source.filename
        recorded = record.files.get(source.filename)
        previous = record.active.get(str(year))

        if path.exists():
            if recorded is None:
                kind: ActionKind = "adopt" if adopt_existing else "conflict"
                reason = "file is on disk but not in the download record"
                if not adopt_existing:
                    reason += "; delete it or pass --adopt-existing to record it as-is"
                actions.append(PlannedAction(kind, source, reason))
            elif sha256_of(path) != recorded["sha256"]:
                actions.append(
                    PlannedAction(
                        "conflict",
                        source,
                        "file on disk differs from its recorded checksum; it was modified "
                        "or corrupted. Delete it to re-download",
                    )
                )
            else:
                actions.append(PlannedAction("skip", source, "present and checksum verified"))
        elif previous is not None and previous != source.filename:
            if accept_republished:
                actions.append(
                    PlannedAction("download", source, f"NCEI re-published; replaces {previous}")
                )
            else:
                actions.append(
                    PlannedAction(
                        "conflict",
                        source,
                        f"NCEI re-published this year (recorded {previous}). Pass "
                        "--accept-republished to switch, and note it in the data manifest",
                    )
                )
        else:
            actions.append(PlannedAction("download", source, "not yet downloaded"))
    return actions


def download_file(client: httpx.Client, url: str, destination: Path) -> tuple[str, int]:
    """Stream `url` to `destination` and return (sha256, bytes).

    Writes to a `.part` file first, so an interrupted download never leaves a
    truncated file under the real name.
    """
    partial = destination.with_name(destination.name + ".part")
    digest = hashlib.sha256()
    size = 0
    try:
        with client.stream("GET", url) as response:
            response.raise_for_status()
            with partial.open("wb") as handle:
                for chunk in response.iter_bytes():
                    handle.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
        partial.replace(destination)
    finally:
        partial.unlink(missing_ok=True)
    return digest.hexdigest(), size


def active_detail_files(raw_dir: Path, years: Iterable[int]) -> list[Path]:
    """Return the recorded details file for each year, verifying it exists.

    Raises:
        FileNotFoundError: a year was never downloaded or its file is missing.
    """
    record = DownloadRecord.load(raw_dir)
    paths: list[Path] = []
    missing: list[int] = []
    for year in sorted(set(years)):
        filename = record.active.get(str(year))
        if filename is None or not (raw_dir / filename).exists():
            missing.append(year)
        else:
            paths.append(raw_dir / filename)
    if missing:
        raise FileNotFoundError(
            f"No downloaded NOAA details file for year(s) {missing} in {raw_dir}. "
            "Run `make download`, or set STORMROUTE_DATA_MODE=sample."
        )
    return paths


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

RAW_COLUMNS: tuple[str, ...] = (
    "BEGIN_YEARMONTH",
    "BEGIN_DAY",
    "BEGIN_TIME",
    "END_YEARMONTH",
    "END_DAY",
    "END_TIME",
    "EPISODE_ID",
    "EVENT_ID",
    "STATE",
    "STATE_FIPS",
    "EVENT_TYPE",
    "CZ_TYPE",
    "CZ_FIPS",
    "CZ_NAME",
    "CZ_TIMEZONE",
    "INJURIES_DIRECT",
    "INJURIES_INDIRECT",
    "DEATHS_DIRECT",
    "DEATHS_INDIRECT",
    "DAMAGE_PROPERTY",
    "SOURCE",
)

_DAMAGE = re.compile(r"(?P<amount>\d+(?:\.\d+)?)(?P<unit>[KMB]?)", re.IGNORECASE)
_DAMAGE_UNITS = {"": 1.0, "K": 1e3, "M": 1e6, "B": 1e9}
_UTC_OFFSET = re.compile(r"(?P<zone>[A-Z]{3})-(?P<hours>\d{1,2})")


def parse_damage(value: str | None) -> float:
    """Convert an NCEI damage string to US dollars.

    Empty means *not reported*, which is not the same as zero, so it returns NaN.

    Examples: `25.00K` → 25000.0, `2.5M` → 2500000.0, `0.00K` → 0.0, `` → nan.

    Raises:
        ValueError: the string is not a number with an optional K, M, or B suffix.
    """
    text = (value or "").strip()
    if not text:
        return math.nan
    match = _DAMAGE.fullmatch(text)
    if match is None:
        raise ValueError(f"Unparseable NOAA damage string: {value!r}")
    return float(match["amount"]) * _DAMAGE_UNITS[match["unit"].upper()]


def parse_utc_offset(timezone_field: str) -> timedelta:
    """Convert an NCEI `CZ_TIMEZONE` value such as `EST-5` to a UTC offset.

    Raises:
        ValueError: the value does not carry an explicit offset.
    """
    match = _UTC_OFFSET.fullmatch(timezone_field.strip())
    if match is None:
        raise ValueError(f"CZ_TIMEZONE {timezone_field!r} has no explicit UTC offset")
    return -timedelta(hours=int(match["hours"]))


def _utc_timestamps(
    yearmonth: pd.Series[str], day: pd.Series[str], hhmm: pd.Series[str], offsets: pd.Series
) -> pd.Series:
    """Build UTC timestamps from NCEI's split, unpadded date and time fields.

    Returns NaT wherever the fields are empty or do not form a real date.
    """
    stamp = yearmonth.str.strip() + day.str.strip().str.zfill(2) + hhmm.str.strip().str.zfill(4)
    empty = (yearmonth.str.strip() == "") | (day.str.strip() == "") | (hhmm.str.strip() == "")
    local = pd.to_datetime(stamp.where(~empty), format="%Y%m%d%H%M", errors="coerce")
    return (local - offsets).dt.tz_localize("UTC")


def _counts(values: pd.Series[str]) -> pd.Series:
    """Parse a count column; empty means not reported (NA), never zero."""
    return pd.to_numeric(values.str.strip().replace("", pd.NA), errors="raise").astype("Int64")


@dataclass
class IngestReport:
    """Row counts at every filtering step, for the EDA and the data card."""

    source_files: list[str]
    rows_read: int = 0
    rows_in_state: int = 0
    rows_qualifying_type: int = 0
    exact_duplicates_removed: int = 0
    excluded_unresolved_geography: dict[str, int] = field(default_factory=dict)
    excluded_invalid_begin: int = 0
    excluded_invalid_end: int = 0
    excluded_end_before_begin: int = 0
    missing_end_kept: int = 0
    zero_duration: int = 0
    events_out: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Plain-dict form for JSON export."""
        return asdict(self)


def read_details(paths: Sequence[Path], columns: Sequence[str] | None = RAW_COLUMNS) -> pd.DataFrame:
    """Read NCEI details files as strings, exactly as published.

    Every column is read as text, so no county code or time loses a leading
    zero to integer parsing. Pass `columns=None` to read all 51 columns.
    """
    frames = [
        pd.read_csv(
            path,
            dtype=str,
            keep_default_na=False,
            usecols=list(columns) if columns is not None else None,
        )
        for path in paths
    ]
    return pd.concat(frames, ignore_index=True)


def clean_events(
    raw: pd.DataFrame,
    *,
    source_files: Sequence[str] = (),
    state_fips: str | None = None,
    event_types: Sequence[str] | None = None,
) -> tuple[pd.DataFrame, IngestReport]:
    """Filter and parse raw NCEI rows into the canonical events table.

    Defaults come from `configs/data.yaml`. Every excluded row is counted in the
    returned report.

    Raises:
        DataContractError: raw columns are missing, or two different rows share
            an EVENT_ID.
    """
    data_config = load_config("data")
    state_fips = state_fips or str(data_config["geography"]["state_fips"])
    event_types = list(event_types or data_config["label"]["hazard_event_types"])

    missing_columns = [column for column in RAW_COLUMNS if column not in raw.columns]
    if missing_columns:
        raise DataContractError([f"raw NOAA data is missing columns {missing_columns}"])

    report = IngestReport(source_files=list(source_files), rows_read=len(raw))
    rows = raw.loc[:, list(RAW_COLUMNS)]

    rows = rows[rows["STATE_FIPS"].str.strip().str.zfill(2) == state_fips.zfill(2)]
    report.rows_in_state = len(rows)

    rows = rows[rows["EVENT_TYPE"].str.strip().isin(event_types)]
    report.rows_qualifying_type = len(rows)

    before = len(rows)
    rows = rows.drop_duplicates()
    report.exact_duplicates_removed = before - len(rows)
    conflicting = rows.loc[rows["EVENT_ID"].duplicated(keep=False), "EVENT_ID"]
    if not conflicting.empty:
        raise DataContractError(
            [f"different rows share EVENT_ID(s) {sorted(conflicting.unique())[:10]}"]
        )

    county_coded = rows["CZ_TYPE"].str.strip() == "C"
    unresolved = rows.loc[~county_coded, "CZ_TYPE"].str.strip().value_counts()
    report.excluded_unresolved_geography = {str(k): int(v) for k, v in unresolved.items()}
    rows = rows[county_coded]

    offsets = rows["CZ_TIMEZONE"].map(parse_utc_offset)
    begin = _utc_timestamps(rows["BEGIN_YEARMONTH"], rows["BEGIN_DAY"], rows["BEGIN_TIME"], offsets)
    end = _utc_timestamps(rows["END_YEARMONTH"], rows["END_DAY"], rows["END_TIME"], offsets)

    end_fields_empty = (
        (rows["END_YEARMONTH"].str.strip() == "")
        | (rows["END_DAY"].str.strip() == "")
        | (rows["END_TIME"].str.strip() == "")
    )
    invalid_begin = begin.isna()
    invalid_end = end.isna() & ~end_fields_empty
    end_before_begin = end.notna() & begin.notna() & (end < begin)
    keep = ~(invalid_begin | invalid_end | end_before_begin)

    report.excluded_invalid_begin = int(invalid_begin.sum())
    report.excluded_invalid_end = int((invalid_end & ~invalid_begin).sum())
    report.excluded_end_before_begin = int(end_before_begin.sum())
    report.missing_end_kept = int((end_fields_empty & keep).sum())
    report.zero_duration = int(((end == begin) & keep).sum())

    rows, begin, end = rows[keep], begin[keep], end[keep]

    events = pd.DataFrame(
        {
            "event_id": rows["EVENT_ID"].str.strip().astype("string"),
            "episode_id": rows["EPISODE_ID"].str.strip().astype("string"),
            "county_fips": (
                rows["STATE_FIPS"].str.strip().str.zfill(2) + rows["CZ_FIPS"].str.strip().str.zfill(3)
            ).astype("string"),
            "begin_utc": begin,
            "end_utc": end,
            "event_type": pd.Categorical(rows["EVENT_TYPE"].str.strip(), categories=event_types),
            "source": rows["SOURCE"].str.strip().astype("string"),
            "injuries": _counts(rows["INJURIES_DIRECT"]) + _counts(rows["INJURIES_INDIRECT"]),
            "deaths": _counts(rows["DEATHS_DIRECT"]) + _counts(rows["DEATHS_INDIRECT"]),
            "property_damage_usd": rows["DAMAGE_PROPERTY"].map(parse_damage).astype("float64"),
        }
    )
    events = events.sort_values(["begin_utc", "event_id"], kind="stable").reset_index(drop=True)
    report.events_out = len(events)
    return events.loc[:, list(EVENTS_COLUMNS)], report


def load_events(
    mode: Literal["full", "sample"] | None = None,
    *,
    raw_dir: Path | None = None,
    years: Iterable[int] | None = None,
) -> tuple[pd.DataFrame, IngestReport]:
    """Load clean North Carolina flood events in `sample` or `full` mode.

    `sample` reads the tracked fixture and needs no download. `full` reads the
    active files from the download record. The mode defaults to
    STORMROUTE_DATA_MODE.
    """
    mode = mode or data_mode()
    if mode == "sample":
        paths = [data_path("sample") / "storm_events_sample.csv"]
    else:
        period = load_config("data")["period"]
        wanted = years or range(period["start_year"], period["end_year"] + 1)
        paths = active_detail_files(raw_dir or data_path("noaa_raw"), wanted)
    return clean_events(read_details(paths), source_files=[path.name for path in paths])
