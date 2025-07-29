#!/usr/bin/env python3
"""
Good Python code example - follows best practices.
This should pass RUFF checks and have minimal VULTURE warnings.
"""

import json
import sys
from pathlib import Path


class DataProcessor:
    """A well-structured data processor class."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the processor with optional configuration."""
        self.config_path = config_path
        self.data: list[dict[str, str]] = []
        self.processed_count = 0

    def load_config(self) -> dict[str, str]:
        """Load configuration from file."""
        if not self.config_path or not self.config_path.exists():
            return {"default": "true", "format": "json"}

        with open(self.config_path, encoding="utf-8") as f:
            return json.load(f)

    def process_data(self, input_data: list[dict[str, str]]) -> list[dict[str, str]]:
        """Process input data and return cleaned results."""
        self.data = input_data
        processed = []

        for item in input_data:
            if self._is_valid_item(item):
                cleaned = self._clean_item(item)
                processed.append(cleaned)
                self.processed_count += 1

        return processed

    def _is_valid_item(self, item: dict[str, str]) -> bool:
        """Check if an item is valid for processing."""
        return "name" in item and "value" in item and item["name"].strip()

    def _clean_item(self, item: dict[str, str]) -> dict[str, str]:
        """Clean and normalize an item."""
        return {
            "name": item["name"].strip().lower(),
            "value": item["value"].strip(),
            "processed": "true",
        }

    def get_stats(self) -> dict[str, int]:
        """Get processing statistics."""
        return {
            "total_items": len(self.data),
            "processed_count": self.processed_count,
            "success_rate": int((self.processed_count / len(self.data)) * 100)
            if self.data
            else 0,
        }


def main() -> None:
    """Main function demonstrating good practices."""
    processor = DataProcessor()

    sample_data = [
        {"name": "Item 1", "value": "test_value"},
        {"name": "Item 2", "value": "another_value"},
        {"name": "", "value": "invalid"},  # This will be filtered out
        {"name": "Item 3", "value": "final_value"},
    ]

    results = processor.process_data(sample_data)
    stats = processor.get_stats()

    print(f"Processed {len(results)} items successfully")
    print(f"Success rate: {stats['success_rate']}%")

    for result in results:
        print(f"  - {result['name']}: {result['value']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
