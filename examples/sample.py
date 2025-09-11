# Sample Python code with some issues for RUFF and VULTURE
import json


def process_data(data, debug=False):
    """Process data with optional debugging."""
    if not data:
        return None

    results = []
    for item in data:
        if item.get("active"):
            results.append(
                {"id": item["id"], "name": item["name"], "timestamp": 1234567890}
            )

    if debug:
        print(f"Processed {len(results)} items")

    return results


def unused_function():
    """This function is never used."""
    return "unused"


class DataProcessor:
    def __init__(self, config):
        self.config = config
        self.debug = config.get("debug", False)

    def transform(self, data):
        return [self._process_item(item) for item in data]

    def _process_item(self, item):
        return {"processed_id": item["id"], "processed_name": item["name"].upper()}


# Main execution
if __name__ == "__main__":
    sample_data = [
        {"id": 1, "name": "Alice", "active": True},
        {"id": 2, "name": "Bob", "active": False},
    ]
    result = process_data(sample_data, debug=True)
    print(json.dumps(result, indent=2))
