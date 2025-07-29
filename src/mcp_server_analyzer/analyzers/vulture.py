"""VULTURE integration for Python dead code detection."""

import re
import subprocess
import tempfile
from pathlib import Path

from mcp_server_analyzer.models import VultureItem, VultureScanResult


class VultureAnalyzer:
    """Handles VULTURE-based dead code detection."""

    def __init__(self) -> None:
        """Initialize the VULTURE analyzer."""
        self._check_vulture_installation()

    def _check_vulture_installation(self) -> None:
        """Verify that VULTURE is installed and accessible."""
        try:
            result = subprocess.run(
                ["vulture", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"VULTURE is not properly installed: {result.stderr}"
                )
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ) as e:
            raise RuntimeError(f"VULTURE is not available: {e}") from e

    def scan_code(self, code: str, min_confidence: int = 80) -> VultureScanResult:
        """
        Scan Python code for dead/unused code using VULTURE.

        Args:
            code: Python code to analyze
            min_confidence: Minimum confidence level (0-100) for reporting items

        Returns:
            VultureScanResult containing unused code items
        """
        if not 0 <= min_confidence <= 100:  # noqa: PLR2004
            raise ValueError("min_confidence must be between 0 and 100")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            cmd = [
                "vulture",
                str(temp_file),
                f"--min-confidence={min_confidence}",
                "--sort-by-size",
            ]

            # Check if pyproject.toml exists and use it
            pyproject_path = Path.cwd() / "pyproject.toml"
            if pyproject_path.exists():
                cmd.extend(["--config", str(pyproject_path)])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, check=False
            )

            # VULTURE exit codes:
            # 0: No dead code found
            # 1: Invalid input (file missing, syntax error, wrong encoding)
            # 2: Invalid command line arguments
            # 3: Dead code found
            if result.returncode not in (0, 1, 3):
                error_msg = (
                    result.stderr.strip()
                    or f"Unknown VULTURE error (exit code {result.returncode})"
                )
                raise RuntimeError(f"VULTURE scan failed: {error_msg}")

            items = []
            if result.stdout.strip():
                items = self._parse_vulture_output(result.stdout, str(temp_file))
            high_confidence_percentage = 80
            high_confidence_count = sum(
                1 for item in items if item.confidence >= high_confidence_percentage
            )

            return VultureScanResult(
                unused_items=items,
                total_items=len(items),
                high_confidence_items=high_confidence_count,
            )

        except subprocess.TimeoutExpired:
            raise RuntimeError("VULTURE scan timed out") from None
        except (FileNotFoundError, PermissionError) as e:
            raise RuntimeError(f"Failed to run VULTURE: {e}") from e
        finally:
            temp_file.unlink()

    def _parse_vulture_output(
        self, output: str, temp_filename: str
    ) -> list[VultureItem]:
        """
        Parse VULTURE output into structured items.

        Args:
            output: Raw VULTURE output
            temp_filename: Temporary file name to filter out from output

        Returns:
            List of VultureItem objects
        """
        items: list[VultureItem] = []
        # VULTURE output format: filename:line: message (confidence%, size info)
        pattern = (
            r"^(.+):(\d+):\s+(.+?)\s+\((\d+)%\s+confidence(?:,\s+\d+\s+lines?)?\)$"
        )

        # Resolve the temp filename for comparison
        temp_path_resolved = str(Path(temp_filename).resolve())

        for line in output.strip().split("\n"):
            if not line.strip():
                continue

            match = re.match(pattern, line)
            if match:
                filename, line_num, message, confidence = match.groups()

                # Compare resolved paths to handle /private prefix on macOS
                file_path_resolved = str(Path(filename).resolve())
                if file_path_resolved != temp_path_resolved:
                    continue

                # Extract item name and type from message
                item_name, item_type = self._extract_item_info(message)

                item = VultureItem(
                    name=item_name,
                    type=item_type,
                    line=int(line_num),
                    column=0,  # Vulture doesn't provide column info in this format
                    confidence=int(confidence),
                    message=message,
                )
                items.append(item)

        return items

    def _extract_item_info(self, message: str) -> tuple[str, str]:
        """
        Extract item name and type from VULTURE message.

        Args:
            message: VULTURE message string

        Returns:
            Tuple of (item_name, item_type)
        """
        # Common VULTURE message patterns
        patterns = [
            (r"unused import '(.+?)'", "import"),
            (r"unused function '(.+?)'", "function"),
            (r"unused method '(.+?)'", "method"),
            (r"unused class '(.+?)'", "class"),
            (r"unused variable '(.+?)'", "variable"),
            (r"unused attribute '(.+?)'", "attribute"),
            (r"unused property '(.+?)'", "property"),
            (r"unused argument '(.+?)'", "argument"),
        ]

        for pattern, item_type in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1), item_type

        # Fallback: try to extract quoted name
        quoted_match = re.search(r"'(.+?)'", message)
        if quoted_match:
            return quoted_match.group(1), "unknown"

        # Last resort: use first word as name
        words = message.split()
        if words:
            return words[0], "unknown"

        return "unknown", "unknown"
