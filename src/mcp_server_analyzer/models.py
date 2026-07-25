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
    fixable: bool = Field(
        default=False, description="Whether the issue can be auto-fixed"
    )


class RuffCheckResult(BaseModel):
    """Result of RUFF check operation."""

    issues: list[RuffIssue] = Field(description="List of linting issues found")
    total_issues: int = Field(description="Total number of issues")
    fixable_issues: int = Field(description="Number of auto-fixable issues")


class RuffFormatResult(BaseModel):
    """Result of RUFF format operation."""

    formatted_code: str = Field(description="The formatted Python code")
    changed: bool = Field(description="Whether the code was modified during formatting")


class TyDiagnostic(BaseModel):
    """Represents a ty type-checking diagnostic."""

    line: int = Field(description="Line number where the diagnostic occurs")
    column: int = Field(description="Column number where the diagnostic occurs")
    rule: str = Field(description="ty diagnostic rule identifier")
    message: str = Field(description="Human-readable description of the diagnostic")
    severity: str = Field(description="Diagnostic severity level")


class TyCheckResult(BaseModel):
    """Result of a ty type-check operation."""

    diagnostics: list[TyDiagnostic] = Field(
        description="List of type diagnostics found"
    )
    total_diagnostics: int = Field(description="Total number of diagnostics")
    error_count: int = Field(description="Number of error diagnostics")
    warning_count: int = Field(description="Number of warning diagnostics")


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


class BiomeIssue(BaseModel):
    """Represents a single Biome lint/format diagnostic."""

    rule: str = Field(
        description="Biome rule category (e.g., lint/suspicious/noDoubleEquals)"
    )
    severity: str = Field(
        description="Severity level: error, warning, information, or hint"
    )
    message: str = Field(description="Human-readable description of the diagnostic")
    file: str = Field(description="Source filename passed via --stdin-file-path")
    start_offset: int | None = Field(
        None, description="Start byte offset from span[0], or None if unavailable"
    )
    end_offset: int | None = Field(
        None, description="End byte offset from span[1], or None if unavailable"
    )


class BiomeCheckResult(BaseModel):
    """Result of a biome check operation."""

    issues: list[BiomeIssue] = Field(description="List of diagnostics found")
    total_issues: int = Field(description="Total number of diagnostics")
    errors: int = Field(description="Number of error-severity diagnostics")
    warnings: int = Field(description="Number of warning-severity diagnostics")


class BiomeFormatResult(BaseModel):
    """Result of a biome format operation."""

    formatted_code: str = Field(description="The formatted JS/TS code")
    changed: bool = Field(description="Whether the code was modified during formatting")


class RuffCICheckResult(BaseModel):
    """Result of a RUFF CI/CD check operation."""

    output: str = Field(description="Raw RUFF output in the requested format")
    format: str = Field(description="Output format used (json, gitlab, github, sarif)")
    success: bool = Field(description="Whether the check completed without errors")


class SemgrepIssue(BaseModel):
    """Represents a single Semgrep security/SAST finding."""

    check_id: str = Field(description="Semgrep rule identifier that matched")
    line: int = Field(description="Line number where the finding starts")
    column: int = Field(description="Column number where the finding starts")
    end_line: int = Field(description="Line number where the finding ends")
    end_column: int = Field(description="Column number where the finding ends")
    severity: str = Field(description="Semgrep severity (ERROR, WARNING, INFO)")
    message: str = Field(description="Human-readable description of the finding")
    cwe: list[str] = Field(
        default_factory=list, description="Associated CWE identifiers, if any"
    )
    owasp: list[str] = Field(
        default_factory=list, description="Associated OWASP Top 10 categories, if any"
    )


class SemgrepScanResult(BaseModel):
    """Result of a Semgrep security scan operation."""

    issues: list[SemgrepIssue] = Field(description="List of security findings")
    total_issues: int = Field(description="Total number of findings")
    error_count: int = Field(description="Number of ERROR-severity findings")
    warning_count: int = Field(description="Number of WARNING-severity findings")


class ActionlintIssue(BaseModel):
    """Represents a single actionlint GitHub Actions workflow issue."""

    line: int = Field(description="Line number where the issue occurs")
    column: int = Field(description="Column number where the issue occurs")
    end_column: int | None = Field(None, description="End column number, if reported")
    kind: str = Field(description="actionlint rule/check category")
    message: str = Field(description="Human-readable description of the issue")
    snippet: str | None = Field(
        None, description="Source snippet showing the issue location"
    )


class ActionlintCheckResult(BaseModel):
    """Result of an actionlint workflow check operation."""

    issues: list[ActionlintIssue] = Field(description="List of workflow issues found")
    total_issues: int = Field(description="Total number of issues")


class GitleaksFinding(BaseModel):
    """Represents a single gitleaks secret-scanning finding. Secret values are always redacted."""

    rule_id: str = Field(description="gitleaks rule identifier that matched")
    description: str = Field(description="Human-readable description of the rule")
    file: str = Field(description="Source filename the finding was reported against")
    start_line: int = Field(description="Line number where the secret starts")
    end_line: int = Field(description="Line number where the secret ends")
    start_column: int = Field(description="Column number where the secret starts")
    end_column: int = Field(description="Column number where the secret ends")
    secret: str = Field(
        description="Redacted secret value — always 'REDACTED', raw secrets are never returned"
    )
    match: str = Field(description="Redacted matched line context — always 'REDACTED'")


class GitleaksScanResult(BaseModel):
    """Result of a gitleaks secret scan operation."""

    findings: list[GitleaksFinding] = Field(description="List of secret findings")
    total_findings: int = Field(description="Total number of findings")


class AnalysisSummary(BaseModel):
    """Summary statistics from a combined code analysis."""

    total_ruff_issues: int = Field(description="Total number of RUFF linting issues")
    fixable_ruff_issues: int = Field(description="Number of auto-fixable RUFF issues")
    total_ty_diagnostics: int = Field(description="Total number of ty diagnostics")
    ty_error_count: int = Field(description="Number of ty error diagnostics")
    ty_warning_count: int = Field(description="Number of ty warning diagnostics")
    total_unused_items: int = Field(description="Total unused code items from VULTURE")
    high_confidence_unused: int = Field(
        description="Unused items with confidence >= 80"
    )
    code_quality_score: int = Field(description="Combined quality score (0-100)")


class AnalysisResult(BaseModel):
    """Combined analysis result from the available analyzers."""

    ruff_result: RuffCheckResult = Field(description="RUFF linting results")
    ty_result: TyCheckResult = Field(description="ty type-checking results")
    vulture_result: VultureScanResult = Field(
        description="VULTURE dead code detection results"
    )
    summary: AnalysisSummary = Field(description="Summary statistics of the analysis")
