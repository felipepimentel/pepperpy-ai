#!/usr/bin/env python3
"""
Project Structure Validator
Validates project structure, dependencies, and code patterns.
"""

import os
import sys
import ast
import fnmatch
import yaml
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, DefaultDict
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass
class ValidationStats:
    """Statistics for a module."""
    imports: Set[str]
    loc: int  # lines of code
    complexity: int  # cyclomatic complexity
    dependencies: Set[str]


class DependencyGraph:
    """Simple dependency graph implementation."""
    
    def __init__(self):
        self.graph: DefaultDict[str, Set[str]] = defaultdict(set)
        
    def add_node(self, node: str) -> None:
        """Add a node to the graph."""
        if node not in self.graph:
            self.graph[node] = set()
            
    def add_edge(self, from_node: str, to_node: str) -> None:
        """Add a directed edge to the graph."""
        self.add_node(from_node)
        self.add_node(to_node)
        self.graph[from_node].add(to_node)
    
    def find_cycles(self) -> List[List[str]]:
        """Find all cycles in the graph using DFS."""
        cycles: List[List[str]] = []
        visited = set()
        path = []
        
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
    """AST visitor to collect imports."""
    
    def __init__(self):
        self.imports: Set[str] = set()
        self.from_imports: DefaultDict[str, Set[str]] = defaultdict(set)
        
    def visit_Import(self, node: ast.Import) -> None:
        """Visit Import node."""
        for name in node.names:
            self.imports.add(name.name.split('.')[0])
            
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit ImportFrom node."""
        if node.module:
            base_module = node.module.split('.')[0]
            self.imports.add(base_module)
            for name in node.names:
                self.from_imports[base_module].add(name.name)


class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor to calculate cyclomatic complexity."""
    
    def __init__(self):
        self.complexity = 1
        
    def visit_If(self, node: ast.If) -> None:
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_While(self, node: ast.While) -> None:
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_For(self, node: ast.For) -> None:
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.complexity += 1
        self.generic_visit(node)


