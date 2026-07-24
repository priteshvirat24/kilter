"""
engine/diff/l0_capability.py — Layer 0: Capability diff.

Input: two capability snapshots.
Cost: free. Determinism: total. Run: every probe cycle.

Detects tool added/removed/renamed, schema changes, description changes.
The tool-description insight: a tool's description is prompt content.
Embed descriptions, cosine-distance against baseline, threshold ~0.05.

Signature (identical to all diff layers):
    def diff(baseline: Baseline, current: list[Observation]) -> list[DriftFinding]

But L0 operates on capability snapshots, not observations. The primary entry
point is `diff_capabilities(baseline_snap, current_snap)`.
"""

from __future__ import annotations

import json
from typing import Any

from engine.diff.types import Baseline, DriftFinding, Layer, Observation, Severity

# Cosine distance threshold for tool description embedding comparison
_DESCRIPTION_COSINE_THRESHOLD = 0.05


def diff_capabilities(
    baseline_tools: list[dict[str, Any]],
    current_tools: list[dict[str, Any]],
    baseline_protocol: str | None,
    current_protocol: str | None,
    description_embeddings: dict[str, list[float]] | None = None,
    baseline_embeddings: dict[str, list[float]] | None = None,
) -> list[DriftFinding]:
    """
    Compare two capability snapshots and return findings.

    description_embeddings: tool_name -> current embedding vector
    baseline_embeddings:    tool_name -> baseline embedding vector
    """
    findings: list[DriftFinding] = []

    baseline_by_name = {t["name"]: t for t in baseline_tools}
    current_by_name = {t["name"]: t for t in current_tools}

    baseline_names = set(baseline_by_name)
    current_names = set(current_by_name)

    # ── Tool removed (BREAKING) ──────────────────────────────────────────────
    for name in baseline_names - current_names:
        findings.append(
            DriftFinding(
                layer="l0_capability",
                severity="breaking",
                change_type="tool_removed",
                field_path=None,
                title=f"Tool '{name}' was removed",
                evidence={
                    "layer": "l0_capability",
                    "test": "schema_diff",
                    "statistic": 1.0,
                    "p_value": None,
                    "p_value_adjusted": None,
                    "field_volatility": 0.0,
                    "baseline": {"tool_name": name, "present": True},
                    "current": {"tool_name": name, "present": False},
                    "detected_pattern": {"kind": "tool_removed"},
                    "plain_english": (
                        f"The tool '{name}' was present in the baseline capability snapshot "
                        f"but is no longer advertised by the server. Any agent calls to this "
                        f"tool will now fail."
                    ),
                    "affected_probesets": 1,
                },
                confidence=1.0,
            )
        )

    # ── Tool added (COSMETIC — new tools don't break existing callers) ────────
    for name in current_names - baseline_names:
        findings.append(
            DriftFinding(
                layer="l0_capability",
                severity="cosmetic",
                change_type="tool_added",
                field_path=None,
                title=f"Tool '{name}' was added",
                evidence={
                    "layer": "l0_capability",
                    "test": "schema_diff",
                    "statistic": 1.0,
                    "p_value": None,
                    "p_value_adjusted": None,
                    "field_volatility": 0.0,
                    "baseline": {"tool_name": name, "present": False},
                    "current": {"tool_name": name, "present": True},
                    "detected_pattern": {"kind": "tool_added"},
                    "plain_english": f"A new tool '{name}' is now advertised by the server.",
                    "affected_probesets": 0,
                },
                confidence=1.0,
            )
        )

    # ── Tools present in both — compare schemas ───────────────────────────────
    for name in baseline_names & current_names:
        b_tool = baseline_by_name[name]
        c_tool = current_by_name[name]
        findings.extend(_diff_tool(b_tool, c_tool))

        # ── Description change (BEHAVIORAL) via embedding cosine distance ──
        if (
            description_embeddings is not None
            and baseline_embeddings is not None
            and name in description_embeddings
            and name in baseline_embeddings
        ):
            dist = _cosine_distance(
                baseline_embeddings[name], description_embeddings[name]
            )
            if dist >= _DESCRIPTION_COSINE_THRESHOLD:
                findings.append(
                    DriftFinding(
                        layer="l0_capability",
                        severity="behavioral",
                        change_type="description_changed",
                        field_path=None,
                        title=f"Tool description for '{name}' changed (cosine distance {dist:.2f})",
                        evidence={
                            "layer": "l0_capability",
                            "test": "cosine",
                            "statistic": dist,
                            "p_value": None,
                            "p_value_adjusted": None,
                            "field_volatility": 0.0,
                            "baseline": {
                                "description": b_tool.get("description", ""),
                            },
                            "current": {
                                "description": c_tool.get("description", ""),
                            },
                            "detected_pattern": {"kind": "description_changed"},
                            "plain_english": (
                                f"The description of tool '{name}' changed. "
                                f"Tool descriptions are serialized directly into the agent's context — "
                                f"this change may affect when and how agents call this tool "
                                f"(cosine distance: {dist:.3f})."
                            ),
                            "affected_probesets": 1,
                        },
                        confidence=float(min(1.0, dist / 0.5)),
                    )
                )
        elif b_tool.get("description", "") != c_tool.get("description", ""):
            # Fallback: no embeddings — flag on any text change
            findings.append(
                DriftFinding(
                    layer="l0_capability",
                    severity="behavioral",
                    change_type="description_changed",
                    field_path=None,
                    title=f"Tool description for '{name}' changed",
                    evidence={
                        "layer": "l0_capability",
                        "test": "schema_diff",
                        "statistic": 1.0,
                        "p_value": None,
                        "p_value_adjusted": None,
                        "field_volatility": 0.0,
                        "baseline": {"description": b_tool.get("description", "")},
                        "current": {"description": c_tool.get("description", "")},
                        "detected_pattern": {"kind": "description_changed"},
                        "plain_english": (
                            f"The description of tool '{name}' changed. "
                            f"Tool descriptions are prompt content — this may alter agent behavior."
                        ),
                        "affected_probesets": 1,
                    },
                    confidence=0.9,
                )
            )

    # ── Protocol revision change (BEHAVIORAL) ────────────────────────────────
    if baseline_protocol and current_protocol and baseline_protocol != current_protocol:
        findings.append(
            DriftFinding(
                layer="l0_capability",
                severity="behavioral",
                change_type="protocol_revision_changed",
                field_path=None,
                title=f"Protocol revision changed from {baseline_protocol} to {current_protocol}",
                evidence={
                    "layer": "l0_capability",
                    "test": "schema_diff",
                    "statistic": 1.0,
                    "p_value": None,
                    "p_value_adjusted": None,
                    "field_volatility": 0.0,
                    "baseline": {"protocol_revision": baseline_protocol},
                    "current": {"protocol_revision": current_protocol},
                    "detected_pattern": {"kind": "protocol_revision_changed"},
                    "plain_english": (
                        f"The server's MCP protocol revision changed from '{baseline_protocol}' "
                        f"to '{current_protocol}'. This may affect clients that match exact "
                        f"revision strings."
                    ),
                    "affected_probesets": 0,
                },
                confidence=1.0,
            )
        )

    return findings


