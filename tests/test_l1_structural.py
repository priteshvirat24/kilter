"""
tests/test_l1_structural.py — Tests for L1 structural diff.

100% deterministic — pure function tests.
Covers: field added/removed, type shift, null-rate shift, cardinality shift,
        shape fingerprinting (array index collapse), structural type breaks.
"""

import pytest
from datetime import datetime, timezone
from engine.diff.l1_structural import (
    diff,
    extract_shape_fingerprint,
    _json_type,
    _is_structural_type_shift,
)
from engine.diff.types import Baseline, FieldStats, Observation


def _make_baseline(field_stats: dict[str, FieldStats], volatility: dict[str, float] | None = None) -> Baseline:
    return Baseline(
        probeset_id="test",
        sample_count=30,
        field_stats=field_stats,
        volatility=volatility or {k: 0.1 for k in field_stats},
        centroid=None,
    )


def _make_obs(response: dict) -> Observation:
    return Observation(
        probeset_id="test",
        sample_index=0,
        observed_at=datetime.now(timezone.utc),
        raw_response=response,
        is_error=False,
        error_code=None,
        latency_ms=100,
    )


# ── Shape fingerprint ──────────────────────────────────────────────────────


def test_fingerprint_flat_dict():
    fp = extract_shape_fingerprint({"name": "Alice", "score": 42})
    assert "name" in fp["paths"]
    assert "score" in fp["paths"]
    assert fp["types"]["name"] == "string"
    assert fp["types"]["score"] == "number"


def test_fingerprint_array_index_collapse():
    """Array items must use [*] notation, not [0], [1], [2]."""
    fp = extract_shape_fingerprint({"results": [{"id": 1}, {"id": 2}]})
    assert "results" in fp["types"]
    assert "results[*]" in fp["types"] or "results[*].id" in fp["types"]
    # No indexed paths
    assert "results[0]" not in fp["types"]
    assert "results[1]" not in fp["types"]


def test_fingerprint_nested():
    fp = extract_shape_fingerprint({"meta": {"total": 100, "page": 1}})
    assert "meta.total" in fp["types"]
    assert "meta.page" in fp["types"]


def test_fingerprint_null_value():
    fp = extract_shape_fingerprint({"value": None})
    assert fp["types"]["value"] == "null"
    assert fp["null_rate"]["value"] == 1.0


# ── Field removed ─────────────────────────────────────────────────────────


def test_field_removed_behavioral():
    baseline = _make_baseline({
        "results": FieldStats("results", "array", 0.0, None, None, None, 10),
    })
    current = [_make_obs({})]  # results disappeared
    findings = diff(baseline, current)
    assert any(f.change_type == "field_removed" and "results" in (f.field_path or "") for f in findings)


def test_field_removed_high_null_rate_is_cosmetic():
    """If a field was already 80% null, its disappearance is cosmetic."""
    baseline = _make_baseline({
        "maybe_field": FieldStats("maybe_field", "string", 0.8, None, None, None, None),
    })
    current = [_make_obs({"other": 1})]
    findings = diff(baseline, current)
    removed = [f for f in findings if "maybe_field" in (f.field_path or "")]
    if removed:
        assert removed[0].severity == "cosmetic"


# ── Field added ───────────────────────────────────────────────────────────


def test_new_field_is_cosmetic():
    baseline = _make_baseline({"name": FieldStats("name", "string", 0.0, None, None, None, None)})
    current = [_make_obs({"name": "Alice", "age": 30})]
    findings = diff(baseline, current)
    assert any(f.change_type == "field_added" and f.severity == "cosmetic" for f in findings)


# ── Type shift ────────────────────────────────────────────────────────────


def test_type_shift_scalar_to_array_is_breaking():
    baseline = _make_baseline({"tags": FieldStats("tags", "string", 0.0, None, None, None, None)})
    current = [_make_obs({"tags": ["python", "mcp"]})]
    findings = diff(baseline, current)
    type_shifts = [f for f in findings if f.change_type == "type_shift" and "tags" in (f.field_path or "")]
    assert type_shifts
    assert type_shifts[0].severity == "breaking"


def test_type_shift_number_to_string_is_behavioral():
    baseline = _make_baseline({"score": FieldStats("score", "number", 0.0, 0.8, 0.1, None, None)})
    current = [_make_obs({"score": "high"})]
    findings = diff(baseline, current)
    shifts = [f for f in findings if "score" in (f.field_path or "") and f.change_type == "type_shift"]
    assert shifts
    assert shifts[0].severity == "behavioral"


# ── Null rate shift ───────────────────────────────────────────────────────


def test_null_rate_shift():
    baseline = _make_baseline({
        "description": FieldStats("description", "string", 0.05, None, None, None, None)
    })
    # 5 responses, 4 have null description → 80% null (shift from 5%)
    current = [
        _make_obs({"description": None}),
        _make_obs({"description": None}),
        _make_obs({"description": None}),
        _make_obs({"description": None}),
        _make_obs({"description": "text"}),
    ]
    findings = diff(baseline, current)
    shifts = [f for f in findings if f.change_type == "null_rate_shift"]
    assert shifts


# ── Cardinality shift ──────────────────────────────────────────────────────


def test_cardinality_shift():
    baseline = _make_baseline({
        "results": FieldStats("results", "array", 0.0, None, None, None, 20)
    })
    # Array now has only 5 items (halved)
    current = [_make_obs({"results": [{"id": i} for i in range(5)]})]
    findings = diff(baseline, current)
    cards = [f for f in findings if f.change_type == "cardinality_shift"]
    assert cards


def test_cardinality_stable_no_finding():
    baseline = _make_baseline({
        "results": FieldStats("results", "array", 0.0, None, None, None, 10)
    })
    # Array still has 10 items
    current = [_make_obs({"results": [{"id": i} for i in range(10)]})]
    findings = diff(baseline, current)
    cards = [f for f in findings if f.change_type == "cardinality_shift"]
    assert not cards


# ── json_type helper ──────────────────────────────────────────────────────


def test_json_type_bool_not_number():
    assert _json_type(True) == "bool"
    assert _json_type(42) == "number"
    assert _json_type(3.14) == "number"
    assert _json_type(None) == "null"
    assert _json_type([]) == "array"
    assert _json_type({}) == "object"


# ── Evidence structure ────────────────────────────────────────────────────


def test_l1_findings_have_evidence_keys():
    baseline = _make_baseline({"score": FieldStats("score", "number", 0.0, 0.8, 0.1, None, None)})
    current = [_make_obs({"score": "high"})]
    findings = diff(baseline, current)
    for f in findings:
        assert "layer" in f.evidence
        assert f.evidence["layer"] == "l1_structural"
        assert "plain_english" in f.evidence
