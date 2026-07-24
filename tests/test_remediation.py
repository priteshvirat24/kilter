"""
tests/test_remediation.py — Tests for the remediation patch generator.

Validates:
- Only BREAKING findings generate patches
- Shim strategy for unit_shift produces valid unified diff format
- Shim contains the correct inverse factor
- Pin stub is returned for tool_removed
- Explanation is present and non-empty
"""

import pytest
from engine.diff.types import DriftFinding
from engine.remediate.patch import generate_patch


def _finding(severity: str, change_type: str, evidence: dict | None = None, field_path: str | None = None) -> DriftFinding:
    return DriftFinding(
        layer="l2_statistical",
        severity=severity,
        change_type=change_type,
        field_path=field_path or "results[*].weight",
        title=f"Test finding: {change_type}",
        evidence=evidence or {
            "layer": "l2_statistical",
            "test": "unit_shift_detector",
            "statistic": 2.20462,
            "p_value": None,
            "p_value_adjusted": None,
            "field_volatility": 0.04,
            "baseline": {"sample_count": 30, "window": [], "summary": {"mean": 12.4, "std": 1.0}, "examples": []},
            "current": {"sample_count": 30, "window": [], "summary": {"mean": 27.3, "std": 2.2}, "examples": []},
            "detected_pattern": {"kind": "unit_shift", "factor": 2.20462, "interpretation": "kilograms to pounds"},
            "plain_english": "The weight field changed from kg to lbs.",
            "affected_probesets": 3,
        },
        confidence=0.94,
    )


def test_only_breaking_generates_patch():
    for severity in ("cosmetic", "behavioral"):
        f = _finding(severity, "unit_shift")
        assert generate_patch(f) is None


def test_unit_shift_generates_shim():
    f = _finding("breaking", "unit_shift")
    result = generate_patch(f)
    assert result is not None
    assert result.strategy == "shim"
    assert result.language == "python"


def test_unit_shift_patch_is_valid_diff():
    f = _finding("breaking", "unit_shift")
    result = generate_patch(f)
    assert result is not None
    lines = result.patch_diff.split("\n")
    assert any(l.startswith("---") for l in lines)
    assert any(l.startswith("+++") for l in lines)
    assert any(l.startswith("+") for l in lines)
    assert any(l.startswith("-") for l in lines)


def test_unit_shift_patch_contains_inverse_factor():
    """The shim must apply the inverse factor (1/2.20462 ≈ 0.45359)."""
    f = _finding("breaking", "unit_shift")
    result = generate_patch(f)
    assert result is not None
    # Factor 1/2.20462 ≈ 0.45359
    inverse = 1.0 / 2.20462
    assert f"{inverse:.4g}" in result.patch_diff or "0.453" in result.patch_diff or "LBS_TO_KG" in result.patch_diff.upper() or "WEIGHT_CONVERSION" in result.patch_diff.upper()


def test_explanation_is_present():
    f = _finding("breaking", "unit_shift")
    result = generate_patch(f)
    assert result is not None
    assert result.explanation
    assert len(result.explanation) > 20


def test_tool_removed_generates_pin_stub():
    f = DriftFinding(
        layer="l0_capability",
        severity="breaking",
        change_type="tool_removed",
        field_path=None,
        title="Tool 'search' was removed",
        evidence={"layer": "l0_capability", "test": "schema_diff", "statistic": 1.0, "p_value": None, "p_value_adjusted": None, "field_volatility": 0.0, "baseline": {"tool_name": "search", "present": True}, "current": {"tool_name": "search", "present": False}, "detected_pattern": {"kind": "tool_removed"}, "plain_english": "Tool removed.", "affected_probesets": 1},
        confidence=1.0,
    )
    result = generate_patch(f)
    assert result is not None
    assert result.strategy == "pin"
    assert "tool_removed" in result.patch_diff or "PINNED" in result.patch_diff


def test_field_removed_generates_shim():
    f = _finding("breaking", "input_field_removed", field_path="results.field_name")
    result = generate_patch(f)
    assert result is not None
    assert result.strategy == "shim"


def test_no_patch_for_cosmetic_statistical():
    f = DriftFinding(
        layer="l2_statistical",
        severity="cosmetic",
        change_type="statistical_drift_kolmogorov_smirnov",
        field_path="some.field",
        title="Minor drift",
        evidence={},
        confidence=0.95,
    )
    result = generate_patch(f)
    assert result is None
