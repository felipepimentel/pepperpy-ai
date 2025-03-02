"""Specific code analyzers implementation.

This module provides concrete implementations of code analyzers for
security analysis, complexity analysis, and other specialized checks.
"""

import ast
import importlib.util
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pepperpy.core.common.analysis.types import (
    AnalysisLevel,
    AnalysisResult,
    BaseVisitor,
    CodeAnalyzer,
)


class SecurityVisitor(BaseVisitor):
    """AST visitor for security analysis.

    Detects use of potentially dangerous functions and modules.

    Attributes:
        banned_functions: Set of function names that are considered unsafe
        banned_modules: Set of module names that are considered unsafe
    """

    def __init__(
        self,
        banned_functions: Optional[Set[str]] = None,
        banned_modules: Optional[Set[str]] = None,
    ) -> None:
        """Initialize security visitor.

        Args:
            banned_functions: Functions to flag as unsafe
            banned_modules: Modules to flag as unsafe
        """
        super().__init__()
        self.banned_functions = banned_functions or {
            "eval",
            "exec",
            "compile",
            "__import__",
        }
        self.banned_modules = banned_modules or {"subprocess", "os.system"}

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function/method calls.

        Args:
            node: AST call node
        """
        if isinstance(node.func, ast.Name):
            if node.func.id in self.banned_functions:
                self.add_result(
                    level=AnalysisLevel.ERROR,
                    message=f"Use of banned function: {node.func.id}",
                    node=node,
                    details={"function": node.func.id},
                )
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statements.

        Args:
            node: AST import node
        """
        for name in node.names:
            if name.name in self.banned_modules:
                self.add_result(
                    level=AnalysisLevel.ERROR,
                    message=f"Import of banned module: {name.name}",
                    node=node,
                    details={"module": name.name},
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from-import statements.

        Args:
            node: AST import-from node
        """
        if node.module in self.banned_modules:
            self.add_result(
                level=AnalysisLevel.ERROR,
                message=f"Import from banned module: {node.module}",
                node=node,
                details={"module": node.module},
            )
        self.generic_visit(node)


class ComplexityVisitor(BaseVisitor):
    """AST visitor for complexity analysis.

    Calculates cyclomatic complexity of functions and methods.

    Attributes:
        max_complexity: Maximum allowed complexity
        current_complexity: Current complexity being calculated
    """

    def __init__(self, max_complexity: int = 10) -> None:
        """Initialize complexity visitor.

        Args:
            max_complexity: Maximum allowed complexity
        """
        super().__init__()
        self.max_complexity = max_complexity
        self.current_complexity = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions.

        Args:
            node: AST function node
        """
        old_complexity = self.current_complexity
        self.current_complexity = 1

        self.generic_visit(node)

        if self.current_complexity > self.max_complexity:
            self.add_result(
                level=AnalysisLevel.WARNING,
                message=f"Function {node.name} has complexity {self.current_complexity}",
                node=node,
                details={
                    "complexity": self.current_complexity,
                    "max_allowed": self.max_complexity,
                },
            )

        self.current_complexity = old_complexity

    def visit_If(self, node: ast.If) -> None:
        """Visit if statements.

        Args:
            node: AST if node
        """
        self.current_complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        """Visit while loops.

        Args:
            node: AST while node
        """
        self.current_complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """Visit for loops.

        Args:
            node: AST for node
        """
        self.current_complexity += 1
        self.generic_visit(node)


class SecurityAnalyzer(CodeAnalyzer):
    """Analyzer for security issues in code.

    Detects use of potentially dangerous functions and modules.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize security analyzer.

        Args:
            config: Optional configuration with banned functions/modules
        """
        self.config = config or {}
        self.banned_functions = self.config.get("banned_functions", None)
        self.banned_modules = self.config.get("banned_modules", None)

    def analyze(self, code: str) -> List[AnalysisResult]:
        """Analyze source code string.

        Args:
            code: Source code to analyze

        Returns:
            List of security issues found

        Raises:
            SyntaxError: If code is invalid Python
        """
        try:
            tree = ast.parse(code)
            visitor = SecurityVisitor(
                banned_functions=self.banned_functions,
                banned_modules=self.banned_modules,
            )
            visitor.visit(tree)
            return visitor.results
        except SyntaxError as e:
            return [
                AnalysisResult(
                    level=AnalysisLevel.ERROR,
                    message="Syntax error in code",
                    line=e.lineno,
                    column=e.offset,
                    details={"error": str(e)},
                )
            ]

    def analyze_file(self, path: str) -> List[AnalysisResult]:
        """Analyze a source file.

        Args:
            path: Path to source file

        Returns:
            List of security issues found

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file can't be read
        """
        try:
            code = Path(path).read_text()
            return self.analyze(code)
        except (FileNotFoundError, PermissionError) as e:
            return [
                AnalysisResult(
                    level=AnalysisLevel.ERROR,
                    message=f"Failed to read file: {path}",
                    details={"error": str(e)},
                )
            ]

    def analyze_module(self, module: str) -> List[AnalysisResult]:
        """Analyze an imported module.

        Args:
            module: Fully qualified module name

        Returns:
            List of security issues found

        Raises:
            ImportError: If module can't be imported
        """
        try:
            spec = importlib.util.find_spec(module)
            if spec is None or spec.origin is None:
                return [
                    AnalysisResult(
                        level=AnalysisLevel.ERROR,
                        message=f"Module not found: {module}",
                        details={"module": module},
                    )
                ]
            return self.analyze_file(spec.origin)
        except ImportError as e:
            return [
                AnalysisResult(
                    level=AnalysisLevel.ERROR,
                    message=f"Failed to import module: {module}",
                    details={"error": str(e)},
                )
            ]


class ComplexityAnalyzer(CodeAnalyzer):
    """Analyzer for code complexity.

    Calculates cyclomatic complexity of functions and methods.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize complexity analyzer.

        Args:
            config: Optional configuration with complexity thresholds
        """
        self.config = config or {}
        self.max_complexity = self.config.get("max_complexity", 10)

    def analyze(self, code: str) -> List[AnalysisResult]:
        """Analyze source code string.

        Args:
            code: Source code to analyze

        Returns:
            List of complexity issues found

        Raises:
            SyntaxError: If code is invalid Python
        """
        try:
            tree = ast.parse(code)
            visitor = ComplexityVisitor(self.max_complexity)
            visitor.visit(tree)
            return visitor.results
        except SyntaxError as e:
            return [
                AnalysisResult(
                    level=AnalysisLevel.ERROR,
                    message="Syntax error in code",
                    line=e.lineno,
                    column=e.offset,
                    details={"error": str(e)},
                )
            ]

    def analyze_file(self, path: str) -> List[AnalysisResult]:
        """Analyze a source file.

        Args:
            path: Path to source file

        Returns:
            List of complexity issues found

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file can't be read
        """
        try:
            code = Path(path).read_text()
            return self.analyze(code)
        except (FileNotFoundError, PermissionError) as e:
            return [
                AnalysisResult(
                    level=AnalysisLevel.ERROR,
                    message=f"Failed to read file: {path}",
                    details={"error": str(e)},
                )
            ]

    def analyze_module(self, module: str) -> List[AnalysisResult]:
        """Analyze an imported module.

        Args:
            module: Fully qualified module name

        Returns:
            List of complexity issues found

        Raises:
            ImportError: If module can't be imported
        """
        try:
            spec = importlib.util.find_spec(module)
            if spec is None or spec.origin is None:
                return [
                    AnalysisResult(
                        level=AnalysisLevel.ERROR,
                        message=f"Module not found: {module}",
                        details={"module": module},
                    )
                ]
            return self.analyze_file(spec.origin)
        except ImportError as e:
            return [
                AnalysisResult(
                    level=AnalysisLevel.ERROR,
                    message=f"Failed to import module: {module}",
                    details={"error": str(e)},
                )
            ]
