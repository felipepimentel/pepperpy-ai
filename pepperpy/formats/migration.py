"""Migration utilities for transitioning from old format handling to the unified system.

This module provides utilities to help migrate from previous format handling
implementations to the new unified format handling system. It includes:

- Detection of old format usage in code
- Mapping between old and new format handlers
- Code generation for migration
- Migration guides and examples
"""

import ast
import re
from typing import Dict, List, Optional


class MigrationHelper:
    """Helper class for migrating from old format handling to the new unified system."""

    # Mapping from old format classes to new format handlers
    OLD_TO_NEW_MAPPING = {
        # Text formats
        "TextFormat": "PlainTextFormat",
        "MarkdownParser": "MarkdownFormat",
        "JSONParser": "JSONFormat",
        "YAMLParser": "YAMLFormat",
        "XMLParser": "XMLFormat",
        # Audio formats
        "AudioProcessor": "WAVFormat",
        "MP3Processor": "MP3Format",
        "WAVProcessor": "WAVFormat",
        "OGGProcessor": "OGGFormat",
        "FLACProcessor": "FLACFormat",
        # Image formats
        "ImageProcessor": "PNGFormat",
        "PNGProcessor": "PNGFormat",
        "JPEGProcessor": "JPEGFormat",
        "GIFProcessor": "GIFFormat",
        "BMPProcessor": "BMPFormat",
        "TIFFProcessor": "TIFFFormat",
        # Vector formats
        "VectorProcessor": "NumpyFormat",
        "NumpyVectorProcessor": "NumpyFormat",
        "JSONVectorProcessor": "JSONVectorFormat",
    }

    # Mapping from old import paths to new import paths
    IMPORT_MAPPING = {
        "pepperpy.text.formats": "pepperpy.formats.text",
        "pepperpy.audio.formats": "pepperpy.formats.audio",
        "pepperpy.image.formats": "pepperpy.formats.image",
        "pepperpy.vector.formats": "pepperpy.formats.vector",
        "pepperpy.text.parsers": "pepperpy.formats.text",
        "pepperpy.audio.processors": "pepperpy.formats.audio",
        "pepperpy.image.processors": "pepperpy.formats.image",
        "pepperpy.vector.processors": "pepperpy.formats.vector",
    }

    # Method name mappings (old method name -> new method name)
    METHOD_MAPPING = {
        "process": "serialize",
        "parse": "deserialize",
        "to_bytes": "serialize",
        "from_bytes": "deserialize",
        "to_string": "serialize",
        "from_string": "deserialize",
        "validate": "validate",
    }

    @classmethod
    def detect_old_formats(cls, code: str) -> List[str]:
        """Detect old format classes used in the provided code.

        Args:
            code: Python code to analyze

        Returns:
            List of old format class names found in the code
        """
        old_formats = []

        # Parse the code into an AST
        try:
            tree = ast.parse(code)

            # Find all class names that might be old formats
            for node in ast.walk(tree):
                # Check for direct class usage
                if isinstance(node, ast.Name) and node.id in cls.OLD_TO_NEW_MAPPING:
                    old_formats.append(node.id)

                # Check for attribute access (e.g., module.ClassType)
                elif (
                    isinstance(node, ast.Attribute)
                    and node.attr in cls.OLD_TO_NEW_MAPPING
                ):
                    old_formats.append(node.attr)

                # Check for imports
                elif (
                    isinstance(node, ast.ImportFrom)
                    and node.module in cls.IMPORT_MAPPING
                ):
                    for name in node.names:
                        if name.name in cls.OLD_TO_NEW_MAPPING:
                            old_formats.append(name.name)

        except SyntaxError:
            # If code can't be parsed, use regex as fallback
            for old_format in cls.OLD_TO_NEW_MAPPING:
                if re.search(r"\b" + re.escape(old_format) + r"\b", code):
                    old_formats.append(old_format)

        return list(set(old_formats))  # Remove duplicates

    @classmethod
    def get_equivalent_format(cls, old_format: str) -> Optional[str]:
        """Get the equivalent new format handler for an old format class.

        Args:
            old_format: Name of the old format class

        Returns:
            Name of the equivalent new format handler, or None if not found
        """
        return cls.OLD_TO_NEW_MAPPING.get(old_format)

    @classmethod
    def map_imports(cls, old_import: str) -> Optional[str]:
        """Map an old import path to the new import path.

        Args:
            old_import: Old import path

        Returns:
            New import path, or None if not found
        """
        return cls.IMPORT_MAPPING.get(old_import)

    @classmethod
    def generate_migration_code(cls, old_code: str) -> str:
        """Generate migrated code from old format handling code.

        Args:
            old_code: Python code using old format handling

        Returns:
            Migrated code using the new unified format handling system
        """
        # This is a simplified implementation
        # A real implementation would parse the AST and transform it

        new_code = old_code

        # Replace imports
        for old_import, new_import in cls.IMPORT_MAPPING.items():
            new_code = re.sub(
                r"from\s+" + re.escape(old_import) + r"\s+import",
                f"from {new_import} import",
                new_code,
            )
            new_code = re.sub(
                r"import\s+" + re.escape(old_import), f"import {new_import}", new_code
            )

        # Replace class names
        for old_format, new_format in cls.OLD_TO_NEW_MAPPING.items():
            new_code = re.sub(
                r"\b" + re.escape(old_format) + r"\b", new_format, new_code
            )

        # Replace method names
        for old_method, new_method in cls.METHOD_MAPPING.items():
            new_code = re.sub(
                r"(\w+)\." + re.escape(old_method) + r"\(",
                r"\1." + new_method + "(",
                new_code,
            )

        return new_code

    @classmethod
    def print_migration_guide(cls, old_formats: Optional[List[str]] = None) -> str:
        """Generate a migration guide for transitioning to the new format system.

        Args:
            old_formats: Optional list of old format classes to focus on

        Returns:
            Migration guide as a string
        """
        if old_formats is None:
            old_formats = list(cls.OLD_TO_NEW_MAPPING.keys())

        guide = [
            "# Migration Guide: Format Handling System",
            "",
            "## Overview",
            "",
            "This guide helps you migrate from the old format handling classes to the new unified format system.",
            "The new system provides a consistent interface across all format types with improved type safety and extensibility.",
            "",
            "## Key Changes",
            "",
            "- All format handlers are now in the `pepperpy.formats` package",
            "- Consistent method names across all formats (`serialize`, `deserialize`, `validate`)",
            "- Format-specific data containers (e.g., `AudioData`, `ImageData`, `VectorData`)",
            "- Registry system for format discovery and lookup",
            "",
            "## Class Mappings",
            "",
        ]

        # Add mappings for the specified old formats
        for old_format in sorted(old_formats):
            new_format = cls.get_equivalent_format(old_format)
            if new_format:
                guide.append(f"- `{old_format}` → `{new_format}`")

        guide.extend(["", "## Method Mappings", ""])

        # Add method mappings
        for old_method, new_method in cls.METHOD_MAPPING.items():
            guide.append(f"- `{old_method}()` → `{new_method}()`")

        guide.extend(["", "## Import Changes", ""])

        # Add import mappings
        for old_import, new_import in cls.IMPORT_MAPPING.items():
            guide.append(
                f"- `from {old_import} import ...` → `from {new_import} import ...`"
            )

        guide.extend([
            "",
            "## Example Migration",
            "",
            "### Old Code",
            "",
            "```python",
            "from pepperpy.audio.processors import WAVProcessor",
            "",
            "processor = WAVProcessor()",
            "audio_bytes = processor.process(audio_data)",
            "```",
            "",
            "### New Code",
            "",
            "```python",
            "from pepperpy.formats.audio import WAVFormat, AudioData",
            "",
            "format_handler = WAVFormat()",
            "audio_bytes = format_handler.serialize(audio_data)",
            "```",
            "",
            "## Working with the Format Registry",
            "",
            "The new system provides a central registry for formats:",
            "",
            "```python",
            "from pepperpy.formats import get_format_by_extension, get_format_by_mime_type",
            "",
            "# Get a format handler by file extension",
            "wav_format = get_format_by_extension('wav')",
            "",
            "# Get a format handler by MIME type",
            "json_format = get_format_by_mime_type('application/json')",
            "```",
        ])

        return "\n".join(guide)


