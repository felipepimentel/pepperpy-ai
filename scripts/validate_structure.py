#!/usr/bin/env python3
"""Project structure validation script.

This script validates the project structure against the defined schema.
"""

import ast
import fnmatch
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ValidationStats:
    """Statistics for a module."""

    imports: set[str]
    loc: int  # lines of code
    complexity: int  # cyclomatic complexity
    dependencies: set[str]


class DependencyGraph:
    """Simple dependency graph implementation."""

    def __init__(self) -> None:
        self.graph: defaultdict[str, set[str]] = defaultdict(set)

    def add_node(self, node: str) -> None:
        """Add a node to the graph."""
        if node not in self.graph:
            self.graph[node] = set()

    def add_edge(self, from_node: str, to_node: str) -> None:
        """Add a directed edge to the graph."""
        self.add_node(from_node)
        self.add_node(to_node)
        self.graph[from_node].add(to_node)

    def find_cycles(self) -> list[list[str]]:
        """Find all cycles in the graph using DFS."""
        cycles: list[list[str]] = []
        visited = set()
        path: list[str] = []

        def dfs(node: str) -> None:
            if node in path:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return

            if node in visited:
                return

            visited.add(node)
            path.append(node)

            for neighbor in self.graph[node]:
                dfs(neighbor)

            path.pop()

        for node in self.graph:
            if node not in visited:
                dfs(node)

        return cycles

    def generate_dot(self) -> str:
        """Generate DOT format for graph visualization."""
        dot = ["digraph G {"]
        for node in self.graph:
            for dep in self.graph[node]:
                dot.append(f'    "{node}" -> "{dep}";')
        dot.append("}")
        return "\n".join(dot)


class ValidationError(Exception):
    """Validation specific error."""

    pass


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to collect imports and complexity metrics."""

    def __init__(self) -> None:
        """Initialize the import visitor."""
        self.imports: set[str] = set()
        self.from_imports: defaultdict[str, set] = defaultdict(set)
        self.complexity = 1

    def visit_import(self, node: ast.Import) -> None:
        """Visit Import node.

        Args:
            node: The AST Import node
        """
        for name in node.names:
            self.imports.add(name.name.split(".")[0])

    def visit_importfrom(self, node: ast.ImportFrom) -> None:
        """Visit ImportFrom node.

        Args:
            node: The AST ImportFrom node
        """
        if node.module:
            module = node.module.split(".")[0]
            for name in node.names:
                self.from_imports[module].add(name.name)

    def visit_if(self, node: ast.If) -> None:
        """Visit If node.

        Args:
            node: The AST If node
        """
        self.complexity += 1
        self.generic_visit(node)

    def visit_while(self, node: ast.While) -> None:
        """Visit While node.

        Args:
            node: The AST While node
        """
        self.complexity += 1
        self.generic_visit(node)

    def visit_for(self, node: ast.For) -> None:
        """Visit For node.

        Args:
            node: The AST For node
        """
        self.complexity += 1
        self.generic_visit(node)

    def visit_excepthandler(self, node: ast.ExceptHandler) -> None:
        """Visit ExceptHandler node.

        Args:
            node: The AST ExceptHandler node
        """
        self.complexity += 1
        self.generic_visit(node)


class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor for calculating cyclomatic complexity."""

    def __init__(self) -> None:
        """Initialize the complexity visitor."""
        self.complexity = 1

    def visit_if(self, node: ast.If) -> None:
        """Visit if statement.

        Args:
            node: The AST node to visit.
        """
        self.complexity += 1
        self.generic_visit(node)

    def visit_while(self, node: ast.While) -> None:
        """Visit while statement.

        Args:
            node: The AST node to visit.
        """
        self.complexity += 1
        self.generic_visit(node)

    def visit_for(self, node: ast.For) -> None:
        """Visit for statement.

        Args:
            node: The AST node to visit.
        """
        self.complexity += 1
        self.generic_visit(node)

    def visit_except_handler(self, node: ast.ExceptHandler) -> None:
        """Visit except handler.

        Args:
            node: The AST node to visit.
        """
        self.complexity += 1
        self.generic_visit(node)


