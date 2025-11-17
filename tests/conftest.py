"""Shared test fixtures for MCP Python Analyzer tests."""

import json
import subprocess
from pathlib import Path

import pytest

from mcp_server_analyzer.models import BiomeIssue


@pytest.fixture
def sample_bad_code() -> str:
    """Provide sample bad code for testing."""
    return """
import os
import sys
unused_var = "not used"

def unused_function():
    return "never called"

def main():
    print("hello world")
    temp = "unused"
    return 42

class UnusedClass:
    def __init__(self):
        self.value = "unused"

if __name__ == "__main__":
    main()
"""


@pytest.fixture
def sample_good_code() -> str:
    """Provide sample good code for testing."""
    return '''
def main() -> int:
    """Main function."""
    print("hello world")
    return 42

if __name__ == "__main__":
    main()
'''


@pytest.fixture
def sample_biome_issue() -> BiomeIssue:
    """Return a representative BiomeIssue for tests."""
    return BiomeIssue(
        line=1,
        column=1,
        end_line=1,
        end_column=5,
        rule="mock/rule",
        message="Mocked Biome issue",
        severity="warning",
        fixable=True,
        file_path="mock.js",
    )


@pytest.fixture
def mock_biome_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock Biome CLI commands so tests do not require the real tool."""

    real_run = subprocess.run

    def _read_source_from_args(args: list[str]) -> str:
        for token in reversed(args):
            path = Path(token)
            if path.exists() and path.is_file():
                try:
                    return path.read_text()
                except OSError:
                    return ""
        return ""

    def _make_diagnostics(source: str) -> dict[str, object]:
        span_end = min(len(source), 5) or 1
        return {
            "category": "lint/style",
            "severity": "warning",
            "tags": ["fixable"],
            "location": {"span": [0, span_end], "sourceCode": source},
            "message": [{"content": "Mocked Biome diagnostic"}],
        }

    def fake_run(cmd: list[str], *args, **kwargs):
        if (
            isinstance(cmd, list | tuple)
            and len(cmd) >= 2
            and cmd[0] == "npx"
            and cmd[1] == "biome"
        ):
            if any(part in ("--version",) for part in cmd[2:]) or len(cmd) == 2:
                return subprocess.CompletedProcess(
                    cmd, 0, stdout="biome 1.8.0\n", stderr=""
                )

            if "check" in cmd:
                source = _read_source_from_args(list(cmd))
                diagnostics = [_make_diagnostics(source)]
                stdout = json.dumps({"version": "1.8.0", "diagnostics": diagnostics})
                return subprocess.CompletedProcess(cmd, 1, stdout=stdout, stderr="")

            if "ci" in cmd:
                source = _read_source_from_args(list(cmd))
                diagnostics = [_make_diagnostics(source)]
                stdout = json.dumps({"version": "1.8.0", "diagnostics": diagnostics})
                return subprocess.CompletedProcess(cmd, 1, stdout=stdout, stderr="")

            if "format" in cmd:
                formatted = kwargs.get("input", "").strip() + "\n"
                return subprocess.CompletedProcess(cmd, 0, stdout=formatted, stderr="")

        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", fake_run)
