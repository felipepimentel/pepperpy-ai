"""Base adapter system.

This module provides core adapter functionality:
- Adapter definition
- Adapter lifecycle
- Adapter tracking
- Adapter metadata
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pepperpy.core.errors import AdapterError
from pepperpy.core.lifecycle import LifecycleComponent
from pepperpy.core.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Type variables for adapter input/output
InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class AdapterType(str, Enum):
    """Adapter types."""

    PROVIDER = "provider"
    PROCESSOR = "processor"
    STORAGE = "storage"
    NETWORK = "network"
    CUSTOM = "custom"


class AdapterState(str, Enum):
    """Adapter states."""

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    CLEANED = "cleaned"


@dataclass
class AdapterMetadata:
    """Adapter metadata information."""

    type: AdapterType
    version: str
    description: str
    author: str
    dependencies: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: datetime | None = None
    expires_at: datetime | None = None
    tags: dict[str, str] = field(default_factory=dict)


class Adapter(LifecycleComponent, Generic[InputT, OutputT]):
    """Base class for adapters."""

    def __init__(
        self,
        name: str,
        config: dict[str, Any],
    ) -> None:
        """Initialize adapter.

        Args:
            name: Adapter name
            config: Adapter configuration
        """
        super().__init__(f"adapter_{name}")
        self.name = name
        self.config = config
        self._state = AdapterState.CREATED

    @property
    def state(self) -> AdapterState:
        """Get adapter state.

        Returns:
            Adapter state
        """
        return self._state

    @classmethod
    def get_metadata(cls) -> AdapterMetadata:
        """Get adapter metadata.

        Returns:
            Adapter metadata
        """
        return getattr(cls, "__adapter_metadata__", None) or AdapterMetadata(
            type=AdapterType.CUSTOM,
            version="1.0.0",
            description=cls.__doc__ or "No description available",
            author="Unknown",
        )

    async def initialize(self) -> None:
        """Initialize adapter.

        Raises:
            AdapterError: If initialization fails
        """
        try:
            await super().initialize()
            self._state = AdapterState.INITIALIZING
            await self._initialize_adapter()
            self._state = AdapterState.READY
            logger.info(
                "Adapter initialized",
                extra={
                    "name": self.name,
                    "type": self.get_metadata().type,
                },
            )
        except Exception as e:
            self._state = AdapterState.ERROR
            raise AdapterError(f"Failed to initialize adapter {self.name}: {e}")

    async def cleanup(self) -> None:
        """Clean up adapter.

        Raises:
            AdapterError: If cleanup fails
        """
        try:
            await super().cleanup()
            await self._cleanup_adapter()
            self._state = AdapterState.CLEANED
            logger.info(
                "Adapter cleaned up",
                extra={
                    "name": self.name,
                    "type": self.get_metadata().type,
                },
            )
        except Exception as e:
            self._state = AdapterState.ERROR
            raise AdapterError(f"Failed to clean up adapter {self.name}: {e}")

    async def adapt(self, input: InputT) -> OutputT:
        """Adapt input to output.

        Args:
            input: Input data

        Returns:
            Adapted output

        Raises:
            AdapterError: If adaptation fails
        """
        try:
            return await self._adapt(input)
        except Exception as e:
            raise AdapterError(f"Adaptation failed: {e}")

    async def _initialize_adapter(self) -> None:
        """Initialize adapter implementation.

        This method should be overridden by subclasses to perform
        adapter-specific initialization.

        Raises:
            AdapterError: If initialization fails
        """
        pass

    async def _cleanup_adapter(self) -> None:
        """Clean up adapter implementation.

        This method should be overridden by subclasses to perform
        adapter-specific cleanup.

        Raises:
            AdapterError: If cleanup fails
        """
        pass

    async def _adapt(self, input: InputT) -> OutputT:
        """Adapt input to output implementation.

        This method must be overridden by subclasses to perform
        the actual adaptation.

        Args:
            input: Input data

        Returns:
            Adapted output

        Raises:
            AdapterError: If adaptation fails
        """
        raise NotImplementedError("Subclasses must implement _adapt")


class ProviderAdapter(Adapter[InputT, OutputT]):
    """Base class for provider adapters."""

    @classmethod
    def get_metadata(cls) -> AdapterMetadata:
        """Get adapter metadata.

        Returns:
            Adapter metadata
        """
        metadata = super().get_metadata()
        metadata.type = AdapterType.PROVIDER
        return metadata


class ProcessorAdapter(Adapter[InputT, OutputT]):
    """Base class for processor adapters."""

    @classmethod
    def get_metadata(cls) -> AdapterMetadata:
        """Get adapter metadata.

        Returns:
            Adapter metadata
        """
        metadata = super().get_metadata()
        metadata.type = AdapterType.PROCESSOR
        return metadata


class StorageAdapter(Adapter[InputT, OutputT]):
    """Base class for storage adapters."""

    @classmethod
    def get_metadata(cls) -> AdapterMetadata:
        """Get adapter metadata.

        Returns:
            Adapter metadata
        """
        metadata = super().get_metadata()
        metadata.type = AdapterType.STORAGE
        return metadata


class NetworkAdapter(Adapter[InputT, OutputT]):
    """Base class for network adapters."""

    @classmethod
    def get_metadata(cls) -> AdapterMetadata:
        """Get adapter metadata.

        Returns:
            Adapter metadata
        """
        metadata = super().get_metadata()
        metadata.type = AdapterType.NETWORK
        return metadata


# Export public API
__all__ = [
    "Adapter",
    "AdapterMetadata",
    "AdapterState",
    "AdapterType",
    "NetworkAdapter",
    "ProcessorAdapter",
    "ProviderAdapter",
    "StorageAdapter",
]
