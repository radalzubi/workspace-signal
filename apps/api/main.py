from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from apps.api.core.config import get_settings
from apps.api.core.logging import configure_logging
from apps.api.core.security import InMemoryRateLimiter
from apps.api.db import models  # noqa: F401
from apps.api.db.session import Base, SessionLocal, engine
from apps.api.routes.api import router
from apps.api.services.demo import bootstrap_demo

settings = get_settings()
configure_logging()
logger = structlog.get_logger()
limiter = InMemoryRateLimiter()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings.media_root.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    if settings.demo_mode:
        with SessionLocal() as db:
            try:
                result = bootstrap_demo(db, settings)
                logger.info("demo_bootstrap", **result)
            except Exception:
                logger.exception("demo_bootstrap_failed")
    yield


app = FastAPI(
    title="DealForge API",
    version="0.1.0",
    description="Profit-optimized affiliate deal discovery and Pinterest publishing API.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def request_controls(request: Request, call_next):  # type: ignore[no-untyped-def]
    started = time.monotonic()
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))[:100]
    key = request.client.host if request.client else "unknown"
    if not limiter.allow(key):
        return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    logger.info(
        "http_request",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round((time.monotonic() - started) * 1000, 2),
    )
    return response


app.include_router(router, prefix=settings.api_prefix)
app.include_router(router, include_in_schema=False) if False else None
app.add_api_route(
    "/go/{slug}",
    __import__("apps.api.routes.api", fromlist=["track_redirect"]).track_redirect,
    methods=["GET"],
    include_in_schema=False,
)

media_root = Path(settings.media_root).resolve()
media_root.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=media_root), name="media")
