"""Explicit cross-origin policy for the API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from stormroute_api.config import Settings


def configure_cors(app: FastAPI, settings: Settings) -> None:
    """Allow browser requests from the configured frontend origins."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
