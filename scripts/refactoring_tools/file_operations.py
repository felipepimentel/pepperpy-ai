#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File operation utilities.

This module provides functions for file operations like consolidating multiple
files, restructuring files according to a mapping, and cleaning up directories.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from .common import DEAD_FILES, RefactoringContext, logger


def restructure_files(
    file_mapping: Dict[str, str], context: RefactoringContext
) -> None:
    """
    Move files according to mapping and ensure __init__.py exists.

    Args:
        file_mapping: Dictionary with {old_path: new_path}
        context: Refactoring context
    """
    logger.info("Restructuring files according to mapping...")

    for old_path, new_path in file_mapping.items():
        old = Path(old_path)
        new = Path(new_path)

        if not old.exists():
            logger.warning(f"Warning: {old} does not exist.")
            continue

        # Create intermediate directories
        new.parent.mkdir(parents=True, exist_ok=True)

        # Create __init__.py in each directory
        for parent in new.parents:
            init_file = parent / "__init__.py"
            if not init_file.exists() and parent.name:
                if not context.dry_run:
                    init_file.touch()
                    logger.info(f"Created: {init_file}")
                else:
                    logger.info(f"Would create: {init_file}")

        # Move the file
        if not context.dry_run:
            if context.backup and old != new:
                # Create backup by copying original
                backup_path = old.with_suffix(".py.bak")
                shutil.copy2(old, backup_path)
                logger.info(f"Created backup: {backup_path}")

            shutil.copy2(old, new)
            logger.info(f"Moved: {old} -> {new}")
        else:
            logger.info(f"Would move: {old} -> {new}")


def consolidate_modules(
    files_to_consolidate: List[str],
    output_file: str,
    header: str = "",
    context: Optional[RefactoringContext] = None,
) -> None:
    """
    Consolidate multiple files into a single file.

    Args:
        files_to_consolidate: List of file paths to consolidate
        output_file: Path of the output file
        header: Optional text to add at the beginning of the file
        context: Optional refactoring context
    """
    logger.info(f"Consolidating modules into {output_file}...")

    # If context is not provided, assume we're making real changes
    dry_run = False
    backup = True

    if context is not None:
        dry_run = context.dry_run
        backup = context.backup

    output = Path(output_file)
    content = header + "\n\n" if header else ""

    for file in files_to_consolidate:
        path = Path(file)
        if not path.exists():
            logger.warning(f"Warning: {path} does not exist.")
            continue

        file_content = path.read_text(encoding="utf-8")

        content += f"# From {path}\n"
        content += file_content
        content += "\n\n"

    if not dry_run:
        # Create backup if requested and file exists
        if backup and output.exists():
            backup_path = output.with_suffix(".py.bak")
            shutil.copy2(output, backup_path)
            logger.info(f"Created backup: {backup_path}")

        # Create parent directories
        output.parent.mkdir(parents=True, exist_ok=True)

        # Write consolidated content
        output.write_text(content, encoding="utf-8")
        logger.info(f"Consolidated into: {output}")
    else:
        logger.info(f"Would consolidate into: {output}")


def clean_directories(directory: str, context: RefactoringContext) -> None:
    """
    Remove empty directories and dead files.

    Args:
        directory: Directory to clean
        context: Refactoring context
    """
    logger.info(f"Cleaning {directory}...")

    # Remove dead files
    dead_files = []
    for pattern in DEAD_FILES:
        dead_files.extend(list(Path(directory).glob(f"**/{pattern}")))

    for file in dead_files:
        if not context.dry_run:
            file.unlink()
            logger.info(f"Removed dead file: {file}")
        else:
            logger.info(f"Would remove dead file: {file}")

    # Remove empty directories
    for root, dirs, files in os.walk(directory, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            if not os.listdir(dir_path):
                if not context.dry_run:
                    os.rmdir(dir_path)
                    logger.info(f"Removed empty directory: {dir_path}")
                else:
                    logger.info(f"Would remove empty directory: {dir_path}")


def create_backup(file_path: Path, context: RefactoringContext) -> None:
    """
    Create a backup of a file.

    Args:
        file_path: Path to the file to backup
        context: Refactoring context
    """
    if not context.backup or not file_path.exists():
        return

    backup_path = file_path.with_suffix(f"{file_path.suffix}.bak")
    if not context.dry_run:
        shutil.copy2(file_path, backup_path)
        if context.verbose:
            logger.info(f"Created backup: {backup_path}")
    else:
        logger.info(f"Would create backup: {backup_path}")


def find_files(directory: str, pattern: str) -> List[Path]:
    """
    Find files matching a glob pattern.

    Args:
        directory: Directory to search
        pattern: Glob pattern to match

    Returns:
        List of matching file paths
    """
    directory_path = Path(directory)
    return list(directory_path.glob(pattern))
