"""gitleaks integration for secret scanning."""

import json
import subprocess
import tempfile
from pathlib import Path

from mcp_server_analyzer.models import GitleaksFinding, GitleaksScanResult


class GitleaksAnalyzer:
    """Handles gitleaks-based secret scanning. Secret values are always redacted."""

    def __init__(self) -> None:
        """Initialize the gitleaks analyzer."""
        self._check_gitleaks_installation()

    def _check_gitleaks_installation(self) -> None:
        """Verify that gitleaks is installed and accessible."""
        try:
            subprocess.run(
                ["gitleaks", "version"],
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
            raise RuntimeError(f"gitleaks is not available: {e}") from e

    def scan_code(self, code: str, filename: str = "code.txt") -> GitleaksScanResult:
        """
        Scan code for hardcoded secrets using gitleaks.

        Args:
            code: Source code to scan
            filename: Virtual filename reported against each finding

        Returns:
            GitleaksScanResult containing findings with secret values redacted

        """
        temp_file: Path | None = None
        try:
            suffix = Path(filename).suffix or ".txt"
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=suffix, delete=False
            ) as f:
                f.write(code)
                temp_file = Path(f.name)

            cmd = [
                "gitleaks",
                "dir",
                "--redact",
                "--report-format",
                "json",
                "--report-path",
                "-",
                "--no-banner",
                str(temp_file),
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, check=False
            )

            # 0 = no leaks found, 1 = leaks found; anything else is a real failure.
            if result.returncode not in (0, 1):
                error_msg = (
                    result.stderr.strip()
                    or f"Unknown gitleaks error (exit code {result.returncode})"
                )
                raise RuntimeError(f"gitleaks scan failed: {error_msg}")

            stdout = result.stdout.strip()
            try:
                raw_findings = json.loads(stdout) if stdout else []
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Failed to parse gitleaks output: {e}") from e

            findings = [
                GitleaksFinding(
                    rule_id=item.get("RuleID", ""),
                    description=item.get("Description", ""),
                    file=filename,
                    start_line=item.get("StartLine", 0),
                    end_line=item.get("EndLine", 0),
                    start_column=item.get("StartColumn", 0),
                    end_column=item.get("EndColumn", 0),
                    secret=item.get("Secret", "REDACTED"),
                    match=item.get("Match", "REDACTED"),
                )
                for item in raw_findings
            ]

            return GitleaksScanResult(findings=findings, total_findings=len(findings))
        except subprocess.TimeoutExpired:
            raise RuntimeError("gitleaks scan timed out") from None
        except (FileNotFoundError, PermissionError) as e:
            raise RuntimeError(f"Failed to run gitleaks: {e}") from e
        finally:
            if temp_file is not None:
                temp_file.unlink(missing_ok=True)