def _diff_tool(b_tool: dict[str, Any], c_tool: dict[str, Any]) -> list[DriftFinding]:
    """Compare schemas of two tools with the same name."""
    findings: list[DriftFinding] = []
    name = b_tool["name"]

    b_schema = b_tool.get("inputSchema", {}) or {}
    c_schema = c_tool.get("inputSchema", {}) or {}

    b_props = b_schema.get("properties", {}) if isinstance(b_schema, dict) else {}
    c_props = c_schema.get("properties", {}) if isinstance(c_schema, dict) else {}
    b_required = set(b_schema.get("required", []) if isinstance(b_schema, dict) else [])
    c_required = set(c_schema.get("required", []) if isinstance(c_schema, dict) else [])

    b_fields = set(b_props)
    c_fields = set(c_props)

    # ── Required field added (BREAKING) ──────────────────────────────────────
    for field in (c_required - b_required) & c_fields:
        findings.append(_make_field_finding(
            "breaking", "required_field_added", name, field,
            f"Required input field '{field}' added to tool '{name}'",
            b_schema, c_schema,
            "Agents that do not provide this field will now receive an error.",
        ))

    # ── Field removed (BREAKING) ──────────────────────────────────────────────
    for field in b_fields - c_fields:
        findings.append(_make_field_finding(
            "breaking", "input_field_removed", name, field,
            f"Input field '{field}' removed from tool '{name}'",
            b_schema, c_schema,
            f"Agents passing '{field}' will now receive an error or it will be ignored.",
        ))

    # ── Field type changed (BREAKING) ─────────────────────────────────────────
    for field in b_fields & c_fields:
        b_type = b_props[field].get("type") if isinstance(b_props[field], dict) else None
        c_type = c_props[field].get("type") if isinstance(c_props[field], dict) else None
        if b_type and c_type and b_type != c_type:
            findings.append(_make_field_finding(
                "breaking", "field_type_changed", name, field,
                f"Type of '{field}' changed from {b_type} to {c_type} in tool '{name}'",
                b_schema, c_schema,
                f"Agents providing a {b_type} for '{field}' will receive a type error.",
            ))

    # ── Enum value removed (BREAKING) ─────────────────────────────────────────
    for field in b_fields & c_fields:
        b_enum = set(b_props[field].get("enum", []) if isinstance(b_props[field], dict) else [])
        c_enum = set(c_props[field].get("enum", []) if isinstance(c_props[field], dict) else [])
        if b_enum and c_enum:
            removed = b_enum - c_enum
            added = c_enum - b_enum
            for val in removed:
                findings.append(_make_field_finding(
                    "breaking", "enum_value_removed", name, field,
                    f"Enum value '{val}' removed from '{field}' in tool '{name}'",
                    b_schema, c_schema,
                    f"Agents passing '{val}' for '{field}' will now receive an error.",
                ))
            for val in added:
                findings.append(_make_field_finding(
                    "behavioral", "enum_value_added", name, field,
                    f"Enum value '{val}' added to '{field}' in tool '{name}'",
                    b_schema, c_schema,
                    f"The field '{field}' now accepts the new value '{val}'.",
                ))

    # ── Optional field added (COSMETIC) ──────────────────────────────────────
    for field in (c_fields - b_fields):
        if field not in c_required:
            findings.append(_make_field_finding(
                "cosmetic", "optional_field_added", name, field,
                f"Optional input field '{field}' added to tool '{name}'",
                b_schema, c_schema,
                f"The tool now accepts an optional '{field}' parameter.",
            ))

    # ── Output schema changed (BEHAVIORAL) ───────────────────────────────────
    b_out = json.dumps(b_tool.get("outputSchema", {}), sort_keys=True)
    c_out = json.dumps(c_tool.get("outputSchema", {}), sort_keys=True)
    if b_out != c_out and (b_out != "{}" or c_out != "{}"):
        findings.append(
            DriftFinding(
                layer="l0_capability",
                severity="behavioral",
                change_type="output_schema_changed",
                field_path=None,
                title=f"Output schema changed for tool '{name}'",
                evidence={
                    "layer": "l0_capability",
                    "test": "schema_diff",
                    "statistic": 1.0,
                    "p_value": None,
                    "p_value_adjusted": None,
                    "field_volatility": 0.0,
                    "baseline": {"output_schema": b_tool.get("outputSchema", {})},
                    "current": {"output_schema": c_tool.get("outputSchema", {})},
                    "detected_pattern": {"kind": "output_schema_changed"},
                    "plain_english": f"The output schema for tool '{name}' changed.",
                    "affected_probesets": 1,
                },
                confidence=1.0,
            )
        )

    return findings


