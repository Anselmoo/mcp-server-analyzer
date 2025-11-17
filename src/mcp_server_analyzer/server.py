"""MCP Python Analyzer Server - Main FastMCP server implementation."""

import logging
import sys
from typing import Any

from fastmcp import FastMCP

from mcp_server_analyzer.analyzers import BiomeAnalyzer, RuffAnalyzer, VultureAnalyzer
from mcp_server_analyzer.models import (
    AnalysisResult,
    BiomeCheckResult,
    ExtendedAnalysisResult,
    RuffCheckResult,
    VultureScanResult,
)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
app: FastMCP[Any] = FastMCP("Python Analyzer")

# Initialize analyzers
ruff_analyzer = RuffAnalyzer()

# Try to initialize VULTURE analyzer, but handle gracefully if it fails
try:
    vulture_analyzer: VultureAnalyzer | None = VultureAnalyzer()
    vulture_available = True
except RuntimeError as e:
    logger.warning("VULTURE not available: %s", e)
    vulture_analyzer = None
    vulture_available = False

# Try to initialize Biome analyzer, but handle gracefully if it fails
try:
    biome_analyzer: BiomeAnalyzer | None = BiomeAnalyzer()
    biome_available = True
except RuntimeError as e:
    logger.warning("Biome not available: %s", e)
    biome_analyzer = None
    biome_available = False


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
    try:
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


@app.tool(name="biome-check")
def biome_check(
    code: str, file_extension: str = ".js", config_path: str | None = None
) -> dict[str, Any]:
    """
    Lint JavaScript/TypeScript code using Biome to identify style violations and potential errors.

    Args:
        code: JavaScript/TypeScript code to analyze
        file_extension: File extension to determine language (.js, .ts, .jsx, .tsx)
        config_path: Optional path to Biome configuration file

    Returns:
        Dictionary containing linting results with issues, counts, and metadata
    """
    if not biome_available:
        return {
            "error": "Biome is not available - please install @biomejs/biome package",
            "issues": [],
            "total_issues": 0,
            "fixable_issues": 0,
            "files_checked": 0,
        }

    try:
        assert biome_analyzer is not None  # assure the type checker
        result = biome_analyzer.check_code(code, file_extension, config_path)
        return result.model_dump()
    except Exception as e:
        return {
            "error": f"Biome check failed: {e!s}",
            "issues": [],
            "total_issues": 0,
            "fixable_issues": 0,
            "files_checked": 0,
        }


@app.tool(name="biome-format")
def biome_format(
    code: str, file_extension: str = ".js", config_path: str | None = None
) -> dict[str, Any]:
    """
    Format JavaScript/TypeScript code using Biome's fast formatter.

    Args:
        code: JavaScript/TypeScript code to format
        file_extension: File extension to determine language (.js, .ts, .jsx, .tsx)
        config_path: Optional path to Biome configuration file

    Returns:
        Dictionary containing formatted code and change status
    """
    if not biome_available:
        return {
            "error": "Biome is not available - please install @biomejs/biome package",
            "formatted_code": code,  # Return original code on error
            "changed": False,
        }

    try:
        assert biome_analyzer is not None  # assure the type checker
        result = biome_analyzer.format_code(code, file_extension, config_path)
        return result.model_dump()
    except Exception as e:
        return {
            "error": f"Biome format failed: {e!s}",
            "formatted_code": code,  # Return original code on error
            "changed": False,
        }


@app.tool(name="biome-check-ci")
def biome_check_ci(
    code: str,
    file_extension: str = ".js",
    output_format: str = "json",
    config_path: str | None = None,
) -> dict[str, Any]:
    """
    Run Biome linter with CI/CD-specific output formats.

    Args:
        code: JavaScript/TypeScript code to lint
        file_extension: File extension to determine language (.js, .ts, .jsx, .tsx)
        output_format: Output format (json, github)
        config_path: Optional path to Biome configuration file

    Returns:
        Dictionary containing raw Biome output in specified format
    """
    if not biome_available:
        return {
            "error": "Biome is not available - please install @biomejs/biome package",
            "output": "",
            "format": output_format,
            "success": False,
        }

    try:
        assert biome_analyzer is not None  # assure the type checker
        result = biome_analyzer.check_code_for_ci(
            code, file_extension, output_format, config_path
        )
        return {
            "output": result,
            "format": output_format,
            "success": True,
        }
    except Exception as e:
        return {
            "error": f"Biome CI check failed: {e!s}",
            "output": "",
            "format": output_format,
            "success": False,
        }


@app.tool(name="analyze-code")
def analyze_code(
    code: str,
    ruff_config_path: str | None = None,
    min_confidence: int = 80,
) -> dict[str, Any]:
    """
    Comprehensive analysis combining RUFF linting and VULTURE dead code detection.

    Args:
        code: Python code to analyze
        ruff_config_path: Optional path to RUFF configuration file
        min_confidence: Minimum confidence level for VULTURE (default: 80)

    Returns:
        Dictionary containing combined analysis results with summary statistics
    """
    try:
        # Run RUFF analysis
        ruff_result = ruff_analyzer.check_code(code, ruff_config_path)

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
            "total_unused_items": vulture_result.total_items,
            "high_confidence_unused": vulture_result.high_confidence_items,
            "code_quality_score": _calculate_quality_score(ruff_result, vulture_result),
        }

        # Combine results
        analysis = AnalysisResult(
            ruff_result=ruff_result,
            vulture_result=vulture_result,
            summary=summary,
        )

        return analysis.model_dump()

    except Exception as e:
        return {
            "error": f"Code analysis failed: {e!s}",
            "ruff_result": {"issues": [], "total_issues": 0, "fixable_issues": 0},
            "vulture_result": {
                "unused_items": [],
                "total_items": 0,
                "high_confidence_items": 0,
            },
            "summary": {
                "total_ruff_issues": 0,
                "fixable_ruff_issues": 0,
                "total_unused_items": 0,
                "high_confidence_unused": 0,
                "code_quality_score": 0,
            },
        }


