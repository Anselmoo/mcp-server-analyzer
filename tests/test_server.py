"""Simple working tests for MCP Python Analyzer."""

from types import SimpleNamespace

from mcp_server_analyzer import server
from mcp_server_analyzer.analyzers.ruff import RuffAnalyzer
from mcp_server_analyzer.analyzers.vulture import VultureAnalyzer
from mcp_server_analyzer.models import (
    BiomeCheckResult,
    RuffCheckResult,
    VultureScanResult,
)


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


class TestServerTools:
    """Test the tool functions defined in the server module."""

    def test_ruff_check_success(self, monkeypatch) -> None:
        """Ensure ruff_check delegates to the analyzer and returns a dict."""

        def fake_check(code: str, config: str | None) -> RuffCheckResult:
            assert code == "print('hi')"
            assert config == "pyproject.toml"
            return RuffCheckResult(issues=[], total_issues=1, fixable_issues=0)

        monkeypatch.setattr(
            server, "ruff_analyzer", SimpleNamespace(check_code=fake_check)
        )

        result = server.ruff_check.fn("print('hi')", config_path="pyproject.toml")

        assert result["total_issues"] == 1
        assert result["fixable_issues"] == 0

    def test_ruff_check_handles_exception(self, monkeypatch) -> None:
        """ruff_check should return an error payload when analyzer fails."""

        def fake_check(_: str, __: str | None) -> RuffCheckResult:
            raise RuntimeError("boom")

        monkeypatch.setattr(
            server, "ruff_analyzer", SimpleNamespace(check_code=fake_check)
        )

        result = server.ruff_check.fn("raise ValueError()")

        assert result["error"].startswith("RUFF check failed")
        assert result["total_issues"] == 0

    def test_vulture_scan_not_available(self, monkeypatch) -> None:
        """vulture_scan should short-circuit when Vulture is unavailable."""

        monkeypatch.setattr(server, "vulture_available", False)

        result = server.vulture_scan.fn("print('hi')")

        assert result["error"].startswith("VULTURE is not available")
        assert result["total_items"] == 0

    def test_vulture_scan_success(self, monkeypatch) -> None:
        """vulture_scan should return analyzer output when available."""

        def fake_scan(code: str, min_conf: int) -> VultureScanResult:
            assert code == "print('hi')"
            assert min_conf == 70
            return VultureScanResult(
                unused_items=[],
                total_items=2,
                high_confidence_items=1,
            )

        monkeypatch.setattr(server, "vulture_available", True)
        monkeypatch.setattr(
            server, "vulture_analyzer", SimpleNamespace(scan_code=fake_scan)
        )

        result = server.vulture_scan.fn("print('hi')", min_confidence=70)

        assert result["total_items"] == 2
        assert result["high_confidence_items"] == 1

    def test_biome_check_not_available(self, monkeypatch) -> None:
        """biome_check should return error payload when Biome is missing."""

        monkeypatch.setattr(server, "biome_available", False)

        result = server.biome_check.fn("console.log('hi');")

        assert result["error"].startswith("Biome is not available")
        assert result["total_issues"] == 0

    def test_analyze_code_combines_results(self, monkeypatch) -> None:
        """analyze_code should merge RUFF and Vulture summaries."""

        ruff_result = RuffCheckResult(issues=[], total_issues=2, fixable_issues=1)
        vulture_result = VultureScanResult(
            unused_items=[], total_items=3, high_confidence_items=1
        )

        monkeypatch.setattr(
            server, "ruff_analyzer", SimpleNamespace(check_code=lambda *_: ruff_result)
        )
        monkeypatch.setattr(server, "vulture_available", True)
        monkeypatch.setattr(
            server,
            "vulture_analyzer",
            SimpleNamespace(scan_code=lambda *_: vulture_result),
        )

        result = server.analyze_code.fn("print('hi')", ruff_config_path="cfg.toml")

        summary = result["summary"]
        assert summary["total_ruff_issues"] == 2
        assert summary["total_unused_items"] == 3
        assert result["ruff_result"]["total_issues"] == 2
        assert result["vulture_result"]["total_items"] == 3

    def test_analyze_mixed_code_all_tools(self, monkeypatch) -> None:
        """analyze_mixed_code should aggregate all available tool outputs."""

        ruff_result = RuffCheckResult(issues=[], total_issues=1, fixable_issues=0)
        vulture_result = VultureScanResult(
            unused_items=[], total_items=2, high_confidence_items=1
        )
        biome_result = BiomeCheckResult(
            issues=[], total_issues=3, fixable_issues=1, files_checked=1
        )

        monkeypatch.setattr(
            server, "ruff_analyzer", SimpleNamespace(check_code=lambda *_: ruff_result)
        )
        monkeypatch.setattr(server, "vulture_available", True)
        monkeypatch.setattr(
            server,
            "vulture_analyzer",
            SimpleNamespace(scan_code=lambda *_: vulture_result),
        )
        monkeypatch.setattr(server, "biome_available", True)
        monkeypatch.setattr(
            server,
            "biome_analyzer",
            SimpleNamespace(check_code=lambda *_: biome_result),
        )

        result = server.analyze_mixed_code.fn(
            python_code="print('hi')",
            js_ts_code="console.log('hi');",
            file_extension=".ts",
            config_paths={"ruff": "ruff.toml", "biome": "biome.json"},
            min_confidence=60,
        )

        summary = result["summary"]
        assert summary["total_ruff_issues"] == 1
        assert summary["total_unused_items"] == 2
        assert summary["total_biome_issues"] == 3
        assert result["biome_result"]["files_checked"] == 1

    def test_analyze_mixed_code_handles_missing_js_tools(self, monkeypatch) -> None:
        """analyze_mixed_code should tolerate missing Biome support."""

        ruff_result = RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)
        vulture_result = VultureScanResult(
            unused_items=[], total_items=0, high_confidence_items=0
        )

        monkeypatch.setattr(
            server, "ruff_analyzer", SimpleNamespace(check_code=lambda *_: ruff_result)
        )
        monkeypatch.setattr(server, "vulture_available", True)
        monkeypatch.setattr(
            server,
            "vulture_analyzer",
            SimpleNamespace(scan_code=lambda *_: vulture_result),
        )
        monkeypatch.setattr(server, "biome_available", False)

        result = server.analyze_mixed_code.fn(python_code="print('hi')", js_ts_code="foo")

        summary = result["summary"]
        assert summary["total_biome_issues"] == 0
        assert result["biome_result"] is None