def _make_field_finding(
    severity: Severity,
    change_type: str,
    tool_name: str,
    field: str,
    title: str,
    b_schema: dict[str, Any],
    c_schema: dict[str, Any],
    plain_english: str,
) -> DriftFinding:
    return DriftFinding(
        layer="l0_capability",
        severity=severity,
        change_type=change_type,
        field_path=field,
        title=title,
        evidence={
            "layer": "l0_capability",
            "test": "schema_diff",
            "statistic": 1.0,
            "p_value": None,
            "p_value_adjusted": None,
            "field_volatility": 0.0,
            "baseline": {"tool": tool_name, "schema": b_schema},
            "current": {"tool": tool_name, "schema": c_schema},
            "detected_pattern": {"kind": change_type, "field": field},
            "plain_english": plain_english,
            "affected_probesets": 1,
        },
        confidence=1.0,
    )


def _cosine_distance(a: list[float], b: list[float]) -> float:
    """1 - cosine_similarity(a, b). Range [0, 2]; 0 = identical."""
    import math
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 1.0
    similarity = dot / (norm_a * norm_b)
    return 1.0 - similarity


# ─────────────────────────────────────────────────────────────────────────────
# Adapter: satisfies the standard diff() signature
# (L0 is special — it's called on snapshots, not observations)
# ─────────────────────────────────────────────────────────────────────────────


def diff(baseline: Baseline, current: list[Observation]) -> list[DriftFinding]:
    """
    Standard signature adapter. L0 cannot produce meaningful findings from
    observation payloads alone — call diff_capabilities() directly instead.
    This stub exists to satisfy the uniform interface contract.
    """
    return []
