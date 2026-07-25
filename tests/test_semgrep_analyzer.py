"""Unit tests for SemgrepAnalyzer using monkeypatching (no real semgrep needed)."""

import json
import subprocess
from typing import Any

import pytest

from mcp_server_analyzer.analyzers.semgrep import SemgrepAnalyzer


class FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


# ── _find_semgrep_cmd ────────────────────────────────────────────────────────


def test_find_semgrep_cmd_uses_local_semgrep(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: FakeCompletedProcess(0, "1.90.0")
    )
    analyzer = SemgrepAnalyzer()
    assert analyzer._semgrep_cmd == ["semgrep"]


def test_find_semgrep_cmd_falls_back_to_uvx(monkeypatch: Any) -> None:
    call_count = [0]

    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        call_count[0] += 1
        if call_count[0] == 1:
            raise FileNotFoundError("semgrep not in PATH")
        return FakeCompletedProcess(0, "1.90.0")

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = SemgrepAnalyzer()
    assert analyzer._semgrep_cmd == ["uvx", "semgrep"]


def test_find_semgrep_cmd_raises_when_neither_available(monkeypatch: Any) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        raise FileNotFoundError("not found")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="Semgrep is not available"):
        SemgrepAnalyzer()


def test_find_semgrep_cmd_raises_on_called_process_error(monkeypatch: Any) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        raise subprocess.CalledProcessError(1, "semgrep")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="Semgrep is not available"):
        SemgrepAnalyzer()


def test_find_semgrep_cmd_raises_on_timeout(monkeypatch: Any) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        raise subprocess.TimeoutExpired("semgrep", 10)

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="Semgrep is not available"):
        SemgrepAnalyzer()


# ── check_code ───────────────────────────────────────────────────────────────


def test_check_code_no_issues(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "1.90.0"),
        FakeCompletedProcess(0, json.dumps({"results": [], "errors": []})),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = SemgrepAnalyzer()
    result = analyzer.check_code("x = 1\n")
    assert result.total_issues == 0
    assert result.error_count == 0
    assert result.warning_count == 0
    assert result.issues == []


def test_check_code_with_findings(monkeypatch: Any) -> None:
    finding = {
        "check_id": "python.lang.security.audit.subprocess-shell-true",
        "path": "PLACEHOLDER",
        "start": {"line": 5, "col": 38, "offset": 91},
        "end": {"line": 5, "col": 42, "offset": 95},
        "extra": {
            "severity": "ERROR",
            "message": "Found subprocess with shell=True",
            "metadata": {
                "cwe": ["CWE-78: OS Command Injection"],
                "owasp": ["A03:2021 - Injection"],
            },
        },
    }

    def fake_run(cmd: list, **kwargs: Any) -> FakeCompletedProcess:
        if "--version" in cmd:
            return FakeCompletedProcess(0, "1.90.0")
        temp_path = cmd[-1]
        finding["path"] = temp_path
        return FakeCompletedProcess(0, json.dumps({"results": [finding], "errors": []}))

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = SemgrepAnalyzer()
    result = analyzer.check_code(
        "import subprocess\nsubprocess.run('ls', shell=True)\n"
    )
    assert result.total_issues == 1
    assert result.error_count == 1
    assert result.warning_count == 0
    issue = result.issues[0]
    assert issue.check_id == "python.lang.security.audit.subprocess-shell-true"
    assert issue.line == 5
    assert issue.column == 38
    assert issue.end_line == 5
    assert issue.end_column == 42
    assert issue.severity == "ERROR"
    assert issue.cwe == ["CWE-78: OS Command Injection"]
    assert issue.owasp == ["A03:2021 - Injection"]


def test_check_code_findings_missing_metadata(monkeypatch: Any) -> None:
    def fake_run(cmd: list, **kwargs: Any) -> FakeCompletedProcess:
        if "--version" in cmd:
            return FakeCompletedProcess(0, "1.90.0")
        temp_path = cmd[-1]
        finding = {
            "check_id": "rule-x",
            "path": temp_path,
            "start": {},
            "end": {},
            "extra": {},
        }
        return FakeCompletedProcess(0, json.dumps({"results": [finding], "errors": []}))

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = SemgrepAnalyzer()
    result = analyzer.check_code("x = 1\n")
    assert result.total_issues == 1
    issue = result.issues[0]
    assert issue.line == 0
    assert issue.column == 0
    assert issue.severity == "INFO"
    assert issue.message == ""
    assert issue.cwe == []
    assert issue.owasp == []