@app.tool(name="analyze-mixed-code")
def analyze_mixed_code(
    python_code: str | None = None,
    js_ts_code: str | None = None,
    file_extension: str = ".js",
    config_paths: dict[str, str] | None = None,
    min_confidence: int = 80,
) -> dict[str, Any]:
    """
    Comprehensive analysis for mixed Python and JavaScript/TypeScript projects.

    Args:
        python_code: Python code to analyze (optional)
        js_ts_code: JavaScript/TypeScript code to analyze (optional)
        file_extension: File extension for JS/TS code (.js, .ts, .jsx, .tsx)
        config_paths: Optional dict with 'ruff' and 'biome' config file paths
        min_confidence: Minimum confidence level for VULTURE (default: 80)

    Returns:
        Dictionary containing combined analysis results with summary statistics
    """
    try:
        # Extract config paths
        config_paths = config_paths or {}
        ruff_config_path = config_paths.get("ruff")
        biome_config_path = config_paths.get("biome")

        ruff_result = None
        vulture_result = None
        biome_result = None

        # Analyze Python code if provided
        if python_code:
            ruff_result = ruff_analyzer.check_code(python_code, ruff_config_path)

            if vulture_available:
                assert vulture_analyzer is not None
                vulture_result = vulture_analyzer.scan_code(python_code, min_confidence)
            else:
                vulture_result = VultureScanResult(
                    unused_items=[],
                    total_items=0,
                    high_confidence_items=0,
                )

        # Analyze JS/TS code if provided
        if js_ts_code and biome_available:
            assert biome_analyzer is not None
            biome_result = biome_analyzer.check_code(
                js_ts_code, file_extension, biome_config_path
            )

        # Create summary statistics
        summary = {
            "total_ruff_issues": ruff_result.total_issues if ruff_result else 0,
            "fixable_ruff_issues": ruff_result.fixable_issues if ruff_result else 0,
            "total_unused_items": vulture_result.total_items if vulture_result else 0,
            "high_confidence_unused": vulture_result.high_confidence_items
            if vulture_result
            else 0,
            "total_biome_issues": biome_result.total_issues if biome_result else 0,
            "fixable_biome_issues": biome_result.fixable_issues if biome_result else 0,
            "code_quality_score": _calculate_extended_quality_score(
                ruff_result, vulture_result, biome_result
            ),
        }

        # Combine results
        analysis = ExtendedAnalysisResult(
            ruff_result=ruff_result,
            vulture_result=vulture_result,
            biome_result=biome_result,
            summary=summary,
        )

        return analysis.model_dump()

    except Exception as e:
        return {
            "error": f"Mixed code analysis failed: {e!s}",
            "ruff_result": None,
            "vulture_result": None,
            "biome_result": None,
            "summary": {
                "total_ruff_issues": 0,
                "fixable_ruff_issues": 0,
                "total_unused_items": 0,
                "high_confidence_unused": 0,
                "total_biome_issues": 0,
                "fixable_biome_issues": 0,
                "code_quality_score": 0,
            },
        }


def _calculate_quality_score(
    ruff_result: RuffCheckResult, vulture_result: VultureScanResult
) -> int:
    """
    Calculate a simple code quality score based on analysis results.

    Args:
        ruff_result: RUFF linting results
        vulture_result: VULTURE scanning results

    Returns:
        Quality score from 0 to 100 (higher is better)
    """
    # Simple scoring algorithm - can be improved
    base_score = 100

    # Deduct points for RUFF issues
    ruff_penalty = min(ruff_result.total_issues * 2, 50)  # Max 50 points deduction

    # Deduct points for high-confidence unused items
    vulture_penalty = min(
        vulture_result.high_confidence_items * 5, 30
    )  # Max 30 points deduction

    # Deduct points for total unused items (less severe)
    total_unused_penalty = min(
        (vulture_result.total_items - vulture_result.high_confidence_items) * 2, 20
    )  # Max 20 points

    # Replace temp variable with direct return
    return max(0, base_score - ruff_penalty - vulture_penalty - total_unused_penalty)


def _calculate_extended_quality_score(
    ruff_result: RuffCheckResult | None,
    vulture_result: VultureScanResult | None,
    biome_result: BiomeCheckResult | None,
) -> int:
    """
    Calculate a code quality score for mixed Python and JS/TS projects.

    Args:
        ruff_result: RUFF linting results for Python (optional)
        vulture_result: VULTURE scanning results for Python (optional)
        biome_result: Biome results for JS/TS (optional)

    Returns:
        Quality score from 0 to 100 (higher is better)
    """
    base_score = 100

    # Python analysis penalties
    if ruff_result:
        ruff_penalty = min(ruff_result.total_issues * 2, 30)  # Max 30 points
        base_score -= ruff_penalty

    if vulture_result:
        vulture_penalty = min(
            vulture_result.high_confidence_items * 3, 20
        )  # Max 20 points
        total_unused_penalty = min(
            (vulture_result.total_items - vulture_result.high_confidence_items) * 1, 10
        )  # Max 10 points
        base_score -= vulture_penalty + total_unused_penalty

    # JS/TS analysis penalties
    if biome_result:
        biome_penalty = min(biome_result.total_issues * 2, 40)  # Max 40 points
        base_score -= biome_penalty

    return max(0, base_score)


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
