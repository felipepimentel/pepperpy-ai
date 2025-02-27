"""Examples of using the unified format handling system.

This module provides practical examples of using the format handling system
for various data types and scenarios.
"""

import json
import os
from typing import Any, Dict, List, cast

# Import format registry functions
from pepperpy.formats import (
    get_format_by_extension,
    get_format_by_mime_type,
    register_format,
)


# Example 1: Working with text formats
def text_format_example() -> None:
    """Example of working with text formats."""
    print("Example 1: Text Formats")
    print("======================")

    # Import text formats
    from pepperpy.formats.text import JSONFormat, MarkdownFormat, PlainTextFormat

    # Create some data
    data = {
        "name": "PepperPy",
        "version": "1.0.0",
        "features": ["text", "audio", "image", "vector"],
        "metadata": {"author": "PepperPy Team", "license": "MIT"},
    }

    # JSON format
    json_format = JSONFormat()
    json_bytes = json_format.serialize(data)
    print(f"JSON serialized ({len(json_bytes)} bytes):")
    print(
        json_bytes.decode("utf-8")[:100] + "..."
        if len(json_bytes) > 100
        else json_bytes.decode("utf-8")
    )

    # Deserialize back
    deserialized_data = cast(Dict[str, Any], json_format.deserialize(json_bytes))
    print("\nDeserialized data:")
    print(f"Name: {deserialized_data['name']}")
    print(f"Features: {', '.join(deserialized_data['features'])}")

    # Plain text format
    text_format = PlainTextFormat()
    text = "Hello, PepperPy!"
    text_bytes = text_format.serialize(text)
    print(f"\nPlain text serialized ({len(text_bytes)} bytes):")
    print(text_bytes.decode("utf-8"))

    # Markdown format
    markdown_format = MarkdownFormat()
    markdown = "# PepperPy\n\n**Bold** and *italic* text."
    markdown_bytes = markdown_format.serialize(markdown)
    print(f"\nMarkdown serialized ({len(markdown_bytes)} bytes):")
    print(markdown_bytes.decode("utf-8"))

    print("\n")


# Example 2: Using the format registry
def format_registry_example() -> None:
    """Example of using the format registry."""
    print("Example 2: Format Registry")
    print("========================")

    # Get format handlers by extension
    json_format = get_format_by_extension("json")
    wav_format = get_format_by_extension("wav")
    png_format = get_format_by_extension("png")

    print("Format handlers by extension:")
    print(f"json: {json_format.__class__.__name__ if json_format else 'Not found'}")
    print(f"wav: {wav_format.__class__.__name__ if wav_format else 'Not found'}")
    print(f"png: {png_format.__class__.__name__ if png_format else 'Not found'}")

    # Get format handlers by MIME type
    json_format = get_format_by_mime_type("application/json")
    wav_format = get_format_by_mime_type("audio/wav")
    png_format = get_format_by_mime_type("image/png")

    print("\nFormat handlers by MIME type:")
    print(
        f"application/json: {json_format.__class__.__name__ if json_format else 'Not found'}"
    )
    print(f"audio/wav: {wav_format.__class__.__name__ if wav_format else 'Not found'}")
    print(f"image/png: {png_format.__class__.__name__ if png_format else 'Not found'}")

    print("\n")


# Example 3: Custom format handler
def custom_format_example() -> None:
    """Example of creating and using a custom format handler."""
    print("Example 3: Custom Format Handler")
    print("==============================")

    from pepperpy.formats.base import FormatError, FormatHandler

    # Define a custom format handler for CSV data
    class CSVFormat(FormatHandler[list]):
        """Handler for CSV format."""

        @property
        def mime_type(self) -> str:
            """Get the MIME type for this format."""
            return "text/csv"

        @property
        def file_extensions(self) -> list[str]:
            """Get the file extensions for this format."""
            return ["csv"]

        def serialize(self, data: list) -> bytes:
            """Serialize list of lists to CSV bytes."""
            try:
                lines = []
                for row in data:
                    # Convert all values to strings and escape commas
                    csv_row = ",".join(
                        f'"{str(cell)}"' if "," in str(cell) else str(cell)
                        for cell in row
                    )
                    lines.append(csv_row)
                return "\n".join(lines).encode("utf-8")
            except Exception as e:
                raise FormatError(f"Failed to serialize CSV: {str(e)}") from e

        def deserialize(self, data: bytes) -> list:
            """Deserialize CSV bytes to list of lists."""
            try:
                text = data.decode("utf-8")
                lines = text.strip().split("\n")
                result = []

                for line in lines:
                    # Simple CSV parsing (doesn't handle all edge cases)
                    row = []
                    in_quotes = False
                    current_cell = ""

                    for char in line:
                        if char == '"':
                            in_quotes = not in_quotes
                        elif char == "," and not in_quotes:
                            row.append(current_cell)
                            current_cell = ""
                        else:
                            current_cell += char

                    # Add the last cell
                    row.append(current_cell)
                    result.append(row)

                return result
            except Exception as e:
                raise FormatError(f"Failed to deserialize CSV: {str(e)}") from e

    # Create and register the custom format handler
    csv_format = CSVFormat()
    register_format(csv_format)

    # Use the custom format handler
    data = [
        ["Name", "Age", "City"],
        ["Alice", "30", "New York"],
        ["Bob", "25", "San Francisco"],
        ["Charlie", "35", "Chicago, IL"],  # Note the comma in the city
    ]

    csv_bytes = csv_format.serialize(data)
    print("CSV serialized:")
    print(csv_bytes.decode("utf-8"))

    # Deserialize back
    deserialized_data = csv_format.deserialize(csv_bytes)
    print("\nDeserialized data:")
    for row in deserialized_data:
        print(row)

    # Verify registration
    registered_format = get_format_by_extension("csv")
    print(
        f"\nRegistered format for .csv: {registered_format.__class__.__name__ if registered_format else 'Not found'}"
    )

    print("\n")


# Example 4: File operations with formats
def file_operations_example() -> None:
    """Example of file operations with formats."""
    print("Example 4: File Operations")
    print("========================")

    from pepperpy.formats.text import JSONFormat

    # Create some data
    data = {
        "name": "PepperPy",
        "version": "1.0.0",
        "features": ["text", "audio", "image", "vector"],
    }

    # Get the JSON format handler
    json_format = JSONFormat()

    # Serialize to bytes
    json_bytes = json_format.serialize(data)

    # Write to a file
    filename = "example_data.json"
    with open(filename, "wb") as f:
        f.write(json_bytes)

    print(f"Wrote data to {filename}")

    # Read from the file
    with open(filename, "rb") as f:
        read_bytes = f.read()

    # Deserialize
    read_data = json_format.deserialize(read_bytes)

    print("Read data from file:")
    print(json.dumps(read_data, indent=2))

    # Clean up
    os.remove(filename)
    print(f"Removed {filename}")

    print("\n")


# Run all examples
def run_all_examples() -> None:
    """Run all examples."""
    text_format_example()
    format_registry_example()
    custom_format_example()
    file_operations_example()


if __name__ == "__main__":
    run_all_examples()
