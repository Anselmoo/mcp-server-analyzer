"""Unit tests for GitleaksAnalyzer using monkeypatching (no real gitleaks needed)."""

import json
import subprocess
from typing import Any

import pytest

from mcp_server_analyzer.analyzers.gitleaks import GitleaksAnalyzer


class FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


# ── _check_gitleaks_installation ────────────────────────────────────────────


def test_check_installation_ok(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: FakeCompletedProcess(0, "8.30.1")
    )
    GitleaksAnalyzer()


def test_check_installation_raises_on_called_process_error(monkeypatch: Any) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        raise subprocess.CalledProcessError(1, "gitleaks")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="gitleaks is not available"):
        GitleaksAnalyzer()


def test_check_installation_raises_on_file_not_found(monkeypatch: Any) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        raise FileNotFoundError("not found")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="gitleaks is not available"):
        GitleaksAnalyzer()


def test_check_installation_raises_on_timeout(monkeypatch: Any) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        raise subprocess.TimeoutExpired("gitleaks", 10)

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="gitleaks is not available"):
        GitleaksAnalyzer()


# ── scan_code ────────────────────────────────────────────────────────────────


def test_scan_code_no_findings(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "8.30.1"),
        FakeCompletedProcess(0, "[]"),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = GitleaksAnalyzer()
    result = analyzer.scan_code("hello world\n")
    assert result.total_findings == 0
    assert result.findings == []


def test_scan_code_redacts_secret_values(monkeypatch: Any) -> None:
    """Security-critical: raw secret values must never be returned, always 'REDACTED'."""
    finding = {
        "RuleID": "private-key",
        "Description": "Identified a Private Key",
        "StartLine": 1,
        "EndLine": 28,
        "StartColumn": 1,
        "EndColumn": 26,
        "Match": "REDACTED",
        "Secret": "REDACTED",
        "File": "/private/var/tmp-workdir/some-temp-file.pem",
        "Entropy": 6.01,
    }
    responses = [
        FakeCompletedProcess(0, "8.30.1"),
        FakeCompletedProcess(1, json.dumps([finding])),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = GitleaksAnalyzer()
    result = analyzer.scan_code("-----BEGIN PRIVATE KEY-----\n...\n", "key.pem")
    assert result.total_findings == 1
    found = result.findings[0]
    assert found.rule_id == "private-key"
    assert found.secret == "REDACTED"  # noqa: S105 -- asserting redaction, not a real secret
    assert found.match == "REDACTED"
    # caller-supplied filename must override the raw OS temp path gitleaks reports
    assert found.file == "key.pem"
    assert found.start_line == 1
    assert found.end_line == 28
    assert found.start_column == 1
    assert found.end_column == 26


def test_scan_code_missing_optional_fields(monkeypatch: Any) -> None:
    finding = {"RuleID": "generic-api-key"}
    responses = [
        FakeCompletedProcess(0, "8.30.1"),
        FakeCompletedProcess(1, json.dumps([finding])),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = GitleaksAnalyzer()
    result = analyzer.scan_code("api_key = 'x'\n")
    assert result.total_findings == 1
    found = result.findings[0]
    assert found.description == ""
    assert found.secret == "REDACTED"  # noqa: S105 -- asserting redaction, not a real secret
    assert found.match == "REDACTED"
    assert found.start_line == 0


def test_scan_code_empty_stdout(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "8.30.1"),
        FakeCompletedProcess(0, ""),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = GitleaksAnalyzer()
    result = analyzer.scan_code("hello world\n")
    assert result.total_findings == 0


def test_scan_code_bad_returncode_with_stderr(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "8.30.1"),
        FakeCompletedProcess(2, "", "invalid config"),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = GitleaksAnalyzer()
    with pytest.raises(RuntimeError, match="gitleaks scan failed"):
        analyzer.scan_code("hello world\n")


def test_scan_code_bad_returncode_empty_stderr(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "8.30.1"),
        FakeCompletedProcess(2, "", ""),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = GitleaksAnalyzer()
    with pytest.raises(RuntimeError, match="gitleaks scan failed"):
        analyzer.scan_code("hello world\n")


def test_scan_code_json_decode_error(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "8.30.1"),
        FakeCompletedProcess(1, "NOT_VALID_JSON"),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = GitleaksAnalyzer()
    with pytest.raises(RuntimeError, match="Failed to parse gitleaks output"):
        analyzer.scan_code("hello world\n")


def test_scan_code_timeout(monkeypatch: Any) -> None:
    call_count = [0]

    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        call_count[0] += 1
        if call_count[0] == 1:
            return FakeCompletedProcess(0, "8.30.1")
        raise subprocess.TimeoutExpired("gitleaks", 30)

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = GitleaksAnalyzer()
    with pytest.raises(RuntimeError, match="gitleaks scan timed out"):
        analyzer.scan_code("hello world\n")


def test_scan_code_file_not_found(monkeypatch: Any) -> None:
    call_count = [0]

    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        call_count[0] += 1
        if call_count[0] == 1:
            return FakeCompletedProcess(0, "8.30.1")
        raise FileNotFoundError("gitleaks vanished")

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = GitleaksAnalyzer()
    with pytest.raises(RuntimeError, match="Failed to run gitleaks"):
        analyzer.scan_code("hello world\n")


def test_scan_code_permission_error(monkeypatch: Any) -> None:
    call_count = [0]

    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        call_count[0] += 1
        if call_count[0] == 1:
            return FakeCompletedProcess(0, "8.30.1")
        raise PermissionError("permission denied")

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = GitleaksAnalyzer()
    with pytest.raises(RuntimeError, match="Failed to run gitleaks"):
        analyzer.scan_code("hello world\n")


def test_scan_code_always_passes_redact_flag(monkeypatch: Any) -> None:
    """Security-critical: --redact must always be present in the gitleaks command."""
    captured_cmds = []

    def fake_run(cmd: list, **kwargs: Any) -> FakeCompletedProcess:
        captured_cmds.append(cmd)
        if "version" in cmd:
            return FakeCompletedProcess(0, "8.30.1")
        return FakeCompletedProcess(0, "[]")

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = GitleaksAnalyzer()
    analyzer.scan_code("hello world\n")
    scan_cmd = captured_cmds[-1]
    assert "--redact" in scan_cmd
