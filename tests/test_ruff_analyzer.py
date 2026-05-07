import json
import subprocess
from typing import Any

from mcp_server_analyzer.analyzers.ruff import RuffAnalyzer


class FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_check_code_parses_json(monkeypatch: Any):
    # Prepare responses: first call is --version check
    responses = [
        FakeCompletedProcess(returncode=0, stdout="ruff 1.0"),
        FakeCompletedProcess(
            returncode=1,
            stdout=json.dumps(
                [
                    {
                        "location": {"row": 10, "column": 2},
                        "end_location": {"row": 10, "column": 5},
                        "code": "F401",
                        "message": "unused import",
                        "fix": {"applicability": "safe"},
                    }
                ]
            ),
        ),
    ]

    def fake_run(*_args, **_kwargs):
        return responses.pop(0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    analyzer = RuffAnalyzer()
    result = analyzer.check_code("import os\n")

    assert result.total_issues == 1
    assert result.fixable_issues == 1
    assert result.issues[0].rule == "F401"


def test_format_code_returns_changed(monkeypatch: Any):
    responses = [
        FakeCompletedProcess(returncode=0, stdout="ruff 1.0"),
        FakeCompletedProcess(returncode=0, stdout="formatted_code\n"),
    ]

    def fake_run(*_args, **_kwargs):
        return responses.pop(0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    analyzer = RuffAnalyzer()
    res = analyzer.format_code("x = 1\n")
    assert res.changed is True
    assert "formatted_code" in res.formatted_code


def test_check_code_for_ci_returns_output(monkeypatch: Any):
    responses = [
        FakeCompletedProcess(returncode=0, stdout="ruff 1.0"),
        FakeCompletedProcess(returncode=0, stdout="CI_OUTPUT"),
    ]

    def fake_run(*_args, **_kwargs):
        return responses.pop(0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    analyzer = RuffAnalyzer()
    out = analyzer.check_code_for_ci("x=1", output_format="json")
    assert "CI_OUTPUT" in out


def test_get_severity():
    a = RuffAnalyzer.__new__(RuffAnalyzer)
    # Test a few rule codes
    assert a._get_severity("F401") == "error"
    assert a._get_severity("W292") == "warning"
    assert a._get_severity("I001") == "info"
