"""
engine/store/repo.py — All database access goes through here.

Rules (per spec):
- No other module may import psycopg or execute SQL.
- Uses psycopg3 async connection pool.
- Returns typed dataclass rows (engine/store/models.py), never raw dicts.
- opt_out servers are filtered at the query layer, never in application logic.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import class_row, dict_row

from engine.store.models import (
    BaselineRow,
    CapabilitySnapshotRow,
    DriftEventRow,
    ObservationRow,
    ProbesetRow,
    RemediationRow,
    ServerRow,
)


class Repository:
    """All DB access for Kilter. Instantiated once and passed via dependency injection."""

    def __init__(self, conn: psycopg.AsyncConnection) -> None:
        self._conn = conn

    # ─────────────────────────────────────────────────────────────────────────
    # Servers
    # ─────────────────────────────────────────────────────────────────────────

    async def list_servers(self, *, include_opt_out: bool = False) -> list[ServerRow]:
        """List servers. opt_out=True servers are excluded unless explicitly requested."""
        q = """
            SELECT id, name, slug, endpoint_url, transport, registry_source,
                   protocol_revision, auth_mode, probe_enabled, opt_out,
                   rate_limit_rps::float, first_seen_at, last_probed_at
            FROM servers
            WHERE probe_enabled = true
        """
        params: list[Any] = []
        if not include_opt_out:
            q += " AND opt_out = false"
        q += " ORDER BY name"

        async with self._conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(q, params)
            rows = await cur.fetchall()
        return [_map_server(r) for r in rows]

    async def get_server(self, server_id: UUID) -> ServerRow | None:
        async with self._conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, name, slug, endpoint_url, transport, registry_source,
                       protocol_revision, auth_mode, probe_enabled, opt_out,
                       rate_limit_rps::float, first_seen_at, last_probed_at
                FROM servers WHERE id = %s
                """,
                (server_id,),
            )
            row = await cur.fetchone()
        return _map_server(row) if row else None

    async def get_server_by_slug(self, slug: str) -> ServerRow | None:
        async with self._conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, name, slug, endpoint_url, transport, registry_source,
                       protocol_revision, auth_mode, probe_enabled, opt_out,
                       rate_limit_rps::float, first_seen_at, last_probed_at
                FROM servers WHERE slug = %s
                """,
                (slug,),
            )
            row = await cur.fetchone()
        return _map_server(row) if row else None

    async def upsert_server(
        self,
        *,
        name: str,
        slug: str,
        endpoint_url: str,
        transport: str = "streamable_http",
        registry_source: str | None = None,
        protocol_revision: str | None = None,
        auth_mode: str = "none",
        rate_limit_rps: float = 0.2,
    ) -> UUID:
        async with self._conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO servers (name, slug, endpoint_url, transport,
                    registry_source, protocol_revision, auth_mode, rate_limit_rps)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (slug) DO UPDATE SET
                    name = EXCLUDED.name,
                    endpoint_url = EXCLUDED.endpoint_url,
                    protocol_revision = EXCLUDED.protocol_revision,
                    rate_limit_rps = EXCLUDED.rate_limit_rps
                RETURNING id
                """,
                (
                    name, slug, endpoint_url, transport,
                    registry_source, protocol_revision, auth_mode, rate_limit_rps,
                ),
            )
            row = await cur.fetchone()
        return row[0]  # type: ignore[index]

    async def mark_probed(self, server_id: UUID) -> None:
        async with self._conn.cursor() as cur:
            await cur.execute(
                "UPDATE servers SET last_probed_at = now() WHERE id = %s",
                (server_id,),
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Capability Snapshots
    # ─────────────────────────────────────────────────────────────────────────

    async def insert_capability_snapshot(
        self,
        *,
        server_id: UUID,
        protocol_revision: str | None,
        tools: list[dict[str, Any]],
        resources: list[dict[str, Any]] | None,
        prompts: list[dict[str, Any]] | None,
        content_hash: str,
    ) -> UUID:
        async with self._conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO capability_snapshots
                    (server_id, protocol_revision, tools, resources, prompts, content_hash)
                VALUES (%s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s)
                RETURNING id
                """,
                (
                    server_id,
                    protocol_revision,
                    json.dumps(tools),
                    json.dumps(resources) if resources is not None else None,
                    json.dumps(prompts) if prompts is not None else None,
                    content_hash,
                ),
            )
            row = await cur.fetchone()
        return row[0]  # type: ignore[index]

    async def get_latest_capability_snapshot(
        self, server_id: UUID
    ) -> CapabilitySnapshotRow | None:
        async with self._conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, server_id, captured_at, protocol_revision,
                       tools, resources, prompts, content_hash
                FROM capability_snapshots
                WHERE server_id = %s
                ORDER BY captured_at DESC
                LIMIT 1
                """,
                (server_id,),
            )
            row = await cur.fetchone()
        return _map_capability_snapshot(row) if row else None

    # ─────────────────────────────────────────────────────────────────────────
    # Probesets
    # ─────────────────────────────────────────────────────────────────────────

    async def upsert_probeset(
        self,
        *,
        server_id: UUID,
        tool_name: str,
        arguments: dict[str, Any],
        generation_method: str,
        is_safe: bool,
    ) -> UUID:
        async with self._conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO probesets (server_id, tool_name, arguments, generation_method, is_safe)
                VALUES (%s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (server_id, tool_name, arguments) DO UPDATE SET
                    generation_method = EXCLUDED.generation_method,
                    is_safe = EXCLUDED.is_safe
                RETURNING id
                """,
                (
                    server_id,
                    tool_name,
                    json.dumps(arguments, sort_keys=True),
                    generation_method,
                    is_safe,
                ),
            )
            row = await cur.fetchone()
        return row[0]  # type: ignore[index]

    async def list_probesets_for_server(self, server_id: UUID) -> list[ProbesetRow]:
        async with self._conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, server_id, tool_name, arguments, generation_method, is_safe, created_at
                FROM probesets WHERE server_id = %s AND is_safe = true
                ORDER BY tool_name, created_at
                """,
                (server_id,),
            )
            rows = await cur.fetchall()
        return [_map_probeset(r) for r in rows]

    # ─────────────────────────────────────────────────────────────────────────
    # Observations
    # ─────────────────────────────────────────────────────────────────────────

    async def insert_observation(
        self,
        *,
        probeset_id: UUID,
        run_id: UUID,
        sample_index: int,
        latency_ms: int | None,
        is_error: bool,
        error_code: int | None,
        error_message: str | None,
        raw_response: dict[str, Any] | None,
        shape_fingerprint: dict[str, Any] | None,
        text_embedding: list[float] | None,
    ) -> UUID:
        embedding_literal = (
            json.dumps(text_embedding) if text_embedding is not None else None
        )
        async with self._conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO observations (
                    probeset_id, run_id, sample_index, latency_ms,
                    is_error, error_code, error_message,
                    raw_response, shape_fingerprint, text_embedding
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::vector)
                RETURNING id
                """,
                (
                    probeset_id,
                    run_id,
                    sample_index,
                    latency_ms,
                    is_error,
                    error_code,
                    error_message,
                    json.dumps(raw_response) if raw_response is not None else None,
                    json.dumps(shape_fingerprint) if shape_fingerprint is not None else None,
                    embedding_literal,
                ),
            )
            row = await cur.fetchone()
        return row[0]  # type: ignore[index]

    async def list_observations_for_probeset(
        self,
        probeset_id: UUID,
        *,
        run_id: UUID | None = None,
        limit: int = 200,
    ) -> list[ObservationRow]:
        q = """
            SELECT id, probeset_id, run_id, observed_at, sample_index,
                   latency_ms, is_error, error_code, error_message,
                   raw_response, shape_fingerprint, text_embedding::text
            FROM observations
            WHERE probeset_id = %s
        """
        params: list[Any] = [probeset_id]
        if run_id is not None:
            q += " AND run_id = %s"
            params.append(run_id)
        q += " ORDER BY observed_at DESC LIMIT %s"
        params.append(limit)

        async with self._conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(q, params)
            rows = await cur.fetchall()
        return [_map_observation(r) for r in rows]

    # ─────────────────────────────────────────────────────────────────────────
    # Baselines
    # ─────────────────────────────────────────────────────────────────────────

    async def insert_baseline(
        self,
        *,
        probeset_id: UUID,
        sample_count: int,
        capability_snapshot_id: UUID | None,
        field_stats: dict[str, Any],
        volatility: dict[str, float],
        centroid: list[float] | None,
        centroid_dispersion: float | None,
    ) -> UUID:
        # Deactivate any existing active baseline for this probeset first
        async with self._conn.cursor() as cur:
            await cur.execute(
                "UPDATE baselines SET is_active = false WHERE probeset_id = %s AND is_active = true",
                (probeset_id,),
            )
            centroid_literal = json.dumps(centroid) if centroid is not None else None
            await cur.execute(
                """
                INSERT INTO baselines (
                    probeset_id, sample_count, capability_snapshot_id,
                    field_stats, volatility, centroid, centroid_dispersion, is_active
                )
                VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::vector, %s, true)
                RETURNING id
                """,
                (
                    probeset_id,
                    sample_count,
                    capability_snapshot_id,
                    json.dumps(field_stats),
                    json.dumps(volatility),
                    centroid_literal,
                    centroid_dispersion,
                ),
            )
            row = await cur.fetchone()
        return row[0]  # type: ignore[index]

    async def get_active_baseline(self, probeset_id: UUID) -> BaselineRow | None:
        async with self._conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, probeset_id, established_at, sample_count, capability_snapshot_id,
                       field_stats, volatility, centroid::text, centroid_dispersion::float, is_active
                FROM baselines
                WHERE probeset_id = %s AND is_active = true
                LIMIT 1
                """,
                (probeset_id,),
            )
            row = await cur.fetchone()
        return _map_baseline(row) if row else None

    # ─────────────────────────────────────────────────────────────────────────
    # Drift Events
    # ─────────────────────────────────────────────────────────────────────────

    async def insert_drift_event(
        self,
        *,
        server_id: UUID,
        probeset_id: UUID | None,
        baseline_id: UUID | None,
        run_id: UUID,
        layer: str,
        severity: str,
        change_type: str,
        field_path: str | None,
        title: str,
        evidence: dict[str, Any],
        confidence: float | None,
    ) -> UUID:
        async with self._conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO drift_events (
                    server_id, probeset_id, baseline_id, run_id,
                    layer, severity, change_type, field_path,
                    title, evidence, confidence
                )
                VALUES (%s, %s, %s, %s, %s::drift_layer, %s::drift_severity,
                        %s, %s, %s, %s::jsonb, %s)
                RETURNING id
                """,
                (
                    server_id,
                    probeset_id,
                    baseline_id,
                    run_id,
                    layer,
                    severity,
                    change_type,
                    field_path,
                    title,
                    json.dumps(evidence),
                    confidence,
                ),
            )
            row = await cur.fetchone()
        return row[0]  # type: ignore[index]

    async def list_drift_events(
        self,
        *,
        server_id: UUID | None = None,
        severity: str | None = None,
        since: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[DriftEventRow], str | None]:
        """Paginated drift event feed. Returns (events, next_cursor)."""
        q = """
            SELECT id, server_id, probeset_id, baseline_id, run_id,
                   detected_at, layer, severity, change_type, field_path,
                   title, evidence, confidence::float, acknowledged
            FROM drift_events
            WHERE 1=1
        """
        params: list[Any] = []

        if server_id is not None:
            q += " AND server_id = %s"
            params.append(server_id)
        if severity is not None:
            q += " AND severity = %s::drift_severity"
            params.append(severity)
        if since is not None:
            q += " AND detected_at >= %s"
            params.append(since)
        if cursor is not None:
            q += " AND detected_at < %s"
            params.append(cursor)

        q += " ORDER BY detected_at DESC LIMIT %s"
        params.append(limit + 1)

        async with self._conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(q, params)
            rows = await cur.fetchall()

        next_cursor: str | None = None
        if len(rows) > limit:
            next_cursor = rows[limit]["detected_at"].isoformat()
            rows = rows[:limit]

        return [_map_drift_event(r) for r in rows], next_cursor

    async def get_drift_event(self, event_id: UUID) -> DriftEventRow | None:
        async with self._conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, server_id, probeset_id, baseline_id, run_id,
                       detected_at, layer, severity, change_type, field_path,
                       title, evidence, confidence::float, acknowledged
                FROM drift_events WHERE id = %s
                """,
                (event_id,),
            )
            row = await cur.fetchone()
        return _map_drift_event(row) if row else None

    # ─────────────────────────────────────────────────────────────────────────
    # Remediations
    # ─────────────────────────────────────────────────────────────────────────

    async def insert_remediation(
        self,
        *,
        drift_event_id: UUID,
        strategy: str,
        language: str,
        patch_diff: str,
        explanation: str,
    ) -> UUID:
        async with self._conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO remediations (drift_event_id, strategy, language, patch_diff, explanation)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (drift_event_id, strategy, language, patch_diff, explanation),
            )
            row = await cur.fetchone()
        return row[0]  # type: ignore[index]

    async def get_remediation_for_event(self, drift_event_id: UUID) -> RemediationRow | None:
        async with self._conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, drift_event_id, strategy, language, patch_diff, explanation, created_at
                FROM remediations WHERE drift_event_id = %s
                ORDER BY created_at DESC LIMIT 1
                """,
                (drift_event_id,),
            )
            row = await cur.fetchone()
        return _map_remediation(row) if row else None

    # ─────────────────────────────────────────────────────────────────────────
    # Stats (for /api/stats endpoint)
    # ─────────────────────────────────────────────────────────────────────────

    async def get_stats(self) -> dict[str, Any]:
        async with self._conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM servers WHERE probe_enabled AND NOT opt_out) AS servers_monitored,
                    (SELECT COUNT(DISTINCT run_id) FROM observations) AS probe_runs_total,
                    (SELECT COUNT(*) FROM drift_events WHERE severity = 'cosmetic') AS drift_cosmetic,
                    (SELECT COUNT(*) FROM drift_events WHERE severity = 'behavioral') AS drift_behavioral,
                    (SELECT COUNT(*) FROM drift_events WHERE severity = 'breaking') AS drift_breaking,
                    (SELECT COUNT(DISTINCT server_id) FROM drift_events
                     WHERE severity = 'breaking' AND detected_at >= now() - interval '7 days')
                        AS servers_with_breaking_drift_7d,
                    (SELECT MAX(observed_at) FROM observations) AS last_run_at
                """
            )
            return await cur.fetchone()  # type: ignore[return-value]


