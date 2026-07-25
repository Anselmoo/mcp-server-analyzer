"""actionlint integration for GitHub Actions workflow linting."""

import json
import subprocess

from mcp_server_analyzer.models import ActionlintCheckResult, ActionlintIssue


class ActionlintAnalyzer:
    """Handles actionlint-based GitHub Actions workflow linting."""

    def __init__(self) -> None:
        """Initialize ActionlintAnalyzer by checking the actionlint binary is available."""
        self._check_actionlint_installation()

    def _check_actionlint_installation(self) -> None:
        """Verify that actionlint is installed and accessible."""
        try:
            subprocess.run(
                ["actionlint", "-version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ) as e:
            raise RuntimeError(f"actionlint is not available: {e}") from e

    def check_workflow(
        self, code: str, filename: str = "workflow.yml"
    ) -> ActionlintCheckResult:
        """
        Lint a GitHub Actions workflow YAML file using actionlint via stdin.

        Args:
            code: Workflow YAML source to lint
            filename: Virtual filename reported in issue locations

        Returns:
            ActionlintCheckResult containing workflow issues and counts

        """
        cmd = [
            "actionlint",
            "-stdin-filename",
            filename,
            "-format",
            "{{json .}}",
            "-",
        ]

        try:
            result = subprocess.run(
                cmd,
                input=code,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("actionlint check timed out") from None
        except (FileNotFoundError, PermissionError) as e:
            raise RuntimeError(f"Failed to run actionlint: {e}") from e

        # 0 = success/no problems, 1 = success/problems found; 2 = invalid CLI
        # option, 3 = fatal error.
        if result.returncode not in (0, 1):
            raise RuntimeError(
                f"actionlint check failed: {result.stderr.strip() or 'unknown error'}"
            )

        stdout = result.stdout.strip()
        try:
            raw_issues = json.loads(stdout) if stdout else []
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse actionlint output: {e}") from e

        issues = [
            ActionlintIssue(
                line=item.get("line", 0),
                column=item.get("column", 0),
                end_column=item.get("end_column"),
                kind=item.get("kind", ""),
                message=item.get("message", ""),
                snippet=item.get("snippet"),
            )
            for item in raw_issues
        ]

        return ActionlintCheckResult(issues=issues, total_issues=len(issues))
