"""Error handling and edge case tests for server and analyzers."""

import importlib.metadata
import subprocess
from unittest.mock import Mock, patch

import pytest
from fastmcp.exceptions import ToolError

from mcp_server_analyzer import server
from mcp_server_analyzer.analyzers.ruff import RuffAnalyzer
from mcp_server_analyzer.analyzers.ty import TyAnalyzer
from mcp_server_analyzer.analyzers.vulture import VultureAnalyzer
from mcp_server_analyzer.models import (
    AnalysisResult,
    RuffCheckResult,
    TyCheckResult,
    VultureScanResult,
)


def _get_fn(tool_func):
    """Extract the underlying function from a tool, handling both FunctionTool and plain functions."""
    return getattr(tool_func, "fn", tool_func)


class TestServerToolsUnavailable:
    """Tests for tool functions when analyzers are unavailable."""

    def test_ruff_check_unavailable(self, monkeypatch):
        """Test ruff_check raises ToolError when unavailable."""
        monkeypatch.setattr(server, "ruff_available", False)
        fn = _get_fn(server.ruff_check)
        with pytest.raises(ToolError, match="not available"):
            fn("code")

    def test_ruff_format_unavailable(self, monkeypatch):
        """Test ruff_format raises ToolError when unavailable."""
        monkeypatch.setattr(server, "ruff_available", False)
        fn = _get_fn(server.ruff_format)
        with pytest.raises(ToolError, match="not available"):
            fn("code")

    def test_ruff_check_ci_unavailable(self, monkeypatch):
        """Test ruff_check_ci raises ToolError when unavailable."""
        monkeypatch.setattr(server, "ruff_available", False)
        fn = _get_fn(server.ruff_check_ci)
        with pytest.raises(ToolError, match="not available"):
            fn("code")

    def test_ty_check_unavailable(self, monkeypatch):
        """Test ty_check raises ToolError when unavailable."""
        monkeypatch.setattr(server, "ty_available", False)
        fn = _get_fn(server.ty_check)
        with pytest.raises(ToolError, match="not available"):
            fn("code")

    def test_vulture_scan_unavailable(self, monkeypatch):
        """Test vulture_scan raises ToolError when unavailable."""
        monkeypatch.setattr(server, "vulture_available", False)
        fn = _get_fn(server.vulture_scan)
        with pytest.raises(ToolError, match="not available"):
            fn("code")

    def test_biome_check_unavailable(self, monkeypatch):
        """Test biome_check raises ToolError when unavailable."""
        monkeypatch.setattr(server, "biome_available", False)
        fn = _get_fn(server.biome_check)
        with pytest.raises(ToolError, match="not available"):
            fn("const x = 1;")

    def test_biome_format_unavailable(self, monkeypatch):
        """Test biome_format raises ToolError when unavailable."""
        monkeypatch.setattr(server, "biome_available", False)
        fn = _get_fn(server.biome_format)
        with pytest.raises(ToolError, match="not available"):
            fn("const x = 1;")


class TestServerToolsExceptions:
    """Tests for tool functions handling analyzer exceptions."""

    def test_ruff_check_exception(self, monkeypatch):
        """Test ruff_check raises ToolError on analyzer exception."""
        mock_analyzer = Mock()
        mock_analyzer.check_code.side_effect = RuntimeError("Check failed")
        monkeypatch.setattr(server, "ruff_analyzer", mock_analyzer)
        monkeypatch.setattr(server, "ruff_available", True)

        fn = _get_fn(server.ruff_check)
        with pytest.raises(ToolError, match="RUFF check failed"):
            fn("code")

    def test_ruff_format_exception(self, monkeypatch):
        """Test ruff_format raises ToolError on analyzer exception."""
        mock_analyzer = Mock()
        mock_analyzer.format_code.side_effect = RuntimeError("Format failed")
        monkeypatch.setattr(server, "ruff_analyzer", mock_analyzer)
        monkeypatch.setattr(server, "ruff_available", True)

        fn = _get_fn(server.ruff_format)
        with pytest.raises(ToolError, match="RUFF format failed"):
            fn("code")

    def test_ruff_check_ci_exception(self, monkeypatch):
        """Test ruff_check_ci raises ToolError on analyzer exception."""
        mock_analyzer = Mock()
        mock_analyzer.check_code_for_ci.side_effect = RuntimeError("CI check failed")
        monkeypatch.setattr(server, "ruff_analyzer", mock_analyzer)
        monkeypatch.setattr(server, "ruff_available", True)

        fn = _get_fn(server.ruff_check_ci)
        with pytest.raises(ToolError, match="RUFF CI check failed"):
            fn("code")

    def test_ty_check_exception(self, monkeypatch):
        """Test ty_check raises ToolError on analyzer exception."""
        mock_analyzer = Mock()
        mock_analyzer.check_code.side_effect = RuntimeError("Type check failed")
        monkeypatch.setattr(server, "ty_analyzer", mock_analyzer)
        monkeypatch.setattr(server, "ty_available", True)

        fn = _get_fn(server.ty_check)
        with pytest.raises(ToolError, match="ty check failed"):
            fn("code")

    def test_vulture_scan_exception(self, monkeypatch):
        """Test vulture_scan raises ToolError on analyzer exception."""
        mock_analyzer = Mock()
        mock_analyzer.scan_code.side_effect = RuntimeError("Scan failed")
        monkeypatch.setattr(server, "vulture_analyzer", mock_analyzer)
        monkeypatch.setattr(server, "vulture_available", True)

        fn = _get_fn(server.vulture_scan)
        with pytest.raises(ToolError, match="VULTURE scan failed"):
            fn("code")

    def test_biome_check_exception(self, monkeypatch):
        """Test biome_check raises ToolError on analyzer exception."""
        mock_analyzer = Mock()
        mock_analyzer.check_code.side_effect = RuntimeError("Check failed")
        monkeypatch.setattr(server, "biome_analyzer", mock_analyzer)
        monkeypatch.setattr(server, "biome_available", True)

        fn = _get_fn(server.biome_check)
        with pytest.raises(ToolError, match="Biome check failed"):
            fn("const x = 1;")

    def test_biome_format_exception(self, monkeypatch):
        """Test biome_format raises ToolError on analyzer exception."""
        mock_analyzer = Mock()
        mock_analyzer.format_code.side_effect = RuntimeError("Format failed")
        monkeypatch.setattr(server, "biome_analyzer", mock_analyzer)
        monkeypatch.setattr(server, "biome_available", True)

        fn = _get_fn(server.biome_format)
        with pytest.raises(ToolError, match="Biome format failed"):
            fn("const x = 1;")


