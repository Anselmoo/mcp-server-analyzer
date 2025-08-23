"""Comprehensive tests for VultureAnalyzer."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_server_analyzer.analyzers.vulture import VultureAnalyzer
from mcp_server_analyzer.models import VultureScanResult


class TestVultureAnalyzer:
    """Test VultureAnalyzer functionality."""

    def test_init_success(self) -> None:
        """Test successful VultureAnalyzer initialization."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            assert analyzer is not None
            mock_run.assert_called_once()

    def test_init_failure_not_installed(self) -> None:
        """Test VultureAnalyzer initialization when VULTURE is not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError("vulture not found")):
            with pytest.raises(RuntimeError, match="VULTURE is not available"):
                VultureAnalyzer()

    def test_init_failure_timeout(self) -> None:
        """Test VultureAnalyzer initialization with timeout."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("vulture", 10)):
            with pytest.raises(RuntimeError, match="VULTURE is not available"):
                VultureAnalyzer()

    def test_init_failure_bad_returncode(self) -> None:
        """Test VultureAnalyzer initialization with bad return code."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "Version check failed"
            with pytest.raises(RuntimeError, match="VULTURE is not properly installed"):
                VultureAnalyzer()

    def test_scan_code_no_issues(self) -> None:
        """Test scan_code with clean code (no unused items)."""
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            # Mock scan command with no output (no unused items)
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            result = analyzer.scan_code("print('hello world')")
            
            assert isinstance(result, VultureScanResult)
            assert result.total_items == 0
            assert result.high_confidence_items == 0
            assert len(result.unused_items) == 0

    def test_scan_code_with_unused_items(self) -> None:
        """Test scan_code with code that has unused items."""
        mock_vulture_output = """/tmp/test.py:1: unused import 'os' (90% confidence)
