# Contributing Guide

Thank you for your interest in contributing to **mcp-server-analyzer**!

## Getting Started

```bash
git clone https://github.com/Anselmoo/mcp-server-analyzer.git
cd mcp-server-analyzer
uv sync --dev
```

## Development Workflow

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/mcp_server_analyzer --cov-report=html

# Lint
uv run ruff check src tests

# Format
uv run ruff format src tests

# Type check
uv run ty check src tests

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

## Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new analysis tool
fix: handle empty ruff output
docs: update tool reference
test: add edge case for ty parser
chore: bump dependencies
```

Commit subjects are validated in CI via `repo-release-tools`.

## Pull Request Process

1. Fork the repository and create a branch from `main`.
2. Add or update tests to cover your change.
3. Ensure `uv run pre-commit run --all-files` passes.
4. Update `CHANGELOG.md` under the `[Unreleased]` section.
5. Open a pull request — CI will run the full test matrix.

## Adding a New Analyzer

1. Create `src/mcp_server_analyzer/analyzers/<name>.py` with a class following the pattern of `RuffAnalyzer`.
2. Add corresponding Pydantic models to `src/mcp_server_analyzer/models.py`.
3. Register the tool in `server.py` with `@mcp.tool(...)`.
4. Export the new analyzer from `src/mcp_server_analyzer/analyzers/__init__.py`.
5. Add tests under `tests/`.

## Code Style

- All public functions should have type annotations.
- Ruff enforces `select = ["ALL"]` with a minimal ignore list — run `uv run ruff check` before committing.
- Use `raise ToolError(...)` (not return-dict error patterns) to surface errors from MCP tools.

## Reporting Bugs

Open a [GitHub issue](https://github.com/Anselmoo/mcp-server-analyzer/issues). For security issues, see [SECURITY.md](SECURITY.md).
