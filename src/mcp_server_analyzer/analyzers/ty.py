"""ty integration for Python type checking."""

import re
import subprocess
import tempfile
from pathlib import Path

from mcp_server_analyzer.models import TyCheckResult, TyDiagnostic


class TyAnalyzer:
    """Handles ty-based Python type checking."""

    def __init__(self) -> None:
        """Initialize the ty analyzer."""
        self._check_ty_installation()

    def _check_ty_installation(self) -> None:
        """Verify that ty is installed and accessible."""
        try:
            subprocess.run(
                ["ty", "version"],
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
            raise RuntimeError(f"ty is not available: {e}") from e

    def check_code(self, code: str, project_path: str | None = None) -> TyCheckResult:
        """
        Run ty on the provided code.

        Args:
            code: Python code to type-check
            project_path: Optional project directory used for config and import resolution

        Returns:
            TyCheckResult containing diagnostics
        """
        resolved_project_path = (
            Path(project_path).resolve() if project_path else Path.cwd()
        )
        if not resolved_project_path.is_dir():
            raise ValueError(
                f"project_path must be an existing directory: {resolved_project_path}"
            )

        temp_file: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                temp_file = Path(f.name)

            cmd = [
                "ty",
                "check",
                "--no-progress",
                "--output-format=concise",
                "--project",
                str(resolved_project_path),
                str(temp_file),
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, check=False
            )

            if result.returncode not in (0, 1):
                error_msg = (
                    result.stderr.strip()
                    or result.stdout.strip()
                    or f"Unknown ty error (exit code {result.returncode})"
                )
                raise RuntimeError(f"ty check failed: {error_msg}")

            diagnostics = self._parse_ty_output(result.stdout, str(temp_file))

            return TyCheckResult(
                diagnostics=diagnostics,
                total_diagnostics=len(diagnostics),
                error_count=sum(
                    1 for diagnostic in diagnostics if diagnostic.severity == "error"
                ),
                warning_count=sum(
                    1 for diagnostic in diagnostics if diagnostic.severity == "warning"
                ),
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("ty check timed out") from None
        except (FileNotFoundError, PermissionError) as e:
            raise RuntimeError(f"Failed to run ty: {e}") from e
        finally:
            if temp_file is not None:
                temp_file.unlink(missing_ok=True)

    def _parse_ty_output(self, output: str, temp_filename: str) -> list[TyDiagnostic]:
        """
        Parse concise ty output into structured diagnostics.

        Args:
            output: Raw ty output
            temp_filename: Temporary file name to filter out from output

        Returns:
            List of TyDiagnostic objects
        """
        diagnostics: list[TyDiagnostic] = []
        pattern = re.compile(
            r"^(?P<filename>.+):(?P<line>\d+):(?P<column>\d+): "
            r"(?P<severity>error|warning)\[(?P<rule>[^\]]+)\] (?P<message>.+)$"
        )

        temp_path_resolved = str(Path(temp_filename).resolve())

        for line in output.strip().splitlines():
            match = pattern.match(line)
            if not match:
                continue

            filename = match.group("filename")
            if str(Path(filename).resolve()) != temp_path_resolved:
                continue

            diagnostics.append(
                TyDiagnostic(
                    line=int(match.group("line")),
                    column=int(match.group("column")),
                    rule=match.group("rule"),
                    message=match.group("message"),
                    severity=match.group("severity"),
                )
            )

        return diagnostics