def detect_old_formats_in_file(file_path: str) -> List[str]:
    """Detect old format classes used in a file.

    Args:
        file_path: Path to the Python file to analyze

    Returns:
        List of old format class names found in the file
    """
    try:
        with open(file_path, "r") as f:
            code = f.read()
        return MigrationHelper.detect_old_formats(code)
    except Exception as e:
        print(f"Error analyzing {file_path}: {str(e)}")
        return []


def generate_migration_report(directory_path: str) -> Dict[str, List[str]]:
    """Generate a migration report for a directory.

    Args:
        directory_path: Path to the directory to analyze

    Returns:
        Dictionary mapping file paths to lists of old format classes found
    """
    import os

    report = {}

    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                old_formats = detect_old_formats_in_file(file_path)
                if old_formats:
                    report[file_path] = old_formats

    return report


def print_migration_report(report: Dict[str, List[str]]) -> None:
    """Print a migration report.

    Args:
        report: Dictionary mapping file paths to lists of old format classes found
    """
    if not report:
        print("No files requiring migration were found.")
        return

    print("Migration Report")
    print("===============")
    print()
    print(f"Found {len(report)} files requiring migration:")
    print()

    for file_path, old_formats in sorted(report.items()):
        print(f"- {file_path}")
        for old_format in sorted(old_formats):
            new_format = MigrationHelper.get_equivalent_format(old_format)
            print(f"  - {old_format} → {new_format}")

    print()
    print(
        "For detailed migration instructions, use MigrationHelper.print_migration_guide()"
    )
