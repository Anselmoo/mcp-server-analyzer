#!/usr/bin/env python3
"""
Bad Python code example - violates many best practices.
This should trigger multiple RUFF warnings and VULTURE dead code detection.
"""

# Unused imports
import json

# More unused imports

# Global variables (bad practice)
GLOBAL_DATA = []
config = {}
counter = 0
total_items = 0


class badDataProcessor:  # Class name should be PascalCase
    """A poorly structured class with many issues."""

    def __init__(self, data=None, config_file=None):  # No spaces around = in parameters
        self.data = data if data else []  # No spaces around =
        self.config_file = config_file
        self.results = {}
        self.temp_var = "unused"  # Will be unused
        self.another_unused = 42
        # Unnecessary pass

    def load_config(self):  # Missing return type annotation
        if self.config_file == None:  # Should use 'is None'
            return {"default": True}
        try:
            f = open(self.config_file)  # Should use context manager
            data = json.load(f)
            f.close()  # Manual close instead of context manager
            return data
        except:  # Bare except clause
            return {}

    def process_data(self, input_data):  # No type hints, no spaces
        # Bad formatting and logic
        if len(input_data) == 0:
            return []  # Multiple statements on one line

        processed = []
        for i in range(len(input_data)):  # Should use enumerate or direct iteration
            item = input_data[i]
            if (
                item.get("name") != None and item.get("name") != ""
            ):  # Verbose None checks
                result = {}
                result["name"] = item["name"].strip().lower()
                result["value"] = item.get("value", "")
                result["processed"] = True
                processed.append(result)
            else:
                pass  # Unnecessary pass
        return processed

    def validate_item(
        self, item
    ):  # Method name doesn't follow convention, unused method
        """This method is never called - dead code."""
        if "name" in item:
            if len(item["name"]) > 0:
                if item["name"].isalnum():
                    return True
        return False

    def unused_method(self):  # Dead code
        """This method is never used."""
        temp = "hello world"
        temp2 = temp.upper()
        return temp2


# Unused function
def helper_function(data):
    """This function is never called."""
    return [x for x in data if x]


def another_unused_function():
    """Another unused function."""
    x = 1
    y = 2
    z = x + y
    return z


def main():
    # Bad practices in main
    global GLOBAL_DATA, config  # Using global variables

    processor = badDataProcessor()

    # Hardcoded data (should be configurable)
    sample_data = [
        {"name": "Item 1", "value": "test"},
        {"name": "Item 2", "value": "test2"},
        {"name": "", "value": "invalid"},
        {"name": "Item 3", "value": "test3"},
    ]

    results = processor.process_data(sample_data)

    # Bad string formatting
    print("Processed " + str(len(results)) + " items")

    # Unused variables
    unused_var = "this is never used"
    another_unused = [1, 2, 3, 4, 5]
    temp_dict = {"key": "value"}

    # Bad loop
    for i in range(len(results)):
        item = results[i]
        print("Item: " + item["name"] + " = " + item["value"])

    # Dead code after return would go here, but let's not make it too obvious

    return results


# Unused class
class UnusedClass:
    """This class is never instantiated."""

    def __init__(self):
        self.value = "unused"
        self.data = []

    def unused_method(self):
        return self.value


# More unused code
def calculate_something(a, b, c):
    """Function with unused parameters."""
    return a + b  # 'c' is unused


# Unused variables at module level
MODULE_CONSTANT = "never used"
ANOTHER_CONSTANT = 42
unused_dict = {"a": 1, "b": 2}

if __name__ == "__main__":
    # No error handling
    main()
