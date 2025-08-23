"""Tests for command line interface and main entry points."""

import sys
from unittest.mock import patch

import pytest


class TestMainEntryPoints:
    """Test main entry points and CLI functionality."""

    def test_main_module_import(self) -> None:
        """Test __main__ module can be imported."""
        try:
            import mcp_server_analyzer.__main__
            assert True
        except ImportError:
            assert False, "__main__ module should be importable"

    def test_main_function_exists(self) -> None:
        """Test main function exists and is callable."""
        from mcp_server_analyzer.server import main
        
        assert callable(main)

    def test_main_function_keyboard_interrupt(self) -> None:
        """Test main function handles KeyboardInterrupt gracefully."""
        from mcp_server_analyzer.server import main
        
        with patch("mcp_server_analyzer.server.app.run", side_effect=KeyboardInterrupt()):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_function_exception_handling(self) -> None:
        """Test main function handles exceptions with proper exit codes."""
        from mcp_server_analyzer.server import main
        
        with patch("mcp_server_analyzer.server.app.run", side_effect=RuntimeError("Test error")):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_package_as_module_execution(self) -> None:
        """Test package can be executed as module."""
        # This would test: python -m mcp_server_analyzer
        from mcp_server_analyzer.__main__ import main
        
        # Verify the main from __main__ is the same as server.main
        from mcp_server_analyzer.server import main as server_main
        assert main is server_main

    def test_script_entry_point_availability(self) -> None:
        """Test that script entry point is defined in the package."""
        # This tests the console_scripts entry point from pyproject.toml
        # We can't easily test the actual script execution, but we can verify
        # the main function is accessible
        from mcp_server_analyzer.server import main
        
        assert main is not None
        assert callable(main)


class TestLoggingConfiguration:
    """Test logging setup and configuration."""

    def test_logging_is_configured(self) -> None:
        """Test that logging is properly configured."""
        import logging
        import mcp_server_analyzer.server
        
        # Server should have a logger
        assert hasattr(mcp_server_analyzer.server, "logger")
        logger = mcp_server_analyzer.server.logger
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "mcp_server_analyzer.server"

    def test_logging_level_configuration(self) -> None:
        """Test logging level is set appropriately."""
        import mcp_server_analyzer.server
        
        logger = mcp_server_analyzer.server.logger
        # Should be configured at INFO level or higher
        assert logger.level <= logging.INFO or logger.getEffectiveLevel() <= logging.INFO


