"""Code scanner module for static analysis.

This module provides static analysis capabilities to detect potential security issues
and code quality problems in Python code.
"""

import ast
import json
import logging
from typing import Any, Dict, List, Optional, Set, Union

from pepperpy.core.base import Lifecycle
from pepperpy.security.errors import SecurityError
from pepperpy.security.types import ValidationResult

logger = logging.getLogger(__name__)


class ScannerConfig:
    """Configuration for code scanner."""

    def __init__(
        self,
        banned_functions: Optional[Set[str]] = None,
        banned_modules: Optional[Set[str]] = None,
        max_complexity: int = 10,
    ):
        """Initialize scanner configuration.

        Args:
            banned_functions: Set of banned function names
            banned_modules: Set of banned module imports
            max_complexity: Maximum allowed cyclomatic complexity
        """
        self.banned_functions = banned_functions or {
            "eval",
            "exec",
            "compile",
            "__import__",
            "globals",
            "locals",
            "vars",
            "input",
        }
        self.banned_modules = banned_modules or {
            "subprocess",
            "os",
            "sys",
            "shutil",
            "pickle",
            "marshal",
        }
        self.max_complexity = max_complexity


class CodeVisitor(ast.NodeVisitor):
    """AST visitor for code analysis."""

    def __init__(self, config: ScannerConfig) -> None:
        """Initialize visitor.

        Args:
            config: Scanner configuration
        """
        self.config = config
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.complexity = 0

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call nodes.

        Args:
            node: AST call node
        """
        if isinstance(node.func, ast.Name):
            if node.func.id in self.config.banned_functions:
                self.issues.append(f"Use of banned function: {node.func.id}")
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import nodes.

        Args:
            node: AST import node
        """
        for name in node.names:
            if name.name in self.config.banned_modules:
                self.issues.append(f"Import of banned module: {name.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit import from nodes.

        Args:
            node: AST import from node
        """
        if node.module in self.config.banned_modules:
            self.issues.append(f"Import from banned module: {node.module}")
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition nodes.

        Args:
            node: AST function definition node
        """
        # Check function complexity
        self.complexity = 1  # Base complexity
        self.generic_visit(node)
        if self.complexity > self.config.max_complexity:
            self.warnings.append(
                f"Function {node.name} has high complexity: {self.complexity}"
            )

    def visit_If(self, node: ast.If) -> None:
        """Visit if nodes.

        Args:
            node: AST if node
        """
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        """Visit while nodes.

        Args:
            node: AST while node
        """
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """Visit for nodes.

        Args:
            node: AST for node
        """
        self.complexity += 1
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        """Visit try nodes.

        Args:
            node: AST try node
        """
        self.complexity += len(node.handlers)
        self.generic_visit(node)


class CodeScanner(Lifecycle):
    """Static code analyzer."""

    def __init__(self, config: Optional[ScannerConfig] = None) -> None:
        """Initialize scanner.

        Args:
            config: Optional scanner configuration
        """
        super().__init__()
        self.config = config or ScannerConfig()

    async def initialize(self) -> None:
        """Initialize scanner."""
        logger.info("Code scanner initialized")

    async def cleanup(self) -> None:
        """Clean up scanner resources."""
        logger.info("Code scanner cleaned up")

    async def scan(self, code: Union[str, Dict[str, Any]]) -> ValidationResult:
        """Scan code for security issues.

        Args:
            code: Code to scan, either as string or dict

        Returns:
            ValidationResult: Scan results with issues and warnings

        Raises:
            SecurityError: If scanning fails
        """
        try:
            # Convert dict to string if needed
            if isinstance(code, dict):
                code = json.dumps(code, indent=2)

            # Parse code into AST
            tree = ast.parse(code)

            # Analyze code
            visitor = CodeVisitor(self.config)
            visitor.visit(tree)

            # Create validation result
            result = ValidationResult(
                is_valid=len(visitor.issues) == 0,
                errors=visitor.issues,
                warnings=visitor.warnings,
            )

            return result

        except SyntaxError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Syntax error: {str(e)}"],
            )
        except Exception as e:
            raise SecurityError(f"Failed to scan code: {e}")

    def _check_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity.

        Args:
            node: AST node

        Returns:
            int: Cyclomatic complexity
        """
        visitor = CodeVisitor(self.config)
        visitor.visit(node)
        return visitor.complexity
