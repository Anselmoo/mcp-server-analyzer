"""Tests for the VultureAnalyzer module."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from mcp_server_analyzer.analyzers.vulture import MAX_CONFIDENCE, VultureAnalyzer


def test_scan_code_parses_vulture_output(monkeypatch):
    """Ensure scan_code parses Vulture output and cleans up temp files."""
    monkeypatch.setattr(VultureAnalyzer, "_check_vulture_installation", lambda _: None)

    captured_commands: list[list[str]] = []
    created_temp_paths: list[Path] = []

    def fake_run(cmd, **_kwargs):
        captured_commands.append(cmd)
        if cmd[:2] == ["vulture", "--version"]:
            return SimpleNamespace(returncode=0, stdout="2.7", stderr="")

        temp_path = Path(cmd[1])
        created_temp_paths.append(temp_path)
        stdout = f"{temp_path}:7: unused function 'foo' (90% confidence, 1 lines)\n"
        return SimpleNamespace(returncode=3, stdout=stdout, stderr="")

    monkeypatch.setattr(
        "mcp_server_analyzer.analyzers.vulture.subprocess.run", fake_run
    )

    analyzer = VultureAnalyzer()
    result = analyzer.scan_code("def foo():\n    pass\n", min_confidence=85)

    assert "--min-confidence=85" in captured_commands[-1]
    assert result.total_items == 1
    item = result.unused_items[0]
    assert item.name == "foo"
    assert item.type == "function"
    assert item.line == 7
    assert result.high_confidence_items == 1
    assert created_temp_paths
    assert not created_temp_paths[0].exists()


def test_scan_code_rejects_invalid_confidence(monkeypatch):
    """scan_code should validate the confidence bounds."""
    monkeypatch.setattr(VultureAnalyzer, "_check_vulture_installation", lambda _: None)
    analyzer = VultureAnalyzer()

    with pytest.raises(ValueError, match="between 0 and"):
        analyzer.scan_code("print('hi')", min_confidence=MAX_CONFIDENCE + 1)

    with pytest.raises(ValueError, match="between 0 and"):
        analyzer.scan_code("print('hi')", min_confidence=-1)


def test_parse_vulture_output_filters_other_files(monkeypatch, tmp_path):
    """Only entries for the analyzed temp file should be returned."""
    monkeypatch.setattr(VultureAnalyzer, "_check_vulture_installation", lambda _: None)
    analyzer = VultureAnalyzer()

    target_file = tmp_path / "target.py"
    target_file.write_text("print('hello')\n")
    other_file = tmp_path / "other.py"
    other_file.write_text("print('world')\n")

    output = (
        f"{target_file}:10: unused variable 'alpha' (60% confidence)\n"
        f"{other_file}:12: unused variable 'beta' (60% confidence)\n"
    )

    items = analyzer._parse_vulture_output(output, str(target_file))

    assert len(items) == 1
    item = items[0]
    assert item.name == "alpha"
    assert item.type == "variable"
    assert item.line == 10
