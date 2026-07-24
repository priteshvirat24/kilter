"""
api/main.py — FastAPI app. Thin wiring only.

Responsibility: mount routes, configure CORS, set up DB pool lifespan,
configure logging, and start/stop the APScheduler.
"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

import psycopg_pool
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from engine.config import load_config

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    config = load_config()

    # ── Logging ───────────────────────────────────────────────────────────────
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(config.log_level)
        ),
    )

    # ── Database pool ─────────────────────────────────────────────────────────
    pool = psycopg_pool.AsyncConnectionPool(
        conninfo=config.database_url,
        min_size=2,
        max_size=10,
        open=False,
    )
    await pool.open()
    app.state.db_pool = pool
    app.state.config = config
    log.info("db_pool_opened", database_url=config.database_url.split("@")[-1])

    # ── Scheduler ─────────────────────────────────────────────────────────────
    # APScheduler in-process (no Celery/Redis per spec)
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    scheduler = AsyncIOScheduler()
    # The scheduled probe sweep will be wired here in Phase 4 (probe runner)
    # scheduler.add_job(run_sweep, "interval", minutes=config.scheduler_interval_minutes)
    scheduler.start()
    app.state.scheduler = scheduler
    log.info("scheduler_started", interval_minutes=config.scheduler_interval_minutes)

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    scheduler.shutdown(wait=False)
    await pool.close()
    log.info("shutdown_complete")


def create_app() -> FastAPI:
    config = load_config()

    app = FastAPI(
        title="Kilter",
        description="Active MCP server drift detection.",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # ── CORS (Vercel origin + localhost per spec) ──────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # ── Routes ────────────────────────────────────────────────────────────
    from api.routes.servers import router as servers_router
    from api.routes.drift import router as drift_router
    from api.routes.evidence import router as evidence_router

    app.include_router(servers_router)
    app.include_router(drift_router)
    app.include_router(evidence_router)

    # ── Error handler — typed codes, never bare 500s (per spec) ───────────
    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_error", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": "An unexpected error occurred.", "detail": {}}},
        )

    return app


app = create_app()
