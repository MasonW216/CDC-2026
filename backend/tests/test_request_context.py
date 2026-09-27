"""Request IDs and metadata-only request logging."""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_valid_incoming_request_id_is_returned():
    from stormroute_api.request_context import install_request_context

    app = FastAPI()
    install_request_context(app)

    @app.get("/check")
    def check() -> dict[str, str]:
        return {"ok": "yes"}

    response = TestClient(app).get("/check", headers={"X-Request-ID": "trace-123_ABC.9"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "trace-123_ABC.9"


@pytest.mark.parametrize(
    "unsafe_id", ["has space", "line\nbreak", "x" * 129, "éclair".encode("latin-1")]
)
def test_unsafe_incoming_request_id_is_replaced(unsafe_id):
    from stormroute_api.request_context import install_request_context

    app = FastAPI()
    install_request_context(app)

    @app.get("/check")
    def check() -> dict[str, str]:
        return {"ok": "yes"}

    response = TestClient(app).get("/check", headers={"X-Request-ID": unsafe_id})

    assert response.status_code == 200
    returned_id = response.headers["X-Request-ID"]
    assert returned_id != unsafe_id
    assert UUID(returned_id).version == 4


def test_request_log_is_structured_and_excludes_sensitive_inputs(caplog):
    from stormroute_api.request_context import install_request_context

    app = FastAPI()
    install_request_context(app)

    @app.post("/submit", status_code=201)
    def submit(payload: dict[str, str]) -> dict[str, str]:
        return {"received": payload["secret"]}

    with caplog.at_level(logging.INFO, logger="stormroute_api.request"):
        response = TestClient(app).post(
            "/submit?token=query-secret",
            headers={"X-Request-ID": "abc-123", "Authorization": "Bearer header-secret"},
            json={"secret": "body-secret"},
        )

    assert response.status_code == 201
    assert response.headers["X-Request-ID"] == "abc-123"
    assert [json.loads(record.message) for record in caplog.records] == [
        {"request_id": "abc-123", "method": "POST", "path": "/submit", "status": 201}
    ]
    assert "body-secret" not in caplog.text
    assert "query-secret" not in caplog.text
    assert "header-secret" not in caplog.text


def test_unhandled_error_returns_request_id_and_logs_500(caplog):
    from stormroute_api.request_context import install_request_context

    app = FastAPI()
    install_request_context(app)

    @app.get("/broken")
    def broken() -> None:
        raise RuntimeError("private server detail")

    with caplog.at_level(logging.INFO, logger="stormroute_api.request"):
        response = TestClient(app, raise_server_exceptions=False).get(
            "/broken", headers={"X-Request-ID": "error-123"}
        )

    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "error-123"
    assert "private server detail" not in response.text
    assert [json.loads(record.message) for record in caplog.records] == [
        {"request_id": "error-123", "method": "GET", "path": "/broken", "status": 500}
    ]


def test_missing_request_ids_are_generated_independently_for_app_instances():
    from stormroute_api.request_context import install_request_context

    first_app = FastAPI()
    second_app = FastAPI()
    install_request_context(first_app)
    install_request_context(second_app)

    first_response = TestClient(first_app).get("/missing")
    second_response = TestClient(second_app).get("/missing")

    assert first_response.status_code == second_response.status_code == 404
    first_id = first_response.headers["X-Request-ID"]
    second_id = second_response.headers["X-Request-ID"]
    assert UUID(first_id).version == UUID(second_id).version == 4
    assert first_id != second_id


def test_request_logs_emit_once_per_app_under_uvicorn_configuration():
    repo_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo_root / "src"), str(repo_root / "backend" / "src"), env.get("PYTHONPATH", "")]
    )
    script = """
from fastapi.testclient import TestClient
from uvicorn import Config
from stormroute_api.main import create_app

Config('stormroute_api.main:app').configure_logging()
for _ in range(2):
    response = TestClient(create_app()).get(
        '/health?token=query-secret',
        headers={'X-Request-ID': 'trace-123', 'Authorization': 'Bearer header-secret'},
    )
    assert response.status_code == 200
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stderr.count('"request_id": "trace-123"') == 2
    assert '"method": "GET"' in result.stderr
    assert '"path": "/health"' in result.stderr
    assert '"status": 200' in result.stderr
    assert "query-secret" not in result.stderr
    assert "header-secret" not in result.stderr
