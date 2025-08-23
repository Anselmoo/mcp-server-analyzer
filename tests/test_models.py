"""Enhanced tests for Pydantic models with good coverage."""

from mcp_server_analyzer.models import (
    AnalysisResult,
    RuffCheckResult,
    RuffFormatResult,
    RuffIssue,
    VultureItem,
    VultureScanResult,
)


def test_ruff_issue_creation():
    """Test basic RuffIssue creation with required fields."""
    issue = RuffIssue(
        line=10,
        column=5,
        rule="F401",
        message="'os' imported but unused",
        severity="error",
    )

    assert issue.line == 10
    assert issue.column == 5
    assert issue.rule == "F401"
    assert issue.message == "'os' imported but unused"
    assert issue.severity == "error"
    assert issue.fixable is False  # Default value
    assert issue.end_line is None  # Optional field
    assert issue.end_column is None  # Optional field


def test_ruff_issue_with_optional_fields():
    """Test RuffIssue creation with optional fields."""
    issue = RuffIssue(
        line=10,
        column=5,
        end_line=12,
        end_column=15,
        rule="F401",
        message="'os' imported but unused",
        severity="error",
        fixable=True,
    )

    assert issue.end_line == 12
    assert issue.end_column == 15
    assert issue.fixable is True


def test_ruff_check_result_empty():
    """Test RuffCheckResult with no issues."""
    result = RuffCheckResult(
        issues=[],
        total_issues=0,
        fixable_issues=0,
    )

    assert result.issues == []
    assert result.total_issues == 0
    assert result.fixable_issues == 0


def test_ruff_check_result_with_issues():
    """Test RuffCheckResult with issues."""
    issues = [
        RuffIssue(
            line=1, column=1, rule="F401", message="unused import", severity="error"
        ),
        RuffIssue(
            line=2, column=1, rule="E302", message="expected 2 blank lines", severity="warning"
        ),
    ]

    result = RuffCheckResult(
        issues=issues,
        total_issues=2,
        fixable_issues=1,
    )

    assert len(result.issues) == 2
    assert result.total_issues == 2
    assert result.fixable_issues == 1


def test_vulture_item_creation():
    """Test VultureItem creation."""
    item = VultureItem(
        name="unused_function",
        type="function",
        line=5,
        column=1,
        confidence=80,
        message="unused function 'unused_function'",
    )

    assert item.name == "unused_function"
    assert item.type == "function"
    assert item.line == 5
    assert item.column == 1
    assert item.confidence == 80
    assert item.message == "unused function 'unused_function'"


def test_vulture_scan_result_empty():
    """Test VultureScanResult with no unused items."""
    result = VultureScanResult(
        unused_items=[],
        total_items=0,
        high_confidence_items=0,
    )

    assert result.unused_items == []
    assert result.total_items == 0
    assert result.high_confidence_items == 0


def test_analysis_result_creation():
    """Test AnalysisResult creation."""
    ruff_result = RuffCheckResult(
        issues=[], total_issues=0, fixable_issues=0
    )
    vulture_result = VultureScanResult(
        unused_items=[], total_items=0, high_confidence_items=0
    )

    analysis = AnalysisResult(
        ruff_result=ruff_result,
        vulture_result=vulture_result,
        quality_score=100,
    )

    assert analysis.quality_score == 100
    assert analysis.ruff_result.total_issues == 0
    assert analysis.vulture_result.total_items == 0


def test_model_serialization():
    """Test model JSON serialization/deserialization."""
    issue = RuffIssue(
        line=1, column=1, rule="F401", message="test", severity="error"
    )

    # Test model_dump (JSON serialization)
    data = issue.model_dump()
    assert data["line"] == 1
    assert data["rule"] == "F401"

    # Test model_validate (deserialization)
    recreated = RuffIssue.model_validate(data)
    assert recreated.line == issue.line
    assert recreated.rule == issue.rule
    assert recreated.message == issue.message


def test_ruff_format_result_unchanged():
    """Test RuffFormatResult when code is unchanged."""
    original_code = "print('hello')"
    result = RuffFormatResult(
        formatted_code=original_code,
        changed=False,
    )

    assert result.formatted_code == original_code
    assert result.changed is False


def test_ruff_format_result_changed():
    """Test RuffFormatResult when code is changed."""
    original_code = "print( 'hello' )"
    formatted_code = "print('hello')"
    result = RuffFormatResult(
        formatted_code=formatted_code,
        changed=True,
    )

    assert result.formatted_code == formatted_code
    assert result.changed is True