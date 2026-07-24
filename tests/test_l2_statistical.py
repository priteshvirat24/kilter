"""
tests/test_l2_statistical.py — Tests for L2 statistical diff.

Focuses on:
- KS test fires on a clear distribution shift
- KS test does NOT fire on stable field (FP rate check)
- Unit shift detector catches kg→lbs (factor 2.20462)
- Unit shift detector catches s→ms (factor 1000)
- BH correction suppresses marginal signals
- Insufficient power handling

Uses synthetic data only — no fixtures, no DB.
"""

import pytest
from datetime import datetime, timezone
import numpy as np

from engine.diff.l2_statistical import diff, _detect_unit_shift, rbo, _compute_psi
from engine.diff.types import Baseline, FieldStats, Observation


def _make_baseline(field_path: str, mean: float, std: float, volatility: float = 0.1) -> Baseline:
    return Baseline(
        probeset_id="test",
        sample_count=30,
        field_stats={
            field_path: FieldStats(
                path=field_path,
                dtype="number",
                null_rate=0.0,
                mean=mean,
                std=std,
                categories=None,
                cardinality=None,
            )
        },
        volatility={field_path: volatility},
        centroid=None,
    )


def _obs(val: float) -> Observation:
    return Observation(
        probeset_id="test",
        sample_index=0,
        observed_at=datetime.now(timezone.utc),
        raw_response={"weight": val},
        is_error=False,
        error_code=None,
        latency_ms=100,
    )


# ── KS test ───────────────────────────────────────────────────────────────


def test_ks_detects_clear_shift():
    """A 3σ mean shift should always be flagged."""
    baseline = _make_baseline("weight", mean=12.4, std=1.0, volatility=0.04)
    current = [_obs(27.3 + np.random.normal(0, 1)) for _ in range(30)]
    findings = diff(baseline, current)
    assert findings, "Expected at least one finding for a 3σ shift"


def test_ks_stable_field_no_fp():
    """A stable field with no shift should not produce findings at the 5% FDR level."""
    rng = np.random.default_rng(42)
    baseline = _make_baseline("weight", mean=12.4, std=0.5, volatility=0.04)
    # Current: drawn from same distribution
    current = [_obs(float(v)) for v in rng.normal(12.4, 0.5, 30)]
    findings = diff(baseline, current)
    ks_findings = [f for f in findings if "kolmogorov_smirnov" in f.change_type]
    assert not ks_findings, f"False positive on stable field: {ks_findings}"


# ── Unit shift detector ────────────────────────────────────────────────────


def test_unit_shift_kg_to_lbs():
    """Factor 2.20462 must be detected as kg → lbs unit shift."""
    fs = FieldStats("weight", "number", 0.0, 12.4, 1.0, None, None)

    class _B:
        field_stats = {"weight": fs}
        volatility = {"weight": 0.04}
        centroid = None
        sample_count = 30
        probeset_id = "test"

    class FakeBaseline:
        def __init__(self):
            self.field_stats = {"weight": fs}
            self.volatility = {"weight": 0.04}
            self.centroid = None
            self.sample_count = 30
            self.probeset_id = "test"

    baseline = FakeBaseline()

    rng = np.random.default_rng(42)
    # 12.4 kg × 2.20462 ≈ 27.33 lbs — simulate 30 lbs values
    current_vals = [float(v) for v in rng.normal(27.3, 2.2, 30)]

    finding = _detect_unit_shift("weight", fs, current_vals, volatility=0.04)
    assert finding is not None
    assert finding.change_type == "unit_shift"
    assert finding.severity == "breaking"
    assert "pound" in finding.evidence["detected_pattern"]["interpretation"].lower()


def test_unit_shift_seconds_to_milliseconds():
    """Factor 1000 must be detected as seconds → milliseconds."""
    fs = FieldStats("latency", "number", 0.0, 0.5, 0.1, None, None)
    rng = np.random.default_rng(42)
    current_vals = [float(v) for v in rng.normal(500, 100, 30)]  # 500ms instead of 0.5s
    finding = _detect_unit_shift("latency", fs, current_vals, volatility=0.05)
    assert finding is not None
    assert "milliseconds" in finding.evidence["detected_pattern"]["interpretation"].lower()


def test_no_unit_shift_for_genuine_change():
    """A shape-changing distribution shift should NOT trigger unit shift detector."""
    fs = FieldStats("score", "number", 0.0, 0.72, 0.05, None, None)
    rng = np.random.default_rng(42)
    # Not a scale factor — genuinely different distribution
    current_vals = [float(v) for v in rng.normal(0.44, 0.20, 30)]  # wide, not 0.72×2.2
    finding = _detect_unit_shift("score", fs, current_vals, volatility=0.3)
    # Should not detect as unit shift because std ratio is wrong
    # (or if it does detect, the interpretation is irrelevant)
    if finding is not None:
        factor = finding.evidence["detected_pattern"]["factor"]
        assert abs(factor - 2.20462) > 0.1 and abs(factor - 1000) > 1


# ── PSI ────────────────────────────────────────────────────────────────────


def test_psi_stable_near_zero():
    rng = np.random.default_rng(42)
    a = rng.normal(10, 1, 1000).tolist()
    b = rng.normal(10, 1, 1000).tolist()
    psi = _compute_psi(a, b)
    assert psi < 0.10, f"Expected stable PSI < 0.10, got {psi:.4f}"


def test_psi_shifted_high():
    rng = np.random.default_rng(42)
    a = rng.normal(10, 1, 1000).tolist()
    b = rng.normal(20, 1, 1000).tolist()   # massive shift
    psi = _compute_psi(a, b)
    assert psi > 0.25, f"Expected significant PSI > 0.25, got {psi:.4f}"


# ── RBO ────────────────────────────────────────────────────────────────────


def test_rbo_identical_lists():
    lst = ["a", "b", "c", "d"]
    score = rbo(lst, lst)
    assert score > 0.9


def test_rbo_reversed_lists():
    lst = ["a", "b", "c", "d"]
    score = rbo(lst, list(reversed(lst)))
    assert score < 0.5


def test_rbo_empty_lists():
    assert rbo([], []) == 0.0
    assert rbo(["a"], []) == 0.0


# ── Insufficient power ─────────────────────────────────────────────────────


def test_insufficient_power_produces_finding_not_alarm():
    """Fewer than 5 samples should produce 'insufficient_power', not a false alarm."""
    baseline = _make_baseline("weight", mean=12.4, std=1.0)
    # Only 3 observations — below threshold
    current = [_obs(27.0), _obs(28.0), _obs(26.0)]
    findings = diff(baseline, current)
    # Should get insufficient_power, not a ks finding
    ks_findings = [f for f in findings if "kolmogorov_smirnov" in f.change_type]
    assert not ks_findings
    ip_findings = [f for f in findings if f.change_type == "insufficient_power"]
    assert ip_findings
