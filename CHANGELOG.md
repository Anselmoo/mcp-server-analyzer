# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-05-23

### Added
- FastMCP 2.x modern patterns: `ToolAnnotations` (readOnlyHint, idempotentHint) and `tags` on all tools
- `ToolError` for clean input-validation errors (empty code guard on all tools)
- `mask_error_details=True` on the server to prevent leaking internal stack traces
- Two MCP resources: `docs://analyzers/overview` (markdown) and `config://analyzer-versions` (JSON)
- `py.typed` marker — the package is now fully typed
- `poethepoet` task runner replacing hatch scripts (`poe test`, `poe lint`, etc.)
- `[tool.rrt.version]` targets for `repo-release-tools` version-bump automation
- Changelog URL added to `[project.urls]`

### Changed
- Minimum Python raised from 3.10 → **3.13**; classifiers now list 3.13 and 3.14
- Build backend switched from `hatchling` → **`uv_build`**
- `fastmcp` minimum version raised from `0.3.0` → **`2.0.0`** (already at 2.10.6 in lock file)
- Server variable renamed from `app` → `mcp` (backward-compat alias `app = mcp` retained)
- Ruff `target-version` updated to `py313`; ty `python-version` updated to `3.13`
- CI/CD pipeline consolidated into a single `ci-cd.yml`; redundant `ci.yml` removed
- Test matrix changed from `[3.10, 3.11, 3.12]` → **`[3.13, 3.14]`**
- Docker image build/push separated into `docker-check` (smoke) and `docker-publish` (on tags)
- `black` removed from dev dependencies (covered by `ruff format`)
- `ignore_decorators` in vulture config updated from `@app.tool` → `@mcp.tool, @mcp.resource`

### CI/CD
- Added **SBOM** generation (SPDX JSON via `anchore/sbom-action`)
- Added **build provenance attestation** via `actions/attest-build-provenance`
- Added **TestPyPI verification** step with 8-attempt retry logic before PyPI publish
- Updated `astral-sh/setup-uv` to v6 across all jobs
- Coverage gate kept at 84%; now enforced with `--cov-fail-under=84` in pytest args

## [0.1.2] - 2025-07-01

### Changed
- CI: increase coverage gate from 65% to 84%
- Refactor: extract helper functions to reduce `analyze_code` complexity
- Fix: make test tool access robust for different fastmcp versions
- Fix: ensure test dependencies are installed in CI workflow

## [0.1.1] - 2025-06-01

### Added
- ty type checker integration and related tests
- Guard for ruff availability checks in server tools

## [0.1.0] - 2025-05-01

### Added
- Initial release with Ruff linting, ty type checking, and Vulture dead code detection
- FastMCP server with six tools: `ruff-check`, `ruff-format`, `ruff-check-ci`, `ty-check`, `vulture-scan`, `analyze-code`
- Docker image support with multi-arch builds
- CI/CD pipeline with PyPI publishing
