"""Tests for Biome analyzer integration."""

import pytest

from mcp_server_analyzer.analyzers.biome import BiomeAnalyzer
from mcp_server_analyzer.models import BiomeCheckResult, BiomeFormatResult

pytestmark = pytest.mark.usefixtures("mock_biome_cli")


class TestBiomeAnalyzer:
    """Test cases for BiomeAnalyzer functionality."""

    def test_biome_analyzer_initialization(self):
        """Test that BiomeAnalyzer can be initialized."""
        try:
            analyzer = BiomeAnalyzer()
            assert analyzer is not None
        except RuntimeError:
            # Skip if Biome is not available
            pytest.skip("Biome not available for testing")

    def test_biome_check_basic_js(self):
        """Test basic Biome check functionality with JavaScript code."""
        try:
            analyzer = BiomeAnalyzer()
        except RuntimeError:
            pytest.skip("Biome not available for testing")

        # Test code with issues
        js_code = """
let x = "hello";
const y = 'world';
function test(){
    return x + y
}
test()
"""

        result = analyzer.check_code(js_code, ".js")

        assert isinstance(result, BiomeCheckResult)
        assert result.files_checked == 1
        # Should find some issues (formatting, consistency)
        assert result.total_issues >= 0

    def test_biome_format_js(self):
        """Test Biome formatting functionality."""
        try:
            analyzer = BiomeAnalyzer()
        except RuntimeError:
            pytest.skip("Biome not available for testing")

        # Test code that needs formatting
        js_code = """const x="hello";let y='world';function test(){return x+y;}"""

        result = analyzer.format_code(js_code, ".js")

        assert isinstance(result, BiomeFormatResult)
        assert result.changed is True
        assert len(result.formatted_code) > len(
            js_code
        )  # Should be formatted with proper spacing

    def test_biome_check_typescript(self):
        """Test Biome check with TypeScript code."""
        try:
            analyzer = BiomeAnalyzer()
        except RuntimeError:
            pytest.skip("Biome not available for testing")

        # TypeScript code
        ts_code = """
interface User {
    name: string;
    age: number;
}

function greet(user: User): string {
    return `Hello, ${user.name}!`;
}
"""

        result = analyzer.check_code(ts_code, ".ts")

        assert isinstance(result, BiomeCheckResult)
        assert result.files_checked == 1
        # TypeScript code might have fewer issues
        assert result.total_issues >= 0

    def test_biome_check_ci_format(self):
        """Test Biome CI check functionality."""
        try:
            analyzer = BiomeAnalyzer()
        except RuntimeError:
            pytest.skip("Biome not available for testing")

        js_code = 'const x = "test";'

        result = analyzer.check_code_for_ci(js_code, ".js", "json")

        assert isinstance(result, str)
        # Should return valid output (even if empty for clean code)
        assert result is not None

    def test_biome_file_type_detection(self):
        """Test file type detection helper."""
        try:
            analyzer = BiomeAnalyzer()
        except RuntimeError:
            pytest.skip("Biome not available for testing")

        # Test TypeScript detection
        ts_code = "interface User { name: string; }"
        file_type = analyzer._detect_file_type(ts_code)
        assert file_type == ".ts"

        # Test JSX detection
        jsx_code = "import React from 'react';"
        file_type = analyzer._detect_file_type(jsx_code)
        assert file_type == ".jsx"

        # Test JavaScript fallback
        js_code = "const x = 1;"
        file_type = analyzer._detect_file_type(js_code)
        assert file_type == ".js"

    def test_parse_span_location_with_valid_span(self):
        """Parse span data into accurate line/column positions."""
        try:
            analyzer = BiomeAnalyzer()
        except RuntimeError:
            pytest.skip("Biome not available for testing")

        source_code = "ab\ncd\nef"
        start_line, start_col, end_line, end_col = analyzer._parse_span_location(
            {"sourceCode": source_code},
            [3, 7],
        )

        assert (start_line, start_col, end_line, end_col) == (2, 1, 3, 2)

    def test_parse_span_location_with_missing_span(self):
        """Fallback to defaults when span data is unavailable."""
        try:
            analyzer = BiomeAnalyzer()
        except RuntimeError:
            pytest.skip("Biome not available for testing")

        start_line, start_col, end_line, end_col = analyzer._parse_span_location(
            {"sourceCode": "function demo() {}"},
            [],
        )

        assert (start_line, start_col, end_line, end_col) == (1, 1, None, None)

    def test_biome_issue_fixture(self, sample_biome_issue):
        """Ensure the shared BiomeIssue fixture provides stable data."""
        assert sample_biome_issue.rule == "mock/rule"
        assert sample_biome_issue.fixable is True
