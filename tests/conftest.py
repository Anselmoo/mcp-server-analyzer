"""Shared test fixtures for MCP Python Analyzer tests."""

import pytest


@pytest.fixture
def sample_bad_code() -> str:
    """Provide sample bad code for testing."""
    return """
import os
import sys
unused_var = "not used"

def unused_function():
    return "never called"

def main():
    print("hello world")
    temp = "unused"
    return 42

class UnusedClass:
    def __init__(self):
        self.value = "unused"

if __name__ == "__main__":
    main()
"""


@pytest.fixture
def sample_good_code() -> str:
    """Provide sample good code for testing."""
    return '''
def main() -> int:
    """Main function."""
    print("hello world")
    return 42

if __name__ == "__main__":
    main()
'''
