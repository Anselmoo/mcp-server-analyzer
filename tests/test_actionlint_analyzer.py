"""Unit tests for ActionlintAnalyzer using monkeypatching (no real actionlint needed)."""

import json
import subprocess
from typing import Any

import pytest

from mcp_server_analyzer.analyzers.actionlint import ActionlintAnalyzer


class FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


# ── _check_actionlint_installation ──────────────────────────────────────────


def test_check_installation_ok(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: FakeCompletedProcess(0, "v1.7.12")
    )
    ActionlintAnalyzer()


def test_check_installation_raises_on_called_process_error(monkeypatch: Any) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        raise subprocess.CalledProcessError(1, "actionlint")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="actionlint is not available"):
        ActionlintAnalyzer()


def test_check_installation_raises_on_file_not_found(monkeypatch: Any) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        raise FileNotFoundError("not found")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="actionlint is not available"):
        ActionlintAnalyzer()


def test_check_installation_raises_on_timeout(monkeypatch: Any) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        raise subprocess.TimeoutExpired("actionlint", 10)

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="actionlint is not available"):
        ActionlintAnalyzer()


# ── check_workflow ───────────────────────────────────────────────────────────


def test_check_workflow_no_issues(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "v1.7.12"),
        FakeCompletedProcess(0, "[]"),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = ActionlintAnalyzer()
    result = analyzer.check_workflow("on: push\njobs: {}\n")
    assert result.total_issues == 0
    assert result.issues == []


def test_check_workflow_with_issues(monkeypatch: Any) -> None:
    issue = {
        "message": "unexpected end of input while parsing",
        "filepath": "workflow.yml",
        "line": 8,
        "column": 31,
        "kind": "expression",
        "snippet": "        if: ${{ badcondition( }}\n                              ^~",
        "end_column": 32,
    }
    responses = [
        FakeCompletedProcess(0, "v1.7.12"),
        FakeCompletedProcess(1, json.dumps([issue])),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = ActionlintAnalyzer()
    result = analyzer.check_workflow("on: push\n")
    assert result.total_issues == 1
    found = result.issues[0]
    assert found.line == 8
    assert found.column == 31
    assert found.end_column == 32
    assert found.kind == "expression"
    assert "unexpected end of input" in found.message
    assert found.snippet is not None


def test_check_workflow_missing_optional_fields(monkeypatch: Any) -> None:
    issue = {"message": "some error", "line": 1, "column": 1, "kind": "syntax-check"}
    responses = [
        FakeCompletedProcess(0, "v1.7.12"),
        FakeCompletedProcess(1, json.dumps([issue])),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = ActionlintAnalyzer()
    result = analyzer.check_workflow("on: push\n")
    assert result.total_issues == 1
    assert result.issues[0].end_column is None
    assert result.issues[0].snippet is None


def test_check_workflow_empty_stdout(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "v1.7.12"),
        FakeCompletedProcess(0, ""),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = ActionlintAnalyzer()
    result = analyzer.check_workflow("on: push\n")
    assert result.total_issues == 0


def test_check_workflow_invalid_option_exit_code(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "v1.7.12"),
        FakeCompletedProcess(2, "", "flag provided but not defined"),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = ActionlintAnalyzer()
    with pytest.raises(RuntimeError, match="actionlint check failed"):
        analyzer.check_workflow("on: push\n")


def test_check_workflow_fatal_error_exit_code(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "v1.7.12"),
        FakeCompletedProcess(3, "", "fatal error"),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = ActionlintAnalyzer()
    with pytest.raises(RuntimeError, match="actionlint check failed"):
        analyzer.check_workflow("on: push\n")


def test_check_workflow_bad_returncode_empty_stderr(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "v1.7.12"),
        FakeCompletedProcess(3, "", ""),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = ActionlintAnalyzer()
    with pytest.raises(RuntimeError, match="actionlint check failed"):
        analyzer.check_workflow("on: push\n")


def test_check_workflow_json_decode_error(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "v1.7.12"),
        FakeCompletedProcess(1, "NOT_VALID_JSON"),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = ActionlintAnalyzer()
    with pytest.raises(RuntimeError, match="Failed to parse actionlint output"):
        analyzer.check_workflow("on: push\n")


def test_check_workflow_timeout(monkeypatch: Any) -> None:
    call_count = [0]

    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        call_count[0] += 1
        if call_count[0] == 1:
            return FakeCompletedProcess(0, "v1.7.12")
        raise subprocess.TimeoutExpired("actionlint", 30)

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = ActionlintAnalyzer()
    with pytest.raises(RuntimeError, match="actionlint check timed out"):
        analyzer.check_workflow("on: push\n")


def test_check_workflow_file_not_found(monkeypatch: Any) -> None:
    call_count = [0]

    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        call_count[0] += 1
        if call_count[0] == 1:
            return FakeCompletedProcess(0, "v1.7.12")
        raise FileNotFoundError("actionlint vanished")

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = ActionlintAnalyzer()
    with pytest.raises(RuntimeError, match="Failed to run actionlint"):
        analyzer.check_workflow("on: push\n")


def test_check_workflow_permission_error(monkeypatch: Any) -> None:
    call_count = [0]

    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        call_count[0] += 1
        if call_count[0] == 1:
            return FakeCompletedProcess(0, "v1.7.12")
        raise PermissionError("permission denied")

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = ActionlintAnalyzer()
    with pytest.raises(RuntimeError, match="Failed to run actionlint"):
        analyzer.check_workflow("on: push\n")
