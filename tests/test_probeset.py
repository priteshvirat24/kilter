"""
tests/test_probeset.py — Tests for probe safety gate and probe generation.

The safety gate is code, not config. Every test here protects against
accidentally probing a write tool on a stranger's production server.
"""

import pytest
from engine.probe.probeset import is_tool_safe, generate_probesets


# ── Safety gate ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("tool_name,description", [
    ("create_issue", "Creates a GitHub issue"),
    ("delete_file", "Deletes a file"),
    ("update_record", "Updates a database record"),
    ("send_email", "Sends an email"),
    ("execute_sql", "Executes a SQL query"),
    ("run_script", "Runs a shell script"),
    ("post_message", "Posts a Slack message"),
    ("submit_form", "Submits a web form"),
    ("insert_row", "Inserts a row into the database"),
    ("modify_config", "Modifies server configuration"),
    ("patch_deployment", "Patches a deployment"),
    ("put_object", "Puts an object in S3"),
    ("remove_permission", "Removes a user permission"),
    ("destroy_cluster", "Destroys a Kubernetes cluster"),
    ("wipe_database", "Wipes all data"),
    ("reset_password", "Resets a user password"),
    ("trigger_webhook", "Triggers a webhook"),
])
def test_write_tool_is_unsafe(tool_name: str, description: str):
    assert not is_tool_safe(tool_name, description), \
        f"Expected '{tool_name}' to be unsafe but is_tool_safe returned True"


@pytest.mark.parametrize("tool_name,description", [
    ("search_issues", "Search GitHub issues"),
    ("list_repos", "List repositories"),
    ("get_file", "Get file contents"),
    ("read_config", "Read configuration"),
    ("query_data", "Query data from the database"),
    ("fetch_weather", "Fetch weather data"),
    ("lookup_user", "Look up user information"),
    ("browse_page", "Browse a web page"),
])
def test_read_tool_is_safe(tool_name: str, description: str):
    assert is_tool_safe(tool_name, description), \
        f"Expected '{tool_name}' to be safe but is_tool_safe returned False"


def test_ambiguous_tool_name_defaults_to_unsafe():
    """Tools with ambiguous names default to unsafe."""
    # "update" appears in description — should be unsafe
    assert not is_tool_safe("tool", "Update the record when found")


# ── Probeset generation ────────────────────────────────────────────────────


def test_unsafe_tool_generates_no_probesets():
    tool = {
        "name": "create_file",
        "description": "Creates a file",
        "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    }
    assert generate_probesets(tool) == []


def test_safe_tool_generates_probesets():
    tool = {
        "name": "search_repos",
        "description": "Search GitHub repositories",
        "inputSchema": {
            "type": "object",
            "properties": {"q": {"type": "string"}},
            "required": ["q"],
        },
    }
    probesets = generate_probesets(tool)
    assert len(probesets) >= 1
    for ps in probesets:
        assert isinstance(ps, dict)
        # Required field must be present
        assert "q" in ps


def test_probesets_respect_max_limit():
    tool = {
        "name": "search",
        "description": "Search for data",
        "inputSchema": {
            "type": "object",
            "properties": {f"field_{i}": {"type": "string"} for i in range(20)},
            "required": [],
        },
    }
    probesets = generate_probesets(tool, max_probesets=3)
    assert len(probesets) <= 3


def test_schema_synth_query_field_gets_test_value():
    """'query' field should get a realistic default, not None."""
    tool = {
        "name": "search",
        "description": "Search",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    }
    probesets = generate_probesets(tool)
    assert probesets
    assert probesets[0]["query"] == "test"


def test_enum_property_gets_first_enum_value():
    tool = {
        "name": "filter",
        "description": "Filter data",
        "inputSchema": {
            "type": "object",
            "properties": {"mode": {"type": "string", "enum": ["fast", "slow", "medium"]}},
            "required": ["mode"],
        },
    }
    probesets = generate_probesets(tool)
    assert probesets
    assert probesets[0]["mode"] == "fast"


def test_no_schema_generates_empty_args():
    """A tool with no schema properties should probe with empty args."""
    tool = {
        "name": "ping",
        "description": "Ping the server",
        "inputSchema": {"type": "object"},
    }
    probesets = generate_probesets(tool)
    assert probesets == [{}]
