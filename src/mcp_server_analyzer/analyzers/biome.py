"""Biome integration for JavaScript/TypeScript code linting and formatting."""
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from mcp_server_analyzer.installer import NodeJSInstaller
from mcp_server_analyzer.models import BiomeCheckResult, BiomeFormatResult, BiomeIssue

# Constants
SPAN_MIN_LENGTH = 2


class BiomeAnalyzer:
    """Handles Biome-based JavaScript/TypeScript code analysis."""

    def __init__(self) -> None:
        """Initialize the Biome analyzer."""
        self._check_biome_installation()

    def _check_biome_installation(self) -> None:
        """Verify that Biome is installed and accessible."""
        try:
            result = subprocess.run(
                ["npx", "biome", "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise RuntimeError("Biome is not properly installed")
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ) as e:
            # Try to provide helpful installation instructions
            installer = NodeJSInstaller()
            if not installer.check_nodejs_available():
                raise RuntimeError(
                    "Node.js is required for JavaScript/TypeScript analysis. "
                    "Please install Node.js from https://nodejs.org/ and run 'npm install' "
                    "or use 'install-js-deps' command."
                ) from e
            if not installer.check_tool_available("biome"):
                # Attempt automatic installation
                if installer.install_dependencies():
                    # Re-check after installation
                    try:
                        subprocess.run(
                            ["npx", "biome", "--version"],
                            capture_output=True,
                            check=True,
                            timeout=10,
                        )
                        return  # Success
                    except (
                        subprocess.CalledProcessError,
                        FileNotFoundError,
                        subprocess.TimeoutExpired,
                    ):
                        pass

                raise RuntimeError(
                    "Biome is not installed. Please run 'npm install' or 'install-js-deps' "
                    "to install JavaScript/TypeScript analysis tools."
                ) from e
            raise RuntimeError(f"Biome is not available: {e}") from e

    def _parse_span_location(
        self, location: dict[str, Any], span: list[int]
    ) -> tuple[int, int, int | None, int | None]:
        """Parse span-based location from Biome diagnostic.

        Args:
            location: Location dict from Biome diagnostic
            span: Span list with start/end offsets

        Returns:
            Tuple of (start_line, start_col, end_line, end_col)
        """
        start_line = 1
        start_col = 1
        end_line = None
        end_col = None

        if span and isinstance(span, list) and len(span) >= SPAN_MIN_LENGTH:
            source_code = location.get("sourceCode", "")
            if source_code:
                lines_before = source_code[: span[0]].count("\n")
                start_line = lines_before + 1
                last_newline = source_code.rfind("\n", 0, span[0])
                start_col = (
                    span[0] - last_newline if last_newline != -1 else span[0] + 1
                )

                if len(span) > 1:
                    lines_before_end = source_code[: span[1]].count("\n")
                    end_line = lines_before_end + 1
                    last_newline_end = source_code.rfind("\n", 0, span[1])
                    end_col = (
                        span[1] - last_newline_end
                        if last_newline_end != -1
                        else span[1] + 1
                    )

        return start_line, start_col, end_line, end_col

    def check_code(
        self, code: str, file_extension: str = ".js", config_path: str | None = None
    ) -> BiomeCheckResult:
        """
        Run Biome linter on the provided code.

        Args:
            code: JavaScript/TypeScript code to lint
            file_extension: File extension to determine language (.js, .ts, .jsx, .tsx)
            config_path: Optional path to Biome configuration file

        Returns:
            BiomeCheckResult containing linting issues
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=file_extension, delete=False
        ) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            cmd = ["npx", "biome", "check", "--reporter=json", str(temp_file)]
            if config_path:
                cmd.extend(["--config-path", config_path])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, check=False
            )

            # Biome returns non-zero exit code when issues are found
            if result.returncode not in (0, 1):
                raise RuntimeError(f"Biome check failed: {result.stderr}")

            issues: list[BiomeIssue] = []
            if result.stdout.strip():
                try:
                    biome_output = json.loads(result.stdout)

                    # Parse diagnostics from Biome output
                    for diagnostic in biome_output.get("diagnostics", []):
                        location = diagnostic.get("location", {})
                        span = location.get("span")

                        # Extract line/column info from source code and span
                        start_line, start_col, end_line, end_col = (
                            self._parse_span_location(location, span)
                        )

                        # Map severity
                        severity_map = {
                            "error": "error",
                            "warning": "warning",
                            "info": "info",
                        }
                        severity = severity_map.get(
                            diagnostic.get("severity", "warning"), "warning"
                        )

                        # Extract message content
                        message_content = ""
                        message_parts = diagnostic.get("message", [])
                        if isinstance(message_parts, list):
                            message_content = "".join(
                                part.get("content", "") for part in message_parts
                            )
                        elif isinstance(message_parts, str):
                            message_content = message_parts
                        else:
                            message_content = diagnostic.get("description", "")

                        issue = BiomeIssue(
                            line=start_line,
                            column=start_col,
                            end_line=end_line if end_line != start_line else None,
                            end_column=end_col if end_col != start_col else None,
                            rule=diagnostic.get("category", "biome"),
                            message=message_content,
                            severity=severity,
                            fixable="fixable" in diagnostic.get("tags", []),
                            file_path=str(temp_file),
                        )
                        issues.append(issue)

                except json.JSONDecodeError as e:
                    raise RuntimeError(f"Failed to parse Biome output: {e}") from e

            return BiomeCheckResult(
                issues=issues,
                total_issues=len(issues),
                fixable_issues=sum(1 for issue in issues if issue.fixable),
                files_checked=1,
            )

        finally:
            temp_file.unlink()

    def check_code_for_ci(
        self,
        code: str,
        file_extension: str = ".js",
        output_format: str = "json",
        config_path: str | None = None,
    ) -> str:
        """
        Run Biome linter with specific output format for CI/CD systems.

        Args:
            code: JavaScript/TypeScript code to lint
            file_extension: File extension to determine language (.js, .ts, .jsx, .tsx)
            output_format: Output format (json, github)
            config_path: Optional path to Biome configuration file

        Returns:
            Raw Biome output in specified format
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=file_extension, delete=False
        ) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            # Map output formats
            reporter_map = {"json": "json", "github": "github"}
            reporter = reporter_map.get(output_format, "json")

            cmd = ["npx", "biome", "ci", f"--reporter={reporter}", str(temp_file)]
            if config_path:
                cmd.extend(["--config-path", config_path])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, check=False
            )

            # Biome returns non-zero exit code when issues are found
            if result.returncode not in (0, 1):
                raise RuntimeError(f"Biome CI check failed: {result.stderr}")

            return result.stdout

        finally:
            temp_file.unlink()

    def format_code(
        self, code: str, file_extension: str = ".js", config_path: str | None = None
    ) -> BiomeFormatResult:
        """
        Format JavaScript/TypeScript code using Biome formatter.

        Args:
            code: JavaScript/TypeScript code to format
            file_extension: File extension to determine language (.js, .ts, .jsx, .tsx)
            config_path: Optional path to Biome configuration file

        Returns:
            BiomeFormatResult containing formatted code
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=file_extension, delete=False
        ) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            cmd = ["npx", "biome", "format", "--stdin-file-path", str(temp_file)]
            if config_path:
                cmd.extend(["--config-path", config_path])

            result = subprocess.run(
                cmd, input=code, capture_output=True, text=True, timeout=30, check=False
            )

            if result.returncode != 0:
                raise RuntimeError(f"Biome format failed: {result.stderr}")

            formatted_code = result.stdout
            changed = formatted_code != code

            return BiomeFormatResult(
                formatted_code=formatted_code,
                changed=changed,
            )

        finally:
            temp_file.unlink()

    def _detect_file_type(self, code: str) -> str:
        """
        Detect file type based on code content.

        Args:
            code: Source code to analyze

        Returns:
            Appropriate file extension
        """
        # Simple heuristics for file type detection
        if "import type" in code or "interface " in code or "type " in code:
            return ".ts"
        if "import React" in code or "jsx" in code.lower():
            return ".jsx"
        if any(
            keyword in code for keyword in ["class ", "function ", "const ", "let "]
        ):
            return ".js"
        return ".js"  # Default to JavaScript
