# MCP Server Analyzer for Python 🐍🔍

[![CI/CD Pipeline](https://github.com/anselmoo/mcp-server-analyzer/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/anselmoo/mcp-server-analyzer/actions/workflows/ci-cd.yml)
[![PyPI version](https://badge.fury.io/py/mcp-server-analyzer.svg)](https://badge.fury.io/py/mcp-server-analyzer)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-available-blue.svg)](https://github.com/anselmoo/mcp-server-analyzer/pkgs/container/mcp-server-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Coverage](https://codecov.io/gh/anselmoo/mcp-server-analyzer/branch/main/graph/badge.svg)](https://codecov.io/gh/anselmoo/mcp-server-analyzer)

A powerful [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that provides comprehensive Python code analysis using [**RUFF**](https://docs.astral.sh/ruff/) for linting and [**VULTURE**](https://github.com/jendrikseipp/vulture) for dead code detection. Perfect for AI assistants, IDEs, and automated code review workflows.

## 🚀 Quick Start

### VS Code Integration (One-Click Install)

For quick installation, use one of the one-click install buttons below...

[![Install with UV in VS Code](https://img.shields.io/badge/VS_Code-UV-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=analyzer&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mcp-server-analyzer%22%5D%7D) [![Install with UV in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-UV-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=analyzer&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22mcp-server-analyzer%22%5D%7D&quality=insiders)

[![Install with Docker in VS Code](https://img.shields.io/badge/VS_Code-Docker-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=analyzer&config=%7B%22command%22%3A%22docker%22%2C%22args%22%3A%5B%22run%22%2C%22-i%22%2C%22--rm%22%2C%22ghcr.io%2Fanselmoo%2Fmcp-server-analyzer%22%5D%7D) [![Install with Docker in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Docker-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=analyzer&config=%7B%22command%22%3A%22docker%22%2C%22args%22%3A%5B%22run%22%2C%22-i%22%2C%22--rm%22%2C%22ghcr.io%2Fanselmoo%2Fmcp-server-analyzer%22%5D%7D&quality=insiders)

For manual installation, add the following JSON block to your User Settings (JSON) file in VS Code. You can do this by pressing `Ctrl + Shift + P` and typing `Preferences: Open User Settings (JSON)`.

Optionally, you can add it to a file called `.vscode/mcp.json` in your workspace. This will allow you to share the configuration with others.

> Note that the `mcp` key is needed when using the `mcp.json` file.

**Using uvx (recommended):**

```json
{
  "mcp": {
    "servers": {
      "analyzer": {
        "command": "uvx",
        "args": ["mcp-server-analyzer"]
      }
    }
  }
}
```

**Using Docker:**

```json
{
  "mcp": {
    "servers": {
      "analyzer": {
        "command": "docker",
        "args": ["run", "-i", "--rm", "ghcr.io/anselmoo/mcp-server-analyzer"]
      }
    }
  }
}
```

### Universal Installation

```bash
# Install with uvx (recommended)
uvx install mcp-server-analyzer

# Install with pip
pip install mcp-server-analyzer

# Run with Docker
docker run ghcr.io/anselmoo/mcp-server-analyzer:latest

# Install from source
git clone https://github.com/anselmoo/mcp-server-analyzer.git
cd mcp-server-analyzer
uv sync --dev
uv run mcp-server-analyzer
```

## 📋 Features

- **🔍 RUFF Analysis**: Comprehensive Python linting with auto-fixes
- **🧹 Dead Code Detection**: Find unused imports, functions, and variables with VULTURE
- **📊 Quality Scoring**: Combined analysis with quality metrics
- **🚀 FastMCP Framework**: High-performance MCP server implementation
- **🐳 Docker Ready**: Multi-architecture containers with security signing
- **🔒 Secure**: All releases signed with Sigstore for supply chain security

## 📈 Analysis Examples

### RUFF Linting Preview

See comprehensive linting analysis examples: **[📋 RUFF Analysis Preview](examples/preview-ruff.md)**

### VULTURE Dead Code Detection Preview

Explore dead code detection capabilities: **[🧹 VULTURE Analysis Preview](examples/preview-vulture.md)**

## 🛠️ Available Tools

| Tool            | Description                      | Use Case                             |
| --------------- | -------------------------------- | ------------------------------------ |
| `ruff-check`    | Lint Python code with RUFF       | Style violations, potential errors   |
| `ruff-format`   | Format Python code with RUFF     | Code formatting and consistency      |
| `ruff-check-ci` | CI/CD optimized RUFF output      | GitHub Actions, GitLab CI            |
| `vulture-scan`  | Dead code detection              | Unused imports, functions, variables |
| `analyze-code`  | Combined RUFF + VULTURE analysis | Complete code quality assessment     |

## 🔧 Configuration

### Claude Desktop

Add to your `claude_desktop_config.json`:

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

### Zed

Add to your Zed settings.json:

```json
"context_servers": {
  "analyzer": {
    "command": "uvx",
    "args": ["mcp-server-analyzer"]
  }
}
```

## 🧪 Development

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- [Docker](https://docker.com) (optional)

### Setup

```bash
# Clone repository
git clone https://github.com/anselmoo/mcp-server-analyzer.git
cd mcp-server-analyzer

# Install dependencies
uv sync --dev

# Run tests
uv run pytest

# Run pre-commit hooks
uv tool run pre-commit run --all-files

# Build Docker image
docker build -t mcp-server-analyzer .
```

### Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest --cov=src/mcp_server_analyzer --cov-report=html

# Test specific functionality
uv run pytest tests/test_server.py::TestAnalyzer::test_ruff_analysis
```

## 📊 Quality Metrics

The server provides quality scoring based on:

- **RUFF Issues**: Style violations, potential bugs, complexity metrics
- **Dead Code Detection**: Unused imports, functions, variables
- **Combined Score**: Weighted quality assessment (0-100)

## 🔒 Security

- **Signed Releases**: All releases signed with [Sigstore](https://sigstore.dev/)
- **Container Signing**: Docker images signed with [Cosign](https://docs.sigstore.dev/cosign/overview/)
- **Trusted Publishing**: PyPI releases use GitHub OIDC trusted publishing
- **Vulnerability Scanning**: Automated security scanning in CI/CD
- **Supply Chain Security**: SLSA Build Level 3 compliance

## 📚 Documentation

- **[MCP Specification](https://modelcontextprotocol.io/)** - Learn about Model Context Protocol
- **[FastMCP Framework](https://gofastmcp.com/)** - High-performance MCP implementation
- **[RUFF Documentation](https://docs.astral.sh/ruff/)** - Python linter and formatter
- **[VULTURE Documentation](https://github.com/jendrikseipp/vulture)** - Dead code finder

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Astral](https://astral.sh/) for RUFF and uv
- [Jendrik Seipp](https://github.com/jendrikseipp) for VULTURE
- [Model Context Protocol](https://modelcontextprotocol.io/) team
- [FastMCP](https://gofastmcp.com/) framework

---

**Made with ❤️ for better Python code quality**
