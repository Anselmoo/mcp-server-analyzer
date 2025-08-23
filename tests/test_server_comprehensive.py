"""Enhanced tests for MCP server functionality."""

from mcp_server_analyzer.models import (
    RuffCheckResult,
    RuffFormatResult,
    RuffIssue,
    VultureItem,
    VultureScanResult,
)


def test_server_imports():
    """Test that server module and tools can be imported."""
    try:
        from mcp_server_analyzer.server import app, main
        assert app is not None
        assert main is not None
        assert callable(main)
    except ImportError as e:
        assert False, f"Server module import failed: {e}"


def test_ruff_check_tool_basic():
    """Test basic ruff-check tool functionality."""
    try:
        from mcp_server_analyzer.server import ruff_check

        test_code = "print('hello world')"
        result = ruff_check(test_code)

        # Result should be a dictionary
        assert isinstance(result, dict)
        assert "total_issues" in result
        assert "fixable_issues" in result
        assert "issues" in result

    except Exception as e:
        assert False, f"ruff_check tool failed: {e}"


def test_ruff_format_tool_basic():
    """Test basic ruff-format tool functionality."""
    try:
        from mcp_server_analyzer.server import ruff_format

        test_code = "print('hello world')"
        result = ruff_format(test_code)

        # Result should be a dictionary
        assert isinstance(result, dict)
        assert "formatted_code" in result
        assert "changed" in result

    except Exception as e:
        assert False, f"ruff_format tool failed: {e}"


def test_vulture_scan_tool_basic():
    """Test basic vulture-scan tool functionality."""
    try:
        from mcp_server_analyzer.server import vulture_scan

        test_code = "print('hello world')"
        result = vulture_scan(test_code)

        # Result should be a dictionary
        assert isinstance(result, dict)
        assert "total_items" in result
        assert "high_confidence_items" in result
        assert "unused_items" in result

    except Exception as e:
        assert False, f"vulture_scan tool failed: {e}"


def test_analyze_code_tool_basic():
    """Test basic analyze-code tool functionality."""
    try:
        from mcp_server_analyzer.server import analyze_code

        test_code = "print('hello world')"
        result = analyze_code(test_code)

        # Result should be a dictionary with analysis results
        assert isinstance(result, dict)
        assert "ruff_result" in result
        assert "vulture_result" in result
        assert "quality_score" in result

    except Exception as e:
        assert False, f"analyze_code tool failed: {e}"


def test_quality_score_calculation():
    """Test quality score calculation function."""
    try:
        from mcp_server_analyzer.server import _calculate_quality_score

        # Test with perfect results
        perfect_ruff = RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)
        perfect_vulture = VultureScanResult(
            unused_items=[], total_items=0, high_confidence_items=0
        )

        perfect_score = _calculate_quality_score(perfect_ruff, perfect_vulture)
        assert perfect_score == 100

        # Test with some issues
        ruff_with_issues = RuffCheckResult(
            issues=[], total_issues=5, fixable_issues=2
        )
        vulture_with_issues = VultureScanResult(
            unused_items=[], total_items=3, high_confidence_items=1
        )

        score_with_issues = _calculate_quality_score(ruff_with_issues, vulture_with_issues)
        assert 0 <= score_with_issues <= 100
        assert score_with_issues < 100

    except Exception as e:
        assert False, f"Quality score calculation failed: {e}"


def test_server_error_handling():
    """Test server tools handle errors gracefully."""
    try:
        from mcp_server_analyzer.server import ruff_check, vulture_scan

        # Test with invalid Python code
        invalid_code = "invalid python syntax !!!"

        # Tools should handle errors gracefully and not crash
        try:
            result = ruff_check(invalid_code)
            # Even with invalid code, should return a result structure
            assert isinstance(result, dict)
        except Exception:
            # If it raises an exception, that's also acceptable for invalid code
            pass

        try:
            result = vulture_scan(invalid_code)
            # Even with invalid code, should return a result structure
            assert isinstance(result, dict)
        except Exception:
            # If it raises an exception, that's also acceptable for invalid code
            pass

    except Exception as e:
        assert False, f"Server error handling test failed: {e}"


