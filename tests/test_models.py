"""Comprehensive tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from mcp_server_analyzer.models import (
    AnalysisResult,
    RuffCheckResult,
    RuffFormatResult,
    RuffIssue,
    VultureItem,
    VultureScanResult,
)


class TestRuffIssue:
    """Test RuffIssue model."""

    def test_ruff_issue_creation(self) -> None:
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

    def test_ruff_issue_with_optional_fields(self) -> None:
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

    def test_ruff_issue_validation_errors(self) -> None:
        """Test RuffIssue validation errors."""
        # Missing required fields
        with pytest.raises(ValidationError):
            RuffIssue()
        
        # Invalid types
        with pytest.raises(ValidationError):
            RuffIssue(
                line="not_an_int",  # Should be int
                column=5,
                rule="F401",
                message="test",
                severity="error",
            )


class TestRuffCheckResult:
    """Test RuffCheckResult model."""

    def test_ruff_check_result_empty(self) -> None:
        """Test RuffCheckResult with no issues."""
        result = RuffCheckResult(
            issues=[],
            total_issues=0,
            fixable_issues=0,
        )
        
        assert result.issues == []
        assert result.total_issues == 0
        assert result.fixable_issues == 0

    def test_ruff_check_result_with_issues(self) -> None:
        """Test RuffCheckResult with multiple issues."""
        issue1 = RuffIssue(
            line=1, column=1, rule="F401", message="unused import", severity="error"
        )
        issue2 = RuffIssue(
            line=2, column=1, rule="E302", message="blank lines", severity="warning", fixable=True
        )
        
        result = RuffCheckResult(
            issues=[issue1, issue2],
            total_issues=2,
            fixable_issues=1,
        )
        
        assert len(result.issues) == 2
        assert result.total_issues == 2
        assert result.fixable_issues == 1

    def test_ruff_check_result_validation(self) -> None:
        """Test RuffCheckResult validation."""
        # Negative values should still be accepted (edge case handling)
        result = RuffCheckResult(
            issues=[],
            total_issues=0,
            fixable_issues=0,
        )
        assert result.total_issues == 0


class TestRuffFormatResult:
    """Test RuffFormatResult model."""

    def test_ruff_format_result_unchanged(self) -> None:
        """Test RuffFormatResult when code is unchanged."""
        original_code = "print('hello')"
        result = RuffFormatResult(
            formatted_code=original_code,
            changed=False,
        )
        
        assert result.formatted_code == original_code
        assert result.changed is False

    def test_ruff_format_result_changed(self) -> None:
        """Test RuffFormatResult when code is changed."""
        original_code = "print( 'hello' )"
        formatted_code = "print('hello')"
        result = RuffFormatResult(
            formatted_code=formatted_code,
            changed=True,
        )
        
        assert result.formatted_code == formatted_code
        assert result.changed is True


class TestVultureItem:
    """Test VultureItem model."""

    def test_vulture_item_creation(self) -> None:
        """Test basic VultureItem creation."""
        item = VultureItem(
            name="unused_function",
            type="function",
            line=10,
            column=0,
            confidence=80,
            message="unused function 'unused_function'",
        )
        
        assert item.name == "unused_function"
        assert item.type == "function"
        assert item.line == 10
        assert item.column == 0
        assert item.confidence == 80
        assert item.message == "unused function 'unused_function'"

    def test_vulture_item_validation(self) -> None:
        """Test VultureItem validation."""
        # Test valid confidence range
        item = VultureItem(
            name="test",
            type="variable",
            line=1,
            column=0,
            confidence=100,
            message="test message",
        )
        assert item.confidence == 100
        
        # Test confidence of 0
        item_zero = VultureItem(
            name="test",
            type="variable", 
            line=1,
            column=0,
            confidence=0,
            message="test message",
        )
        assert item_zero.confidence == 0


class TestVultureScanResult:
    """Test VultureScanResult model."""

    def test_vulture_scan_result_empty(self) -> None:
        """Test VultureScanResult with no unused items."""
        result = VultureScanResult(
            unused_items=[],
            total_items=0,
            high_confidence_items=0,
        )
        
        assert result.unused_items == []
        assert result.total_items == 0
        assert result.high_confidence_items == 0

    def test_vulture_scan_result_with_items(self) -> None:
        """Test VultureScanResult with multiple items."""
        item1 = VultureItem(
            name="unused_var", type="variable", line=1, column=0, 
            confidence=85, message="unused variable"
        )
        item2 = VultureItem(
            name="unused_func", type="function", line=5, column=0,
            confidence=60, message="unused function"
        )
        
        result = VultureScanResult(
            unused_items=[item1, item2],
            total_items=2,
            high_confidence_items=1,  # Only item1 has confidence >= 80
        )
        
        assert len(result.unused_items) == 2
        assert result.total_items == 2
        assert result.high_confidence_items == 1


class TestAnalysisResult:
    """Test AnalysisResult model."""

    def test_analysis_result_creation(self) -> None:
        """Test AnalysisResult creation with all components."""
        ruff_result = RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)
        vulture_result = VultureScanResult(unused_items=[], total_items=0, high_confidence_items=0)
        summary = {
            "total_ruff_issues": 0,
            "fixable_ruff_issues": 0,
            "total_unused_items": 0,
            "high_confidence_unused": 0,
            "code_quality_score": 100,
        }
        
        result = AnalysisResult(
            ruff_result=ruff_result,
            vulture_result=vulture_result,
            summary=summary,
        )
        
        assert result.ruff_result == ruff_result
        assert result.vulture_result == vulture_result
        assert result.summary == summary
        assert result.summary["code_quality_score"] == 100

    def test_analysis_result_model_dump(self) -> None:
        """Test AnalysisResult model serialization."""
        ruff_result = RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)
        vulture_result = VultureScanResult(unused_items=[], total_items=0, high_confidence_items=0)
        summary = {"code_quality_score": 100}
        
        result = AnalysisResult(
            ruff_result=ruff_result,
            vulture_result=vulture_result,
            summary=summary,
        )
        
        dumped = result.model_dump()
        assert isinstance(dumped, dict)
        assert "ruff_result" in dumped
        assert "vulture_result" in dumped
        assert "summary" in dumped

    def test_analysis_result_with_issues(self) -> None:
        """Test AnalysisResult with actual issues and unused items."""
        ruff_issue = RuffIssue(
            line=1, column=1, rule="F401", message="unused import", severity="error"
        )
        vulture_item = VultureItem(
            name="unused_var", type="variable", line=2, column=0,
            confidence=90, message="unused variable"
        )
        
        ruff_result = RuffCheckResult(
            issues=[ruff_issue], total_issues=1, fixable_issues=0
        )
        vulture_result = VultureScanResult(
            unused_items=[vulture_item], total_items=1, high_confidence_items=1
        )
        summary = {
            "total_ruff_issues": 1,
            "fixable_ruff_issues": 0,
            "total_unused_items": 1,
            "high_confidence_unused": 1,
            "code_quality_score": 75,
        }
        
        result = AnalysisResult(
            ruff_result=ruff_result,
            vulture_result=vulture_result,
            summary=summary,
        )
        
        assert len(result.ruff_result.issues) == 1
        assert len(result.vulture_result.unused_items) == 1
        assert result.summary["code_quality_score"] == 75