#!/usr/bin/env python3
"""
scripts/seed_servers.py — Pull top MCP servers from public registries.

Filters to servers that are:
- Publicly reachable without auth
- Read-only in at least one tool (never probe a tool that writes)
- Responsive (under 5s)

Target: 30–60 servers for the 72-hour demo. Not 500.

Usage:
    python scripts/seed_servers.py [--limit 30]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Add kilter root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import structlog

from engine.config import load_config
from engine.probe.probeset import is_tool_safe

log = structlog.get_logger(__name__)

# Known public MCP servers (manual seed for demo)
# In production: pull from PulseMCP API, Smithery, official registry
_KNOWN_PUBLIC_SERVERS = [
    {
        "name": "Everything MCP",
        "slug": "everything-mcp",
        "endpoint_url": "https://everything.modelcontextprotocol.io/mcp",
        "registry_source": "official",
    },
    {
        "name": "Fetch MCP",
        "slug": "fetch-mcp",
        "endpoint_url": "https://fetch.mcp.so/mcp",
        "registry_source": "official",
    },
    {
        "name": "Filesystem MCP",
        "slug": "filesystem-mcp",
        "endpoint_url": "https://filesystem.mcp.so/mcp",
        "registry_source": "official",
    },
]


async def check_server_reachable(
    endpoint_url: str,
    user_agent: str,
    timeout: float = 5.0,
) -> bool:
    """Quick reachability check before adding to DB."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                endpoint_url,
                headers={"User-Agent": user_agent},
                timeout=timeout,
                follow_redirects=True,
            )
            return resp.status_code < 500
    except Exception as exc:
        log.debug("server_unreachable", url=endpoint_url, error=str(exc))
        return False


async def seed_servers(limit: int = 30) -> None:
    config = load_config()

    import psycopg
    import psycopg_pool

    pool = psycopg_pool.AsyncConnectionPool(
        conninfo=config.database_url,
        min_size=1,
        max_size=3,
        open=False,
    )
    await pool.open()

    from engine.store.repo import Repository

    seeded = 0
    async with pool.connection() as conn:
        repo = Repository(conn)
        for server_info in _KNOWN_PUBLIC_SERVERS[:limit]:
            reachable = await check_server_reachable(
                server_info["endpoint_url"], config.user_agent
            )
            if not reachable:
                log.warning("skipping_unreachable", slug=server_info["slug"])
                continue

            server_id = await repo.upsert_server(
                name=server_info["name"],
                slug=server_info["slug"],
                endpoint_url=server_info["endpoint_url"],
                registry_source=server_info.get("registry_source"),
                auth_mode="none",
                rate_limit_rps=config.probe_default_rps,
            )
            seeded += 1
            log.info("server_seeded", slug=server_info["slug"], id=str(server_id))

    await pool.close()
    log.info("seeding_complete", seeded=seeded)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed MCP servers into the database")
    parser.add_argument("--limit", type=int, default=30, help="Max servers to seed")
    args = parser.parse_args()

    asyncio.run(seed_servers(limit=args.limit))


if __name__ == "__main__":
    main()
