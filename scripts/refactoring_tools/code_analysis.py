#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Code analysis utilities.

This module provides functions for code analysis, including validating project
structure, finding unused code, and detecting circular dependencies.
"""

import ast
import importlib.util
from pathlib import Path
from typing import Dict, List, Set, Tuple

import networkx as nx

from .common import DEAD_FILES, RefactoringContext, logger
from .imports_manager import ImportAnalyzer


def validate_structure(directory: str, context: RefactoringContext) -> None:
    """
    Validate the project structure after refactoring.

    Args:
        directory: Directory to validate
        context: Refactoring context
    """
    logger.info(f"Validating structure of {directory}...")

    # Check for dead files
    dead_files = []
    for pattern in DEAD_FILES:
        dead_files.extend(list(Path(directory).glob(f"**/{pattern}")))

    if dead_files:
        logger.warning("Found files that should be removed:")
        for file in dead_files:
            logger.warning(f"  - {file}")

    # Test importability
    try:
        spec = importlib.util.find_spec(directory)
        if spec:
            logger.info(f"Module {directory} can be imported successfully.")
        else:
            logger.warning(f"Failed to find module {directory}.")
    except Exception as e:
        logger.error(f"Error importing {directory}: {e}")

    # Check for empty directories
    empty_dirs = []
    for path in Path(directory).glob("**"):
        if path.is_dir() and not list(path.iterdir()):
            empty_dirs.append(path)

    if empty_dirs:
        logger.warning("Empty directories found:")
        for dir_path in empty_dirs:
            logger.warning(f"  - {dir_path}")

    # Check for missing __init__.py files
    missing_init = []
    for path in Path(directory).glob("**"):
        if path.is_dir() and path.name and not (path / "__init__.py").exists():
            missing_init.append(path)

    if missing_init:
        logger.warning("Directories missing __init__.py:")
        for dir_path in missing_init:
            logger.warning(f"  - {dir_path}")


def find_unused_code(
    directory: str, context: RefactoringContext
) -> Set[Tuple[str, str]]:
    """
    Detect potentially unused code.

    Args:
        directory: Directory to analyze
        context: Refactoring context

    Returns:
        Set of (name, file_path) tuples for unused symbols
    """
    logger.info(f"Finding potentially unused code in {directory}...")

    # Collect all definitions and imports
    all_definitions = {}
    all_imports = {}

    # Collect all usages
    all_usages = set()

    files = list(Path(directory).glob("**/*.py"))

    # First pass: collect definitions
    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file))

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    all_definitions[node.name] = str(file)
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        all_imports[name.name] = str(file)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module if node.module else ""
                    for name in node.names:
                        all_imports[f"{module}.{name.name}"] = str(file)
        except Exception as e:
            logger.error(f"Error analyzing {file}: {e}")

    # Second pass: collect usages
    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

            for definition in all_definitions:
                if definition in content:
                    all_usages.add(definition)
        except Exception as e:
            logger.error(f"Error analyzing usages in {file}: {e}")

    # Find unused code
    unused = set(all_definitions.keys()) - all_usages

    # Convert to set of (name, file_path) tuples
    unused_with_locations = {(name, all_definitions[name]) for name in unused}

    if unused and context.verbose:
        logger.warning("Potentially unused code:")
        for name, file_path in unused_with_locations:
            logger.warning(f"  - {name} in {file_path}")

    return unused_with_locations


def detect_circular_dependencies(
    directory: str, context: RefactoringContext
) -> List[List[str]]:
    """
    Detect circular dependencies in the codebase.

    Args:
        directory: Directory to analyze
        context: Refactoring context

    Returns:
        List of cycles, where each cycle is a list of files
    """
    logger.info(f"Detecting circular dependencies in {directory}...")

    # Build a directed graph of module dependencies
    graph = nx.DiGraph()

    # Add all Python files to the graph
    python_files = list(Path(directory).glob("**/*.py"))
    for file_path in python_files:
        try:
            # Add the file as a node
            graph.add_node(str(file_path))

            # Parse the file and analyze imports
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            analyzer = ImportAnalyzer(str(file_path))
            analyzer.visit(tree)

            # Add edges for all imports
            for imported_module in analyzer.imports:
                # Try to map the import to a file
                potential_files = []
                for other_file in python_files:
                    if imported_module in str(other_file):
                        potential_files.append(str(other_file))

                # Add an edge for each potential file
                for potential_file in potential_files:
                    graph.add_edge(str(file_path), potential_file)

        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")

    # Find circular dependencies
    try:
        cycles = list(nx.simple_cycles(graph))

        if cycles and context.verbose:
            logger.warning("Circular dependencies found:")
            for cycle in cycles:
                logger.warning(f"  - {' -> '.join(cycle)}")

        return cycles
    except nx.NetworkXNoCycle:
        logger.info("No circular dependencies found.")
        return []


class CodeSmellDetector:
    """Detects and reports code smells."""

    def __init__(self, context: RefactoringContext):
        self.context = context
        self.smells = []

    def detect_smells(self, file_path: Path) -> List[str]:
        """Detect code smells in a file."""
        self.smells = []

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read())

                # Check for long methods
                self._check_long_methods(tree)

                # Check for large classes
                self._check_large_classes(tree)

                # Check for too many function parameters
                self._check_too_many_parameters(tree)

                # Check for deeply nested structures
                self._check_deep_nesting(tree)

            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")

        return self.smells

    def _check_long_methods(self, tree: ast.AST) -> None:
        """Check for methods that are too long."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if len(node.body) > 20:  # Threshold for "too long"
                    self.smells.append(
                        f"Long method: {node.name} ({len(node.body)} lines)"
                    )

    def _check_large_classes(self, tree: ast.AST) -> None:
        """Check for classes with too many methods."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(methods) > 10:  # Threshold for "too many methods"
                    self.smells.append(
                        f"Large class: {node.name} ({len(methods)} methods)"
                    )

    def _check_too_many_parameters(self, tree: ast.AST) -> None:
        """Check for functions with too many parameters."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count required parameters (excluding *args, **kwargs, and those with default values)
                required_params = len([
                    arg
                    for arg in node.args.args
                    if arg.arg != "self" and arg.arg != "cls"
                ])

                if required_params > 5:  # Threshold for "too many parameters"
                    self.smells.append(
                        f"Too many parameters: {node.name} ({required_params} params)"
                    )

    def _check_deep_nesting(self, tree: ast.AST) -> None:
        """Check for deeply nested control structures."""
        # This is a simplified implementation - a full version would track nesting levels
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count nested if/for/while statements
                nested_nodes = 0
                for subnode in ast.walk(node):
                    if (
                        isinstance(subnode, (ast.If, ast.For, ast.While))
                        and subnode != node
                    ):
                        nested_nodes += 1

                if nested_nodes > 4:  # Threshold for "too deep nesting"
                    self.smells.append(
                        f"Deep nesting in: {node.name} ({nested_nodes} nested blocks)"
                    )


