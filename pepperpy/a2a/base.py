"""
PepperPy A2A Protocol Module.

Base classes and interfaces for implementing Google's Agent2Agent protocol.
https://github.com/google/A2A
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pepperpy.core.base import PepperpyError
from pepperpy.core.logging import get_logger
from pepperpy.plugin import PepperpyPlugin

logger = get_logger(__name__)


class A2AError(PepperpyError):
    """Base exception for A2A errors."""

    pass


class TaskState(str, Enum):
    """Task states as defined in the A2A protocol."""

    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class PartType(str, Enum):
    """Part types as defined in the A2A protocol."""

    TEXT = "text"
    DATA = "data"
    FILE = "file"


class Part:
    """Base class for message parts in A2A protocol."""

    def __init__(self, part_type: PartType) -> None:
        """Initialize a message part.

        Args:
            part_type: Type of the message part
        """
        self.part_type = part_type

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the part
        """
        return {"type": self.part_type}


class TextPart(Part):
    """Text part in A2A protocol."""

    def __init__(self, text: str) -> None:
        """Initialize a text part.

        Args:
            text: Text content
        """
        super().__init__(PartType.TEXT)
        self.text = text

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the text part
        """
        result = super().to_dict()
        result["text"] = self.text
        return result


class DataPart(Part):
    """Data part (structured JSON) in A2A protocol."""

    def __init__(
        self, data: dict[str, Any], mime_type: str = "application/json"
    ) -> None:
        """Initialize a data part.

        Args:
            data: JSON-serializable data
            mime_type: MIME type of the data
        """
        super().__init__(PartType.DATA)
        self.data = data
        self.mime_type = mime_type

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the data part
        """
        result = super().to_dict()
        result["data"] = self.data
        result["mime_type"] = self.mime_type
        return result


class FilePart(Part):
    """File part in A2A protocol."""

    def __init__(
        self,
        file_id: str,
        name: str,
        mime_type: str,
        bytes_base64: str | None = None,
        uri: str | None = None,
    ) -> None:
        """Initialize a file part.

        Args:
            file_id: Unique identifier for the file
            name: File name
            mime_type: MIME type of the file
            bytes_base64: Optional base64-encoded file content
            uri: Optional URI to the file
        """
        super().__init__(PartType.FILE)
        self.file_id = file_id
        self.name = name
        self.mime_type = mime_type
        self.bytes_base64 = bytes_base64
        self.uri = uri

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the file part
        """
        result = super().to_dict()
        result["file_id"] = self.file_id
        result["name"] = self.name
        result["mime_type"] = self.mime_type

        if self.bytes_base64:
            result["bytes_base64"] = self.bytes_base64

        if self.uri:
            result["uri"] = self.uri

        return result


class Message:
    """Message in A2A protocol."""

    def __init__(
        self, 
        role: str, 
        parts: list[Part],
        function_call: dict[str, Any] | None = None
    ) -> None:
        """Initialize a message.

        Args:
            role: Role of the message sender (user/agent)
            parts: List of message parts
            function_call: Optional function call data for function calling
        """
        self.role = role
        self.parts = parts
        self.function_call = function_call

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the message
        """
        result: dict[str, Any] = {
            "role": self.role,
            "parts": [part.to_dict() for part in self.parts],
        }

        # Add function call data if present
        if self.function_call is not None:
            result["function_call"] = self.function_call

        return result


class Artifact:
    """Artifact in A2A protocol."""

    def __init__(self, artifact_id: str, artifact_type: str, parts: list[Part]) -> None:
        """Initialize an artifact.

        Args:
            artifact_id: Unique identifier for the artifact
            artifact_type: Type of the artifact
            parts: List of artifact parts
        """
        self.artifact_id = artifact_id
        self.artifact_type = artifact_type
        self.parts = parts

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the artifact
        """
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "parts": [part.to_dict() for part in self.parts],
        }


class Task:
    """Task in A2A protocol."""

    def __init__(
        self,
        task_id: str,
        state: TaskState,
        messages: list[Message],
        artifacts: list[Artifact] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a task.

        Args:
            task_id: Unique identifier for the task
            state: Current state of the task
            messages: List of messages in the task
            artifacts: Optional list of artifacts generated during the task
            metadata: Optional metadata about the task
        """
        self.task_id = task_id
        self.state = state
        self.messages = messages
        self.artifacts = artifacts or []
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the task
        """
        return {
            "task_id": self.task_id,
            "state": self.state,
            "messages": [message.to_dict() for message in self.messages],
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "metadata": self.metadata,
        }


class AgentCard:
    """Agent Card in A2A protocol."""

    def __init__(
        self,
        name: str,
        description: str,
        endpoint: str,
        capabilities: list[str],
        skills: list[dict[str, Any]] | None = None,
        authentication: dict[str, Any] | None = None,
        version: str = "1.0.0",
    ) -> None:
        """Initialize an agent card.

        Args:
            name: Name of the agent
            description: Description of the agent
            endpoint: HTTP endpoint URL
            capabilities: List of capabilities
            skills: Optional list of skill descriptions
            authentication: Optional authentication requirements
            version: Version of the agent card
        """
        self.name = name
        self.description = description
        self.endpoint = endpoint
        self.capabilities = capabilities
        self.skills = skills or []
        self.authentication = authentication or {}
        self.version = version

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the agent card
        """
        return {
            "name": self.name,
            "description": self.description,
            "endpoint": self.endpoint,
            "capabilities": self.capabilities,
            "skills": self.skills,
            "authentication": self.authentication,
            "version": self.version,
        }


class A2AProvider(PepperpyPlugin, ABC):
    """Base class for A2A protocol providers."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize A2A provider.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__()
        self.config = config or {}
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize A2A provider resources."""
        if self.initialized:
            return
        await self._initialize_resources()
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up A2A provider resources."""
        if not self.initialized:
            return
        await self._cleanup_resources()
        self.initialized = False

    @abstractmethod
    async def _initialize_resources(self) -> None:
        """Initialize resources for the A2A provider."""
        pass

    @abstractmethod
    async def _cleanup_resources(self) -> None:
        """Clean up resources for the A2A provider."""
        pass

    @abstractmethod
    async def create_task(self, agent_id: str, message: Message) -> Task:
        """Create a new task.

        Args:
            agent_id: Target agent ID
            message: Initial message

        Returns:
            Created task
        """
        pass

    @abstractmethod
    async def get_task(self, task_id: str) -> Task:
        """Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task information
        """
        pass

    @abstractmethod
    async def update_task(self, task_id: str, message: Message) -> Task:
        """Update a task with a new message.

        Args:
            task_id: Task ID
            message: New message to add

        Returns:
            Updated task
        """
        pass
