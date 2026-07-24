"""
api/schemas/__init__.py — Pydantic response models for all API endpoints.

All shapes match 04-api-contract.md exactly.
Generated from these models → openapi.json → web/src/api/types.ts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Shared
# ─────────────────────────────────────────────────────────────────────────────


class ErrorDetail(BaseModel):
    code: str
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/servers
# ─────────────────────────────────────────────────────────────────────────────


class DriftCounts(BaseModel):
    cosmetic: int
    behavioral: int
    breaking: int


class ServerSummary(BaseModel):
    id: UUID
    name: str
    slug: str
    protocol_revision: str | None
    tool_count: int
    last_probed_at: datetime | None
    health: Literal["stable", "drifting", "breaking", "unreachable"]
    drift_counts: DriftCounts
    detection_power: Literal["high", "medium", "low"]


class ServersResponse(BaseModel):
    servers: list[ServerSummary]
    total: int


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/servers/{id}
# ─────────────────────────────────────────────────────────────────────────────


class LastDrift(BaseModel):
    severity: Literal["cosmetic", "behavioral", "breaking"]
    detected_at: datetime


class ToolSummary(BaseModel):
    name: str
    probeset_count: int
    volatility_mean: float
    detection_power: Literal["high", "medium", "low"]
    last_drift: LastDrift | None


class ServerDetailResponse(BaseModel):
    id: UUID
    name: str
    endpoint_url: str
    protocol_revision: str | None
    baseline_established_at: datetime | None
    tools: list[ToolSummary]


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/servers/{id}/timeline
# ─────────────────────────────────────────────────────────────────────────────


class TimelinePoint(BaseModel):
    run_id: UUID
    at: datetime
    value: float
    in_tolerance: bool
    drift_event_id: UUID | None


class FieldSeries(BaseModel):
    field_path: str
    dtype: str
    volatility: float
    nominal: float
    tolerance_lower: float
    tolerance_upper: float
    points: list[TimelinePoint]


class CapabilityMarker(BaseModel):
    at: datetime
    kind: str
    severity: Literal["cosmetic", "behavioral", "breaking"]
    drift_event_id: UUID


class TimelineResponse(BaseModel):
    server_id: UUID
    tool_name: str
    field_series: list[FieldSeries]
    capability_markers: list[CapabilityMarker]


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/drift
# ─────────────────────────────────────────────────────────────────────────────


class DriftEventServer(BaseModel):
    id: UUID
    name: str
    slug: str


class DriftEventSummary(BaseModel):
    id: UUID
    server: DriftEventServer
    detected_at: datetime
    layer: Literal["l0_capability", "l1_structural", "l2_statistical", "l3_semantic"]
    severity: Literal["cosmetic", "behavioral", "breaking"]
    change_type: str
    field_path: str | None
    title: str
    confidence: float | None
    has_remediation: bool
    acknowledged: bool


class DriftFeedResponse(BaseModel):
    events: list[DriftEventSummary]
    next_cursor: str | None


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/drift/{id}/evidence
# ─────────────────────────────────────────────────────────────────────────────


class EvidenceResponse(BaseModel):
    drift_event_id: UUID
    server: DriftEventServer
    detected_at: datetime
    layer: str
    severity: str
    change_type: str
    field_path: str | None
    title: str
    confidence: float | None
    evidence: dict[str, Any]   # the full evidence JSONB per 03-data-model.md


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/drift/{id}/remediation
# ─────────────────────────────────────────────────────────────────────────────


class RemediationResponse(BaseModel):
    drift_event_id: UUID
    strategy: str
    language: str
    explanation: str
    patch_diff: str
    confidence: float | None


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/servers/{id}/probe  (demo-only trigger)
# ─────────────────────────────────────────────────────────────────────────────


class ProbeTriggeredResponse(BaseModel):
    server_id: UUID
    run_id: UUID
    message: str


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/stats
# ─────────────────────────────────────────────────────────────────────────────


class StatsResponse(BaseModel):
    servers_monitored: int
    probe_runs_total: int
    drift_events: DriftCounts
    servers_with_breaking_drift_7d: int
    last_run_at: datetime | None
