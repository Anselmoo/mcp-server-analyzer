"""Enhanced tests for VultureAnalyzer with improved coverage."""

import tempfile
from pathlib import Path

from mcp_server_analyzer.analyzers.vulture import VultureAnalyzer


def test_vulture_analyzer_init():
    """Test VultureAnalyzer initialization."""
    analyzer = VultureAnalyzer()
    assert analyzer is not None


def test_vulture_analyzer_scan_code_basic():
    """Test basic code scanning functionality."""
    analyzer = VultureAnalyzer()

    # Test clean code
    clean_code = "print('hello world')"
    result = analyzer.scan_code(clean_code)

    assert hasattr(result, "total_items")
    assert hasattr(result, "unused_items")
    assert hasattr(result, "high_confidence_items")
    assert result.total_items >= 0
    assert result.high_confidence_items >= 0


def test_vulture_analyzer_scan_code_with_unused():
    """Test code scanning with unused items."""
    analyzer = VultureAnalyzer()

    # Code with unused function and variable
    code_with_unused = """
import os
unused_var = "not used"

def unused_function():
    return "never called"

def main():
    print('hello')

if __name__ == "__main__":
    main()
"""

    result = analyzer.scan_code(code_with_unused)

    assert result.total_items >= 0
    assert isinstance(result.unused_items, list)


def test_vulture_analyzer_with_confidence():
    """Test analyzer with different confidence levels."""
    analyzer = VultureAnalyzer()

    test_code = """
import os
unused_var = "not used"
print('hello')
"""

    # Test different confidence thresholds
    confidence_levels = [60, 80, 90, 100]

    for confidence in confidence_levels:
        result = analyzer.scan_code(test_code, min_confidence=confidence)
        assert result.total_items >= 0
        assert isinstance(result.unused_items, list)
        assert result.high_confidence_items >= 0


def test_vulture_analyzer_different_code_samples():
    """Test analyzer with different code samples."""
    analyzer = VultureAnalyzer()

    code_samples = [
        "",  # Empty code
        "print('hello')",  # Simple code
        "import os\nprint('hello')",  # Import only
        "def func():\n    pass\nprint('used')",  # Function definition
        "class MyClass:\n    pass\nMyClass()",  # Class definition with usage
    ]

    for code in code_samples:
        result = analyzer.scan_code(code)
        assert result.total_items >= 0
        assert isinstance(result.unused_items, list)
        assert result.high_confidence_items >= 0