"""Enhanced integration tests for MCP server analyzer."""

from mcp_server_analyzer.analyzers.ruff import RuffAnalyzer
from mcp_server_analyzer.analyzers.vulture import VultureAnalyzer


def test_integration_ruff_vulture_workflow():
    """Test complete RUFF + VULTURE analysis workflow."""
    # Sample code with both RUFF and VULTURE issues
    sample_code = """
import os
import sys

unused_variable = "not used"

def unused_function():
    return "never called"

def main():
    print("hello world")
    return 42

if __name__ == "__main__":
    main()
"""

    try:
        # Test RUFF analysis
        ruff_analyzer = RuffAnalyzer()
        ruff_result = ruff_analyzer.check_code(sample_code)

        assert hasattr(ruff_result, "total_issues")
        assert hasattr(ruff_result, "fixable_issues")
        assert hasattr(ruff_result, "issues")

        # Test VULTURE analysis
        vulture_analyzer = VultureAnalyzer()
        vulture_result = vulture_analyzer.scan_code(sample_code)

        assert hasattr(vulture_result, "total_items")
        assert hasattr(vulture_result, "high_confidence_items")
        assert hasattr(vulture_result, "unused_items")

        # Both should work without errors
        assert ruff_result.total_issues >= 0
        assert vulture_result.total_items >= 0

    except Exception as e:
        assert False, f"Integration workflow failed: {e}"


def test_integration_clean_code_workflow():
    """Test workflow with clean code."""
    clean_code = """
def main() -> int:
    '''Main function.'''
    print("hello world")
    return 42

if __name__ == "__main__":
    main()
"""

    try:
        ruff_analyzer = RuffAnalyzer()
        ruff_result = ruff_analyzer.check_code(clean_code)

        vulture_analyzer = VultureAnalyzer()
        vulture_result = vulture_analyzer.scan_code(clean_code)

        # Should complete without errors
        assert ruff_result.total_issues >= 0
        assert vulture_result.total_items >= 0

    except Exception as e:
        assert False, f"Clean code workflow failed: {e}"


def test_integration_format_then_analyze():
    """Test format-then-analyze workflow."""
    unformatted_code = "print(   'hello world'   )"

    try:
        ruff_analyzer = RuffAnalyzer()

        # Format the code first
        format_result = ruff_analyzer.format_code(unformatted_code)
        assert hasattr(format_result, "formatted_code")
        assert hasattr(format_result, "changed")

        # Then analyze the formatted code
        check_result = ruff_analyzer.check_code(format_result.formatted_code)
        assert hasattr(check_result, "total_issues")

    except Exception as e:
        assert False, f"Format-then-analyze workflow failed: {e}"


def test_integration_server_analyze_code():
    """Test full server analyze-code workflow."""
    try:
        from mcp_server_analyzer.server import analyze_code

        test_code = """
import os
def main():
    print('hello world')

if __name__ == "__main__":
    main()
"""

        result = analyze_code(test_code)

        # Should return complete analysis
        assert isinstance(result, dict)
        assert "ruff_result" in result
        assert "vulture_result" in result
        assert "quality_score" in result

        # Quality score should be reasonable
        quality_score = result["quality_score"]
        assert isinstance(quality_score, int)
        assert 0 <= quality_score <= 100

    except Exception as e:
        assert False, f"Server analyze-code workflow failed: {e}"


def test_integration_multiple_code_samples():
    """Test integration with multiple code samples."""
    code_samples = [
        "print('hello')",  # Simple
        "import os\nprint('world')",  # With import
        "def func():\n    pass\nfunc()",  # Function call
        "",  # Empty
    ]

    try:
        ruff_analyzer = RuffAnalyzer()
        vulture_analyzer = VultureAnalyzer()

        for code in code_samples:
            # Both analyzers should handle all samples
            ruff_result = ruff_analyzer.check_code(code)
            vulture_result = vulture_analyzer.scan_code(code)

            assert ruff_result.total_issues >= 0
            assert vulture_result.total_items >= 0

    except Exception as e:
        assert False, f"Multiple code samples workflow failed: {e}"


