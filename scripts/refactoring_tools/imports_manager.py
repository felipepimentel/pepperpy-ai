#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Import management functions.

This module provides functions for updating and fixing import statements
in Python files, supporting both legacy and AST-based approaches.
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Set

import ast_decompiler

from .common import RefactoringContext, logger


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


def update_imports_ast(
    directory: str, import_map: Dict[str, str], context: RefactoringContext
) -> None:
    """
    Update imports in all Python files using AST.

    Args:
        directory: Directory to process
        import_map: Dictionary with {old_import: new_import}
        context: Refactoring context
    """
    logger.info(f"Updating imports in {directory} using AST...")

    files = Path(directory).glob("**/*.py")
    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            transformer = ImportTransformer(context, import_map)
            modified_tree = transformer.visit(tree)

            if transformer.changes:
                if context.verbose:
                    for change in transformer.changes:
                        logger.info(f"{file}: {change}")

                modified_code = ast_decompiler.decompile(modified_tree)

                if context.backup:
                    backup_path = file.with_suffix(".py.bak")
                    with open(backup_path, "w", encoding="utf-8") as f:
                        f.write(modified_code)

                if not context.dry_run:
                    with open(file, "w", encoding="utf-8") as f:
                        f.write(modified_code)

                    logger.info(f"Updated imports in: {file}")
        except Exception as e:
            logger.error(f"Error processing {file}: {e}")


def update_imports_regex(
    directory: str, import_map: Dict[str, str], context: RefactoringContext
) -> None:
    """
    Update imports in all Python files using regex (simpler approach).

    Args:
        directory: Directory to process
        import_map: Dictionary with {old_import: new_import}
        context: Refactoring context
    """
    logger.info(f"Updating imports in {directory} using regex...")

    files = Path(directory).glob("**/*.py")
    for file in files:
        try:
            content = file.read_text(encoding="utf-8")
            updated = content

            for old, new in import_map.items():
                # Update direct imports (from x import y, import x)
                pattern = rf"(from|import)\s+{re.escape(old)}(\s|\.|,|$)"
                updated = re.sub(pattern, rf"\1 {new}\2", updated)

            if content != updated:
                if context.backup:
                    backup_path = file.with_suffix(".py.bak")
                    backup_path.write_text(content, encoding="utf-8")

                if not context.dry_run:
                    file.write_text(updated, encoding="utf-8")
                    logger.info(f"Updated imports in: {file}")
        except Exception as e:
            logger.error(f"Error processing {file}: {e}")


def fix_relative_imports(directory: str, context: RefactoringContext) -> None:
    """
    Fix relative imports by converting them to absolute imports.

    Args:
        directory: Directory to process
        context: Refactoring context
    """
    logger.info(f"Fixing relative imports in {directory}...")

    # Patterns to replace
    patterns = [
        (r"from pepperpy\.", r"from pepperpy."),  # Keep absolute imports
        (r"import pepperpy\.", r"import pepperpy."),  # Keep absolute imports
        (r"from \.\.", r"from pepperpy."),  # Replace relative imports with absolute
        (r"from \.", r"from pepperpy."),  # Replace relative imports with absolute
    ]

    # Process each file
    python_files = list(Path(directory).glob("**/*.py"))
    total_files = len(python_files)

    for i, file_path in enumerate(python_files):
        if context.verbose:
            logger.info(f"Processing file {i + 1}/{total_files}: {file_path}")
        else:
            logger.debug(f"Processing file {i + 1}/{total_files}: {file_path}")

        try:
            # Read the file
            content = file_path.read_text(encoding="utf-8")

            # Apply replacements
            new_content = content
            for pattern, replacement in patterns:
                new_content = re.sub(pattern, replacement, new_content)

            # Write the file if changes were made
            if new_content != content:
                if context.backup:
                    backup_path = file_path.with_suffix(".py.bak")
                    backup_path.write_text(content, encoding="utf-8")

                if not context.dry_run:
                    file_path.write_text(new_content, encoding="utf-8")
                    logger.info(f"Updated imports in {file_path}")
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
