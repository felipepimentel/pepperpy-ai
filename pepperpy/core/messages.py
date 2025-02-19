"""Message and response types for the Pepperpy framework.

This module defines the base message and response types used throughout
the framework for communication between components.
"""

from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Base message type.

    Attributes:
        id: Unique message identifier
        content: Message content
        metadata: Additional message metadata
    """

    id: UUID = Field(default_factory=uuid4)
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Response(BaseModel):
    """Base response type.

    Attributes:
        id: Unique response identifier
        content: Response content
        metadata: Additional response metadata
    """

    id: UUID = Field(default_factory=uuid4)
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProviderMessage(Message):
    """Provider-specific message type.

    Attributes:
        provider_id: Provider identifier
        provider_type: Provider type
    """

    provider_id: Optional[UUID] = None
    provider_type: Optional[str] = None


class ProviderResponse(Response):
    """Provider-specific response type.

    Attributes:
        provider_id: Provider identifier
        provider_type: Provider type
    """

    provider_id: Optional[UUID] = None
    provider_type: Optional[str] = None