class TestAnalyzeCodeErrorPaths:
    """Tests for analyze_code error handling."""

    def test_analyze_code_all_unavailable(self, monkeypatch):
        """Test analyze_code succeeds with zero results when all analyzers unavailable."""
        monkeypatch.setattr(server, "ruff_available", False)
        monkeypatch.setattr(server, "ty_available", False)
        monkeypatch.setattr(server, "vulture_available", False)

        fn = _get_fn(server.analyze_code)
        result = fn("code")
        assert isinstance(result, AnalysisResult)
        assert result.summary.total_ruff_issues == 0

    def test_analyze_code_ruff_only(self, monkeypatch):
        """Test analyze_code with only ruff available."""
        mock_ruff = Mock()
        mock_ruff.check_code.return_value = RuffCheckResult(
            issues=[], total_issues=3, fixable_issues=1
        )

        monkeypatch.setattr(server, "ruff_analyzer", mock_ruff)
        monkeypatch.setattr(server, "ruff_available", True)
        monkeypatch.setattr(server, "ty_available", False)
        monkeypatch.setattr(server, "vulture_available", False)

        fn = _get_fn(server.analyze_code)
        result = fn("code")
        assert result.summary.total_ruff_issues == 3

    def test_analyze_code_exception(self, monkeypatch):
        """Test analyze_code raises ToolError on analyzer exception."""
        mock_ruff = Mock()
        mock_ruff.check_code.side_effect = RuntimeError("Failed")
        monkeypatch.setattr(server, "ruff_analyzer", mock_ruff)
        monkeypatch.setattr(server, "ruff_available", True)

        fn = _get_fn(server.analyze_code)
        with pytest.raises(ToolError, match="Code analysis failed"):
            fn("code")