def analyze_cohesion(file_path: str, context: RefactoringContext) -> Dict[str, float]:
    """
    Analyze module cohesion and suggest refactorings.

    Args:
        file_path: File to analyze
        context: Refactoring context

    Returns:
        Dictionary of cohesion metrics
    """
    logger.info(f"Analyzing cohesion of {file_path}...")

    metrics = {
        "lack_of_cohesion": 0.0,
        "tight_class_cohesion": 0.0,
        "classes_analyzed": 0,
    }

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

        if not classes:
            logger.info(f"No classes found in {file_path}")
            return metrics

        metrics["classes_analyzed"] = len(classes)

        # Simple cohesion calculation based on shared attribute access
        for cls in classes:
            methods = [node for node in cls.body if isinstance(node, ast.FunctionDef)]

            if len(methods) <= 1:
                continue

            # Track attributes accessed by each method
            method_attrs = {}

            for method in methods:
                attrs = set()
                for node in ast.walk(method):
                    if isinstance(node, ast.Attribute) and isinstance(
                        node.value, ast.Name
                    ):
                        if node.value.id == "self":
                            attrs.add(node.attr)

                method_attrs[method.name] = attrs

            # Calculate Lack of Cohesion of Methods (LCOM)
            # LCOM = number of pairs of methods that don't share attributes
            no_shared_attrs = 0
            total_pairs = 0

            methods_names = list(method_attrs.keys())
            for i in range(len(methods_names)):
                for j in range(i + 1, len(methods_names)):
                    m1 = methods_names[i]
                    m2 = methods_names[j]
                    total_pairs += 1

                    if not (method_attrs[m1] & method_attrs[m2]):
                        no_shared_attrs += 1

            if total_pairs > 0:
                # Normalize to 0-1 where 0 is good cohesion and 1 is poor cohesion
                lcom = no_shared_attrs / total_pairs if total_pairs > 0 else 0
                metrics["lack_of_cohesion"] += lcom

                # Tight Class Cohesion (TCC) - opposite of LCOM
                tcc = 1 - lcom
                metrics["tight_class_cohesion"] += tcc

        # Average metrics across all classes
        if metrics["classes_analyzed"] > 0:
            metrics["lack_of_cohesion"] /= metrics["classes_analyzed"]
            metrics["tight_class_cohesion"] /= metrics["classes_analyzed"]

        # Log suggestions based on metrics
        if metrics["lack_of_cohesion"] > 0.7:
            logger.warning(
                f"High lack of cohesion ({metrics['lack_of_cohesion']:.2f}) in {file_path}"
            )
            logger.warning(
                "Suggestion: Consider splitting classes with low cohesion into multiple cohesive classes"
            )

    except Exception as e:
        logger.error(f"Error analyzing cohesion in {file_path}: {e}")

    return metrics
