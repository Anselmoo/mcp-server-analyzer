"""Tests for package initialization and imports."""


class TestPackageImports:
    """Test package-level imports and initialization."""

    def test_main_package_imports(self) -> None:
        """Test main package can be imported with metadata."""
        import mcp_server_analyzer
        
        assert hasattr(mcp_server_analyzer, "__version__")
        assert hasattr(mcp_server_analyzer, "__author__")
        assert hasattr(mcp_server_analyzer, "__email__")
        assert mcp_server_analyzer.__version__ == "0.1.2"
        assert mcp_server_analyzer.__author__ == "Anselm Hahn"

    def test_analyzers_package_imports(self) -> None:
        """Test analyzers package imports work correctly."""
        from mcp_server_analyzer.analyzers import RuffAnalyzer, VultureAnalyzer
        
        assert RuffAnalyzer is not None
        assert VultureAnalyzer is not None
        
        # Test __all__ export
        import mcp_server_analyzer.analyzers as analyzers_pkg
        assert "RuffAnalyzer" in analyzers_pkg.__all__
        assert "VultureAnalyzer" in analyzers_pkg.__all__

    def test_models_imports(self) -> None:
        """Test that all models can be imported."""
        from mcp_server_analyzer.models import (
            AnalysisResult,
            RuffCheckResult,
            RuffFormatResult,
            RuffIssue,
            VultureItem,
            VultureScanResult,
        )
        
        # Verify all models are available
        models = [
            RuffIssue, RuffCheckResult, RuffFormatResult,
            VultureItem, VultureScanResult, AnalysisResult
        ]
        
        for model in models:
            assert model is not None
            # Verify they are Pydantic models
            assert hasattr(model, "model_validate")
            assert hasattr(model, "model_dump")

    def test_server_module_imports(self) -> None:
        """Test server module can be imported."""
        # This should work without errors
        import mcp_server_analyzer.server
        
        assert hasattr(mcp_server_analyzer.server, "app")
        assert hasattr(mcp_server_analyzer.server, "main")
        assert hasattr(mcp_server_analyzer.server, "_calculate_quality_score")

    def test_main_module_executable(self) -> None:
        """Test __main__ module can be imported."""
        # This tests that the package can be run with python -m
        try:
            import mcp_server_analyzer.__main__
            # If it imports without error, it's good
            assert True
        except ImportError:
            # If __main__.py doesn't exist or has issues
            assert False, "Failed to import __main__ module"


class TestAnalyzerInstantiation:
    """Test analyzer classes can be instantiated (with mocking)."""

    def test_ruff_analyzer_class_structure(self) -> None:
        """Test RuffAnalyzer class structure."""
        from mcp_server_analyzer.analyzers.ruff import RuffAnalyzer
        
        # Test class has expected methods
        expected_methods = [
            "check_code", "check_code_for_ci", "format_code", "_get_severity"
        ]
        
        for method in expected_methods:
            assert hasattr(RuffAnalyzer, method)
            assert callable(getattr(RuffAnalyzer, method))

    def test_vulture_analyzer_class_structure(self) -> None:
        """Test VultureAnalyzer class structure.""" 
        from mcp_server_analyzer.analyzers.vulture import VultureAnalyzer
        
        # Test class has expected methods
        expected_methods = [
            "scan_code", "_parse_vulture_output", "_extract_item_info"
        ]
        
        for method in expected_methods:
            assert hasattr(VultureAnalyzer, method)
            assert callable(getattr(VultureAnalyzer, method))

    def test_analyzer_error_states(self) -> None:
        """Test analyzers handle error states appropriately."""
        from unittest.mock import patch
        
        # Test RuffAnalyzer with failed initialization
        with patch("subprocess.run", side_effect=FileNotFoundError("ruff not found")):
            from mcp_server_analyzer.analyzers.ruff import RuffAnalyzer
            try:
                RuffAnalyzer()
                assert False, "Should have raised RuntimeError"
            except RuntimeError as e:
                assert "RUFF is not available" in str(e)

        # Test VultureAnalyzer with failed initialization  
        with patch("subprocess.run", side_effect=FileNotFoundError("vulture not found")):
            from mcp_server_analyzer.analyzers.vulture import VultureAnalyzer
            try:
                VultureAnalyzer()
                assert False, "Should have raised RuntimeError"
            except RuntimeError as e:
                assert "VULTURE is not available" in str(e)