/tmp/test.py:3: unused function 'unused_func' (85% confidence, 3 lines)
/tmp/test.py:7: unused variable 'unused_var' (60% confidence)"""
        
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            # Mock scan command with unused items (exit code 3 = dead code found)
            mock_run.return_value = MagicMock(
                returncode=3,
                stdout=mock_vulture_output,
                stderr=""
            )
            
            with patch("pathlib.Path.resolve") as mock_resolve:
                mock_resolve.return_value = Path("/tmp/test.py")
                
                result = analyzer.scan_code("import os\n\ndef unused_func():\n    return 1\n\nunused_var = 42")
                
                assert result.total_items == 3
                assert result.high_confidence_items == 2  # >= 80% confidence
                assert len(result.unused_items) == 3
                
                # Check first item (import)
                item1 = result.unused_items[0]
                assert item1.name == "os"
                assert item1.type == "import"
                assert item1.line == 1
                assert item1.confidence == 90
                assert "unused import 'os'" in item1.message
                
                # Check second item (function)
                item2 = result.unused_items[1]
                assert item2.name == "unused_func"
                assert item2.type == "function"
                assert item2.line == 3
                assert item2.confidence == 85
                
                # Check third item (variable)
                item3 = result.unused_items[2]
                assert item3.name == "unused_var"
                assert item3.type == "variable"
                assert item3.line == 7
                assert item3.confidence == 60

    def test_scan_code_confidence_filtering(self) -> None:
        """Test scan_code with minimum confidence filtering."""
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            # Mock scan command
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            analyzer.scan_code("print('hello')", min_confidence=90)
            
            # Verify min_confidence was passed to command
            call_args = mock_run.call_args_list[-1]
            assert "--min-confidence=90" in call_args[0][0]

    def test_scan_code_invalid_confidence(self) -> None:
        """Test scan_code with invalid confidence values."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            # Test confidence below 0
            with pytest.raises(ValueError, match="min_confidence must be between 0 and 100"):
                analyzer.scan_code("print('hello')", min_confidence=-1)
            
            # Test confidence above 100
            with pytest.raises(ValueError, match="min_confidence must be between 0 and 100"):
                analyzer.scan_code("print('hello')", min_confidence=101)

    def test_scan_code_with_config_file(self) -> None:
        """Test scan_code with pyproject.toml configuration."""
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            # Mock scan command and config file existence
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.cwd", return_value=Path("/project")):
                    analyzer.scan_code("print('hello')")
                    
                    # Verify config was passed to command
                    call_args = mock_run.call_args_list[-1]
                    assert "--config" in call_args[0][0]
                    assert "/project/pyproject.toml" in call_args[0][0]

    def test_scan_code_without_config_file(self) -> None:
        """Test scan_code without pyproject.toml configuration."""
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            # Mock scan command
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            with patch("pathlib.Path.exists", return_value=False):
                analyzer.scan_code("print('hello')")
                
                # Verify config was NOT passed to command
                call_args = mock_run.call_args_list[-1]
                assert "--config" not in call_args[0][0]

    def test_scan_code_failure(self) -> None:
        """Test scan_code when VULTURE command fails."""
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            # Mock scan command failure (exit code 2 = invalid arguments)
            mock_run.return_value = MagicMock(
                returncode=2,
                stdout="",
                stderr="Invalid command line arguments"
            )
            
            with pytest.raises(RuntimeError, match="VULTURE scan failed"):
                analyzer.scan_code("print('hello')")

    def test_scan_code_timeout(self) -> None:
        """Test scan_code when VULTURE command times out."""
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            # Mock scan command timeout
            mock_run.side_effect = [
                MagicMock(returncode=0),  # version check
                subprocess.TimeoutExpired("vulture", 30)  # scan command
            ]
            
            with pytest.raises(RuntimeError, match="VULTURE scan timed out"):
                analyzer.scan_code("print('hello')")

    def test_scan_code_syntax_error(self) -> None:
        """Test scan_code with invalid Python syntax."""
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            # Mock scan command - syntax error (exit code 1)
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Syntax error in input file"
            )
            
            with pytest.raises(RuntimeError, match="VULTURE scan failed"):
                analyzer.scan_code("invalid python syntax !!!")

    def test_parse_vulture_output_various_patterns(self) -> None:
        """Test parsing of various VULTURE output patterns."""
        test_outputs = [
            ("/tmp/test.py:1: unused import 'os' (90% confidence)", "os", "import"),
            ("/tmp/test.py:5: unused function 'func_name' (85% confidence, 3 lines)", "func_name", "function"),
            ("/tmp/test.py:10: unused method 'method_name' (80% confidence)", "method_name", "method"),
            ("/tmp/test.py:15: unused class 'ClassName' (75% confidence)", "ClassName", "class"),
            ("/tmp/test.py:20: unused variable 'var_name' (70% confidence)", "var_name", "variable"),
            ("/tmp/test.py:25: unused attribute 'attr_name' (65% confidence)", "attr_name", "attribute"),
            ("/tmp/test.py:30: unused property 'prop_name' (60% confidence)", "prop_name", "property"),
            ("/tmp/test.py:35: unused argument 'arg_name' (95% confidence)", "arg_name", "argument"),
        ]
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            for output_line, expected_name, expected_type in test_outputs:
                items = analyzer._parse_vulture_output(output_line, "/tmp/test.py")
                assert len(items) == 1
                item = items[0]
                assert item.name == expected_name
                assert item.type == expected_type

    def test_parse_vulture_output_unknown_pattern(self) -> None:
        """Test parsing of unknown VULTURE output patterns."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            # Test with unrecognized pattern but with quoted name
            output = "/tmp/test.py:1: some unknown message 'unknown_item' (80% confidence)"
            items = analyzer._parse_vulture_output(output, "/tmp/test.py")
            assert len(items) == 1
            assert items[0].name == "unknown_item"
            assert items[0].type == "unknown"
            
            # Test with completely unrecognized pattern
            output = "/tmp/test.py:1: completely unknown message format (80% confidence)"
            items = analyzer._parse_vulture_output(output, "/tmp/test.py")
            assert len(items) == 1
            assert items[0].name == "completely"  # First word
            assert items[0].type == "unknown"

    def test_parse_vulture_output_empty_lines(self) -> None:
        """Test parsing VULTURE output with empty lines."""
        output = """
        
/tmp/test.py:1: unused import 'os' (90% confidence)

/tmp/test.py:3: unused function 'func' (80% confidence)

        """
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            items = analyzer._parse_vulture_output(output, "/tmp/test.py")
            assert len(items) == 2  # Should ignore empty lines

    def test_parse_vulture_output_different_files(self) -> None:
        """Test parsing VULTURE output that filters out different files."""
        output = """/tmp/test.py:1: unused import 'os' (90% confidence)
/tmp/other.py:1: unused import 'sys' (85% confidence)
/tmp/test.py:3: unused function 'func' (80% confidence)"""
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            with patch("pathlib.Path.resolve") as mock_resolve:
                def resolve_side_effect(path):
                    return Path(str(path))  # Return the path as-is for comparison
                mock_resolve.side_effect = resolve_side_effect
                
                items = analyzer._parse_vulture_output(output, "/tmp/test.py")
                # Should only include items from /tmp/test.py
                assert len(items) == 2
                assert all(item.line in [1, 3] for item in items)

    def test_parse_vulture_output_malformed_lines(self) -> None:
        """Test parsing VULTURE output with malformed lines."""
        output = """malformed line without proper format
