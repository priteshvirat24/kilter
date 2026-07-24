"""
tests/test_api_fixtures.py — API fixture smoke tests.

Validates that all fixture JSON files:
1. Exist and parse as valid JSON
2. Conform to the Pydantic response models exactly

These tests run without a database. KILTER_FIXTURES=1 implied.
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from api.schemas import (
    DriftFeedResponse,
    EvidenceResponse,
    RemediationResponse,
    ServersResponse,
    ServerDetailResponse,
    StatsResponse,
    TimelineResponse,
)

FIXTURES = Path(__file__).parent.parent / "api" / "fixtures"


def load(name: str) -> dict:
    with open(FIXTURES / name) as f:
        return json.load(f)


def test_servers_fixture_valid():
    data = load("servers.json")
    response = ServersResponse(**data)
    assert response.total > 0
    assert len(response.servers) > 0


def test_server_detail_fixture_valid():
    data = load("server_detail.json")
    response = ServerDetailResponse(**data)
    assert response.name
    assert len(response.tools) > 0


def test_timeline_fixture_valid():
    data = load("timeline.json")
    response = TimelineResponse(**data)
    assert len(response.field_series) > 0
    for series in response.field_series:
        assert len(series.points) > 0
        assert series.nominal > 0


def test_drift_fixture_valid():
    data = load("drift.json")
    response = DriftFeedResponse(**data)
    assert len(response.events) > 0
    for event in response.events:
        assert event.severity in ("cosmetic", "behavioral", "breaking")
        assert event.layer in ("l0_capability", "l1_structural", "l2_statistical", "l3_semantic")


def test_evidence_fixture_valid():
    data = load("evidence.json")
    response = EvidenceResponse(**data)
    assert response.confidence is not None
    ev = response.evidence
    # Evidence must have all required keys per 03-data-model.md
    assert "layer" in ev
    assert "test" in ev
    assert "plain_english" in ev
    assert "baseline" in ev
    assert "current" in ev
    assert "detected_pattern" in ev


def test_remediation_fixture_valid():
    data = load("remediation.json")
    response = RemediationResponse(**data)
    assert response.patch_diff.startswith("---")
    assert "+++" in response.patch_diff
    assert response.strategy in ("shim", "pin", "call_site")


def test_stats_fixture_valid():
    data = load("stats.json")
    response = StatsResponse(**data)
    assert response.servers_monitored > 0
    assert response.probe_runs_total > 0


def test_fixtures_have_correct_severity_values():
    """Only valid severity values appear in drift fixture."""
    data = load("drift.json")
    valid = {"cosmetic", "behavioral", "breaking"}
    for event in data["events"]:
        assert event["severity"] in valid, f"Bad severity: {event['severity']}"


def test_breaking_events_have_higher_confidence():
    """Breaking events should have confidence ≥ 0.85."""
    data = load("drift.json")
    for event in data["events"]:
        if event["severity"] == "breaking" and event["confidence"] is not None:
            assert event["confidence"] >= 0.85, (
                f"Breaking event {event['id']} has low confidence {event['confidence']}"
            )
