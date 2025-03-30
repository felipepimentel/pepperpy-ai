"""Code quality analysis tools for the refactoring system."""

import ast
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set

import flake8.api.legacy as flake8

from .context import RefactoringContext

logger = logging.getLogger(__name__)


@dataclass
class StyleIssue:
    """Represents a style issue found in code."""

    line: int
    column: int
    message: str
    code: str


@dataclass
class DocIssue:
    """Represents a documentation issue."""

    node: ast.AST
    message: str
    type: str  # "missing" | "incomplete" | "example"


class StyleChecker:
    """Check code style against project standards."""

    def __init__(self, context: RefactoringContext):
        self.context = context
        self._style_guide = flake8.get_style_guide(
            max_line_length=88,  # Match black
            ignore=["E203", "W503"],  # Black-compatible
        )

    def check_style(self, content: str) -> List[StyleIssue]:
        """Run style checks using flake8.

        Args:
            content: Source code to check

        Returns:
            List of style issues found
        """
        try:
            # Create a temporary file for flake8
            temp_file = Path(self.context.workspace_root) / "_temp_style_check.py"
            temp_file.write_text(content)

            # Run flake8
            report = self._style_guide.check_files([str(temp_file)])

            # Convert to StyleIssues
            issues = [
                StyleIssue(
                    line=int(error[0]),
                    column=int(error[1]),
                    message=error[2],
                    code=error[3]
                )
                for error in report.get_statistics("")
            ]

            # Clean up
            temp_file.unlink()

            return issues
        except Exception as e:
            self.context.logger.error(f"Failed to check style: {e}")
            return []


class DocAnalyzer:
    """Analyze documentation completeness."""

    def __init__(self, context: RefactoringContext):
        self.context = context
        self._required_sections = {"Args", "Returns", "Raises", "Examples"}

    def check_documentation(self, tree: ast.AST) -> List[DocIssue]:
        """Check docstring coverage and quality.

        Args:
            tree: AST to analyze

        Returns:
            List of documentation issues found
        """
        try:
            issues = []
            issues.extend(self._find_missing_docs(tree))
            issues.extend(self._find_incomplete_docs(tree))
            issues.extend(self._check_example_coverage(tree))
            return issues
        except Exception as e:
            self.context.logger.error(f"Failed to check documentation: {e}")
            return []

    def _find_missing_docs(self, tree: ast.AST) -> List[DocIssue]:
        """Find nodes missing docstrings."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                if not ast.get_docstring(node):
                    issues.append(
                        DocIssue(
                            node=node,
                            message=f"Missing docstring for {self._get_node_name(node)}",
                            type="missing",
                        )
                    )

        return issues

    def _find_incomplete_docs(self, tree: ast.AST) -> List[DocIssue]:
        """Find incomplete docstrings."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                if docstring:
                    # Check for required sections
                    missing_sections = self._check_required_sections(docstring, node)
                    if missing_sections:
                        issues.append(
                            DocIssue(
                                node=node,
                                message=(
                                    f"Incomplete docstring for {self._get_node_name(node)}: "
                                    f"missing {', '.join(missing_sections)}"
                                ),
                                type="incomplete",
                            )
                        )

        return issues

    def _check_example_coverage(self, tree: ast.AST) -> List[DocIssue]:
        """Check for missing examples in docstrings."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                if docstring and not self._has_example(docstring):
                    issues.append(
                        DocIssue(
                            node=node,
                            message=f"No example in docstring for {self._get_node_name(node)}",
                            type="example",
                        )
                    )

        return issues

    def _check_required_sections(self, docstring: str, node: ast.AST) -> Set[str]:
        """Check which required sections are missing."""
        if not isinstance(node, ast.FunctionDef):
            return set()  # Only check functions

        sections = set()
        lines = docstring.split("\n")

        for line in lines:
            line = line.strip()
            for section in self._required_sections:
                if line.startswith(f"{section}:"):
                    sections.add(section)

        # Only require Args if function has parameters
        required = set(self._required_sections)
        if not self._has_parameters(node):
            required.remove("Args")

        # Only require Returns if function returns something
        if not self._has_return(node):
            required.remove("Returns")

        # Only require Raises if function has error handling
        if not self._has_error_handling(node):
            required.remove("Raises")

        return required - sections

    def _has_example(self, docstring: str) -> bool:
        """Check if docstring has an example section."""
        return "Examples:" in docstring or "Example:" in docstring

    def _has_parameters(self, node: ast.FunctionDef) -> bool:
        """Check if function has parameters."""
        return bool(node.args.args)

    def _has_return(self, node: ast.FunctionDef) -> bool:
        """Check if function has return statement."""
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value is not None:
                return True
        return False

    def _has_error_handling(self, node: ast.FunctionDef) -> bool:
        """Check if function has try/except blocks."""
        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                return True
        return False

    def _get_node_name(self, node: ast.AST) -> str:
        """Get descriptive name for node."""
        if isinstance(node, ast.Module):
            return "module"
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            return node.name
        return "unknown"


class SecurityChecker:
    """Check for security issues."""

    def __init__(self, context: RefactoringContext):
        self.context = context

    def check_security(self, content: str) -> List[str]:
        """Run security checks using bandit.

        Args:
            content: Source code to check

        Returns:
            List of security issues found
        """
        try:
            from bandit.core import manager

            # Create a temporary file for bandit
            temp_file = Path(self.context.workspace_root) / "_temp_security_check.py"
            temp_file.write_text(content)

            # Configure bandit
            b_mgr = manager.BanditManager(
                config_file=None, agg_type="file", debug=False, verbose=False
            )

            # Run the scan
            b_mgr.discover_files([str(temp_file)])
            b_mgr.run_tests()

            # Extract issues
            issues = []
            for issue in b_mgr.get_issue_list():
                issues.append(f"[{issue.severity}] {issue.test_id}: {issue.text}")

            # Clean up
            temp_file.unlink()

            return issues
        except Exception as e:
            self.context.logger.error(f"Failed to check security: {e}")
            return []
