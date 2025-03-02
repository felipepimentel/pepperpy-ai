#!/usr/bin/env python3
"""
Reorganize Structure Module

This module implements the second phase of the PepperPy refactoring process,
focusing on reorganizing the project structure to improve clarity and maintainability.

Key areas addressed:
1. Consolidation of overlapping directories (common and core)
2. Standardization of naming conventions (singular vs. plural)
3. Creation of a clear public API interface
4. Reorganization of providers and utilities

The module creates compatibility stubs for backward compatibility and generates
a detailed report of all changes made.
"""

import datetime
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("reorganization.log"), logging.StreamHandler()],
)
logger = logging.getLogger("reorganize_structure")

# Define reorganization mappings
REORGANIZATION_MAPPINGS = [
    {
        "source": "pepperpy/common",
        "target": "pepperpy/core/common",
        "description": "Move common utilities to core/common",
    },
    {
        "source": "pepperpy/providers/embeddings",
        "target": "pepperpy/embeddings/providers",
        "description": "Standardize provider organization for embeddings",
    },
    {
        "source": "pepperpy/utils",
        "target": "pepperpy/core/utils",
        "description": "Move utilities to core/utils",
    },
]

# Define directories to create for public interfaces
PUBLIC_INTERFACE_DIRS = [
    "pepperpy/core/public",
    "pepperpy/capabilities/public",
    "pepperpy/workflows/public",
    "pepperpy/embedding/public",
    "pepperpy/llm/public",
    "pepperpy/providers/public",
]


def find_python_files(directory: Path) -> List[Path]:
    """
    Find all Python files in the given directory recursively.

    Args:
        directory: The directory to search in

    Returns:
        A list of Path objects for Python files
    """
    return list(directory.glob("**/*.py"))


def create_compatibility_stub(source_file: Path, target_file: Path) -> None:
    """
    Create a compatibility stub for a moved file.

    Args:
        source_file: Original file path
        target_file: New file path
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(source_file), exist_ok=True)

    # Get the relative import path
    rel_path = os.path.relpath(target_file, os.path.dirname(source_file))
    rel_path = rel_path.replace(".py", "").replace("/", ".")

    # If the relative path starts with a dot, it's a relative import
    if rel_path.startswith(".."):
        # Convert to absolute import
        parts = target_file.parts
        if "pepperpy" in parts:
            idx = parts.index("pepperpy")
            rel_path = ".".join(parts[idx:]).replace(".py", "")

    # Create stub file
    with open(source_file, "w") as f:
        f.write(f'''"""
