#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Impact analysis for refactoring operations.

This module provides tools to analyze the potential impact of refactoring
operations before they are executed, to help make informed decisions.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List

import networkx as nx

from .common import RefactoringContext, logger
from .imports_manager import ImportAnalyzer


def analyze_import_update_impact(
    directory: str, import_map: Dict[str, str], context: RefactoringContext
) -> Dict[str, List[str]]:
    """
    Analyze the impact of updating imports.

    Args:
        directory: Directory to analyze
        import_map: Mapping of old imports to new imports
        context: Refactoring context

    Returns:
        Dictionary mapping files to affected imports
    """
    logger.info(f"Analyzing impact of import updates in {directory}...")
    impact = {}

    files = Path(directory).glob("**/*.py")
    for file in files:
        file_str = str(file)
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for each import in the map
            affected_imports = []
            for old_import in import_map:
                if old_import in content:
                    affected_imports.append(old_import)

            if affected_imports:
                impact[file_str] = affected_imports
                if context.verbose:
                    logger.info(
                        f"File {file_str} has {len(affected_imports)} affected imports"
                    )

        except Exception as e:
            logger.error(f"Error analyzing {file}: {e}")

    # Summary
    total_files = len(impact)
    total_imports = sum(len(imports) for imports in impact.values())
    logger.info(
        f"Impact analysis: {total_files} files and {total_imports} import statements affected"
    )

    return impact


def analyze_file_move_impact(
    file_mapping: Dict[str, str], context: RefactoringContext
) -> Dict[str, List[str]]:
    """
    Analyze the impact of moving files.

    Args:
        file_mapping: Mapping of old file paths to new file paths
        context: Refactoring context

    Returns:
        Dictionary mapping files to their dependent files
    """
    logger.info("Analyzing impact of file moves...")
    impact = {}

    # Build dependency graph
    graph = nx.DiGraph()

    # Add all Python files to the graph
    for root, _, files in os.walk("pepperpy"):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                graph.add_node(file_path)

    # Add edges for dependencies
    for node in graph.nodes:
        try:
            with open(node, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            analyzer = ImportAnalyzer(node)
            analyzer.visit(tree)

            # Find potentially affected files
            content = Path(node).read_text(encoding="utf-8")

            for old_path in file_mapping:
                if old_path in content:
                    # This file imports from a file that's being moved
                    if old_path not in impact:
                        impact[old_path] = []
                    impact[old_path].append(node)

                    # Add edge in the graph
                    graph.add_edge(node, old_path)

        except Exception as e:
            logger.error(f"Error analyzing {node}: {e}")

    # Find nodes that would be affected by changes to the moved files
    for old_path in file_mapping:
        if old_path in graph:
            # Get all descendants (files that depend on this one)
            descendants = list(nx.descendants(graph, old_path))
            if descendants:
                if old_path not in impact:
                    impact[old_path] = []
                impact[old_path].extend(descendants)

    # Summary
    total_files = len(impact)
    total_dependents = sum(len(set(deps)) for deps in impact.values())
    logger.info(
        f"Impact analysis: {total_files} files moved will affect {total_dependents} dependent files"
    )

    return impact


def analyze_task_impact(
    task_id: str, context: RefactoringContext
) -> Dict[str, List[str]]:
    """
    Analyze the impact of running a specific task.

    Args:
        task_id: Task ID to analyze
        context: Refactoring context

    Returns:
        Dictionary with impact analysis
    """
    from .common import TASK_MAP

    logger.info(f"Analyzing impact of task {task_id}...")
    impact = {}

    if task_id not in TASK_MAP:
        logger.error(f"Task {task_id} not found")
        return impact

    # Analyze based on the specific task
    if task_id == "1.1.1":
        # Consolidating exceptions
        error_import_map = {
            "pepperpy.llm.errors": "pepperpy.core.errors",
            "pepperpy.rag.errors": "pepperpy.core.errors",
        }
        impact["imports"] = analyze_import_update_impact(
            "pepperpy", error_import_map, context
        )
        impact["files"] = [
            "pepperpy/llm/errors.py",
            "pepperpy/rag/errors.py",
            "pepperpy/core/errors.py",
        ]

    elif task_id == "1.2.1":
        # Consolidating events
        events_import_map = {
            "pepperpy.events": "pepperpy.infra.events",
        }
        impact["imports"] = analyze_import_update_impact(
            "pepperpy", events_import_map, context
        )
        impact["files"] = [
            "pepperpy/events/base.py",
            "pepperpy/events/handlers.py",
            "pepperpy/events/registry.py",
            "pepperpy/infra/events.py",
        ]

    elif task_id == "1.2.2":
        # Consolidating streaming
        streaming_import_map = {
            "pepperpy.streaming": "pepperpy.infra.streaming",
        }
        impact["imports"] = analyze_import_update_impact(
            "pepperpy", streaming_import_map, context
        )
        impact["files"] = [
            "pepperpy/streaming/base.py",
            "pepperpy/streaming/handlers.py",
            "pepperpy/streaming/processors.py",
            "pepperpy/infra/streaming.py",
        ]

    elif task_id == "2.1.1":
        # Organize embedding functionality
        impact["files"] = ["pepperpy/llm/embedding.py"]

    elif task_id == "2.1.2":
        # Implement LLM providers
        impact["files"] = [
            "pepperpy/llm/providers/__init__.py",
            "pepperpy/llm/providers/base.py",
        ]

    elif task_id == "2.2.1":
        # Finalize RAG models
        impact["files"] = ["pepperpy/rag/models.py"]

    # Print summary
    logger.info(f"Task {task_id} impact analysis:")

    if "imports" in impact:
        total_files = len(impact["imports"])
        total_imports = sum(len(imports) for imports in impact["imports"].values())
        logger.info(
            f"  - {total_files} files with {total_imports} import statements affected"
        )

    if "files" in impact:
        logger.info(f"  - {len(impact['files'])} files directly modified")
        for file in impact["files"]:
            logger.info(f"    - {file}")

    return impact


def analyze_phase_impact(phase: int, context: RefactoringContext) -> Dict[str, Dict]:
    """
    Analyze the impact of running all tasks in a phase.

    Args:
        phase: Phase number
        context: Refactoring context

    Returns:
        Dictionary with impact analysis for each task
    """
    from .common import TASK_MAP

    logger.info(f"Analyzing impact of phase {phase}...")
    impact = {}

    # Find all tasks for the phase
    phase_prefix = f"{phase}."
    phase_tasks = [
        task_id for task_id in TASK_MAP.keys() if task_id.startswith(phase_prefix)
    ]

    if not phase_tasks:
        logger.error(f"No tasks found for phase {phase}")
        return impact

    # Sort tasks
    phase_tasks.sort(key=lambda x: [int(p) for p in x.split(".")])

    # Analyze each task
    for task_id in phase_tasks:
        impact[task_id] = analyze_task_impact(task_id, context)

    # Print summary
    logger.info(f"Phase {phase} impact analysis:")
    logger.info(f"  - {len(phase_tasks)} tasks will be executed")

    # Count unique files affected
    all_files = set()
    for task_id, task_impact in impact.items():
        if "files" in task_impact:
            all_files.update(task_impact["files"])

    logger.info(f"  - {len(all_files)} unique files will be modified")

    return impact
