# MCP Server Analyzer

MCP Server Analyzer is a Python-based Model Context Protocol (MCP) server that provides comprehensive Python code analysis using RUFF linting and VULTURE dead code detection. Built with FastMCP framework and UV package manager for modern Python development workflows.

**ALWAYS reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working Effectively

### Prerequisites and Setup
- Python 3.10+ required (3.12+ recommended)
- Install UV package manager: `pip install uv`
- Docker (optional, for containerized deployment)

### Essential Commands (VALIDATED WORKING)
- **Install dependencies**: `uv sync --dev` -- takes 2-3 seconds
- **Run tests**: `uv run pytest -v` -- takes 3-5 seconds for 13 tests
- **Run tests with coverage**: `uv run pytest --cov=src/mcp_server_analyzer --cov-report=html` -- takes 5-6 seconds
- **Lint code**: `uv run ruff check src tests` -- takes < 1 second  
- **Format code**: `uv run ruff format src tests` -- takes < 1 second
- **Check format only**: `uv run ruff format --check src tests` -- takes < 1 second
- **Start MCP server**: `uv run mcp-server-analyzer` (runs STDIO-based MCP server)

### Critical Timing Information
- **NEVER CANCEL builds or tests** - All operations complete in under 10 seconds
- Dependency installation: 2-3 seconds  
- Test suite: 3-5 seconds for full suite
- Coverage reporting: 5-6 seconds
- Linting operations: Sub-second

## Validation

### Always Validate Changes With These Steps
1. **Lint the code**: `uv run ruff check src tests` 
2. **Format the code**: `uv run ruff format src tests`
3. **Run the full test suite**: `uv run pytest -v`
4. **Test the MCP server starts**: `echo 'print("test")' | timeout 5 uv run mcp-server-analyzer`

### Manual Testing Scenarios
After making changes to analyzers or server functionality, always test:

**Test RUFF analyzer integration**:
```bash
cd /home/runner/work/mcp-server-analyzer/mcp-server-analyzer
PYTHONPATH=src uv run python -c "
from mcp_server_analyzer.analyzers.ruff import RuffAnalyzer
analyzer = RuffAnalyzer()
result = analyzer.check_code('import os\nprint(\"test\")')
print(f'Found {result.total_issues} issues')
"
```

**Test VULTURE analyzer integration**:
```bash
PYTHONPATH=src uv run python -c "
from mcp_server_analyzer.analyzers.vulture import VultureAnalyzer
analyzer = VultureAnalyzer()
result = analyzer.scan_code('import os\ndef unused(): pass\nprint(\"test\")')
print(f'Found {result.total_items} unused items')
"
```

**Test MCP server basic functionality**:
```bash
# Server should start and display FastMCP banner, then wait for input
echo 'print("hello")' | timeout 3 uv run mcp-server-analyzer
```

## CI/CD and Quality Requirements

### Pre-commit Validation  
**WARNING**: Pre-commit hooks require Python 3.11 which may not be available in all environments
- **If Python 3.11 available**: `pip install pre-commit && pre-commit run --all-files`  
- **If Python 3.11 NOT available**: Run manual validation commands above instead

### CI Pipeline Requirements
The CI pipeline (.github/workflows/ci-cd.yml) runs:
- Pre-commit hooks (Python 3.11 only)
- Tests on Python 3.10, 3.11, 3.12
- Code coverage with Codecov upload
- Docker multi-arch builds (linux/amd64, linux/arm64)  
- PyPI publishing for tags
- Security signing with Sigstore and Cosign

**Before pushing changes, ALWAYS run**:
- `uv run ruff check src tests`
- `uv run ruff format src tests`  
- `uv run pytest -v`

## Docker Support

### Docker Limitations  
**KNOWN ISSUE**: Docker builds may fail in sandboxed environments due to SSL certificate issues with PyPI downloads during `uv sync` operations.

**Working Docker commands**:
- **Pre-built image**: `docker run ghcr.io/anselmoo/mcp-server-analyzer`
- **Test script**: `./docker-test.sh` (builds and tests Docker image)

**If Docker build fails**:
- Use the pre-built images from GitHub Container Registry
- Docker builds work in GitHub Actions CI with proper certificates

## Repository Structure and Key Files

