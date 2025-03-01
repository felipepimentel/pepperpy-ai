#!/usr/bin/env python3
"""Script to fix registry imports in the PepperPy framework.

This script scans the codebase for registry imports and updates them
to use the consolidated registry system.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import logging
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("fix_registry_imports")

# Define the project root
PROJECT_ROOT = Path(__file__).parent.parent

# Define the old and new import paths
OLD_IMPORT_PATHS = [
    "pepperpy.core.common.registry",
    "pepperpy.common.registry",
]
NEW_IMPORT_PATH = "pepperpy.core.registry"

# Define the registry files to check
REGISTRY_FILES = [
    "pepperpy/agents/registry.py",
    "pepperpy/workflows/registry.py",
    "pepperpy/rag/registry.py",
    "pepperpy/cli/registry.py",
    "examples/registry_example.py",
]

# Define regex patterns for imports
IMPORT_PATTERN = re.compile(
    r"(from|import)\s+([\w.]+)\s+import\s+([\w,\s]+)"
)


def find_registry_files() -> List[Path]:
    """Find all registry files in the project.

    Returns:
        List of registry file paths
    """
    registry_files = []

    # Add explicitly defined registry files
    for file_path in REGISTRY_FILES:
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            registry_files.append(full_path)

    # Find additional registry files
    for root, _, files in os.walk(PROJECT_ROOT):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                if file_path not in registry_files:
                    with open(file_path, "r") as f:
                        content = f.read()
                        for old_path in OLD_IMPORT_PATHS:
                            if old_path in content:
                                registry_files.append(file_path)
                                break

    return registry_files


def fix_imports(file_path: Path) -> Tuple[bool, int]:
    """Fix imports in a file.

    Args:
        file_path: Path to the file

    Returns:
        Tuple of (whether file was modified, number of changes)
    """
    with open(file_path, "r") as f:
        content = f.read()

    original_content = content
    changes = 0

    # Replace old import paths
    for old_path in OLD_IMPORT_PATHS:
        # Replace direct imports
        pattern = re.compile(f"from {old_path}(\\.|\\s+)")
        content = pattern.sub(f"from {NEW_IMPORT_PATH}\\1", content)

        # Replace import statements
        pattern = re.compile(f"import {old_path}(\\.|\\s+)")
        content = pattern.sub(f"import {NEW_IMPORT_PATH}\\1", content)

        # Count changes
        changes += len(re.findall(old_path, original_content))

    # Write changes if needed
    if content != original_content:
        with open(file_path, "w") as f:
            f.write(content)
        return True, changes

    return False, 0


def main():
    """Run the script."""
    logger.info("Scanning for registry files...")
    registry_files = find_registry_files()
    logger.info(f"Found {len(registry_files)} registry files")

    total_changes = 0
    modified_files = 0

    for file_path in registry_files:
        logger.info(f"Checking {file_path.relative_to(PROJECT_ROOT)}...")
        modified, changes = fix_imports(file_path)
        if modified:
            logger.info(f"  Modified with {changes} changes")
            total_changes += changes
            modified_files += 1
        else:
            logger.info("  No changes needed")

    logger.info(f"Fixed {total_changes} imports in {modified_files} files")


if __name__ == "__main__":
    main()