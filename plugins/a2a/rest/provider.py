"""
REST implementation of the A2A protocol provider.

This provider enables agent-to-agent communication through a RESTful API
following Google's A2A protocol specification.
"""

import asyncio
import json
from typing import Any

import aiohttp
from aiohttp import ClientError, ClientSession

from pepperpy.a2a.base import (
    A2AError,
    A2AProvider,
    AgentCard,
    Artifact,
    DataPart,
    FilePart,
    Message,
    Task,
    TaskState,
    TextPart,
)
from pepperpy.core.logging import get_logger
from pepperpy.plugin import ProviderPlugin

logger = get_logger(__name__)


class RestA2AError(A2AError):
    """Exceptions related to REST A2A provider."""

    pass


class RestA2AProvider(A2AProvider, ProviderPlugin):
    """REST implementation of the A2A protocol provider.

    This provider implements the A2A protocol using RESTful API calls.
    """

    # Config attributes with type annotations
    base_url: str
    timeout: int = 30
    verify_ssl: bool = True
    max_retries: int = 3
    retry_delay: int = 1
    auth: dict[str, Any] = {}

    def __init__(self, **config: Any) -> None:
        """Initialize the REST A2A provider.

        Args:
            **config: Provider configuration
        """
        super().__init__(config)
        self.session: ClientSession | None = None
        self._agent_card: AgentCard | None = None

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if the key is not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def has_config(self, key: str) -> bool:
        """Check if a configuration key exists.

        Args:
            key: Configuration key

        Returns:
            True if the key exists, False otherwise
        """
        return key in self.config

    def update_config(self, **kwargs: Any) -> None:
        """Update the configuration.

        Args:
            **kwargs: Configuration values to update
        """
        self.config.update(kwargs)

    async def _initialize_resources(self) -> None:
        """Initialize provider resources.

        Creates HTTP session and registers agent if needed.
        """
        if not self.base_url:
            raise RestA2AError("base_url is required")

        # Create HTTP session
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={"Content-Type": "application/json"},
        )

        # Set up authentication if configured
        if self.auth.get("type") != "none":
            await self._setup_authentication()

        logger.debug(f"Initialized REST A2A provider with base URL: {self.base_url}")

    async def _cleanup_resources(self) -> None:
        """Clean up provider resources.

        Closes the HTTP session.
        """
        if self.session:
            await self.session.close()
            self.session = None
        logger.debug("Cleaned up REST A2A provider resources")

    async def _setup_authentication(self) -> None:
        """Set up authentication for the HTTP session."""
        if not self.session:
            raise RestA2AError("Session not initialized")

        auth_type = self.auth.get("type")
        auth_headers = {}

        if auth_type == "basic":
            username = self.auth.get("username")
            password = self.auth.get("password")
            if not username or not password:
                raise RestA2AError(
                    "Username and password required for basic authentication"
                )

            # aiohttp handles basic auth through auth parameter in request
            # We'll set it up during actual requests

        elif auth_type == "bearer":
            token = self.auth.get("token")
            if not token:
                raise RestA2AError("Token required for bearer authentication")
            auth_headers["Authorization"] = f"Bearer {token}"

        elif auth_type == "oauth2":
            # For OAuth2, we would typically fetch a token first
            client_id = self.auth.get("client_id")
            client_secret = self.auth.get("client_secret")
            token_url = self.auth.get("token_url")

            if not client_id or not client_secret or not token_url:
                raise RestA2AError(
                    "Client ID, client secret, and token URL required for OAuth2"
                )

            # This is a simplified version - we should implement proper token fetching
            # and refreshing for production use
            token = await self._get_oauth2_token()
            auth_headers["Authorization"] = f"Bearer {token}"

        # Update session headers with auth headers
        self.session.headers.update(auth_headers)

    async def _get_oauth2_token(self) -> str:
        """Get OAuth2 token.

        Returns:
            OAuth2 token

        Raises:
            RestA2AError: If token acquisition fails
            NotImplementedError: OAuth2 token acquisition is currently not implemented
        """
        # This is a placeholder - implement actual OAuth2 token acquisition
        raise NotImplementedError("OAuth2 token acquisition not implemented")
        # Return dummy value to satisfy type checker, but this code is unreachable
        return ""

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a request to the A2A API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request data
            params: Query parameters

        Returns:
            Response data

        Raises:
            RestA2AError: If the request fails
        """
        if not self.session:
            raise RestA2AError("Provider not initialized")

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        auth = None

        # Set up basic auth if configured
        if self.auth.get("type") == "basic":
            auth = aiohttp.BasicAuth(
                login=self.auth.get("username", ""),
                password=self.auth.get("password", ""),
            )

        for attempt in range(self.max_retries + 1):
            try:
                async with getattr(self.session, method.lower())(
                    url, json=data, params=params, auth=auth, ssl=self.verify_ssl
                ) as response:
                    response_data = await response.json()

                    if response.status < 200 or response.status >= 300:
                        error_msg = response_data.get("error", {}).get(
                            "message", "Unknown error"
                        )
                        raise RestA2AError(
                            f"API error: {error_msg} (status {response.status})"
                        )

                    return response_data
            except (ClientError, json.JSONDecodeError) as e:
                if attempt < self.max_retries:
                    logger.warning(
                        f"Request failed, retrying ({attempt + 1}/{self.max_retries}): {e!s}"
                    )
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise RestA2AError(
                        f"Request failed after {self.max_retries} retries: {e!s}"
                    ) from e
        
        # This line should never be reached because the loop above will either return
        # a response or raise an exception, but we add it to satisfy the type checker
        raise RestA2AError("Unexpected error in request handling")

    async def register_agent(self, agent_card: AgentCard) -> None:
        """Register an agent with the A2A service.

        Args:
            agent_card: Agent card with agent information

        Raises:
            RestA2AError: If registration fails
        """
        try:
            data = agent_card.to_dict()
            await self._make_request("POST", "agents", data=data)
            self._agent_card = agent_card
            logger.info(f"Agent '{agent_card.name}' registered successfully")
        except Exception as e:
            raise RestA2AError(f"Failed to register agent: {e!s}") from e

    async def create_task(self, agent_id: str, initial_message: Message) -> Task:
        """Create a new task with the specified agent.

        Args:
            agent_id: ID of the agent to create a task with
            initial_message: Initial message for the task

        Returns:
            Created task

        Raises:
            RestA2AError: If task creation fails
        """
        try:
            data = {
                "agent_id": agent_id,
                "messages": [initial_message.to_dict()],
            }

            response = await self._make_request("POST", "tasks", data=data)

            # Create Task object from response
            return self._create_task_from_response(response)
        except Exception as e:
            raise RestA2AError(f"Failed to create task: {e!s}") from e

    async def get_task(self, task_id: str) -> Task:
        """Get a task by ID.

        Args:
            task_id: ID of the task to get

        Returns:
            Task object

        Raises:
            RestA2AError: If task retrieval fails
        """
        try:
            response = await self._make_request("GET", f"tasks/{task_id}")
            return self._create_task_from_response(response)
        except Exception as e:
            raise RestA2AError(f"Failed to get task {task_id}: {e!s}") from e

    async def update_task(self, task_id: str, message: Message) -> Task:
        """Update a task with a new message.

        Args:
            task_id: ID of the task to update
            message: New message to add to the task

        Returns:
            Updated task

        Raises:
            RestA2AError: If task update fails
        """
        try:
            data = {
                "message": message.to_dict(),
            }

            response = await self._make_request(
                "POST", f"tasks/{task_id}/messages", data=data
            )
            return self._create_task_from_response(response)
        except Exception as e:
            raise RestA2AError(f"Failed to update task {task_id}: {e!s}") from e

    async def cancel_task(self, task_id: str) -> Task:
        """Cancel a task.

        Args:
            task_id: ID of the task to cancel

        Returns:
            Canceled task

        Raises:
            RestA2AError: If task cancellation fails
        """
        try:
            response = await self._make_request("POST", f"tasks/{task_id}/cancel")
            return self._create_task_from_response(response)
        except Exception as e:
            raise RestA2AError(f"Failed to cancel task {task_id}: {e!s}") from e

    def _create_task_from_response(self, response: dict[str, Any]) -> Task:
        """Create a Task object from API response.

        Args:
            response: API response data

        Returns:
            Task object
        """
        # Parse messages
        messages = []
        for msg_data in response.get("messages", []):
            parts = []
            for part_data in msg_data.get("parts", []):
                part_type = part_data.get("type")

                if part_type == "text":
                    parts.append(TextPart(part_data.get("text", "")))
                elif part_type == "data":
                    parts.append(
                        DataPart(
                            part_data.get("data", {}),
                            part_data.get("mime_type", "application/json"),
                        )
                    )
                elif part_type == "file":
                    parts.append(
                        FilePart(
                            part_data.get("file_id", ""),
                            part_data.get("name", ""),
                            part_data.get("mime_type", ""),
                            part_data.get("bytes_base64"),
                            part_data.get("uri"),
                        )
                    )

            messages.append(Message(msg_data.get("role", ""), parts))

        # Parse artifacts
        artifacts = []
        for artifact_data in response.get("artifacts", []):
            artifact_parts = []
            for part_data in artifact_data.get("parts", []):
                part_type = part_data.get("type")

                if part_type == "text":
                    artifact_parts.append(TextPart(part_data.get("text", "")))
                elif part_type == "data":
                    artifact_parts.append(
                        DataPart(
                            part_data.get("data", {}),
                            part_data.get("mime_type", "application/json"),
                        )
                    )
                elif part_type == "file":
                    artifact_parts.append(
                        FilePart(
                            part_data.get("file_id", ""),
                            part_data.get("name", ""),
                            part_data.get("mime_type", ""),
                            part_data.get("bytes_base64"),
                            part_data.get("uri"),
                        )
                    )

            artifacts.append(
                Artifact(
                    artifact_data.get("artifact_id", ""),
                    artifact_data.get("artifact_type", ""),
                    artifact_parts,
                )
            )

        # Create Task object
        return Task(
            response.get("task_id", ""),
            TaskState(response.get("state", "submitted")),
            messages,
            artifacts,
            response.get("metadata", {}),
        )

    async def list_agents(self) -> list[AgentCard]:
        """List available agents.

        Returns:
            List of agent cards

        Raises:
            RestA2AError: If agent listing fails
        """
        try:
            response = await self._make_request("GET", "agents")

            agents = []
            for agent_data in response.get("agents", []):
                agent = AgentCard(
                    agent_data.get("name", ""),
                    agent_data.get("description", ""),
                    agent_data.get("endpoint", ""),
                    agent_data.get("capabilities", []),
                    agent_data.get("skills", []),
                    agent_data.get("authentication", {}),
                    agent_data.get("version", "1.0.0"),
                )
                agents.append(agent)

            return agents
        except Exception as e:
            raise RestA2AError(f"Failed to list agents: {e!s}") from e
