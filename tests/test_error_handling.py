"""Error handling and edge case tests for server and analyzers."""

import subprocess
from typing import Any, cast
from unittest.mock import Mock

import pytest

from mcp_server_analyzer import server
from mcp_server_analyzer.analyzers.ruff import RuffAnalyzer
from mcp_server_analyzer.analyzers.ty import TyAnalyzer
from mcp_server_analyzer.models import RuffCheckResult


class TestServerToolsUnavailable:
    """Tests for tool functions when analyzers are unavailable."""

    def test_ruff_check_unavailable(self, monkeypatch):
        """Test ruff_check returns error when unavailable."""
        monkeypatch.setattr(server, "ruff_available", False)
        fn = cast(Any, server.ruff_check).fn
        result = fn("code")
        assert "error" in result
        assert "ruff is not available" in result["error"]

    def test_ruff_format_unavailable(self, monkeypatch):
        """Test ruff_format returns error when unavailable."""
        monkeypatch.setattr(server, "ruff_available", False)
        fn = cast(Any, server.ruff_format).fn
        result = fn("code")
        assert "error" in result
        assert result["changed"] is False

    def test_ruff_check_ci_unavailable(self, monkeypatch):
        """Test ruff_check_ci returns error when unavailable."""
        monkeypatch.setattr(server, "ruff_available", False)
        fn = cast(Any, server.ruff_check_ci).fn
        result = fn("code")
        assert "error" in result
        assert result["success"] is False

    def test_ty_check_unavailable(self, monkeypatch):
        """Test ty_check returns error when unavailable."""
        monkeypatch.setattr(server, "ty_available", False)
        fn = cast(Any, server.ty_check).fn
        result = fn("code")
        assert "error" in result
        assert "ty is not available" in result["error"]

    def test_vulture_scan_unavailable(self, monkeypatch):
        """Test vulture_scan returns error when unavailable."""
        monkeypatch.setattr(server, "vulture_available", False)
        fn = cast(Any, server.vulture_scan).fn
        result = fn("code")
        assert "error" in result
        assert "VULTURE is not available" in result["error"]


class TestServerToolsExceptions:
    """Tests for tool functions handling analyzer exceptions."""

    def test_ruff_check_exception(self, monkeypatch):
        """Test ruff_check handles analyzer exception."""
        mock_analyzer = Mock()
        mock_analyzer.check_code.side_effect = RuntimeError("Check failed")
        monkeypatch.setattr(server, "ruff_analyzer", mock_analyzer)
        monkeypatch.setattr(server, "ruff_available", True)

        fn = cast(Any, server.ruff_check).fn
        result = fn("code")
        assert "error" in result
        assert "RUFF check failed" in result["error"]

    def test_ruff_format_exception(self, monkeypatch):
        """Test ruff_format handles analyzer exception."""
        mock_analyzer = Mock()
        mock_analyzer.format_code.side_effect = RuntimeError("Format failed")
        monkeypatch.setattr(server, "ruff_analyzer", mock_analyzer)
        monkeypatch.setattr(server, "ruff_available", True)

        fn = cast(Any, server.ruff_format).fn
        result = fn("code")
        assert "error" in result
        assert "RUFF format failed" in result["error"]

    def test_ruff_check_ci_exception(self, monkeypatch):
        """Test ruff_check_ci handles analyzer exception."""
        mock_analyzer = Mock()
        mock_analyzer.check_code_for_ci.side_effect = RuntimeError("CI check failed")
        monkeypatch.setattr(server, "ruff_analyzer", mock_analyzer)
        monkeypatch.setattr(server, "ruff_available", True)

        fn = cast(Any, server.ruff_check_ci).fn
        result = fn("code")
        assert "error" in result
        assert "RUFF CI check failed" in result["error"]

    def test_ty_check_exception(self, monkeypatch):
        """Test ty_check handles analyzer exception."""
        mock_analyzer = Mock()
        mock_analyzer.check_code.side_effect = RuntimeError("Type check failed")
        monkeypatch.setattr(server, "ty_analyzer", mock_analyzer)
        monkeypatch.setattr(server, "ty_available", True)

        fn = cast(Any, server.ty_check).fn
        result = fn("code")
        assert "error" in result
        assert "ty check failed" in result["error"]

    def test_vulture_scan_exception(self, monkeypatch):
        """Test vulture_scan handles analyzer exception."""
        mock_analyzer = Mock()
        mock_analyzer.scan_code.side_effect = RuntimeError("Scan failed")
        monkeypatch.setattr(server, "vulture_analyzer", mock_analyzer)
        monkeypatch.setattr(server, "vulture_available", True)

        fn = cast(Any, server.vulture_scan).fn
        result = fn("code")
        assert "error" in result
        assert "VULTURE scan failed" in result["error"]


class TestAnalyzeCodeErrorPaths:
    """Tests for analyze_code error handling."""

    def test_analyze_code_all_unavailable(self, monkeypatch):
        """Test analyze_code when all analyzers unavailable."""
        monkeypatch.setattr(server, "ruff_available", False)
        monkeypatch.setattr(server, "ty_available", False)
        monkeypatch.setattr(server, "vulture_available", False)

        fn = cast(Any, server.analyze_code).fn
        result = fn("code")
        assert "summary" in result
        assert result["summary"]["total_ruff_issues"] == 0

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

        fn = cast(Any, server.analyze_code).fn
        result = fn("code")
        assert result["summary"]["total_ruff_issues"] == 3

    def test_analyze_code_exception(self, monkeypatch):
        """Test analyze_code handles analyzer exception."""
        mock_ruff = Mock()
        mock_ruff.check_code.side_effect = RuntimeError("Failed")
        monkeypatch.setattr(server, "ruff_analyzer", mock_ruff)
        monkeypatch.setattr(server, "ruff_available", True)

        fn = cast(Any, server.analyze_code).fn
        result = fn("code")
        assert "error" in result
        assert "Code analysis failed" in result["error"]


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
