"""Semgrep integration for security/SAST scanning."""

import json
import subprocess
import tempfile
from pathlib import Path

from mcp_server_analyzer.models import SemgrepIssue, SemgrepScanResult

_SEMGREP_ERRORS = (
    subprocess.CalledProcessError,
    FileNotFoundError,
    subprocess.TimeoutExpired,
)


class SemgrepAnalyzer:
    """Handles Semgrep-based security/SAST scanning."""

    def __init__(self) -> None:
        """Initialize SemgrepAnalyzer by discovering the semgrep command."""
        self._semgrep_cmd: list[str] = self._find_semgrep_cmd()

    def _find_semgrep_cmd(self) -> list[str]:
        """
        Discover which semgrep command is available.

        Tries ["semgrep"] first; falls back to ["uvx", "semgrep"] so semgrep
        doesn't have to be a pinned project dependency (semgrep bundles its own
        MCP integration and pins an exact `mcp` version, which would otherwise
        downgrade this project's own MCP stack). Raises RuntimeError if neither
        is found.
        """
        try:
            subprocess.run(
                ["semgrep", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
        except _SEMGREP_ERRORS:
            pass
        else:
            return ["semgrep"]

        try:
            subprocess.run(
                ["uvx", "semgrep", "--version"],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
        except _SEMGREP_ERRORS as e:
            raise RuntimeError(
                f"Semgrep is not available: neither 'semgrep' nor 'uvx semgrep' found: {e}"
            ) from e
        else:
            return ["uvx", "semgrep"]

    def check_code(
        self, code: str, config: str = "auto", filename: str = "code.py"
    ) -> SemgrepScanResult:
        """
        Scan code for security issues using Semgrep.

        Args:
            code: Source code to scan
            config: Semgrep ruleset (e.g. "auto", "p/security-audit", or a local path).
                "auto" pulls rules from the Semgrep registry over the network.
            filename: Virtual filename used to pick the correct file suffix/parser

        Returns:
            SemgrepScanResult containing security findings and counts

        """
        temp_file: Path | None = None
        try:
            suffix = Path(filename).suffix or ".py"
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=suffix, delete=False
            ) as f:
                f.write(code)
                temp_file = Path(f.name)

            cmd = [
                *self._semgrep_cmd,
                "--config",
                config,
                "--json",
                "--quiet",
                "--disable-version-check",
                str(temp_file),
            ]
            # --metrics=off cannot be combined with --config auto (semgrep requires
            # metrics to resolve the auto ruleset); only disable metrics for explicit
            # configs, where no registry auto-resolution is involved.
            if config != "auto":
                cmd.append("--metrics=off")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60, check=False
            )

            # semgrep exits 0 whether or not findings are present (--error is not
            # passed); any other exit code indicates a real failure (bad config,
            # crash, etc).
            if result.returncode != 0:
                error_msg = (
                    result.stderr.strip()
                    or result.stdout.strip()
                    or f"Unknown semgrep error (exit code {result.returncode})"
                )
                raise RuntimeError(f"Semgrep check failed: {error_msg}")

            try:
                output = json.loads(result.stdout) if result.stdout.strip() else {}
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Failed to parse Semgrep output: {e}") from e

            issues = self._parse_results(output.get("results", []), str(temp_file))

            return SemgrepScanResult(
                issues=issues,
                total_issues=len(issues),
                error_count=sum(1 for i in issues if i.severity == "ERROR"),
                warning_count=sum(1 for i in issues if i.severity == "WARNING"),
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Semgrep check timed out") from None
        except (FileNotFoundError, PermissionError) as e:
            raise RuntimeError(f"Failed to run Semgrep: {e}") from e
        finally:
            if temp_file is not None:
                temp_file.unlink(missing_ok=True)

    def _parse_results(
        self, results: list[dict], temp_filename: str
    ) -> list[SemgrepIssue]:
        """
        Parse Semgrep's JSON "results" list into structured issues.

        Args:
            results: Raw "results" list from Semgrep's JSON output
            temp_filename: Temporary file name to filter out unrelated results

        Returns:
            List of SemgrepIssue objects

        """
        issues: list[SemgrepIssue] = []
        temp_path_resolved = str(Path(temp_filename).resolve())

        for item in results:
            path = item.get("path")
            if path is not None and str(Path(path).resolve()) != temp_path_resolved:
                continue

            start = item.get("start") or {}
            end = item.get("end") or {}
            extra = item.get("extra") or {}
            metadata = extra.get("metadata") or {}

            issues.append(
                SemgrepIssue(
                    check_id=item.get("check_id", ""),
                    line=start.get("line", 0),
                    column=start.get("col", 0),
                    end_line=end.get("line", 0),
                    end_column=end.get("col", 0),
                    severity=extra.get("severity", "INFO"),
                    message=extra.get("message", ""),
                    cwe=metadata.get("cwe", []),
                    owasp=metadata.get("owasp", []),
                )
            )

        return issues