# ─────────────────────────────────────────────────────────────────────────────
# Row mappers — psycopg dict_row → typed dataclass
# ─────────────────────────────────────────────────────────────────────────────


def _map_server(r: dict[str, Any]) -> ServerRow:
    return ServerRow(
        id=r["id"],
        name=r["name"],
        slug=r["slug"],
        endpoint_url=r["endpoint_url"],
        transport=r["transport"],
        registry_source=r["registry_source"],
        protocol_revision=r["protocol_revision"],
        auth_mode=r["auth_mode"],
        probe_enabled=r["probe_enabled"],
        opt_out=r["opt_out"],
        rate_limit_rps=float(r["rate_limit_rps"]),
        first_seen_at=r["first_seen_at"],
        last_probed_at=r["last_probed_at"],
    )


def _map_capability_snapshot(r: dict[str, Any]) -> CapabilitySnapshotRow:
    return CapabilitySnapshotRow(
        id=r["id"],
        server_id=r["server_id"],
        captured_at=r["captured_at"],
        protocol_revision=r["protocol_revision"],
        tools=r["tools"] if isinstance(r["tools"], list) else json.loads(r["tools"]),
        resources=(
            r["resources"] if r["resources"] is None or isinstance(r["resources"], list)
            else json.loads(r["resources"])
        ),
        prompts=(
            r["prompts"] if r["prompts"] is None or isinstance(r["prompts"], list)
            else json.loads(r["prompts"])
        ),
        content_hash=r["content_hash"],
    )


