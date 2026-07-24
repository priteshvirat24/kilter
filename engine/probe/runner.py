"""
engine/probe/runner.py — Executes ProbeSets, N samples per run.

Hard safety gate: probesets.is_safe must be True before execution.
This is a code check, not a config flag. One accidental write to a
stranger's production server ends the public-dataset strategy permanently.

Rate limiting: ≤ 0.2 rps per server (configurable per server row).
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import structlog
from mcp.types import CallToolResult

from engine.diff.l1_structural import extract_shape_fingerprint
from engine.probe.capability import CapabilitySnapshot, snapshot_capabilities
from engine.probe.client import mcp_session
from engine.probe.probeset import is_tool_safe
from engine.store.models import ProbesetRow, ServerRow
from engine.store.repo import Repository

log = structlog.get_logger(__name__)

# Hard maximum RPS cap — never exceeded regardless of server configuration
_HARD_MAX_RPS = 1.0


async def run_probe_cycle(
    server: ServerRow,
    probesets: list[ProbesetRow],
    repo: Repository,
    *,
    n_samples: int,
    user_agent: str,
) -> tuple[UUID, CapabilitySnapshot | None]:
    """
    Execute one complete probe cycle for a server.

    Returns (run_id, capability_snapshot).
    The capability_snapshot is None if the server was unreachable.

    Steps:
    1. Connect to the MCP server.
    2. Snapshot capabilities (store in capability_snapshots).
    3. For each is_safe probeset, call the tool n_samples times.
    4. Store each result as an observation.
    5. Update servers.last_probed_at.
    """
    run_id = uuid4()
    rps = min(float(server.rate_limit_rps), _HARD_MAX_RPS)
    min_interval = 1.0 / rps  # seconds between calls

    log.info("probe_cycle_start", server=server.slug, run_id=str(run_id), n_samples=n_samples)

    try:
        async with mcp_session(server.endpoint_url, user_agent=user_agent) as (session, protocol_revision):
            # Snapshot capabilities
            cap_snapshot = await snapshot_capabilities(session)

            snapshot_id = await repo.insert_capability_snapshot(
                server_id=server.id,
                protocol_revision=protocol_revision,
                tools=cap_snapshot.tools,
                resources=cap_snapshot.resources,
                prompts=cap_snapshot.prompts,
                content_hash=cap_snapshot.content_hash,
            )

            # Execute probesets
            for ps in probesets:
                # HARD SAFETY GATE — code, not config
                if not ps.is_safe:
                    log.warning("probeset_skipped_unsafe", probeset_id=str(ps.id), tool=ps.tool_name)
                    continue

                # Double-check with the live tool description from the snapshot
                tool_info = next(
                    (t for t in cap_snapshot.tools if t["name"] == ps.tool_name), None
                )
                if tool_info is None:
                    log.info("tool_not_found_in_snapshot", tool=ps.tool_name, server=server.slug)
                    continue

                if not is_tool_safe(ps.tool_name, tool_info.get("description", "")):
                    log.warning(
                        "probeset_skipped_unsafe_description",
                        probeset_id=str(ps.id),
                        tool=ps.tool_name,
                    )
                    continue

                await _execute_probeset_samples(
                    session=session,
                    probeset=ps,
                    run_id=run_id,
                    n_samples=n_samples,
                    min_interval=min_interval,
                    repo=repo,
                )

            await repo.mark_probed(server.id)
            log.info("probe_cycle_complete", server=server.slug, run_id=str(run_id))
            return run_id, cap_snapshot

    except Exception as exc:
        log.warning("probe_cycle_failed", server=server.slug, error=str(exc), run_id=str(run_id))
        return run_id, None


async def _execute_probeset_samples(
    session: Any,
    probeset: ProbesetRow,
    run_id: UUID,
    n_samples: int,
    min_interval: float,
    repo: Repository,
) -> None:
    """Call the tool n_samples times and store each result as an observation."""

    for i in range(n_samples):
        t0 = time.monotonic()
        is_error = False
        error_code: int | None = None
        error_message: str | None = None
        raw_response: dict[str, Any] | None = None

        try:
            result: CallToolResult = await session.call_tool(
                probeset.tool_name,
                arguments=probeset.arguments,
            )

            # Extract the response content as a dict
            if result.content:
                # MCP content is a list of content blocks
                raw_response = _content_to_dict(result.content)

        except Exception as exc:
            is_error = True
            error_message = str(exc)
            # Detect the -32002 → -32602 error code migration
            if hasattr(exc, "code"):
                error_code = exc.code  # type: ignore[attr-defined]

        latency_ms = int((time.monotonic() - t0) * 1000)

        shape_fingerprint = (
            extract_shape_fingerprint(raw_response) if raw_response is not None else None
        )

        await repo.insert_observation(
            probeset_id=probeset.id,
            run_id=run_id,
            sample_index=i,
            latency_ms=latency_ms,
            is_error=is_error,
            error_code=error_code,
            error_message=error_message,
            raw_response=raw_response,
            shape_fingerprint=shape_fingerprint,
            text_embedding=None,  # L3 embeddings computed separately by l3_semantic.py
        )

        # Rate limit: wait before next call
        if i < n_samples - 1:
            elapsed = time.monotonic() - t0
            wait = max(0.0, min_interval - elapsed)
            if wait > 0:
                await asyncio.sleep(wait)


def _content_to_dict(content: list[Any]) -> dict[str, Any]:
    """Convert MCP tool response content blocks to a plain dict for storage."""
    if not content:
        return {}

    # If a single text block with JSON, parse it
    if len(content) == 1 and hasattr(content[0], "text"):
        import json
        text = content[0].text or ""
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        return {"text": text}

    # Multiple content blocks: collect as list
    blocks = []
    for block in content:
        if hasattr(block, "text"):
            blocks.append({"type": "text", "text": block.text})
        elif hasattr(block, "data"):
            blocks.append({"type": "image", "mimeType": getattr(block, "mimeType", "")})
        else:
            blocks.append({"type": "unknown"})

    return {"content": blocks}
