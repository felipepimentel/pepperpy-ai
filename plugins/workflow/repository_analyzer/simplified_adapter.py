"""
Simplified adapter for repository analyzer workflow.

This module demonstrates how to use the simplified workflow base class
with the plugin system.
"""

import logging
import os
from typing import Any

from pepperpy.workflow.simplified import SimpleWorkflow, workflow_task


class RepositoryAnalyzerSimple(SimpleWorkflow):
    """Simplified repository analyzer workflow.

    This workflow provides repository analysis functionality with minimal boilerplate.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the workflow.

        Args:
            **kwargs: Configuration options
        """
        # Initialize the SimpleWorkflow with required name and description
        super().__init__(
            name="repository_analyzer",
            description="Analyze code repositories and provide insights",
        )

        # Store other config parameters
        self.config = kwargs

        # Configuration with defaults
        self.repository_path = self.config.get("repository_path", ".")
        self.include_patterns = self.config.get("include_patterns", ["**/*.py"])
        self.exclude_patterns = self.config.get(
            "exclude_patterns",
            ["**/node_modules/**", "**/__pycache__/**", "**/.git/**"],
        )
        self.max_files = self.config.get("max_files", 1000)

        # State
        self.git_repo = None

    async def initialize(self) -> None:
        """Initialize the workflow."""
        if self.initialized:
            return

        # Validate repository path
        from pathlib import Path

        repo_path = Path(self.repository_path).resolve()
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        self.repo_path = repo_path

        # Try to initialize git repository
        try:
            import git

            try:
                self.git_repo = git.Repo(repo_path)
                print(f"Initialized Git repository at {repo_path}")
            except (git.InvalidGitRepositoryError, git.NoSuchPathError):
                print(f"Not a Git repository: {repo_path}")
                self.git_repo = None
        except ImportError:
            print("GitPython not installed, Git functionality disabled")

        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        self.git_repo = None
        self.initialized = False
        print("Cleaned up repository analyzer resources")

    @workflow_task()
    async def analyze_repository(self, **kwargs: Any) -> dict[str, Any]:
        """Analyze entire repository.

        Returns:
            Complete repository analysis
        """
        # Get list of files
        files = self._get_repository_files()

        # Basic structure analysis
        structure = self._analyze_structure(files)

        # Git repository analysis if available
        git_info = self._get_git_info() if self.git_repo else None

        return {
            "status": "success",
            "total_files": len(files),
            "structure": structure,
            "git_info": git_info,
        }

    @workflow_task()
    async def analyze_structure(self, **kwargs: Any) -> dict[str, Any]:
        """Analyze repository structure.

        Returns:
            Repository structure analysis
        """
        # Get list of files
        files = self._get_repository_files()

        # Basic structure analysis
        structure = self._analyze_structure(files)

        return {"status": "success", "total_files": len(files), "structure": structure}

    @workflow_task()
    async def analyze_code_quality(self, **kwargs: Any) -> dict[str, Any]:
        """Analyze code quality.

        Returns:
            Code quality analysis
        """
        # Get list of files
        files = self._get_repository_files()

        # Filter Python files
        python_files = [f for f in files if f.endswith(".py")]

        if not python_files:
            return {
                "status": "warning",
                "message": "No Python files found for analysis",
            }

        # Simple code analysis
        import os

        analysis = {}
        total_lines = 0
        for file_path in python_files:
            try:
                with open(os.path.join(self.repo_path, file_path)) as f:
                    content = f.readlines()
                    lines = len(content)
                    empty_lines = sum(1 for line in content if not line.strip())
                    comment_lines = sum(
                        1 for line in content if line.strip().startswith("#")
                    )

                    total_lines += lines

                    analysis[file_path] = {
                        "lines": lines,
                        "empty_lines": empty_lines,
                        "comment_lines": comment_lines,
                        "code_lines": lines - empty_lines - comment_lines,
                    }
            except Exception as e:
                analysis[file_path] = {"error": str(e)}

        return {
            "status": "success",
            "analyzed_files": len(python_files),
            "total_lines": total_lines,
            "file_analysis": analysis,
        }

    @workflow_task()
    async def analyze_complexity(self, **kwargs: Any) -> dict[str, Any]:
        """Analyze code complexity.

        Returns:
            Code complexity analysis
        """
        # Get list of files
        files = self._get_repository_files()

        # Filter Python files
        python_files = [f for f in files if f.endswith(".py")]

        if not python_files:
            return {
                "status": "warning",
                "message": "No Python files found for analysis",
            }

        # Simple complexity metrics
        import os
        import re

        analysis = {}
        for file_path in python_files:
            try:
                with open(os.path.join(self.repo_path, file_path)) as f:
                    content = f.read()

                    # Count function definitions
                    functions = re.findall(r"def\s+\w+\s*\(", content)

                    # Count class definitions
                    classes = re.findall(r"class\s+\w+\s*[\(:]", content)

                    # Count import statements
                    imports = re.findall(r"^\s*(import|from)\s+", content, re.MULTILINE)

                    # Simple cyclomatic complexity (if/for/while statements)
                    conditionals = re.findall(
                        r"^\s*(if|for|while)\s+", content, re.MULTILINE
                    )

                    analysis[file_path] = {
                        "functions": len(functions),
                        "classes": len(classes),
                        "imports": len(imports),
                        "conditionals": len(conditionals),
                        "complexity_score": len(functions)
                        + len(classes)
                        + len(conditionals),
                    }
            except Exception as e:
                analysis[file_path] = {"error": str(e)}

        return {
            "status": "success",
            "analyzed_files": len(python_files),
            "complexity_analysis": analysis,
        }

    @workflow_task()
    async def count_files(
        self, topic: str = "file count", **kwargs: Any
    ) -> dict[str, Any]:
        """Count files in the repository by extension.

        Args:
            topic: The topic of the analysis
            **kwargs: Additional arguments

        Returns:
            Dict with file counts by extension
        """
        logging.info(f"Starting repository file count analysis: {topic}")

        # Get the files
        files = self._get_repository_files()

        # Count by extension
        extensions_count = {}
        for file in files:
            ext = os.path.splitext(file)[1] or "no_extension"
            extensions_count[ext] = extensions_count.get(ext, 0) + 1

        # Sort by count (descending)
        sorted_extensions = sorted(
            extensions_count.items(), key=lambda x: x[1], reverse=True
        )

        return {
            "status": "success",
            "total_files": len(files),
            "extensions": extensions_count,
            "top_extensions": sorted_extensions[:10],  # Top 10 extensions
        }

    def _get_repository_files(self) -> list[str]:
        """Get files from repository based on include/exclude patterns.

        Returns:
            List of file paths relative to repository root
        """
        import glob
        import os

        files = []

        for pattern in self.include_patterns:
            matched_files = glob.glob(str(self.repo_path / pattern), recursive=True)
            files.extend(matched_files)

        # Convert to relative paths
        files = [os.path.relpath(f, self.repo_path) for f in files]

        # Apply exclude patterns
        for pattern in self.exclude_patterns:
            # Convert glob pattern to regex
            exclude_matches = glob.glob(str(self.repo_path / pattern), recursive=True)
            exclude_files = [
                os.path.relpath(f, self.repo_path) for f in exclude_matches
            ]
            files = [f for f in files if f not in exclude_files]

        # Limit number of files
        files = files[: self.max_files]

        return files

    def _analyze_structure(self, files: list[str]) -> dict[str, Any]:
        """Analyze repository structure.

        Args:
            files: List of files

        Returns:
            Structure analysis
        """
        import os

        # Count files by directory
        dirs = {}
        for file_path in files:
            directory = os.path.dirname(file_path) or "."
            dirs[directory] = dirs.get(directory, 0) + 1

        # Count files by extension
        extensions = {}
        for file_path in files:
            _, ext = os.path.splitext(file_path)
            if ext:
                extensions[ext] = extensions.get(ext, 0) + 1

        # Get top directories and extensions
        top_dirs = sorted(dirs.items(), key=lambda x: x[1], reverse=True)[:10]
        top_exts = sorted(extensions.items(), key=lambda x: x[1], reverse=True)

        # Build directory tree
        tree = {}
        for file_path in files:
            parts = file_path.split(os.sep)
            current = tree
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # File
                    current.setdefault("files", []).append(part)
                else:  # Directory
                    current = current.setdefault("dirs", {}).setdefault(part, {})

        return {
            "directories": dirs,
            "top_directories": top_dirs,
            "extensions": extensions,
            "top_extensions": top_exts,
            "tree": tree,
        }

    def _get_git_info(self) -> dict[str, Any]:
        """Get Git repository information.

        Returns:
            Git repository information
        """
        if not self.git_repo:
            return {}

        try:
            # Get basic info
            try:
                active_branch = self.git_repo.active_branch.name
            except Exception:
                active_branch = "DETACHED_HEAD"

            # Get commit count
            commit_count = len(list(self.git_repo.iter_commits()))

            # Get last commit
            last_commit = self.git_repo.head.commit
            last_commit_info = {
                "hash": last_commit.hexsha,
                "author": f"{last_commit.author.name} <{last_commit.author.email}>",
                "date": last_commit.committed_datetime.isoformat(),
                "message": last_commit.message.strip(),
            }

            return {
                "active_branch": active_branch,
                "commit_count": commit_count,
                "last_commit": last_commit_info,
            }
        except Exception as e:
            return {"error": str(e)}


class SimpleRepositoryAnalyzerAdapter:
    """Adapter for simplified repository analyzer workflow.

    This adapter connects the simplified workflow to the plugin system.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the adapter.

        Args:
            **kwargs: Configuration options
        """
        self.workflow = RepositoryAnalyzerSimple(**kwargs)
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the workflow."""
        if not self.initialized:
            await self.workflow.initialize()
            self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.initialized:
            await self.workflow.cleanup()
            self.initialized = False

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a task in the workflow.

        Args:
            input_data: Dictionary with task name and parameters

        Returns:
            Task execution results
        """
        if not self.initialized:
            await self.initialize()

        # Add topic to satisfy ContentGeneratorWorkflow validation
        input_data["topic"] = "repository analysis"

        return await self.workflow.execute(input_data)


# Export the adapter for plugin discovery
__all__ = ["SimpleRepositoryAnalyzerAdapter"]
