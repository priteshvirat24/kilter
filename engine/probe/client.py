"""
engine/probe/client.py — MCP connection and version negotiation.

Connects to a single MCP server over Streamable HTTP, negotiates protocol
version, and returns a ready ClientSession.

Pin: mcp>=1.27,<2
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
import structlog
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

log = structlog.get_logger(__name__)

# Timeout for the initial connection + capability snapshot (seconds)
_CONNECT_TIMEOUT = 10.0
# Read timeout per individual tool call (seconds)
_READ_TIMEOUT = 15.0


@asynccontextmanager
async def mcp_session(
    endpoint_url: str,
    *,
    user_agent: str,
    timeout: float = _CONNECT_TIMEOUT,
) -> AsyncGenerator[tuple[ClientSession, str | None], None]:
    """
    Async context manager yielding (ClientSession, negotiated_protocol_revision).

    Usage:
        async with mcp_session(url, user_agent=ua) as (session, revision):
            snapshot = await snapshot_capabilities(session)

    Raises httpx.ConnectError / httpx.TimeoutException on unreachable servers.
    Never suppresses exceptions — callers decide how to handle them.
    """
    headers = {
        "User-Agent": user_agent,
        "Accept": "application/json, text/event-stream",
    }

    async with streamablehttp_client(
        endpoint_url,
        headers=headers,
        timeout=httpx.Timeout(timeout, read=_READ_TIMEOUT),
    ) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            init_result = await session.initialize()

            # The protocol revision is in the server info returned by initialize()
            protocol_revision: str | None = None
            if hasattr(init_result, "protocolVersion"):
                protocol_revision = init_result.protocolVersion
            elif hasattr(init_result, "protocol_version"):
                protocol_revision = init_result.protocol_version

            log.debug(
                "mcp_connected",
                endpoint_url=endpoint_url,
                protocol_revision=protocol_revision,
            )
            yield session, protocol_revision
