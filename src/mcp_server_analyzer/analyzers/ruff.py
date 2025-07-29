"""RUFF integration for Python code linting and formatting."""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from mcp_server_analyzer.models import RuffCheckResult, RuffFormatResult, RuffIssue


class RuffAnalyzer:
    """Handles RUFF-based Python code analysis."""

    def __init__(self) -> None:
        """Initialize the RUFF analyzer."""
        self._check_ruff_installation()

    def _check_ruff_installation(self) -> None:
        """Verify that RUFF is installed and accessible."""
        try:
            result = subprocess.run(
                ["ruff", "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise RuntimeError("RUFF is not properly installed")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise RuntimeError(f"RUFF is not available: {e}") from e

    def check_code(self, code: str, config_path: str | None = None) -> RuffCheckResult:
        """
        Run RUFF linter on the provided code.

        Args:
            code: Python code to lint
            config_path: Optional path to RUFF configuration file

        Returns:
            RuffCheckResult containing linting issues
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            cmd = ["ruff", "check", "--output-format=json", str(temp_file)]
            if config_path:
                cmd.extend(["--config", config_path])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, check=False
            )

            # RUFF returns non-zero exit code when issues are found
            if result.returncode not in (0, 1):
                raise RuntimeError(f"RUFF check failed: {result.stderr}")

            issues: list[RuffIssue] = []
            if result.stdout.strip():
                try:
                    ruff_output = json.loads(result.stdout)
                    for item in ruff_output:
                        end_location: dict[str, int] = item.get("end_location") or {}
                        fix_info: dict[str, Any] = item.get("fix") or {}
                        issue = RuffIssue(
                            line=item["location"]["row"],
                            column=item["location"]["column"],
                            end_line=end_location.get("row"),
                            end_column=end_location.get("column"),
                            rule=item["code"],
                            message=item["message"],
                            severity=self._get_severity(item["code"]),
                            fixable=fix_info.get("applicability") == "safe",
                        )
                        issues.append(issue)
                except json.JSONDecodeError as e:
                    raise RuntimeError(f"Failed to parse RUFF output: {e}") from e

            return RuffCheckResult(
                issues=issues,
                total_issues=len(issues),
                fixable_issues=sum(1 for issue in issues if issue.fixable),
            )

        finally:
            temp_file.unlink()

    def check_code_for_ci(
        self, code: str, output_format: str = "json", config_path: str | None = None
    ) -> str:
        """
        Run RUFF linter with specific output format for CI/CD systems.

        Args:
            code: Python code to lint
            output_format: Output format (json, gitlab, github, sarif)
            config_path: Optional path to RUFF configuration file

        Returns:
            Raw RUFF output in specified format
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            cmd = ["ruff", "check", f"--output-format={output_format}", str(temp_file)]
            if config_path:
                cmd.extend(["--config", config_path])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, check=False
            )

            # RUFF returns non-zero exit code when issues are found
            if result.returncode not in (0, 1):
                raise RuntimeError(f"RUFF check failed: {result.stderr}")

            return result.stdout

        finally:
            temp_file.unlink()

    def format_code(
        self, code: str, config_path: str | None = None
    ) -> RuffFormatResult:
        """
        Format Python code using RUFF formatter.

        Args:
            code: Python code to format
            config_path: Optional path to RUFF configuration file

        Returns:
            RuffFormatResult containing formatted code
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            cmd = ["ruff", "format", "--stdin-filename", str(temp_file)]
            if config_path:
                cmd.extend(["--config", config_path])

            result = subprocess.run(
                cmd, input=code, capture_output=True, text=True, timeout=30, check=False
            )

            if result.returncode != 0:
                raise RuntimeError(f"RUFF format failed: {result.stderr}")

            formatted_code = result.stdout
            changed = formatted_code != code

            return RuffFormatResult(
                formatted_code=formatted_code,
                changed=changed,
            )

        finally:
            temp_file.unlink()

    def _get_severity(self, rule_code: str) -> str:
        """
        Determine severity level based on RUFF rule code.

        Args:
            rule_code: RUFF rule code (e.g., F401, E302)

        Returns:
            Severity level string
        """
        # Map RUFF rule prefixes to severity levels
        if rule_code.startswith(("F", "E9")):
            return "error"
        elif rule_code.startswith(("W", "E", "C90", "N", "B", "A", "C4")):  # noqa: RET505
            return "warning"
        elif rule_code.startswith(
            ("I", "UP", "PIE", "T20", "PT", "RET", "SIM", "TID", "ARG", "PL", "RUF")
        ):
            return "info"
        else:
            return "warning"
