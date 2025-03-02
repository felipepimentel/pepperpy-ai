#!/usr/bin/env python3
"""
Script to update imports after core module restructuring.

This script updates imports from:
- pepperpy.core.common.base -> pepperpy.core.base
- pepperpy.core.common.types -> pepperpy.core.types
- pepperpy.core.common.validation -> pepperpy.core.validation
"""

import re
import sys
from pathlib import Path

# Mapping of old imports to new imports
IMPORT_REPLACEMENTS = [
    # Base module replacements
    (r"from pepperpy\.core\.common\.base import", r"from pepperpy.core.base import"),
    (r"from pepperpy\.core\.common\.base\.", r"from pepperpy.core.base."),
    (r"import pepperpy\.core\.common\.base", r"import pepperpy.core.base"),
    # Types module replacements
    (r"from pepperpy\.core\.common\.types import", r"from pepperpy.core.types import"),
    (r"from pepperpy\.core\.common\.types\.", r"from pepperpy.core.types."),
    (r"import pepperpy\.core\.common\.types", r"import pepperpy.core.types"),
    # Validation module replacements
    (
        r"from pepperpy\.core\.common\.validation import",
        r"from pepperpy.core.validation import",
    ),
    (r"from pepperpy\.core\.common\.validation\.", r"from pepperpy.core.validation."),
    (r"import pepperpy\.core\.common\.validation", r"import pepperpy.core.validation"),
    # Common module replacements (be careful with this one)
    (r"from pepperpy\.core\.common import \*", r"from pepperpy.core import *"),
]


def update_file(file_path: Path) -> bool:
    """Update imports in a file.

    Args:
        file_path: Path to the file to update

    Returns:
        True if file was modified, False otherwise
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Apply all replacements
    for pattern, replacement in IMPORT_REPLACEMENTS:
        content = re.sub(pattern, replacement, content)

    # Check if content was modified
    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True

    return False


def main():
    """Main function."""
    # Get the project root directory
    if len(sys.argv) > 1:
        root_dir = Path(sys.argv[1])
    else:
        # Assume script is in scripts/ directory
        root_dir = Path(__file__).parent.parent

    # Directories to search
    search_dirs = [
        root_dir / "pepperpy",
        root_dir / "examples",
        root_dir / "tests",
    ]

    # Count of modified files
    modified_count = 0

    # Process all Python files
    for search_dir in search_dirs:
        if not search_dir.exists():
            print(f"Directory not found: {search_dir}")
            continue

        for file_path in search_dir.glob("**/*.py"):
            if update_file(file_path):
                modified_count += 1
                print(f"Updated: {file_path.relative_to(root_dir)}")

    print(f"\nTotal files modified: {modified_count}")


if __name__ == "__main__":
    main()
