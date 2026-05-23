# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.2.x   | Yes       |
| < 0.2   | No        |

## Reporting a Vulnerability

**Please do not open public GitHub issues for security vulnerabilities.**

Report vulnerabilities privately via [GitHub Security Advisories](https://github.com/Anselmoo/mcp-server-analyzer/security/advisories/new).

Include:
- A description of the vulnerability and its potential impact
- Steps to reproduce
- Affected versions
- Any suggested mitigations

You will receive a response within 48 hours. If confirmed, a fix will be released as soon as possible, typically within 7 days for critical issues.

## Security Architecture

### How the Server Processes Code

- **In-memory only**: Code passed to tools is written to temporary files, analyzed, and the temp files are immediately deleted. No code is persisted or logged.
- **No network access**: The server makes no outbound network calls during analysis.
- **Subprocess isolation**: Analysis tools (ruff, ty, vulture) are invoked as child processes with captured stdout/stderr. No shell expansion is used.
- **Input validation**: All tool inputs are validated before processing; empty inputs are rejected with a structured error.

### Supply Chain Security

- All PyPI releases use [OIDC Trusted Publishing](https://docs.pypi.org/trusted-publishers/) — no long-lived API tokens.
- Release artifacts are signed with [Sigstore](https://sigstore.dev/).
- Docker images are signed with [Cosign](https://docs.sigstore.dev/cosign/overview/).
- SBOM (SPDX format) is generated and attached to every GitHub Release.
- Dependencies are managed with `uv` and a locked `uv.lock` for reproducible builds.

### Known Limitations

- The server spawns subprocesses to run ruff, ty, and vulture. A compromised dependency in those tools could affect analysis results.
- Code passed to the `project_path` parameter of `ty-check` is used as a filesystem path — callers should validate this input when wrapping the server.
