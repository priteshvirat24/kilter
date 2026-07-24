"""
engine/store/models.py — Python representations of all database rows.

These are plain dataclasses matching the db/schema.sql columns exactly.
No ORM — direct psycopg3 row mapping via `row_factory`.
All DB access goes through engine/store/repo.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class ServerRow:
    id: UUID
    name: str
    slug: str
    endpoint_url: str
    transport: str
    registry_source: str | None
    protocol_revision: str | None
    auth_mode: str
    probe_enabled: bool
    opt_out: bool
    rate_limit_rps: float
    first_seen_at: datetime
    last_probed_at: datetime | None


@dataclass(frozen=True)
class CapabilitySnapshotRow:
    id: UUID
    server_id: UUID
    captured_at: datetime
    protocol_revision: str | None
    tools: list[dict[str, Any]]        # full tools/list payload
    resources: list[dict[str, Any]] | None
    prompts: list[dict[str, Any]] | None
    content_hash: str


@dataclass(frozen=True)
class ProbesetRow:
    id: UUID
    server_id: UUID
    tool_name: str
    arguments: dict[str, Any]
    generation_method: str             # 'schema_synth' | 'recorded_trace' | 'manual'
    is_safe: bool
    created_at: datetime


@dataclass(frozen=True)
class ObservationRow:
    id: UUID
    probeset_id: UUID
    run_id: UUID
    observed_at: datetime
    sample_index: int
    latency_ms: int | None
    is_error: bool
    error_code: int | None
    error_message: str | None
    raw_response: dict[str, Any] | None
    shape_fingerprint: dict[str, Any] | None
    text_embedding: list[float] | None  # vector(1536); None when no free text


@dataclass(frozen=True)
class BaselineRow:
    id: UUID
    probeset_id: UUID
    established_at: datetime
    sample_count: int
    capability_snapshot_id: UUID | None
    field_stats: dict[str, Any]        # path -> {type, mean, std, categories, null_rate}
    volatility: dict[str, float]       # path -> 0.0..1.0
    centroid: list[float] | None
    centroid_dispersion: float | None
    is_active: bool


@dataclass(frozen=True)
class DriftEventRow:
    id: UUID
    server_id: UUID
    probeset_id: UUID | None
    baseline_id: UUID | None
    run_id: UUID
    detected_at: datetime
    layer: str                         # drift_layer enum value
    severity: str                      # drift_severity enum value
    change_type: str
    field_path: str | None
    title: str
    evidence: dict[str, Any]
    confidence: float | None
    acknowledged: bool


@dataclass(frozen=True)
class RemediationRow:
    id: UUID
    drift_event_id: UUID
    strategy: str                      # 'pin' | 'shim' | 'call_site'
    language: str                      # 'python' | 'typescript'
    patch_diff: str
    explanation: str
    created_at: datetime
