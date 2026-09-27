"""Command-line behavior of scripts/download_boundaries.py.

The network and the real TIGER reader are replaced with fakes, so these tests
exercise exit codes and the record/validate ordering without a download.
"""

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

from stormroute.config import REPO_ROOT
from stormroute.data.geography import RECORD_FILENAME, TIGER_COUNTY_FILENAME
from stormroute.data.validation import DataContractError


def load_script() -> ModuleType:
    path = REPO_ROOT / "scripts" / "download_boundaries.py"
    spec = importlib.util.spec_from_file_location("download_boundaries", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def script(tmp_path, monkeypatch):
    module = load_script()
    monkeypatch.setattr(module, "data_path", lambda key: tmp_path)

    def fake_download(client, url, destination: Path):
        destination.write_bytes(b"downloaded bytes")
        return "unused", 16

    monkeypatch.setattr(module, "download_file", fake_download)
    return module


def accept(module, monkeypatch) -> None:
    monkeypatch.setattr(module, "load_nc_counties", lambda path: [None] * 100)


def reject(module, monkeypatch) -> None:
    def fail(path):
        raise DataContractError(["99 counties, expected exactly 100"])

    monkeypatch.setattr(module, "load_nc_counties", fail)


def recorded(tmp_path: Path) -> dict:
    path = tmp_path / RECORD_FILENAME
    return json.loads(path.read_text())["files"] if path.exists() else {}


def test_download_records_only_after_validation(script, tmp_path, monkeypatch):
    accept(script, monkeypatch)
    assert script.main([]) == 0
    assert TIGER_COUNTY_FILENAME in recorded(tmp_path)


def test_invalid_download_is_deleted_and_not_recorded(script, tmp_path, monkeypatch):
    reject(script, monkeypatch)
    assert script.main([]) == 1
    assert not (tmp_path / TIGER_COUNTY_FILENAME).exists()
    assert recorded(tmp_path) == {}


def test_unreadable_download_is_handled_without_a_traceback(script, tmp_path, monkeypatch):
    def unreadable(path):
        raise RuntimeError("not a recognized data source")

    monkeypatch.setattr(script, "load_nc_counties", unreadable)
    assert script.main([]) == 1
    assert recorded(tmp_path) == {}


def test_unrecorded_file_on_disk_is_a_conflict(script, tmp_path, monkeypatch):
    accept(script, monkeypatch)
    (tmp_path / TIGER_COUNTY_FILENAME).write_bytes(b"someone else's file")
    assert script.main([]) == 1
    assert (tmp_path / TIGER_COUNTY_FILENAME).read_bytes() == b"someone else's file"


def test_adopt_existing_records_a_valid_file(script, tmp_path, monkeypatch):
    accept(script, monkeypatch)
    (tmp_path / TIGER_COUNTY_FILENAME).write_bytes(b"already here")
    assert script.main(["--adopt-existing"]) == 0
    assert recorded(tmp_path)[TIGER_COUNTY_FILENAME]["note"] == "adopted from disk"


def test_adopting_an_invalid_file_keeps_it_but_does_not_record_it(script, tmp_path, monkeypatch):
    reject(script, monkeypatch)
    (tmp_path / TIGER_COUNTY_FILENAME).write_bytes(b"already here")
    assert script.main(["--adopt-existing"]) == 1
    assert (tmp_path / TIGER_COUNTY_FILENAME).exists()
    assert recorded(tmp_path) == {}


def test_dry_run_downloads_nothing(script, tmp_path, monkeypatch):
    accept(script, monkeypatch)
    assert script.main(["--dry-run"]) == 0
    assert not (tmp_path / TIGER_COUNTY_FILENAME).exists()