def _map_probeset(r: dict[str, Any]) -> ProbesetRow:
    return ProbesetRow(
        id=r["id"],
        server_id=r["server_id"],
        tool_name=r["tool_name"],
        arguments=r["arguments"] if isinstance(r["arguments"], dict) else json.loads(r["arguments"]),
        generation_method=r["generation_method"],
        is_safe=r["is_safe"],
        created_at=r["created_at"],
    )


def _map_observation(r: dict[str, Any]) -> ObservationRow:
    # text_embedding comes back as a string like "[0.1, 0.2, ...]" from ::text cast
    embedding = None
    if r.get("text_embedding") is not None:
        raw = r["text_embedding"]
        if isinstance(raw, str):
            embedding = json.loads(raw)
        elif isinstance(raw, list):
            embedding = raw

    return ObservationRow(
        id=r["id"],
        probeset_id=r["probeset_id"],
        run_id=r["run_id"],
        observed_at=r["observed_at"],
        sample_index=r["sample_index"],
        latency_ms=r["latency_ms"],
        is_error=r["is_error"],
        error_code=r["error_code"],
        error_message=r["error_message"],
        raw_response=(
            r["raw_response"] if isinstance(r["raw_response"], dict)
            else json.loads(r["raw_response"]) if r["raw_response"] else None
        ),
        shape_fingerprint=(
            r["shape_fingerprint"] if isinstance(r["shape_fingerprint"], dict)
            else json.loads(r["shape_fingerprint"]) if r["shape_fingerprint"] else None
        ),
        text_embedding=embedding,
    )


