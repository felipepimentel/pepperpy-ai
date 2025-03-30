"""Test generation tools for the refactoring system."""

import ast
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import coverage

from .context import RefactoringContext

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """Represents a generated test case."""

    function_name: str
    test_name: str
    description: str
    setup: List[str]
    assertions: List[str]
    cleanup: List[str]


@dataclass
class CoverageReport:
    """Coverage statistics for a module."""

    module_name: str
    line_coverage: float
    branch_coverage: float
    missing_lines: List[int]
    excluded_lines: List[int]
    branch_misses: List[Tuple[int, int]]  # (line, branch)


class TestGenerator:
    """Generate test cases for Python modules."""

    def __init__(self, context: RefactoringContext):
        self.context = context

    def generate_tests(self, module_path: str) -> List[TestCase]:
        """Generate test cases for a Python module.

        Args:
            module_path: Path to the module to test

        Returns:
            List of generated test cases
        """
        try:
            # Parse the module
            with open(module_path, "r") as f:
                tree = ast.parse(f.read())

            test_cases = []

            # Find testable functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    test_cases.extend(self._generate_function_tests(node))
                elif isinstance(node, ast.ClassDef):
                    test_cases.extend(self._generate_class_tests(node))

            return test_cases
        except Exception as e:
            self.context.logger.error(f"Failed to generate tests: {e}")
            return []

    def _generate_function_tests(self, node: ast.FunctionDef) -> List[TestCase]:
        """Generate test cases for a function."""
        test_cases = []

        # Skip private functions
        if node.name.startswith("_"):
            return []

        # Basic test case
        test_cases.append(
            TestCase(
                function_name=node.name,
                test_name=f"test_{node.name}_basic",
                description=f"Test basic functionality of {node.name}",
                setup=self._generate_setup(node),
                assertions=self._generate_assertions(node),
                cleanup=[],
            )
        )

        # Edge cases
        test_cases.append(
            TestCase(
                function_name=node.name,
                test_name=f"test_{node.name}_edge_cases",
                description=f"Test edge cases for {node.name}",
                setup=self._generate_edge_setup(node),
                assertions=self._generate_edge_assertions(node),
                cleanup=[],
            )
        )

        # Error cases
        test_cases.append(
            TestCase(
                function_name=node.name,
                test_name=f"test_{node.name}_errors",
                description=f"Test error handling in {node.name}",
                setup=self._generate_error_setup(node),
                assertions=self._generate_error_assertions(node),
                cleanup=[],
            )
        )

        return test_cases

    def _generate_class_tests(self, node: ast.ClassDef) -> List[TestCase]:
        """Generate test cases for a class."""
        test_cases = []

        # Skip private classes
        if node.name.startswith("_"):
            return []

        # Test initialization
        test_cases.append(
            TestCase(
                function_name=node.name,
                test_name=f"test_{node.name}_init",
                description=f"Test initialization of {node.name}",
                setup=self._generate_class_setup(node),
                assertions=self._generate_class_assertions(node),
                cleanup=self._generate_class_cleanup(node),
            )
        )

        # Test methods
        for method in self._get_public_methods(node):
            test_cases.extend(self._generate_method_tests(node, method))

        return test_cases

    def _generate_setup(self, node: ast.FunctionDef) -> List[str]:
        """Generate setup code for a function test."""
        setup = []

        # Import the function
        setup.append("from module import function")

        # Create test inputs based on parameters
        for arg in node.args.args:
            if hasattr(arg, "annotation"):
                arg_type = self._get_type_hint(arg.annotation)
                setup.append(f"{arg.arg} = self._create_test_value('{arg_type}')")
            else:
                setup.append(f"{arg.arg} = 'test_value'")

        return setup

    def _generate_assertions(self, node: ast.FunctionDef) -> List[str]:
        """Generate assertions for a function test."""
        assertions = []

        # Basic assertion
        assertions.append(
            f"result = {node.name}({', '.join(arg.arg for arg in node.args.args)})"
        )
        assertions.append("assert result is not None")

        # Type check if return annotation exists
        if hasattr(node, "returns"):
            return_type = self._get_type_hint(node.returns)
            assertions.append(f"assert isinstance(result, {return_type})")

        return assertions

    def _generate_edge_setup(self, node: ast.FunctionDef) -> List[str]:
        """Generate setup code for edge case tests."""
        setup = []

        # Import the function
        setup.append("from module import function")

        # Create edge case inputs
        for arg in node.args.args:
            if hasattr(arg, "annotation"):
                arg_type = self._get_type_hint(arg.annotation)
                setup.append(f"{arg.arg} = self._create_edge_value('{arg_type}')")
            else:
                setup.append(f"{arg.arg} = None")  # Edge case: None

        return setup

    def _generate_edge_assertions(self, node: ast.FunctionDef) -> List[str]:
        """Generate assertions for edge case tests."""
        assertions = []

        # Test with edge case values
        assertions.append(
            f"result = {node.name}({', '.join(arg.arg for arg in node.args.args)})"
        )
        assertions.append("assert result is not None")

        return assertions

    def _generate_error_setup(self, node: ast.FunctionDef) -> List[str]:
        """Generate setup code for error case tests."""
        setup = []

        # Import the function
        setup.append("from module import function")

        # Create invalid inputs
        for arg in node.args.args:
            if hasattr(arg, "annotation"):
                arg_type = self._get_type_hint(arg.annotation)
                setup.append(f"{arg.arg} = self._create_invalid_value('{arg_type}')")
            else:
                setup.append(f"{arg.arg} = object()")  # Invalid type

        return setup

    def _generate_error_assertions(self, node: ast.FunctionDef) -> List[str]:
        """Generate assertions for error case tests."""
        assertions = []

        # Test error handling
        assertions.append("with pytest.raises(Exception):")
        assertions.append(
            f"    {node.name}({', '.join(arg.arg for arg in node.args.args)})"
        )

        return assertions

    def _generate_class_setup(self, node: ast.ClassDef) -> List[str]:
        """Generate setup code for class tests."""
        setup = []

        # Import the class
        setup.append("from module import class")

        # Create instance with default values
        setup.append(f"instance = {node.name}()")

        return setup

    def _generate_class_assertions(self, node: ast.ClassDef) -> List[str]:
        """Generate assertions for class tests."""
        assertions = []

        # Test instance creation
        assertions.append(f"assert isinstance(instance, {node.name})")

        # Test attributes
        for attr in self._get_attributes(node):
            assertions.append(f"assert hasattr(instance, '{attr}')")

        return assertions

    def _generate_class_cleanup(self, node: ast.ClassDef) -> List[str]:
        """Generate cleanup code for class tests."""
        cleanup = []

        # Clean up instance
        cleanup.append("del instance")

        return cleanup

    def _generate_method_tests(
        self, class_node: ast.ClassDef, method_node: ast.FunctionDef
    ) -> List[TestCase]:
        """Generate test cases for a class method."""
        test_cases = []

        # Basic method test
        test_cases.append(
            TestCase(
                function_name=f"{class_node.name}.{method_node.name}",
                test_name=f"test_{class_node.name}_{method_node.name}_basic",
                description=f"Test basic functionality of {method_node.name}",
                setup=[
                    f"instance = {class_node.name}()",
                    *self._generate_setup(method_node),
                ],
                assertions=[*self._generate_assertions(method_node)],
                cleanup=["del instance"],
            )
        )

        return test_cases

    def _get_public_methods(self, node: ast.ClassDef) -> List[ast.FunctionDef]:
        """Get public methods from a class."""
        methods = []

        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef) and not child.name.startswith("_"):
                methods.append(child)

        return methods

    def _get_attributes(self, node: ast.ClassDef) -> List[str]:
        """Get attributes from a class."""
        attributes = []

        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)

        return attributes

    def _get_type_hint(self, annotation: Optional[ast.AST]) -> str:
        """Convert AST annotation to type hint string."""
        if annotation is None:
            return "Any"

        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Subscript):
            if isinstance(annotation.value, ast.Name):
                value_id = annotation.value.id
                slice_hint = self._get_type_hint(annotation.slice)
                return f"{value_id}[{slice_hint}]"
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        return "Any"


