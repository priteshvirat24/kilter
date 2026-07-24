"""
engine/diff/l1_structural.py — Layer 1: Structural response diff.

Input: N baseline response samples, N current samples, per tool+args.
Cost: free. Determinism: total.

Computes a shape fingerprint per response: the set of JSON paths present,
the type at each path, array cardinalities, and null-rates per path.

CRITICAL: array paths collapse indices (items[*].price, not items[3].price)
or every response looks different and we get pure noise.
"""

from __future__ import annotations

from typing import Any

from engine.diff.types import Baseline, DriftFinding, Observation


def diff(baseline: Baseline, current: list[Observation]) -> list[DriftFinding]:
    """
    Compare structural fingerprints of current observations against baseline.

    Returns findings for:
    - New/removed fields in responses
    - Type shifts at a path (string → number, scalar → array)
    - Null-rate shifts
    - Cardinality shifts (array length changes)
    - Nesting changes
    """
    findings: list[DriftFinding] = []

    current_responses = [
        obs.raw_response for obs in current
        if not obs.is_error and obs.raw_response is not None
    ]
    if not current_responses:
        return findings

    # Compute current fingerprints
    current_fingerprints = [extract_shape_fingerprint(r) for r in current_responses]
    current_agg = _aggregate_fingerprints(current_fingerprints)

    # Baseline field_stats contains the baseline fingerprint summary
    baseline_paths = set(baseline.field_stats.keys())
    current_paths = set(current_agg.keys())

    # ── New fields (COSMETIC — may become BEHAVIORAL via L2) ──────────────────
    for path in current_paths - baseline_paths:
        findings.append(
            DriftFinding(
                layer="l1_structural",
                severity="cosmetic",
                change_type="field_added",
                field_path=path,
                title=f"New field '{path}' appeared in responses",
                evidence=_make_evidence(
                    path=path,
                    baseline_summary=None,
                    current_summary=current_agg[path],
                    pattern_kind="field_added",
                    plain_english=(
                        f"The field '{path}' is present in current responses but was absent "
                        f"in the baseline. This may indicate new functionality."
                    ),
                ),
                confidence=0.9,
            )
        )

    # ── Removed fields (BEHAVIORAL) ───────────────────────────────────────────
    for path in baseline_paths - current_paths:
        b_stats = baseline.field_stats[path]
        # If the field had a low null_rate in the baseline, its absence is meaningful
        severity = "behavioral" if b_stats.null_rate < 0.5 else "cosmetic"
        findings.append(
            DriftFinding(
                layer="l1_structural",
                severity=severity,
                change_type="field_removed",
                field_path=path,
                title=f"Field '{path}' disappeared from responses",
                evidence=_make_evidence(
                    path=path,
                    baseline_summary={
                        "null_rate": b_stats.null_rate,
                        "dtype": b_stats.dtype,
                    },
                    current_summary=None,
                    pattern_kind="field_removed",
                    plain_english=(
                        f"The field '{path}' was present in the baseline (null_rate={b_stats.null_rate:.0%}) "
                        f"but is no longer present in current responses. Agents reading this field "
                        f"may receive None or KeyError."
                    ),
                ),
                confidence=0.95,
            )
        )

    # ── Fields present in both — compare properties ───────────────────────────
    for path in baseline_paths & current_paths:
        b_stats = baseline.field_stats[path]
        c_summary = current_agg[path]

        # Type shift (BREAKING if scalar→array or vice versa, else BEHAVIORAL)
        c_dtype = c_summary.get("dtype")
        if c_dtype and c_dtype != b_stats.dtype:
            severity = (
                "breaking"
                if _is_structural_type_shift(b_stats.dtype, c_dtype)
                else "behavioral"
            )
            findings.append(
                DriftFinding(
                    layer="l1_structural",
                    severity=severity,
                    change_type="type_shift",
                    field_path=path,
                    title=f"Type of '{path}' changed from {b_stats.dtype} to {c_dtype}",
                    evidence=_make_evidence(
                        path=path,
                        baseline_summary={"dtype": b_stats.dtype, "null_rate": b_stats.null_rate},
                        current_summary=c_summary,
                        pattern_kind="type_shift",
                        plain_english=(
                            f"The field '{path}' was {b_stats.dtype} in the baseline "
                            f"and is now {c_dtype}. Code that casts this field to "
                            f"{b_stats.dtype} will now fail."
                        ),
                    ),
                    confidence=0.95,
                )
            )

        # Null-rate shift (BEHAVIORAL)
        c_null_rate = c_summary.get("null_rate")
        if c_null_rate is not None and b_stats.null_rate is not None:
            null_delta = abs(c_null_rate - b_stats.null_rate)
            if null_delta >= 0.2:  # 20pp shift
                findings.append(
                    DriftFinding(
                        layer="l1_structural",
                        severity="behavioral",
                        change_type="null_rate_shift",
                        field_path=path,
                        title=f"Null rate of '{path}' shifted from {b_stats.null_rate:.0%} to {c_null_rate:.0%}",
                        evidence=_make_evidence(
                            path=path,
                            baseline_summary={"null_rate": b_stats.null_rate},
                            current_summary=c_summary,
                            pattern_kind="null_rate_shift",
                            plain_english=(
                                f"The field '{path}' is now {c_null_rate:.0%} null "
                                f"(was {b_stats.null_rate:.0%}). This often signals an upstream "
                                f"data source degrading."
                            ),
                        ),
                        confidence=min(0.99, 0.5 + null_delta),
                    )
                )

        # Cardinality shift (BEHAVIORAL) — for array fields
        if b_stats.dtype == "array" and b_stats.cardinality is not None:
            c_card = c_summary.get("cardinality")
            if c_card is not None and b_stats.cardinality > 0:
                ratio = c_card / b_stats.cardinality
                if ratio < 0.5 or ratio > 2.0:
                    findings.append(
                        DriftFinding(
                            layer="l1_structural",
                            severity="behavioral",
                            change_type="cardinality_shift",
                            field_path=path,
                            title=(
                                f"'{path}' array length changed: "
                                f"median {b_stats.cardinality} → {c_card}"
                            ),
                            evidence=_make_evidence(
                                path=path,
                                baseline_summary={"cardinality": b_stats.cardinality},
                                current_summary=c_summary,
                                pattern_kind="cardinality_shift",
                                plain_english=(
                                    f"The '{path}' array returned {c_card} items on average "
                                    f"vs {b_stats.cardinality} in the baseline. "
                                    f"This may indicate a pagination default change."
                                ),
                            ),
                            confidence=0.85,
                        )
                    )

    return findings


