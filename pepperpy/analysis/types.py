"""Core types for the code analysis system.

This module provides the fundamental types and interfaces for code analysis,
including enums for analysis levels, result containers, and base classes
for analyzers and visitors.
"""

import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class AnalysisLevel(str, Enum):
    """Analysis severity levels.

    Attributes:
        ERROR: Critical issues that must be fixed
        WARNING: Potential problems that should be reviewed
        INFO: Informational findings
    """

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class AnalysisResult:
    """Container for code analysis results.

    Attributes:
        level: Severity level of the finding
        message: Description of the finding
        node: AST node where the issue was found
        line: Line number in source code
        column: Column number in source code
        details: Additional context about the finding

    Example:
        >>> result = AnalysisResult(
        ...     level=AnalysisLevel.WARNING,
        ...     message="Complex function detected",
        ...     line=10,
        ...     details={"complexity": 15}
        ... )
    """

    level: AnalysisLevel
    message: str
    node: Optional[ast.AST] = None
    line: Optional[int] = None
    column: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


class CodeAnalyzer(ABC):
    """Base class for code analyzers.

    All code analyzers must inherit from this class and implement
    its abstract methods.

    Example:
        >>> class SecurityAnalyzer(CodeAnalyzer):
        ...     def analyze(self, code: str) -> List[AnalysisResult]:
        ...         # Implementation
        ...         pass
    """

    @abstractmethod
    def analyze(self, code: str) -> List[AnalysisResult]:
        """Analyze source code string.

        Args:
            code: Source code to analyze

        Returns:
            List of analysis results

        Raises:
            SyntaxError: If code is invalid Python
        """
        pass

    @abstractmethod
    def analyze_file(self, path: str) -> List[AnalysisResult]:
        """Analyze a source file.

        Args:
            path: Path to source file

        Returns:
            List of analysis results

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file can't be read
            SyntaxError: If file contains invalid Python
        """
        pass

    @abstractmethod
    def analyze_module(self, module: str) -> List[AnalysisResult]:
        """Analyze an imported module.

        Args:
            module: Fully qualified module name

        Returns:
            List of analysis results

        Raises:
            ImportError: If module can't be imported
            SyntaxError: If module contains invalid Python
        """
        pass


class BaseVisitor(ast.NodeVisitor):
    """Base class for AST visitors used in analysis.

    Provides common functionality for collecting analysis results
    while traversing the AST.

    Example:
        >>> class SecurityVisitor(BaseVisitor):
        ...     def visit_Call(self, node: ast.Call) -> None:
        ...         if isinstance(node.func, ast.Name):
        ...             if node.func.id == "eval":
        ...                 self.add_result(
        ...                     level=AnalysisLevel.ERROR,
        ...                     message="Use of eval() detected",
        ...                     node=node
        ...                 )
    """

    def __init__(self) -> None:
        """Initialize visitor."""
        super().__init__()
        self.results: List[AnalysisResult] = []

    def add_result(
        self,
        level: AnalysisLevel,
        message: str,
        node: ast.AST,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add an analysis result.

        Args:
            level: Severity level
            message: Finding description
            node: AST node where issue was found
            details: Additional context
        """
        self.results.append(
            AnalysisResult(
                level=level,
                message=message,
                node=node,
                line=getattr(node, "lineno", None),
                column=getattr(node, "col_offset", None),
                details=details,
            )
        )
