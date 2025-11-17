"""Integration tests for MCP server tools with Biome support."""

import pytest

pytestmark = pytest.mark.usefixtures("mock_biome_cli")


class TestBiomeServerIntegration:
    """Test MCP server Biome tool integration."""

    def test_biome_analyzer_direct(self):
        """Test Biome analyzer directly."""
        try:
            from mcp_server_analyzer.analyzers import BiomeAnalyzer

            analyzer = BiomeAnalyzer()

            js_code = 'let x = "hello"; const y = "world";'
            result = analyzer.check_code(js_code, ".js")

            assert result.files_checked == 1
            assert result.total_issues >= 0
            assert isinstance(result.issues, list)

        except RuntimeError:
            # Biome not available - this is expected in some environments
            pytest.skip("Biome not available for testing")

    def test_biome_format_direct(self):
        """Test Biome formatting directly."""
        try:
            from mcp_server_analyzer.analyzers import BiomeAnalyzer

            analyzer = BiomeAnalyzer()

            js_code = 'const x="hello";let y="world";'
            result = analyzer.format_code(js_code, ".js")

            assert hasattr(result, "formatted_code")
            assert hasattr(result, "changed")

        except RuntimeError:
            # Biome not available - this is expected in some environments
            pytest.skip("Biome not available for testing")

    def test_mixed_analysis_types(self):
        """Test different file extensions are handled correctly."""
        try:
            from mcp_server_analyzer.analyzers import BiomeAnalyzer

            analyzer = BiomeAnalyzer()

            # Test JavaScript
            js_result = analyzer.check_code("const x = 1;", ".js")
            assert js_result.files_checked == 1

            # Test TypeScript
            ts_result = analyzer.check_code("const x: number = 1;", ".ts")
            assert ts_result.files_checked == 1

        except RuntimeError:
            pytest.skip("Biome not available for testing")

    def test_server_imports(self):
        """Test that server imports work correctly with Biome integration."""
        # This should not raise any import errors
        from mcp_server_analyzer.analyzers import BiomeAnalyzer
        from mcp_server_analyzer.server import app

        assert app is not None
        # BiomeAnalyzer should be importable even if Biome isn't available
        assert BiomeAnalyzer is not None

    def test_model_imports(self):
        """Test that new Biome models can be imported."""
        from mcp_server_analyzer.models import (
            BiomeIssue,
        )

        # Test BiomeIssue creation
        issue = BiomeIssue(
            line=1,
            column=1,
            rule="test-rule",
            message="Test message",
            severity="error",
            fixable=True,
        )
        assert issue.line == 1
        assert issue.rule == "test-rule"