def test_check_code_filters_unrelated_paths(monkeypatch: Any) -> None:
    def fake_run(cmd: list, **kwargs: Any) -> FakeCompletedProcess:
        if "--version" in cmd:
            return FakeCompletedProcess(0, "1.90.0")
        finding = {
            "check_id": "rule-x",
            "path": "/some/unrelated/file.py",
            "start": {"line": 1, "col": 1},
            "end": {"line": 1, "col": 2},
            "extra": {"severity": "WARNING", "message": "noise"},
        }
        return FakeCompletedProcess(0, json.dumps({"results": [finding], "errors": []}))

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = SemgrepAnalyzer()
    result = analyzer.check_code("x = 1\n")
    assert result.total_issues == 0


def test_check_code_empty_stdout(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "1.90.0"),
        FakeCompletedProcess(0, ""),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = SemgrepAnalyzer()
    result = analyzer.check_code("x = 1\n")
    assert result.total_issues == 0


def test_check_code_bad_returncode_with_stderr(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "1.90.0"),
        FakeCompletedProcess(7, "", "invalid config"),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = SemgrepAnalyzer()
    with pytest.raises(RuntimeError, match="Semgrep check failed"):
        analyzer.check_code("x = 1\n")


def test_check_code_bad_returncode_empty_stderr(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "1.90.0"),
        FakeCompletedProcess(7, "", ""),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = SemgrepAnalyzer()
    with pytest.raises(RuntimeError, match="Semgrep check failed"):
        analyzer.check_code("x = 1\n")


def test_check_code_json_decode_error(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "1.90.0"),
        FakeCompletedProcess(0, "NOT_VALID_JSON"),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = SemgrepAnalyzer()
    with pytest.raises(RuntimeError, match="Failed to parse Semgrep output"):
        analyzer.check_code("x = 1\n")


def test_check_code_timeout(monkeypatch: Any) -> None:
    call_count = [0]

    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        call_count[0] += 1
        if call_count[0] == 1:
            return FakeCompletedProcess(0, "1.90.0")
        raise subprocess.TimeoutExpired("semgrep", 60)

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = SemgrepAnalyzer()
    with pytest.raises(RuntimeError, match="Semgrep check timed out"):
        analyzer.check_code("x = 1\n")


def test_check_code_file_not_found(monkeypatch: Any) -> None:
    call_count = [0]

    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        call_count[0] += 1
        if call_count[0] == 1:
            return FakeCompletedProcess(0, "1.90.0")
        raise FileNotFoundError("semgrep vanished")

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = SemgrepAnalyzer()
    with pytest.raises(RuntimeError, match="Failed to run Semgrep"):
        analyzer.check_code("x = 1\n")


def test_check_code_permission_error(monkeypatch: Any) -> None:
    call_count = [0]

    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        call_count[0] += 1
        if call_count[0] == 1:
            return FakeCompletedProcess(0, "1.90.0")
        raise PermissionError("permission denied")

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = SemgrepAnalyzer()
    with pytest.raises(RuntimeError, match="Failed to run Semgrep"):
        analyzer.check_code("x = 1\n")


def test_check_code_default_config_omits_metrics_off(monkeypatch: Any) -> None:
    """--metrics=off cannot be combined with --config auto; must be omitted for auto."""
    captured_cmds = []

    def fake_run(cmd: list, **kwargs: Any) -> FakeCompletedProcess:
        captured_cmds.append(cmd)
        if "--version" in cmd:
            return FakeCompletedProcess(0, "1.90.0")
        return FakeCompletedProcess(0, json.dumps({"results": [], "errors": []}))

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = SemgrepAnalyzer()
    analyzer.check_code("x = 1\n", config="auto")
    scan_cmd = captured_cmds[-1]
    assert "--metrics=off" not in scan_cmd


def test_check_code_explicit_config_adds_metrics_off(monkeypatch: Any) -> None:
    captured_cmds = []

    def fake_run(cmd: list, **kwargs: Any) -> FakeCompletedProcess:
        captured_cmds.append(cmd)
        if "--version" in cmd:
            return FakeCompletedProcess(0, "1.90.0")
        return FakeCompletedProcess(0, json.dumps({"results": [], "errors": []}))

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = SemgrepAnalyzer()
    analyzer.check_code("x = 1\n", config="p/security-audit")
    scan_cmd = captured_cmds[-1]
    assert "--metrics=off" in scan_cmd
