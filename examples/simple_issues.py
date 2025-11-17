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
    if x is None:
        return None  # Multiple issues here
    return x + y


def main():
    """Main function with various issues."""
    # VULTURE will catch unused variables:

    # RUFF will catch style issues:

    # Using the badly formatted function:
    result = badly_formatted(10, 20)

    # More RUFF issues:
    if result is not None:  # Should use 'is not None'
        pass

    return result


if __name__ == "__main__":
    main()
