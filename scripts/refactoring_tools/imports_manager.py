#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Import management utilities.

This module provides functions for updating and fixing import statements
throughout the codebase.
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set

# Try to import ast_decompiler, but provide an alternative if not available
try:
    import ast_decompiler

    AST_DECOMPILER_AVAILABLE = True
except ImportError:
    AST_DECOMPILER_AVAILABLE = False
    print(
        "Warning: ast_decompiler module not available. Using alternative implementation."
    )

from .common import logger
from .context import RefactoringContext


class ImportTransformer(ast.NodeTransformer):
    """Handles import-related transformations using AST."""

    def __init__(self, context: RefactoringContext, import_map: Dict[str, str]):
        self.context = context
        self.import_map = import_map
        self.changes: List[str] = []

    def visit_Import(self, node: ast.Import) -> ast.Import:
        """Process Import nodes."""
        new_names = []
        modified = False

        for name in node.names:
            if name.name in self.import_map:
                new_name = self.import_map[name.name]
                new_names.append(ast.alias(name=new_name, asname=name.asname))
                self.changes.append(f"Updated import: {name.name} -> {new_name}")
                modified = True
            else:
                new_names.append(name)

        if modified:
            return ast.Import(names=new_names)
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom:
        """Process ImportFrom nodes."""
        if node.module in self.import_map:
            new_module = self.import_map[node.module]
            self.changes.append(f"Updated from import: {node.module} -> {new_module}")
            return ast.ImportFrom(
                module=new_module,
                names=node.names,
                level=0,  # Convert to absolute import
            )

        # Check if we need to update relative imports
        if node.level > 0 and self.context.verbose:
            self.changes.append(
                f"Found relative import (level {node.level}): {node.module}"
            )

        return node


def update_imports_regex(
    directory: str, import_mapping: Dict[str, str], context: "RefactoringContext"
) -> None:
    """
    Update import statements in Python files using regex patterns.

    Args:
        directory: The directory to process
        import_mapping: A dictionary mapping old import paths to new ones
        context: The refactoring context
    """
    logger.info(f"Updating imports in {directory} using regex")

    # Generate regex patterns for each import type
    patterns = {}
    for old_import, new_import in import_mapping.items():
        # Direct import pattern: import module.submodule
        patterns[f"import\\s+{old_import}(\\s|$)"] = f"import {new_import}\\1"

        # From import pattern: from module.submodule import X
        patterns[f"from\\s+{old_import}\\s+import"] = f"from {new_import} import"

        # Submodule import pattern: from module import submodule
        old_parent = old_import.split(".")[0]
        old_child = ".".join(old_import.split(".")[1:])
        new_parent = new_import.split(".")[0]
        new_child = ".".join(new_import.split(".")[1:])

        if old_child and new_child:
            patterns[f"from\\s+{old_parent}\\s+import\\s+{old_child}(\\s|$|,)"] = (
                f"from {new_parent} import {new_child}\\1"
            )

    # Walk through the directory and update files
    python_files = list(Path(directory).glob("**/*.py"))
    logger.info(f"Found {len(python_files)} Python files to process")

    for file_path in python_files:
        if "__pycache__" in str(file_path):
            continue

        try:
            # Read the file
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # Apply each pattern
            for pattern, replacement in patterns.items():
                content = re.sub(pattern, replacement, content)

            # Only write if content changed
            if content != original_content:
                logger.info(f"Updating imports in {file_path}")

                if not context.dry_run:
                    # Create a backup if needed
                    if context.backup:
                        backup_path = file_path.with_suffix(".py.bak")
                        backup_path.write_text(original_content, encoding="utf-8")
                        logger.info(f"Created backup at {backup_path}")

                    # Write updated content
                    file_path.write_text(content, encoding="utf-8")
                else:
                    logger.info(f"Would update imports in {file_path}")

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")


def _format_node(node: ast.AST) -> str:
    """
    Format an AST node as a string without relying on ast_decompiler.

    Args:
        node: The AST node to format

    Returns:
        A string representation of the node
    """
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return f"{_format_node(node.value)}.{node.attr}"
    elif isinstance(node, ast.Alias):
        if node.asname:
            return f"{node.name} as {node.asname}"
        return node.name
    elif isinstance(node, ast.Import):
        names = [_format_node(name) for name in node.names]
        return f"import {', '.join(names)}"
    elif isinstance(node, ast.ImportFrom):
        names = [_format_node(name) for name in node.names]
        level = "." * node.level
        module = node.module or ""
        return f"from {level}{module} import {', '.join(names)}"
    return str(node)


