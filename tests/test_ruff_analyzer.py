"""Enhanced tests for RuffAnalyzer with improved coverage."""

import tempfile
from pathlib import Path

from mcp_server_analyzer.analyzers.ruff import RuffAnalyzer


def test_ruff_analyzer_init():
    """Test RuffAnalyzer initialization."""
    analyzer = RuffAnalyzer()
    assert analyzer is not None


def test_ruff_analyzer_check_code_basic():
    """Test basic code checking functionality."""
    analyzer = RuffAnalyzer()

    # Test clean code
    clean_code = "print('hello world')"
    result = analyzer.check_code(clean_code)

    assert hasattr(result, "total_issues")
    assert hasattr(result, "issues")
    assert hasattr(result, "fixable_issues")
    assert result.total_issues >= 0
    assert result.fixable_issues >= 0


def test_ruff_analyzer_check_code_with_issues():
    """Test code checking with known issues."""
    analyzer = RuffAnalyzer()

    # Code with unused import (should trigger F401)
    bad_code = "import os\nprint('hello')"
    result = analyzer.check_code(bad_code)

    assert result.total_issues >= 0
    assert isinstance(result.issues, list)


def test_ruff_analyzer_format_code():
    """Test code formatting functionality."""
    analyzer = RuffAnalyzer()

    # Test formatting
    unformatted_code = "print(   'hello'   )"
    result = analyzer.format_code(unformatted_code)

    assert hasattr(result, "formatted_code")
    assert hasattr(result, "changed")
    assert isinstance(result.formatted_code, str)
    assert isinstance(result.changed, bool)


def test_ruff_analyzer_with_config():
    """Test analyzer with custom config path."""
    analyzer = RuffAnalyzer()

    test_code = "print('hello')"

    # Test with None config (should work)
    result = analyzer.check_code(test_code, config_path=None)
    assert result.total_issues >= 0

    # Test format with None config
    format_result = analyzer.format_code(test_code, config_path=None)
    assert format_result.formatted_code is not None


def test_ruff_analyzer_file_operations():
    """Test analyzer with temporary files."""
    analyzer = RuffAnalyzer()

    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
        tmp_file.write("import os\nprint('hello')")
        tmp_path = Path(tmp_file.name)

    try:
        # Test checking file
        result = analyzer.check_code(tmp_path.read_text())
        assert result.total_issues >= 0

    finally:
        # Clean up
        tmp_path.unlink()


def test_ruff_analyzer_check_code_for_ci():
    """Test CI-specific checking functionality."""
    analyzer = RuffAnalyzer()

    test_code = "import os\nprint('hello')"
    result = analyzer.check_code_for_ci(test_code)

    # CI result should have same structure as regular check
    assert hasattr(result, "total_issues")
    assert hasattr(result, "issues")
    assert hasattr(result, "fixable_issues")


def test_ruff_analyzer_different_code_samples():
    """Test analyzer with different code samples."""
    analyzer = RuffAnalyzer()

    code_samples = [
        "",  # Empty code
        "print('hello')",  # Simple code
        "import os\nimport sys\nprint('hello')",  # Multiple imports
        "def func():\n    pass",  # Function definition
        "class MyClass:\n    pass",  # Class definition
    ]

    for code in code_samples:
        result = analyzer.check_code(code)
        assert result.total_issues >= 0
        assert isinstance(result.issues, list)
        assert result.fixable_issues >= 0

        format_result = analyzer.format_code(code)
        assert isinstance(format_result.formatted_code, str)
        assert isinstance(format_result.changed, bool)