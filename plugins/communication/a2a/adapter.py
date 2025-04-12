"""
A2A Protocol Adapter.

This module adapts the Google A2A protocol to the PepperPy communication interface.
"""

from collections.abc import AsyncGenerator
from typing import Any

from pepperpy.a2a import (
    A2AProvider,
    TaskState,
)
from pepperpy.a2a import (
    DataPart as A2ADataPart,
)
from pepperpy.a2a import (
    FilePart as A2AFilePart,
)
from pepperpy.a2a import Message as A2AMessage
from pepperpy.a2a import (
    TextPart as A2ATextPart,
)
from pepperpy.a2a import create_provider as create_a2a_provider
from pepperpy.communication import (
    BaseCommunicationProvider,
    CommunicationError,
    CommunicationProtocol,
    DataPart,
    FilePart,
    Message,
    TextPart,
)
from pepperpy.core.logging import get_logger
from pepperpy.plugin.plugin import ProviderPlugin

logger = get_logger(__name__)


class A2ACommunicationAdapter(BaseCommunicationProvider, ProviderPlugin):
    """Adapter for A2A protocol.

    This adapter bridges the A2A protocol to the PepperPy communication interface,
    allowing A2A providers to be used as communication providers.
    """

    def __init__(self, **config: Any) -> None:
        """Initialize A2A adapter.

        Args:
            **config: Configuration options including:
                - provider_type: The A2A provider type to use (default, rest, mock)
                - Additional config options passed to the A2A provider
        """
        super().__init__(**config)
        self.provider: A2AProvider | None = None
        self.tasks: dict[str, Any] = {}
        self.a2a_provider_type = self.config.get("provider_type", "default")

    @property
    def protocol_type(self) -> CommunicationProtocol:
        """Get the protocol type.

        Returns:
            Communication protocol type
        """
        return CommunicationProtocol.A2A

    async def _initialize_resources(self) -> None:
        """Initialize A2A provider."""
        try:
            # Create the A2A provider
            self.provider = await create_a2a_provider(
                self.a2a_provider_type, **self.config
            )

            logger.info(
                f"Initialized A2A adapter with provider: {self.a2a_provider_type}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize A2A adapter: {e}")
            raise CommunicationError(f"Failed to initialize A2A adapter: {e}") from e

    async def _cleanup_resources(self) -> None:
        """Clean up A2A provider resources."""
        if self.provider:
            await self.provider.cleanup()
            self.provider = None
            self.tasks = {}
            logger.info("Cleaned up A2A adapter")

    def _convert_to_a2a_message(self, message: Message) -> A2AMessage:
        """Convert communication message to A2A message.

        Args:
            message: Communication message

        Returns:
            A2A message
        """
        a2a_parts = []

        # Convert text parts
        for text_part in message.get_text_parts():
            a2a_parts.append(A2ATextPart(text_part.text))

        # Convert data parts
        for data_part in message.get_data_parts():
            a2a_parts.append(A2ADataPart(data_part.data))

        # Convert file parts
        for file_part in message.get_file_parts():
            a2a_parts.append(
                A2AFilePart(
                    file_id=file_part.path,
                    name=file_part.path.split("/")[-1],
                    mime_type=file_part.mime_type or "application/octet-stream",
                )
            )

        # If no parts, create a default text part
        if not a2a_parts:
            a2a_parts.append(A2ATextPart("No content"))

        # Extract function call data from metadata if present
        function_call = message.metadata.get("a2a_function_call")

        return A2AMessage(
            role=message.sender or "user", parts=a2a_parts, function_call=function_call
        )

    def _convert_from_a2a_message(self, a2a_message: A2AMessage) -> Message:
        """Convert A2A message to communication message.

        Args:
            a2a_message: A2A message

        Returns:
            Communication message
        """
        comm_message = Message(sender=a2a_message.role)

        # Convert A2A parts to communication parts
        for a2a_part in a2a_message.parts:
            if isinstance(a2a_part, A2ATextPart):
                comm_message.add_part(TextPart(a2a_part.text, role=a2a_message.role))
            elif isinstance(a2a_part, A2ADataPart):
                comm_message.add_part(DataPart(a2a_part.data, format_="json"))
            elif isinstance(a2a_part, A2AFilePart):
                comm_message.add_part(
                    FilePart(path=a2a_part.file_id, mime_type=a2a_part.mime_type)
                )

        # Add function call to metadata if present
        if a2a_message.function_call:
            comm_message.metadata["a2a_function_call"] = a2a_message.function_call

        return comm_message

    async def send_message(self, message: Message) -> str:
        """Send a message.

        Args:
            message: Message to send

        Returns:
            Task ID

        Raises:
            CommunicationError: If message sending fails
        """
        if not self._initialized:
            await self.initialize()

        if not self.provider:
            raise CommunicationError("A2A provider not initialized")

        if not message.receiver:
            raise CommunicationError("Message must have a receiver")

        try:
            # Convert message to A2A format
            a2a_message = self._convert_to_a2a_message(message)

            # Create task with the A2A provider
            task = await self.provider.create_task(message.receiver, a2a_message)

            # Store task for later reference
            self.tasks[task.task_id] = task

            return task.task_id
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise CommunicationError(f"Failed to send message: {e}") from e

    async def receive_message(self, task_id: str) -> Message:
        """Receive a message by task ID.

        Args:
            task_id: Task ID

        Returns:
            Received message

        Raises:
            CommunicationError: If message retrieval fails
        """
        if not self._initialized:
            await self.initialize()

        if not self.provider:
            raise CommunicationError("A2A provider not initialized")

        try:
            # Get the task from the A2A provider
            task = await self.provider.get_task(task_id)

            # Update our local copy
            self.tasks[task_id] = task

            # If task is completed, return last message from agent
            if task.state == TaskState.COMPLETED and task.messages:
                # Find the last message from the agent
                for a2a_message in reversed(task.messages):
                    if a2a_message.role != "user":
                        return self._convert_from_a2a_message(a2a_message)

            # If no agent message found or task not completed
            raise CommunicationError(
                f"No response message available for task {task_id}"
            )
        except Exception as e:
            logger.error(f"Failed to receive message: {e}")
            raise CommunicationError(f"Failed to receive message: {e}") from e

    async def stream_messages(
        self, filter_criteria: dict[str, Any] | None = None
    ) -> AsyncGenerator[Message, None]:
        """Stream messages based on filter criteria.

        Args:
            filter_criteria: Optional filtering criteria

        Yields:
            Messages matching the criteria

        Raises:
            CommunicationError: If streaming fails
        """
        if not self._initialized:
            await self.initialize()

        if not self.provider:
            raise CommunicationError("A2A provider not initialized")

        try:
            # A2A doesn't have a native streaming mechanism,
            # so we implement polling for known tasks

            # Get task IDs from filter or use all known tasks
            task_ids = (
                filter_criteria.get("task_ids", list(self.tasks.keys()))
                if filter_criteria
                else list(self.tasks.keys())
            )

            for task_id in task_ids:
                # Get fresh task data
                task = await self.provider.get_task(task_id)

                # Update our cache
                self.tasks[task_id] = task

                # Convert all messages in the task
                for a2a_message in task.messages:
                    yield self._convert_from_a2a_message(a2a_message)
        except Exception as e:
            logger.error(f"Failed to stream messages: {e}")
            raise CommunicationError(f"Failed to stream messages: {e}") from e
