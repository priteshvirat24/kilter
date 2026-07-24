"""
api/routes/evidence.py — /api/drift/{id}/evidence and /api/drift/{id}/remediation routes.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException

from api.deps import ConfigDep, RepoDep
from api.schemas import (
    DriftEventServer,
    EvidenceResponse,
    RemediationResponse,
)

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/api")

_FIXTURES = Path(__file__).parent.parent / "fixtures"


def _load_fixture(name: str) -> dict:
    with open(_FIXTURES / name) as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/drift/{id}/evidence
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/drift/{event_id}/evidence", response_model=EvidenceResponse)
async def get_evidence(
    event_id: UUID,
    config: ConfigDep,
    repo: RepoDep,
) -> EvidenceResponse:
    if config.fixtures_enabled:
        data = _load_fixture("evidence.json")
        return EvidenceResponse(**data)

    event = await repo.get_drift_event(event_id)
    if event is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "not_found", "message": f"Drift event {event_id} not found", "detail": {}}},
        )

    server = await repo.get_server(event.server_id)
    server_summary = DriftEventServer(
        id=event.server_id,
        name=server.name if server else "Unknown",
        slug=server.slug if server else "",
    )

    return EvidenceResponse(
        drift_event_id=event.id,
        server=server_summary,
        detected_at=event.detected_at,
        layer=event.layer,
        severity=event.severity,
        change_type=event.change_type,
        field_path=event.field_path,
        title=event.title,
        confidence=event.confidence,
        evidence=event.evidence,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/drift/{id}/remediation
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/drift/{event_id}/remediation", response_model=RemediationResponse)
async def get_remediation(
    event_id: UUID,
    config: ConfigDep,
    repo: RepoDep,
) -> RemediationResponse:
    if config.fixtures_enabled:
        data = _load_fixture("remediation.json")
        return RemediationResponse(**data)

    event = await repo.get_drift_event(event_id)
    if event is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "not_found", "message": f"Drift event {event_id} not found", "detail": {}}},
        )

    remediation = await repo.get_remediation_for_event(event_id)
    if remediation is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "not_found", "message": "No remediation generated for this event", "detail": {}}},
        )

    return RemediationResponse(
        drift_event_id=event_id,
        strategy=remediation.strategy,
        language=remediation.language,
        explanation=remediation.explanation,
        patch_diff=remediation.patch_diff,
        confidence=event.confidence,
    )
