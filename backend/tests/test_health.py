"""Health endpoint contract.

Asserts 200, the documented body shape, and honest reporting of model and
demo-artifact availability -- including the case where an artifact is missing.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from stormroute_api.config import Settings
from stormroute_api.main import create_app

DEMO_FILES = ("demo_routes.geojson", "demo_scores.json", "demo_weather.json")


def _settings(root: Path) -> Settings:
    return Settings(
        model_path=root / "models" / "stormroute_model.joblib",
        demo_artifact_paths=[root / "demo" / name for name in DEMO_FILES],
    )


def _get_health(settings: Settings) -> dict[str, object]:
    response = TestClient(create_app(settings)).get("/health")
    assert response.status_code == 200
    body: dict[str, object] = response.json()
    return body


def test_health_returns_documented_shape(tmp_path):
    body = _get_health(_settings(tmp_path))
    assert set(body) == {"status", "version", "model_available", "demo_available"}
    assert body["status"] == "ok"
    assert isinstance(body["version"], str)


def test_health_reports_missing_artifacts_honestly(tmp_path):
    body = _get_health(_settings(tmp_path))
    assert body["model_available"] is False
    assert body["demo_available"] is False


def test_health_reports_present_artifacts(tmp_path):
    settings = _settings(tmp_path)
    for path in [settings.model_path, *settings.demo_artifact_paths]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}")
    body = _get_health(settings)
    assert body["model_available"] is True
    assert body["demo_available"] is True


def test_demo_unavailable_when_any_single_artifact_is_missing(tmp_path):
    settings = _settings(tmp_path)
    for path in settings.demo_artifact_paths[:-1]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}")
    assert _get_health(settings)["demo_available"] is False


def test_default_settings_resolve_demo_artifacts_from_config():
    names = {path.name for path in Settings().demo_artifact_paths}
    assert names == set(DEMO_FILES)


def test_scaffold_placeholders_do_not_count_as_available(tmp_path):
    settings = _settings(tmp_path)
    routes, scores, weather = settings.demo_artifact_paths
    routes.parent.mkdir(parents=True)
    routes.write_text('{"type": "FeatureCollection", "features": []}')
    scores.write_text('{"placeholder": true, "scenarios": {}}')
    weather.write_text('{"placeholder": true}')
    assert _get_health(settings)["demo_available"] is False


def test_unreadable_artifact_does_not_count_as_available(tmp_path):
    settings = _settings(tmp_path)
    for path in settings.demo_artifact_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}")
    settings.demo_artifact_paths[0].write_text("not json")
    assert _get_health(settings)["demo_available"] is False
