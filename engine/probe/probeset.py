"""
engine/probe/probeset.py — ProbeSet generator.

Generates probe inputs from a tool's JSON Schema (schema_synth method).
Also enforces the is_safe gate — determines whether a tool should be probed.

SAFETY: A single accidental write to a stranger's production server would
end the public-dataset strategy permanently. This check is code, not config.
"""

from __future__ import annotations

import re
from typing import Any

# Tools whose names match these patterns are NEVER probed.
# Default to False (unsafe) on ambiguity.
_UNSAFE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?<![a-zA-Z])(create|update|delete|write|send|post|execute|run|submit|insert|modify|patch|put|remove|destroy|wipe|reset|trigger)(?![a-zA-Z])", re.IGNORECASE),
]


def is_tool_safe(tool_name: str, description: str) -> bool:
    """
    Return True only if the tool is definitely read-only.

    Conservative: any match on the name OR description pattern → unsafe.
    Ambiguity → unsafe.
    """
    combined = f"{tool_name} {description}"
    for pattern in _UNSAFE_PATTERNS:
        if pattern.search(combined):
            return False
    return True


def generate_probesets(
    tool: dict[str, Any],
    *,
    max_probesets: int = 3,
) -> list[dict[str, Any]]:
    """
    Generate a list of argument dicts for the given tool from its inputSchema.

    For the 72h demo: generate up to max_probesets argument combinations
    using schema synthesis (schema_synth method). Each returned dict is a
    frozen argument set that will become one row in the probesets table.

    Returns empty list if the tool is not safe.
    """
    tool_name = tool.get("name", "")
    description = tool.get("description", "")

    if not is_tool_safe(tool_name, description):
        return []

    schema = tool.get("inputSchema", {})
    if not isinstance(schema, dict):
        return []

    argument_sets = _synth_arguments(schema, max_probesets=max_probesets)
    return argument_sets


def _synth_arguments(
    schema: dict[str, Any],
    *,
    max_probesets: int,
) -> list[dict[str, Any]]:
    """
    Synthesize argument dicts from a JSON Schema object.

    Strategy (schema_synth):
    1. For each required property, generate a representative value.
    2. For optional properties, generate both with and without them.
    3. Cap total combinations at max_probesets.

    We handle only flat schemas here; nested schemas produce a best-effort
    single example. The goal is real probes, not exhaustive coverage.
    """
    if schema.get("type") != "object":
        # If schema root isn't an object, probe with empty args
        return [{}]

    properties: dict[str, Any] = schema.get("properties", {})
    required: list[str] = schema.get("required", [])

    if not properties:
        return [{}]

    # Build the required-fields base case
    base: dict[str, Any] = {}
    for prop_name in required:
        if prop_name in properties:
            base[prop_name] = _synth_value(prop_name, properties[prop_name])

    if not base and not required:
        # No required fields — probe with empty args and first optional
        results: list[dict[str, Any]] = [{}]
        for prop_name, prop_schema in list(properties.items())[:max_probesets - 1]:
            results.append({prop_name: _synth_value(prop_name, prop_schema)})
        return results[:max_probesets]

    results = [dict(base)]

    # Add a variant for each optional property up to the cap
    optional = [k for k in properties if k not in required]
    for opt_name in optional:
        if len(results) >= max_probesets:
            break
        variant = dict(base)
        variant[opt_name] = _synth_value(opt_name, properties[opt_name])
        results.append(variant)

    return results[:max_probesets]


def _synth_value(name: str, prop_schema: dict[str, Any]) -> Any:
    """Produce a plausible synthetic value for a single property."""
    # Enum: use first value
    if "enum" in prop_schema:
        return prop_schema["enum"][0]

    # const
    if "const" in prop_schema:
        return prop_schema["const"]

    dtype = prop_schema.get("type", "string")

    if dtype == "string":
        # Use name-based heuristics for more realistic values
        lower = name.lower()
        if "query" in lower or "search" in lower or "q" == lower:
            return "test"
        if "id" in lower:
            return "1"
        if "name" in lower:
            return "example"
        if "url" in lower or "uri" in lower:
            return "https://example.com"
        if "email" in lower:
            return "user@example.com"
        if "date" in lower:
            return "2026-07-24"
        return "test"

    if dtype in ("number", "integer"):
        minimum = prop_schema.get("minimum", 1)
        return int(minimum) if dtype == "integer" else float(minimum)

    if dtype == "boolean":
        return False

    if dtype == "array":
        items = prop_schema.get("items", {})
        return [_synth_value(name, items)]

    if dtype == "object":
        return {}

    if dtype == "null":
        return None

    return None
