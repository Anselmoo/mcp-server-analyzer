"""FastMCP in-process E2E tests using Client(mcp) transport."""

import json

import pytest
import pytest_asyncio
from fastmcp import Client
from fastmcp.exceptions import ToolError

from mcp_server_analyzer import server
from mcp_server_analyzer.server import mcp


@pytest_asyncio.fixture
async def client():
    async with Client(mcp) as c:
        yield c


@pytest.mark.asyncio
async def test_list_tools(client):
    tools = await client.list_tools()
    tool_names = {t.name for t in tools}
    expected = {
        "ruff-check",
        "ruff-format",
        "ruff-check-ci",
        "ty-check",
        "vulture-scan",
        "biome-check",
        "biome-format",
        "analyze-code",
    }
    assert expected == tool_names


@pytest.mark.asyncio
async def test_list_resources(client):
    resources = await client.list_resources()
    uris = {str(r.uri) for r in resources}
    assert "docs://analyzers/overview" in uris
    assert "config://analyzer-versions" in uris


@pytest.mark.asyncio
async def test_ruff_check_clean_code(client):
    result = await client.call_tool("ruff-check", {"code": "pass\n"})
    assert not result.is_error
    parsed = result.structured_content
    assert "total_issues" in parsed
    assert "issues" in parsed
    # Verify no error-severity issues on clean code (INP001 is info-level and may fire)
    error_issues = [i for i in parsed["issues"] if i["severity"] == "error"]
    assert len(error_issues) == 0


@pytest.mark.asyncio
async def test_ruff_check_with_issues(client):
    code = "import os\n"
    result = await client.call_tool("ruff-check", {"code": code})
    assert not result.is_error
    parsed = result.structured_content
    assert parsed["total_issues"] >= 1
    assert len(parsed["issues"]) >= 1


@pytest.mark.asyncio
async def test_ruff_format_normalizes_code(client):
    code = "x=1\n"
    result = await client.call_tool("ruff-format", {"code": code})
    assert not result.is_error
    parsed = result.structured_content
    assert isinstance(parsed["changed"], bool)
    assert "formatted_code" in parsed


@pytest.mark.asyncio
async def test_ruff_check_ci_json_format(client):
    result = await client.call_tool(
        "ruff-check-ci", {"code": "x = 1\n", "output_format": "json"}
    )
    assert not result.is_error
    parsed = result.structured_content
    assert parsed["success"] is True
    assert parsed["format"] == "json"


@pytest.mark.asyncio
async def test_ruff_check_ci_github_format(client):
    result = await client.call_tool(
        "ruff-check-ci", {"code": "x = 1\n", "output_format": "github"}
    )
    assert not result.is_error
    parsed = result.structured_content
    assert parsed["success"] is True


@pytest.mark.asyncio
async def test_vulture_scan_detects_dead_code(client):
    code = "def unused_function():\n    pass\n\nx = 1\n"
    result = await client.call_tool(
        "vulture-scan", {"code": code, "min_confidence": 60}
    )
    assert not result.is_error
    parsed = result.structured_content
    assert parsed["total_items"] >= 1


@pytest.mark.asyncio
async def test_vulture_scan_clean_code(client):
    code = "def main():\n    print('hello')\n\nmain()\n"
    result = await client.call_tool("vulture-scan", {"code": code})
    assert not result.is_error
    parsed = result.structured_content
    assert parsed["total_items"] == 0


@pytest.mark.asyncio
async def test_analyze_code_summary_structure(client):
    code = "import os\ndef unused():\n    pass\n"
    result = await client.call_tool("analyze-code", {"code": code})
    assert not result.is_error
    parsed = result.structured_content
    summary = parsed["summary"]
    expected_keys = {
        "total_ruff_issues",
        "fixable_ruff_issues",
        "total_ty_diagnostics",
        "ty_error_count",
        "ty_warning_count",
        "total_unused_items",
        "high_confidence_unused",
        "code_quality_score",
    }
    assert expected_keys == set(summary.keys())


@pytest.mark.asyncio
async def test_analyze_code_quality_score_range(client):
    result = await client.call_tool("analyze-code", {"code": "import os\n"})
    assert not result.is_error
    parsed = result.structured_content
    score = parsed["summary"]["code_quality_score"]
    assert isinstance(score, int)
    assert 0 <= score <= 100


@pytest.mark.asyncio
async def test_ty_check_tool(client):
    if not server.ty_available:
        pytest.skip("ty not available")
    result = await client.call_tool("ty-check", {"code": "x: int = 1\n"})
    assert not result.is_error
    parsed = result.structured_content
    assert parsed["total_diagnostics"] == 0


@pytest.mark.asyncio
async def test_ruff_check_empty_raises(client):
    with pytest.raises(ToolError, match="must not be empty"):
        await client.call_tool("ruff-check", {"code": ""})


@pytest.mark.asyncio
async def test_read_overview_resource(client):
    content = await client.read_resource("docs://analyzers/overview")
    text = content[0].text if hasattr(content[0], "text") else str(content[0])
    assert "Python Analyzer" in text
    assert "ruff-check" in text


@pytest.mark.asyncio
async def test_read_versions_resource(client):
    content = await client.read_resource("config://analyzer-versions")
    text = content[0].text if hasattr(content[0], "text") else str(content[0])
    parsed = json.loads(text)
    assert "ruff" in parsed
    assert "vulture" in parsed
    assert "fastmcp" in parsed


@pytest.mark.asyncio
async def test_tool_annotations(client):
    tools = await client.list_tools()
    ruff_check_tool = next(t for t in tools if t.name == "ruff-check")
    annotations = ruff_check_tool.annotations
    assert annotations is not None
    assert annotations.readOnlyHint is True
