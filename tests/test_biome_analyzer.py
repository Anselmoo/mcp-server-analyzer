"""Unit tests for BiomeAnalyzer using monkeypatching (no real biome needed)."""

import json
import subprocess
from typing import Any

import pytest

from mcp_server_analyzer.analyzers.biome import (
    BiomeAnalyzer,
)


class FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


# ── _find_biome_cmd ───────────────────────────────────────────────────────────


def test_find_biome_cmd_uses_local_biome(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: FakeCompletedProcess(0, "biome 2.0.0")
    )
    analyzer = BiomeAnalyzer()
    assert analyzer._biome_cmd == ["biome"]


def test_find_biome_cmd_falls_back_to_npx(monkeypatch: Any) -> None:
    call_count = [0]

    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        call_count[0] += 1
        if call_count[0] == 1:
            raise FileNotFoundError("biome not in PATH")
        return FakeCompletedProcess(0, "biome 2.0.0")

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = BiomeAnalyzer()
    assert analyzer._biome_cmd == ["npx", "--no-install", "biome"]


def test_find_biome_cmd_raises_when_neither_available(monkeypatch: Any) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        raise FileNotFoundError("not found")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="Biome is not available"):
        BiomeAnalyzer()


def test_find_biome_cmd_raises_on_called_process_error(monkeypatch: Any) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        raise subprocess.CalledProcessError(1, "biome")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="Biome is not available"):
        BiomeAnalyzer()


def test_find_biome_cmd_raises_on_timeout(monkeypatch: Any) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        raise subprocess.TimeoutExpired("biome", 10)

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="Biome is not available"):
        BiomeAnalyzer()


# ── check_code ────────────────────────────────────────────────────────────────


def test_check_code_no_issues(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "biome 2.0.0"),
        FakeCompletedProcess(
            0, json.dumps({"diagnostics": [], "summary": {"errors": 0}})
        ),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = BiomeAnalyzer()
    result = analyzer.check_code("const x = 1;\n", "code.ts")
    assert result.total_issues == 0
    assert result.errors == 0
    assert result.warnings == 0
    assert result.issues == []