class StructureValidator:
    def __init__(self, root_dir: str = "."):
        self.root = Path(root_dir)
        self.structure_file = self.root / "docs" / "project_structure.yml"
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats: Dict[str, ValidationStats] = {}
        self.dependency_graph = DependencyGraph()
        
        # Load configuration
        with open(self.structure_file) as f:
            self.config = yaml.safe_load(f)
            
        self.validation_rules = self.config.get("validation_rules", {})
        self.allow_extra_files = self.validation_rules.get("allow_extra_files", False)
        self.required_files = set(self.validation_rules.get("required_files", []))
        self.ignore_patterns = self.validation_rules.get("ignore_patterns", [])
        
        # Architecture components and dependencies
        self.architecture = self.config.get("architecture", {})
        self.components = self.architecture.get("components", {})
        
        # Code quality thresholds
        self.max_complexity = self.validation_rules.get("max_complexity", 10)
        self.max_file_lines = self.validation_rules.get("max_file_lines", 500)

    def get_component_for_path(self, path: Path) -> Optional[str]:
        """Get the component name for a given path."""
        try:
            rel_path = str(path.relative_to(self.root / "pepperpy"))
            first_dir = rel_path.split(os.sep)[0]
            return first_dir if first_dir in self.components else None
        except ValueError:
            return None

    def analyze_file(self, file_path: Path) -> ValidationStats:
        """Analyze a Python file for metrics and dependencies."""
        with open(file_path) as f:
            content = f.read()
            tree = ast.parse(content)
            
        # Collect imports
        import_visitor = ImportVisitor()
        import_visitor.visit(tree)
        
        # Calculate complexity
        complexity_visitor = ComplexityVisitor()
        complexity_visitor.visit(tree)
        
        # Count lines of code (excluding empty lines and comments)
        loc = sum(1 for line in content.splitlines() 
                 if line.strip() and not line.strip().startswith('#'))
        
        return ValidationStats(
            imports=import_visitor.imports,
            loc=loc,
            complexity=complexity_visitor.complexity,
            dependencies=set()
        )

    def check_imports(self, file_path: Path) -> None:
        """Check imports in a Python file for dependency violations."""
        try:
            component = self.get_component_for_path(file_path)
            if not component:
                return
                
            stats = self.analyze_file(file_path)
            self.stats[str(file_path)] = stats
            
            # Update dependency graph
            allowed_deps = self.components[component].get("allowed_dependencies", [])
            self.dependency_graph.add_node(component)
            
            for imp in stats.imports:
                if imp == "pepperpy":
                    # Check internal imports
                    if "." in imp:
                        module = imp.split(".")[1]
                        if module not in allowed_deps and module != component:
                            self.errors.append(
                                f"Illegal import in {file_path}: {imp} "
                                f"(component {component} cannot depend on {module})"
                            )
                        self.dependency_graph.add_edge(component, module)
            
            # Check code quality metrics
            if stats.complexity > self.max_complexity:
                self.warnings.append(
                    f"High complexity in {file_path}: {stats.complexity} "
                    f"(max: {self.max_complexity})"
                )
            
            if stats.loc > self.max_file_lines:
                self.warnings.append(
                    f"File too long: {file_path}: {stats.loc} lines "
                    f"(max: {self.max_file_lines})"
                )
                
        except Exception as e:
            self.warnings.append(f"Could not check imports in {file_path}: {str(e)}")

    def check_circular_dependencies(self) -> None:
        """Check for circular dependencies in the component graph."""
        try:
            cycles = self.dependency_graph.find_cycles()
            for cycle in cycles:
                self.errors.append(
                    f"Circular dependency detected: {' -> '.join(cycle)}"
                )
        except Exception as e:
            self.warnings.append(f"Could not check circular dependencies: {str(e)}")

    def generate_dependency_graph(self) -> None:
        """Generate a dependency graph visualization using DOT format."""
        try:
            dot_content = self.dependency_graph.generate_dot()
            with open('dependency_graph.dot', 'w') as f:
                f.write(dot_content)
            print("\nDependency graph saved as 'dependency_graph.dot'")
            print("To visualize, install Graphviz and run: dot -Tpng dependency_graph.dot -o dependency_graph.png")
        except Exception as e:
            self.warnings.append(f"Could not generate dependency graph: {str(e)}")

    def validate_node(
        self,
        expected: Dict[str, Any],
        actual_path: Path,
        context: str = "",
    ) -> None:
        """Validate a node in the structure tree."""
        if not actual_path.exists():
            if expected.get("required", False):
                self.errors.append(f"Missing required path: {actual_path}")
            else:
                self.warnings.append(f"Missing optional path: {actual_path}")
            return

        # Validate type
        node_type = expected.get("type", "file")
        if node_type == "directory" or node_type == "module":
            if not actual_path.is_dir():
                self.errors.append(f"Expected directory at: {actual_path}")
                return
                
            # For modules, check for __init__.py if required
            if node_type == "module" and "__init__.py" in self.required_files:
                init_file = actual_path / "__init__.py"
                if not init_file.exists():
                    self.errors.append(f"Missing __init__.py in module: {actual_path}")
            
            # Process children
            children = expected.get("children", {})
            actual_children = set(
                item.name for item in actual_path.iterdir()
                if not self.should_ignore(item.name)
            )
            
            # Check for required children
            for child_name, child_spec in children.items():
                child_path = actual_path / child_name
                self.validate_node(
                    child_spec,
                    child_path,
                    f"{context}/{child_name}" if context else child_name
                )
                actual_children.discard(child_name)
            
            # Check for unexpected children
            if not self.allow_extra_files:
                for extra in actual_children:
                    if not self.should_ignore(extra):
                        self.errors.append(
                            f"Unexpected item in {actual_path}: {extra}"
                        )
        
        elif node_type == "file":
            if not actual_path.is_file():
                self.errors.append(f"Expected file at: {actual_path}")
            elif actual_path.suffix == '.py':
                self.check_imports(actual_path)

    def validate(self) -> bool:
        """Validate the project structure and dependencies."""
        try:
            root_spec = self.config.get("root", {})
            if not root_spec:
                raise ValidationError("No root specification found in config")
                
            project_root = self.root / root_spec.get("path", "pepperpy")
            if not project_root.exists():
                raise ValidationError(f"Project root not found: {project_root}")
            
            self.validate_node(root_spec, project_root)
            self.check_circular_dependencies()
            self.generate_dependency_graph()
            
            return len(self.errors) == 0
            
        except Exception as e:
            self.errors.append(f"Validation error: {str(e)}")
            return False

    def should_ignore(self, name: str) -> bool:
        """Check if a file/directory should be ignored."""
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
        avg_complexity = sum(stats.complexity for stats in self.stats.values()) / len(self.stats) if self.stats else 0
        print(f"  Total Lines of Code: {total_loc}")
        print(f"  Average Complexity: {avg_complexity:.2f}")
        print(f"  Total Files: {len(self.stats)}")
        
        if not self.errors and not self.warnings:
            print("\nProject structure and dependency validation passed!")
        else:
            print("\nPlease ensure your project structure and dependencies match docs/project_structure.yml")


def main() -> int:
    """Main entry point."""
    try:
        validator = StructureValidator()
        is_valid = validator.validate()
        validator.report()
        return 0 if is_valid else 1
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main()) 