class TestModelValidation:
    """Test model validation and edge cases."""

    def test_model_field_types(self) -> None:
        """Test that model fields have correct types."""
        from mcp_server_analyzer.models import RuffIssue, VultureItem
        
        # Test RuffIssue field annotations
        annotations = RuffIssue.__annotations__
        assert annotations["line"] == int
        assert annotations["column"] == int
        assert annotations["rule"] == str
        assert annotations["message"] == str
        assert annotations["severity"] == str
        assert annotations["fixable"] == bool
        
        # Test VultureItem field annotations
        v_annotations = VultureItem.__annotations__
        assert v_annotations["name"] == str
        assert v_annotations["type"] == str
        assert v_annotations["line"] == int
        assert v_annotations["column"] == int
        assert v_annotations["confidence"] == int
        assert v_annotations["message"] == str

    def test_model_defaults(self) -> None:
        """Test model default values."""
        from mcp_server_analyzer.models import RuffIssue
        
        issue = RuffIssue(
            line=1, column=1, rule="F401", message="test", severity="error"
        )
        
        # Test defaults
        assert issue.fixable is False
        assert issue.end_line is None
        assert issue.end_column is None

    def test_model_serialization_roundtrip(self) -> None:
        """Test model serialization and deserialization."""
        from mcp_server_analyzer.models import AnalysisResult, RuffCheckResult, VultureScanResult
        
        # Create a complex analysis result
        ruff_result = RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)
        vulture_result = VultureScanResult(unused_items=[], total_items=0, high_confidence_items=0)
        
        original = AnalysisResult(
            ruff_result=ruff_result,
            vulture_result=vulture_result,
            summary={"code_quality_score": 100}
        )
        
        # Serialize and deserialize
        serialized = original.model_dump()
        restored = AnalysisResult.model_validate(serialized)
        
        assert restored.ruff_result.total_issues == original.ruff_result.total_issues
        assert restored.vulture_result.total_items == original.vulture_result.total_items
        assert restored.summary == original.summary


class TestUtilityFunctions:
    """Test utility functions and helpers."""

    def test_quality_score_bounds(self) -> None:
        """Test quality score calculation boundary conditions."""
        from mcp_server_analyzer.server import _calculate_quality_score
        from mcp_server_analyzer.models import RuffCheckResult, VultureScanResult
        
        # Test extreme values
        extreme_ruff = RuffCheckResult(issues=[], total_issues=1000, fixable_issues=0)
        extreme_vulture = VultureScanResult(unused_items=[], total_items=1000, high_confidence_items=1000)
        
        score = _calculate_quality_score(extreme_ruff, extreme_vulture)
        
        # Should never go below 0
        assert score >= 0
        assert score <= 100
        assert isinstance(score, int)

    def test_quality_score_types(self) -> None:
        """Test quality score calculation with different input types."""
        from mcp_server_analyzer.server import _calculate_quality_score
        from mcp_server_analyzer.models import RuffCheckResult, VultureScanResult
        
        # Test with zero values
        zero_ruff = RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)
        zero_vulture = VultureScanResult(unused_items=[], total_items=0, high_confidence_items=0)
        
        score = _calculate_quality_score(zero_ruff, zero_vulture)
        assert score == 100
        assert isinstance(score, int)
        
        # Test with minimal values
        min_ruff = RuffCheckResult(issues=[], total_issues=1, fixable_issues=0)
        min_vulture = VultureScanResult(unused_items=[], total_items=1, high_confidence_items=0)
        
        score = _calculate_quality_score(min_ruff, min_vulture)
        assert 0 <= score <= 100
        assert isinstance(score, int)


class TestServerConfiguration:
    """Test server configuration and setup."""

    def test_fastmcp_app_configuration(self) -> None:
        """Test FastMCP app is configured correctly."""
        from mcp_server_analyzer.server import app
        
        assert app is not None
        assert hasattr(app, "run")
        
        # Test that tools are registered (this might be framework-specific)
        # The exact test depends on FastMCP's API
        assert hasattr(app, "tool")  # Should have tool decorator

    def test_logging_configuration(self) -> None:
        """Test logging is configured."""
        import mcp_server_analyzer.server
        
        # Should have logger configured
        assert hasattr(mcp_server_analyzer.server, "logger")
        logger = mcp_server_analyzer.server.logger
        assert logger is not None
        assert logger.name == "mcp_server_analyzer.server"

    def test_analyzer_availability_flags(self) -> None:
        """Test analyzer availability tracking."""
        import mcp_server_analyzer.server as server_module
        
        # Should have availability tracking
        assert hasattr(server_module, "vulture_available")
        assert isinstance(server_module.vulture_available, bool)
        
        # RUFF should always be available (initialized without try/catch)
        assert hasattr(server_module, "ruff_analyzer")
        assert server_module.ruff_analyzer is not None