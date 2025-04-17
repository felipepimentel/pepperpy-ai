"""
PepperPy Repository Tool Base Module.

Base interfaces and abstractions for repository tools.
"""

from abc import abstractmethod
from typing import Any

from pepperpy.tool.base import BaseToolProvider, ToolProviderError


class RepositoryError(ToolProviderError):
    """Base error for repository operations."""

    pass


class RepositoryProvider(BaseToolProvider):
    """Base implementation for repository tool providers."""

    async def get_capabilities(self) -> list[str]:
        """Get the repository provider capabilities.

        Returns:
            List of capability strings
        """
        return [
            "clone",
            "get_files",
            "get_file_content",
            "get_repository",
            "list_repository_files",
            "read_repository_file",
            "get_commits",
        ]

    async def execute(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a repository command.

        Args:
            command: Command to execute
            **kwargs: Additional command-specific parameters

        Returns:
            Command result

        Raises:
            RepositoryError: If command execution fails
        """
        if not self.initialized:
            await self.initialize()

        try:
            if command == "clone":
                url = kwargs.get("url")
                branch = kwargs.get("branch")
                if not url:
                    raise RepositoryError("URL parameter is required for clone command")
                repo_path = await self.clone(url, branch)
                return {"success": True, "repo_path": repo_path}

            elif command == "get_files":
                path = kwargs.get("path")
                files = await self.get_files(path)
                return {"success": True, "files": files}

            elif command == "get_file_content":
                path = kwargs.get("path")
                if not path:
                    raise RepositoryError(
                        "Path parameter is required for get_file_content command"
                    )
                content = await self.get_file_content(path)
                return {"success": True, "content": content}

            elif command == "get_repository":
                repo_identifier = kwargs.get("repo_identifier")
                if not repo_identifier:
                    raise RepositoryError(
                        "Repository identifier is required for get_repository command"
                    )
                repo_data = await self.get_repository(repo_identifier)
                return {"success": True, "repository": repo_data}

            elif command == "list_repository_files":
                repo_identifier = kwargs.get("repo_identifier")
                path = kwargs.get("path")
                if not repo_identifier:
                    raise RepositoryError(
                        "Repository identifier is required for list_repository_files command"
                    )
                files = await self.list_repository_files(repo_identifier, path)
                return {"success": True, "files": files}

            elif command == "read_repository_file":
                repo_identifier = kwargs.get("repo_identifier")
                file_path = kwargs.get("file_path")
                if not repo_identifier or not file_path:
                    raise RepositoryError(
                        "Repository identifier and file path are required for read_repository_file command"
                    )
                content = await self.read_repository_file(repo_identifier, file_path)
                return {"success": True, "content": content}

            elif command == "get_commits":
                repo_identifier = kwargs.get("repo_identifier")
                limit = kwargs.get("limit")
                if not repo_identifier:
                    raise RepositoryError(
                        "Repository identifier is required for get_commits command"
                    )
                commits = await self.get_commits(repo_identifier, limit)
                return {"success": True, "commits": commits}

            else:
                raise RepositoryError(f"Unknown command: {command}")

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command,
                "parameters": kwargs,
            }

    @abstractmethod
    async def clone(self, url: str, branch: str | None = None) -> str:
        """Clone a repository.

        Args:
            url: Repository URL
            branch: Optional branch to clone

        Returns:
            Path to cloned repository

        Raises:
            RepositoryError: If cloning fails
        """
        raise NotImplementedError("clone not implemented")

    @abstractmethod
    async def get_files(self, path: str | None = None) -> list[str]:
        """Get list of files in repository.

        Args:
            path: Optional path to list files from

        Returns:
            List of file paths

        Raises:
            RepositoryError: If repository access fails
        """
        raise NotImplementedError("get_files not implemented")

    @abstractmethod
    async def get_file_content(self, path: str) -> str:
        """Get content of a file.

        Args:
            path: Path to file

        Returns:
            File content as string

        Raises:
            RepositoryError: If file access fails
        """
        raise NotImplementedError("get_file_content not implemented")

    @abstractmethod
    async def get_repository(self, repo_identifier: str) -> dict[str, Any]:
        """Get repository data by identifier.

        Args:
            repo_identifier: Repository identifier (e.g., "username/repo")

        Returns:
            Repository data dictionary

        Raises:
            RepositoryError: If repository cannot be accessed
        """
        raise NotImplementedError("get_repository not implemented")

    @abstractmethod
    async def list_repository_files(
        self, repo_identifier: str, path: str | None = None
    ) -> list[dict[str, Any]]:
        """Get file list from repository.

        Args:
            repo_identifier: Repository identifier
            path: Optional path within repository

        Returns:
            List of file metadata dictionaries

        Raises:
            RepositoryError: If files cannot be accessed
        """
        raise NotImplementedError("list_repository_files not implemented")

    @abstractmethod
    async def read_repository_file(self, repo_identifier: str, file_path: str) -> str:
        """Get content of a specific file.

        Args:
            repo_identifier: Repository identifier
            file_path: Path to file within repository

        Returns:
            File content as string

        Raises:
            RepositoryError: If file cannot be accessed
        """
        raise NotImplementedError("read_repository_file not implemented")

    @abstractmethod
    async def get_commits(
        self, repo_identifier: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Get commit history for repository.

        Args:
            repo_identifier: Repository identifier
            limit: Optional limit on number of commits to retrieve

        Returns:
            List of commit metadata dictionaries

        Raises:
            RepositoryError: If commits cannot be accessed
        """
        raise NotImplementedError("get_commits not implemented")
