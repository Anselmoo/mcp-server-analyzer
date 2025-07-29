"""Simple test to verify the basic setup works."""


def test_basic_import():
    """Test that we can import the main modules."""
    from mcp_server_analyzer.analyzers.ruff import RuffAnalyzer
    from mcp_server_analyzer.analyzers.vulture import VultureAnalyzer
    from mcp_server_analyzer.models import RuffCheckResult

    assert RuffAnalyzer is not None
    assert VultureAnalyzer is not None
    assert RuffCheckResult is not None


def test_ruff_analyzer_basic():
    """Test basic RUFF analyzer functionality."""
    from mcp_server_analyzer.analyzers.ruff import RuffAnalyzer

    analyzer = RuffAnalyzer()
    test_code = "import os\nprint('hello')"
    result = analyzer.check_code(test_code)

    assert hasattr(result, "total_issues")
    assert hasattr(result, "issues")
    assert result.total_issues >= 0


def test_vulture_analyzer_basic():
    """Test basic VULTURE analyzer functionality."""
    from mcp_server_analyzer.analyzers.vulture import VultureAnalyzer

    analyzer = VultureAnalyzer()
    test_code = "import os\ndef unused(): pass\nprint('hello')"
    result = analyzer.scan_code(test_code)

    assert hasattr(result, "total_items")
    assert hasattr(result, "unused_items")
    assert result.total_items >= 0
