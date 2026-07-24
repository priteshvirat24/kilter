"""
engine/diff/types.py — Shared dataclasses: the internal contract.

Defined per 03-data-model.md. Written by hand, not agent-generated.
Every diff layer (L0–L3) has the identical signature:
    def diff(baseline: Baseline, current: list[Observation]) -> list[DriftFinding]

No I/O, no database, no network inside any diff function.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

Severity = Literal["cosmetic", "behavioral", "breaking"]
Layer = Literal["l0_capability", "l1_structural", "l2_statistical", "l3_semantic"]


@dataclass(frozen=True)
class Observation:
    probeset_id: str
    sample_index: int
    observed_at: datetime
    raw_response: dict[str, Any] | None
    is_error: bool
    error_code: int | None
    latency_ms: int | None


@dataclass(frozen=True)
class FieldStats:
    path: str
    dtype: Literal["number", "string", "bool", "null", "array", "object"]
    null_rate: float
    mean: float | None
    std: float | None
    categories: dict[str, int] | None   # categorical: value -> count
    cardinality: int | None             # for array fields: typical element count


@dataclass(frozen=True)
class Baseline:
    probeset_id: str
    sample_count: int
    field_stats: dict[str, FieldStats]  # path -> FieldStats
    volatility: dict[str, float]        # path -> 0.0..1.0
    centroid: list[float] | None        # pgvector embedding centroid


@dataclass(frozen=True)
class DriftFinding:
    layer: Layer
    severity: Severity
    change_type: str
    field_path: str | None
    title: str
    evidence: dict[str, Any]
    confidence: float
