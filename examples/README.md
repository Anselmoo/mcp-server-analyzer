# Examples Directory

This directory contains Python code examples to demonstrate the MCP Python Analyzer's capabilities.

## Files

### `good_example.py`

**Clean, well-structured Python code that follows best practices.**

- ✅ Proper type hints
- ✅ Good documentation
- ✅ Clean formatting
- ✅ Error handling
- ✅ No unused imports or variables
- ✅ Follows PEP 8 guidelines

**Expected Results:**

- RUFF: Minimal or no issues
- VULTURE: No unused code detected
- High code quality score

### `bad_example.py`

**Poorly written code with many issues.**

- ❌ Missing type hints
- ❌ Poor formatting
- ❌ Unused imports and variables
- ❌ Bad naming conventions
- ❌ Inefficient patterns
- ❌ Dead code
- ❌ Multiple PEP 8 violations

**Expected Results:**

- RUFF: Many style and quality issues
- VULTURE: Multiple unused code detections
- Low code quality score

### `mixed_example.py`

**Real-world code with both good and problematic patterns.**

- ⚠️ Some good practices mixed with issues
- ⚠️ Outdated typing patterns
- ⚠️ Some unused code
- ⚠️ Room for improvement

**Expected Results:**

- RUFF: Moderate number of issues
- VULTURE: Some unused code detected
- Medium code quality score

### `simple_issues.py`

**Simple example highlighting specific issues.**

- 🎯 Focused on demonstrating specific problems
- 🎯 Easy to understand issues
- 🎯 Good for testing individual tools

**Expected Results:**

- RUFF: Clear formatting and style issues
- VULTURE: Clear unused code examples

## Testing with MCP Tools

Use these examples to test the MCP Python Analyzer tools:

### Test RUFF Check

```bash
# Good example (should pass)
uv run python tests/test.py

# Or test specific files through VS Code MCP integration
```

### Test VULTURE Scan

```bash
# Bad example (should find unused code)
# Use the VS Code MCP integration or development server
```

### Test Complete Analysis

```bash
# All examples for comprehensive analysis
# Use analyze_code tool through MCP
```

## Usage in VS Code

1. Open any example file
2. Use GitHub Copilot chat with MCP integration
3. Ask questions like:
   - "Use ruff_check to analyze this file"
   - "Find dead code in this file using vulture_scan"
   - "Run analyze_code on this Python file"
   - "Format this code with ruff_format"

## Expected Tool Responses

### Good Example

- **ruff_check**: Minimal issues, mostly suggestions
- **vulture_scan**: No unused items found
- **analyze_code**: High quality score (80-100)

### Bad Example

- **ruff_check**: Many issues (import order, formatting, style)
- **vulture_scan**: Multiple unused imports, functions, variables
- **analyze_code**: Low quality score (0-40)

### Mixed Example

- **ruff_check**: Moderate issues (outdated typing, some style issues)
- **vulture_scan**: Some unused items
- **analyze_code**: Medium quality score (40-80)
