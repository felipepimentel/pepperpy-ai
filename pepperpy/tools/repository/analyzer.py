"""Repository analysis tool for PepperPy.

This module provides functionality for analyzing code repositories,
including structure analysis, code quality assessment, and security scanning.
"""

import asyncio
import json
import logging
import os
import sys
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Set

from pepperpy.core import PepperpyError
from pepperpy.core.logging import VerbosityLevel
from pepperpy.tools.base import ToolError
from pepperpy.tools.repository.base import RepositoryProvider


# Error classes for repository analysis
class AnalysisError(ToolError):
    """Base error for repository analysis operations."""
    pass


class FileSystemError(AnalysisError):
    """Error related to file system operations."""
    pass


class ParsingError(AnalysisError):
    """Error related to parsing repository data."""
    pass


# Data models for repository analysis
class IssueSeverity(str, Enum):
    """Severity levels for code issues."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


@dataclass
class CodeIssue:
    """Represents a code issue found during analysis."""
    file: str
    line: int
    message: str
    severity: IssueSeverity
    code: Optional[str] = None


@dataclass
class RepoStructure:
    """Repository structure information."""
    
    name: str
    files_count: int
    directories: Dict[str, Dict[str, Any]]
    languages: Dict[str, float]
    entry_points: List[str] = field(default_factory=list)
    test_directories: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SecurityAlert:
    """Security vulnerability information."""
    
    level: str
    component: str
    description: str
    cve: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CodeQuality:
    """Code quality metrics."""
    
    maintainability_index: float
    cyclomatic_complexity: float
    code_duplication: float
    test_coverage: float
    documentation_coverage: float
    issues: Dict[str, List[Dict[str, Any]]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AnalysisReport:
    """Complete repository analysis report."""
    
    repository_name: str
    repository_url: str
    structure: RepoStructure
    code_quality: CodeQuality
    recommendations: List[str]
    security_alerts: List[SecurityAlert]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary format."""
        return {
            "repository": {
                "name": self.repository_name,
                "url": self.repository_url
            },
            "timestamp": self.timestamp.isoformat(),
            "structure": self.structure.to_dict(),
            "code_quality": self.code_quality.to_dict(),
            "recommendations": self.recommendations,
            "security_alerts": [alert.to_dict() for alert in self.security_alerts]
        }


class FileSystemManager:
    """Handles file system operations for repository analysis."""
    
    def __init__(self):
        """Initialize FileSystemManager."""
        self.logger = logging.getLogger("pepperpy.tools.repository.fs")
    
    def ensure_directory(self, directory: Union[str, Path]) -> Path:
        """Ensure a directory exists.
        
        Args:
            directory: Directory path
            
        Returns:
            Path object for the directory
            
        Raises:
            FileSystemError: If directory creation fails
        """
        directory = Path(directory)
        try:
            directory.mkdir(parents=True, exist_ok=True)
            return directory
        except Exception as e:
            error_msg = f"Failed to create directory {directory}: {e}"
            self.logger.error(error_msg)
            raise FileSystemError(error_msg)


# Mapping from VerbosityLevel to logging level
LEVEL_MAP = {
    VerbosityLevel.SILENT: logging.CRITICAL,
    VerbosityLevel.ERROR: logging.ERROR,
    VerbosityLevel.INFO: logging.INFO,
    VerbosityLevel.DEBUG: logging.DEBUG,
    VerbosityLevel.VERBOSE: logging.DEBUG  # Python doesn't have a more verbose level
}


