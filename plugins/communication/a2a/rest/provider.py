"""A2A REST protocol provider implementation."""

import uuid
from typing import Any

import aiohttp
from aiohttp import ClientSession

from pepperpy.a2a.base import (
    A2AError,
    A2AProvider,
    AgentCard,
    Artifact,
    Task,
    TaskState,
)
from pepperpy.a2a.base import (
    DataPart as A2ADataPart,
)
from pepperpy.a2a.base import (
    FilePart as A2AFilePart,
)
from pepperpy.a2a.base import (
    Message as A2AMessage,
)
from pepperpy.a2a.base import (
    TextPart as A2ATextPart,
)
from pepperpy.core.logging import get_logger
from pepperpy.plugin.plugin import ProviderPlugin

logger = get_logger(__name__)


class A2ARestProvider(A2AProvider, ProviderPlugin):
    """A2A REST protocol provider implementation.

    This provider implements the Google A2A protocol over REST APIs.
    It communicates with a REST endpoint that speaks the A2A protocol.
    """

    def __init__(self, **config: Any) -> None:
        """Initialize the provider.

        Args:
            **config: Provider configuration
        """
        super().__init__(config or {})
        self.base_url = config.get("base_url", "http://localhost:8080/a2a")
        self.api_key = config.get("api_key", "")
        self.timeout = int(config.get("timeout", 30))
        self.headers = config.get("headers", {})
        self.session: ClientSession | None = None

    async def _initialize_resources(self) -> None:
        """Initialize provider resources."""
        headers = {"Content-Type": "application/json", **self.headers}

        # Add API key if provided
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.session = aiohttp.ClientSession(headers=headers)
        logger.debug(f"Initialized A2A REST provider with base URL: {self.base_url}")

    async def _cleanup_resources(self) -> None:
        """Clean up provider resources."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.debug("Cleaned up A2A REST provider resources")

    async def create_task(self, agent_id: str, message: A2AMessage) -> Task:
        """Create a new task.

        Args:
            agent_id: Target agent ID
            message: Initial message

        Returns:
            Created task

        Raises:
            A2AError: If task creation fails
        """
        if not self.session:
            raise A2AError("Provider not initialized")

        task_id = str(uuid.uuid4())
        payload = {
            "task_id": task_id,
            "agent_id": agent_id,
            "state": TaskState.SUBMITTED.value,
            "messages": [message.to_dict()],
        }

        try:
            async with self.session.post(
                f"{self.base_url}/tasks", json=payload, timeout=self.timeout
            ) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise A2AError(f"Failed to create task: {error_text}")

                data = await response.json()
                return self._dict_to_task(data)
        except aiohttp.ClientError as e:
            raise A2AError(f"HTTP error creating task: {e}") from e
        except Exception as e:
            raise A2AError(f"Error creating task: {e}") from e

    async def get_task(self, task_id: str) -> Task:
        """Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task information

        Raises:
            A2AError: If getting task fails
        """
        if not self.session:
            raise A2AError("Provider not initialized")

        try:
            async with self.session.get(
                f"{self.base_url}/tasks/{task_id}", timeout=self.timeout
            ) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise A2AError(f"Failed to get task: {error_text}")

                data = await response.json()
                return self._dict_to_task(data)
        except aiohttp.ClientError as e:
            raise A2AError(f"HTTP error getting task: {e}") from e
        except Exception as e:
            raise A2AError(f"Error getting task: {e}") from e

    async def update_task(self, task_id: str, message: A2AMessage) -> Task:
        """Update task with a new message.

        Args:
            task_id: Task ID
            message: New message

        Returns:
            Updated task

        Raises:
            A2AError: If updating task fails
        """
        if not self.session:
            raise A2AError("Provider not initialized")

        payload = {"message": message.to_dict()}

        try:
            async with self.session.patch(
                f"{self.base_url}/tasks/{task_id}", json=payload, timeout=self.timeout
            ) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise A2AError(f"Failed to update task: {error_text}")

                data = await response.json()
                return self._dict_to_task(data)
        except aiohttp.ClientError as e:
            raise A2AError(f"HTTP error updating task: {e}") from e
        except Exception as e:
            raise A2AError(f"Error updating task: {e}") from e

    async def get_agent_card(self, agent_id: str) -> AgentCard:
        """Get agent card by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Agent card

        Raises:
            A2AError: If getting agent card fails
        """
        if not self.session:
            raise A2AError("Provider not initialized")

        try:
            async with self.session.get(
                f"{self.base_url}/agents/{agent_id}", timeout=self.timeout
            ) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise A2AError(f"Failed to get agent card: {error_text}")

                data = await response.json()
                return AgentCard(
                    name=data.get("name", ""),
                    description=data.get("description", ""),
                    endpoint=data.get("endpoint", ""),
                    capabilities=data.get("capabilities", []),
                    skills=data.get("skills", []),
                    authentication=data.get("authentication", {}),
                    version=data.get("version", "1.0.0"),
                )
        except aiohttp.ClientError as e:
            raise A2AError(f"HTTP error getting agent card: {e}") from e
        except Exception as e:
            raise A2AError(f"Error getting agent card: {e}") from e

    def _dict_to_task(self, data: dict[str, Any]) -> Task:
        """Convert dictionary to Task.

        Args:
            data: Task data dictionary

        Returns:
            Task object
        """
        # Parse task state
        state_str = data.get("state", "")
        state = TaskState(state_str) if state_str else TaskState.SUBMITTED

        # Parse messages
        messages = []
        for msg_data in data.get("messages", []):
            messages.append(self._dict_to_message(msg_data))

        # Parse artifacts
        artifacts = []
        for artifact_data in data.get("artifacts", []):
            artifacts.append(self._dict_to_artifact(artifact_data))

        return Task(
            task_id=data.get("task_id", ""),
            state=state,
            messages=messages,
            artifacts=artifacts,
            metadata=data.get("metadata", {}),
        )

    def _dict_to_message(self, data: dict[str, Any]) -> A2AMessage:
        """Convert dictionary to Message.

        Args:
            data: Message data dictionary

        Returns:
            Message object
        """
        parts = []
        for part_data in data.get("parts", []):
            part_type = part_data.get("type", "")

            if part_type == "text":
                parts.append(A2ATextPart(part_data.get("text", "")))
            elif part_type == "data":
                parts.append(
                    A2ADataPart(
                        data=part_data.get("data", {}),
                        mime_type=part_data.get("mime_type", "application/json"),
                    )
                )
            elif part_type == "file":
                parts.append(
                    A2AFilePart(
                        file_id=part_data.get("file_id", ""),
                        name=part_data.get("name", ""),
                        mime_type=part_data.get(
                            "mime_type", "application/octet-stream"
                        ),
                        bytes_base64=part_data.get("bytes_base64"),
                        uri=part_data.get("uri"),
                    )
                )

        return A2AMessage(
            role=data.get("role", "user"),
            parts=parts,
            function_call=data.get("function_call"),
        )

    def _dict_to_artifact(self, data: dict[str, Any]) -> Artifact:
        """Convert dictionary to Artifact.

        Args:
            data: Artifact data dictionary

        Returns:
            Artifact object
        """
        parts = []
        for part_data in data.get("parts", []):
            part_type = part_data.get("type", "")

            if part_type == "text":
                parts.append(A2ATextPart(part_data.get("text", "")))
            elif part_type == "data":
                parts.append(
                    A2ADataPart(
                        data=part_data.get("data", {}),
                        mime_type=part_data.get("mime_type", "application/json"),
                    )
                )
            elif part_type == "file":
                parts.append(
                    A2AFilePart(
                        file_id=part_data.get("file_id", ""),
                        name=part_data.get("name", ""),
                        mime_type=part_data.get(
                            "mime_type", "application/octet-stream"
                        ),
                        bytes_base64=part_data.get("bytes_base64"),
                        uri=part_data.get("uri"),
                    )
                )

        return Artifact(
            artifact_id=data.get("artifact_id", ""),
            artifact_type=data.get("artifact_type", ""),
            parts=parts,
        )
