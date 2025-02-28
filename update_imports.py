#!/usr/bin/env python3
"""
Script to update imports after directory restructuring.

This script updates imports in Python files to reflect the new directory structure:
- pepperpy.core.types -> pepperpy.core.common.types
- pepperpy.core.utils -> pepperpy.core.common.utils
- pepperpy.core.capabilities -> pepperpy.capabilities
"""

import re
from pathlib import Path

# Define the import replacements
REPLACEMENTS = {
    r"from pepperpy\.core\.types(\.?)": r"from pepperpy.core.common.types\1",
    r"from pepperpy\.core\.utils(\.?)": r"from pepperpy.core.common.utils\1",
    r"from pepperpy\.core\.capabilities(\.?)": r"from pepperpy.capabilities\1",
    r"from pepperpy\.agents\.workflows(\.?)": r"from pepperpy.workflows\1",
    r"from pepperpy\.agents\.providers(\.?)": r"from pepperpy.providers.agent\1",
    r"from pepperpy\.processing(\.?)": r"# Removed import: pepperpy.processing\1",
}


def update_file(file_path):
    """Update imports in a single file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    for pattern, replacement in REPLACEMENTS.items():
        content = re.sub(pattern, replacement, content)

    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def main():
    """Update imports in all Python files in the project."""
    root_dir = Path("pepperpy")
    examples_dir = Path("examples")
    tests_dir = Path("tests")

    updated_files = 0

    # Process all Python files in the project
    for directory in [root_dir, examples_dir, tests_dir]:
        if not directory.exists():
            continue

        for file_path in directory.glob("**/*.py"):
            if update_file(file_path):
                print(f"Updated imports in {file_path}")
                updated_files += 1

    print(f"\nTotal files updated: {updated_files}")


if __name__ == "__main__":
    main()
