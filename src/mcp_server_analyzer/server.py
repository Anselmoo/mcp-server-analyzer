"""MCP Python Analyzer Server - Main FastMCP server implementation."""

import logging
import sys
from typing import Any

from fastmcp import FastMCP

from mcp_server_analyzer.analyzers import RuffAnalyzer, TyAnalyzer, VultureAnalyzer
from mcp_server_analyzer.models import (
    AnalysisResult,
    RuffCheckResult,
    TyCheckResult,
    VultureScanResult,
)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
app: FastMCP[Any] = FastMCP("Python Analyzer")

# Initialize analyzers
try:
    ruff_analyzer: RuffAnalyzer | None = RuffAnalyzer()
    ruff_available = True
except RuntimeError as e:
    logger.warning("ruff not available: %s", e)
    ruff_analyzer = None
    ruff_available = False

# Try to initialize ty analyzer, but handle gracefully if it fails
try:
    ty_analyzer: TyAnalyzer | None = TyAnalyzer()
    ty_available = True
except RuntimeError as e:
    logger.warning("ty not available: %s", e)
    ty_analyzer = None
    ty_available = False

# Try to initialize VULTURE analyzer, but handle gracefully if it fails
try:
    vulture_analyzer: VultureAnalyzer | None = VultureAnalyzer()
    vulture_available = True
except RuntimeError as e:
    logger.warning("VULTURE not available: %s", e)
    vulture_analyzer = None
    vulture_available = False


@app.tool(name="ruff-check")
def ruff_check(code: str, config_path: str | None = None) -> dict[str, Any]:
    """
    Lint Python code using RUFF to identify style violations and potential errors.

    Args:
        code: Python code to analyze
        config_path: Optional path to RUFF configuration file

    Returns:
        Dictionary containing linting results with issues, counts, and metadata
    """
    if not ruff_available:
        return {
            "error": "ruff is not available - please install the ruff package",
            "issues": [],
            "total_issues": 0,
            "fixable_issues": 0,
        }
    try:
        assert ruff_analyzer is not None
        result = ruff_analyzer.check_code(code, config_path)
        return result.model_dump()
    except Exception as e:
        return {
            "error": f"RUFF check failed: {e!s}",
            "issues": [],
            "total_issues": 0,
            "fixable_issues": 0,
        }


@app.tool(name="ruff-format")
def ruff_format(code: str, config_path: str | None = None) -> dict[str, Any]:
    """
    Format Python code using RUFF's fast formatter.

    Args:
        code: Python code to format
        config_path: Optional path to RUFF configuration file

    Returns:
        Dictionary containing formatted code and change status
    """
    if not ruff_available:
        return {
            "error": "ruff is not available - please install the ruff package",
            "formatted_code": code,
            "changed": False,
        }
    try:
        assert ruff_analyzer is not None
        result = ruff_analyzer.format_code(code, config_path)
        return result.model_dump()
    except Exception as e:
        return {
            "error": f"RUFF format failed: {e!s}",
            "formatted_code": code,  # Return original code on error
            "changed": False,
        }


@app.tool(name="ruff-check-ci")
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
    if not ruff_available:
        return {
            "error": "ruff is not available - please install the ruff package",
            "output": "",
            "format": output_format,
            "success": False,
        }
    try:
        assert ruff_analyzer is not None
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


@app.tool(name="ty-check")
def ty_check(code: str, project_path: str | None = None) -> dict[str, Any]:
    """
    Type-check Python code using ty.

    Args:
        code: Python code to analyze
        project_path: Optional project directory used for ty config and import resolution

    Returns:
        Dictionary containing type diagnostics and counts
    """
    if not ty_available:
        return {
            "error": "ty is not available - please install the ty package",
            "diagnostics": [],
            "total_diagnostics": 0,
            "error_count": 0,
            "warning_count": 0,
        }

    try:
        assert ty_analyzer is not None  # assure the type checker
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


@app.tool(name="vulture-scan")
def vulture_scan(code: str, min_confidence: int = 80) -> dict[str, Any]:
    """
    Detect dead/unused code using VULTURE.

    Args:
        code: Python code to analyze
        min_confidence: Minimum confidence level (0-100) for reporting items

    Returns:
        Dictionary containing unused code items with confidence scores and locations
    """
    if not vulture_available:
        return {
            "error": "VULTURE is not available - please install vulture package",
            "unused_items": [],
            "total_items": 0,
            "high_confidence_items": 0,
        }

    try:
        assert vulture_analyzer is not None  # assure the type checker
        result = vulture_analyzer.scan_code(code, min_confidence)
        return result.model_dump()
    except Exception as e:
        return {
            "error": f"VULTURE scan failed: {e!s}",
            "unused_items": [],
            "total_items": 0,
            "high_confidence_items": 0,
        }


@app.tool(name="analyze-code")
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
    try:
        # Run RUFF analysis
        if ruff_available:
            assert ruff_analyzer is not None
            ruff_result = ruff_analyzer.check_code(code, ruff_config_path)
        else:
            ruff_result = RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)

        # Run ty analysis if available
        if ty_available:
            assert ty_analyzer is not None  # assure the type checker
            ty_result = ty_analyzer.check_code(code, project_path)
        else:
            ty_result = TyCheckResult(
                diagnostics=[],
                total_diagnostics=0,
                error_count=0,
                warning_count=0,
            )

        # Run VULTURE analysis if available
        if vulture_available:
            assert vulture_analyzer is not None  # assure the type checker
            vulture_result = vulture_analyzer.scan_code(code, min_confidence)
        else:
            # Create empty VULTURE result if not available
            vulture_result = VultureScanResult(
                unused_items=[],
                total_items=0,
                high_confidence_items=0,
            )

        # Create summary statistics
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

        # Combine results
        analysis = AnalysisResult(
            ruff_result=ruff_result,
            ty_result=ty_result,
            vulture_result=vulture_result,
            summary=summary,
        )

        return analysis.model_dump()

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
    """
    Calculate a simple code quality score based on analysis results.

    Args:
        ruff_result: RUFF linting results
        ty_result: ty type-checking results
        vulture_result: VULTURE scanning results

    Returns:
        Quality score from 0 to 100 (higher is better)
    """
    # Simple scoring algorithm - can be improved
    base_score = 100

    # Deduct points for RUFF issues
    ruff_penalty = min(ruff_result.total_issues * 2, 50)  # Max 50 points deduction

    # Deduct points for type-checking diagnostics
    ty_penalty = min((ty_result.error_count * 10) + (ty_result.warning_count * 5), 40)

    # Deduct points for high-confidence unused items
    vulture_penalty = min(
        vulture_result.high_confidence_items * 5, 30
    )  # Max 30 points deduction

    # Deduct points for total unused items (less severe)
    total_unused_penalty = min(
        (vulture_result.total_items - vulture_result.high_confidence_items) * 2, 20
    )  # Max 20 points

    return max(
        0,
        base_score - ruff_penalty - ty_penalty - vulture_penalty - total_unused_penalty,
    )


def main() -> None:
    """Main entry point for the MCP server."""
    try:
        # Run the FastMCP server
        app.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Server error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