def test_check_code_with_issues_and_span(monkeypatch: Any) -> None:
    diagnostic = {
        "category": "lint/suspicious/noDoubleEquals",
        "severity": "error",
        "description": "Use === instead of ==",
        "location": {
            "path": {"file": "code.ts"},
            "span": [10, 12],
            "sourceCode": "const x = 1 == 2",
        },
    }
    responses = [
        FakeCompletedProcess(0, "biome 2.0.0"),
        FakeCompletedProcess(
            1, json.dumps({"diagnostics": [diagnostic], "summary": {}})
        ),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = BiomeAnalyzer()
    result = analyzer.check_code("const x = 1 == 2;\n", "code.ts")
    assert result.total_issues == 1
    assert result.errors == 1
    assert result.warnings == 0
    assert result.issues[0].rule == "lint/suspicious/noDoubleEquals"
    assert result.issues[0].severity == "error"
    assert result.issues[0].start_offset == 10
    assert result.issues[0].end_offset == 12


def test_check_code_with_null_span(monkeypatch: Any) -> None:
    diagnostic = {
        "category": "lint/style/useConst",
        "severity": "warning",
        "description": "Use const",
        "location": {"path": {"file": "code.ts"}, "span": None},
    }
    responses = [
        FakeCompletedProcess(0, "biome 2.0.0"),
        FakeCompletedProcess(
            1, json.dumps({"diagnostics": [diagnostic], "summary": {}})
        ),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = BiomeAnalyzer()
    result = analyzer.check_code("let x = 1;\n", "code.ts")
    assert result.total_issues == 1
    assert result.issues[0].start_offset is None
    assert result.issues[0].end_offset is None
    assert result.warnings == 1


def test_check_code_empty_stdout(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "biome 2.0.0"),
        FakeCompletedProcess(0, ""),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = BiomeAnalyzer()
    result = analyzer.check_code("const x = 1;\n")
    assert result.total_issues == 0


def test_check_code_biome2x_echo(monkeypatch: Any) -> None:
    """Biome 2.x echoes input to stdout instead of JSON; returns empty results with a warning."""
    code = "const x = 1;\n"
    responses = [
        FakeCompletedProcess(0, "biome 2.0.0"),
        FakeCompletedProcess(1, code),  # stdout == input code (Biome 2.x echo mode)
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = BiomeAnalyzer()
    result = analyzer.check_code(code)
    assert result.total_issues == 0
    assert result.issues == []


def test_check_code_bad_returncode_with_stderr(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "biome 2.0.0"),
        FakeCompletedProcess(2, "", "configuration error"),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = BiomeAnalyzer()
    with pytest.raises(RuntimeError, match="Biome check failed"):
        analyzer.check_code("const x = 1;\n")


def test_check_code_bad_returncode_empty_stderr(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "biome 2.0.0"),
        FakeCompletedProcess(2, "", ""),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = BiomeAnalyzer()
    with pytest.raises(RuntimeError, match="Biome check failed"):
        analyzer.check_code("const x = 1;\n")


def test_check_code_json_decode_error(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "biome 2.0.0"),
        FakeCompletedProcess(1, "NOT_VALID_JSON"),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = BiomeAnalyzer()
    with pytest.raises(RuntimeError, match="Failed to parse Biome output"):
        analyzer.check_code("const x = 1;\n")


def test_check_code_timeout(monkeypatch: Any) -> None:
    call_count = [0]

    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        call_count[0] += 1
        if call_count[0] == 1:
            return FakeCompletedProcess(0, "biome 2.0.0")
        raise subprocess.TimeoutExpired("biome", 30)

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = BiomeAnalyzer()
    with pytest.raises(RuntimeError, match="Biome check timed out"):
        analyzer.check_code("const x = 1;\n")


def test_check_code_file_not_found(monkeypatch: Any) -> None:
    call_count = [0]

    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        call_count[0] += 1
        if call_count[0] == 1:
            return FakeCompletedProcess(0, "biome 2.0.0")
        raise FileNotFoundError("biome vanished")

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = BiomeAnalyzer()
    with pytest.raises(RuntimeError, match="Failed to run Biome"):
        analyzer.check_code("const x = 1;\n")


def test_check_code_permission_error(monkeypatch: Any) -> None:
    call_count = [0]

    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        call_count[0] += 1
        if call_count[0] == 1:
            return FakeCompletedProcess(0, "biome 2.0.0")
        raise PermissionError("permission denied")

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = BiomeAnalyzer()
    with pytest.raises(RuntimeError, match="Failed to run Biome"):
        analyzer.check_code("const x = 1;\n")


def test_format_code_permission_error(monkeypatch: Any) -> None:
    call_count = [0]

    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        call_count[0] += 1
        if call_count[0] == 1:
            return FakeCompletedProcess(0, "biome 2.0.0")
        raise PermissionError("permission denied")

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = BiomeAnalyzer()
    with pytest.raises(RuntimeError, match="Failed to run Biome"):
        analyzer.format_code("const x = 1;\n")


def test_check_code_missing_location_fields(monkeypatch: Any) -> None:
    """Diagnostic with missing/null location fields handled gracefully."""
    diagnostic = {
        "category": "lint/style/useConst",
        "severity": "information",
        "description": "Use const",
        "location": None,
    }
    responses = [
        FakeCompletedProcess(0, "biome 2.0.0"),
        FakeCompletedProcess(
            1, json.dumps({"diagnostics": [diagnostic], "summary": {}})
        ),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = BiomeAnalyzer()
    result = analyzer.check_code("let x = 1;\n", "fallback.ts")
    assert result.total_issues == 1
    assert result.issues[0].file == "fallback.ts"
    assert result.issues[0].start_offset is None


# ── format_code ───────────────────────────────────────────────────────────────


def test_format_code_unchanged(monkeypatch: Any) -> None:
    code = "const x = 1;\n"
    responses = [
        FakeCompletedProcess(0, "biome 2.0.0"),
        FakeCompletedProcess(0, code),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = BiomeAnalyzer()
    result = analyzer.format_code(code)
    assert result.changed is False
    assert result.formatted_code == code


def test_format_code_changed(monkeypatch: Any) -> None:
    code = "const x=1\n"
    formatted = "const x = 1;\n"
    responses = [
        FakeCompletedProcess(0, "biome 2.0.0"),
        FakeCompletedProcess(0, formatted),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = BiomeAnalyzer()
    result = analyzer.format_code(code)
    assert result.changed is True
    assert result.formatted_code == formatted


def test_format_code_bad_returncode(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "biome 2.0.0"),
        FakeCompletedProcess(1, "", "syntax error in code"),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = BiomeAnalyzer()
    with pytest.raises(RuntimeError, match="Biome format failed"):
        analyzer.format_code("const x=1\n")


def test_format_code_bad_returncode_empty_stderr(monkeypatch: Any) -> None:
    responses = [
        FakeCompletedProcess(0, "biome 2.0.0"),
        FakeCompletedProcess(2, "", ""),
    ]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: responses.pop(0))
    analyzer = BiomeAnalyzer()
    with pytest.raises(RuntimeError, match="Biome format failed"):
        analyzer.format_code("const x=1\n")


def test_format_code_timeout(monkeypatch: Any) -> None:
    call_count = [0]

    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        call_count[0] += 1
        if call_count[0] == 1:
            return FakeCompletedProcess(0, "biome 2.0.0")
        raise subprocess.TimeoutExpired("biome", 30)

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = BiomeAnalyzer()
    with pytest.raises(RuntimeError, match="Biome format timed out"):
        analyzer.format_code("const x=1\n")


def test_format_code_file_not_found(monkeypatch: Any) -> None:
    call_count = [0]

    def fake_run(*args: Any, **kwargs: Any) -> FakeCompletedProcess:
        call_count[0] += 1
        if call_count[0] == 1:
            return FakeCompletedProcess(0, "biome 2.0.0")
        raise FileNotFoundError("biome vanished")

    monkeypatch.setattr(subprocess, "run", fake_run)
    analyzer = BiomeAnalyzer()
    with pytest.raises(RuntimeError, match="Failed to run Biome"):
        analyzer.format_code("const x=1\n")
