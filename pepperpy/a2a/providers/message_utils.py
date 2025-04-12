"""
Message utilities for A2A protocol.

This module provides helper functions for creating and working with
A2A protocol messages and parts.
"""

import base64
import json
import uuid
from typing import Any

from pepperpy.a2a.base import (
    DataPart,
    FilePart,
    Message,
    Part,
    Task,
    TaskState,
    TextPart,
)
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)


def create_text_message(role: str, text: str) -> Message:
    """Create a simple text message.

    Args:
        role: Role of the message sender (user/agent)
        text: Text content

    Returns:
        Message with a single TextPart
    """
    text_part = TextPart(text)
    return Message(role=role, parts=[text_part])


def create_data_message(
    role: str, data: dict[str, Any], mime_type: str = "application/json"
) -> Message:
    """Create a message with structured data.

    Args:
        role: Role of the message sender (user/agent)
        data: JSON-serializable data
        mime_type: MIME type of the data

    Returns:
        Message with a single DataPart
    """
    data_part = DataPart(data, mime_type)
    return Message(role=role, parts=[data_part])


def create_file_message(
    role: str,
    file_id: str | None = None,
    name: str = "file",
    mime_type: str = "application/octet-stream",
    content: str | bytes | None = None,
    uri: str | None = None,
) -> Message:
    """Create a message with a file attachment.

    Args:
        role: Role of the message sender (user/agent)
        file_id: Unique identifier for the file (generated if None)
        name: File name
        mime_type: MIME type of the file
        content: Optional file content (string or bytes)
        uri: Optional URI to the file

    Returns:
        Message with a single FilePart
    """
    # Generate file ID if not provided
    if file_id is None:
        file_id = str(uuid.uuid4())

    # Encode content if provided
    bytes_base64 = None
    if content is not None:
        if isinstance(content, str):
            content = content.encode("utf-8")
        bytes_base64 = base64.b64encode(content).decode("utf-8")

    file_part = FilePart(
        file_id=file_id,
        name=name,
        mime_type=mime_type,
        bytes_base64=bytes_base64,
        uri=uri,
    )

    return Message(role=role, parts=[file_part])


def create_mixed_message(role: str, parts: list[Part]) -> Message:
    """Create a message with multiple parts.

    Args:
        role: Role of the message sender (user/agent)
        parts: List of message parts

    Returns:
        Message with multiple parts
    """
    return Message(role=role, parts=parts)


def create_function_call_message(
    role: str,
    function_name: str,
    arguments: dict[str, Any],
    text: str | None = None,
) -> Message:
    """Create a message with a function call.

    Args:
        role: Role of the message sender (user/agent)
        function_name: Name of the function to call
        arguments: Function arguments
        text: Optional text description

    Returns:
        Message with a function call
    """
    parts = []
    if text:
        parts.append(TextPart(text))

    function_call = {
        "name": function_name,
        "arguments": json.dumps(arguments),
    }

    return Message(role=role, parts=parts, function_call=function_call)


def create_empty_task(task_id: str | None = None) -> Task:
    """Create an empty task in submitted state.

    Args:
        task_id: Unique identifier for the task (generated if None)

    Returns:
        Empty task in submitted state
    """
    if task_id is None:
        task_id = str(uuid.uuid4())

    return Task(
        task_id=task_id,
        state=TaskState.SUBMITTED,
        messages=[],
    )


def extract_text_from_message(message: Message) -> str:
    """Extract text from all TextParts in a message.

    Args:
        message: Message to extract text from

    Returns:
        Concatenated text from all TextParts
    """
    text_parts = [part.text for part in message.parts if isinstance(part, TextPart)]
    return " ".join(text_parts)
