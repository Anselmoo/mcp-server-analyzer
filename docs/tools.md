# Tools Reference

All tools accept source code as a string and return structured Pydantic models serialized to JSON.

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

## `semgrep-check`

Scan code for security issues using [Semgrep](https://semgrep.dev/) (SAST).

> **Requires Semgrep:** not a project dependency — uses `semgrep` if it's on `PATH`, otherwise falls back to `uvx semgrep` (no separate install needed if `uv`/`uvx` is available).

**Parameters**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `code` | `string` | Yes | — | Source code to scan |
| `config` | `string` | No | `"auto"` | Semgrep ruleset (`"auto"`, `"p/security-audit"`, or a local rule file/path). `"auto"` calls the Semgrep registry over the network; any other value runs fully offline with `--metrics=off`. |
| `filename` | `string` | No | `"code.py"` | Virtual filename — controls the file suffix/parser used |

**Returns** `SemgrepScanResult`

```json
{
  "issues": [
    {
      "check_id": "python.lang.security.audit.subprocess-shell-true",
      "line": 5,
      "column": 38,
      "end_line": 5,
      "end_column": 42,
      "severity": "ERROR",
      "message": "Found 'subprocess' function 'run' with 'shell=True'.",
      "cwe": ["CWE-78: Improper Neutralization of Special Elements used in an OS Command ('OS Command Injection')"],
      "owasp": ["A03:2021 - Injection"]
    }
  ],
  "total_issues": 1,
  "error_count": 1,
  "warning_count": 0
}
```

---

## `actionlint-check`

Lint a GitHub Actions workflow YAML file using [actionlint](https://github.com/rhysd/actionlint).

> **Requires actionlint:** install the binary, e.g. `go install github.com/rhysd/actionlint/cmd/actionlint@latest` or via the [official install script](https://github.com/rhysd/actionlint/blob/main/scripts/download-actionlint.bash).

**Parameters**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `code` | `string` | Yes | — | Workflow YAML source to lint |
| `filename` | `string` | No | `"workflow.yml"` | Virtual filename reported in issue locations |

**Returns** `ActionlintCheckResult`

```json
{
  "issues": [
    {
      "line": 8,
      "column": 31,
      "end_column": 32,
      "kind": "expression",
      "message": "unexpected end of input while parsing variable access, function call, null, bool, int, float or string",
      "snippet": "        if: ${{ badcondition( }}\n                              ^~"
    }
  ],
  "total_issues": 1
}
```

---

## `gitleaks-scan`

Scan code for hardcoded secrets using [gitleaks](https://github.com/gitleaks/gitleaks). Secret values are always redacted — `secret` and `match` are always the literal string `"REDACTED"`, never the actual matched text.

> **Requires gitleaks:** install the binary, e.g. `go install github.com/gitleaks/gitleaks/v8@latest` or download a [release binary](https://github.com/gitleaks/gitleaks/releases).

**Parameters**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `code` | `string` | Yes | — | Source code to scan |
| `filename` | `string` | No | `"code.txt"` | Virtual filename reported against each finding |

**Returns** `GitleaksScanResult`

```json
{
  "findings": [
    {
      "rule_id": "private-key",
      "description": "Identified a Private Key, which may compromise cryptographic security and sensitive data encryption.",
      "file": "key.pem",
      "start_line": 1,
      "end_line": 28,
      "start_column": 1,
      "end_column": 26,
      "secret": "REDACTED",
      "match": "REDACTED"
    }
  ],
  "total_findings": 1
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
- The backing tool (ruff/ty/vulture/biome/semgrep/actionlint/gitleaks) is not installed.
- The tool process exits with an unexpected error.

MCP clients receive the error as a structured response with `isError: true`.
