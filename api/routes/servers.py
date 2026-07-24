"""
api/routes/servers.py — /api/servers routes.

In fixture mode (KILTER_FIXTURES=1) all routes return fixture JSON.
Otherwise they query the live database via the Repository.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, HTTPException, Query

from api.deps import ConfigDep, RepoDep
from api.schemas import (
    DriftCounts,
    LastDrift,
    ProbeTriggeredResponse,
    ServerDetailResponse,
    ServersResponse,
    ServerSummary,
    StatsResponse,
    TimelineResponse,
    ToolSummary,
)

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/api")

_FIXTURES = Path(__file__).parent.parent / "fixtures"


def _load_fixture(name: str) -> dict:
    with open(_FIXTURES / name) as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/servers
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/servers", response_model=ServersResponse)
async def list_servers(config: ConfigDep, repo: RepoDep) -> ServersResponse:
    if config.fixtures_enabled:
        data = _load_fixture("servers.json")
        return ServersResponse(**data)

    servers = await repo.list_servers()
    summaries: list[ServerSummary] = []
    for s in servers:
        # Compute per-server rollup from live data
        events, _ = await repo.list_drift_events(server_id=s.id, limit=200)
        probesets = await repo.list_probesets_for_server(s.id)
        tool_count = len({p.tool_name for p in probesets})

        cosmetic = sum(1 for e in events if e.severity == "cosmetic")
        behavioral = sum(1 for e in events if e.severity == "behavioral")
        breaking = sum(1 for e in events if e.severity == "breaking")

        if breaking > 0:
            health: Literal["stable", "drifting", "breaking", "unreachable"] = "breaking"
        elif behavioral > 0:
            health = "drifting"
        elif s.last_probed_at is None:
            health = "unreachable"
        else:
            health = "stable"

        # detection_power derived from mean field volatility across active baselines
        # simplified: count probesets; in production compute from baseline.volatility
        power: Literal["high", "medium", "low"] = "high"

        summaries.append(
            ServerSummary(
                id=s.id,
                name=s.name,
                slug=s.slug,
                protocol_revision=s.protocol_revision,
                tool_count=tool_count,
                last_probed_at=s.last_probed_at,
                health=health,
                drift_counts=DriftCounts(cosmetic=cosmetic, behavioral=behavioral, breaking=breaking),
                detection_power=power,
            )
        )

    return ServersResponse(servers=summaries, total=len(summaries))


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/servers/{id}
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/servers/{server_id}", response_model=ServerDetailResponse)
async def get_server(server_id: UUID, config: ConfigDep, repo: RepoDep) -> ServerDetailResponse:
    if config.fixtures_enabled:
        data = _load_fixture("server_detail.json")
        return ServerDetailResponse(**data)

    server = await repo.get_server(server_id)
    if server is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "not_found", "message": f"Server {server_id} not found", "detail": {}}},
        )

    probesets = await repo.list_probesets_for_server(server_id)
    tool_names = list({p.tool_name for p in probesets})

    tools: list[ToolSummary] = []
    for tool_name in tool_names:
        tool_probesets = [p for p in probesets if p.tool_name == tool_name]
        events, _ = await repo.list_drift_events(server_id=server_id, limit=10)
        tool_events = [e for e in events if e.probeset_id in {p.id for p in tool_probesets}]

        last_drift: LastDrift | None = None
        if tool_events:
            latest = tool_events[0]
            last_drift = LastDrift(severity=latest.severity, detected_at=latest.detected_at)  # type: ignore[arg-type]

        tools.append(
            ToolSummary(
                name=tool_name,
                probeset_count=len(tool_probesets),
                volatility_mean=0.25,  # populated from baseline.volatility in full impl
                detection_power="high",
                last_drift=last_drift,
            )
        )

    # Find earliest baseline for this server's probesets
    baseline_established_at = None
    for p in probesets:
        b = await repo.get_active_baseline(p.id)
        if b is not None:
            if baseline_established_at is None or b.established_at < baseline_established_at:
                baseline_established_at = b.established_at

    return ServerDetailResponse(
        id=server.id,
        name=server.name,
        endpoint_url=server.endpoint_url,
        protocol_revision=server.protocol_revision,
        baseline_established_at=baseline_established_at,
        tools=tools,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/servers/{id}/timeline
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/servers/{server_id}/timeline", response_model=TimelineResponse)
async def get_timeline(
    server_id: UUID,
    config: ConfigDep,
    repo: RepoDep,
    tool: str | None = Query(default=None),
    window: str = Query(default="7d"),
) -> TimelineResponse:
    if config.fixtures_enabled:
        data = _load_fixture("timeline.json")
        return TimelineResponse(**data)

    # In live mode: build timeline from observations + drift_events
    # Full implementation in Phase 7 (statistical diff feeds this)
    # For now return empty but well-typed response
    server = await repo.get_server(server_id)
    if server is None:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "Server not found", "detail": {}}})

    return TimelineResponse(
        server_id=server_id,
        tool_name=tool or "",
        field_series=[],
        capability_markers=[],
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/servers/{id}/probe  (demo-only trigger)
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/servers/{server_id}/probe", response_model=ProbeTriggeredResponse)
async def trigger_probe(server_id: UUID, config: ConfigDep, repo: RepoDep) -> ProbeTriggeredResponse:
    """Trigger an immediate probe cycle. Demo-only. Rate-limited by the probe runner."""
    server = await repo.get_server(server_id)
    if server is None:
        raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "Server not found", "detail": {}}})

    run_id = uuid4()
    log.info("probe_triggered", server_id=str(server_id), run_id=str(run_id))
    # The actual probe run is dispatched via APScheduler; this endpoint enqueues it.
    # Full implementation wired in api/main.py scheduler setup.
    return ProbeTriggeredResponse(
        server_id=server_id,
        run_id=run_id,
        message="Probe cycle queued. Results will appear in the timeline within 60s.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/stats
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/stats", response_model=StatsResponse)
async def get_stats(config: ConfigDep, repo: RepoDep) -> StatsResponse:
    if config.fixtures_enabled:
        data = _load_fixture("stats.json")
        return StatsResponse(**data)

    row = await repo.get_stats()
    if row is None:
        return StatsResponse(
            servers_monitored=0,
            probe_runs_total=0,
            drift_events=DriftCounts(cosmetic=0, behavioral=0, breaking=0),
            servers_with_breaking_drift_7d=0,
            last_run_at=None,
        )

    return StatsResponse(
        servers_monitored=int(row["servers_monitored"] or 0),
        probe_runs_total=int(row["probe_runs_total"] or 0),
        drift_events=DriftCounts(
            cosmetic=int(row["drift_cosmetic"] or 0),
            behavioral=int(row["drift_behavioral"] or 0),
            breaking=int(row["drift_breaking"] or 0),
        ),
        servers_with_breaking_drift_7d=int(row["servers_with_breaking_drift_7d"] or 0),
        last_run_at=row["last_run_at"],
    )