COMPATIBILITY STUB: This module has been moved to {rel_path}
This stub exists for backward compatibility and will be removed in a future version.
"""

import warnings
import importlib

warnings.warn(
    f"The module {source_file} has been moved to {rel_path}. "
    f"Please update your imports. This stub will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Import the module from the new location
_module = importlib.import_module("{rel_path}")

# Copy all attributes from the imported module to this module's namespace
for _attr in dir(_module):
    if not _attr.startswith("_"):
        globals()[_attr] = getattr(_module, _attr)
''')
    logger.info(f"Created compatibility stub at {source_file} pointing to {rel_path}")


def update_imports(file_path: Path, old_prefix: str, new_prefix: str) -> bool:
    """
    Update import statements in a file.

    Args:
        file_path: Path to the file to update
        old_prefix: Old import prefix to replace
        new_prefix: New import prefix

    Returns:
        True if file was modified, False otherwise
    """
    with open(file_path, "r") as f:
        content = f.read()

    # Replace import statements
    old_import_pattern = rf"import\s+{old_prefix.replace('/', '.')}"
    new_import = f"import {new_prefix.replace('/', '.')}"
    modified_content = re.sub(old_import_pattern, new_import, content)

    # Replace from ... import statements
    old_from_pattern = rf"from\s+{old_prefix.replace('/', '.')}"
    new_from = f"from {new_prefix.replace('/', '.')}"
    modified_content = re.sub(old_from_pattern, new_from, modified_content)

    if content != modified_content:
        with open(file_path, "w") as f:
            f.write(modified_content)
        return True
    return False


def reorganize_directory(
    source_dir: Path, target_dir: Path, project_root: Path
) -> Dict:
    """
    Reorganize a source directory into a target directory.

    Args:
        source_dir: Source directory to reorganize
        target_dir: Target directory to reorganize into
        project_root: Root of the project

    Returns:
        Dictionary with statistics about the reorganization
    """
    stats = {"files_moved": 0, "stubs_created": 0, "imports_updated": 0, "errors": 0}

    # Ensure source directory exists
    if not source_dir.exists():
        logger.warning(f"Source directory {source_dir} does not exist. Skipping.")
        return stats

    # Create target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)

    # Find all Python files in source directory
    python_files = find_python_files(source_dir)

    # Move each file and create compatibility stub
    for source_file in python_files:
        try:
            # Determine target file path
            rel_path = source_file.relative_to(source_dir)
            target_file = target_dir / rel_path

            # Create target directory if it doesn't exist
            os.makedirs(target_file.parent, exist_ok=True)

            # Check if target file already exists
            if target_file.exists():
                # Compare files
                with open(source_file, "r") as f1, open(target_file, "r") as f2:
                    source_content = f1.read()
                    target_content = f2.read()

                if source_content == target_content:
                    # Files are identical, just create stub
                    create_compatibility_stub(source_file, target_file)
                    stats["stubs_created"] += 1
                else:
                    # Files differ, merge them
                    # For simplicity, we'll just append the source content to the target
                    # In a real implementation, you might want a more sophisticated merge strategy
                    with open(target_file, "a") as f:
                        f.write(
                            f"\n\n# Merged from {source_file} during reorganization\n"
                        )
                        f.write(source_content)

                    # Create compatibility stub
                    create_compatibility_stub(source_file, target_file)
                    stats["stubs_created"] += 1
                    logger.info(f"Merged {source_file} into {target_file}")
            else:
                # Copy file to target location
                shutil.copy2(source_file, target_file)
                stats["files_moved"] += 1

                # Create compatibility stub
                create_compatibility_stub(source_file, target_file)
                stats["stubs_created"] += 1
                logger.info(f"Moved {source_file} to {target_file}")
        except Exception as e:
            logger.error(f"Error processing {source_file}: {str(e)}")
            stats["errors"] += 1

    # Update imports in all Python files
    all_python_files = find_python_files(project_root)
    source_prefix = str(source_dir).replace(str(project_root) + "/", "")
    target_prefix = str(target_dir).replace(str(project_root) + "/", "")

    for file_path in all_python_files:
        try:
            if update_imports(file_path, source_prefix, target_prefix):
                stats["imports_updated"] += 1
                logger.info(f"Updated imports in {file_path}")
        except Exception as e:
            logger.error(f"Error updating imports in {file_path}: {str(e)}")
            stats["errors"] += 1

    return stats


def create_public_interfaces(project_root: Path) -> Dict:
    """
    Create public interfaces for the PepperPy project.

    Args:
        project_root: Root of the project

    Returns:
        Dictionary with statistics about the interface creation
    """
    stats = {"interfaces_created": 0, "errors": 0}

    # Create interfaces directory
    interfaces_dir = project_root / "pepperpy" / "interfaces"
    os.makedirs(interfaces_dir, exist_ok=True)

    # Create __init__.py file
    init_file = interfaces_dir / "__init__.py"
    with open(init_file, "w") as f:
        f.write('''"""
Public Interfaces Package

This package provides stable public interfaces for the PepperPy framework.
These interfaces are guaranteed to be backward compatible across minor versions.
"""

# Import all public interfaces
from .core import *
from .capabilities import *
from .workflows import *
from .embeddings import *
from .llm import *
from .providers import *
''')

    # Create interface directories
    for interface_dir in PUBLIC_INTERFACE_DIRS:
        try:
            dir_path = project_root / interface_dir
            os.makedirs(dir_path, exist_ok=True)

            # Create __init__.py file
            init_file = dir_path / "__init__.py"
            with open(init_file, "w") as f:
                module_name = dir_path.name
                f.write(f'''"""
