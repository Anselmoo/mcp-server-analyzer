"""Tests for the NodeJSInstaller module."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from mcp_server_analyzer.installer import NodeJSInstaller


def _make_installer(tmp_path: Path) -> NodeJSInstaller:
    """Helper to build an installer rooted at a temporary path."""
    return NodeJSInstaller(package_root=tmp_path)


def test_check_nodejs_available_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """check_nodejs_available should call node and npm once each."""
    calls: list[tuple[str, ...]] = []

    def fake_run(cmd: list[str], **_: object) -> SimpleNamespace:
        calls.append(tuple(cmd))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    installer = _make_installer(tmp_path)
    assert installer.check_nodejs_available() is True
    assert calls == [("node", "--version"), ("npm", "--version")]


def test_check_nodejs_available_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """check_nodejs_available should return False when subprocess.run raises."""

    def fake_run(*_: object, **__: object) -> None:
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", fake_run)

    installer = _make_installer(tmp_path)
    assert installer.check_nodejs_available() is False


def test_install_dependencies_missing_node(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """install_dependencies should abort if Node.js is unavailable."""
    monkeypatch.setattr(NodeJSInstaller, "check_nodejs_available", lambda self: False)

    installer = _make_installer(tmp_path)
    assert installer.install_dependencies() is False


def test_install_dependencies_missing_package_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """install_dependencies should warn and return False when package.json is absent."""
    monkeypatch.setattr(NodeJSInstaller, "check_nodejs_available", lambda self: True)

    installer = _make_installer(tmp_path)
    assert installer.install_dependencies() is False


def test_install_dependencies_skips_when_node_modules_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """install_dependencies should skip reinstall when node_modules already populated."""
    monkeypatch.setattr(NodeJSInstaller, "check_nodejs_available", lambda self: True)

    package_json = tmp_path / "package.json"
    package_json.write_text("{}")

    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    (node_modules / "existing").mkdir()

    def fake_run(*_: object, **__: object) -> None:
        raise AssertionError("npm install should not be executed when node_modules is populated")

    monkeypatch.setattr(subprocess, "run", fake_run)

    installer = _make_installer(tmp_path)
    assert installer.install_dependencies() is True


def test_install_dependencies_runs_npm_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """install_dependencies should invoke npm install when dependencies are missing."""
    monkeypatch.setattr(NodeJSInstaller, "check_nodejs_available", lambda self: True)

    package_json = tmp_path / "package.json"
    package_json.write_text("{}")

    calls: list[tuple[tuple[str, ...], Path | None]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append((tuple(cmd), kwargs.get("cwd")))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    installer = _make_installer(tmp_path)
    assert installer.install_dependencies() is True
    assert calls == [(("npm", "install"), tmp_path)]


def test_check_tool_available_falls_back_to_global(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """check_tool_available should retry without cwd when local invocation fails."""
    calls: list[tuple[tuple[str, ...], Path | None]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append((tuple(cmd), kwargs.get("cwd")))
        if kwargs.get("cwd") is not None:
            raise FileNotFoundError
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    installer = _make_installer(tmp_path)
    assert installer.check_tool_available("biome") is True
    assert calls == [
        (("npx", "biome", "--version"), tmp_path),
        (("npx", "biome", "--version"), None),
    ]


def test_check_tool_available_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """check_tool_available should return False when both invocations fail."""

    def fake_run(*_: object, **__: object) -> None:
        raise subprocess.CalledProcessError(returncode=1, cmd="npx")

    monkeypatch.setattr(subprocess, "run", fake_run)

    installer = _make_installer(tmp_path)
    assert installer.check_tool_available("biome") is False


