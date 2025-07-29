#!/usr/bin/env python3
"""
Mixed Python code example - some good practices, some issues.
This demonstrates typical real-world code with room for improvement.
"""

import json
import os  # Used but could be more specific

# Some unused imports
import sys
from pathlib import Path


class FileProcessor:
    """A file processor with mixed code quality."""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.processed_files: list[str] = []  # Using older typing
        self.errors: list[str] = []
        self.temp_data = {}  # This will be unused

    def find_files(self, pattern: str = "*.json") -> list[Path]:
        """Find files matching pattern - good method."""
        files = list(self.base_path.glob(pattern))
        return files

    def process_file(self, file_path):  # Missing type hints
        """Process a single file - mixed quality."""
        if not os.path.exists(file_path):  # Could use Path.exists()
            self.errors.append(f"File not found: {file_path}")
            return None

        try:
            # Good: using context manager
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # Bad: no type checking
            if data:
                result = self._transform_data(data)
                self.processed_files.append(str(file_path))
                return result
        except Exception as e:  # Too broad exception handling
            self.errors.append(f"Error processing {file_path}: {e}")
            return None

    def _transform_data(self, data):  # Missing type hints
        """Transform data - needs improvement."""
        if type(data) == dict:  # Bad: should use isinstance()
            transformed = {}
            for key, value in data.items():
                # String concatenation instead of f-strings
                new_key = "processed_" + str(key)
                transformed[new_key] = value
            return transformed
        if type(data) == list:  # Bad: should use isinstance()
            return [self._transform_data(item) for item in data]
        return data

    def save_results(
        self, output_path: str, results: list[dict]
    ) -> bool:  # Using older typing
        """Save results to file - decent method."""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            return True
        except Exception:  # Bare except is bad
            return False

    def get_stats(self):  # Missing return type
        """Get processing statistics."""
        stats = {
            "processed_count": len(self.processed_files),
            "error_count": len(self.errors),
            "success_rate": 0,
        }

        total = stats["processed_count"] + stats["error_count"]
        if total > 0:
            stats["success_rate"] = (stats["processed_count"] / total) * 100

        return stats

    def unused_method(self):  # Dead code - never called
        """This method is never used."""
        temp = "unused value"
        return temp.upper()


def validate_json_file(filepath):  # Missing type hints
    """Validate if file contains valid JSON - standalone function."""
    try:
        with open(filepath) as f:  # Missing encoding
            json.load(f)
        return True
    except:  # Bare except clause
        return False


def unused_utility_function():  # Dead code
    """This function is never called."""
    return "unused"


def main():
    """Main function with some issues."""
    processor = FileProcessor("./data")  # Hardcoded path

    # Find and process files
    json_files = processor.find_files("*.json")

    if len(json_files) == 0:  # Verbose empty check
        print("No JSON files found")  # Should use logging
        return

    results = []
    for file in json_files:
        result = processor.process_file(file)
        if result != None:  # Should use 'is not None'
            results.append(result)

    # Some unused variables
    temp_var = "not used"
    another_unused = 42

    # Get and display stats
    stats = processor.get_stats()
    print(f"Processed: {stats['processed_count']} files")  # Should use logging
    print(f"Errors: {stats['error_count']} files")
    print(f"Success rate: {stats['success_rate']:.1f}%")

    # Save results if any
    if len(results) > 0:  # Verbose empty check
        output_file = "processed_data.json"
        if processor.save_results(output_file, results):
            print(f"Results saved to {output_file}")
        else:
            print("Failed to save results")


# Unused constants
UNUSED_CONSTANT = "never used"
DEFAULT_CONFIG = {"setting": "value"}  # This is used implicitly


if __name__ == "__main__":
    # Good: some error handling
    try:
        main()
    except Exception as e:
        print(f"Application error: {e}", file=sys.stderr)
        sys.exit(1)
