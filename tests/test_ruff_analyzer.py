"""Comprehensive tests for RuffAnalyzer."""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_server_analyzer.analyzers.ruff import RuffAnalyzer
from mcp_server_analyzer.models import RuffCheckResult, RuffFormatResult


class TestRuffAnalyzer:
    """Test RuffAnalyzer functionality."""

    def test_init_success(self) -> None:
        """Test successful RuffAnalyzer initialization."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            assert analyzer is not None
            mock_run.assert_called_once()

    def test_init_failure_not_installed(self) -> None:
        """Test RuffAnalyzer initialization when RUFF is not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError("ruff not found")):
            with pytest.raises(RuntimeError, match="RUFF is not available"):
                RuffAnalyzer()

    def test_init_failure_bad_version(self) -> None:
        """Test RuffAnalyzer initialization with bad version check."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            with pytest.raises(RuntimeError, match="RUFF is not properly installed"):
                RuffAnalyzer()

    def test_check_code_no_issues(self) -> None:
        """Test check_code with clean code (no issues)."""
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            # Mock check command with no output (no issues)
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            result = analyzer.check_code("print('hello world')")
            
            assert isinstance(result, RuffCheckResult)
            assert result.total_issues == 0
            assert result.fixable_issues == 0
            assert len(result.issues) == 0

    def test_check_code_with_issues(self) -> None:
        """Test check_code with code that has issues."""
        mock_ruff_output = [
            {
                "location": {"row": 1, "column": 1},
                "end_location": {"row": 1, "column": 10},
                "code": "F401",
                "message": "'os' imported but unused",
                "fix": {"applicability": "safe"}
            },
            {
                "location": {"row": 2, "column": 1},
                "end_location": None,
                "code": "E302",
                "message": "expected 2 blank lines",
                "fix": {"applicability": "unsafe"}
            }
        ]
        
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            # Mock check command with issues
            mock_run.return_value = MagicMock(
                returncode=1,  # RUFF returns 1 when issues found
                stdout=json.dumps(mock_ruff_output),
                stderr=""
            )
            
            result = analyzer.check_code("import os\ndef func(): pass")
            
            assert result.total_issues == 2
            assert result.fixable_issues == 1  # Only first issue is safely fixable
            assert len(result.issues) == 2
            
            # Check first issue
            issue1 = result.issues[0]
            assert issue1.line == 1
            assert issue1.column == 1
            assert issue1.end_line == 1
            assert issue1.end_column == 10
            assert issue1.rule == "F401"
            assert issue1.message == "'os' imported but unused"
            assert issue1.fixable is True
            assert issue1.severity == "error"  # F-series rules are errors
            
            # Check second issue
            issue2 = result.issues[1]
            assert issue2.line == 2
            assert issue2.rule == "E302"
            assert issue2.fixable is False  # unsafe applicability
            assert issue2.end_line is None

    def test_check_code_invalid_json(self) -> None:
        """Test check_code with invalid JSON output."""
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            # Mock check command with invalid JSON
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="invalid json output",
                stderr=""
            )
            
            with pytest.raises(RuntimeError, match="Failed to parse RUFF output"):
                analyzer.check_code("import os")

    def test_check_code_failure(self) -> None:
        """Test check_code when RUFF command fails."""
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            # Mock check command failure
            mock_run.return_value = MagicMock(
                returncode=2,  # Unexpected error code
                stdout="",
                stderr="RUFF internal error"
            )
            
            with pytest.raises(RuntimeError, match="RUFF check failed"):
                analyzer.check_code("import os")

    def test_check_code_with_config(self) -> None:
        """Test check_code with custom configuration."""
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            # Mock check command
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            analyzer.check_code("print('hello')", config_path="/path/to/config.toml")
            
            # Verify config was passed to command
            call_args = mock_run.call_args_list[-1]
            assert "--config" in call_args[0][0]
            assert "/path/to/config.toml" in call_args[0][0]

    def test_check_code_for_ci_json_format(self) -> None:
        """Test check_code_for_ci with JSON format."""
        expected_output = '{"issues": []}'
        
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            # Mock CI check command
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=expected_output,
                stderr=""
            )
            
            result = analyzer.check_code_for_ci("print('hello')", output_format="json")
            
            assert result == expected_output
            
            # Verify correct format was used
            call_args = mock_run.call_args_list[-1]
            assert "--output-format=json" in call_args[0][0]

    def test_check_code_for_ci_other_formats(self) -> None:
        """Test check_code_for_ci with different output formats."""
        formats = ["github", "gitlab", "sarif"]
        
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            for fmt in formats:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout=f"output in {fmt} format",
                    stderr=""
                )
                
                result = analyzer.check_code_for_ci("print('hello')", output_format=fmt)
                assert result == f"output in {fmt} format"
                
                # Verify correct format was used
                call_args = mock_run.call_args_list[-1]
                assert f"--output-format={fmt}" in call_args[0][0]

    def test_format_code_no_changes(self) -> None:
        """Test format_code with already formatted code."""
        original_code = "print('hello world')"
        
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            # Mock format command - returns same code
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=original_code,
                stderr=""
            )
            
            result = analyzer.format_code(original_code)
            
            assert isinstance(result, RuffFormatResult)
            assert result.formatted_code == original_code
            assert result.changed is False

    def test_format_code_with_changes(self) -> None:
        """Test format_code with code that needs formatting."""
        original_code = "print( 'hello world' )"
        formatted_code = "print('hello world')"
        
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            # Mock format command - returns formatted code
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=formatted_code,
                stderr=""
            )
            
            result = analyzer.format_code(original_code)
            
            assert result.formatted_code == formatted_code
            assert result.changed is True

    def test_format_code_failure(self) -> None:
        """Test format_code when formatting fails."""
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            # Mock format command failure
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Syntax error in code"
            )
            
            with pytest.raises(RuntimeError, match="RUFF format failed"):
                analyzer.format_code("invalid python code !!!")

    def test_format_code_with_config(self) -> None:
        """Test format_code with custom configuration."""
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            # Mock format command
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="formatted code",
                stderr=""
            )
            
            analyzer.format_code("code", config_path="/path/to/config.toml")
            
            # Verify config was passed to command
            call_args = mock_run.call_args_list[-1]
            assert "--config" in call_args[0][0]
            assert "/path/to/config.toml" in call_args[0][0]

    def test_get_severity_mapping(self) -> None:
        """Test severity mapping for different rule codes."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            # Test error severity
            assert analyzer._get_severity("F401") == "error"
            assert analyzer._get_severity("E999") == "error"
            
            # Test warning severity
            assert analyzer._get_severity("W292") == "warning"
            assert analyzer._get_severity("E302") == "warning"
            assert analyzer._get_severity("C901") == "warning"
            assert analyzer._get_severity("N806") == "warning"
            assert analyzer._get_severity("B902") == "warning"
            assert analyzer._get_severity("A001") == "warning"
            assert analyzer._get_severity("C415") == "warning"
            
            # Test info severity
            assert analyzer._get_severity("I001") == "info"
            assert analyzer._get_severity("UP032") == "info"
            assert analyzer._get_severity("PIE810") == "info"
            assert analyzer._get_severity("T201") == "info"
            assert analyzer._get_severity("PT009") == "info"
            assert analyzer._get_severity("RET501") == "info"
            assert analyzer._get_severity("SIM108") == "info"
            assert analyzer._get_severity("TID252") == "info"
            assert analyzer._get_severity("ARG001") == "info"
            assert analyzer._get_severity("PLR0912") == "info"
            assert analyzer._get_severity("RUF001") == "info"
            
            # Test unknown rule (defaults to warning)
            assert analyzer._get_severity("UNKNOWN123") == "warning"

    def test_temp_file_cleanup(self) -> None:
        """Test that temporary files are properly cleaned up."""
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            # Mock successful check
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            # Track created temp files
            original_tempfile = tempfile.NamedTemporaryFile
            created_files = []
            
            def track_tempfile(*args, **kwargs):
                tf = original_tempfile(*args, **kwargs)
                created_files.append(Path(tf.name))
                return tf
            
            with patch("tempfile.NamedTemporaryFile", track_tempfile):
                analyzer.check_code("print('hello')")
            
            # Verify temp files were cleaned up
            for temp_file in created_files:
                assert not temp_file.exists()

    def test_temp_file_cleanup_on_exception(self) -> None:
        """Test that temporary files are cleaned up even when exceptions occur."""
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            # Mock command that raises exception
            mock_run.side_effect = [
                MagicMock(returncode=0),  # version check
                RuntimeError("Test error")  # check command
            ]
            
            # Track created temp files
            original_tempfile = tempfile.NamedTemporaryFile
            created_files = []
            
            def track_tempfile(*args, **kwargs):
                tf = original_tempfile(*args, **kwargs)
                created_files.append(Path(tf.name))
                return tf
            
            with patch("tempfile.NamedTemporaryFile", track_tempfile):
                with pytest.raises(RuntimeError):
                    analyzer.check_code("print('hello')")
            
            # Verify temp files were still cleaned up
            for temp_file in created_files:
                assert not temp_file.exists()


