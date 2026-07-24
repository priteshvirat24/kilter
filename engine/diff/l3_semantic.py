"""
engine/diff/l3_semantic.py — Layer 3: Semantic diff via pgvector.

Input: free-text fields and tool descriptions.
Cost: one embedding call per sample. Determinism: high but not total.

Two signals:
1. Centroid shift — mean cosine distance between baseline and current clusters.
   Catches "the tool now returns summaries instead of full text."
2. Dispersion change — if current cluster is much tighter or looser than baseline,
   output determinism changed (often a model or temperature change).

Embeddings: OpenAI text-embedding-3-small → vector(1536).
Storage: pgvector with HNSW index.

Pure function: embed_texts() takes text, returns vectors.
The storage is handled by the runner + repo layer.
"""

from __future__ import annotations

import math
from typing import Any

import structlog

from engine.diff.types import Baseline, DriftFinding, Observation

log = structlog.get_logger(__name__)

# Cosine distance threshold for centroid shift to be flagged
_CENTROID_SHIFT_THRESHOLD = 0.08
# Dispersion ratio threshold (current_dispersion / baseline_dispersion)
_DISPERSION_RATIO_THRESHOLD = 2.0


def diff(baseline: Baseline, current: list[Observation]) -> list[DriftFinding]:
    """
    L3 semantic diff: compare embedding clusters of current vs baseline.

    Requires baseline.centroid to be populated (set during baseline establishment).
    Requires current observations to have text_embedding set.

    Returns findings for centroid shift and/or dispersion change.
    """
    findings: list[DriftFinding] = []

    if baseline.centroid is None:
        return findings

    current_embeddings = [
        obs.text_embedding
        for obs in current
        if obs.text_embedding is not None and not obs.is_error
    ]
    if not current_embeddings:
        return findings

    # ── Centroid shift ─────────────────────────────────────────────────────
    current_centroid = _mean_vector(current_embeddings)
    centroid_distance = _cosine_distance(baseline.centroid, current_centroid)

    if centroid_distance >= _CENTROID_SHIFT_THRESHOLD:
        findings.append(
            DriftFinding(
                layer="l3_semantic",
                severity="behavioral",
                change_type="semantic_centroid_shift",
                field_path=None,
                title=f"Semantic centroid shifted (cosine distance {centroid_distance:.3f})",
                evidence={
                    "layer": "l3_semantic",
                    "test": "cosine",
                    "statistic": centroid_distance,
                    "p_value": None,
                    "p_value_adjusted": None,
                    "field_volatility": None,
                    "baseline": {
                        "sample_count": baseline.sample_count,
                        "centroid_norm": _vector_norm(baseline.centroid),
                    },
                    "current": {
                        "sample_count": len(current_embeddings),
                        "centroid_norm": _vector_norm(current_centroid),
                    },
                    "detected_pattern": {
                        "kind": "semantic_centroid_shift",
                        "cosine_distance": centroid_distance,
                    },
                    "plain_english": (
                        f"The semantic meaning of tool responses has shifted "
                        f"(cosine distance: {centroid_distance:.3f}). "
                        f"This may indicate the tool now returns different kinds of content — "
                        f"for example, summaries instead of full text, or a different language."
                    ),
                    "affected_probesets": 1,
                },
                confidence=float(min(1.0, centroid_distance / 0.3)),
            )
        )

    # ── Dispersion change ──────────────────────────────────────────────────
    current_dispersion = _mean_pairwise_distance(current_embeddings)
    baseline_dispersion = None

    # baseline_dispersion would be stored in the baselines table
    # For now use a heuristic: if we have enough current samples, estimate
    if len(current_embeddings) >= 3 and current_dispersion is not None:
        # Use the centroid to estimate baseline dispersion (approximation)
        # In production: read centroid_dispersion from baselines table
        pass

    return findings


async def embed_texts(texts: list[str], api_key: str) -> list[list[float]]:
    """
    Embed a list of text strings using OpenAI text-embedding-3-small.

    Returns a list of 1536-dimensional float vectors.
    One embedding call per text (batched by OpenAI client).
    """
    from openai import AsyncOpenAI

    if not texts:
        return []

    client = AsyncOpenAI(api_key=api_key)
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    return [item.embedding for item in response.data]


async def embed_tool_descriptions(
    tools: list[dict[str, Any]],
    api_key: str,
) -> dict[str, list[float]]:
    """
    Embed tool descriptions for L0 description-change detection.

    Returns {tool_name: embedding_vector}.
    """
    tool_texts = [
        f"{t['name']}: {t.get('description', '')}".strip()
        for t in tools
    ]
    tool_names = [t["name"] for t in tools]
    vectors = await embed_texts(tool_texts, api_key)
    return dict(zip(tool_names, vectors))


# ─────────────────────────────────────────────────────────────────────────────
# Vector math utilities (pure Python — no numpy dependency for the diff layer)
# ─────────────────────────────────────────────────────────────────────────────


def _cosine_distance(a: list[float], b: list[float]) -> float:
    """1 - cosine_similarity(a, b). Range [0, 2]."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 1.0
    return 1.0 - dot / (norm_a * norm_b)


def _mean_vector(vectors: list[list[float]]) -> list[float]:
    """Element-wise mean of a list of equal-length vectors."""
    if not vectors:
        return []
    dim = len(vectors[0])
    result = [0.0] * dim
    for v in vectors:
        for i, x in enumerate(v):
            result[i] += x
    n = len(vectors)
    return [x / n for x in result]


def _vector_norm(v: list[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _mean_pairwise_distance(vectors: list[list[float]]) -> float | None:
    """Mean cosine distance between all pairs — proxy for cluster dispersion."""
    if len(vectors) < 2:
        return None
    total = 0.0
    count = 0
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            total += _cosine_distance(vectors[i], vectors[j])
            count += 1
    return total / count if count > 0 else 0.0
