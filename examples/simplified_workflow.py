#!/usr/bin/env python3
"""
Example of using the simplified workflow API.

This example demonstrates how to create a simple repository analyzer workflow
with minimal boilerplate code using the new SimpleWorkflow base class.
"""

import asyncio
import os
from pathlib import Path
from typing import Any

from pepperpy.workflow.simplified import SimpleWorkflow, workflow_task


class RepositoryAnalyzerSimple(SimpleWorkflow):
    """Simplified repository analyzer workflow.

    This workflow analyzes code repositories with minimal boilerplate code.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the workflow.

        Args:
            **kwargs: Configuration options
        """
        super().__init__(**kwargs)

        # Configuration with defaults
        self.repository_path = self.config.get("repository_path", ".")
        self.include_patterns = self.config.get(
            "include_patterns", ["**/*.py", "**/*.js", "**/*.md"]
        )
        self.exclude_patterns = self.config.get(
            "exclude_patterns",
            ["**/node_modules/**", "**/__pycache__/**", "**/.git/**"],
        )

    async def initialize(self) -> None:
        """Initialize the workflow."""
        if self.initialized:
            return

        # Simple initialization
        self.repo_path = Path(self.repository_path).resolve()
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {self.repo_path}")

        # Initialize git repo if available
        try:
            import git

            try:
                self.git_repo = git.Repo(self.repo_path)
                print(f"Initialized Git repository at {self.repo_path}")
            except (git.InvalidGitRepositoryError, git.NoSuchPathError):
                print(f"Not a Git repository: {self.repo_path}")
                self.git_repo = None
        except ImportError:
            self.git_repo = None
            print("GitPython not installed, Git functionality disabled")

        self.initialized = True

    @workflow_task()
    async def analyze_structure(self, **kwargs) -> dict[str, Any]:
        """Analyze repository structure.

        Returns:
            Repository structure analysis
        """
        # Get list of files
        files = self._get_files()

        # Get directory structure
        structure = self._analyze_directory_structure(files)

        # Get Git info if available
        git_info = self._get_git_info() if self.git_repo else None

        # Prepare result
        return {
            "status": "success",
            "total_files": len(files),
            "structure": structure,
            "git_info": git_info,
        }

    @workflow_task()
    async def analyze_code(
        self, file_types: list[str] | None = None, **kwargs
    ) -> dict[str, Any]:
        """Analyze code files in the repository.

        Args:
            file_types: Optional list of file extensions to include

        Returns:
            Code analysis results
        """
        file_types = file_types or [".py", ".js", ".ts", ".java", ".c", ".cpp"]

        # Get files of specified types
        files = [
            f for f in self._get_files() if any(f.endswith(ext) for ext in file_types)
        ]

        # Analyze code (simple metrics for demonstration)
        file_analysis = {}
        total_lines = 0
        for file_path in files:
            try:
                with open(os.path.join(self.repo_path, file_path)) as f:
                    content = f.readlines()
                    lines = len(content)
                    total_lines += lines
                    file_analysis[file_path] = {
                        "lines": lines,
                        "size": os.path.getsize(
                            os.path.join(self.repo_path, file_path)
                        ),
                    }
            except Exception as e:
                file_analysis[file_path] = {"error": str(e)}

        return {
            "status": "success",
            "analyzed_files": len(files),
            "total_lines": total_lines,
            "file_types": file_types,
            "file_analysis": file_analysis,
        }

    @workflow_task(name="find_docs", description="Find documentation files")
    async def find_documentation(self, **kwargs) -> dict[str, Any]:
        """Find documentation files in the repository.

        Returns:
            List of documentation files
        """
        doc_patterns = [
            "**/*.md",
            "**/*.rst",
            "**/docs/**",
            "**/documentation/**",
            "**/*.ipynb",
        ]

        doc_files = []
        for pattern in doc_patterns:
            import glob

            matches = glob.glob(str(self.repo_path / pattern), recursive=True)
            for match in matches:
                doc_files.append(os.path.relpath(match, self.repo_path))

        return {
            "status": "success",
            "doc_files": doc_files,
            "doc_count": len(doc_files),
        }

    def _get_files(self) -> list[str]:
        """Get all files in the repository.

        Returns:
            List of file paths relative to repository root
        """
        import glob

        files = []
        for pattern in self.include_patterns:
            matches = glob.glob(str(self.repo_path / pattern), recursive=True)
            files.extend([os.path.relpath(f, self.repo_path) for f in matches])

        # Apply exclude patterns
        for pattern in self.exclude_patterns:
            exclude_matches = glob.glob(str(self.repo_path / pattern), recursive=True)
            exclude_files = [
                os.path.relpath(f, self.repo_path) for f in exclude_matches
            ]
            files = [f for f in files if f not in exclude_files]

        return files

    def _analyze_directory_structure(self, files: list[str]) -> dict[str, Any]:
        """Analyze directory structure.

        Args:
            files: List of file paths

        Returns:
            Directory structure analysis
        """
        dirs = {}
        extensions = {}

        for file_path in files:
            # Get directory
            directory = os.path.dirname(file_path)
            dirs[directory] = dirs.get(directory, 0) + 1

            # Get extension
            _, ext = os.path.splitext(file_path)
            if ext:
                extensions[ext] = extensions.get(ext, 0) + 1

        # Get top directories
        top_dirs = sorted(dirs.items(), key=lambda x: x[1], reverse=True)[:10]

        # Get top extensions
        top_exts = sorted(extensions.items(), key=lambda x: x[1], reverse=True)

        return {
            "directories": dirs,
            "top_directories": top_dirs,
            "extensions": extensions,
            "top_extensions": top_exts,
        }

    def _get_git_info(self) -> dict[str, Any]:
        """Get Git repository information.

        Returns:
            Git repository information
        """
        if not self.git_repo:
            return None

        try:
            # Get basic info
            active_branch = self.git_repo.active_branch.name
        except Exception:
            active_branch = "DETACHED_HEAD"

        try:
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
            return {"active_branch": active_branch, "error": str(e)}


async def main():
    """Run the example."""
    # Path to analyze (current directory by default)
    repo_path = "."

    print(f"Analyzing repository: {repo_path}")

    # Create workflow
    workflow = RepositoryAnalyzerSimple(repository_path=repo_path)

    # Using async context manager for auto cleanup
    async with workflow:
        # Get available tasks
        tasks = workflow.get_available_tasks()
        print("Available tasks:")
        for task in tasks:
            print(f"- {task['name']}: {task['description']}")

        print("\nRunning analyze_structure task...")
        structure_result = await workflow.execute({"task": "analyze_structure"})
        print(f"Total files: {structure_result.get('total_files')}")
        print(
            f"Top file types: {structure_result.get('structure', {}).get('top_extensions')}"
        )

        print("\nRunning analyze_code task...")
        code_result = await workflow.execute({
            "task": "analyze_code",
            "file_types": [".py"],
        })
        print(f"Python files: {code_result.get('analyzed_files')}")
        print(f"Total lines: {code_result.get('total_lines')}")

        print("\nRunning find_docs task...")
        docs_result = await workflow.execute({"task": "find_docs"})
        print(f"Documentation files: {docs_result.get('doc_count')}")

    print("\nWorkflow completed")


if __name__ == "__main__":
    asyncio.run(main())