class TestServerApplicationSetup:
    """Test FastMCP server application setup."""

    def test_fastmcp_app_instance(self) -> None:
        """Test FastMCP app is properly instantiated."""
        from mcp_server_analyzer.server import app
        
        assert app is not None
        # FastMCP apps should have these methods
        assert hasattr(app, "run")

    def test_analyzer_initialization_state(self) -> None:
        """Test analyzer initialization states."""
        import mcp_server_analyzer.server as server
        
        # RUFF analyzer should always be available
        assert server.ruff_analyzer is not None
        
        # VULTURE availability should be tracked
        assert hasattr(server, "vulture_available")
        assert isinstance(server.vulture_available, bool)
        
        if server.vulture_available:
            assert server.vulture_analyzer is not None
        else:
            assert server.vulture_analyzer is None


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery mechanisms."""

    def test_server_graceful_degradation(self) -> None:
        """Test server works even if VULTURE is unavailable."""
        # This tests the try/except block in server initialization
        with patch("mcp_server_analyzer.analyzers.VultureAnalyzer", side_effect=RuntimeError("VULTURE not found")):
            # Reload the server module to test initialization
            import importlib
            import mcp_server_analyzer.server
            
            importlib.reload(mcp_server_analyzer.server)
            
            # Server should still be functional
            assert mcp_server_analyzer.server.ruff_analyzer is not None
            assert mcp_server_analyzer.server.vulture_available is False
            assert mcp_server_analyzer.server.vulture_analyzer is None

    def test_individual_tool_error_handling(self) -> None:
        """Test individual tools handle errors gracefully."""
        from mcp_server_analyzer.server import ruff_check, vulture_scan
        
        # Test RUFF check error handling
        with patch("mcp_server_analyzer.server.ruff_analyzer.check_code", side_effect=Exception("Test error")):
            result = ruff_check("test code")
            assert "error" in result
            assert "RUFF check failed" in result["error"]

        # Test VULTURE scan when not available
        with patch("mcp_server_analyzer.server.vulture_available", False):
            result = vulture_scan("test code")
            assert "error" in result
            assert "VULTURE is not available" in result["error"]


class TestEnvironmentAdaptation:
    """Test adaptation to different environments."""

    def test_import_error_handling(self) -> None:
        """Test handling of import errors for optional dependencies."""
        # This is already tested in the server initialization,
        # but we can verify the pattern is followed
        import mcp_server_analyzer.server as server
        
        # The server should handle missing VULTURE gracefully
        assert hasattr(server, "vulture_available")
        
        # If VULTURE is available, it should be properly initialized
        if server.vulture_available:
            assert server.vulture_analyzer is not None
            # Test that we can call VULTURE functions
            from mcp_server_analyzer.server import vulture_scan
            # vulture_scan should work (we don't call it to avoid dependency issues)
            assert callable(vulture_scan)

    def test_cross_platform_compatibility(self) -> None:
        """Test basic cross-platform compatibility."""
        # Test that basic functionality works regardless of platform
        from mcp_server_analyzer.server import _calculate_quality_score
        from mcp_server_analyzer.models import RuffCheckResult, VultureScanResult
        
        # This should work on any platform
        ruff_result = RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)
        vulture_result = VultureScanResult(unused_items=[], total_items=0, high_confidence_items=0)
        
        score = _calculate_quality_score(ruff_result, vulture_result)
        assert isinstance(score, int)
        assert 0 <= score <= 100


class TestConfigurationHandling:
    """Test configuration file and parameter handling."""

    def test_default_parameter_values(self) -> None:
        """Test that functions use appropriate default values."""
        from mcp_server_analyzer.server import vulture_scan, ruff_check
        
        # These should work with defaults (mocked)
        with patch("mcp_server_analyzer.server.vulture_available", True):
            with patch("mcp_server_analyzer.server.vulture_analyzer") as mock_vulture:
                with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_ruff:
                    from mcp_server_analyzer.models import VultureScanResult, RuffCheckResult
                    
                    mock_vulture.scan_code.return_value = VultureScanResult(
                        unused_items=[], total_items=0, high_confidence_items=0
                    )
                    mock_ruff.check_code.return_value = RuffCheckResult(
                        issues=[], total_issues=0, fixable_issues=0
                    )
                    
                    # Test default min_confidence for VULTURE
                    vulture_scan("test code")
                    mock_vulture.scan_code.assert_called_with("test code", 80)  # default min_confidence
                    
                    # Test default config_path for RUFF
                    ruff_check("test code")
                    mock_ruff.check_code.assert_called_with("test code", None)  # default config_path

    def test_parameter_validation(self) -> None:
        """Test parameter validation in server functions."""
        # Most parameter validation is done at the analyzer level,
        # but we can test that parameters are passed through correctly
        from mcp_server_analyzer.server import analyze_code
        
        with patch("mcp_server_analyzer.server.vulture_available", True):
            with patch("mcp_server_analyzer.server.vulture_analyzer") as mock_vulture:
                with patch("mcp_server_analyzer.server.ruff_analyzer") as mock_ruff:
                    from mcp_server_analyzer.models import VultureScanResult, RuffCheckResult
                    
                    mock_vulture.scan_code.return_value = VultureScanResult(
                        unused_items=[], total_items=0, high_confidence_items=0
                    )
                    mock_ruff.check_code.return_value = RuffCheckResult(
                        issues=[], total_issues=0, fixable_issues=0
                    )
                    
                    analyze_code("test", ruff_config_path="/test/path", min_confidence=95)
                    
                    # Verify parameters were passed correctly
                    mock_ruff.check_code.assert_called_with("test", "/test/path")
                    mock_vulture.scan_code.assert_called_with("test", 95)