def update_imports_ast(
    directory: str, import_mapping: Dict[str, str], context: "RefactoringContext"
) -> None:
    """
    Update import statements in Python files using AST parsing.

    Args:
        directory: The directory to process
        import_mapping: A dictionary mapping old import paths to new ones
        context: The refactoring context
    """
    logger.info(f"Updating imports in {directory} using AST")

    # Walk through the directory and update files
    python_files = list(Path(directory).glob("**/*.py"))
    logger.info(f"Found {len(python_files)} Python files to process")

    for file_path in python_files:
        if "__pycache__" in str(file_path):
            continue

        try:
            # Read the file
            content = file_path.read_text(encoding="utf-8")

            # Parse the code
            tree = ast.parse(content)

            # Find import statements
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(node)

            # If no imports found, skip this file
            if not imports:
                continue

            # Check if any imports need to be updated
            updated = False
            for node in imports:
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in import_mapping:
                            alias.name = import_mapping[alias.name]
                            updated = True

                elif isinstance(node, ast.ImportFrom):
                    if node.module in import_mapping:
                        node.module = import_mapping[node.module]
                        updated = True

                    # Check if the module prefix matches any keys in the mapping
                    for old_import, new_import in import_mapping.items():
                        if node.module and node.module.startswith(old_import + "."):
                            suffix = node.module[len(old_import) :]
                            node.module = new_import + suffix
                            updated = True

            # Only rewrite if needed
            if updated:
                logger.info(f"Updating imports in {file_path}")

                if not context.dry_run:
                    # Create a backup if needed
                    if context.backup:
                        backup_path = file_path.with_suffix(".py.bak")
                        backup_path.write_text(content, encoding="utf-8")
                        logger.info(f"Created backup at {backup_path}")

                    # Format the new code
                    if AST_DECOMPILER_AVAILABLE:
                        new_content = ast_decompiler.decompile(tree)
                    else:
                        # Fall back to regex-based replacement
                        new_content = content
                        for old_import, new_import in import_mapping.items():
                            new_content = re.sub(
                                f"import\\s+{old_import}(\\s|$)",
                                f"import {new_import}\\1",
                                new_content,
                            )
                            new_content = re.sub(
                                f"from\\s+{old_import}\\s+import",
                                f"from {new_import} import",
                                new_content,
                            )

                    # Write the new code
                    file_path.write_text(new_content, encoding="utf-8")
                else:
                    logger.info(f"Would update imports in {file_path}")

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")


def fix_relative_imports(directory: str, context: "RefactoringContext") -> None:
    """
    Fix relative imports by converting them to absolute imports.

    Args:
        directory: The directory to process
        context: The refactoring context
    """
    logger.info(f"Fixing relative imports in {directory}")

    # Walk through the directory and update files
    python_files = list(Path(directory).glob("**/*.py"))
    logger.info(f"Found {len(python_files)} Python files to process")

    package_name = os.path.basename(os.path.abspath(directory))

    for file_path in python_files:
        if "__pycache__" in str(file_path):
            continue

        try:
            # Read the file
            content = file_path.read_text(encoding="utf-8")

            # Find relative imports
            relative_import_pattern = r"from\s+\.\.?[.\w]*\s+import"
            if not re.search(relative_import_pattern, content):
                continue

            # Parse the code
            tree = ast.parse(content)

            # Find all relative imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level > 0:
                    imports.append(node)

            # If no relative imports found, skip this file
            if not imports:
                continue

            # Convert relative imports to absolute
            updated = False
            for node in imports:
                # Calculate the absolute import path
                rel_path = os.path.relpath(file_path.parent, directory)
                if rel_path == ".":
                    module_path = package_name
                else:
                    module_path = f"{package_name}.{rel_path.replace('/', '.')}"

                # Calculate absolute import based on the level
                path_parts = module_path.split(".")
                if node.level <= len(path_parts):
                    abs_prefix = ".".join(path_parts[: -node.level])

                    if node.module:
                        node.module = f"{abs_prefix}.{node.module}"
                    else:
                        node.module = abs_prefix

                    node.level = 0
                    updated = True

            # Only rewrite if needed
            if updated:
                logger.info(f"Fixing relative imports in {file_path}")

                if not context.dry_run:
                    # Create a backup if needed
                    if context.backup:
                        backup_path = file_path.with_suffix(".py.bak")
                        backup_path.write_text(content, encoding="utf-8")
                        logger.info(f"Created backup at {backup_path}")

                    # Format the new code
                    if AST_DECOMPILER_AVAILABLE:
                        new_content = ast_decompiler.decompile(tree)
                    else:
                        # This is a fallback, but won't actually fix the imports without
                        # a proper decompiler or manual regex replacement specific to each file
                        logger.warning(
                            f"Unable to fully fix relative imports in {file_path} without ast_decompiler"
                        )
                        new_content = content

                    # Write the new code
                    file_path.write_text(new_content, encoding="utf-8")
                else:
                    logger.info(f"Would fix relative imports in {file_path}")

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")


class ImportAnalyzer(ast.NodeVisitor):
    """Analyzes imports in a Python module."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.imports: Set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        """Process Import nodes."""
        for name in node.names:
            self.imports.add(name.name.split(".")[0])  # Add top-level module
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Process ImportFrom nodes."""
        if node.module:
            self.imports.add(node.module.split(".")[0])  # Add top-level module
        self.generic_visit(node)