class StructureValidator:
    """Validates project structure and dependencies."""

    def __init__(self, root: Path | None = None) -> None:
        """Initialize the validator.

        Args:
            root: Root directory of the project.
        """
        self.root = root or Path(__file__).parent.parent
        self.config = self._load_config()
        self.stats: dict[str, ValidationStats] = {}
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.ignore_patterns = [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".git",
            ".env",
            "*.egg-info",
            "dist",
            "build",
        ]
        self.dependency_graph = DependencyGraph()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from YAML.

        Returns:
            The loaded configuration.

        Raises:
            FileNotFoundError: If config file not found.
            yaml.YAMLError: If config file is invalid.
        """
        config_path = self.root / ".product" / "project_structure.yml"
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with open(config_path) as f:
            config: dict[str, Any] = yaml.safe_load(f)
            return config

    def validate_node(self, spec: dict[str, Any], path: Path) -> None:
        """Validate a node in the project structure.

        Args:
            spec: Node specification from config.
            path: Path to the node.
        """
        if not path.exists():
            self.errors.append(f"Missing required path: {path}")
            return

        if path.is_file():
            self._validate_file(spec, path)
        else:
            self._validate_directory(spec, path)

    def _validate_file(self, spec: dict[str, Any], path: Path) -> None:
        """Validate a file.

        Args:
            spec: File specification from config.
            path: Path to the file.
        """
        if path.suffix == ".py":
            self._analyze_python_file(path)

    def _validate_directory(self, spec: dict[str, Any], path: Path) -> None:
        """Validate a directory.

        Args:
            spec: Directory specification from config.
            path: Path to the directory.
        """
        for child_name, child_spec in spec.get("children", {}).items():
            child_path = path / child_name
            self.validate_node(child_spec, child_path)

    def _analyze_python_file(self, path: Path) -> None:
        """Analyze a Python file.

        Args:
            path: Path to the file.
        """
        try:
            with open(path) as f:
                content = f.read()
                tree = ast.parse(content)

            visitor = ComplexityVisitor()
            visitor.visit(tree)

            self.stats[str(path)] = ValidationStats(
                imports=set(),
                loc=len(content.splitlines()),
                complexity=visitor.complexity,
                dependencies=set(),
            )

        except Exception as e:
            self.errors.append(f"Error analyzing {path}: {e}")

    def check_circular_dependencies(self) -> None:
        """Check for circular dependencies in the project."""
        try:
            cycles = self.dependency_graph.find_cycles()
            for cycle in cycles:
                self.errors.append(
                    f"Circular dependency detected: {' -> '.join(cycle)}"
                )
        except Exception as e:
            self.warnings.append(f"Could not check circular dependencies: {e!s}")

    def generate_dependency_graph(self) -> None:
        """Generate a dependency graph visualization."""
        try:
            dot_content = self.dependency_graph.generate_dot()
            with open("dependency_graph.dot", "w") as f:
                f.write(dot_content)
            print("\nDependency graph saved as 'dependency_graph.dot'")
            print(
                "To visualize, install Graphviz and run: "
                "dot -Tpng dependency_graph.dot -o dependency_graph.png"
            )
        except Exception as e:
            self.warnings.append(f"Could not generate dependency graph: {e!s}")

    def validate(self) -> bool:
        """Validate the project structure and dependencies.

        Returns:
            True if validation succeeds, False otherwise.
        """
        try:
            root_spec = self.config.get("root", {})
            if not root_spec:
                raise ValueError("No root specification found in config")

            project_root = self.root / root_spec.get("path", "pepperpy")
            if not project_root.exists():
                raise ValueError(f"Project root not found: {project_root}")

            self.validate_node(root_spec, project_root)
            self.check_circular_dependencies()
            self.generate_dependency_graph()

            return len(self.errors) == 0

        except Exception as e:
            self.errors.append(f"Validation error: {e}")
            return False

    def should_ignore(self, name: str) -> bool:
        """Check if a file/directory should be ignored.

        Args:
            name: Name of the file/directory.

        Returns:
            True if the file/directory should be ignored.
        """
        return any(fnmatch.fnmatch(name, pattern) for pattern in self.ignore_patterns)

    def report(self) -> None:
        """Print validation report."""
        if self.errors:
            print("\nStructure and Dependency Validation Errors:")
            for error in sorted(self.errors):
                print(f"  - {error}")

        if self.warnings:
            print("\nWarnings:")
            for warning in sorted(self.warnings):
                print(f"  - {warning}")

        # Print statistics
        print("\nCode Statistics:")
        total_loc = sum(stats.loc for stats in self.stats.values())
        avg_complexity = (
            sum(stats.complexity for stats in self.stats.values()) / len(self.stats)
            if self.stats
            else 0
        )
        print(f"  Total Lines of Code: {total_loc}")
        print(f"  Average Complexity: {avg_complexity:.2f}")
        print(f"  Total Files: {len(self.stats)}")

        if not self.errors and not self.warnings:
            print("\nProject structure and dependency validation passed!")
        else:
            print(
                "Please ensure your project structure and dependencies match "
                ".product/project_structure.yml"
            )


def load_structure_config(config_path: str) -> dict[str, Any]:
    """Load the structure configuration from YAML.

    Args:
        config_path: Path to the configuration file.

    Returns:
        The loaded configuration dictionary.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If the configuration file is invalid.
    """
    with open(config_path) as f:
        config = yaml.safe_load(f)
        if not isinstance(config, dict):
            raise yaml.YAMLError("Configuration must be a dictionary")
        return config


def validate_directory(path: Path, expected: list[str]) -> bool:
    """Validate a directory against expected contents.

    Args:
        path: Path to the directory to validate.
        expected: List of expected files/directories.

    Returns:
        True if validation succeeds, False otherwise.
    """
    actual = {p.name for p in path.iterdir()}
    return all(e in actual for e in expected)


def validate_structure(root_path: Path, config: dict) -> bool:
    """Validate project structure against configuration.

    Args:
        root_path: Project root path
        config: Configuration dictionary

    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
        # Check directories
        print("Validating directories...")
        for directory in config.get("directories", []):
            dir_path = root_path / directory
            if not dir_path.exists():
                print(f"Missing directory: {directory}")
                return False
            print(f"Found directory: {directory}")

        # Check files
        print("Validating files...")
        for file in config.get("files", []):
            file_path = root_path / file
            if not file_path.exists():
                print(f"Missing file: {file}")
                return False
            print(f"Found file: {file}")

        return True

    except Exception as e:
        print(f"Error during validation: {e!s}")
        return False


def main() -> None:
    """Main entry point."""
    try:
        root_path = Path(__file__).parent.parent  # Only go up two levels
        config_path = root_path / ".product" / "project_structure.yml"

        print(f"Loading config from: {config_path}")
        with open(config_path) as f:
            config = yaml.safe_load(f)

        if validate_structure(root_path, config):
            print("✅ Project structure validation passed")
            sys.exit(0)
        else:
            print("❌ Project structure validation failed")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e!s}")
        sys.exit(2)


if __name__ == "__main__":
    main()
