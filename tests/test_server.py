"""Simple working tests for MCP Python Analyzer."""

from mcp_server_analyzer.analyzers.ruff import RuffAnalyzer
from mcp_server_analyzer.analyzers.vulture import VultureAnalyzer
from mcp_server_analyzer.models import RuffCheckResult, VultureScanResult


class TestAnalyzers:
    """Test the analyzers directly."""

    def test_ruff_analyzer_basic(self) -> None:
        """Test basic RUFF analyzer functionality."""
        analyzer = RuffAnalyzer()
        test_code = "import os\nprint('hello')"
        result = analyzer.check_code(test_code)

        assert hasattr(result, "total_issues")
        assert hasattr(result, "issues")
        assert result.total_issues >= 0

    def test_vulture_analyzer_basic(self) -> None:
        """Test basic VULTURE analyzer functionality."""
        analyzer = VultureAnalyzer()
        test_code = "import os\ndef unused(): pass\nprint('hello')"
        result = analyzer.scan_code(test_code)

        assert hasattr(result, "total_items")
        assert hasattr(result, "unused_items")
        assert result.total_items >= 0

    def test_ruff_with_sample_code(self, sample_bad_code: str) -> None:
        """Test RUFF with sample bad code."""
        analyzer = RuffAnalyzer()
        result = analyzer.check_code(sample_bad_code)

        # Should find some issues in bad code
        assert result.total_issues > 0
        assert len(result.issues) > 0

    def test_vulture_with_sample_code(self, sample_bad_code: str) -> None:
        """Test VULTURE with sample bad code."""
        analyzer = VultureAnalyzer()
        result = analyzer.scan_code(sample_bad_code)

        # Should find some unused items in bad code
        assert result.total_items > 0
        assert len(result.unused_items) > 0

    def test_quality_score_calculation(self) -> None:
        """Test quality score calculation with proper model objects."""
        from mcp_server_analyzer.server import _calculate_quality_score

        # Create perfect results
        perfect_ruff = RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)
        perfect_vulture = VultureScanResult(
            unused_items=[], total_items=0, high_confidence_items=0
        )

        perfect_score = _calculate_quality_score(perfect_ruff, perfect_vulture)
        assert perfect_score == 100

        # Create results with issues
        ruff_with_issues = RuffCheckResult(
            issues=[],  # Not filling actual issues for test
            total_issues=10,
            fixable_issues=5,
        )
        vulture_with_issues = VultureScanResult(
            unused_items=[],  # Not filling actual items for test
            total_items=3,
            high_confidence_items=2,
        )

        score_with_issues = _calculate_quality_score(
            ruff_with_issues, vulture_with_issues
        )
        assert 0 <= score_with_issues <= 100
        assert isinstance(score_with_issues, int)
        assert score_with_issues < 100  # Should be less than perfect