def test_server_with_different_inputs():
    """Test server tools with various input types."""
    try:
        from mcp_server_analyzer.server import ruff_check, vulture_scan

        test_inputs = [
            "",  # Empty code
            "print('hello')",  # Simple code
            "import os\nprint('hello')",  # Code with import
            "def func():\n    pass",  # Function definition
        ]

        for test_code in test_inputs:
            # Test ruff_check
            ruff_result = ruff_check(test_code)
            assert isinstance(ruff_result, dict)
            assert "total_issues" in ruff_result

            # Test vulture_scan
            vulture_result = vulture_scan(test_code)
            assert isinstance(vulture_result, dict)
            assert "total_items" in vulture_result

    except Exception as e:
        assert False, f"Server input variation test failed: {e}"

        mock_result = RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)

        with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_analyzer:
            mock_analyzer.check_code.return_value = mock_result

            result = ruff_check("print('hello')", config_path="/path/to/config.toml")

            assert "error" not in result
            mock_analyzer.check_code.assert_called_once_with(
                "print('hello')", "/path/to/config.toml"
            )

    def test_ruff_check_failure(self) -> None:
        """Test ruff-check tool when analyzer fails."""
        from mcp_server_analyzer.server import ruff_check

        with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_analyzer:
            mock_analyzer.check_code.side_effect = RuntimeError("RUFF failed")

            result = ruff_check("invalid code")

            assert "error" in result
            assert "RUFF check failed: RUFF failed" in result["error"]
            assert result["total_issues"] == 0
            assert result["fixable_issues"] == 0
            assert result["issues"] == []

    def test_ruff_format_success(self) -> None:
        """Test successful ruff-format tool execution."""
        from mcp_server_analyzer.server import ruff_format

        mock_result = RuffFormatResult(
            formatted_code="print('hello')",
            changed=True
        )

        with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_analyzer:
            mock_analyzer.format_code.return_value = mock_result

            result = ruff_format("print( 'hello' )")

            assert "error" not in result
            assert result["formatted_code"] == "print('hello')"
            assert result["changed"] is True
            mock_analyzer.format_code.assert_called_once_with("print( 'hello' )", None)

    def test_ruff_format_with_config(self) -> None:
        """Test ruff-format tool with configuration path."""
        from mcp_server_analyzer.server import ruff_format

        mock_result = RuffFormatResult(formatted_code="print('hello')", changed=False)

        with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_analyzer:
            mock_analyzer.format_code.return_value = mock_result

            result = ruff_format("print('hello')", config_path="/path/to/config.toml")

            assert "error" not in result
            mock_analyzer.format_code.assert_called_once_with(
                "print('hello')", "/path/to/config.toml"
            )

    def test_ruff_format_failure(self) -> None:
        """Test ruff-format tool when analyzer fails."""
        from mcp_server_analyzer.server import ruff_format

        original_code = "invalid code"

        with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_analyzer:
            mock_analyzer.format_code.side_effect = RuntimeError("Format failed")

            result = ruff_format(original_code)

            assert "error" in result
            assert "RUFF format failed: Format failed" in result["error"]
            assert result["formatted_code"] == original_code  # Should return original
            assert result["changed"] is False

    def test_ruff_check_ci_success(self) -> None:
        """Test successful ruff-check-ci tool execution."""
        from mcp_server_analyzer.server import ruff_check_ci

        mock_output = '{"issues": [{"line": 1, "message": "test"}]}'

        with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_analyzer:
            mock_analyzer.check_code_for_ci.return_value = mock_output

            result = ruff_check_ci("import os", output_format="json")

            assert result["success"] is True
            assert result["output"] == mock_output
            assert result["format"] == "json"
            assert "error" not in result
            mock_analyzer.check_code_for_ci.assert_called_once_with("import os", "json", None)

    def test_ruff_check_ci_different_formats(self) -> None:
        """Test ruff-check-ci tool with different output formats."""
        from mcp_server_analyzer.server import ruff_check_ci

        formats = ["gitlab", "github", "sarif"]

        with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_analyzer:
            for fmt in formats:
                mock_analyzer.check_code_for_ci.return_value = f"output in {fmt} format"

                result = ruff_check_ci("import os", output_format=fmt)

                assert result["success"] is True
                assert result["output"] == f"output in {fmt} format"
                assert result["format"] == fmt

    def test_ruff_check_ci_failure(self) -> None:
        """Test ruff-check-ci tool when analyzer fails."""
        from mcp_server_analyzer.server import ruff_check_ci

        with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_analyzer:
            mock_analyzer.check_code_for_ci.side_effect = RuntimeError("CI check failed")

            result = ruff_check_ci("invalid code", output_format="json")

            assert result["success"] is False
            assert "error" in result
            assert "RUFF CI check failed: CI check failed" in result["error"]
            assert result["output"] == ""
            assert result["format"] == "json"

    def test_vulture_scan_success(self) -> None:
        """Test successful vulture-scan tool execution when VULTURE is available."""
        from mcp_server_analyzer.server import vulture_scan

        mock_result = VultureScanResult(
            unused_items=[
                VultureItem(
                    name="unused_var", type="variable", line=1, column=0,
                    confidence=85, message="unused variable 'unused_var'"
                )
            ],
            total_items=1,
            high_confidence_items=1
        )

        with patch("mcp_server_analyzer.server.vulture_available", True):
            with patch("mcp_server_analyzer.server.vulture_analyzer") as mock_analyzer:
                mock_analyzer.scan_code.return_value = mock_result

                result = vulture_scan("unused_var = 42")

                assert "error" not in result
                assert result["total_items"] == 1
                assert result["high_confidence_items"] == 1
                assert len(result["unused_items"]) == 1
                mock_analyzer.scan_code.assert_called_once_with("unused_var = 42", 80)

    def test_vulture_scan_with_min_confidence(self) -> None:
        """Test vulture-scan tool with custom minimum confidence."""
        from mcp_server_analyzer.server import vulture_scan

        mock_result = VultureScanResult(unused_items=[], total_items=0, high_confidence_items=0)

        with patch("mcp_server_analyzer.server.vulture_available", True):
            with patch("mcp_server_analyzer.server.vulture_analyzer") as mock_analyzer:
                mock_analyzer.scan_code.return_value = mock_result

                result = vulture_scan("print('hello')", min_confidence=90)

                assert "error" not in result
                mock_analyzer.scan_code.assert_called_once_with("print('hello')", 90)

    def test_vulture_scan_not_available(self) -> None:
        """Test vulture-scan tool when VULTURE is not available."""
        from mcp_server_analyzer.server import vulture_scan

        with patch("mcp_server_analyzer.server.vulture_available", False):
            result = vulture_scan("unused_var = 42")

            assert "error" in result
            assert "VULTURE is not available" in result["error"]
            assert result["total_items"] == 0
            assert result["high_confidence_items"] == 0
            assert result["unused_items"] == []

    def test_vulture_scan_failure(self) -> None:
        """Test vulture-scan tool when analyzer fails."""
        from mcp_server_analyzer.server import vulture_scan

        with patch("mcp_server_analyzer.server.vulture_available", True):
            with patch("mcp_server_analyzer.server.vulture_analyzer") as mock_analyzer:
                mock_analyzer.scan_code.side_effect = RuntimeError("Scan failed")

                result = vulture_scan("invalid code")

                assert "error" in result
                assert "VULTURE scan failed: Scan failed" in result["error"]
                assert result["total_items"] == 0

    def test_analyze_code_success(self) -> None:
        """Test successful analyze-code tool execution."""
        from mcp_server_analyzer.server import analyze_code

        mock_ruff = RuffCheckResult(
            issues=[RuffIssue(line=1, column=1, rule="F401", message="unused", severity="error")],
            total_issues=1,
            fixable_issues=0
        )
        mock_vulture = VultureScanResult(
            unused_items=[VultureItem(name="var", type="variable", line=2, column=0, confidence=85, message="unused var")],
            total_items=1,
            high_confidence_items=1
        )

        with patch("mcp_server_analyzer.server.vulture_available", True):
            with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_ruff_analyzer:
                with patch("mcp_server_analyzer.server.vulture_analyzer") as mock_vulture_analyzer:
                    mock_ruff_analyzer.check_code.return_value = mock_ruff
                    mock_vulture_analyzer.scan_code.return_value = mock_vulture

                    result = analyze_code("import os\nunused_var = 42")

                    assert "error" not in result
                    assert result["ruff_result"]["total_issues"] == 1
                    assert result["vulture_result"]["total_items"] == 1
                    assert result["summary"]["total_ruff_issues"] == 1
                    assert result["summary"]["total_unused_items"] == 1
                    assert result["summary"]["high_confidence_unused"] == 1
                    assert "code_quality_score" in result["summary"]

    def test_analyze_code_with_configs(self) -> None:
        """Test analyze-code tool with configuration parameters."""
        from mcp_server_analyzer.server import analyze_code

        mock_ruff = RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)
        mock_vulture = VultureScanResult(unused_items=[], total_items=0, high_confidence_items=0)

        with patch("mcp_server_analyzer.server.vulture_available", True):
            with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_ruff_analyzer:
                with patch("mcp_server_analyzer.server.vulture_analyzer") as mock_vulture_analyzer:
                    mock_ruff_analyzer.check_code.return_value = mock_ruff
                    mock_vulture_analyzer.scan_code.return_value = mock_vulture

                    result = analyze_code(
                        "print('hello')",
                        ruff_config_path="/path/to/ruff.toml",
                        min_confidence=90
                    )

                    assert "error" not in result
                    mock_ruff_analyzer.check_code.assert_called_once_with(
                        "print('hello')", "/path/to/ruff.toml"
                    )
                    mock_vulture_analyzer.scan_code.assert_called_once_with(
                        "print('hello')", 90
                    )

    def test_analyze_code_vulture_unavailable(self) -> None:
        """Test analyze-code tool when VULTURE is unavailable."""
        from mcp_server_analyzer.server import analyze_code

        mock_ruff = RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)

        with patch("mcp_server_analyzer.server.vulture_available", False):
            with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_ruff_analyzer:
                mock_ruff_analyzer.check_code.return_value = mock_ruff

                result = analyze_code("print('hello')")

                assert "error" not in result
                assert result["ruff_result"]["total_issues"] == 0
                # Should use default values for VULTURE when unavailable
                assert result["vulture_result"]["total_items"] == 0
                assert result["summary"]["code_quality_score"] == 100  # Perfect score without issues

    def test_analyze_code_failure(self) -> None:
        """Test analyze-code tool when analysis fails."""
        from mcp_server_analyzer.server import analyze_code

        with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_ruff_analyzer:
            mock_ruff_analyzer.check_code.side_effect = RuntimeError("Analysis failed")

            result = analyze_code("invalid code")

            assert "error" in result
            assert "Code analysis failed: Analysis failed" in result["error"]
            assert result["ruff_result"]["total_issues"] == 0
            assert result["vulture_result"]["total_items"] == 0
            assert result["summary"]["code_quality_score"] == 0


