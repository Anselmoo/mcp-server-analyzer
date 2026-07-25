# MCP Server Analyzer — Claude Instructions

## Branch Naming
- All branches **must** follow `<type>/<kebab-case-description>` (e.g. `docs/update-biome-support`).
- `check-branch-name: "true"` stays enabled in `.github/workflows/ci-cd.yml` — do NOT set it to `false`.
- Worktrees created by Kepler may have non-conventional names (e.g. `update-docs-for-biome`).
  **Before creating a PR**, rename the worktree branch to follow the convention, or CI will fail.
  Use `git branch -m <old> <type>/<new>` then `git push origin -u <type>/<new>`.

## repo-release-tools (rrt)
- Pre-commit hooks: `rrt-branch-name` (pre-commit), `rrt-commit-subject` (commit-msg), `rrt-changelog` (pre-commit).
- All three rrt hooks rely on git internals (`git diff --cached`, branch name) that are unreliable in `pre-commit run --all-files` mode. **CI skips all rrt hooks** via `SKIP: rrt-branch-name,rrt-commit-subject,rrt-changelog` in the `lint` job.
- Release policy is enforced instead by the dedicated **parallel `release-policy` job** (runs `Anselmoo/repo-release-tools@vX.Y.Z` action) on PRs and tags. The `test` job waits for both `lint` and `release-policy`.
- Pin to the **latest tagged version** — check installed version with `uv run rrt --version` and update `rev:` in `.pre-commit-config.yaml` to match.
- Dependabot keeps the CI action (`Anselmoo/repo-release-tools@vX.Y.Z`) up to date automatically — do not pin it manually.

### Useful rrt commands
```bash
uv run rrt branch new <type> "<description>"  # create conventional branch
uv run rrt git commit "<description>"          # conventional commit (infers type from branch)
uv run rrt changelog lint                      # lint [Unreleased] entries for style
uv run rrt bump patch                          # bump patch version across all targets
uv run rrt doctor                              # project health check
uv run rrt release check                       # validate version targets and changelog
```

## GitHub / PR Creation
- `gh` CLI does **not** work in this environment (missing token). Use `mcp__GitKraken__pull_request_create` or the GitHub MCP tool instead.
- Target branch for PRs: `main`.

## Serena MCP (LSP-powered code navigation)
- Call `mcp__serena__initial_instructions` first in any session that uses Serena tools.
- Key tools: `mcp__serena__find_symbol`, `mcp__serena__find_implementations`, `mcp__serena__get_symbols_overview`, `mcp__serena__get_diagnostics_for_file`, `mcp__serena__find_referencing_symbols`.
- Prefer Serena over grep for cross-file symbol lookup and rename operations.

## Biome (JS/TS)
- Run `npm ci` before using `biome-check`/`biome-format` MCP tools or the pre-commit Biome hook.
- `.mcp.json` uses `sh -c "PATH=\"$PWD/node_modules/.bin:$PATH\" uv run mcp-server-analyzer"` to make Biome discoverable in dev mode.

## Semgrep, actionlint, gitleaks
- None of these three are `pyproject.toml` dependencies — do NOT add `semgrep` there. Semgrep's PyPI package bundles its own MCP integration and pins an exact `mcp` version, which downgrades this project's own `mcp`/`fastmcp` resolution if added as a direct dependency (verified: pulls `mcp` from 1.28.x down to 1.23.3).
- `SemgrepAnalyzer` mirrors `BiomeAnalyzer`'s discovery pattern: tries `semgrep` on `PATH` first, falls back to `uvx semgrep` — no install step needed if `uv` is available.
- `semgrep-check`'s default `config="auto"` requires network access to the Semgrep registry and **cannot** be combined with `--metrics=off` (Semgrep rejects that combination outright) — `SemgrepAnalyzer` only appends `--metrics=off` when a non-`"auto"` config is passed.
- `actionlint`/`gitleaks` are Go binaries with no PyPI/npm equivalent — install via `go install .../actionlint/cmd/actionlint@latest` and `go install .../gitleaks/v8@latest`, or let CI's pinned release-binary download handle it.
- `gitleaks-scan` always passes `--redact` — this is a security-critical, non-negotiable invariant. Never remove it or make it optional.

## Dev commands
```bash
uv sync --dev && npm ci                        # full setup
uv run pytest                                  # all tests (100% coverage required)
uv tool run pre-commit run --all-files         # run all hooks
```
