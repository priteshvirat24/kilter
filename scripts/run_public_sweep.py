#!/usr/bin/env python3
"""
scripts/run_public_sweep.py — Run a full probe sweep for the launch dataset.

Produces the public drift record for the top public MCP servers.
This is the launch artifact: simultaneously the demo, the dataset, and the lead list.

Usage:
    python scripts/run_public_sweep.py [--cycles 3]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

import structlog

from engine.config import load_config
from engine.diff import l0_capability, l1_structural, l2_statistical, l3_semantic, severity
from engine.diff.types import Baseline, FieldStats, Observation
from engine.diff.volatility import compute_volatility
from engine.probe.capability import snapshot_capabilities
from engine.probe.client import mcp_session
from engine.probe.probeset import generate_probesets, is_tool_safe
from engine.probe.runner import run_probe_cycle
from engine.remediate.patch import generate_patch

log = structlog.get_logger(__name__)


async def run_sweep(cycles: int = 3) -> None:
    config = load_config()

    import psycopg_pool
    from engine.store.repo import Repository

    pool = psycopg_pool.AsyncConnectionPool(
        conninfo=config.database_url, min_size=1, max_size=5, open=False
    )
    await pool.open()

    async with pool.connection() as conn:
        repo = Repository(conn)
        servers = await repo.list_servers()

        if not servers:
            log.warning("no_servers_found", hint="Run scripts/seed_servers.py first")
            await pool.close()
            return

        log.info("sweep_start", server_count=len(servers), cycles=cycles)

        for server in servers:
            log.info("sweeping_server", slug=server.slug)

            # First: generate probesets from capability snapshot
            try:
                async with mcp_session(server.endpoint_url, user_agent=config.user_agent) as (session, revision):
                    cap = await snapshot_capabilities(session)

                    await repo.insert_capability_snapshot(
                        server_id=server.id,
                        protocol_revision=revision,
                        tools=cap.tools,
                        resources=cap.resources,
                        prompts=cap.prompts,
                        content_hash=cap.content_hash,
                    )

                    for tool in cap.tools:
                        args_sets = generate_probesets(tool, max_probesets=3)
                        for args in args_sets:
                            await repo.upsert_probeset(
                                server_id=server.id,
                                tool_name=tool["name"],
                                arguments=args,
                                generation_method="schema_synth",
                                is_safe=is_tool_safe(tool["name"], tool.get("description", "")),
                            )

            except Exception as exc:
                log.warning("snapshot_failed", slug=server.slug, error=str(exc))
                continue

            # Run probe cycles
            probesets = await repo.list_probesets_for_server(server.id)
            if not probesets:
                log.info("no_probesets", slug=server.slug)
                continue

            for cycle_n in range(cycles):
                run_id, cap_snap = await run_probe_cycle(
                    server=server,
                    probesets=probesets,
                    repo=repo,
                    n_samples=config.probe_n_samples,
                    user_agent=config.user_agent,
                )
                log.info("cycle_complete", slug=server.slug, cycle=cycle_n + 1, run_id=str(run_id))

            log.info("server_sweep_complete", slug=server.slug)

    await pool.close()
    log.info("sweep_complete")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run public MCP server sweep")
    parser.add_argument("--cycles", type=int, default=3, help="Probe cycles per server")
    args = parser.parse_args()
    asyncio.run(run_sweep(cycles=args.cycles))


if __name__ == "__main__":
    main()