class TestTyAnalyzerErrors:
    """Tests for TyAnalyzer error handling."""

    def test_invalid_project_path(self, monkeypatch):
        """Test check_code with invalid project path."""
        mock_result = Mock()
        mock_result.returncode = 0
        monkeypatch.setattr(subprocess, "run", Mock(return_value=mock_result))

        analyzer = TyAnalyzer()
        with pytest.raises(
            ValueError, match="project_path must be an existing directory"
        ):
            analyzer.check_code("code", "/nonexistent")

    def test_timeout_in_check_code(self, monkeypatch):
        """Test check_code timeout handling."""

        init_mock = Mock()
        init_mock.returncode = 0
        call_count = [0]

        def side_effect(*_args, **_kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return init_mock
            raise subprocess.TimeoutExpired("ty", 30)

        monkeypatch.setattr(subprocess, "run", Mock(side_effect=side_effect))
        analyzer = TyAnalyzer()

        with pytest.raises(RuntimeError, match="ty check timed out"):
            analyzer.check_code("code")

    def test_parse_ty_malformed_output(self, monkeypatch):
        """Test _parse_ty_output handles malformed lines."""
        mock_result = Mock()
        mock_result.returncode = 0
        monkeypatch.setattr(subprocess, "run", Mock(return_value=mock_result))

        analyzer = TyAnalyzer()
        output = "invalid\nmore invalid\n"
        result = analyzer._parse_ty_output(output, "file.py")
        assert result == []


class TestRuffAnalyzerErrors:
    """Tests for RuffAnalyzer error handling."""

    def test_get_severity(self, monkeypatch):
        """Test _get_severity returns valid severity."""
        mock_result = Mock()
        mock_result.returncode = 0
        monkeypatch.setattr(subprocess, "run", Mock(return_value=mock_result))

        analyzer = RuffAnalyzer()
        severity = analyzer._get_severity("UNKNOWN")
        assert severity in ["error", "warning", "note"]


class TestMainEntrypoint:
    """Tests for main() error handling."""

    def test_keyboard_interrupt(self, monkeypatch):
        """Test main() handles KeyboardInterrupt."""
        mock_app = Mock()
        mock_app.run.side_effect = KeyboardInterrupt()
        monkeypatch.setattr(server, "app", mock_app)

        with pytest.raises(SystemExit) as exc:
            server.main()
        assert exc.value.code == 0

    def test_exception(self, monkeypatch):
        """Test main() handles general exception."""
        mock_app = Mock()
        mock_app.run.side_effect = RuntimeError("Server error")
        monkeypatch.setattr(server, "app", mock_app)

        with pytest.raises(SystemExit) as exc:
            server.main()
        assert exc.value.code == 1


class TestServerNullAnalyzerGuards:
    """Tests for null analyzer type guards in tool functions."""

    def test_ruff_check_null_analyzer(self, monkeypatch):
        """Test ruff_check raises ToolError when analyzer is None."""
        monkeypatch.setattr(server, "ruff_available", True)
        monkeypatch.setattr(server, "ruff_analyzer", None)
        fn = _get_fn(server.ruff_check)
        with pytest.raises(ToolError, match="not available"):
            fn("code")

    def test_ruff_format_null_analyzer(self, monkeypatch):
        """Test ruff_format raises ToolError when analyzer is None."""
        monkeypatch.setattr(server, "ruff_available", True)
        monkeypatch.setattr(server, "ruff_analyzer", None)
        fn = _get_fn(server.ruff_format)
        with pytest.raises(ToolError, match="not available"):
            fn("code")

    def test_ruff_check_ci_null_analyzer(self, monkeypatch):
        """Test ruff_check_ci raises ToolError when analyzer is None."""
        monkeypatch.setattr(server, "ruff_available", True)
        monkeypatch.setattr(server, "ruff_analyzer", None)
        fn = _get_fn(server.ruff_check_ci)
        with pytest.raises(ToolError, match="not available"):
            fn("code", "github")

    def test_ty_check_null_analyzer(self, monkeypatch):
        """Test ty_check raises ToolError when analyzer is None."""
        monkeypatch.setattr(server, "ty_available", True)
        monkeypatch.setattr(server, "ty_analyzer", None)
        fn = _get_fn(server.ty_check)
        with pytest.raises(ToolError, match="not available"):
            fn("code")

    def test_vulture_scan_null_analyzer(self, monkeypatch):
        """Test vulture_scan raises ToolError when analyzer is None."""
        monkeypatch.setattr(server, "vulture_available", True)
        monkeypatch.setattr(server, "vulture_analyzer", None)
        fn = _get_fn(server.vulture_scan)
        with pytest.raises(ToolError, match="not available"):
            fn("code")

    def test_analyze_code_null_analyzers(self, monkeypatch):
        """Test analyze_code succeeds with empty results when all analyzers are None."""
        monkeypatch.setattr(server, "ruff_available", True)
        monkeypatch.setattr(server, "ruff_analyzer", None)
        monkeypatch.setattr(server, "ty_available", True)
        monkeypatch.setattr(server, "ty_analyzer", None)
        monkeypatch.setattr(server, "vulture_available", True)
        monkeypatch.setattr(server, "vulture_analyzer", None)
        fn = _get_fn(server.analyze_code)
        result = fn("code")
        assert isinstance(result, AnalysisResult)
        assert result.summary.total_ruff_issues == 0
        assert result.summary.total_ty_diagnostics == 0
        assert result.summary.total_unused_items == 0


class TestToolErrorOnEmptyInput:
    """Tests that all tools raise ToolError for empty/whitespace-only input."""

    def test_ruff_check_empty_input(self):
        """Test ruff_check raises ToolError on empty input."""
        fn = _get_fn(server.ruff_check)
        with pytest.raises(ToolError, match="must not be empty"):
            fn("")

    def test_ruff_check_whitespace_input(self):
        """Test ruff_check raises ToolError on whitespace-only input."""
        fn = _get_fn(server.ruff_check)
        with pytest.raises(ToolError, match="must not be empty"):
            fn("   \n\t  ")

    def test_ruff_format_empty_input(self):
        """Test ruff_format raises ToolError on empty input."""
        fn = _get_fn(server.ruff_format)
        with pytest.raises(ToolError, match="must not be empty"):
            fn("")

    def test_ruff_format_whitespace_input(self):
        """Test ruff_format raises ToolError on whitespace-only input."""
        fn = _get_fn(server.ruff_format)
        with pytest.raises(ToolError, match="must not be empty"):
            fn("  ")

    def test_ruff_check_ci_empty_input(self):
        """Test ruff_check_ci raises ToolError on empty input."""
        fn = _get_fn(server.ruff_check_ci)
        with pytest.raises(ToolError, match="must not be empty"):
            fn("")

    def test_ruff_check_ci_whitespace_input(self):
        """Test ruff_check_ci raises ToolError on whitespace-only input."""
        fn = _get_fn(server.ruff_check_ci)
        with pytest.raises(ToolError, match="must not be empty"):
            fn("\n\n")

    def test_ty_check_empty_input(self):
        """Test ty_check raises ToolError on empty input."""
        fn = _get_fn(server.ty_check)
        with pytest.raises(ToolError, match="must not be empty"):
            fn("")

    def test_ty_check_whitespace_input(self):
        """Test ty_check raises ToolError on whitespace-only input."""
        fn = _get_fn(server.ty_check)
        with pytest.raises(ToolError, match="must not be empty"):
            fn("   ")

    def test_vulture_scan_empty_input(self):
        """Test vulture_scan raises ToolError on empty input."""
        fn = _get_fn(server.vulture_scan)
        with pytest.raises(ToolError, match="must not be empty"):
            fn("")

    def test_vulture_scan_whitespace_input(self):
        """Test vulture_scan raises ToolError on whitespace-only input."""
        fn = _get_fn(server.vulture_scan)
        with pytest.raises(ToolError, match="must not be empty"):
            fn("  \t  ")

    def test_biome_check_empty_input(self):
        """Test biome_check raises ToolError on empty input."""
        fn = _get_fn(server.biome_check)
        with pytest.raises(ToolError, match="must not be empty"):
            fn("")

    def test_biome_check_whitespace_input(self):
        """Test biome_check raises ToolError on whitespace-only input."""
        fn = _get_fn(server.biome_check)
        with pytest.raises(ToolError, match="must not be empty"):
            fn("   \n\t  ")

    def test_biome_format_empty_input(self):
        """Test biome_format raises ToolError on empty input."""
        fn = _get_fn(server.biome_format)
        with pytest.raises(ToolError, match="must not be empty"):
            fn("")

    def test_biome_format_whitespace_input(self):
        """Test biome_format raises ToolError on whitespace-only input."""
        fn = _get_fn(server.biome_format)
        with pytest.raises(ToolError, match="must not be empty"):
            fn("   ")

    def test_analyze_code_empty_input(self):
        """Test analyze_code raises ToolError on empty input."""
        fn = _get_fn(server.analyze_code)
        with pytest.raises(ToolError, match="must not be empty"):
            fn("")

    def test_analyze_code_whitespace_input(self):
        """Test analyze_code raises ToolError on whitespace-only input."""
        fn = _get_fn(server.analyze_code)
        with pytest.raises(ToolError, match="must not be empty"):
            fn("   \n")


class TestServerResources:
    """Tests for MCP resource functions."""

    def test_get_overview_returns_markdown(self):
        """Test get_overview returns valid markdown string."""
        fn = _get_fn(server.get_overview)
        result = fn()
        assert isinstance(result, str)
        assert "Python Analyzer" in result
        assert "ruff-check" in result

    def test_get_analyzer_versions_returns_json(self):
        """Test get_analyzer_versions returns valid JSON with known packages."""
        import json

        fn = _get_fn(server.get_analyzer_versions)
        result = fn()
        assert isinstance(result, str)
        data = json.loads(result)
        assert "ruff" in data
        assert "fastmcp" in data

    def test_get_analyzer_versions_handles_missing_pkg(self, monkeypatch):
        """Test get_analyzer_versions marks unavailable packages."""
        import json

        original_version = importlib.metadata.version

        def patched_version(pkg):
            if pkg == "fastmcp":
                raise importlib.metadata.PackageNotFoundError(pkg)
            return original_version(pkg)

        monkeypatch.setattr(importlib.metadata, "version", patched_version)

        fn = _get_fn(server.get_analyzer_versions)
        result = fn()
        data = json.loads(result)
        assert data["fastmcp"] == "not installed"


class TestRuffAnalyzerEdgeCases:
    """Tests for RuffAnalyzer edge cases and error paths."""

    def test_init_fails_when_ruff_not_found(self):
        """Test RuffAnalyzer raises RuntimeError when ruff binary is missing."""
        with (
            patch("subprocess.run", side_effect=FileNotFoundError("ruff not found")),
            pytest.raises(RuntimeError, match="RUFF is not available"),
        ):
            RuffAnalyzer()

    def test_init_fails_on_subprocess_error(self):
        """Test RuffAnalyzer raises RuntimeError on CalledProcessError."""
        with (
            patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(1, "ruff"),
            ),
            pytest.raises(RuntimeError, match="RUFF is not available"),
        ):
            RuffAnalyzer()

    def test_check_code_bad_returncode(self, monkeypatch):
        """Test check_code raises RuntimeError when ruff exits with unexpected code."""
        mock_init = Mock(returncode=0, stdout="", stderr="")
        mock_check = Mock(returncode=2, stdout="", stderr="internal error")

        call_count = [0]

        def side_effect(*_args, **_kwargs):
            call_count[0] += 1
            return mock_init if call_count[0] == 1 else mock_check

        monkeypatch.setattr(subprocess, "run", Mock(side_effect=side_effect))
        analyzer = RuffAnalyzer()
        with pytest.raises(RuntimeError, match="RUFF check failed"):
            analyzer.check_code("code")

    def test_check_code_with_config_path(self, monkeypatch, tmp_path):
        """Test check_code passes config path to ruff."""
        config_file = tmp_path / "ruff.toml"
        config_file.write_text("[tool.ruff]\n")

        mock_result = Mock(returncode=0, stdout="[]", stderr="")
        call_args_list = []

        def side_effect(*args, **_kwargs):
            call_args_list.append(args)
            return mock_result

        monkeypatch.setattr(subprocess, "run", Mock(side_effect=side_effect))
        analyzer = RuffAnalyzer()
        analyzer.check_code("x = 1", str(config_file))
        assert "--config" in call_args_list[-1][0]

    def test_check_code_json_decode_error(self, monkeypatch):
        """Test check_code raises RuntimeError on malformed JSON output."""
        mock_init = Mock(returncode=0, stdout="", stderr="")
        mock_check = Mock(returncode=0, stdout="NOT JSON", stderr="")

        call_count = [0]

        def side_effect(*_args, **_kwargs):
            call_count[0] += 1
            return mock_init if call_count[0] == 1 else mock_check

        monkeypatch.setattr(subprocess, "run", Mock(side_effect=side_effect))
        analyzer = RuffAnalyzer()
        with pytest.raises(RuntimeError, match="Failed to parse RUFF output"):
            analyzer.check_code("code")

    def test_check_code_for_ci_bad_returncode(self, monkeypatch):
        """Test check_code_for_ci raises RuntimeError on bad returncode."""
        mock_init = Mock(returncode=0, stdout="", stderr="")
        mock_check = Mock(returncode=2, stdout="", stderr="ci error")

        call_count = [0]

        def side_effect(*_args, **_kwargs):
            call_count[0] += 1
            return mock_init if call_count[0] == 1 else mock_check

        monkeypatch.setattr(subprocess, "run", Mock(side_effect=side_effect))
        analyzer = RuffAnalyzer()
        with pytest.raises(RuntimeError, match="RUFF check failed"):
            analyzer.check_code_for_ci("code")

    def test_check_code_for_ci_with_config_path(self, monkeypatch, tmp_path):
        """Test check_code_for_ci passes config path to ruff."""
        config_file = tmp_path / "ruff.toml"
        config_file.write_text("")

        mock_result = Mock(returncode=0, stdout="[]", stderr="")
        call_args_list = []

        def side_effect(*args, **_kwargs):
            call_args_list.append(args)
            return mock_result

        monkeypatch.setattr(subprocess, "run", Mock(side_effect=side_effect))
        analyzer = RuffAnalyzer()
        analyzer.check_code_for_ci("x = 1", config_path=str(config_file))
        assert "--config" in call_args_list[-1][0]

    def test_format_code_bad_returncode(self, monkeypatch):
        """Test format_code raises RuntimeError on bad returncode."""
        mock_init = Mock(returncode=0, stdout="", stderr="")
        mock_format = Mock(returncode=1, stdout="", stderr="format error")

        call_count = [0]

        def side_effect(*_args, **_kwargs):
            call_count[0] += 1
            return mock_init if call_count[0] == 1 else mock_format

        monkeypatch.setattr(subprocess, "run", Mock(side_effect=side_effect))
        analyzer = RuffAnalyzer()
        with pytest.raises(RuntimeError, match="RUFF format failed"):
            analyzer.format_code("code")

    def test_format_code_with_config_path(self, monkeypatch, tmp_path):
        """Test format_code passes config path to ruff."""
        config_file = tmp_path / "ruff.toml"
        config_file.write_text("")

        mock_result = Mock(returncode=0, stdout="x = 1\n", stderr="")
        call_args_list = []

        def side_effect(*args, **_kwargs):
            call_args_list.append(args)
            return mock_result

        monkeypatch.setattr(subprocess, "run", Mock(side_effect=side_effect))
        analyzer = RuffAnalyzer()
        result = analyzer.format_code("x = 1", str(config_file))
        assert result.formatted_code == "x = 1\n"
        assert "--config" in call_args_list[-1][0]

    def test_get_severity_unknown_prefix(self, monkeypatch):
        """Test _get_severity falls back to warning for unknown rules."""
        mock_result = Mock(returncode=0, stdout="", stderr="")
        monkeypatch.setattr(subprocess, "run", Mock(return_value=mock_result))
        analyzer = RuffAnalyzer()
        assert analyzer._get_severity("ZZZ999") == "warning"

    def test_get_severity_info_rule(self, monkeypatch):
        """Test _get_severity returns info for refactoring rules."""
        mock_result = Mock(returncode=0, stdout="", stderr="")
        monkeypatch.setattr(subprocess, "run", Mock(return_value=mock_result))
        analyzer = RuffAnalyzer()
        assert analyzer._get_severity("I001") == "info"


