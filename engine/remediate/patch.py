"""
engine/remediate/patch.py — Generates the unified diff patch for drift events.

Template-driven. No ML. Three strategies defined; only SHIM is built for the demo.
(Pin and call_site are described as roadmap per 02-drift-engine-spec.md.)

Shim strategy handles:
- unit_shift: generates an adapter function that converts back to expected units
- field_renamed: generates a translation layer for the renamed field

For BREAKING events only (per spec).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.diff.types import DriftFinding


@dataclass(frozen=True)
class PatchResult:
    strategy: str
    language: str
    patch_diff: str
    explanation: str


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────


def generate_patch(finding: DriftFinding) -> PatchResult | None:
    """
    Generate a remediation patch for a BREAKING drift finding.

    Returns None if no patch strategy applies.
    Only BREAKING findings trigger remediation (per spec).
    """
    if finding.severity != "breaking":
        return None

    if finding.change_type == "unit_shift":
        return _shim_unit_shift(finding)

    if finding.change_type in ("input_field_removed", "field_type_changed", "field_removed"):
        return _shim_field_rename_or_removal(finding)

    # Other BREAKING types (tool_removed, required_field_added, etc.)
    # produce a pin patch pointing to the last known-good version
    return _pin_stub(finding)


# ─────────────────────────────────────────────────────────────────────────────
# Shim strategy — unit shift
# ─────────────────────────────────────────────────────────────────────────────


def _shim_unit_shift(finding: DriftFinding) -> PatchResult:
    """Generate a Python shim adapter that converts the shifted unit back."""
    evidence = finding.evidence
    pattern = evidence.get("detected_pattern", {})
    factor = pattern.get("factor", 1.0)
    interpretation = pattern.get("interpretation", "unknown unit change")
    field_path = finding.field_path or "unknown_field"
    inverse = 1.0 / factor if factor != 0 else 1.0

    # Derive a simple field name from the path (strip array notation)
    field_name = field_path.split(".")[-1].replace("[*]", "").strip()
    field_name_safe = field_name if field_name.isidentifier() else "value"

    # The module name the shim goes into is a placeholder — real implementation
    # would locate the actual call site in the customer repo
    module_path = "agents/tools/adapter.py"

    explanation = (
        f"The `{field_name}` field appears to have changed units "
        f"({interpretation}). This shim adapter converts responses back to the "
        f"units your code expects, so no call sites need to change. "
        f"Remove this adapter once the upstream server is corrected."
    )

    patch = _build_unit_shift_patch(
        module_path=module_path,
        field_name=field_name,
        field_safe=field_name_safe,
        field_path=field_path,
        factor=inverse,
        interpretation=interpretation,
        drift_event_comment=f"Drift event: {finding.change_type} on {field_path}",
    )

    return PatchResult(
        strategy="shim",
        language="python",
        patch_diff=patch,
        explanation=explanation,
    )


def _build_unit_shift_patch(
    module_path: str,
    field_name: str,
    field_safe: str,
    field_path: str,
    factor: float,
    interpretation: str,
    drift_event_comment: str,
) -> str:
    """Build a unified diff string for a unit-shift shim."""
    factor_str = f"{factor:.8g}"
    constant_name = f"_{field_name.upper()}_CONVERSION_FACTOR"

    return f"""--- a/{module_path}
+++ b/{module_path}
@@ -1,4 +1,30 @@
+# {drift_event_comment}
+# Upstream unit change detected: {interpretation}
+# This shim will be removed when the upstream server is corrected.
+
+{constant_name} = {factor_str}
+
+
+def _normalize_{field_safe}_units(response: dict) -> dict:
+    \"\"\"Convert {field_name} field back to expected units.
+
+    Upstream change: {interpretation}
+    Conversion factor: {factor_str} (inverse of shift)
+    \"\"\"
+    # Handle both top-level and nested field paths
+    if "{field_name}" in response:
+        response["{field_name}"] = response["{field_name}"] * {constant_name}
+    # Handle array results
+    for result in response.get("results", []):
+        if "{field_name}" in result:
+            result["{field_name}"] = result["{field_name}"] * {constant_name}
+    return response
+
+
 def call_tool(tool_name: str, arguments: dict) -> dict:
     response = _raw_call(tool_name, arguments)
-    return response
+    # Apply unit normalization for affected tool fields
+    return _normalize_{field_safe}_units(response)
"""


# ─────────────────────────────────────────────────────────────────────────────
# Shim strategy — field rename / removal
# ─────────────────────────────────────────────────────────────────────────────


def _shim_field_rename_or_removal(finding: DriftFinding) -> PatchResult:
    """Generate a shim that re-adds a removed/renamed field for backwards compatibility."""
    field_path = finding.field_path or "unknown_field"
    field_name = field_path.split(".")[-1].replace("[*]", "").strip()
    field_safe = field_name if field_name.isidentifier() else "field"
    module_path = "agents/tools/adapter.py"

    explanation = (
        f"The field `{field_name}` has changed. This shim restores backwards compatibility "
        f"by translating the new response shape to the old one, so existing code keeps working."
    )

    patch = f"""--- a/{module_path}
+++ b/{module_path}
@@ -1,4 +1,18 @@
+# Drift remediation: field change detected on '{field_path}'
+# Change type: {finding.change_type}
+
+
+def _normalize_{field_safe}(response: dict) -> dict:
+    \"\"\"Restore backwards compatibility for '{field_name}' field.
+
+    Applied automatically by the shim until the call sites are updated.
+    \"\"\"
+    # TODO: update the field mapping below to match the new field name
+    # from the current capability snapshot
+    if "{field_name}" not in response:
+        response["{field_name}"] = response.get("REPLACE_WITH_NEW_FIELD_NAME")
+    return response
+
+
 def call_tool(tool_name: str, arguments: dict) -> dict:
     response = _raw_call(tool_name, arguments)
-    return response
+    return _normalize_{field_safe}(response)
"""

    return PatchResult(
        strategy="shim",
        language="python",
        patch_diff=patch,
        explanation=explanation,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pin stub — points to last known-good version
# ─────────────────────────────="────────────────────────────────────────────────
#
# Note: Full "pin" implementation requires knowing the server's version handle,
# which is roadmap (week 3). This produces a documented placeholder.
# ─────────────────────────────────────────────────────────────────────────────


def _pin_stub(finding: DriftFinding) -> PatchResult:
    explanation = (
        f"A breaking change was detected: {finding.change_type}. "
        f"The recommended remediation is to pin to the last known-good server version "
        f"until the change can be handled gracefully. "
        f"Full pin generation requires the server's version handle — see roadmap."
    )

    patch = f"""--- a/mcp_config.py
+++ b/mcp_config.py
@@ -1,6 +1,12 @@
+# Drift remediation: {finding.change_type}
+# Detected: {finding.title}
+# Action: Pin to last known-good configuration
+
 MCP_SERVERS = {{
     "server": {{
         "url": "https://example-mcp-server.com",
-        "version": "latest",
+        # Pinned due to breaking change: {finding.change_type}
+        # Replace this comment with the exact version handle once identified.
+        "version": "PINNED_TO_LAST_GOOD",
+        "pin_reason": "{finding.title}",
     }}
 }}
"""

    return PatchResult(
        strategy="pin",
        language="python",
        patch_diff=patch,
        explanation=explanation,
    )