# ─────────────────────────────────────────────────────────────────────────────
# Shape fingerprint computation
# ─────────────────────────────────────────────────────────────────────────────


def extract_shape_fingerprint(response: dict[str, Any]) -> dict[str, Any]:
    """
    Compute a shape fingerprint for a single JSON response.

    Returns: {
        "paths": [str],          # all JSON paths present
        "types": {path: dtype},  # type at each path
        "cardinality": {path: int},  # element count for array paths
        "null_rate": {path: float},  # 0.0 or 1.0 per observation; aggregate over many
    }
    """
    paths: dict[str, str] = {}      # path -> dtype string
    cardinality: dict[str, int] = {}

    _walk(response, "", paths, cardinality)

    return {
        "paths": sorted(paths.keys()),
        "types": paths,
        "cardinality": cardinality,
        "null_rate": {k: (1.0 if paths[k] == "null" else 0.0) for k in paths},
    }


def _walk(
    obj: Any,
    prefix: str,
    paths: dict[str, str],
    cardinality: dict[str, int],
) -> None:
    """Recursively walk a JSON value, recording paths and types."""
    dtype = _json_type(obj)

    if prefix:
        paths[prefix] = dtype

    if isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{prefix}.{key}" if prefix else key
            _walk(value, child_path, paths, cardinality)

    elif isinstance(obj, list):
        # Record cardinality at the array path
        if prefix:
            cardinality[prefix] = len(obj)
        # Walk items with collapsed index notation: items[*]
        item_path = f"{prefix}[*]" if prefix else "[*]"
        # Walk first item to establish schema; cardinality tracked above
        for item in obj:
            _walk(item, item_path, paths, cardinality)
            break  # schema from first element is sufficient for fingerprinting


def _json_type(obj: Any) -> str:
    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return "bool"
    if isinstance(obj, (int, float)):
        return "number"
    if isinstance(obj, str):
        return "string"
    if isinstance(obj, list):
        return "array"
    if isinstance(obj, dict):
        return "object"
    return "unknown"


def _is_structural_type_shift(from_dtype: str, to_dtype: str) -> bool:
    """True if the type shift is structurally breaking (scalar ↔ array/object)."""
    scalars = {"number", "string", "bool", "null"}
    containers = {"array", "object"}
    return (from_dtype in scalars and to_dtype in containers) or (
        from_dtype in containers and to_dtype in scalars
    )


# ─────────────────────────────────────────────────────────────────────────────
# Aggregation helpers
# ─────────────────────────────────────────────────────────────────────────────


def _aggregate_fingerprints(
    fingerprints: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """
    Aggregate a list of per-response fingerprints into per-path summaries.
    Returns {path: {dtype, null_rate, cardinality, present_rate}}.
    """
    if not fingerprints:
        return {}

    path_types: dict[str, list[str]] = {}
    path_cards: dict[str, list[int]] = {}
    path_present: dict[str, int] = {}
    n = len(fingerprints)

    for fp in fingerprints:
        types = fp.get("types", {})
        cards = fp.get("cardinality", {})
        for path, dtype in types.items():
            path_types.setdefault(path, []).append(dtype)
            path_present[path] = path_present.get(path, 0) + 1
        for path, card in cards.items():
            path_cards.setdefault(path, []).append(card)

    result: dict[str, dict[str, Any]] = {}
    for path, dtypes in path_types.items():
        # Most common dtype
        dtype_counts: dict[str, int] = {}
        for d in dtypes:
            dtype_counts[d] = dtype_counts.get(d, 0) + 1
        dominant_dtype = max(dtype_counts, key=lambda k: dtype_counts[k])
        null_rate = dtypes.count("null") / len(dtypes) if dtypes else 0.0
        cards = path_cards.get(path, [])
        cardinality = int(sum(cards) / len(cards)) if cards else None
        result[path] = {
            "dtype": dominant_dtype,
            "null_rate": null_rate,
            "cardinality": cardinality,
            "present_rate": path_present[path] / n,
        }

    return result


def _make_evidence(
    path: str,
    baseline_summary: dict[str, Any] | None,
    current_summary: dict[str, Any] | None,
    pattern_kind: str,
    plain_english: str,
) -> dict[str, Any]:
    return {
        "layer": "l1_structural",
        "test": "schema_diff",
        "statistic": 1.0,
        "p_value": None,
        "p_value_adjusted": None,
        "field_volatility": None,
        "baseline": baseline_summary or {},
        "current": current_summary or {},
        "detected_pattern": {"kind": pattern_kind, "field_path": path},
        "plain_english": plain_english,
        "affected_probesets": 1,
    }