def _map_baseline(r: dict[str, Any]) -> BaselineRow:
    centroid = None
    if r.get("centroid") is not None:
        raw = r["centroid"]
        centroid = json.loads(raw) if isinstance(raw, str) else raw

    return BaselineRow(
        id=r["id"],
        probeset_id=r["probeset_id"],
        established_at=r["established_at"],
        sample_count=r["sample_count"],
        capability_snapshot_id=r["capability_snapshot_id"],
        field_stats=r["field_stats"] if isinstance(r["field_stats"], dict) else json.loads(r["field_stats"]),
        volatility=r["volatility"] if isinstance(r["volatility"], dict) else json.loads(r["volatility"]),
        centroid=centroid,
        centroid_dispersion=r["centroid_dispersion"],
        is_active=r["is_active"],
    )


def _map_drift_event(r: dict[str, Any]) -> DriftEventRow:
    return DriftEventRow(
        id=r["id"],
        server_id=r["server_id"],
        probeset_id=r["probeset_id"],
        baseline_id=r["baseline_id"],
        run_id=r["run_id"],
        detected_at=r["detected_at"],
        layer=r["layer"],
        severity=r["severity"],
        change_type=r["change_type"],
        field_path=r["field_path"],
        title=r["title"],
        evidence=r["evidence"] if isinstance(r["evidence"], dict) else json.loads(r["evidence"]),
        confidence=r["confidence"],
        acknowledged=r["acknowledged"],
    )


def _map_remediation(r: dict[str, Any]) -> RemediationRow:
    return RemediationRow(
        id=r["id"],
        drift_event_id=r["drift_event_id"],
        strategy=r["strategy"],
        language=r["language"],
        patch_diff=r["patch_diff"],
        explanation=r["explanation"],
        created_at=r["created_at"],
    )
