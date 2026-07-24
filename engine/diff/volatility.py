"""
engine/diff/volatility.py — Per-field volatility profiling.

Volatility: 0.0 = perfectly stable, 1.0 = completely chaotic.

Computed from the baseline window only — never contaminated by current window.
Used to set per-field alert thresholds in L2 statistical diff.

Design:
  - request_id, timestamp, latency_ms → volatility ≈ 1.0 → effectively never alert
  - results[*].score                  → volatility ≈ 0.4 → alert on large shifts
  - currency, unit, status_enum       → volatility ≈ 0.0 → alert on any change at all
"""

from __future__ import annotations

import math
import statistics
from typing import Any

from engine.diff.l1_structural import _json_type


def compute_volatility(
    observations: list[dict[str, Any] | None],
) -> dict[str, float]:
    """
    Given a list of raw_response dicts from the baseline window, return a
    per-path volatility score in [0.0, 1.0].

    path → 0.0 = completely stable (never changes)
    path → 1.0 = maximally volatile (changes every observation)

    Also applies heuristic boosts for known high-volatility patterns:
    - Fields whose names contain 'timestamp', 'request_id', 'latency', 'time', 'at'
      → clamped to 1.0 (always volatile).
    """
    # Collect all values per path across all observations
    path_values: dict[str, list[Any]] = {}

    for raw in observations:
        if raw is None:
            continue
        paths = _extract_paths(raw)
        for path, value in paths.items():
            path_values.setdefault(path, []).append(value)

    result: dict[str, float] = {}

    for path, values in path_values.items():
        # Heuristic: known always-volatile path names
        if _is_always_volatile_name(path):
            result[path] = 1.0
            continue

        if len(values) < 2:
            result[path] = 0.0
            continue

        dtype = _json_type(values[0])

        if dtype == "number":
            result[path] = _numeric_volatility(values)
        elif dtype == "string":
            result[path] = _categorical_volatility(values)
        elif dtype == "bool":
            result[path] = _categorical_volatility(values)
        elif dtype == "null":
            result[path] = 0.0
        elif dtype == "array":
            # Use cardinality variation as proxy
            cards = [len(v) for v in values if isinstance(v, list)]
            result[path] = _numeric_volatility(cards) if cards else 0.0
        else:
            result[path] = _categorical_volatility([str(v) for v in values])

    return result


def _is_always_volatile_name(path: str) -> bool:
    """Heuristic: paths that contain these tokens are always volatile."""
    lower = path.lower()
    always_volatile_tokens = {
        "timestamp", "request_id", "latency", "latency_ms", "time",
        "_at", "created_at", "updated_at", "modified_at", "expires_at",
        "date", "nonce", "token", "session",
    }
    return any(token in lower for token in always_volatile_tokens)


def _numeric_volatility(values: list[Any]) -> float:
    """
    Coefficient of variation (std/|mean|) normalized to [0, 1].
    A CV of 0 = perfectly stable. A CV > 1 is capped at 1.0.
    """
    nums = [v for v in values if isinstance(v, (int, float))]
    if len(nums) < 2:
        return 0.0
    try:
        mu = statistics.mean(nums)
        sigma = statistics.stdev(nums)
    except statistics.StatisticsError:
        return 0.0
    if mu == 0:
        return min(1.0, sigma)
    cv = sigma / abs(mu)
    return min(1.0, cv)


def _categorical_volatility(values: list[Any]) -> float:
    """
    Proportion of unique values. 0 = all same, 1 = all different.
    """
    if len(values) < 2:
        return 0.0
    unique = len(set(str(v) for v in values))
    return (unique - 1) / (len(values) - 1)


def _extract_paths(obj: Any, prefix: str = "") -> dict[str, Any]:
    """Flatten a JSON object to {path: leaf_value} pairs."""
    result: dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            child = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)):
                result.update(_extract_paths(v, child))
            else:
                result[child] = v
    elif isinstance(obj, list):
        item_path = f"{prefix}[*]"
        if obj:
            item = obj[0]
            if isinstance(item, (dict, list)):
                result.update(_extract_paths(item, item_path))
            else:
                result[item_path] = item
    else:
        result[prefix] = obj
    return result
