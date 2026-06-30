"""Biome integration for JavaScript/TypeScript linting and formatting."""

import json
import subprocess

from mcp_server_analyzer.models import BiomeCheckResult, BiomeFormatResult, BiomeIssue

_BIOME_ERRORS = (
    subprocess.CalledProcessError,
    FileNotFoundError,
    subprocess.TimeoutExpired,
)


class BiomeAnalyzer:
    """Handles Biome-based JS/TS code analysis."""

    def __init__(self) -> None:
        """Initialize BiomeAnalyzer by discovering the biome command."""
        self._biome_cmd: list[str] = self._find_biome_cmd()

    def _find_biome_cmd(self) -> list[str]:
        """
        Discover which biome command is available.

        Tries ["biome"] first; falls back to ["npx", "--no-install", "biome"].
        Raises RuntimeError if neither is found.
        """
        try:
            subprocess.run(
                ["biome", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
        except _BIOME_ERRORS:
            pass
        else:
            return ["biome"]

        try:
            subprocess.run(
                ["npx", "--no-install", "biome", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
        except _BIOME_ERRORS as e:
            raise RuntimeError(
                f"Biome is not available: neither 'biome' nor 'npx biome' found: {e}"
            ) from e
        else:
            return ["npx", "--no-install", "biome"]

    def check_code(self, code: str, filename: str = "code.ts") -> BiomeCheckResult:
        """
        Run biome check on the provided code via stdin.

        Args:
            code: JS/TS code to lint
            filename: Virtual filename passed to --stdin-file-path (controls parser and rules)

        Returns:
            BiomeCheckResult containing all diagnostics and summary counts

        """
        cmd = [
            *self._biome_cmd,
            "check",
            f"--stdin-file-path={filename}",
            "--reporter=json",
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
            raise RuntimeError("Biome check timed out") from None
        except (FileNotFoundError, PermissionError) as e:
            raise RuntimeError(f"Failed to run Biome: {e}") from e

        # 0 = no issues, 1 = issues found; 2+ = configuration/runtime error
        if result.returncode not in (0, 1):
            raise RuntimeError(
                f"Biome check failed: {result.stderr.strip() or 'unknown error'}"
            )

        issues: list[BiomeIssue] = []

        # Biome ≥2.x echoes the input code back to stdout when using
        # --stdin-file-path; the JSON reporter only works for file-based input.
        # Detect this by checking whether stdout equals the submitted code and
        # skip JSON parsing in that case (treating it as "no diagnostics found").
        stdout = result.stdout.strip()
        if stdout and stdout != code.strip():
            try:
                output = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Failed to parse Biome output: {e}") from e

            for diag in output.get("diagnostics", []):
                location = diag.get("location") or {}
                path = location.get("path") or {}
                span = location.get("span")
                issues.append(
                    BiomeIssue(
                        rule=diag.get("category", ""),
                        severity=diag.get("severity", "warning"),
                        message=diag.get("description", ""),
                        file=path.get("file", filename),
                        start_offset=span[0] if span else None,
                        end_offset=span[1] if span else None,
                    )
                )

        return BiomeCheckResult(
            issues=issues,
            total_issues=len(issues),
            errors=sum(1 for i in issues if i.severity == "error"),
            warnings=sum(1 for i in issues if i.severity == "warning"),
        )

    def format_code(self, code: str, filename: str = "code.ts") -> BiomeFormatResult:
        """
        Format JS/TS code using Biome via stdin.

        Args:
            code: JS/TS code to format
            filename: Virtual filename controlling parser selection

        Returns:
            BiomeFormatResult containing formatted code and change flag

        """
        cmd = [*self._biome_cmd, "format", f"--stdin-file-path={filename}"]

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
            raise RuntimeError("Biome format timed out") from None
        except (FileNotFoundError, PermissionError) as e:
            raise RuntimeError(f"Failed to run Biome: {e}") from e

        if result.returncode != 0:
            raise RuntimeError(
                f"Biome format failed: {result.stderr.strip() or 'unknown error'}"
            )

        formatted_code = result.stdout
        return BiomeFormatResult(
            formatted_code=formatted_code,
            changed=formatted_code != code,
        )
