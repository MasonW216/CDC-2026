"""Attach request IDs to API responses and record request metadata."""

import json
import logging
import re
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse

_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
# Uvicorn's default logging config handles the uvicorn namespace, not the root
# logger. A child logger inherits its configured handler without adding one per app.
_LOGGER = logging.getLogger("uvicorn.error.stormroute_api.request")
_LOGGER.setLevel(logging.INFO)


def install_request_context(app: FastAPI) -> None:
    """Install per-request ID handling on a FastAPI app."""

    @app.middleware("http")
    async def add_request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        incoming_id = request.headers.get("X-Request-ID")
        request_id = incoming_id if incoming_id and _SAFE_ID.fullmatch(incoming_id) else uuid4().hex
        try:
            response = await call_next(request)
        except Exception:
            response = PlainTextResponse("Internal Server Error", status_code=500)
        response.headers["X-Request-ID"] = request_id
        _LOGGER.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                }
            )
        )
        return response
