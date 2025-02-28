#!/usr/bin/env python3
"""
Script to consolidate duplicated modules in the PepperPy framework.

This script:
1. Updates imports from old module paths to new ones
2. Removes duplicated modules after migration is complete
"""

import os
import re
from typing import List, Tuple

# Mapping of old imports to new imports
IMPORT_MAPPINGS = {
    # Audio module consolidation
    r"from\s+pepperpy\.audio(\..+)?": r"from pepperpy.multimodal.audio\1",
    r"import\s+pepperpy\.audio(\..+)?": r"import pepperpy.multimodal.audio\1",
    r"from\s+pepperpy\.capabilities\.audio(\..+)?": r"from pepperpy.multimodal.audio\1",
    r"import\s+pepperpy\.capabilities\.audio(\..+)?": r"import pepperpy.multimodal.audio\1",
    # Vision module consolidation
    r"from\s+pepperpy\.vision(\..+)?": r"from pepperpy.multimodal.vision\1",
    r"import\s+pepperpy\.vision(\..+)?": r"import pepperpy.multimodal.vision\1",
    r"from\s+pepperpy\.capabilities\.vision(\..+)?": r"from pepperpy.multimodal.vision\1",
    r"import\s+pepperpy\.capabilities\.vision(\..+)?": r"import pepperpy.multimodal.vision\1",
    # Synthesis module consolidation
    r"from\s+pepperpy\.synthesis(\..+)?": r"from pepperpy.multimodal.synthesis\1",
    r"import\s+pepperpy\.synthesis(\..+)?": r"import pepperpy.multimodal.synthesis\1",
    # Agents module consolidation
    r"from\s+pepperpy\.agents\.types\.autonomous": r"from pepperpy.agents.implementations.autonomous",
    r"from\s+pepperpy\.agents\.types\.interactive": r"from pepperpy.agents.implementations.interactive",
    r"from\s+pepperpy\.agents\.types\.task_assistant": r"from pepperpy.agents.implementations.task_assistant",
}

# Directories to be removed after migration
DIRECTORIES_TO_REMOVE = [
    "pepperpy/audio",
    "pepperpy/vision",
    "pepperpy/synthesis",
    "pepperpy/capabilities/audio",
    "pepperpy/capabilities/vision",
    "pepperpy/agents/types",
]


def find_python_files(root_dir: str) -> List[str]:
    """Find all Python files in the given directory and its subdirectories.

    Args:
        root_dir: Root directory to search in

    Returns:
        List of paths to Python files
    """
    python_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def update_imports(file_path: str) -> Tuple[bool, int]:
    """Update imports in a Python file.

    Args:
        file_path: Path to the Python file

    Returns:
        Tuple of (whether file was modified, number of replacements made)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    replacements = 0

    for old_pattern, new_pattern in IMPORT_MAPPINGS.items():
        new_content, count = re.subn(old_pattern, new_pattern, content)
        replacements += count
        content = new_content

    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True, replacements

    return False, 0


def remove_directories() -> List[str]:
    """Remove directories that should be removed after migration.

    Returns:
        List of directories that were removed
    """
    removed = []
    for directory in DIRECTORIES_TO_REMOVE:
        if os.path.exists(directory):
            try:
                # Use rmdir to ensure directory is empty
                os.rmdir(directory)
                removed.append(directory)
            except OSError:
                print(f"Warning: Could not remove {directory}. It may not be empty.")

    return removed


def main():
    """Main function to run the consolidation script."""
    root_dir = "pepperpy"

    # Find all Python files
    python_files = find_python_files(root_dir)
    print(f"Found {len(python_files)} Python files to process")

    # Update imports
    modified_files = 0
    total_replacements = 0

    for file_path in python_files:
        modified, replacements = update_imports(file_path)
        if modified:
            modified_files += 1
            total_replacements += replacements
            print(f"Updated {replacements} imports in {file_path}")

    print(
        f"Updated imports in {modified_files} files ({total_replacements} replacements)"
    )

    # Remove directories
    removed_dirs = remove_directories()
    for directory in removed_dirs:
        print(f"Removed directory: {directory}")

    print("Consolidation complete!")


if __name__ == "__main__":
    main()
