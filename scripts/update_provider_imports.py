#!/usr/bin/env python3
"""
Script to update imports for the provider reorganization.

This script updates imports in Python files to reflect the new provider organization:
- pepperpy/providers/llm/ -> pepperpy/llm/providers/
- pepperpy/providers/vision/ -> pepperpy/multimodal/vision/providers/
- pepperpy/providers/audio/ -> pepperpy/multimodal/audio/providers/
- pepperpy/providers/rag/ -> pepperpy/rag/providers/
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# Define the import mappings
IMPORT_MAPPINGS = {
    r"from pepperpy\.providers\.llm": "from pepperpy.llm.providers",
    r"from pepperpy\.providers\.vision": "from pepperpy.multimodal.vision.providers",
    r"from pepperpy\.providers\.audio": "from pepperpy.multimodal.audio.providers",
    r"from pepperpy\.providers\.rag": "from pepperpy.rag.providers",
    r"import pepperpy\.providers\.llm": "import pepperpy.llm.providers",
    r"import pepperpy\.providers\.vision": "import pepperpy.multimodal.vision.providers",
    r"import pepperpy\.providers\.audio": "import pepperpy.multimodal.audio.providers",
    r"import pepperpy\.providers\.rag": "import pepperpy.rag.providers",
}


def find_python_files(root_dir: str) -> List[Path]:
    """Find all Python files in the given directory and its subdirectories."""
    python_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(os.path.join(root, file)))
    return python_files


def update_imports_in_file(file_path: Path) -> Tuple[int, List[str]]:
    """Update imports in a single file according to the mappings."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    changes = []

    for pattern, replacement in IMPORT_MAPPINGS.items():
        # Use regex to find and replace imports
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0:
            changes.append(f"Updated {count} occurrences of {pattern} to {replacement}")
            content = new_content

    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return len(changes), changes

    return 0, []


def main():
    """Main function to update imports in all Python files."""
    root_dir = "pepperpy"
    python_files = find_python_files(root_dir)

    total_files_changed = 0
    total_changes = 0

    for file_path in python_files:
        num_changes, changes = update_imports_in_file(file_path)
        if num_changes > 0:
            total_files_changed += 1
            total_changes += num_changes
            print(f"Updated {file_path}:")
            for change in changes:
                print(f"  - {change}")

    print(f"\nSummary: Updated {total_changes} imports in {total_files_changed} files.")


if __name__ == "__main__":
    main()
