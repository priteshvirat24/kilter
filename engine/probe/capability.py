"""
engine/probe/capability.py — Capability snapshot: tools/list, resources/list, prompts/list.

Produces a CapabilitySnapshot that is stored in the capability_snapshots table.
Pure data extraction — no diffing, no DB writes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from mcp import ClientSession


@dataclass(frozen=True)
class CapabilitySnapshot:
    protocol_revision: str | None
    tools: list[dict[str, Any]]
    resources: list[dict[str, Any]] | None
    prompts: list[dict[str, Any]] | None
    content_hash: str                      # sha256 of canonicalized tools payload


async def snapshot_capabilities(session: ClientSession) -> CapabilitySnapshot:
    """Snapshot all advertised capabilities from a connected MCP session."""

    # tools/list
    tools_result = await session.list_tools()
    tools = [_tool_to_dict(t) for t in (tools_result.tools or [])]

    # resources/list (may not be supported)
    resources: list[dict[str, Any]] | None = None
    try:
        resources_result = await session.list_resources()
        resources = [_resource_to_dict(r) for r in (resources_result.resources or [])]
    except Exception:
        # Server doesn't implement resources — not an error
        pass

    # prompts/list (may not be supported)
    prompts: list[dict[str, Any]] | None = None
    try:
        prompts_result = await session.list_prompts()
        prompts = [_prompt_to_dict(p) for p in (prompts_result.prompts or [])]
    except Exception:
        # Server doesn't implement prompts — not an error
        pass

    content_hash = _hash_tools(tools)

    return CapabilitySnapshot(
        protocol_revision=None,  # negotiated by client.py and passed separately
        tools=tools,
        resources=resources,
        prompts=prompts,
        content_hash=content_hash,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Serialization helpers — convert MCP SDK objects to plain dicts
# ─────────────────────────────────────────────────────────────────────────────


def _tool_to_dict(tool: Any) -> dict[str, Any]:
    return {
        "name": tool.name,
        "description": tool.description or "",
        "inputSchema": tool.inputSchema if hasattr(tool, "inputSchema") else {},
    }


def _resource_to_dict(resource: Any) -> dict[str, Any]:
    d: dict[str, Any] = {
        "uri": str(resource.uri) if hasattr(resource, "uri") else "",
        "name": resource.name or "",
    }
    if hasattr(resource, "description") and resource.description:
        d["description"] = resource.description
    if hasattr(resource, "mimeType") and resource.mimeType:
        d["mimeType"] = resource.mimeType
    return d


def _prompt_to_dict(prompt: Any) -> dict[str, Any]:
    d: dict[str, Any] = {
        "name": prompt.name,
    }
    if hasattr(prompt, "description") and prompt.description:
        d["description"] = prompt.description
    if hasattr(prompt, "arguments") and prompt.arguments:
        d["arguments"] = [
            {"name": a.name, "description": a.description or "", "required": a.required or False}
            for a in prompt.arguments
        ]
    return d


def _hash_tools(tools: list[dict[str, Any]]) -> str:
    """Canonical SHA-256 of the tools list (sorted by name, keys sorted)."""
    canonical = json.dumps(
        sorted(tools, key=lambda t: t["name"]),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode()).hexdigest()