class RepositoryAnalyzer:
    """AI-powered repository analysis tool."""

    DEFAULT_OUTPUT_DIR = Path("output/repo_analysis")

    def __init__(
        self,
        provider: Optional[RepositoryProvider] = None,
        output_dir: Optional[Union[str, Path]] = None,
        verbosity: Union[int, VerbosityLevel] = VerbosityLevel.INFO,
        **kwargs: Any
    ) -> None:
        """Initialize the repository analyzer.
        
        Args:
            provider: Repository provider to use for analysis
            output_dir: Directory to save output files. If None, uses default directory.
            verbosity: Verbosity level for analysis operations.
            **kwargs: Additional configuration options.
        """
        # Setup logger
        self.logger = logging.getLogger("pepperpy.tools.repository")
        
        # Convert verbosity to standard logging level
        if isinstance(verbosity, VerbosityLevel):
            if verbosity == VerbosityLevel.SILENT:
                level = logging.CRITICAL
            elif verbosity == VerbosityLevel.ERROR:
                level = logging.ERROR
            elif verbosity == VerbosityLevel.INFO:
                level = logging.INFO
            elif verbosity == VerbosityLevel.DEBUG:
                level = logging.DEBUG
            elif verbosity == VerbosityLevel.VERBOSE:
                level = logging.DEBUG
            else:
                level = logging.INFO
        elif isinstance(verbosity, int):
            if verbosity == 0:  # SILENT
                level = logging.CRITICAL
            elif verbosity == 1:  # ERROR
                level = logging.ERROR
            elif verbosity == 2:  # INFO
                level = logging.INFO
            elif verbosity >= 3:  # DEBUG or VERBOSE
                level = logging.DEBUG
            else:
                level = logging.INFO
        else:
            level = logging.INFO
            
        # Configure console handler if not already present
        if not self.logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
            self.logger.addHandler(console_handler)
            
        self.logger.setLevel(level)
        
        # Store repository provider
        self.provider = provider
        
        # Setup file system manager
        self.fs_manager = FileSystemManager()
        
        # Setup output directory (created automatically)
        self.output_dir = Path(output_dir) if output_dir else self.DEFAULT_OUTPUT_DIR
        self.fs_manager.ensure_directory(self.output_dir)
        
        # Store current analysis state
        self.current_repo: Dict[str, Any] = {}
        self.structure: Optional[RepoStructure] = None
        self.code_quality: Optional[CodeQuality] = None
        
        # Additional configuration
        self.config = kwargs
    
    def capabilities(self) -> Set[str]:
        """Return the capabilities supported by this tool.
        
        Returns:
            Set of capability strings
        """
        capabilities = {
            "repository_analysis",
            "code_quality_assessment",
            "security_scanning",
            "structure_analysis"
        }
        
        # Add provider-specific capabilities if provider is available
        if self.provider:
            capabilities.update(self.provider.capabilities())
            
        return capabilities
    
    async def load_repo_data(self, repo_path: Union[str, Path]) -> Dict[str, Any]:
        """Load repository data from file.
        
        Args:
            repo_path: Path to repository data file
            
        Returns:
            Repository data dictionary
            
        Raises:
            ParsingError: If loading or parsing fails
        """
        repo_data_path = Path(repo_path)
        
        try:
            self.logger.info(f"Loading repository data from {repo_data_path}")
            if repo_data_path.exists():
                with open(repo_data_path, "r") as f:
                    return json.load(f)
            else:
                error_msg = f"Repository data file not found at {repo_data_path}"
                self.logger.error(error_msg)
                raise FileNotFoundError(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in {repo_data_path}: {e}"
            self.logger.error(error_msg)
            raise ParsingError(error_msg)
        except Exception as e:
            error_msg = f"Failed to load repository data: {e}"
            self.logger.error(error_msg)
            raise ParsingError(error_msg)
    
    async def analyze_structure(self, data: Dict[str, Any]) -> RepoStructure:
        """Analyze repository structure from data.
        
        Args:
            data: Repository data
            
        Returns:
            Repository structure
        """
        self.logger.info("Analyzing repository structure...")
        repo = data.get("repository", {})
        
        # Extract structure information from data
        # In a real implementation, this would analyze actual repository files
        return RepoStructure(
            name=repo.get("name", "unknown"),
            files_count=repo.get("files_count", 0),
            directories=repo.get("directories", {}),
            languages=repo.get("languages", {}),
            entry_points=repo.get("entry_points", []),
            test_directories=repo.get("test_directories", [])
        )
    
    async def analyze_code_quality(self, data: Dict[str, Any]) -> CodeQuality:
        """Analyze code quality from data.
        
        Args:
            data: Repository data
            
        Returns:
            Code quality metrics
        """
        self.logger.info("Analyzing code quality...")
        quality_data = data.get("code_quality", {})
        
        # Extract code quality metrics from data
        # In a real implementation, this would calculate metrics from code
        return CodeQuality(
            maintainability_index=quality_data.get("maintainability_index", 0.0),
            cyclomatic_complexity=quality_data.get("cyclomatic_complexity", 0.0),
            code_duplication=quality_data.get("code_duplication", 0.0),
            test_coverage=quality_data.get("test_coverage", 0.0),
            documentation_coverage=quality_data.get("documentation_coverage", 0.0),
            issues=quality_data.get("issues", {})
        )
    
    async def generate_recommendations(self, structure: RepoStructure, quality: CodeQuality) -> List[str]:
        """Generate recommendations based on analysis.
        
        Args:
            structure: Repository structure
            quality: Code quality metrics
            
        Returns:
            List of recommendations
        """
        self.logger.info("Generating recommendations...")
        recommendations = []
        
        # In a real implementation, this would generate tailored recommendations
        # based on structure and quality
        if quality.test_coverage < 80:
            recommendations.append("Increase test coverage for core modules")
            
        if quality.documentation_coverage < 70:
            recommendations.append("Add documentation for public APIs")
            
        if quality.code_duplication > 5:
            recommendations.append("Reduce code duplication by extracting common utilities")
            
        if "critical" in quality.issues and quality.issues["critical"]:
            recommendations.append("Fix critical issues to improve security and reliability")
            
        return recommendations
    
    async def analyze(self, repo_identifier: Union[str, Path, Dict[str, Any]]) -> AnalysisReport:
        """Analyze a repository and generate a comprehensive report.
        
        Args:
            repo_identifier: Repository identifier or data
                - If string, treated as repository identifier for provider
                - If Path, treated as path to local repository data file
                - If dict, treated as repository data dictionary
            
        Returns:
            Complete repository analysis report
            
        Raises:
            AnalysisError: If analysis fails
        """
        try:
            # Check if provider is available for repository identifiers
            if isinstance(repo_identifier, str) and self.provider is None:
                raise AnalysisError("Repository provider is required for repository identifier analysis")
            
            # Load repository data based on input type
            if isinstance(repo_identifier, str) and self.provider:
                # Get repository data from provider
                await self.provider.connect()
                self.current_repo = await self.provider.get_repository(repo_identifier)
            elif isinstance(repo_identifier, Path) or isinstance(repo_identifier, str):
                # Load from file
                self.current_repo = await self.load_repo_data(repo_identifier)
            else:
                # Use provided dictionary
                self.current_repo = repo_identifier
                
            repo = self.current_repo.get("repository", {})
            
            # Analyze repository structure
            self.structure = await self.analyze_structure(self.current_repo)
            
            # Analyze code quality
            self.code_quality = await self.analyze_code_quality(self.current_repo)
            
            # Generate recommendations
            recommendations = await self.generate_recommendations(self.structure, self.code_quality)
            
            # Extract security alerts
            security_data = self.current_repo.get("security", {}).get("alerts", [])
            security_alerts = [
                SecurityAlert(
                    level=alert.get("level", "medium"),
                    component=alert.get("component", "unknown"),
                    description=alert.get("description", "Unknown vulnerability"),
                    cve=alert.get("cve")
                )
                for alert in security_data
            ]
            
            # Create the full report
            return AnalysisReport(
                repository_name=repo.get("name", "unknown"),
                repository_url=repo.get("url", "unknown"),
                structure=self.structure,
                code_quality=self.code_quality,
                recommendations=recommendations,
                security_alerts=security_alerts
            )
            
        except Exception as e:
            error_msg = f"Failed to analyze repository: {e}"
            self.logger.error(error_msg)
            raise AnalysisError(error_msg)
        finally:
            # Disconnect from provider if connected
            if isinstance(repo_identifier, str) and self.provider:
                await self.provider.disconnect()
    
    def save_report(self, report: AnalysisReport, file_path: Optional[Union[str, Path]] = None) -> str:
        """Save analysis report to a file.
        
        Args:
            report: Repository analysis report
            file_path: Optional file path. If None, a path is generated based on the repository name.
            
        Returns:
            Path where the report was saved
            
        Raises:
            AnalysisError: If saving fails
        """
        try:
            # Generate path if not provided
            if file_path is None:
                file_path = self.output_dir / f"{report.repository_name.lower().replace(' ', '_')}_analysis.json"
            else:
                file_path = Path(file_path)
                # Ensure parent directories exist
                self.fs_manager.ensure_directory(file_path.parent)
            
            # Convert report to dictionary
            report_dict = report.to_dict()
            
            # Save to file
            with open(file_path, "w") as f:
                json.dump(report_dict, f, indent=2)
            
            self.logger.info(f"Analysis report saved to {file_path}")
            return str(file_path)
            
        except Exception as e:
            error_msg = f"Failed to save report: {e}"
            self.logger.error(error_msg)
            raise AnalysisError(error_msg) 