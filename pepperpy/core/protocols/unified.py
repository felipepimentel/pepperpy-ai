"""Unified protocol system for Pepperpy.

This module provides a comprehensive protocol framework that includes:
- Base protocol interface
- Protocol metadata representation
- Protocol provider interface
- Protocol registry
- Protocol validation
- Protocol monitoring
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pepperpy.core.errors.unified import PepperpyError
from pepperpy.core.metrics import MetricsManager

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ProtocolError(PepperpyError):
    """Base class for protocol-related errors."""

    def __init__(self, message: str, code: str = "PROTO000", **kwargs):
        super().__init__(message, code=code, category="protocol", **kwargs)


@dataclass
class ProtocolMetadata:
    """Metadata for protocol implementations."""

    name: str
    version: str
    description: str
    capabilities: list[str]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary.

        Returns:
            Dictionary containing metadata.
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "capabilities": self.capabilities,
            "metadata": self.metadata,
        }


class BaseProtocol(ABC, Generic[T]):
    """Base protocol for all interfaces."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component.

        Raises:
            ProtocolError: If initialization fails.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources.

        Raises:
            ProtocolError: If cleanup fails.
        """
        pass

    @abstractmethod
    async def validate(self) -> list[str]:
        """Validate component state.

        Returns:
            List of validation errors, empty if valid.
        """
        pass


class ProtocolProvider(ABC, Generic[T]):
    """Base class for protocol providers."""

    @property
    @abstractmethod
    def metadata(self) -> ProtocolMetadata:
        """Get provider metadata.

        Returns:
            Provider metadata.
        """
        pass

    @abstractmethod
    async def get_implementation(self) -> T:
        """Get protocol implementation.

        Returns:
            Protocol implementation.

        Raises:
            ProtocolError: If implementation cannot be provided.
        """
        pass


class ProtocolRegistry:
    """Registry for protocol implementations."""

    def __init__(self):
        """Initialize the protocol registry."""
        self._protocols: dict[str, dict[str, type[BaseProtocol]]] = {}
        self._providers: dict[str, dict[str, ProtocolProvider]] = {}
        self._metrics = MetricsManager.get_instance()
        self._lock = asyncio.Lock()

    def register_protocol(
        self, name: str, version: str, protocol: type[BaseProtocol]
    ) -> None:
        """Register a protocol implementation.

        Args:
            name: Protocol name.
            version: Protocol version.
            protocol: Protocol class.

        Raises:
            ProtocolError: If protocol is already registered.
        """
        if name not in self._protocols:
            self._protocols[name] = {}

        if version in self._protocols[name]:
            raise ProtocolError(
                f"Protocol already registered: {name} {version}", code="PROTO001"
            )

        self._protocols[name][version] = protocol
        self._metrics.counter("protocol_registered", 1, name=name, version=version)

    def register_provider(self, provider: ProtocolProvider) -> None:
        """Register a protocol provider.

        Args:
            provider: Protocol provider instance.

        Raises:
            ProtocolError: If provider is already registered.
        """
        metadata = provider.metadata
        if metadata.name not in self._providers:
            self._providers[metadata.name] = {}

        if metadata.version in self._providers[metadata.name]:
            raise ProtocolError(
                f"Provider already registered: {metadata.name} {metadata.version}",
                code="PROTO002",
            )

        self._providers[metadata.name][metadata.version] = provider
        self._metrics.counter(
            "provider_registered", 1, name=metadata.name, version=metadata.version
        )

    async def get_implementation(
        self, name: str, version: str | None = None
    ) -> BaseProtocol:
        """Get protocol implementation.

        Args:
            name: Protocol name.
            version: Optional protocol version.

        Returns:
            Protocol implementation.

        Raises:
            ProtocolError: If protocol or version not found.
        """
        if name not in self._providers:
            raise ProtocolError(f"Protocol not found: {name}", code="PROTO003")

        providers = self._providers[name]
        if not version:
            # Get latest version
            version = max(providers.keys())

        if version not in providers:
            raise ProtocolError(f"Version not found: {version}", code="PROTO004")

        try:
            provider = providers[version]
            implementation = await provider.get_implementation()

            self._metrics.counter(
                "implementation_retrieved",
                1,
                name=name,
                version=version,
                success="true",
            )

            return implementation
        except Exception as e:
            self._metrics.counter(
                "implementation_retrieved",
                1,
                name=name,
                version=version,
                success="false",
            )

            raise ProtocolError(
                f"Failed to get implementation: {e}", code="PROTO005"
            ) from e


class ProtocolValidator:
    """Validator for protocol implementations."""

    def __init__(self):
        """Initialize the protocol validator."""
        self._metrics = MetricsManager.get_instance()

    async def validate_implementation(
        self, protocol: type[BaseProtocol], implementation: Any
    ) -> list[str]:
        """Validate protocol implementation.

        Args:
            protocol: Protocol class.
            implementation: Implementation to validate.

        Returns:
            List of validation errors, empty if valid.
        """
        errors = []

        # Check interface
        if not isinstance(implementation, protocol):
            errors.append(
                f"Implementation does not implement protocol: {protocol.__name__}"
            )

        # Check methods
        for method in protocol.__abstractmethods__:
            if not hasattr(implementation, method):
                errors.append(f"Missing method: {method}")
                continue

            impl_method = getattr(implementation, method)
            if not callable(impl_method):
                errors.append(f"Method not callable: {method}")

        self._metrics.counter(
            "implementation_validated",
            1,
            protocol=protocol.__name__,
            success=str(len(errors) == 0).lower(),
        )

        return errors

    async def validate_provider(self, provider: ProtocolProvider) -> list[str]:
        """Validate protocol provider.

        Args:
            provider: Provider to validate.

        Returns:
            List of validation errors, empty if valid.
        """
        errors = []

        try:
            implementation = await provider.get_implementation()
            metadata = provider.metadata

            # Validate metadata
            if not metadata.name:
                errors.append("Missing provider name")
            if not metadata.version:
                errors.append("Missing provider version")

            # Validate implementation
            impl_errors = await self.validate_implementation(
                BaseProtocol, implementation
            )
            errors.extend(impl_errors)

            self._metrics.counter(
                "provider_validated",
                1,
                provider=metadata.name,
                success=str(len(errors) == 0).lower(),
            )

        except Exception as e:
            errors.append(f"Provider validation failed: {e}")

            self._metrics.counter(
                "provider_validated",
                1,
                provider=provider.metadata.name,
                success="false",
            )

        return errors


class ProtocolMonitor:
    """Monitor for protocol implementations."""

    def __init__(self):
        """Initialize the protocol monitor."""
        self._metrics = MetricsManager.get_instance()

    async def record_operation(
        self, protocol: str, operation: str, success: bool = True, **labels: str
    ) -> None:
        """Record protocol operation.

        Args:
            protocol: Protocol name.
            operation: Operation name.
            success: Whether operation succeeded.
            **labels: Additional metric labels.
        """
        self._metrics.counter(
            f"protocol_{operation}",
            1,
            protocol=protocol,
            success=str(success).lower(),
            **labels,
        )

    async def record_error(self, protocol: str, error: str, **labels: str) -> None:
        """Record protocol error.

        Args:
            protocol: Protocol name.
            error: Error message.
            **labels: Additional metric labels.
        """
        self._metrics.counter(
            "protocol_error", 1, protocol=protocol, error=error, **labels
        )

        logger.error(f"Protocol error: {error}", extra={"protocol": protocol, **labels})
