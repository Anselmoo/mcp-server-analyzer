# MCP Server Analyzer

[![SafeSkill 92/100](https://img.shields.io/badge/SafeSkill-92%2F100_Verified%20Safe-brightgreen)](https://safeskill.dev/scan/anselmoo-mcp-server-analyzer)
[![CI/CD Pipeline](https://github.com/anselmoo/mcp-server-analyzer/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/anselmoo/mcp-server-analyzer/actions/workflows/ci-cd.yml)
[![PyPI version](https://badge.fury.io/py/mcp-server-analyzer.svg)](https://badge.fury.io/py/mcp-server-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server providing comprehensive Python, JavaScript, and TypeScript code analysis and security scanning via [**Ruff**](https://docs.astral.sh/ruff/) linting, [**ty**](https://docs.astral.sh/ty/) type checking, [**Vulture**](https://github.com/jendrikseipp/vulture) dead code detection, [**Biome**](https://biomejs.dev/) JS/TS linting and formatting, [**Semgrep**](https://semgrep.dev/) security/SAST scanning, [**actionlint**](https://github.com/rhysd/actionlint) GitHub Actions workflow linting, and [**gitleaks**](https://github.com/gitleaks/gitleaks) secret scanning.

## Quick Start

=== "uvx (recommended)"
    ```bash
    uvx mcp-server-analyzer
    ```

=== "pip"
    ```bash
    pip install mcp-server-analyzer
    mcp-server-analyzer
    ```

=== "Docker"
    ```bash
    docker run -i --rm ghcr.io/anselmoo/mcp-server-analyzer
    ```

=== "From source"
    ```bash
    git clone https://github.com/Anselmoo/mcp-server-analyzer.git
    cd mcp-server-analyzer
    uv sync --dev
    uv run mcp-server-analyzer
    ```

## Client Configuration

=== "Claude Desktop"
    Add to `claude_desktop_config.json`:
    ```json
    {
      "mcpServers": {
        "analyzer": {
          "command": "uvx",
          "args": ["mcp-server-analyzer"]
        }
      }
    }
    ```

=== "VS Code"
    Add to `.vscode/mcp.json`:
    ```json
    {
      "servers": {
        "analyzer": {
          "type": "stdio",
          "command": "uvx",
          "args": ["mcp-server-analyzer"]
        }
      }
    }
    ```

=== "Zed"
    Add to `settings.json`:
    ```json
    "context_servers": {
      "analyzer": {
        "command": "uvx",
        "args": ["mcp-server-analyzer"]
      }
    }
    ```

=== "Claude Code (.mcp.json)"
    Place `.mcp.json` at the project root:
    ```json
    {
      "mcpServers": {
        "analyzer": {
          "command": "uvx",
          "args": ["mcp-server-analyzer"]
        }
      }
    }
    ```

## Features

| Feature | Description |
|---------|-------------|
| **Ruff linting** | Style violations, potential errors, auto-fix hints |
| **Ruff formatting** | Code formatting and consistency |
| **ty type checking** | Fast static type analysis |
| **Vulture dead code** | Unused imports, functions, variables |
| **Biome JS/TS linting** | Style violations, potential errors, auto-fix hints |
| **Biome JS/TS formatting** | Code formatting and consistency |
| **Semgrep security scan** | SAST findings with CWE/OWASP metadata |
| **actionlint workflow linting** | GitHub Actions workflow YAML validation |
| **gitleaks secret scanning** | Hardcoded secret detection (redacted results) |
| **Combined analysis** | Quality score (0-100) across all tools |
| **CI output formats** | json, gitlab, github, sarif |

## Data Handling

- Code is written to a **temporary file**, analyzed, then **immediately deleted** — nothing is persisted.
- The server makes **no outbound network calls** during analysis, except `semgrep-check`'s default `config="auto"`, which fetches rules from the Semgrep registry — pass an explicit local config to run it fully offline.
- No telemetry or usage data is collected, except Semgrep's own usage metrics when `config="auto"` resolves rules from the registry (a Semgrep requirement, not disableable by this server).
- `gitleaks-scan` always redacts secret values — raw secrets are never returned.

## Available Tools

See the [Tools Reference](tools.md) for full parameter documentation.

| Tool | Purpose |
|------|---------|
| `ruff-check` | Lint Python code |
| `ruff-format` | Format Python code |
| `ruff-check-ci` | CI/CD optimized output |
| `ty-check` | Type-check Python code |
| `vulture-scan` | Dead code detection |
| `biome-check` | Lint JS/TS code |
| `biome-format` | Format JS/TS code |
| `semgrep-check` | Security/SAST scan |
| `actionlint-check` | Lint GitHub Actions workflows |
| `gitleaks-scan` | Secret scanning (redacted) |
| `analyze-code` | Combined analysis + score |
