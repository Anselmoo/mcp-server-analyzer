"""MCP Python Analyzer Server - Main FastMCP server implementation."""

import importlib.metadata
import json
import logging
import sys
from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from mcp_server_analyzer.analyzers import RuffAnalyzer, TyAnalyzer, VultureAnalyzer
from mcp_server_analyzer.models import (
    AnalysisResult,
    RuffCheckResult,
    TyCheckResult,
    VultureScanResult,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp: FastMCP[Any] = FastMCP("Python Analyzer", mask_error_details=True)
app = mcp  # backward-compat alias

try:
    ruff_analyzer: RuffAnalyzer | None = RuffAnalyzer()
    ruff_available = True
except RuntimeError as e:
    logger.warning("ruff not available: %s", e)
    ruff_analyzer = None
    ruff_available = False

try:
    ty_analyzer: TyAnalyzer | None = TyAnalyzer()
    ty_available = True
except RuntimeError as e:
    logger.warning("ty not available: %s", e)
    ty_analyzer = None
    ty_available = False

try:
    vulture_analyzer: VultureAnalyzer | None = VultureAnalyzer()
    vulture_available = True
except RuntimeError as e:
    logger.warning("VULTURE not available: %s", e)
    vulture_analyzer = None
    vulture_available = False


# ─── Resources ────────────────────────────────────────────────────────────────


@mcp.resource(
    "docs://analyzers/overview",
    mime_type="text/markdown",
    tags={"docs"},
)
def get_overview() -> str:
    """Overview of available analyzers and tools."""
    return (
        "# Python Analyzer MCP Server\n\n"
        "Provides three complementary static-analysis tools:\n\n"
        "| Tool | Purpose | Decorator |\n"
        "|------|---------|----------|\n"
        "| `ruff-check` | Lint for style & errors | `@mcp.tool` |\n"
        "| `ruff-format` | Auto-format code | `@mcp.tool` |\n"
        "| `ruff-check-ci` | CI-friendly lint output | `@mcp.tool` |\n"
        "| `ty-check` | Type-check with ty | `@mcp.tool` |\n"
        "| `vulture-scan` | Dead code detection | `@mcp.tool` |\n"
        "| `analyze-code` | Combined analysis + score | `@mcp.tool` |\n\n"
        "## Quality Score\n"
        "The `analyze-code` tool produces a 0-100 quality score:\n"
        "- Ruff issues: -2 pts each (max -50)\n"
        "- Type errors: -10 pts each; warnings: -5 pts each (max -40)\n"
        "- High-confidence dead code: -5 pts each (max -30)\n"
    )


@mcp.resource(
    "config://analyzer-versions",
    mime_type="application/json",
    tags={"config"},
)
def get_analyzer_versions() -> str:
    """Return current versions of installed analyzers."""
    versions: dict[str, str] = {}
    for pkg in ("ruff", "ty", "vulture", "fastmcp"):
        try:
            versions[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            versions[pkg] = "not installed"
    return json.dumps(versions)


# ─── Tools ────────────────────────────────────────────────────────────────────


@mcp.tool(
    name="ruff-check",
    tags={"linting", "ruff"},
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
def ruff_check(code: str, config_path: str | None = None) -> dict[str, Any]:
    """
    Lint Python code using RUFF to identify style violations and potential errors.

    Args:
        code: Python code to analyze
        config_path: Optional path to RUFF configuration file

    Returns:
        Dictionary containing linting results with issues, counts, and metadata

    """
    if not code.strip():
        raise ToolError("Input code must not be empty.")
    if not ruff_available:
        return {
            "error": "ruff is not available - please install the ruff package",
            "issues": [],
            "total_issues": 0,
            "fixable_issues": 0,
        }
    if ruff_analyzer is None:
        return {
            "error": "Internal error: ruff_analyzer is None despite ruff_available being True",
            "issues": [],
            "total_issues": 0,
            "fixable_issues": 0,
        }
    try:
        result = ruff_analyzer.check_code(code, config_path)
        return result.model_dump()
    except Exception as e:
        return {
            "error": f"RUFF check failed: {e!s}",
            "issues": [],
            "total_issues": 0,
            "fixable_issues": 0,
        }


@mcp.tool(
    name="ruff-format",
    tags={"linting", "ruff"},
    annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True),
)
def ruff_format(code: str, config_path: str | None = None) -> dict[str, Any]:
    """
    Format Python code using RUFF's fast formatter.

    Args:
        code: Python code to format
        config_path: Optional path to RUFF configuration file

    Returns:
        Dictionary containing formatted code and change status

    """
    if not code.strip():
        raise ToolError("Input code must not be empty.")
    if not ruff_available:
        return {
            "error": "ruff is not available - please install the ruff package",
            "formatted_code": code,
            "changed": False,
        }
    if ruff_analyzer is None:
        return {
            "error": "Internal error: ruff_analyzer is None despite ruff_available being True",
            "formatted_code": code,
            "changed": False,
        }
    try:
        result = ruff_analyzer.format_code(code, config_path)
        return result.model_dump()
    except Exception as e:
        return {
            "error": f"RUFF format failed: {e!s}",
            "formatted_code": code,
            "changed": False,
        }


@mcp.tool(
    name="ruff-check-ci",
    tags={"linting", "ruff", "ci"},
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
def ruff_check_ci(
    code: str, output_format: str = "json", config_path: str | None = None
) -> dict[str, Any]:
    """
    Run RUFF linter with CI/CD-specific output formats.

    Args:
        code: Python code to lint
        output_format: Output format (json, gitlab, github, sarif)
        config_path: Optional path to RUFF configuration file

    Returns:
        Dictionary containing raw RUFF output in specified format

    """
    if not code.strip():
        raise ToolError("Input code must not be empty.")
    if not ruff_available:
        return {
            "error": "ruff is not available - please install the ruff package",
            "output": "",
            "format": output_format,
            "success": False,
        }
    if ruff_analyzer is None:
        return {
            "error": "Internal error: ruff_analyzer is None despite ruff_available being True",
            "output": "",
            "format": output_format,
            "success": False,
        }
    try:
        result = ruff_analyzer.check_code_for_ci(code, output_format, config_path)
        return {
            "output": result,
            "format": output_format,
            "success": True,
        }
    except Exception as e:
        return {
            "error": f"RUFF CI check failed: {e!s}",
            "output": "",
            "format": output_format,
            "success": False,
        }


@mcp.tool(
    name="ty-check",
    tags={"type-checking", "ty"},
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
def ty_check(code: str, project_path: str | None = None) -> dict[str, Any]:
    """
    Type-check Python code using ty.

    Args:
        code: Python code to analyze
        project_path: Optional project directory used for ty config and import resolution

    Returns:
        Dictionary containing type diagnostics and counts

    """
    if not code.strip():
        raise ToolError("Input code must not be empty.")
    if not ty_available:
        return {
            "error": "ty is not available - please install the ty package",
            "diagnostics": [],
            "total_diagnostics": 0,
            "error_count": 0,
            "warning_count": 0,
        }
    if ty_analyzer is None:
        return {
            "error": "Internal error: ty_analyzer is None despite ty_available being True",
            "diagnostics": [],
            "total_diagnostics": 0,
            "error_count": 0,
            "warning_count": 0,
        }
    try:
        result = ty_analyzer.check_code(code, project_path)
        return result.model_dump()
    except Exception as e:
        return {
            "error": f"ty check failed: {e!s}",
            "diagnostics": [],
            "total_diagnostics": 0,
            "error_count": 0,
            "warning_count": 0,
        }


@mcp.tool(
    name="vulture-scan",
    tags={"dead-code", "vulture"},
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
def vulture_scan(code: str, min_confidence: int = 80) -> dict[str, Any]:
    """
    Detect dead/unused code using VULTURE.

    Args:
        code: Python code to analyze
        min_confidence: Minimum confidence level (0-100) for reporting items

    Returns:
        Dictionary containing unused code items with confidence scores and locations

    """
    if not code.strip():
        raise ToolError("Input code must not be empty.")
    if not vulture_available:
        return {
            "error": "VULTURE is not available - please install vulture package",
            "unused_items": [],
            "total_items": 0,
            "high_confidence_items": 0,
        }
    if vulture_analyzer is None:
        return {
            "error": "Internal error: vulture_analyzer is None despite vulture_available being True",
            "unused_items": [],
            "total_items": 0,
            "high_confidence_items": 0,
        }
    try:
        result = vulture_analyzer.scan_code(code, min_confidence)
        return result.model_dump()
    except Exception as e:
        return {
            "error": f"VULTURE scan failed: {e!s}",
            "unused_items": [],
            "total_items": 0,
            "high_confidence_items": 0,
        }


def _get_ruff_result(code: str, config_path: str | None) -> RuffCheckResult:
    if not ruff_available or ruff_analyzer is None:
        return RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)
    return ruff_analyzer.check_code(code, config_path)


def _get_ty_result(code: str, project_path: str | None) -> TyCheckResult:
    if not ty_available or ty_analyzer is None:
        return TyCheckResult(
            diagnostics=[],
            total_diagnostics=0,
            error_count=0,
            warning_count=0,
        )
    return ty_analyzer.check_code(code, project_path)


def _get_vulture_result(code: str, min_confidence: int) -> VultureScanResult:
    if not vulture_available or vulture_analyzer is None:
        return VultureScanResult(
            unused_items=[],
            total_items=0,
            high_confidence_items=0,
        )
    return vulture_analyzer.scan_code(code, min_confidence)


@mcp.tool(
    name="analyze-code",
    tags={"analysis", "comprehensive"},
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
def analyze_code(
    code: str,
    ruff_config_path: str | None = None,
    min_confidence: int = 80,
    project_path: str | None = None,
) -> dict[str, Any]:
    """
    Comprehensive analysis combining Ruff linting, ty type checking, and Vulture dead code detection.

    Args:
        code: Python code to analyze
        ruff_config_path: Optional path to RUFF configuration file
        min_confidence: Minimum confidence level for VULTURE (default: 80)
        project_path: Optional project directory used by ty for config and import resolution

    Returns:
        Dictionary containing combined analysis results with summary statistics

    """
    if not code.strip():
        raise ToolError("Input code must not be empty.")
    try:
        ruff_result = _get_ruff_result(code, ruff_config_path)
        ty_result = _get_ty_result(code, project_path)
        vulture_result = _get_vulture_result(code, min_confidence)

        summary = {
            "total_ruff_issues": ruff_result.total_issues,
            "fixable_ruff_issues": ruff_result.fixable_issues,
            "total_ty_diagnostics": ty_result.total_diagnostics,
            "ty_error_count": ty_result.error_count,
            "ty_warning_count": ty_result.warning_count,
            "total_unused_items": vulture_result.total_items,
            "high_confidence_unused": vulture_result.high_confidence_items,
            "code_quality_score": _calculate_quality_score(
                ruff_result, ty_result, vulture_result
            ),
        }

        analysis = AnalysisResult(
            ruff_result=ruff_result,
            ty_result=ty_result,
            vulture_result=vulture_result,
            summary=summary,
        )

        return analysis.model_dump()

    except ToolError:
        raise
    except Exception as e:
        return {
            "error": f"Code analysis failed: {e!s}",
            "ruff_result": {"issues": [], "total_issues": 0, "fixable_issues": 0},
            "ty_result": {
                "diagnostics": [],
                "total_diagnostics": 0,
                "error_count": 0,
                "warning_count": 0,
            },
            "vulture_result": {
                "unused_items": [],
                "total_items": 0,
                "high_confidence_items": 0,
            },
            "summary": {
                "total_ruff_issues": 0,
                "fixable_ruff_issues": 0,
                "total_ty_diagnostics": 0,
                "ty_error_count": 0,
                "ty_warning_count": 0,
                "total_unused_items": 0,
                "high_confidence_unused": 0,
                "code_quality_score": 0,
            },
        }


def _calculate_quality_score(
    ruff_result: RuffCheckResult,
    ty_result: TyCheckResult,
    vulture_result: VultureScanResult,
) -> int:
    """Calculate a 0-100 quality score (higher is better)."""
    base_score = 100
    ruff_penalty = min(ruff_result.total_issues * 2, 50)
    ty_penalty = min((ty_result.error_count * 10) + (ty_result.warning_count * 5), 40)
    vulture_penalty = min(vulture_result.high_confidence_items * 5, 30)
    total_unused_penalty = min(
        (vulture_result.total_items - vulture_result.high_confidence_items) * 2, 20
    )
    return max(
        0,
        base_score - ruff_penalty - ty_penalty - vulture_penalty - total_unused_penalty,
    )


def main() -> None:
    """Run the MCP server as main entry point."""
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Server error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
