"""CORS origin policy for the API."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from stormroute_api.config import Settings
from stormroute_api.main import create_app


def test_default_origins_are_only_local_frontend_hosts(monkeypatch):
    monkeypatch.delenv("STORMROUTE_CORS_ORIGINS", raising=False)
    settings = Settings(_env_file=None)

    assert settings.cors_origins == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def test_origins_parse_from_comma_separated_environment(monkeypatch):
    monkeypatch.setenv(
        "STORMROUTE_CORS_ORIGINS",
        "https://app.example.org, https://preview.example.org",
    )

    assert Settings(_env_file=None).cors_origins == [
        "https://app.example.org",
        "https://preview.example.org",
    ]


def test_wildcard_origin_is_rejected():
    with pytest.raises(ValidationError, match="wildcard"):
        Settings(cors_origins=["*"])


def test_allowed_origin_preflight_succeeds():
    from stormroute_api import cors

    app = FastAPI()
    cors.configure_cors(app, Settings(cors_origins=["https://app.example.org"]))

    response = TestClient(app).options(
        "/api/v1/trips/score",
        headers={
            "Origin": "https://app.example.org",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://app.example.org"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_unlisted_origin_preflight_is_rejected():
    from stormroute_api import cors

    app = FastAPI()
    cors.configure_cors(app, Settings(cors_origins=["https://app.example.org"]))

    response = TestClient(app).options(
        "/api/v1/trips/score",
        headers={
            "Origin": "https://other.example.org",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_create_app_preflight_allows_request_id_header():
    app = create_app(Settings(cors_origins=["https://app.example.org"]))

    response = TestClient(app).options(
        "/api/v1/trips/score",
        headers={
            "Origin": "https://app.example.org",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-request-id",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://app.example.org"
    assert "x-request-id" in response.headers["access-control-allow-headers"].lower()


def test_create_app_exposes_request_id_on_success():
    app = create_app(Settings(cors_origins=["https://app.example.org"]))

    response = TestClient(app).get(
        "/health", headers={"Origin": "https://app.example.org", "X-Request-ID": "ok-123"}
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "ok-123"
    assert response.headers["access-control-allow-origin"] == "https://app.example.org"
    assert "x-request-id" in response.headers["access-control-expose-headers"].lower()


def test_create_app_500_has_cors_and_request_id():
    app = create_app(Settings(cors_origins=["https://app.example.org"]))

    @app.get("/broken")
    def broken() -> None:
        raise RuntimeError("private server detail")

    response = TestClient(app, raise_server_exceptions=False).get(
        "/broken", headers={"Origin": "https://app.example.org", "X-Request-ID": "error-123"}
    )

    assert response.status_code == 500
    assert response.headers["x-request-id"] == "error-123"
    assert response.headers["access-control-allow-origin"] == "https://app.example.org"
    assert "x-request-id" in response.headers["access-control-expose-headers"].lower()
    assert "private server detail" not in response.text
