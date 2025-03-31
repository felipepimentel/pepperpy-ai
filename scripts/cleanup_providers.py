#!/usr/bin/env python3
"""
Cleanup provider directories.

This script creates a backup of provider directory __init__.py files
and then deletes provider directories that are now empty.
"""

import os
import shutil
from pathlib import Path

# List of provider directories to check
PROVIDER_DIRS = [
    "pepperpy/agents/providers",
    "pepperpy/cache/providers",
    "pepperpy/cli/providers",
    "pepperpy/content/providers/audio",
    "pepperpy/content/providers/document",
    "pepperpy/content/providers/image",
    "pepperpy/content/providers/video",
    "pepperpy/content/providers",
    "pepperpy/embeddings/providers",
    "pepperpy/hub/providers",
    "pepperpy/llm/providers",
    "pepperpy/rag/providers",
    "pepperpy/storage/providers",
    "pepperpy/tools/repository/providers",
    "pepperpy/tts/providers",
    "pepperpy/workflow/providers",
]


def can_remove_dir(dir_path):
    """Check if directory can be safely removed."""
    dir_path = Path(dir_path)

    # Get all files except __pycache__
    files = [f for f in os.listdir(dir_path) if f != "__pycache__"]

    # If only __init__.py exists, or the directory is empty, it can be removed
    return len(files) <= 1 and (len(files) == 0 or files[0] == "__init__.py")


def backup_init_file(dir_path):
    """Backup __init__.py file if it exists."""
    dir_path = Path(dir_path)
    init_file = dir_path / "__init__.py"

    if init_file.exists():
        backup_dir = Path("backup/init_files")
        backup_dir.mkdir(exist_ok=True, parents=True)

        # Create a unique backup filename
        backup_name = f"{dir_path.parent.name}_{dir_path.name}_init.py.bak"
        if "/" in str(dir_path.parent):
            # Handle nested paths like tools/repository
            parts = str(dir_path.parent).split("/")
            backup_name = f"{parts[-2]}_{parts[-1]}_{dir_path.name}_init.py.bak"

        backup_file = backup_dir / backup_name

        # Copy file
        shutil.copy2(init_file, backup_file)
        print(f"Backed up {init_file} to {backup_file}")

        return True

    return False


def remove_directory(dir_path):
    """Remove directory and its contents."""
    dir_path = Path(dir_path)

    # Handle __pycache__ first
    pycache = dir_path / "__pycache__"
    if pycache.exists():
        shutil.rmtree(pycache)
        print(f"Removed {pycache}")

    # Handle __init__.py
    init_file = dir_path / "__init__.py"
    if init_file.exists():
        os.remove(init_file)
        print(f"Removed {init_file}")

    # Remove directory
    os.rmdir(dir_path)
    print(f"Removed {dir_path}")


def cleanup():
    """Clean up provider directories."""
    for dir_path in PROVIDER_DIRS:
        print(f"\nChecking {dir_path}...")

        if not Path(dir_path).exists():
            print(f"Directory {dir_path} doesn't exist, skipping.")
            continue

        if can_remove_dir(dir_path):
            print(f"Directory {dir_path} can be removed.")
            backup_init_file(dir_path)
            remove_directory(dir_path)
        else:
            print(f"Directory {dir_path} still has files, keeping it.")

            # List files
            files = [
                f
                for f in os.listdir(dir_path)
                if f != "__pycache__" and f != "__init__.py"
            ]
            if files:
                print(f"Files: {', '.join(files)}")


if __name__ == "__main__":
    # Create backup directory
    Path("backup/init_files").mkdir(exist_ok=True, parents=True)

    # Clean up provider directories
    cleanup()

    print("\nDone! All provider directories cleaned up.")
