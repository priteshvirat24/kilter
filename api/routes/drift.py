"""
api/routes/drift.py — /api/drift routes.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import structlog
from fastapi import APIRouter, Query

from api.deps import ConfigDep, RepoDep
from api.schemas import (
    DriftEventServer,
    DriftEventSummary,
    DriftFeedResponse,
)

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/api")

_FIXTURES = Path(__file__).parent.parent / "fixtures"


def _load_fixture(name: str) -> dict:
    with open(_FIXTURES / name) as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/drift
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/drift", response_model=DriftFeedResponse)
async def list_drift_events(
    config: ConfigDep,
    repo: RepoDep,
    severity: str | None = Query(default=None),
    server_id: UUID | None = Query(default=None),
    since: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
) -> DriftFeedResponse:
    if config.fixtures_enabled:
        data = _load_fixture("drift.json")
        return DriftFeedResponse(**data)

    events, next_cursor = await repo.list_drift_events(
        server_id=server_id,
        severity=severity,
        since=since,
        cursor=cursor,
        limit=limit,
    )

    summaries: list[DriftEventSummary] = []
    for e in events:
        # Fetch server name/slug for each event (could batch in production)
        server = await repo.get_server(e.server_id)
        server_summary = DriftEventServer(
            id=e.server_id,
            name=server.name if server else "Unknown",
            slug=server.slug if server else "",
        )

        has_remediation = (
            await repo.get_remediation_for_event(e.id) is not None
        )

        summaries.append(
            DriftEventSummary(
                id=e.id,
                server=server_summary,
                detected_at=e.detected_at,
                layer=e.layer,  # type: ignore[arg-type]
                severity=e.severity,  # type: ignore[arg-type]
                change_type=e.change_type,
                field_path=e.field_path,
                title=e.title,
                confidence=e.confidence,
                has_remediation=has_remediation,
                acknowledged=e.acknowledged,
            )
        )

    return DriftFeedResponse(events=summaries, next_cursor=next_cursor)
