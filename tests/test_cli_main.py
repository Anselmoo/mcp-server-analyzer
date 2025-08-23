"""Enhanced tests for CLI and main entry points."""


def test_main_module_import():
    """Test __main__ module can be imported."""
    try:
        import mcp_server_analyzer.__main__
        assert True
    except ImportError as e:
        assert False, f"__main__ module should be importable: {e}"


def test_main_function_exists():
    """Test main function exists and is callable."""
    from mcp_server_analyzer.server import main

    assert callable(main)


def test_package_as_module_execution():
    """Test package can be executed as module."""
    # This would test: python -m mcp_server_analyzer
    try:
        from mcp_server_analyzer.__main__ import main

        # Verify the main from __main__ is accessible
        from mcp_server_analyzer.server import main as server_main
        assert main is server_main
    except ImportError as e:
        assert False, f"Module execution import failed: {e}"


def test_script_entry_point_availability():
    """Test that script entry point is defined in the package."""
    # This tests the console_scripts entry point from pyproject.toml
    # We can't easily test the actual script execution, but we can verify
    # the main function is accessible
    from mcp_server_analyzer.server import main

    assert main is not None
    assert callable(main)


def test_logging_is_configured():
    """Test that logging is properly configured."""
    import logging

    try:
        import mcp_server_analyzer.server

        # Server should have a logger
        assert hasattr(mcp_server_analyzer.server, "logger")
        logger = mcp_server_analyzer.server.logger

        assert isinstance(logger, logging.Logger)
        assert logger.name == "mcp_server_analyzer.server"
    except Exception as e:
        assert False, f"Logging configuration test failed: {e}"


def test_fastmcp_app_instance():
    """Test FastMCP app is properly instantiated."""
    try:
        from mcp_server_analyzer.server import app

        assert app is not None
        # FastMCP apps should have these methods
        assert hasattr(app, "run")
    except Exception as e:
        assert False, f"FastMCP app test failed: {e}"


def test_analyzer_initialization_state():
    """Test analyzer initialization states."""
    try:
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

    except Exception as e:
        assert False, f"Analyzer initialization test failed: {e}"


def test_quality_score_function():
    """Test quality score calculation function exists and works."""
    try:
        from mcp_server_analyzer.server import _calculate_quality_score
        from mcp_server_analyzer.models import RuffCheckResult, VultureScanResult

        # This should work on any platform
        ruff_result = RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)
        vulture_result = VultureScanResult(unused_items=[], total_items=0, high_confidence_items=0)

        score = _calculate_quality_score(ruff_result, vulture_result)
        assert isinstance(score, int)
        assert 0 <= score <= 100

    except Exception as e:
        assert False, f"Quality score function test failed: {e}"


def test_server_tools_exist():
    """Test that all expected server tools exist."""
    expected_tools = ["ruff_check", "ruff_format", "vulture_scan", "analyze_code"]

    try:
        import mcp_server_analyzer.server as server

        for tool_name in expected_tools:
            assert hasattr(server, tool_name), f"Tool {tool_name} not found"
            tool = getattr(server, tool_name)
            assert callable(tool), f"Tool {tool_name} is not callable"

    except Exception as e:
        assert False, f"Server tools test failed: {e}"


def test_basic_imports():
    """Test that all basic imports work without errors."""
    try:
        # Test basic server imports
        from mcp_server_analyzer.server import app, main, logger
        from mcp_server_analyzer.models import RuffIssue, VultureItem
        from mcp_server_analyzer.analyzers import RuffAnalyzer, VultureAnalyzer

        assert all(
            x is not None
            for x in [app, main, logger, RuffIssue, VultureItem, RuffAnalyzer]
        )

    except Exception as e:
        assert False, f"Basic imports test failed: {e}"