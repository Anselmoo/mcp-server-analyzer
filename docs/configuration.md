# Configuration

## Environment Variables

The server itself has no required environment variables. The underlying tools respect their standard config files.

## Ruff Configuration

Pass a `config_path` to any `ruff-*` tool to use a custom configuration:

```python
# Via MCP tool call
{
  "name": "ruff-check",
  "arguments": {
    "code": "...",
    "config_path": "/path/to/ruff.toml"
  }
}
```

Ruff also auto-discovers `pyproject.toml` / `ruff.toml` / `.ruff.toml` from the directory of the analyzed file upward, but since analysis runs against a temporary file the auto-discovery will typically use the server's working directory.

See [Ruff configuration docs](https://docs.astral.sh/ruff/configuration/) for all options.

## ty Configuration

Pass `project_path` to `ty-check` or `analyze-code` to point ty at your project root:

```python
{
  "name": "ty-check",
  "arguments": {
    "code": "...",
    "project_path": "/path/to/your/project"
  }
}
```

ty reads `pyproject.toml` `[tool.ty]` or `ty.toml` from that directory. The `project_path` also controls import resolution.

See [ty configuration docs](https://docs.astral.sh/ty/) for all options.

## Vulture Configuration

Confidence threshold is set per-call via `min_confidence` (default `80`):

```python
{
  "name": "vulture-scan",
  "arguments": {
    "code": "...",
    "min_confidence": 60
  }
}
```

Vulture also reads `[tool.vulture]` from `pyproject.toml` if one exists in the server's working directory.

## pyproject.toml Example

```toml
[tool.ruff]
target-version = "py313"
line-length = 88

[tool.ruff.lint]
select = ["ALL"]
ignore = ["D100", "D101", "D102", "D103", "COM812"]

[tool.ty.environment]
python-version = "3.13"

[tool.vulture]
min_confidence = 80
sort_by_size = true
```
