#!/usr/bin/env python3
"""
Simple example for testing MCP Python Analyzer tools.
This file has specific issues to demonstrate each tool's capabilities.
"""

# RUFF will catch these style issues:

# VULTURE will catch these unused items:

UNUSED_CONSTANT = "never used"


def unused_function():
    """This function is never called."""
    return "dead code"


class UnusedClass:
    """This class is never instantiated."""

    def __init__(self):
        self.value = 42


# RUFF will catch formatting issues:
def badly_formatted(x, y):
    """Function with poor formatting."""
    if x == None:
        return None  # Multiple issues here
    result = x + y
    return result


def main():
    """Main function with various issues."""
    # VULTURE will catch unused variables:
    unused_var = "not used"
    another_unused = [1, 2, 3]

    # RUFF will catch style issues:
    data = {"name": "test", "value": 123}  # No spaces around colons

    # Using the badly formatted function:
    result = badly_formatted(10, 20)

    # More RUFF issues:
    if result != None:  # Should use 'is not None'
        print("Result:", result)

    return result


if __name__ == "__main__":
    main()