/tmp/test.py:1: unused import 'os' (90% confidence)
another malformed line
/tmp/test.py:3: unused function 'func' (80% confidence)
line without confidence percentage"""
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            with patch("pathlib.Path.resolve") as mock_resolve:
                mock_resolve.return_value = Path("/tmp/test.py")
                
                items = analyzer._parse_vulture_output(output, "/tmp/test.py")
                # Should only parse valid lines
                assert len(items) == 2

    def test_extract_item_info_edge_cases(self) -> None:
        """Test _extract_item_info with edge cases."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            # Test message with no quotes
            name, type_name = analyzer._extract_item_info("some message without quotes")
            assert name == "some"
            assert type_name == "unknown"
            
            # Test empty message
            name, type_name = analyzer._extract_item_info("")
            assert name == "unknown"
            assert type_name == "unknown"
            
            # Test message with multiple quoted items
            name, type_name = analyzer._extract_item_info("unused import 'first' and 'second' (90% confidence)")
            assert name == "first"  # Should extract first quoted item
            assert type_name == "import"

    def test_temp_file_cleanup(self) -> None:
        """Test that temporary files are properly cleaned up."""
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            # Mock successful scan
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            # Track created temp files
            original_tempfile = tempfile.NamedTemporaryFile
            created_files = []
            
            def track_tempfile(*args, **kwargs):
                tf = original_tempfile(*args, **kwargs)
                created_files.append(Path(tf.name))
                return tf
            
            with patch("tempfile.NamedTemporaryFile", track_tempfile):
                analyzer.scan_code("print('hello')")
            
            # Verify temp files were cleaned up
            for temp_file in created_files:
                assert not temp_file.exists()

    def test_temp_file_cleanup_on_exception(self) -> None:
        """Test that temporary files are cleaned up even when exceptions occur."""
        with patch("subprocess.run") as mock_run:
            # Mock version check
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            # Mock command that raises exception
            mock_run.side_effect = [
                MagicMock(returncode=0),  # version check
                RuntimeError("Test error")  # scan command
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
                    analyzer.scan_code("print('hello')")
            
            # Verify temp files were still cleaned up
            for temp_file in created_files:
                assert not temp_file.exists()


class TestVultureAnalyzerEdgeCases:
    """Test edge cases and error handling for VultureAnalyzer."""

    def test_empty_code(self) -> None:
        """Test analyzing empty code."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            result = analyzer.scan_code("")
            assert result.total_items == 0

    def test_whitespace_only_code(self) -> None:
        """Test analyzing whitespace-only code."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            result = analyzer.scan_code("   \n\n  \t  \n")
            assert result.total_items == 0

    def test_very_large_code_input(self) -> None:
        """Test handling of very large code inputs."""
        # Create a very large code string
        large_code = "# Comment\n" * 10000 + "print('hello')"
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            # Should handle large inputs without issues
            result = analyzer.scan_code(large_code)
            assert isinstance(result, VultureScanResult)

    def test_unicode_in_code(self) -> None:
        """Test handling of Unicode characters in code."""
        unicode_code = "# Тест with unicode 中文\nprint('hello 🌍')"
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            result = analyzer.scan_code(unicode_code)
            assert isinstance(result, VultureScanResult)

    def test_high_confidence_calculation(self) -> None:
        """Test high confidence items calculation with different confidence values."""
        mock_vulture_output = """/tmp/test.py:1: unused import 'a' (100% confidence)
/tmp/test.py:2: unused import 'b' (90% confidence)
/tmp/test.py:3: unused import 'c' (80% confidence)
/tmp/test.py:4: unused import 'd' (79% confidence)
/tmp/test.py:5: unused import 'e' (50% confidence)"""
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            mock_run.return_value = MagicMock(returncode=3, stdout=mock_vulture_output, stderr="")
            
            with patch("pathlib.Path.resolve", return_value=Path("/tmp/test.py")):
                result = analyzer.scan_code("code")
                
                # Should have 3 high confidence items (>=80%)
                assert result.total_items == 5
                assert result.high_confidence_items == 3

    def test_confidence_edge_cases(self) -> None:
        """Test confidence handling with edge cases."""
        test_cases = [
            ("(0% confidence)", 0),
            ("(1% confidence)", 1),
            ("(99% confidence)", 99),
            ("(100% confidence)", 100),
        ]
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            for confidence_text, expected_confidence in test_cases:
                output = f"/tmp/test.py:1: unused import 'test' {confidence_text}"
                items = analyzer._parse_vulture_output(output, "/tmp/test.py")
                assert len(items) == 1
                assert items[0].confidence == expected_confidence

    def test_macos_private_path_handling(self) -> None:
        """Test handling of macOS /private path prefixes."""
        mock_vulture_output = "/private/tmp/test.py:1: unused import 'os' (90% confidence)"
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            analyzer = VultureAnalyzer()
            
            mock_run.return_value = MagicMock(returncode=3, stdout=mock_vulture_output, stderr="")
            
            # Mock Path.resolve to simulate macOS path resolution
            with patch("pathlib.Path.resolve") as mock_resolve:
                mock_resolve.side_effect = lambda: Path("/private/tmp/test.py")
                
                result = analyzer.scan_code("import os")
                
                # Should properly handle the path resolution and include the item
                assert result.total_items == 1