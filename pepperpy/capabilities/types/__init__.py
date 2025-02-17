"""Capability type implementations.

This module provides implementations of common capability types like
prompt, search, and memory capabilities.
"""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, TypeVar
from uuid import UUID

from pepperpy.core.errors import ConfigurationError
from pepperpy.core.errors import StateError as StateError
from pepperpy.core.logging import get_logger

from ..base import (
    BaseCapability,
    CapabilityMetadata,
    CapabilityType,
)
from ..base import (
    CapabilityResult as CapabilityResult,
)

logger = get_logger(__name__)


# Type variables for specific capability results
PromptT = TypeVar("PromptT")
SearchT = TypeVar("SearchT")
MemoryT = TypeVar("MemoryT")


class PromptCapability(BaseCapability[PromptT]):
    """Prompt capability implementation.

    This class provides functionality for managing prompt generation
    and execution capabilities.

    Attributes:
        id: Unique identifier
        metadata: Capability metadata
        state: Current capability state
        error: Current error if any

    Example:
        >>> capability = PromptCapability(
        ...     metadata=CapabilityMetadata(
        ...         capability_name="gpt4_prompt",
        ...         capability_type=CapabilityType.PROMPT,
        ...     )
        ... )
        >>> await capability.initialize()
        >>> result = await capability.execute(
        ...     prompt="What is the meaning of life?",
        ...     model="gpt-4",
        ... )
        >>> assert result.success

    """

    def __init__(
        self,
        metadata: CapabilityMetadata,
        id: Optional[UUID] = None,
    ) -> None:
        """Initialize the prompt capability.

        Args:
            metadata: Capability metadata
            id: Optional capability ID

        Raises:
            ConfigurationError: If metadata is invalid

        """
        if metadata.capability_type != CapabilityType.PROMPT:
            raise ConfigurationError("Invalid capability type for prompt capability")
        super().__init__(metadata, id)

    async def _initialize(self) -> None:
        """Initialize the prompt capability.

        This method should be overridden by subclasses to perform
        prompt-specific initialization.

        Raises:
            ConfigurationError: If initialization fails

        """
        raise NotImplementedError

    async def _cleanup(self) -> None:
        """Clean up the prompt capability.

        This method should be overridden by subclasses to perform
        prompt-specific cleanup.

        Raises:
            StateError: If cleanup fails

        """
        raise NotImplementedError


class SearchCapability(BaseCapability[SearchT]):
    """Search capability implementation.

    This class provides functionality for managing search and retrieval
    capabilities.

    Attributes:
        id: Unique identifier
        metadata: Capability metadata
        state: Current capability state
        error: Current error if any

    Example:
        >>> capability = SearchCapability(
        ...     metadata=CapabilityMetadata(
        ...         capability_name="vector_search",
        ...         capability_type=CapabilityType.SEARCH,
        ...     )
        ... )
        >>> await capability.initialize()
        >>> result = await capability.execute(
        ...     query="Find documents about AI",
        ...     limit=10,
        ... )
        >>> assert result.success

    """

    def __init__(
        self,
        metadata: CapabilityMetadata,
        id: Optional[UUID] = None,
    ) -> None:
        """Initialize the search capability.

        Args:
            metadata: Capability metadata
            id: Optional capability ID

        Raises:
            ConfigurationError: If metadata is invalid

        """
        if metadata.capability_type != CapabilityType.SEARCH:
            raise ConfigurationError("Invalid capability type for search capability")
        super().__init__(metadata, id)

    async def _initialize(self) -> None:
        """Initialize the search capability.

        This method should be overridden by subclasses to perform
        search-specific initialization.

        Raises:
            ConfigurationError: If initialization fails

        """
        raise NotImplementedError

    async def _cleanup(self) -> None:
        """Clean up the search capability.

        This method should be overridden by subclasses to perform
        search-specific cleanup.

        Raises:
            StateError: If cleanup fails

        """
        raise NotImplementedError


class MemoryCapability(BaseCapability[MemoryT]):
    """Memory capability implementation.

    This class provides functionality for managing memory and context
    capabilities.

    Attributes:
        id: Unique identifier
        metadata: Capability metadata
        state: Current capability state
        error: Current error if any

    Example:
        >>> capability = MemoryCapability(
        ...     metadata=CapabilityMetadata(
        ...         capability_name="conversation_memory",
        ...         capability_type=CapabilityType.MEMORY,
        ...     )
        ... )
        >>> await capability.initialize()
        >>> result = await capability.execute(
        ...     operation="store",
        ...     key="conversation_1",
        ...     value={"messages": [...]},
        ... )
        >>> assert result.success

    """

    def __init__(
        self,
        metadata: CapabilityMetadata,
        id: Optional[UUID] = None,
    ) -> None:
        """Initialize the memory capability.

        Args:
            metadata: Capability metadata
            id: Optional capability ID

        Raises:
            ConfigurationError: If metadata is invalid

        """
        if metadata.capability_type != CapabilityType.MEMORY:
            raise ConfigurationError("Invalid capability type for memory capability")
        super().__init__(metadata, id)

    async def _initialize(self) -> None:
        """Initialize the memory capability.

        This method should be overridden by subclasses to perform
        memory-specific initialization.

        Raises:
            ConfigurationError: If initialization fails

        """
        raise NotImplementedError

    async def _cleanup(self) -> None:
        """Clean up the memory capability.

        This method should be overridden by subclasses to perform
        memory-specific cleanup.

        Raises:
            StateError: If cleanup fails

        """
        raise NotImplementedError