class TestRuffAnalyzerEdgeCases:
    """Test edge cases and error handling for RuffAnalyzer."""

    def test_empty_code(self) -> None:
        """Test analyzing empty code."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            result = analyzer.check_code("")
            assert result.total_issues == 0

    def test_whitespace_only_code(self) -> None:
        """Test analyzing whitespace-only code."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            result = analyzer.check_code("   \n\n  \t  \n")
            assert result.total_issues == 0

    def test_malformed_ruff_output(self) -> None:
        """Test handling of malformed RUFF output structures."""
        malformed_outputs = [
            [{"missing_required_fields": True}],  # Missing location, code, message
            [{"location": "not_a_dict", "code": "F401", "message": "test"}],  # Invalid location
            [{"location": {"row": "not_int"}, "code": "F401", "message": "test"}],  # Invalid row type
        ]
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            for malformed_output in malformed_outputs:
                mock_run.return_value = MagicMock(
                    returncode=1,
                    stdout=json.dumps(malformed_output),
                    stderr=""
                )
                
                # Should not raise exception, but handle gracefully or raise appropriate error
                try:
                    result = analyzer.check_code("import os")
                    # If it doesn't raise, should return valid result
                    assert isinstance(result, RuffCheckResult)
                except (RuntimeError, KeyError, TypeError, ValueError):
                    # Expected for malformed data
                    pass

    def test_very_large_code_input(self) -> None:
        """Test handling of very large code inputs."""
        # Create a very large code string
        large_code = "# Comment\n" * 10000 + "print('hello')"
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            # Should handle large inputs without issues
            result = analyzer.check_code(large_code)
            assert isinstance(result, RuffCheckResult)

    def test_unicode_in_code(self) -> None:
        """Test handling of Unicode characters in code."""
        unicode_code = "# Тест with unicode 中文\nprint('hello 🌍')"
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = RuffAnalyzer()
            
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            result = analyzer.check_code(unicode_code)
            assert isinstance(result, RuffCheckResult)