Public Interface for {module_name}

This module provides a stable public interface for the {module_name} functionality.
"""

# Import public classes and functions from the implementation
''')

            stats["interfaces_created"] += 1
            logger.info(f"Created public interface directory at {dir_path}")
        except Exception as e:
            logger.error(
                f"Error creating interface directory {interface_dir}: {str(e)}"
            )
            stats["errors"] += 1

    return stats


def generate_reorganization_report(
    mappings: List[Dict], stats: List[Dict], interface_stats: Dict
) -> str:
    """
    Generate a report of the reorganization process.

    Args:
        mappings: List of reorganization mappings
        stats: List of statistics for each mapping
        interface_stats: Statistics about interface creation

    Returns:
        Markdown formatted report
    """
    report = "# Reorganization Report\n\n"
    report += (
        f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    )

    report += "## Summary\n\n"
    total_files_moved = sum(stat["files_moved"] for stat in stats)
    total_stubs_created = sum(stat["stubs_created"] for stat in stats)
    total_imports_updated = sum(stat["imports_updated"] for stat in stats)
    total_errors = sum(stat["errors"] for stat in stats) + interface_stats["errors"]

    report += f"- Total files moved: {total_files_moved}\n"
    report += f"- Total compatibility stubs created: {total_stubs_created}\n"
    report += f"- Total import statements updated: {total_imports_updated}\n"
    report += (
        f"- Total public interfaces created: {interface_stats['interfaces_created']}\n"
    )
    report += f"- Total errors encountered: {total_errors}\n\n"

    report += "## Directory Reorganization\n\n"
    for i, (mapping, stat) in enumerate(zip(mappings, stats)):
        report += f"### {i + 1}. {mapping['description']}\n\n"
        report += f"- Source: `{mapping['source']}`\n"
        report += f"- Target: `{mapping['target']}`\n"
        report += f"- Files moved: {stat['files_moved']}\n"
        report += f"- Compatibility stubs created: {stat['stubs_created']}\n"
        report += f"- Import statements updated: {stat['imports_updated']}\n"
        report += f"- Errors encountered: {stat['errors']}\n\n"

    report += "## Public Interfaces\n\n"
    report += f"- Interfaces created: {interface_stats['interfaces_created']}\n"
    report += f"- Errors encountered: {interface_stats['errors']}\n\n"
    report += "### Created Interface Directories\n\n"
    for interface_dir in PUBLIC_INTERFACE_DIRS:
        report += f"- `{interface_dir}`\n"

    return report


def run_reorganization(project_root: Path) -> str:
    """
    Run the reorganization process for all mappings.

    Args:
        project_root: Root of the project

    Returns:
        Path to the generated report
    """
    logger.info("Starting reorganization process")

    stats = []

    # Process each reorganization mapping
    for mapping in REORGANIZATION_MAPPINGS:
        source_dir = project_root / mapping["source"]
        target_dir = project_root / mapping["target"]

        logger.info(f"Reorganizing {source_dir} into {target_dir}")

        mapping_stats = reorganize_directory(source_dir, target_dir, project_root)
        stats.append(mapping_stats)

        logger.info(f"Completed reorganization of {source_dir} into {target_dir}")

    # Create public interfaces
    logger.info("Creating public interfaces")
    interface_stats = create_public_interfaces(project_root)

    # Generate report
    report = generate_reorganization_report(
        REORGANIZATION_MAPPINGS, stats, interface_stats
    )
    report_path = project_root / "reorganization_report.md"

    with open(report_path, "w") as f:
        f.write(report)

    logger.info(f"Reorganization report generated at {report_path}")

    return str(report_path)


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    run_reorganization(project_root)