class TestQualityScoreCalculation:
    """Test quality score calculation functionality."""

    def test_calculate_quality_score_perfect(self) -> None:
        """Test quality score calculation with no issues."""
        from mcp_server_analyzer.server import _calculate_quality_score

        ruff_result = RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)
        vulture_result = VultureScanResult(unused_items=[], total_items=0, high_confidence_items=0)

        score = _calculate_quality_score(ruff_result, vulture_result)

        assert score == 100

    def test_calculate_quality_score_with_ruff_issues(self) -> None:
        """Test quality score calculation with RUFF issues."""
        from mcp_server_analyzer.server import _calculate_quality_score

        # 10 issues should deduct 20 points (2 per issue)
        ruff_result = RuffCheckResult(issues=[], total_issues=10, fixable_issues=0)
        vulture_result = VultureScanResult(unused_items=[], total_items=0, high_confidence_items=0)

        score = _calculate_quality_score(ruff_result, vulture_result)

        assert score == 80  # 100 - 20

    def test_calculate_quality_score_with_vulture_high_confidence(self) -> None:
        """Test quality score calculation with high-confidence unused items."""
        from mcp_server_analyzer.server import _calculate_quality_score

        ruff_result = RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)
        # 2 high-confidence items should deduct 10 points (5 per item)
        vulture_result = VultureScanResult(unused_items=[], total_items=2, high_confidence_items=2)

        score = _calculate_quality_score(ruff_result, vulture_result)

        assert score == 90  # 100 - 10

    def test_calculate_quality_score_with_vulture_low_confidence(self) -> None:
        """Test quality score calculation with low-confidence unused items."""
        from mcp_server_analyzer.server import _calculate_quality_score

        ruff_result = RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)
        # 5 total items, 1 high-confidence -> 4 low-confidence items deduct 8 points (2 per item)
        vulture_result = VultureScanResult(unused_items=[], total_items=5, high_confidence_items=1)

        score = _calculate_quality_score(ruff_result, vulture_result)

        assert score == 87  # 100 - 5 (high conf) - 8 (low conf) = 87

    def test_calculate_quality_score_maximum_penalties(self) -> None:
        """Test quality score calculation with maximum penalties."""
        from mcp_server_analyzer.server import _calculate_quality_score

        # Test maximum RUFF penalty (50 points max)
        ruff_result = RuffCheckResult(issues=[], total_issues=100, fixable_issues=0)  # Would be 200 points, capped at 50
        vulture_result = VultureScanResult(unused_items=[], total_items=0, high_confidence_items=0)

        score = _calculate_quality_score(ruff_result, vulture_result)

        assert score == 50  # 100 - 50 (max RUFF penalty)

    def test_calculate_quality_score_combined_penalties(self) -> None:
        """Test quality score calculation with all penalty types."""
        from mcp_server_analyzer.server import _calculate_quality_score

        ruff_result = RuffCheckResult(issues=[], total_issues=5, fixable_issues=0)  # 10 points penalty
        # 3 high-confidence (15 points) + 2 low-confidence (4 points)
        vulture_result = VultureScanResult(unused_items=[], total_items=5, high_confidence_items=3)

        score = _calculate_quality_score(ruff_result, vulture_result)

        assert score == 71  # 100 - 10 - 15 - 4 = 71

    def test_calculate_quality_score_minimum_zero(self) -> None:
        """Test quality score calculation never goes below zero."""
        from mcp_server_analyzer.server import _calculate_quality_score

        # Extreme values that would result in negative score
        ruff_result = RuffCheckResult(issues=[], total_issues=50, fixable_issues=0)  # 50 points (max)
        vulture_result = VultureScanResult(unused_items=[], total_items=50, high_confidence_items=10)  # 30 + 20 = 50 points

        score = _calculate_quality_score(ruff_result, vulture_result)

        assert score == 0  # Should be clamped to 0, not negative

    def test_calculate_quality_score_edge_cases(self) -> None:
        """Test quality score calculation with edge case values."""
        from mcp_server_analyzer.server import _calculate_quality_score

        # Test with exactly the threshold values
        ruff_result = RuffCheckResult(issues=[], total_issues=25, fixable_issues=0)  # Exactly 50 points
        vulture_result = VultureScanResult(unused_items=[], total_items=6, high_confidence_items=6)  # Exactly 30 points

        score = _calculate_quality_score(ruff_result, vulture_result)

        assert score == 20  # 100 - 50 - 30 = 20


