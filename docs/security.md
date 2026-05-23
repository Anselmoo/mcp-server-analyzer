# Security

## Reporting a Vulnerability

**Do not open public GitHub issues for security vulnerabilities.**

Report privately via [GitHub Security Advisories](https://github.com/Anselmoo/mcp-server-analyzer/security/advisories/new). You will receive a response within 48 hours.

See [SECURITY.md](https://github.com/Anselmoo/mcp-server-analyzer/blob/main/SECURITY.md) for the full policy.

## How Code Is Processed

- Code is written to a **temporary file**, analyzed, and the file is **deleted immediately** — nothing is persisted between calls.
- No outbound network calls are made during analysis.
- No telemetry or usage data is collected.
- Subprocess calls to ruff, ty, and vulture use fixed argument lists — no shell expansion.

## Supply Chain Security

| Control | Implementation |
|---------|---------------|
| PyPI publishing | OIDC Trusted Publishing (no stored API tokens) |
| Release signing | [Sigstore](https://sigstore.dev/) |
| Container signing | [Cosign](https://docs.sigstore.dev/cosign/overview/) |
| SBOM | SPDX JSON attached to every GitHub Release |
| Build provenance | `actions/attest-build-provenance` |
| Dependency locking | `uv.lock` for reproducible installs |

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | Yes       |
| < 0.2   | No        |
