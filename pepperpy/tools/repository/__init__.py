"""Repository analysis tools for PepperPy.

This module provides tools for analyzing code repositories from various sources,
including structure analysis, code quality assessment, and security scanning.

Example:
    >>> from pepperpy.tools.repository import RepositoryAnalyzer
    >>> from pepperpy.tools.repository.providers import GitHubProvider
    >>> analyzer = RepositoryAnalyzer(provider=GitHubProvider(token="your_token"))
    >>> report = await analyzer.analyze("username/repo")
    >>> report_path = analyzer.save_report(report)
"""

from pepperpy.tools.repository.analyzer import (
    AnalysisReport,
    CodeIssue,
    CodeQuality,
    IssueSeverity,
    RepositoryAnalyzer,
    RepoStructure,
    SecurityAlert,
)
from pepperpy.tools.repository.base import RepositoryError, RepositoryProvider
from pepperpy.tools.repository.providers.github import GitHubProvider

__all__ = [
    # Providers and Base
    "RepositoryProvider",
    "RepositoryError",
    # Core Components
    "RepositoryAnalyzer",
    # Data Models
    "AnalysisReport",
    "CodeIssue",
    "CodeQuality",
    "IssueSeverity",
    "RepoStructure",
    "SecurityAlert",
    "GitHubProvider",
]
