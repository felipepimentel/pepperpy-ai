#!/usr/bin/env python
"""
Script to fix imports in the new structure.
This script replaces relative imports with absolute imports.
"""

import re
import sys
from pathlib import Path


def fix_imports(directory):
    """
    Fix imports in all Python files in the given directory.
    """
    print(f"Fixing imports in {directory}...")

    # Get all Python files
    python_files = list(Path(directory).glob("**/*.py"))
    total_files = len(python_files)

    # Patterns to replace
    patterns = [
        (r"from pepperpy\.", r"from pepperpy."),  # Keep absolute imports
        (r"import pepperpy\.", r"import pepperpy."),  # Keep absolute imports
        (r"from \.\.", r"from pepperpy."),  # Replace relative imports with absolute
        (r"from \.", r"from pepperpy."),  # Replace relative imports with absolute
    ]

    # Process each file
    for i, file_path in enumerate(python_files):
        print(f"Processing file {i + 1}/{total_files}: {file_path}")

        # Read the file
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Apply replacements
        new_content = content
        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, new_content)

        # Write the file if changes were made
        if new_content != content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"  Updated imports in {file_path}")


if __name__ == "__main__":
    # Get the directory to process
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = "pepperpy"

    fix_imports(directory)
