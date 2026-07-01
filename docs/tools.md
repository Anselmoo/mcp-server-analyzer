# Tools Reference

All tools accept Python source code as a string and return structured Pydantic models serialized to JSON.

---

## `ruff-check`

Lint Python code using Ruff to identify style violations and potential errors.

**Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `code` | `string` | Yes | Python source code to analyze |
| `config_path` | `string` | No | Path to a `ruff.toml` or `pyproject.toml` with `[tool.ruff]` |

**Returns** `RuffCheckResult`

```json
{
  "issues": [
    {
      "line": 3,
      "column": 1,
      "end_line": 3,
      "end_column": 7,
      "rule": "F401",
      "message": "'os' imported but unused",
      "severity": "error",
      "fixable": true
    }
  ],
  "total_issues": 1,
  "fixable_issues": 1
}
```

---

## `ruff-format`

Format Python code using Ruff's fast formatter (Black-compatible).

**Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `code` | `string` | Yes | Python source code to format |
| `config_path` | `string` | No | Path to Ruff configuration file |

**Returns** `RuffFormatResult`

```json
{
  "formatted_code": "def hello():\n    print(\"world\")\n",
  "changed": true
}
```

---

## `ruff-check-ci`

Run Ruff with CI/CD-specific output formats (json, gitlab, github, sarif).

**Parameters**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `code` | `string` | Yes | — | Python source code |
| `output_format` | `string` | No | `"json"` | `json`, `gitlab`, `github`, or `sarif` |
| `config_path` | `string` | No | — | Path to Ruff configuration file |

**Returns** `RuffCICheckResult`

```json
{
  "output": "[{\"code\": \"F401\", ...}]",
  "format": "json",
  "success": true
}
```

---

## `ty-check`

Type-check Python code using [ty](https://docs.astral.sh/ty/).

**Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `code` | `string` | Yes | Python source code to type-check |
| `project_path` | `string` | No | Directory used for ty config and import resolution (defaults to cwd) |

**Returns** `TyCheckResult`

```json
{
  "diagnostics": [
    {
      "line": 5,
      "column": 10,
      "rule": "invalid-argument-type",
      "message": "Argument of type 'int' cannot be assigned to parameter 'x' of type 'str'",
      "severity": "error"
    }
  ],
  "total_diagnostics": 1,
  "error_count": 1,
  "warning_count": 0
}
```

---

## `vulture-scan`

Detect unused/dead code using [Vulture](https://github.com/jendrikseipp/vulture).

**Parameters**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `code` | `string` | Yes | — | Python source code |
| `min_confidence` | `integer` | No | `80` | Minimum confidence threshold (0-100) |

**Returns** `VultureScanResult`

```json
{
  "unused_items": [
    {
      "name": "unused_helper",
      "type": "function",
      "line": 12,
      "column": 0,
      "confidence": 100,
      "message": "unused function 'unused_helper'"
    }
  ],
  "total_items": 1,
  "high_confidence_items": 1
}
```

---

## `biome-check`

Lint JavaScript/TypeScript code using [Biome](https://biomejs.dev/).

> **Requires Biome:** run `npm ci` (project local) or `npm install -g @biomejs/biome` (global).

**Parameters**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `code` | `string` | Yes | — | JS/TS source code to lint |
| `filename` | `string` | No | `"code.ts"` | Virtual filename — controls parser selection (`.js`, `.ts`, `.jsx`, `.tsx`) |

**Returns** `BiomeCheckResult`

```json
{
  "issues": [
    {
      "rule": "lint/suspicious/noDoubleEquals",
      "severity": "error",
      "message": "Use === instead of ==",
      "file": "code.ts",
      "start_offset": 42,
      "end_offset": 44
    }
  ],
  "total_issues": 1,
  "errors": 1,
  "warnings": 0
}
```

---

## `biome-format`

Format JavaScript/TypeScript code using [Biome](https://biomejs.dev/).

> **Requires Biome:** run `npm ci` (project local) or `npm install -g @biomejs/biome` (global).

**Parameters**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `code` | `string` | Yes | — | JS/TS source code to format |
| `filename` | `string` | No | `"code.ts"` | Virtual filename — controls parser selection |

**Returns** `BiomeFormatResult`

```json
{
  "formatted_code": "const x = 1;\n",
  "changed": true
}
```

---

## `analyze-code`

Run Ruff, ty, and Vulture together and return a combined quality score.

**Parameters**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `code` | `string` | Yes | — | Python source code |
| `ruff_config_path` | `string` | No | — | Path to Ruff configuration file |
| `min_confidence` | `integer` | No | `80` | Vulture minimum confidence |
| `project_path` | `string` | No | — | ty project directory |

**Returns** `AnalysisResult`

```json
{
  "ruff_result": { ... },
  "ty_result": { ... },
  "vulture_result": { ... },
  "summary": {
    "total_ruff_issues": 2,
    "fixable_ruff_issues": 1,
    "total_ty_diagnostics": 0,
    "ty_error_count": 0,
    "ty_warning_count": 0,
    "total_unused_items": 1,
    "high_confidence_unused": 1,
    "code_quality_score": 83
  }
}
```

### Quality Score Formula

| Deduction | Condition |
|-----------|-----------|
| -2 pts per Ruff issue | capped at -50 |
| -10 pts per ty error | combined cap at -40 |
| -5 pts per ty warning | combined cap at -40 |
| -5 pts per high-confidence unused item | capped at -30 |
| -2 pts per low-confidence unused item | capped at -20 |

Score is clamped to `[0, 100]`.

---

## Error Handling

All tools raise a `ToolError` (MCP structured error) when:

- Input `code` is empty or whitespace-only.
- The backing tool (ruff/ty/vulture) is not installed.
- The tool process exits with an unexpected error.

MCP clients receive the error as a structured response with `isError: true`.
