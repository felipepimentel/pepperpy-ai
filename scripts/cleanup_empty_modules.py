#!/usr/bin/env python3
"""
Remove empty module directories after migration.

This script removes directories that only contain __init__.py and __pycache__
after their base.py files were migrated to the main module level.
"""

import os
import shutil
from pathlib import Path

# List of modules we migrated
MIGRATED_MODULES = [
    "cache",
    "llm",
    "embeddings",
    "hub",
    "storage",
]


def is_dir_empty_except_init(dir_path):
    """Check if directory only contains __init__.py and __pycache__."""
    items = os.listdir(dir_path)

    # Filter out __pycache__
    non_pycache_items = [item for item in items if item != "__pycache__"]

    # If only __init__.py remains, it's considered empty for our purposes
    return len(non_pycache_items) == 1 and "__init__.py" in non_pycache_items


def remove_empty_module(module_name):
    """Remove empty module directory."""
    module_path = Path(f"pepperpy/{module_name}")

    if not module_path.exists():
        print(f"Warning: {module_path} does not exist, skipping.")
        return

    if not is_dir_empty_except_init(module_path):
        print(f"Warning: {module_path} contains other files, skipping.")
        return

    # Create backup directory
    backup_dir = Path("backup/empty_dirs")
    backup_dir.mkdir(exist_ok=True, parents=True)

    # Backup __init__.py file
    init_file = module_path / "__init__.py"
    if init_file.exists():
        shutil.copy2(init_file, backup_dir / f"{module_name}_init.py.bak")
        print(f"Backed up {init_file}")

    # Remove the directory
    shutil.rmtree(module_path)
    print(f"Removed directory {module_path}")


def cleanup_all():
    """Remove all empty migrated directories."""
    for module in MIGRATED_MODULES:
        print(f"\nChecking {module}...")
        remove_empty_module(module)


if __name__ == "__main__":
    # Create backup directory
    Path("backup/empty_dirs").mkdir(exist_ok=True, parents=True)

    # Remove empty modules
    cleanup_all()

    print("\nDone! All empty module directories removed.")
