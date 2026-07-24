"""
engine/diff/severity.py — Severity classifier.

Takes a list of DriftFindings and produces the final classification.
Also handles the cosmetic-suppression logic: changes to fields with
volatility > 0.8 are always COSMETIC, regardless of test result.

This is a pure function — no I/O.
"""

from __future__ import annotations

from engine.diff.types import DriftFinding, Severity

# Fields with volatility above this are always cosmetic
_COSMETIC_VOLATILITY_THRESHOLD = 0.8


def classify(
    finding: DriftFinding,
    field_volatility: float | None = None,
) -> DriftFinding:
    """
    Apply final severity classification to a single finding.

    Rules (per spec):
    - Any field with volatility > 0.8 → COSMETIC, always.
    - BREAKING: tool removed, required field added, type changed,
                enum value removed, unit shift detected.
    - BEHAVIORAL: description changed, ranking shifted, null-rate shift,
                  cardinality change, semantic centroid shift.
    - COSMETIC: optional field added, whitespace, key reordering.
    """
    # Volatility override — always silences high-volatility fields
    if field_volatility is not None and field_volatility > _COSMETIC_VOLATILITY_THRESHOLD:
        return _with_severity(finding, "cosmetic")

    # change_type → severity map (per spec)
    breaking_types = {
        "tool_removed",
        "required_field_added",
        "type_shift",
        "field_type_changed",
        "enum_value_removed",
        "unit_shift",
    }
    behavioral_types = {
        "description_changed",
        "protocol_revision_changed",
        "output_schema_changed",
        "cardinality_shift",
        "null_rate_shift",
        "field_removed",
        "statistical_drift_kolmogorov_smirnov",
        "statistical_drift_g_test",
        "statistical_drift_two_proportion_z",
        "semantic_centroid_shift",
        "semantic_dispersion_change",
    }
    cosmetic_types = {
        "optional_field_added",
        "tool_added",
        "field_added",
        "insufficient_power",
        "enum_value_added",
    }

    if finding.change_type in breaking_types:
        return _with_severity(finding, "breaking")
    if finding.change_type in behavioral_types:
        return _with_severity(finding, "behavioral")
    if finding.change_type in cosmetic_types:
        return _with_severity(finding, "cosmetic")

    # Default: keep what the layer already assigned
    return finding


def classify_all(
    findings: list[DriftFinding],
    volatility: dict[str, float] | None = None,
) -> list[DriftFinding]:
    """Classify a list of findings, applying volatility context per field."""
    result: list[DriftFinding] = []
    for f in findings:
        vol = None
        if volatility and f.field_path:
            vol = volatility.get(f.field_path)
        result.append(classify(f, field_volatility=vol))
    return result


def _with_severity(finding: DriftFinding, severity: Severity) -> DriftFinding:
    if finding.severity == severity:
        return finding
    return DriftFinding(
        layer=finding.layer,
        severity=severity,
        change_type=finding.change_type,
        field_path=finding.field_path,
        title=finding.title,
        evidence=finding.evidence,
        confidence=finding.confidence,
    )
