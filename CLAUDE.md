# MCP Server Analyzer — Claude Instructions

## Branch Naming
- All branches **must** follow `<type>/<kebab-case-description>` (e.g. `docs/update-biome-support`).
- `check-branch-name: "true"` stays enabled in `.github/workflows/ci-cd.yml` — do NOT set it to `false`.
- Worktrees created by Kepler may have non-conventional names (e.g. `update-docs-for-biome`).
  **Before creating a PR**, rename the worktree branch to follow the convention, or CI will fail.
  Use `git branch -m <old> <type>/<new>` then `git push origin -u <type>/<new>`.

## repo-release-tools
- Pre-commit uses `https://github.com/Anselmoo/repo-release-tools` hooks (`rrt-branch-name`, `rrt-commit-subject`, `rrt-changelog`).
- Pin to the **latest tagged version** — check `pyproject.toml` (`repo-release-tools>=x.y.z`) and update the `rev:` in `.pre-commit-config.yaml` to match.
- Dependabot keeps the CI action (`Anselmoo/repo-release-tools@vX.Y.Z`) up to date automatically — do not pin it manually.
- CI skips `rrt-branch-name` in the `pre-commit run` step via `SKIP: rrt-branch-name` (env) because the rrt action enforces it separately.

## GitHub / PR Creation
- `gh` CLI does **not** work in this environment (missing token). Use `mcp__GitKraken__pull_request_create` or the GitHub MCP tool instead.
- Target branch for PRs: `main`.

## Biome (JS/TS)
- Run `npm ci` before using `biome-check`/`biome-format` MCP tools or the pre-commit Biome hook.
- `.mcp.json` uses `sh -c "PATH=\"$PWD/node_modules/.bin:$PATH\" uv run mcp-server-analyzer"` to make Biome discoverable in dev mode.
