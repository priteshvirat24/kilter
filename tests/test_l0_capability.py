"""
tests/test_l0_capability.py — Tests for L0 capability diff.

100% deterministic — no I/O, no DB. Pure function tests.
Covers: tool removed, tool added, required field added, field type changed,
        description changed, enum value removed, protocol revision change.
"""

import pytest
from engine.diff.l0_capability import diff_capabilities


def _base_tool(name: str, description: str = "No description", props: dict | None = None, required: list | None = None) -> dict:
    schema: dict = {"type": "object", "properties": props or {}, "required": required or []}
    return {"name": name, "description": description, "inputSchema": schema}


# ── Tool presence changes ──────────────────────────────────────────────────


def test_tool_removed_is_breaking():
    baseline = [_base_tool("search")]
    current: list = []
    findings = diff_capabilities(baseline, current, None, None)
    assert any(f.severity == "breaking" and f.change_type == "tool_removed" for f in findings)


def test_tool_added_is_cosmetic():
    baseline: list = []
    current = [_base_tool("search")]
    findings = diff_capabilities(baseline, current, None, None)
    assert any(f.severity == "cosmetic" and f.change_type == "tool_added" for f in findings)


def test_no_change_produces_no_findings():
    tool = _base_tool("search", props={"q": {"type": "string"}}, required=["q"])
    findings = diff_capabilities([tool], [tool], "2025-11-25", "2025-11-25")
    assert findings == []


# ── Schema changes ─────────────────────────────────────────────────────────


def test_required_field_added_is_breaking():
    baseline = [_base_tool("search", props={"q": {"type": "string"}})]
    current = [_base_tool("search", props={"q": {"type": "string"}, "api_key": {"type": "string"}}, required=["api_key"])]
    findings = diff_capabilities(baseline, current, None, None)
    assert any(f.severity == "breaking" and f.change_type == "required_field_added" for f in findings)


def test_field_type_changed_is_breaking():
    baseline = [_base_tool("search", props={"limit": {"type": "integer"}})]
    current = [_base_tool("search", props={"limit": {"type": "string"}})]
    findings = diff_capabilities(baseline, current, None, None)
    assert any(f.severity == "breaking" and "limit" in f.title for f in findings)


def test_enum_value_removed_is_breaking():
    baseline = [_base_tool("filter", props={"mode": {"type": "string", "enum": ["a", "b", "c"]}})]
    current = [_base_tool("filter", props={"mode": {"type": "string", "enum": ["a", "b"]}})]
    findings = diff_capabilities(baseline, current, None, None)
    assert any(f.severity == "breaking" and f.change_type == "enum_value_removed" for f in findings)


def test_enum_value_added_is_behavioral():
    baseline = [_base_tool("filter", props={"mode": {"type": "string", "enum": ["a"]}})]
    current = [_base_tool("filter", props={"mode": {"type": "string", "enum": ["a", "b"]}})]
    findings = diff_capabilities(baseline, current, None, None)
    assert any(f.severity == "behavioral" and f.change_type == "enum_value_added" for f in findings)


def test_optional_field_added_is_cosmetic():
    baseline = [_base_tool("search", props={"q": {"type": "string"}})]
    current = [_base_tool("search", props={"q": {"type": "string"}, "lang": {"type": "string"}})]
    findings = diff_capabilities(baseline, current, None, None)
    assert any(f.severity == "cosmetic" and f.change_type == "optional_field_added" for f in findings)


# ── Description / protocol ─────────────────────────────────────────────────


def test_description_changed_without_embeddings():
    baseline = [_base_tool("search", description="Search GitHub issues")]
    current = [_base_tool("search", description="Wibble wobble")]
    findings = diff_capabilities(baseline, current, None, None)
    assert any(f.change_type == "description_changed" for f in findings)


def test_description_unchanged_no_finding():
    tool = _base_tool("search", description="Search GitHub issues")
    findings = diff_capabilities([tool], [tool], None, None)
    assert not any(f.change_type == "description_changed" for f in findings)


def test_protocol_revision_change_is_behavioral():
    tool = _base_tool("search")
    findings = diff_capabilities([tool], [tool], "2025-11-25", "2024-11-05")
    assert any(f.change_type == "protocol_revision_changed" and f.severity == "behavioral" for f in findings)


def test_protocol_revision_no_change():
    tool = _base_tool("search")
    findings = diff_capabilities([tool], [tool], "2025-11-25", "2025-11-25")
    assert not any(f.change_type == "protocol_revision_changed" for f in findings)


# ── Evidence JSONB structure ───────────────────────────────────────────────


def test_finding_evidence_has_required_keys():
    """Every finding must have the full evidence schema."""
    baseline = [_base_tool("search")]
    current: list = []
    findings = diff_capabilities(baseline, current, None, None)
    assert findings
    for f in findings:
        ev = f.evidence
        assert "layer" in ev
        assert "test" in ev
        assert "plain_english" in ev
        assert "baseline" in ev
        assert "current" in ev
        assert "detected_pattern" in ev
        assert "affected_probesets" in ev


# ── Confidence ────────────────────────────────────────────────────────────


def test_tool_removed_confidence_is_1():
    baseline = [_base_tool("search")]
    current: list = []
    findings = diff_capabilities(baseline, current, None, None)
    removed = [f for f in findings if f.change_type == "tool_removed"]
    assert removed[0].confidence == 1.0