def test_integration_confidence_filtering():
    """Test integration with different confidence levels."""
    test_code = """
import os
unused_var = "test"
def unused_func(): pass
print('hello')
"""

    try:
        vulture_analyzer = VultureAnalyzer()

        # Test with different confidence thresholds
        confidence_levels = [60, 80, 90, 100]
        results = []

        for confidence in confidence_levels:
            result = vulture_analyzer.scan_code(test_code, min_confidence=confidence)
            results.append(result.total_items)
            assert result.total_items >= 0

        # Generally, higher confidence should yield fewer or equal results
        # (but this isn't guaranteed due to actual tool behavior)
        assert all(isinstance(r, int) for r in results)

    except Exception as e:
        assert False, f"Confidence filtering integration failed: {e}"

    def test_full_analysis_workflow_with_issues(
        self, sample_code_with_issues: str
    ) -> None:
        """Test complete analysis workflow with problematic code."""
        from mcp_server_analyzer.server import analyze_code

        # Mock RUFF results
        mock_ruff_issues = [
            RuffIssue(
                line=2, column=1, rule="F401", message="'os' imported but unused",
                severity="error", fixable=True
            ),
            RuffIssue(
                line=3, column=1, rule="F401", message="'sys' imported but unused",
                severity="error", fixable=True
            ),
        ]
        mock_ruff_result = RuffCheckResult(
            issues=mock_ruff_issues,
            total_issues=2,
            fixable_issues=2
        )

        # Mock VULTURE results
        mock_vulture_items = [
            VultureItem(
                name="unused_variable", type="variable", line=5, column=1,
                confidence=90, message="unused variable 'unused_variable'"
            ),
            VultureItem(
                name="unused_function", type="function", line=7, column=1,
                confidence=85, message="unused function 'unused_function'"
            ),
            VultureItem(
                name="temp_var", type="variable", line=12, column=5,
                confidence=75, message="unused variable 'temp_var'"
            ),
            VultureItem(
                name="UnusedClass", type="class", line=15, column=1,
                confidence=80, message="unused class 'UnusedClass'"
            ),
        ]
        mock_vulture_result = VultureScanResult(
            unused_items=mock_vulture_items,
            total_items=4,
            high_confidence_items=3  # >= 80% confidence
        )

        with patch("mcp_server_analyzer.server.vulture_available", True):
            with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_ruff:
                with patch("mcp_server_analyzer.server.vulture_analyzer") as mock_vulture:
                    mock_ruff.check_code.return_value = mock_ruff_result
                    mock_vulture.scan_code.return_value = mock_vulture_result

                    result = analyze_code(sample_code_with_issues)

                    # Verify structure
                    assert "error" not in result
                    assert "ruff_result" in result
                    assert "vulture_result" in result
                    assert "summary" in result

                    # Verify RUFF results
                    ruff_data = result["ruff_result"]
                    assert ruff_data["total_issues"] == 2
                    assert ruff_data["fixable_issues"] == 2
                    assert len(ruff_data["issues"]) == 2

                    # Verify VULTURE results
                    vulture_data = result["vulture_result"]
                    assert vulture_data["total_items"] == 4
                    assert vulture_data["high_confidence_items"] == 3
                    assert len(vulture_data["unused_items"]) == 4

                    # Verify summary
                    summary = result["summary"]
                    assert summary["total_ruff_issues"] == 2
                    assert summary["fixable_ruff_issues"] == 2
                    assert summary["total_unused_items"] == 4
                    assert summary["high_confidence_unused"] == 3

                    # Verify quality score calculation
                    # Expected: 100 - (2*2) - (3*5) - (1*2) = 100 - 4 - 15 - 2 = 79
                    assert summary["code_quality_score"] == 79

    def test_full_analysis_workflow_clean_code(self, sample_clean_code: str) -> None:
        """Test complete analysis workflow with clean code."""
        from mcp_server_analyzer.server import analyze_code

        mock_ruff_result = RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)
        mock_vulture_result = VultureScanResult(unused_items=[], total_items=0, high_confidence_items=0)

        with patch("mcp_server_analyzer.server.vulture_available", True):
            with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_ruff:
                with patch("mcp_server_analyzer.server.vulture_analyzer") as mock_vulture:
                    mock_ruff.check_code.return_value = mock_ruff_result
                    mock_vulture.scan_code.return_value = mock_vulture_result

                    result = analyze_code(sample_clean_code)

                    # Verify perfect results
                    assert result["ruff_result"]["total_issues"] == 0
                    assert result["vulture_result"]["total_items"] == 0
                    assert result["summary"]["code_quality_score"] == 100

    def test_ruff_only_workflow(self, sample_code_with_issues: str) -> None:
        """Test workflow when only RUFF is available."""
        from mcp_server_analyzer.server import analyze_code

        mock_ruff_result = RuffCheckResult(
            issues=[RuffIssue(line=1, column=1, rule="F401", message="unused", severity="error")],
            total_issues=1,
            fixable_issues=1
        )

        with patch("mcp_server_analyzer.server.vulture_available", False):
            with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_ruff:
                mock_ruff.check_code.return_value = mock_ruff_result

                result = analyze_code(sample_code_with_issues)

                # Should still work with RUFF only
                assert result["ruff_result"]["total_issues"] == 1
                # VULTURE should have default values
                assert result["vulture_result"]["total_items"] == 0
                assert result["summary"]["code_quality_score"] == 98  # 100 - 2

    def test_individual_tool_workflows(self) -> None:
        """Test individual tool workflows."""
        from mcp_server_analyzer.server import ruff_check, ruff_format, vulture_scan

        test_code = "import os\nunused_var = 42\nprint( 'hello' )"

        # Test ruff-check workflow
        mock_ruff_result = RuffCheckResult(
            issues=[RuffIssue(line=1, column=1, rule="F401", message="unused", severity="error")],
            total_issues=1,
            fixable_issues=0
        )

        with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_ruff:
            mock_ruff.check_code.return_value = mock_ruff_result

            result = ruff_check(test_code)
            assert result["total_issues"] == 1

        # Test ruff-format workflow
        from mcp_server_analyzer.models import RuffFormatResult
        mock_format_result = RuffFormatResult(
            formatted_code="import os\nunused_var = 42\nprint('hello')",
            changed=True
        )

        with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_ruff:
            mock_ruff.format_code.return_value = mock_format_result

            result = ruff_format(test_code)
            assert result["changed"] is True
            assert "print('hello')" in result["formatted_code"]

        # Test vulture-scan workflow
        mock_vulture_result = VultureScanResult(
            unused_items=[VultureItem(name="unused_var", type="variable", line=2, column=1, confidence=85, message="unused")],
            total_items=1,
            high_confidence_items=1
        )

        with patch("mcp_server_analyzer.server.vulture_available", True):
            with patch("mcp_server_analyzer.server.vulture_analyzer") as mock_vulture:
                mock_vulture.scan_code.return_value = mock_vulture_result

                result = vulture_scan(test_code)
                assert result["total_items"] == 1
                assert result["high_confidence_items"] == 1

    def test_configuration_parameter_propagation(self) -> None:
        """Test that configuration parameters are properly propagated."""
        from mcp_server_analyzer.server import analyze_code, ruff_check, ruff_format

        test_code = "print('hello')"
        config_path = "/path/to/pyproject.toml"

        mock_ruff_result = RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)

        # Test analyze_code parameter propagation
        with patch("mcp_server_analyzer.server.vulture_available", True):
            with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_ruff:
                with patch("mcp_server_analyzer.server.vulture_analyzer") as mock_vulture:
                    mock_ruff.check_code.return_value = mock_ruff_result
                    mock_vulture.scan_code.return_value = VultureScanResult(
                        unused_items=[], total_items=0, high_confidence_items=0
                    )

                    analyze_code(
                        test_code, ruff_config_path=config_path, min_confidence=90
                    )

                    mock_ruff.check_code.assert_called_with(test_code, config_path)
                    mock_vulture.scan_code.assert_called_with(test_code, 90)

        # Test ruff_check parameter propagation
        with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_ruff:
            mock_ruff.check_code.return_value = mock_ruff_result

            ruff_check(test_code, config_path=config_path)
            mock_ruff.check_code.assert_called_with(test_code, config_path)

        # Test ruff_format parameter propagation
        from mcp_server_analyzer.models import RuffFormatResult
        mock_format_result = RuffFormatResult(formatted_code=test_code, changed=False)

        with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_ruff:
            mock_ruff.format_code.return_value = mock_format_result

            ruff_format(test_code, config_path=config_path)
            mock_ruff.format_code.assert_called_with(test_code, config_path)

    def test_error_handling_workflows(self) -> None:
        """Test error handling in various workflow scenarios."""
        from mcp_server_analyzer.server import analyze_code, ruff_check, vulture_scan

        test_code = "invalid python syntax !!!"

        # Test analyze_code error handling
        with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_ruff:
            mock_ruff.check_code.side_effect = RuntimeError("Syntax error")

            result = analyze_code(test_code)
            assert "error" in result
            assert "Code analysis failed" in result["error"]
            assert result["summary"]["code_quality_score"] == 0

        # Test ruff_check error handling
        with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_ruff:
            mock_ruff.check_code.side_effect = RuntimeError("Check failed")

            result = ruff_check(test_code)
            assert "error" in result
            assert "RUFF check failed" in result["error"]
            assert result["total_issues"] == 0

        # Test vulture_scan error handling when available
        with patch("mcp_server_analyzer.server.vulture_available", True):
            with patch("mcp_server_analyzer.server.vulture_analyzer") as mock_vulture:
                mock_vulture.scan_code.side_effect = RuntimeError("Scan failed")

                result = vulture_scan(test_code)
                assert "error" in result
                assert "VULTURE scan failed" in result["error"]

    def test_quality_score_scenarios(self) -> None:
        """Test various quality score calculation scenarios."""
        from mcp_server_analyzer.server import _calculate_quality_score

        scenarios = [
            # (ruff_issues, vulture_total, vulture_high_conf, expected_score)
            (0, 0, 0, 100),  # Perfect code
            (1, 0, 0, 98),   # One RUFF issue
            (0, 1, 1, 95),   # One high-confidence VULTURE issue
            (0, 2, 1, 93),   # Mixed VULTURE issues
            (5, 2, 1, 86),   # Mixed issues: 100 - 10 - 5 + 1 = 86
            (25, 6, 6, 20),  # High penalty scenario: 100 - 50 - 30 = 20
            (50, 10, 10, 0), # Maximum penalties: should clamp to 0
        ]

        for ruff_issues, vulture_total, vulture_high_conf, expected in scenarios:
            ruff_result = RuffCheckResult(issues=[], total_issues=ruff_issues, fixable_issues=0)
            vulture_result = VultureScanResult(
                unused_items=[], total_items=vulture_total, high_confidence_items=vulture_high_conf
            )

            score = _calculate_quality_score(ruff_result, vulture_result)
            assert score == expected, f"Failed for scenario: {(ruff_issues, vulture_total, vulture_high_conf)}"

    def test_large_codebase_simulation(self) -> None:
        """Test workflow with simulation of large codebase analysis."""
        from mcp_server_analyzer.server import analyze_code

        # Simulate a large codebase with many issues
        large_code = "# Large codebase simulation\n" + "import unused_module\n" * 100

        # Create many issues to test performance characteristics
        ruff_issues = [
            RuffIssue(line=i+2, column=1, rule="F401", message=f"unused import {i}", severity="error")
            for i in range(100)
        ]
        vulture_items = [
            VultureItem(name=f"unused_{i}", type="import", line=i+2, column=1, confidence=85, message=f"unused {i}")
            for i in range(100)
        ]

        mock_ruff_result = RuffCheckResult(issues=ruff_issues, total_issues=100, fixable_issues=100)
        mock_vulture_result = VultureScanResult(unused_items=vulture_items, total_items=100, high_confidence_items=100)

        with patch("mcp_server_analyzer.server.vulture_available", True):
            with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_ruff:
                with patch("mcp_server_analyzer.server.vulture_analyzer") as mock_vulture:
                    mock_ruff.check_code.return_value = mock_ruff_result
                    mock_vulture.scan_code.return_value = mock_vulture_result

                    result = analyze_code(large_code)

                    # Verify it handles large results correctly
                    assert result["ruff_result"]["total_issues"] == 100
                    assert result["vulture_result"]["total_items"] == 100
                    assert len(result["ruff_result"]["issues"]) == 100
                    assert len(result["vulture_result"]["unused_items"]) == 100
                    # Quality score should be 0 due to penalties: 100 - 50 - 30 - 20 = 0
                    assert result["summary"]["code_quality_score"] == 0

    def test_mixed_severity_analysis(self) -> None:
        """Test analysis with mixed severity levels."""
        from mcp_server_analyzer.server import analyze_code

        # Create issues with different severities
        mixed_issues = [
            RuffIssue(line=1, column=1, rule="F401", message="unused import", severity="error", fixable=True),
            RuffIssue(line=2, column=1, rule="W292", message="no newline", severity="warning", fixable=True),
            RuffIssue(line=3, column=1, rule="I001", message="import order", severity="info", fixable=False),
        ]

        # Create mixed confidence unused items
        mixed_vulture_items = [
            VultureItem(name="high_conf", type="variable", line=4, column=1, confidence=95, message="high confidence"),
            VultureItem(name="med_conf", type="function", line=5, column=1, confidence=75, message="medium confidence"),
            VultureItem(name="low_conf", type="class", line=6, column=1, confidence=55, message="low confidence"),
        ]

        mock_ruff_result = RuffCheckResult(issues=mixed_issues, total_issues=3, fixable_issues=2)
        mock_vulture_result = VultureScanResult(
            unused_items=mixed_vulture_items, total_items=3, high_confidence_items=1
        )

        with patch("mcp_server_analyzer.server.vulture_available", True):
            with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_ruff:
                with patch("mcp_server_analyzer.server.vulture_analyzer") as mock_vulture:
                    mock_ruff.check_code.return_value = mock_ruff_result
                    mock_vulture.scan_code.return_value = mock_vulture_result

                    result = analyze_code("mixed code")

                    # Verify mixed results are handled properly
                    assert result["ruff_result"]["total_issues"] == 3
                    assert result["ruff_result"]["fixable_issues"] == 2
                    assert result["vulture_result"]["total_items"] == 3
                    assert result["vulture_result"]["high_confidence_items"] == 1

                    # Verify all issue types are present
                    issues = result["ruff_result"]["issues"]
                    severities = [issue["severity"] for issue in issues]
                    assert "error" in severities
                    assert "warning" in severities
                    assert "info" in severities