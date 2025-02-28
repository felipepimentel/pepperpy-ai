#!/usr/bin/env python3
"""Script to check for circular dependencies in the PepperPy codebase.

This script analyzes Python files to detect import cycles between modules.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple


def extract_imports(file_path: Path) -> List[str]:
    """Extract import statements from a Python file.

    Args:
        file_path: Path to the Python file

    Returns:
        List of imported modules
    """
    imports = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Match 'import pepperpy.x.y' patterns
        import_pattern = r"import\s+(pepperpy\.[^\s;]+)"
        for match in re.finditer(import_pattern, content):
            imports.append(match.group(1))

        # Match 'from pepperpy.x.y import z' patterns
        from_pattern = r"from\s+(pepperpy\.[^\s;]+)\s+import"
        for match in re.finditer(from_pattern, content):
            imports.append(match.group(1))

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return imports


def build_dependency_graph(project_root: Path) -> Dict[str, Set[str]]:
    """Build a dependency graph of the project.

    Args:
        project_root: Path to the project root

    Returns:
        Dictionary mapping module names to sets of imported modules
    """
    graph: Dict[str, Set[str]] = {}

    # Skip directories
    skip_dirs = {".git", ".venv", "backup", "__pycache__", "scripts"}

    for root, dirs, files in os.walk(project_root / "pepperpy"):
        # Skip specified directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file

                # Get module name
                rel_path = file_path.relative_to(project_root)
                module_name = str(rel_path).replace("/", ".").replace(".py", "")

                # Special case for __init__.py
                if module_name.endswith(".__init__"):
                    module_name = module_name[:-9]

                # Extract imports
                imports = extract_imports(file_path)

                # Add to graph
                if module_name not in graph:
                    graph[module_name] = set()

                for imported_module in imports:
                    graph[module_name].add(imported_module)

    return graph


def find_cycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
    """Find cycles in the dependency graph.

    Args:
        graph: Dependency graph

    Returns:
        List of cycles, where each cycle is a list of module names
    """
    cycles: List[List[str]] = []
    visited: Set[str] = set()
    path: List[str] = []
    path_set: Set[str] = set()

    def dfs(node: str):
        if node in path_set:
            # Found a cycle
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:] + [node])
            return

        if node in visited:
            return

        visited.add(node)
        path.append(node)
        path_set.add(node)

        for neighbor in graph.get(node, set()):
            dfs(neighbor)

        path.pop()
        path_set.remove(node)

    # Run DFS from each node
    for node in graph:
        if node not in visited:
            dfs(node)

    return cycles


def analyze_cycles(cycles: List[List[str]]) -> List[Tuple[List[str], str]]:
    """Analyze cycles to provide more context.

    Args:
        cycles: List of cycles

    Returns:
        List of tuples (cycle, description)
    """
    analyzed_cycles: List[Tuple[List[str], str]] = []

    for cycle in cycles:
        # Skip self-imports
        if len(cycle) <= 2 and cycle[0] == cycle[-1]:
            continue

        # Analyze the cycle
        description = ""

        # Check if it's a parent-child cycle
        if len(cycle) == 3 and cycle[0] == cycle[-1]:
            parent = cycle[0]
            child = cycle[1]
            if child.startswith(parent + "."):
                description = (
                    f"Parent-child cycle: {parent} imports from its child {child}"
                )

        # Check if it's between capabilities
        if any("capabilities" in module for module in cycle):
            description = "Cycle involves capabilities modules"

        # Check if it's between providers
        if any("providers" in module for module in cycle):
            description = "Cycle involves provider modules"

        # Default description
        if not description:
            description = f"Cycle of length {len(cycle) - 1}"

        analyzed_cycles.append((cycle, description))

    return analyzed_cycles


def main():
    """Main function."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent

    print("Checking for circular dependencies in PepperPy...")
    print("=" * 50)

    # Build dependency graph
    print("\nBuilding dependency graph...")
    graph = build_dependency_graph(project_root)
    print(f"Found {len(graph)} modules")

    # Find cycles
    print("\nFinding cycles...")
    cycles = find_cycles(graph)

    # Analyze cycles
    analyzed_cycles = analyze_cycles(cycles)

    # Print results
    if analyzed_cycles:
        print(f"\nFound {len(analyzed_cycles)} circular dependencies:")
        for i, (cycle, description) in enumerate(analyzed_cycles, 1):
            print(f"\n{i}. {description}")
            print("   " + " -> ".join(cycle))
    else:
        print("\nNo circular dependencies found!")

    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()
