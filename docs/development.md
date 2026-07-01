# Development

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Node.js 22+ (for Biome JS/TS analysis)
- Docker (optional)

## Setup

```bash
git clone https://github.com/Anselmoo/mcp-server-analyzer.git
cd mcp-server-analyzer
uv sync --dev

# Install Biome (JS/TS analyzer)
npm ci
```

## Common Tasks

```bash
# Tests
uv run pytest
uv run pytest --cov=src/mcp_server_analyzer --cov-report=html

# Lint & format
uv run ruff check src tests
uv run ruff format src tests

# Type check
uv run ty check src tests

# All pre-commit hooks
uv run pre-commit run --all-files

# Build package
uv build

# Run the server locally (via .mcp.json auto-config in Claude Code)
uv run mcp-server-analyzer
```

## Project Structure

```
mcp-server-analyzer/
├── biome.json           # Biome JS/TS linter/formatter config
├── package.json         # Node.js manifest (Biome dev dependency)
src/mcp_server_analyzer/
├── __init__.py          # Package version
├── __main__.py          # python -m entry point
├── server.py            # FastMCP server, tool & resource definitions
├── models.py            # Pydantic response models
└── analyzers/
    ├── __init__.py
    ├── ruff.py          # Ruff linting & formatting
    ├── ty.py            # ty type checking
    ├── vulture.py       # Vulture dead code detection
    └── biome.py         # Biome JS/TS linting & formatting
tests/
    conftest.py
    test_*.py
```

## Adding a New Analyzer

1. Create `src/mcp_server_analyzer/analyzers/<name>.py` following the `RuffAnalyzer` pattern:
   - `__init__` should raise `RuntimeError` if the tool is not installed
   - Use `tempfile.NamedTemporaryFile` for code input; clean up in `finally`
   - Return a Pydantic model
2. Add result/item models to `models.py`
3. Register the tool in `server.py` with `@mcp.tool(...)`
4. Export from `analyzers/__init__.py`
5. Add tests

## Release Process

1. Update version in `pyproject.toml` and `src/mcp_server_analyzer/__init__.py`
2. Update `CHANGELOG.md`
3. Commit: `git commit -m "chore: release vX.Y.Z"`
4. Tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
5. CI handles PyPI publish, Docker image, and GitHub Release automatically

See [CI/CD Setup](CICD_SETUP.md) for details.