### Source Code Layout
```
src/mcp_server_analyzer/
├── __init__.py           # Package initialization
├── __main__.py           # Main entry point
├── server.py             # FastMCP server implementation 
├── models.py             # Pydantic models for API responses
└── analyzers/            # Core analyzer implementations
    ├── ruff.py           # RUFF linting integration  
    └── vulture.py        # VULTURE dead code detection
```

### Test Structure
```
tests/
├── conftest.py           # Pytest configuration and fixtures
├── test_basic.py         # Basic functionality tests
├── test_server.py        # Server integration tests  
└── test_working.py       # Working analyzer tests
```

### Configuration Files
- `pyproject.toml` - Project metadata, dependencies, tool configurations
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `uv.lock` - Locked dependency versions
- `Dockerfile` - Multi-stage Docker build

### Important Directories
- `examples/` - Sample Python files for testing MCP functionality
- `docs/` - Documentation including CI/CD setup guide
- `.github/workflows/ci-cd.yml` - Comprehensive CI/CD pipeline

## MCP Tools Available

The server provides these MCP tools:
- `ruff-check` - Lint Python code with RUFF
- `ruff-format` - Format Python code with RUFF  
- `ruff-check-ci` - CI/CD optimized RUFF output
- `vulture-scan` - Dead code detection with VULTURE
- `analyze-code` - Combined RUFF + VULTURE analysis

## Troubleshooting Common Issues

### Environment Issues
- **UV not found**: Install with `pip install uv`
- **Python version**: Ensure Python 3.10+ is active
- **Import errors**: Set `PYTHONPATH=src` when running direct Python commands

### Build/Test Failures
- **Test failures**: Ensure dependencies installed with `uv sync --dev`
- **Type checking errors**: Models use Pydantic v2, check field names (e.g., `issue.rule` not `issue.code`)
- **Coverage issues**: Use `pytest --cov=src/mcp_server_analyzer` format

### MCP Server Issues  
- **Server won't start**: Check FastMCP and dependencies with `uv run mcp-server-analyzer --help`
- **Missing tools**: Verify RUFF and VULTURE are available in virtual environment
- **STDIO timeout**: MCP server uses STDIO transport - expects JSON-RPC messages, not plain text

## Development Workflow

### Making Changes
1. `uv sync --dev` - Install/update dependencies
2. Make your changes to source code
3. `uv run ruff format src tests` - Format code  
4. `uv run ruff check src tests` - Lint code
5. `uv run pytest -v` - Run tests
6. Test MCP functionality manually (see validation section above)
7. Commit and push changes

### Adding New Features
- Add tests first in `tests/` directory
- Update models in `models.py` if adding new data structures
- Add MCP tools in `server.py` using `@app.tool` decorator
- Update documentation and examples as needed

### Release Process
1. Update version in `pyproject.toml` 
2. Update `CHANGELOG.md`
3. Create tag: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0` 
5. GitHub Actions handles PyPI publishing and Docker builds automatically

## Quick Reference - Common Commands

### Development Setup
```bash
# Install UV package manager
pip install uv

# Install dependencies and setup environment  
uv sync --dev

# Verify installation
uv run mcp-server-analyzer --help
```

### Code Quality (Run Before Commits)
```bash  
# Format code
uv run ruff format src tests

# Lint code
uv run ruff check src tests  

# Run tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=src/mcp_server_analyzer --cov-report=html
```

### Manual Testing Commands
```bash
# Test RUFF integration
PYTHONPATH=src uv run python -c "
from mcp_server_analyzer.analyzers.ruff import RuffAnalyzer
analyzer = RuffAnalyzer()  
result = analyzer.check_code('import os\nprint(\"test\")')
print(f'Found {result.total_issues} issues')
"

# Test VULTURE integration  
PYTHONPATH=src uv run python -c "
from mcp_server_analyzer.analyzers.vulture import VultureAnalyzer
analyzer = VultureAnalyzer()
result = analyzer.scan_code('import os\ndef unused(): pass\nprint(\"test\")')
print(f'Found {result.total_items} unused items')
"

# Test MCP server startup
echo 'print("hello")' | timeout 3 uv run mcp-server-analyzer
```

### Docker Commands (May Fail in Sandboxed Environments)
```bash
# Use pre-built image
docker run ghcr.io/anselmoo/mcp-server-analyzer

# Test with local build (if certificates work)
./docker-test.sh
```