"""
engine/config.py — The ONLY module in the engine that reads os.environ.

All other modules receive config values via function arguments or dependency injection.
No other module may import os or read environment variables directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _required(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(
            f"Required environment variable '{key}' is not set. "
            f"Copy .env.example to .env and fill in the value."
        )
    return value


def _optional(key: str, default: str) -> str:
    return os.environ.get(key, default)


@dataclass(frozen=True)
class Config:
    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str

    # ── OpenAI ────────────────────────────────────────────────────────────────
    openai_api_key: str

    # ── Fixture mode ─────────────────────────────────────────────────────────
    # When True, API routes return fixture JSON instead of live DB queries.
    # Set KILTER_FIXTURES=1 for demo fallback recording.
    fixtures_enabled: bool

    # ── Probe runner ─────────────────────────────────────────────────────────
    probe_n_samples: int          # samples per probeset per run
    probe_baseline_cycles: int    # cycles before baseline is established
    probe_default_rps: float      # max requests-per-second per server (hard cap)

    # ── Scheduler ────────────────────────────────────────────────────────────
    scheduler_interval_minutes: int

    # ── API ──────────────────────────────────────────────────────────────────
    cors_origins: list[str]

    # ── Probe identity ───────────────────────────────────────────────────────
    user_agent: str

    # ── Logging ──────────────────────────────────────────────────────────────
    log_level: str


def load_config() -> Config:
    """Build Config from environment variables. Call once at startup."""
    from dotenv import load_dotenv

    load_dotenv()

    cors_raw = _optional(
        "KILTER_CORS_ORIGINS",
        "http://localhost:5173",
    )
    cors_origins = [o.strip() for o in cors_raw.split(",") if o.strip()]

    return Config(
        database_url=_required("DATABASE_URL"),
        openai_api_key=_required("OPENAI_API_KEY"),
        fixtures_enabled=_optional("KILTER_FIXTURES", "0") == "1",
        probe_n_samples=int(_optional("KILTER_PROBE_N_SAMPLES", "10")),
        probe_baseline_cycles=int(_optional("KILTER_PROBE_BASELINE_CYCLES", "3")),
        probe_default_rps=float(_optional("KILTER_PROBE_DEFAULT_RPS", "0.2")),
        scheduler_interval_minutes=int(
            _optional("KILTER_SCHEDULER_INTERVAL_MINUTES", "20")
        ),
        cors_origins=cors_origins,
        user_agent=_optional(
            "KILTER_USER_AGENT",
            "Kilter-Probe/0.1 (https://kilter.app; probe@kilter.app)",
        ),
        log_level=_optional("LOG_LEVEL", "INFO"),
    )
