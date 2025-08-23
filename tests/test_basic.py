"""Enhanced basic tests to verify the setup works with additional coverage."""


def test_basic_import():
    """Test that we can import the main modules."""
    from mcp_server_analyzer.analyzers.ruff import RuffAnalyzer
    from mcp_server_analyzer.analyzers.vulture import VultureAnalyzer
    from mcp_server_analyzer.models import RuffCheckResult

    assert RuffAnalyzer is not None
    assert VultureAnalyzer is not None
    assert RuffCheckResult is not None


def test_ruff_analyzer_basic():
    """Test basic RUFF analyzer functionality."""
    from mcp_server_analyzer.analyzers.ruff import RuffAnalyzer

    analyzer = RuffAnalyzer()
    test_code = "import os\nprint('hello')"
    result = analyzer.check_code(test_code)

    assert hasattr(result, "total_issues")
    assert hasattr(result, "issues")
    assert result.total_issues >= 0


def test_vulture_analyzer_basic():
    """Test basic VULTURE analyzer functionality."""
    from mcp_server_analyzer.analyzers.vulture import VultureAnalyzer

    analyzer = VultureAnalyzer()
    test_code = "import os\ndef unused(): pass\nprint('hello')"
    result = analyzer.scan_code(test_code)

    assert hasattr(result, "total_items")
    assert hasattr(result, "unused_items")
    assert result.total_items >= 0


def test_all_models_importable():
    """Test that all model classes can be imported."""
    from mcp_server_analyzer.models import (
        AnalysisResult,
        RuffCheckResult,
        RuffFormatResult,
        RuffIssue,
        VultureItem,
        VultureScanResult,
    )

    models = [
        RuffIssue, RuffCheckResult, RuffFormatResult,
        VultureItem, VultureScanResult, AnalysisResult
    ]

    for model in models:
        assert model is not None
        # Verify they have Pydantic methods
        assert hasattr(model, "model_validate")


def test_server_module_importable():
    """Test that the server module can be imported."""
    import mcp_server_analyzer.server

    # Verify key components exist
    assert hasattr(mcp_server_analyzer.server, "app")
    assert hasattr(mcp_server_analyzer.server, "main")
    assert hasattr(mcp_server_analyzer.server, "_calculate_quality_score")


def test_package_version():
    """Test package has version information."""
    import mcp_server_analyzer

    assert hasattr(mcp_server_analyzer, "__version__")
    assert isinstance(mcp_server_analyzer.__version__, str)
    assert len(mcp_server_analyzer.__version__) > 0


def test_analyzer_classes_have_required_methods():
    """Test that analyzer classes have their required methods."""
    from mcp_server_analyzer.analyzers.ruff import RuffAnalyzer
    from mcp_server_analyzer.analyzers.vulture import VultureAnalyzer

    # Test RuffAnalyzer methods
    ruff_methods = ["check_code", "format_code", "check_code_for_ci"]
    for method in ruff_methods:
        assert hasattr(RuffAnalyzer, method)
        assert callable(getattr(RuffAnalyzer, method))

    # Test VultureAnalyzer methods
    vulture_methods = ["scan_code"]
    for method in vulture_methods:
        assert hasattr(VultureAnalyzer, method)
        assert callable(getattr(VultureAnalyzer, method))


def test_model_field_validation():
    """Test basic model field validation."""
    from mcp_server_analyzer.models import RuffIssue, VultureItem

    # Test RuffIssue creation
    issue = RuffIssue(
        line=1, column=1, rule="F401", message="test", severity="error"
    )
    assert issue.line == 1
    assert issue.fixable is False  # default value

    # Test VultureItem creation
    item = VultureItem(
        name="test", type="variable", line=1, column=1,
        confidence=80, message="test message"
    )
    assert item.name == "test"
    assert item.confidence == 80


def test_configuration_handling():
    """Test that analyzers can handle configuration parameters."""
    from mcp_server_analyzer.analyzers.ruff import RuffAnalyzer
    from mcp_server_analyzer.analyzers.vulture import VultureAnalyzer

    ruff_analyzer = RuffAnalyzer()
    vulture_analyzer = VultureAnalyzer()

    test_code = "print('hello')"

    # Test that methods accept config parameters without error
    try:
        ruff_analyzer.check_code(test_code, config_path=None)
        ruff_analyzer.format_code(test_code, config_path=None)
        vulture_analyzer.scan_code(test_code, min_confidence=80)
        # If no exceptions, test passes
        assert True
    except Exception as e:
        # Fail test if basic parameter handling doesn't work
        assert False, f"Configuration parameter handling failed: {e}"