class CoverageReporter:
    """Generate coverage reports for tests."""

    def __init__(self, context: RefactoringContext):
        self.context = context
        self._cov = coverage.Coverage()

    def start_coverage(self) -> None:
        """Start collecting coverage data."""
        self._cov.start()

    def stop_coverage(self) -> None:
        """Stop collecting coverage data."""
        self._cov.stop()

    def get_report(self, module_path: str) -> CoverageReport:
        """Get coverage report for a module.

        Args:
            module_path: Path to the module to analyze

        Returns:
            Coverage statistics for the module
        """
        try:
            # Save coverage data
            self._cov.save()

            # Load data for analysis
            analysis = self._cov.analysis2(module_path)

            # Calculate coverage metrics
            total_lines = len(analysis[1])  # Executable lines
            covered_lines = total_lines - len(analysis[2])  # Missing lines
            line_coverage = covered_lines / total_lines if total_lines > 0 else 0

            # Get branch coverage if available
            branch_coverage = 0.0
            branch_misses: List[Tuple[int, int]] = []

            # Check if analysis has branch information
            if len(analysis) > 6:
                total_branches = len(analysis[4])  # All branches
                missed_branches = len(analysis[6])  # Missing branches
                branch_coverage = (
                    (total_branches - missed_branches) / total_branches
                    if total_branches > 0
                    else 0
                )
                # Convert branch misses to proper format
                if isinstance(analysis[6], list):
                    branch_misses = [
                        (int(line), int(branch)) for line, branch in analysis[6]
                    ]

            return CoverageReport(
                module_name=Path(module_path).stem,
                line_coverage=line_coverage,
                branch_coverage=branch_coverage,
                missing_lines=analysis[2],
                excluded_lines=analysis[3],
                branch_misses=branch_misses,
            )
        except Exception as e:
            self.context.logger.error(f"Failed to generate coverage report: {e}")
            return CoverageReport(
                module_name=Path(module_path).stem,
                line_coverage=0.0,
                branch_coverage=0.0,
                missing_lines=[],
                excluded_lines=[],
                branch_misses=[],
            )
