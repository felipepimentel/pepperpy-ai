"""
PepperPy Tool Tasks.

Fluent API for tool task configuration.
"""

from pathlib import Path
from typing import Any

from pepperpy.agent.task import EnhancerProxy, TaskBase


class Tool(TaskBase):
    """Base tool configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize tool task.

        Args:
            name: Task name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self.enhance = EnhancerProxy(self)
        self._config["tool_type"] = "general"

    def description(self, text: str) -> "Tool":
        """Set the tool description.

        Args:
            text: Description text

        Returns:
            Self for method chaining
        """
        self._config["description"] = text
        return self

    def capability(self, capability_name: str) -> "Tool":
        """Add a capability to the tool.

        Args:
            capability_name: Capability name

        Returns:
            Self for method chaining
        """
        if "capabilities" not in self._config:
            self._config["capabilities"] = []
        if isinstance(self._config["capabilities"], list):
            self._config["capabilities"].append(capability_name)
        return self

    def capabilities(self, capability_list: list[str]) -> "Tool":
        """Set multiple capabilities for the tool.

        Args:
            capability_list: List of capabilities

        Returns:
            Self for method chaining
        """
        self._config["capabilities"] = capability_list
        return self

    def output(self, path: str | Path) -> "Tool":
        """Set the output path for results.

        Args:
            path: Output file path

        Returns:
            Self for method chaining
        """
        self.output_path = path
        return self


class APITool(Tool):
    """API tool configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize API tool task.

        Args:
            name: Task name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._config["tool_type"] = "api"
        self._config["base_url"] = None
        self._config["headers"] = {}
        self._config["auth_type"] = None

    def base_url(self, url: str) -> "APITool":
        """Set the base URL for the API.

        Args:
            url: Base URL

        Returns:
            Self for method chaining
        """
        self._config["base_url"] = url
        return self

    def header(self, key: str, value: str) -> "APITool":
        """Add a header to API requests.

        Args:
            key: Header key
            value: Header value

        Returns:
            Self for method chaining
        """
        if isinstance(self._config["headers"], dict):
            self._config["headers"][key] = value
        return self

    def headers(self, headers_dict: dict[str, str]) -> "APITool":
        """Set multiple headers for API requests.

        Args:
            headers_dict: Headers dictionary

        Returns:
            Self for method chaining
        """
        if isinstance(self._config["headers"], dict):
            self._config["headers"].update(headers_dict)
        return self

    def auth_type(self, auth_type: str) -> "APITool":
        """Set the authentication type.

        Args:
            auth_type: Authentication type (e.g., "basic", "token", "oauth")

        Returns:
            Self for method chaining
        """
        self._config["auth_type"] = auth_type
        return self

    def auth_credentials(self, credentials: dict[str, str]) -> "APITool":
        """Set authentication credentials.

        Args:
            credentials: Credentials dictionary

        Returns:
            Self for method chaining
        """
        self._config["auth_credentials"] = credentials
        return self

    def endpoint(self, path: str, method: str = "GET") -> "APITool":
        """Add an API endpoint.

        Args:
            path: Endpoint path
            method: HTTP method

        Returns:
            Self for method chaining
        """
        if "endpoints" not in self._config:
            self._config["endpoints"] = []
        if isinstance(self._config["endpoints"], list):
            self._config["endpoints"].append({"path": path, "method": method})
        return self


class GitTool(Tool):
    """Git tool configuration."""

    def __init__(self, name: str, pepper_instance: Any):
        """Initialize Git tool task.

        Args:
            name: Task name
            pepper_instance: PepperPy instance
        """
        super().__init__(name, pepper_instance)
        self._config["tool_type"] = "git"
        self._config["repo_url"] = None
        self._config["branch"] = "main"

    def repo_url(self, url: str) -> "GitTool":
        """Set the repository URL.

        Args:
            url: Repository URL

        Returns:
            Self for method chaining
        """
        self._config["repo_url"] = url
        return self

    def branch(self, branch_name: str) -> "GitTool":
        """Set the branch to use.

        Args:
            branch_name: Branch name

        Returns:
            Self for method chaining
        """
        self._config["branch"] = branch_name
        return self

    def clone_directory(self, directory: str | Path) -> "GitTool":
        """Set the directory to clone into.

        Args:
            directory: Clone directory

        Returns:
            Self for method chaining
        """
        self._config["clone_directory"] = str(directory)
        return self

    def auth_token(self, token: str) -> "GitTool":
        """Set the authentication token.

        Args:
            token: Auth token

        Returns:
            Self for method chaining
        """
        self._config["auth_token"] = token
        return self
