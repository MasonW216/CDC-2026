"""MVP gate checks using the frozen Helene inputs and route fixture."""

import importlib.util
import json
import socket
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "run_prototype", REPO_ROOT / "scripts/run_prototype.py"
)
assert _spec and _spec.loader
run_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_prototype)
main, run = run_prototype.main, run_prototype.run

DEMO = Path(__file__).resolve().parents[2] / "artifacts" / "demo"
ROUTES = DEMO / "prototype_routes_provisional.json"
INPUTS = DEMO / "prototype_inputs_helene.json"


def _input_copy(tmp_path: Path, name: str) -> tuple[dict, Path]:
    source = json.loads(INPUTS.read_text(encoding="utf-8"))
    return source, tmp_path / name


def _segments_for_county(result: dict, county_fips: str) -> list[dict]:
    """Every segment for `county_fips`, across whichever route(s) of the fixture cross it."""
    return [
        seg
        for trip in result["routes"].values()
        for seg in trip["segments"]
        if seg["county_fips"] == county_fips
    ]


def test_real_county_with_missing_rain_is_not_assessed(tmp_path: Path) -> None:
    inputs, path = _input_copy(tmp_path, "missing.json")
    del inputs["precipitation"]["mm"]["37109"]  # Lincoln: no active alert
    path.write_text(json.dumps(inputs), encoding="utf-8")

    result = run(ROUTES, path)
    lincoln = _segments_for_county(result, "37109")[0]
    assert lincoln["label"] == "Not assessed"
    assert lincoln["level"] is None
    assert lincoln["data_status"] == "missing_weather"
    trip = next(t for t in result["routes"].values() if "37109" in t["unassessed_segments"])
    assert "37109" in trip["unassessed_segments"]


def test_warning_added_to_real_lower_rain_stretch_never_lowers_level(tmp_path: Path) -> None:
    original = run(ROUTES, INPUTS)
    inputs, path = _input_copy(tmp_path, "warning.json")
    # Synthetic perturbation: the real Catawba stretch(es) otherwise use real data.
    inputs["alerts"]["rows"].append(
        {
            "wfo": "TST",
            "phenomena": "FF",
            "significance": "W",
            "eventid": "999",
            "status": "NEW",
            "ugc": "NCC035",
            "utc_issue": "2024-09-26 08:00",
            "utc_prodissue": "2024-09-26 08:00",
            "utc_init_expire": "202409261800",
            "utc_expire": "2024-09-26 18:00",
        }
    )
    path.write_text(json.dumps(inputs), encoding="utf-8")
    changed = run(ROUTES, path)
    before = [s["level"] for s in _segments_for_county(original, "37035")]
    after = [s["level"] for s in _segments_for_county(changed, "37035")]
    assert before and after and len(before) == len(after)
    assert all(a >= b for a, b in zip(after, before, strict=True))
    assert any(a > b for a, b in zip(after, before, strict=True))


def test_script_replay_is_byte_identical_with_network_blocked(tmp_path: Path, monkeypatch) -> None:
    def no_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("prototype replay tried to use the network")

    with monkeypatch.context() as m:
        m.setattr(socket.socket, "connect", no_network)
        m.setattr(socket.socket, "connect_ex", no_network)
        m.setattr(socket, "create_connection", no_network)
        first, second = tmp_path / "first.json", tmp_path / "second.json"
        for output in (first, second):
            m.setattr(
                sys,
                "argv",
                [
                    "scripts/run_prototype.py",
                    "--routes",
                    str(ROUTES),
                    "--inputs",
                    str(INPUTS),
                    "--out",
                    str(output),
                ],
            )
            main()
    assert first.read_bytes() == second.read_bytes()
