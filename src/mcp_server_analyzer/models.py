"""Pydantic models for MCP Python Analyzer responses and configurations."""

from pydantic import BaseModel, Field


class RuffIssue(BaseModel):
    """Represents a RUFF linting issue."""

    line: int = Field(description="Line number where the issue occurs")
    column: int = Field(description="Column number where the issue occurs")
    end_line: int | None = Field(
        None, description="End line number for multi-line issues"
    )
    end_column: int | None = Field(
        None, description="End column number for multi-line issues"
    )
    rule: str = Field(description="RUFF rule code (e.g., F401, E302)")
    message: str = Field(description="Human-readable description of the issue")
    severity: str = Field(description="Issue severity level")
    fixable: bool = Field(False, description="Whether the issue can be auto-fixed")


class RuffCheckResult(BaseModel):
    """Result of RUFF check operation."""

    issues: list[RuffIssue] = Field(description="List of linting issues found")
    total_issues: int = Field(description="Total number of issues")
    fixable_issues: int = Field(description="Number of auto-fixable issues")


class RuffFormatResult(BaseModel):
    """Result of RUFF format operation."""

    formatted_code: str = Field(description="The formatted Python code")
    changed: bool = Field(description="Whether the code was modified during formatting")


class VultureItem(BaseModel):
    """Represents an unused code item found by VULTURE."""

    name: str = Field(description="Name of the unused item")
    type: str = Field(
        description="Type of unused item (import, function, class, variable, etc.)"
    )
    line: int = Field(description="Line number where the unused item is defined")
    column: int = Field(description="Column number where the unused item is defined")
    confidence: int = Field(
        description="Confidence level (0-100) that the item is unused"
    )
    message: str = Field(description="Description of the unused item")


class VultureScanResult(BaseModel):
    """Result of VULTURE scan operation."""

    unused_items: list[VultureItem] = Field(
        description="List of unused code items found"
    )
    total_items: int = Field(description="Total number of unused items")
    high_confidence_items: int = Field(
        description="Number of items with confidence >= 80"
    )


class AnalysisResult(BaseModel):
    """Combined analysis result from both RUFF and VULTURE."""

    ruff_result: RuffCheckResult = Field(description="RUFF linting results")
    vulture_result: VultureScanResult = Field(
        description="VULTURE dead code detection results"
    )
    summary: dict[str, int] = Field(description="Summary statistics of the analysis")