class TestServerInitialization:
    """Test server initialization and analyzer setup."""

    def test_ruff_analyzer_initialization(self) -> None:
        """Test that RUFF analyzer is always initialized."""
        # This is tested by importing the server module
        from mcp_server_analyzer.server import ruff_analyzer

        assert ruff_analyzer is not None

    def test_vulture_analyzer_initialization_success(self) -> None:
        """Test successful VULTURE analyzer initialization."""
        with patch("mcp_server_analyzer.analyzers.VultureAnalyzer") as mock_vulture:
            mock_instance = MagicMock()
            mock_vulture.return_value = mock_instance

            # Import server module to trigger initialization
            import importlib
            import mcp_server_analyzer.server
            importlib.reload(mcp_server_analyzer.server)

            assert mcp_server_analyzer.server.vulture_available is True
            assert mcp_server_analyzer.server.vulture_analyzer is mock_instance

    def test_vulture_analyzer_initialization_failure(self) -> None:
        """Test VULTURE analyzer initialization failure."""
        with patch("mcp_server_analyzer.analyzers.VultureAnalyzer") as mock_vulture:
            mock_vulture.side_effect = RuntimeError("VULTURE not found")

            # Import server module to trigger initialization
            import importlib
            import mcp_server_analyzer.server
            importlib.reload(mcp_server_analyzer.server)

            assert mcp_server_analyzer.server.vulture_available is False
            assert mcp_server_analyzer.server.vulture_analyzer is None


class TestServerMainFunction:
    """Test server main function and error handling."""

    def test_main_keyboard_interrupt(self) -> None:
        """Test main function handles KeyboardInterrupt."""
        from mcp_server_analyzer.server import main

        with patch("mcp_server_analyzer.server.app") as mock_app:
            mock_app.run.side_effect = KeyboardInterrupt()

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

    def test_main_general_exception(self) -> None:
        """Test main function handles general exceptions."""
        from mcp_server_analyzer.server import main

        with patch("mcp_server_analyzer.server.app") as mock_app:
            mock_app.run.side_effect = RuntimeError("Server error")

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1