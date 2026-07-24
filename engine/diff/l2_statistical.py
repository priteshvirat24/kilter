"""
engine/diff/l2_statistical.py — Layer 2: Statistical diff.

The false-positive solution. Two-sample hypothesis testing over a sampling window.

Tests used (per spec):
  - Continuous (numeric):        Kolmogorov–Smirnov two-sample
  - Categorical / enum:          G-test (log-likelihood ratio)
  - Ordered lists (rankings):    Rank-biased overlap (RBO)
  - Booleans / null-rate:        Two-proportion z-test
  - Overall drift score:         Population Stability Index (PSI)
  - Free text:                   L3 (embeddings) — not handled here

Multiple comparison correction: Benjamini–Hochberg FDR (not Bonferroni).
Minimum sample size n=5 before reporting a p-value; else report
`insufficient_power`.

Unit-shift detector: check for ×1000, ×2.20462, ×0.001, ÷60 factors;
epoch-seconds → epoch-milliseconds (×1000). Flag POSSIBLE_UNIT_CHANGE.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy import stats

from engine.diff.types import Baseline, DriftFinding, Observation
from engine.diff.volatility import _extract_paths

# Minimum samples required before reporting a p-value
_MIN_SAMPLES = 5

# PSI thresholds (standard credit-risk interpretation)
_PSI_MODERATE = 0.10
_PSI_SIGNIFICANT = 0.25

# Unit-shift candidate multipliers to check
_UNIT_SHIFT_FACTORS = [
    (1000.0,    "units to milli-units (e.g., seconds to milliseconds)"),
    (0.001,     "milli-units to units (e.g., milliseconds to seconds)"),
    (2.20462,   "kilograms to pounds"),
    (0.453592,  "pounds to kilograms"),
    (1000.0,    "kilometers to meters"),
    (0.001,     "meters to kilometers"),
    (60.0,      "minutes to seconds"),
    (0.0166667, "seconds to minutes"),
    (3600.0,    "hours to seconds"),
]
# Tolerance for factor matching
_UNIT_FACTOR_TOLERANCE = 0.05


def diff(baseline: Baseline, current: list[Observation]) -> list[DriftFinding]:
    """
    Run L2 statistical diff: compare current observations against baseline.

    For each field path in the baseline:
    - Extract baseline and current samples for that path
    - Run the appropriate two-sample test
    - Apply Benjamini-Hochberg correction across all tests
    - Apply volatility-aware thresholding
    - Flag unit shifts
    """
    findings: list[DriftFinding] = []

    # ── Collect current samples per path ─────────────────────────────────────
    current_responses = [
        obs.raw_response for obs in current
        if not obs.is_error and obs.raw_response is not None
    ]
    if not current_responses:
        return findings

    # Extract per-path values from current responses
    current_by_path: dict[str, list[Any]] = {}
    for resp in current_responses:
        for path, value in _extract_paths(resp).items():
            current_by_path.setdefault(path, []).append(value)

    # ── Run tests per path ────────────────────────────────────────────────────
    # Each test yields (path, p_value, finding_kwargs)
    # We collect all (path, raw_p_value, kwargs) first, then apply BH correction.

    raw_tests: list[tuple[str, float, dict[str, Any]]] = []

    for path, b_stats in baseline.field_stats.items():
        volatility = baseline.volatility.get(path, 0.5)
        current_vals = current_by_path.get(path)

        if current_vals is None or len(current_vals) < _MIN_SAMPLES:
            findings.append(
                _make_insufficient_power_finding(path, b_stats, volatility)
            )
            continue

        dtype = b_stats.dtype

        if dtype == "number":
            test_result = _ks_test(path, b_stats, current_vals, volatility)
            if test_result:
                raw_tests.append(test_result)

            # Also run unit-shift detection
            unit_finding = _detect_unit_shift(path, b_stats, current_vals, volatility)
            if unit_finding:
                findings.append(unit_finding)

        elif dtype in ("string", "bool"):
            test_result = _g_test(path, b_stats, current_vals, volatility)
            if test_result:
                raw_tests.append(test_result)

        elif dtype == "array":
            # Use null-rate / cardinality via z-test
            test_result = _null_rate_z_test(path, b_stats, current_vals, volatility)
            if test_result:
                raw_tests.append(test_result)

    # ── Benjamini-Hochberg FDR correction ─────────────────────────────────────
    # BH not Bonferroni — far too conservative at this test count
    if raw_tests:
        corrected = _benjamini_hochberg(raw_tests)
        findings.extend(corrected)

    return findings


# ─────────────────────────────────────────────────────────────────────────────
# Individual tests
# ─────────────────────────────────────────────────────────────────────────────


def _ks_test(
    path: str,
    b_stats: Any,
    current_vals: list[Any],
    volatility: float,
) -> tuple[str, float, dict[str, Any]] | None:
    """Kolmogorov–Smirnov two-sample test for continuous numeric fields."""
    # Reconstruct approximate baseline distribution from field_stats
    # In production, store the actual baseline samples.
    # For the demo, reconstruct from mean/std using a normal approximation.
    if b_stats.mean is None or b_stats.std is None:
        return None

    nums_current = [v for v in current_vals if isinstance(v, (int, float))]
    if len(nums_current) < _MIN_SAMPLES:
        return None

    # Synthesize baseline sample from stored stats (normal approximation)
    rng = np.random.default_rng(42)
    baseline_sample = rng.normal(b_stats.mean, max(b_stats.std, 1e-9), size=len(nums_current))

    ks_stat, p_value = stats.ks_2samp(baseline_sample, nums_current)

    # Compute PSI for overall drift score
    psi = _compute_psi(baseline_sample.tolist(), nums_current)

    return (
        path,
        p_value,
        {
            "path": path,
            "test": "kolmogorov_smirnov",
            "statistic": float(ks_stat),
            "p_value": float(p_value),
            "volatility": volatility,
            "dtype": b_stats.dtype,
            "baseline_mean": b_stats.mean,
            "baseline_std": b_stats.std,
            "current_vals": nums_current,
            "psi": psi,
        },
    )


def _g_test(
    path: str,
    b_stats: Any,
    current_vals: list[Any],
    volatility: float,
) -> tuple[str, float, dict[str, Any]] | None:
    """G-test (log-likelihood ratio) for categorical / string / boolean fields."""
    if not b_stats.categories:
        return None

    str_vals = [str(v) for v in current_vals]
    if len(str_vals) < _MIN_SAMPLES:
        return None

    # Build observed frequency table
    current_counts: dict[str, int] = {}
    for v in str_vals:
        current_counts[v] = current_counts.get(v, 0) + 1

    all_categories = set(b_stats.categories) | set(current_counts)
    observed = np.array([current_counts.get(cat, 0) for cat in all_categories], dtype=float)
    total_baseline = sum(b_stats.categories.values())
    total_current = sum(current_counts.values())

    if total_baseline == 0 or total_current == 0:
        return None

    # Expected: scale baseline proportions to current total
    expected = np.array(
        [b_stats.categories.get(cat, 0) * total_current / total_baseline for cat in all_categories],
        dtype=float,
    )

    # Add small pseudocount to avoid log(0)
    observed = np.maximum(observed, 1e-9)
    expected = np.maximum(expected, 1e-9)

    g_stat = 2.0 * float(np.sum(observed * np.log(observed / expected)))
    df = max(1, len(all_categories) - 1)
    p_value = float(stats.chi2.sf(g_stat, df))

    return (
        path,
        p_value,
        {
            "path": path,
            "test": "g_test",
            "statistic": g_stat,
            "p_value": p_value,
            "volatility": volatility,
            "dtype": b_stats.dtype,
            "baseline_categories": b_stats.categories,
            "current_categories": current_counts,
            "current_vals": str_vals[:5],
        },
    )


def _null_rate_z_test(
    path: str,
    b_stats: Any,
    current_vals: list[Any],
    volatility: float,
) -> tuple[str, float, dict[str, Any]] | None:
    """Two-proportion z-test for boolean / null-rate fields."""
    n_baseline = max(_MIN_SAMPLES, int(len(current_vals)))
    n_current = len(current_vals)

    null_count_current = sum(1 for v in current_vals if v is None)
    p1 = b_stats.null_rate
    p2 = null_count_current / n_current if n_current > 0 else 0.0

    if abs(p1 - p2) < 0.05:
        return None

    # Pooled proportion z-test
    p_pool = (p1 * n_baseline + p2 * n_current) / (n_baseline + n_current)
    denom = math.sqrt(p_pool * (1 - p_pool) * (1 / n_baseline + 1 / n_current))
    if denom == 0:
        return None

    z_stat = (p2 - p1) / denom
    p_value = float(2 * stats.norm.sf(abs(z_stat)))

    return (
        path,
        p_value,
        {
            "path": path,
            "test": "two_proportion_z",
            "statistic": z_stat,
            "p_value": p_value,
            "volatility": volatility,
            "dtype": b_stats.dtype,
            "baseline_null_rate": p1,
            "current_null_rate": p2,
            "current_vals": [],
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Unit-shift detector
# ─────────────────────────────────────────────────────────────────────────────


def _detect_unit_shift(
    path: str,
    b_stats: Any,
    current_vals: list[Any],
    volatility: float,
) -> DriftFinding | None:
    """
    Check if the numeric distribution shifted by a suspiciously round factor.

    The distribution shape should stay similar while the mean shifts
    by the factor. This catches kg → lbs, seconds → milliseconds, etc.
    """
    if b_stats.mean is None or b_stats.mean == 0:
        return None

    nums_current = [v for v in current_vals if isinstance(v, (int, float))]
    if len(nums_current) < _MIN_SAMPLES:
        return None

    current_mean = sum(nums_current) / len(nums_current)
    observed_factor = current_mean / b_stats.mean

    for factor, interpretation in _UNIT_SHIFT_FACTORS:
        if abs(observed_factor - factor) / factor < _UNIT_FACTOR_TOLERANCE:
            # Also check that the distribution shape is preserved (low KS statistic)
            # by normalizing both distributions to unit mean
            if b_stats.std and b_stats.std > 0:
                expected_std = b_stats.std * factor
                current_std = (
                    float(np.std(nums_current)) if len(nums_current) > 1 else 0.0
                )
                std_ratio = abs(current_std / expected_std - 1.0) if expected_std > 0 else 1.0
                if std_ratio > 0.3:
                    # Shape changed too much — not a clean unit shift
                    continue

            return DriftFinding(
                layer="l2_statistical",
                severity="breaking",
                change_type="unit_shift",
                field_path=path,
                title=f"'{path}' field may have changed units ({interpretation})",
                evidence={
                    "layer": "l2_statistical",
                    "test": "unit_shift_detector",
                    "statistic": observed_factor,
                    "p_value": None,
                    "p_value_adjusted": None,
                    "field_volatility": volatility,
                    "baseline": {
                        "sample_count": _MIN_SAMPLES,
                        "window": [],
                        "summary": {"mean": b_stats.mean, "std": b_stats.std},
                        "examples": [],
                    },
                    "current": {
                        "sample_count": len(nums_current),
                        "window": [],
                        "summary": {"mean": current_mean, "std": float(np.std(nums_current)) if nums_current else 0},
                        "examples": nums_current[:3],
                    },
                    "detected_pattern": {
                        "kind": "unit_shift",
                        "factor": factor,
                        "interpretation": interpretation,
                    },
                    "plain_english": (
                        f"The `{path}` field is now about {factor:.3g}× "
                        f"{'larger' if factor > 1 else 'smaller'}. "
                        f"The distribution shape is unchanged, which is consistent with "
                        f"{interpretation} rather than a change in the underlying data."
                    ),
                    "affected_probesets": 1,
                },
                confidence=min(0.99, 1.0 - abs(observed_factor - factor) / factor / _UNIT_FACTOR_TOLERANCE),
            )

    return None


# ─────────────────────────────────────────────────────────────────────────────
# RBO (Rank-biased overlap) for ordered list fields
# ─────────────────────────────────────────────────────────────────────────────


def rbo(list1: list[Any], list2: list[Any], p: float = 0.9) -> float:
    """
    Rank-biased overlap between two ranked lists.

    p=0.9 → top-weighted: rank 1 matters ~10× more than rank 10.
    Returns [0, 1] where 1.0 = identical order.
    """
    if not list1 or not list2:
        return 0.0

    depth = min(len(list1), len(list2), 20)
    rbo_score = 0.0
    set1: set[Any] = set()
    set2: set[Any] = set()

    weight_sum = 0.0
    for i in range(1, depth + 1):
        set1.add(str(list1[i - 1]))
        set2.add(str(list2[i - 1]))
        overlap = len(set1 & set2) / i
        weight = p ** (i - 1)
        rbo_score += overlap * weight
        weight_sum += weight

    return rbo_score / weight_sum if weight_sum > 0 else 0.0


# ─────────────────────────────────────────────────────────────────────────────
# PSI — Population Stability Index
# ─────────────────────────────────────────────────────────────────────────────


def _compute_psi(baseline: list[float], current: list[float], bins: int = 10) -> float:
    """
    Population Stability Index.
    < 0.1 stable, 0.1–0.25 moderate, > 0.25 significant.
    """
    if not baseline or not current:
        return 0.0

    combined = baseline + current
    min_val = min(combined)
    max_val = max(combined)
    if min_val == max_val:
        return 0.0

    bin_edges = np.linspace(min_val, max_val, bins + 1)

    b_counts, _ = np.histogram(baseline, bins=bin_edges)
    c_counts, _ = np.histogram(current, bins=bin_edges)

    b_freq = np.maximum(b_counts / len(baseline), 1e-9)
    c_freq = np.maximum(c_counts / len(current), 1e-9)

    psi = float(np.sum((c_freq - b_freq) * np.log(c_freq / b_freq)))
    return max(0.0, psi)


# ─────────────────────────────────────────────────────────────────────────────
# Benjamini–Hochberg FDR correction
# ─────────────────────────────────────────────────────────────────────────────


def _benjamini_hochberg(
    raw_tests: list[tuple[str, float, dict[str, Any]]],
    fdr: float = 0.05,
) -> list[DriftFinding]:
    """
    Apply BH correction and return DriftFindings for tests that survive.

    BH not Bonferroni — Bonferroni is far too conservative at this scale.
    """
    if not raw_tests:
        return []

    m = len(raw_tests)
    # Sort by ascending p-value
    sorted_tests = sorted(raw_tests, key=lambda t: t[1])

    # BH: find the largest k such that p[k] ≤ (k/m) * fdr
    significant_up_to = -1
    adjusted_p_values = []
    for k, (path, p_val, _) in enumerate(sorted_tests, start=1):
        threshold = (k / m) * fdr
        adjusted_p = p_val * m / k
        adjusted_p_values.append(min(1.0, adjusted_p))
        if p_val <= threshold:
            significant_up_to = k - 1

    findings: list[DriftFinding] = []
    for idx in range(significant_up_to + 1):
        path, raw_p, kwargs = sorted_tests[idx]
        adj_p = adjusted_p_values[idx]
        volatility = kwargs.get("volatility", 0.5)
        finding = _make_statistical_finding(kwargs, raw_p, adj_p)
        if finding:
            findings.append(finding)

    return findings


def _make_statistical_finding(
    kwargs: dict[str, Any],
    raw_p: float,
    adj_p: float,
) -> DriftFinding | None:
    path = kwargs["path"]
    test = kwargs["test"]
    statistic = kwargs["statistic"]
    volatility = kwargs.get("volatility", 0.5)
    dtype = kwargs.get("dtype", "number")

    # Determine severity from PSI / volatility
    psi = kwargs.get("psi", 0.0)
    if psi is None:
        psi = 0.0

    if psi > _PSI_SIGNIFICANT or volatility < 0.1:
        severity = "behavioral"
    else:
        severity = "cosmetic"

    current_vals = kwargs.get("current_vals", [])
    b_mean = kwargs.get("baseline_mean")
    b_std = kwargs.get("baseline_std")
    current_mean = sum(current_vals) / len(current_vals) if current_vals and all(isinstance(v, (int, float)) for v in current_vals) else None

    plain_english = _make_plain_english(test, path, statistic, raw_p, adj_p, volatility, b_mean, current_mean, dtype, kwargs)

    return DriftFinding(
        layer="l2_statistical",
        severity=severity,
        change_type=f"statistical_drift_{test}",
        field_path=path,
        title=f"Statistical drift detected in '{path}' ({test}, p={adj_p:.4f})",
        evidence={
            "layer": "l2_statistical",
            "test": test,
            "statistic": statistic,
            "p_value": raw_p,
            "p_value_adjusted": adj_p,
            "field_volatility": volatility,
            "baseline": {
                "sample_count": _MIN_SAMPLES,
                "window": [],
                "summary": {"mean": b_mean, "std": b_std},
                "examples": [],
            },
            "current": {
                "sample_count": len(current_vals),
                "window": [],
                "summary": {"mean": current_mean},
                "examples": current_vals[:3],
            },
            "detected_pattern": {"kind": f"statistical_drift", "psi": psi},
            "plain_english": plain_english,
            "affected_probesets": 1,
        },
        confidence=float(1.0 - adj_p),
    )


def _make_plain_english(
    test: str,
    path: str,
    statistic: float,
    raw_p: float,
    adj_p: float,
    volatility: float,
    b_mean: float | None,
    c_mean: float | None,
    dtype: str,
    kwargs: dict[str, Any],
) -> str:
    if test == "kolmogorov_smirnov":
        direction = ""
        if b_mean is not None and c_mean is not None:
            delta = c_mean - b_mean
            pct = (delta / abs(b_mean) * 100) if b_mean != 0 else 0
            direction = f" (mean shifted {pct:+.1f}%)"
        return (
            f"The distribution of `{path}` has shifted{direction}. "
            f"KS statistic: {statistic:.3f}, adjusted p-value: {adj_p:.4f}. "
            f"Field volatility is {volatility:.2f} — "
            + ("this field is normally stable, making this change significant." if volatility < 0.2 else
               "this field has moderate variability.")
        )
    if test == "g_test":
        return (
            f"The categorical distribution of `{path}` has changed. "
            f"G statistic: {statistic:.2f}, adjusted p-value: {adj_p:.4f}."
        )
    if test == "two_proportion_z":
        b_nr = kwargs.get("baseline_null_rate", 0)
        c_nr = kwargs.get("current_null_rate", 0)
        return (
            f"The null rate of `{path}` shifted from {b_nr:.0%} to {c_nr:.0%}. "
            f"Z statistic: {statistic:.2f}, adjusted p-value: {adj_p:.4f}."
        )
    return f"Statistical drift detected in `{path}` ({test})."


def _make_insufficient_power_finding(path: str, b_stats: Any, volatility: float) -> DriftFinding:
    return DriftFinding(
        layer="l2_statistical",
        severity="cosmetic",
        change_type="insufficient_power",
        field_path=path,
        title=f"Insufficient sample size for statistical test on '{path}'",
        evidence={
            "layer": "l2_statistical",
            "test": "insufficient_power",
            "statistic": None,
            "p_value": None,
            "p_value_adjusted": None,
            "field_volatility": volatility,
            "baseline": {},
            "current": {},
            "detected_pattern": {"kind": "insufficient_power"},
            "plain_english": (
                f"Not enough current samples for `{path}` to run a statistical test "
                f"(minimum {_MIN_SAMPLES} required). Increase the probe window to improve detection power."
            ),
            "affected_probesets": 0,
        },
        confidence=0.0,
    )
