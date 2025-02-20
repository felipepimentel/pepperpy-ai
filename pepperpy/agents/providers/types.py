"""Type definitions for providers.

This module defines the core type definitions used by providers in the
Pepperpy framework.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, TypeVar, Union
from uuid import UUID, uuid4

from pepperpy.core.types import Message, MessageType, Response

T = TypeVar("T")


@dataclass
class ProviderMessage(Message[Union[str, Dict[str, Any]]]):
    """Message that can be processed by providers.

    Attributes:
        id: Unique message identifier
        content: Message content
        provider_type: Type of provider to handle message
        metadata: Optional message metadata
        created_at: Message creation timestamp
        parameters: Additional provider parameters

    """

    parameters: Dict[str, Any] = field(default_factory=dict)
    provider_type: str = field(default="")

    def __init__(
        self, content: Union[str, Dict[str, Any]], provider_type: str, **kwargs: Any
    ) -> None:
        """Initialize a provider message.

        Args:
            content: Message content
            provider_type: Type of provider to handle message
            **kwargs: Additional keyword arguments passed to parent

        """
        super().__init__(
            content=content,
            type=kwargs.get("type", MessageType.QUERY),
            metadata=kwargs.get("metadata", {}),
        )
        self.provider_type = provider_type
        self.parameters = kwargs.get("parameters", {})
        if not self.metadata:
            self.metadata = {}
        self.metadata["provider_type"] = self.provider_type
        self.metadata["parameters"] = self.parameters


@dataclass
class ProviderResponse(Response[T]):
    """Response from a provider.

    Attributes:
        id: Unique response identifier
        content: Response content
        provider_type: Type of provider that generated response
        model: Model used to generate response
        metadata: Optional response metadata
        created_at: Response creation timestamp
        usage: Resource usage information

    """

    usage: Dict[str, Any] = field(default_factory=dict)
    provider_type: str = field(default="")
    model: str = field(default="")

    def __init__(
        self, content: T, provider_type: str, model: str, **kwargs: Any
    ) -> None:
        """Initialize a provider response.

        Args:
            content: Response content
            provider_type: Type of provider that generated response
            model: Model used to generate response
            **kwargs: Additional keyword arguments passed to parent

        """
        super().__init__(
            message_id=str(kwargs.get("message_id", uuid4())),
            content=content,
            **kwargs,
        )
        self.provider_type = provider_type
        self.model = model
        self.usage = kwargs.get("usage", {})
        if not self.metadata:
            self.metadata = {}
        self.metadata["provider_type"] = self.provider_type
        self.metadata["model"] = self.model
        self.metadata["usage"] = self.usage


# Type aliases
ProviderID = UUID
MessageID = UUID
ResponseID = UUID