class TestTyAnalyzerEdgeCases:
    """Tests for TyAnalyzer edge cases and error paths."""

    def test_init_fails_when_ty_not_found(self):
        """Test TyAnalyzer raises RuntimeError when ty binary is missing."""
        with (
            patch("subprocess.run", side_effect=FileNotFoundError("ty not found")),
            pytest.raises(RuntimeError, match="ty is not available"),
        ):
            TyAnalyzer()

    def test_init_fails_on_timeout(self):
        """Test TyAnalyzer raises RuntimeError on installation timeout."""
        with (
            patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired("ty", 10),
            ),
            pytest.raises(RuntimeError, match="ty is not available"),
        ):
            TyAnalyzer()

    def test_check_code_bad_returncode(self, monkeypatch):
        """Test check_code raises RuntimeError on unexpected exit code."""
        mock_init = Mock(returncode=0, stdout="", stderr="")
        mock_check = Mock(returncode=2, stdout="", stderr="ty error")

        call_count = [0]

        def side_effect(*_args, **_kwargs):
            call_count[0] += 1
            return mock_init if call_count[0] == 1 else mock_check

        monkeypatch.setattr(subprocess, "run", Mock(side_effect=side_effect))
        analyzer = TyAnalyzer()
        with pytest.raises(RuntimeError, match="ty check failed"):
            analyzer.check_code("code")

    def test_check_code_bad_returncode_uses_stdout(self, monkeypatch):
        """Test check_code uses stdout as error when stderr is empty."""
        mock_init = Mock(returncode=0, stdout="", stderr="")
        mock_check = Mock(returncode=2, stdout="error from stdout", stderr="")

        call_count = [0]

        def side_effect(*_args, **_kwargs):
            call_count[0] += 1
            return mock_init if call_count[0] == 1 else mock_check

        monkeypatch.setattr(subprocess, "run", Mock(side_effect=side_effect))
        analyzer = TyAnalyzer()
        with pytest.raises(RuntimeError, match="ty check failed"):
            analyzer.check_code("code")

    def test_check_code_bad_returncode_default_message(self, monkeypatch):
        """Test check_code uses default message when both stdout and stderr empty."""
        mock_init = Mock(returncode=0, stdout="", stderr="")
        mock_check = Mock(returncode=9, stdout="", stderr="")

        call_count = [0]

        def side_effect(*_args, **_kwargs):
            call_count[0] += 1
            return mock_init if call_count[0] == 1 else mock_check

        monkeypatch.setattr(subprocess, "run", Mock(side_effect=side_effect))
        analyzer = TyAnalyzer()
        with pytest.raises(RuntimeError, match="ty check failed"):
            analyzer.check_code("code")

    def test_parse_ty_output_filters_other_files(self, monkeypatch, tmp_path):
        """Test _parse_ty_output ignores diagnostics from other files."""
        mock_result = Mock(returncode=0, stdout="", stderr="")
        monkeypatch.setattr(subprocess, "run", Mock(return_value=mock_result))
        analyzer = TyAnalyzer()
        output = "/other/file.py:1:1: error[some-rule] some message\n"
        real_file = tmp_path / "myfile.py"
        result = analyzer._parse_ty_output(output, str(real_file))
        assert result == []

    def test_check_code_success(self, monkeypatch):
        """Test check_code returns TyCheckResult with no diagnostics on clean code."""
        mock_init = Mock(returncode=0, stdout="", stderr="")
        mock_check = Mock(returncode=0, stdout="", stderr="")
        call_count = [0]

        def side_effect(*_args, **_kwargs):
            call_count[0] += 1
            return mock_init if call_count[0] == 1 else mock_check

        monkeypatch.setattr(subprocess, "run", Mock(side_effect=side_effect))
        analyzer = TyAnalyzer()
        result = analyzer.check_code("x = 1")
        assert isinstance(result, TyCheckResult)
        assert result.total_diagnostics == 0

    def test_check_code_file_not_found(self, monkeypatch):
        """Test check_code raises RuntimeError when ty binary disappears at check time."""
        mock_init = Mock(returncode=0, stdout="", stderr="")
        call_count = [0]

        def side_effect(*_args, **_kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_init
            raise FileNotFoundError("ty not found")

        monkeypatch.setattr(subprocess, "run", Mock(side_effect=side_effect))
        analyzer = TyAnalyzer()
        with pytest.raises(RuntimeError, match="Failed to run ty"):
            analyzer.check_code("x = 1")

    def test_parse_ty_output_matching_line(self, monkeypatch, tmp_path):
        """Test _parse_ty_output appends a diagnostic when the file matches."""
        mock_result = Mock(returncode=0, stdout="", stderr="")
        monkeypatch.setattr(subprocess, "run", Mock(return_value=mock_result))
        analyzer = TyAnalyzer()
        real_file = tmp_path / "myfile.py"
        real_file.write_text("x: int = 'hello'\n")
        output = f"{real_file}:1:1: error[invalid-assignment] type mismatch\n"
        result = analyzer._parse_ty_output(output, str(real_file))
        assert len(result) == 1
        assert result[0].rule == "invalid-assignment"
        assert result[0].severity == "error"


class TestVultureAnalyzerEdgeCases:
    """Tests for VultureAnalyzer edge cases and error paths."""

    def test_init_fails_when_vulture_not_found(self):
        """Test VultureAnalyzer raises RuntimeError when vulture binary is missing."""
        with (
            patch("subprocess.run", side_effect=FileNotFoundError("vulture not found")),
            pytest.raises(RuntimeError, match="VULTURE is not available"),
        ):
            VultureAnalyzer()

    def test_init_fails_on_subprocess_error(self):
        """Test VultureAnalyzer raises RuntimeError on CalledProcessError."""
        with (
            patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(1, "vulture"),
            ),
            pytest.raises(RuntimeError, match="VULTURE is not available"),
        ):
            VultureAnalyzer()

    def test_init_fails_on_timeout(self):
        """Test VultureAnalyzer raises RuntimeError on installation timeout."""
        with (
            patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired("vulture", 10),
            ),
            pytest.raises(RuntimeError, match="VULTURE is not available"),
        ):
            VultureAnalyzer()

    def test_scan_code_invalid_confidence(self, monkeypatch):
        """Test scan_code raises ValueError for out-of-range confidence."""
        mock_result = Mock(returncode=0, stdout="", stderr="")
        monkeypatch.setattr(subprocess, "run", Mock(return_value=mock_result))
        analyzer = VultureAnalyzer()
        with pytest.raises(
            ValueError, match="min_confidence must be between 0 and 100"
        ):
            analyzer.scan_code("code", min_confidence=150)

    def test_scan_code_bad_returncode(self, monkeypatch):
        """Test scan_code raises RuntimeError on unexpected exit code."""
        mock_init = Mock(returncode=0, stdout="vulture 2.x\n", stderr="")
        mock_scan = Mock(returncode=2, stdout="", stderr="vulture error")

        call_count = [0]

        def side_effect(*_args, **_kwargs):
            call_count[0] += 1
            return mock_init if call_count[0] == 1 else mock_scan

        monkeypatch.setattr(subprocess, "run", Mock(side_effect=side_effect))
        analyzer = VultureAnalyzer()
        with pytest.raises(RuntimeError, match="VULTURE scan failed"):
            analyzer.scan_code("code")

    def test_scan_code_bad_returncode_empty_stderr(self, monkeypatch):
        """Test scan_code uses default message when stderr empty."""
        mock_init = Mock(returncode=0, stdout="vulture 2.x\n", stderr="")
        mock_scan = Mock(returncode=4, stdout="", stderr="")

        call_count = [0]

        def side_effect(*_args, **_kwargs):
            call_count[0] += 1
            return mock_init if call_count[0] == 1 else mock_scan

        monkeypatch.setattr(subprocess, "run", Mock(side_effect=side_effect))
        analyzer = VultureAnalyzer()
        with pytest.raises(RuntimeError, match="VULTURE scan failed"):
            analyzer.scan_code("code")

    def test_scan_code_empty_stdout(self, monkeypatch):
        """Test scan_code with no stdout returns empty results."""
        mock_init = Mock(returncode=0, stdout="vulture 2.x\n", stderr="")
        mock_scan = Mock(returncode=0, stdout="", stderr="")

        call_count = [0]

        def side_effect(*_args, **_kwargs):
            call_count[0] += 1
            return mock_init if call_count[0] == 1 else mock_scan

        monkeypatch.setattr(subprocess, "run", Mock(side_effect=side_effect))
        analyzer = VultureAnalyzer()
        result = analyzer.scan_code("x = 1")
        assert result.total_items == 0

    def test_scan_code_timeout(self, monkeypatch):
        """Test scan_code raises RuntimeError on timeout."""
        mock_init = Mock(returncode=0, stdout="vulture 2.x\n", stderr="")

        call_count = [0]

        def side_effect(*_args, **_kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_init
            raise subprocess.TimeoutExpired("vulture", 30)

        monkeypatch.setattr(subprocess, "run", Mock(side_effect=side_effect))
        analyzer = VultureAnalyzer()
        with pytest.raises(RuntimeError, match="VULTURE scan timed out"):
            analyzer.scan_code("code")

    def test_scan_code_file_not_found(self, monkeypatch):
        """Test scan_code raises RuntimeError on FileNotFoundError."""
        mock_init = Mock(returncode=0, stdout="vulture 2.x\n", stderr="")

        call_count = [0]

        def side_effect(*_args, **_kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_init
            raise FileNotFoundError("vulture not found")

        monkeypatch.setattr(subprocess, "run", Mock(side_effect=side_effect))
        analyzer = VultureAnalyzer()
        with pytest.raises(RuntimeError, match="Failed to run VULTURE"):
            analyzer.scan_code("code")

    def test_parse_vulture_output_filters_other_files(self, monkeypatch, tmp_path):
        """Test _parse_vulture_output ignores items from other files."""
        mock_result = Mock(returncode=0, stdout="vulture 2.x\n", stderr="")
        monkeypatch.setattr(subprocess, "run", Mock(return_value=mock_result))
        analyzer = VultureAnalyzer()
        output = "/other/file.py:10: unused variable 'x' (90% confidence)\n"
        real_file = tmp_path / "myfile.py"
        result = analyzer._parse_vulture_output(output, str(real_file))
        assert result == []

    def test_extract_item_info_quoted_fallback(self, monkeypatch):
        """Test _extract_item_info uses quoted name when no specific pattern matches."""
        mock_result = Mock(returncode=0, stdout="vulture 2.x\n", stderr="")
        monkeypatch.setattr(subprocess, "run", Mock(return_value=mock_result))
        analyzer = VultureAnalyzer()
        name, item_type = analyzer._extract_item_info("some 'my_name' thing")
        assert name == "my_name"
        assert item_type == "unknown"

    def test_extract_item_info_word_fallback(self, monkeypatch):
        """Test _extract_item_info uses first word when no quotes."""
        mock_result = Mock(returncode=0, stdout="vulture 2.x\n", stderr="")
        monkeypatch.setattr(subprocess, "run", Mock(return_value=mock_result))
        analyzer = VultureAnalyzer()
        name, item_type = analyzer._extract_item_info("somename without quotes")
        assert name == "somename"
        assert item_type == "unknown"

    def test_extract_item_info_empty_message(self, monkeypatch):
        """Test _extract_item_info handles empty message."""
        mock_result = Mock(returncode=0, stdout="vulture 2.x\n", stderr="")
        monkeypatch.setattr(subprocess, "run", Mock(return_value=mock_result))
        analyzer = VultureAnalyzer()
        name, item_type = analyzer._extract_item_info("")
        assert name == "unknown"
        assert item_type == "unknown"

    def test_parse_vulture_output_empty_line(self, monkeypatch, tmp_path):
        """Test _parse_vulture_output skips empty lines without raising."""
        mock_result = Mock(returncode=0, stdout="vulture 2.x\n", stderr="")
        monkeypatch.setattr(subprocess, "run", Mock(return_value=mock_result))
        analyzer = VultureAnalyzer()
        real_file = tmp_path / "myfile.py"
        result = analyzer._parse_vulture_output("\n\n   \n", str(real_file))
        assert result == []


class TestAnalyzeCodeHelpers:
    """Tests for private helper functions in server.py analyze_code."""

    def test_get_ty_result_with_available_analyzer(self, monkeypatch):
        """Test _get_ty_result delegates to ty_analyzer when available."""
        mock_ty = Mock()
        mock_ty.check_code.return_value = TyCheckResult(
            diagnostics=[], total_diagnostics=0, error_count=0, warning_count=0
        )
        monkeypatch.setattr(server, "ty_available", True)
        monkeypatch.setattr(server, "ty_analyzer", mock_ty)
        result = server._get_ty_result("x = 1", None)
        assert isinstance(result, TyCheckResult)
        assert result.total_diagnostics == 0

    def test_get_vulture_result_with_available_analyzer(self, monkeypatch):
        """Test _get_vulture_result delegates to vulture_analyzer when available."""
        mock_vulture = Mock()
        mock_vulture.scan_code.return_value = VultureScanResult(
            unused_items=[], total_items=0, high_confidence_items=0
        )
        monkeypatch.setattr(server, "vulture_available", True)
        monkeypatch.setattr(server, "vulture_analyzer", mock_vulture)
        result = server._get_vulture_result("x = 1", 80)
        assert isinstance(result, VultureScanResult)
        assert result.total_items == 0

    def test_analyze_code_propagates_tool_error(self, monkeypatch):
        """Test analyze_code re-raises ToolError without wrapping in 'Code analysis failed'."""
        monkeypatch.setattr(
            server, "_get_ruff_result", Mock(side_effect=ToolError("inner error"))
        )
        fn = _get_fn(server.analyze_code)
        with pytest.raises(ToolError, match="inner error"):
            fn("x = 1")


class TestBiomeNullAnalyzerGuards:
    """Tests for null biome analyzer type guards in tool functions."""

    def test_biome_check_null_analyzer(self, monkeypatch):
        """Test biome_check raises ToolError when analyzer is None."""
        monkeypatch.setattr(server, "biome_available", True)
        monkeypatch.setattr(server, "biome_analyzer", None)
        fn = _get_fn(server.biome_check)
        with pytest.raises(ToolError, match="not available"):
            fn("const x = 1;\n")

    def test_biome_format_null_analyzer(self, monkeypatch):
        """Test biome_format raises ToolError when analyzer is None."""
        monkeypatch.setattr(server, "biome_available", True)
        monkeypatch.setattr(server, "biome_analyzer", None)
        fn = _get_fn(server.biome_format)
        with pytest.raises(ToolError, match="not available"):
            fn("const x = 1;\n")
