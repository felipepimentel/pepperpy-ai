"""Base adapter module.

This module provides base implementations for the adapter system.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Generic, Optional, Type, cast

from pepperpy.adapters.types import (
    AdapterCapabilities,
    AdapterConfig,
    AdapterContext,
    AdapterResult,
    AdapterState,
    AdapterType,
    AdapterValidation,
    T_Config,
    T_Context,
    T_Input,
    T_Output,
)
from pepperpy.common.base import ComponentBase, ComponentConfig, ComponentState
from pepperpy.common.errors import AdapterError

# Configure logging
logger = logging.getLogger(__name__)


def create_default_capabilities() -> AdapterCapabilities:
    """Create default adapter capabilities."""
    return AdapterCapabilities(
        supports_async=True,
        supports_streaming=False,
        supports_batching=False,
        supports_caching=False,
        supports_validation=True,
        supports_conversion=True,
    )


def create_default_validation() -> AdapterValidation:
    """Create default adapter validation."""
    return AdapterValidation(
        input_schema=None,
        output_schema=None,
        config_schema=None,
    )


class BaseAdapter(ComponentBase, Generic[T_Config, T_Context, T_Input, T_Output]):
    """Base adapter implementation.

    This class provides a base implementation for adapters with improved
    flexibility and extensibility.
    """

    def __init__(
        self,
        config: T_Config,
        context: Optional[T_Context] = None,
        capabilities: Optional[AdapterCapabilities] = None,
        validation: Optional[AdapterValidation] = None,
    ) -> None:
        """Initialize adapter.

        Args:
            config: Adapter configuration
            context: Adapter context
            capabilities: Adapter capabilities
            validation: Adapter validation
        """
        component_config = ComponentConfig(
            name=config.name,
            version=config.version,
            description=config.description or "",
        )
        super().__init__(config=component_config)
        self.config = config
        self.context = context or self._create_context()
        self.capabilities = capabilities or create_default_capabilities()
        self.validation = validation or create_default_validation()
        self._lock = asyncio.Lock()

    @property
    def name(self) -> str:
        """Get adapter name."""
        return self.config.name

    @property
    def type(self) -> AdapterType:
        """Get adapter type."""
        return self.config.type

    @property
    def version(self) -> str:
        """Get adapter version."""
        return self.config.version

    @property
    def state(self) -> AdapterState:
        """Get adapter state."""
        return self.context.state if self.context else AdapterState.CREATED

    async def adapt(self, data: T_Input) -> AdapterResult[T_Output]:
        """Adapt input data to output format.

        Args:
            data: Input data to adapt

        Returns:
            AdapterResult: Adaptation result

        Raises:
            AdapterError: If adaptation fails
        """
        try:
            # Update metrics
            self.context.metrics.total_calls += 1
            start_time = datetime.utcnow()

            # Validate input if enabled
            if self.capabilities.supports_validation and self.validation.input_schema:
                await self._validate_input(data)

            # Perform adaptation
            output = await self._adapt(data)

            # Validate output if enabled
            if self.capabilities.supports_validation and self.validation.output_schema:
                await self._validate_output(output)

            # Update metrics
            end_time = datetime.utcnow()
            latency = (end_time - start_time).total_seconds()
            self.context.metrics.successful_calls += 1
            self.context.metrics.total_latency += latency
            self.context.metrics.average_latency = (
                self.context.metrics.total_latency
                / self.context.metrics.successful_calls
            )
            self.context.metrics.last_call = end_time

            return AdapterResult(
                success=True,
                output=output,
                error=None,
                metrics={"latency": latency},
            )

        except Exception as e:
            # Update error metrics
            self.context.metrics.failed_calls += 1
            self.context.metrics.last_error = str(e)

            logger.error(
                f"Adaptation failed: {e}",
                extra={
                    "adapter": self.name,
                    "type": str(self.type),
                    "version": self.version,
                },
                exc_info=True,
            )
            return AdapterResult(
                success=False,
                output=None,
                error=str(e),
                metrics={"error_type": type(e).__name__},
            )

    async def reverse(self, data: T_Output) -> AdapterResult[T_Input]:
        """Reverse adapt output data to input format.

        Args:
            data: Output data to reverse adapt

        Returns:
            AdapterResult: Reverse adaptation result

        Raises:
            AdapterError: If reverse adaptation fails
        """
        try:
            # Update metrics
            self.context.metrics.total_calls += 1
            start_time = datetime.utcnow()

            # Validate output if enabled
            if self.capabilities.supports_validation and self.validation.output_schema:
                await self._validate_output(data)

            # Perform reverse adaptation
            input_data = await self._reverse(data)

            # Validate input if enabled
            if self.capabilities.supports_validation and self.validation.input_schema:
                await self._validate_input(input_data)

            # Update metrics
            end_time = datetime.utcnow()
            latency = (end_time - start_time).total_seconds()
            self.context.metrics.successful_calls += 1
            self.context.metrics.total_latency += latency
            self.context.metrics.average_latency = (
                self.context.metrics.total_latency
                / self.context.metrics.successful_calls
            )
            self.context.metrics.last_call = end_time

            return AdapterResult(
                success=True,
                output=input_data,
                error=None,
                metrics={"latency": latency},
            )

        except Exception as e:
            # Update error metrics
            self.context.metrics.failed_calls += 1
            self.context.metrics.last_error = str(e)

            logger.error(
                f"Reverse adaptation failed: {e}",
                extra={
                    "adapter": self.name,
                    "type": str(self.type),
                    "version": self.version,
                },
                exc_info=True,
            )
            return AdapterResult(
                success=False,
                output=None,
                error=str(e),
                metrics={"error_type": type(e).__name__},
            )

    async def _initialize(self) -> None:
        """Initialize adapter."""
        try:
            # Update state
            await self.set_state(ComponentState.INITIALIZING)
            self.context.state = AdapterState.INITIALIZING

            # Validate configuration if enabled
            if self.capabilities.supports_validation and self.validation.config_schema:
                await self._validate_config(self.config)

            # Initialize adapter
            await self._init()

            # Update state
            await self.set_state(ComponentState.READY)
            self.context.state = AdapterState.READY

        except Exception as e:
            await self.set_state(ComponentState.ERROR)
            self.context.state = AdapterState.FAILED
            raise AdapterError(f"Failed to initialize adapter: {e}") from e

    async def _execute(self, **kwargs: Any) -> Any:
        """Execute adapter.

        Args:
            **kwargs: Execution arguments

        Returns:
            Any: Adaptation result
        """
        data = cast(T_Input, kwargs.get("data"))
        return await self.adapt(data)

    async def _cleanup(self) -> None:
        """Clean up adapter."""
        try:
            # Update state
            await self.set_state(ComponentState.TERMINATED)
            self.context.state = AdapterState.CLOSED

            # Clean up adapter
            await self._clean()

        except Exception as e:
            logger.error(
                f"Failed to clean up adapter: {e}",
                extra={
                    "adapter": self.name,
                    "type": str(self.type),
                    "version": self.version,
                },
                exc_info=True,
            )

    def _create_context(self) -> T_Context:
        """Create adapter context.

        Returns:
            T_Context: Created context
        """
        return AdapterContext(
            adapter_id=self.config.name,
            config=self.config,
        )  # type: ignore

    @abstractmethod
    async def _adapt(self, data: T_Input) -> T_Output:
        """Adapt input data to output format.

        Args:
            data: Input data to adapt

        Returns:
            T_Output: Adapted output data

        Raises:
            AdapterError: If adaptation fails
        """
        pass

    @abstractmethod
    async def _reverse(self, data: T_Output) -> T_Input:
        """Reverse adapt output data to input format.

        Args:
            data: Output data to reverse adapt

        Returns:
            T_Input: Original input data

        Raises:
            AdapterError: If reverse adaptation fails
        """
        pass

    @abstractmethod
    async def _init(self) -> None:
        """Initialize adapter implementation.

        Raises:
            AdapterError: If initialization fails
        """
        pass

    @abstractmethod
    async def _clean(self) -> None:
        """Clean up adapter implementation.

        Raises:
            AdapterError: If cleanup fails
        """
        pass

    async def _validate_config(self, config: T_Config) -> None:
        """Validate adapter configuration.

        Args:
            config: Configuration to validate

        Raises:
            AdapterError: If validation fails
        """
        if not self.validation.config_schema:
            return

        try:
            # TODO: Implement config validation
            pass
        except Exception as e:
            raise AdapterError(f"Invalid adapter configuration: {e}") from e

    async def _validate_input(self, data: T_Input) -> None:
        """Validate input data.

        Args:
            data: Input data to validate

        Raises:
            AdapterError: If validation fails
        """
        if not self.validation.input_schema:
            return

        try:
            # TODO: Implement input validation
            pass
        except Exception as e:
            raise AdapterError(f"Invalid input data: {e}") from e

    async def _validate_output(self, data: T_Output) -> None:
        """Validate output data.

        Args:
            data: Output data to validate

        Raises:
            AdapterError: If validation fails
        """
        if not self.validation.output_schema:
            return

        try:
            # TODO: Implement output validation
            pass
        except Exception as e:
            raise AdapterError(f"Invalid output data: {e}") from e


class AdapterFactory(ABC):
    """Base class for adapter factories.

    This class defines the interface that all adapter factories must implement.
    Adapter factories are responsible for:
    - Creating adapter instances
    - Managing adapter configuration
    - Validating adapter settings
    """

    def __init__(self, adapter_type: Type[Adapter]) -> None:
        """Initialize adapter factory.

        Args:
            adapter_type: Type of adapter to create
        """
        self.adapter_type = adapter_type

    @abstractmethod
    async def create(self, config: AdapterConfig) -> Adapter:
        """Create an adapter instance.

        Args:
            config: Adapter configuration

        Returns:
            Adapter instance

        Raises:
            AdapterError: If creation fails
        """
        pass

    @abstractmethod
    async def validate_config(self, config: AdapterConfig) -> None:
        """Validate adapter configuration.

        Args:
            config: Configuration to validate

        Raises:
            AdapterError: If validation fails
        """
        pass


class AdapterRegistry:
    """Registry for adapters and factories.

    This class manages adapter registration and creation.
    It provides functionality for:
    - Registering adapters and factories
    - Creating adapter instances
    - Managing adapter lifecycle
    """

    _instance: Optional["AdapterRegistry"] = None

    def __init__(self) -> None:
        """Initialize adapter registry."""
        self._adapters: Dict[str, Adapter] = {}
        self._factories: Dict[str, AdapterFactory] = {}

    @classmethod
    def get_instance(cls) -> "AdapterRegistry":
        """Get singleton instance.

        Returns:
            AdapterRegistry instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def register_adapter(
        self,
        adapter: Adapter,
    ) -> None:
        """Register an adapter.

        Args:
            adapter: Adapter to register

        Raises:
            AdapterError: If registration fails
        """
        if adapter.name in self._adapters:
            raise AdapterError(f"Adapter {adapter.name} already registered")

        try:
            # Validate adapter
            await adapter.validate()

            # Register adapter
            self._adapters[adapter.name] = adapter
            logger.info(
                "Registered adapter",
                extra={
                    "name": adapter.name,
                    "type": adapter.type,
                    "version": adapter.version,
                },
            )

        except Exception as e:
            raise AdapterError(f"Failed to register adapter {adapter.name}: {e}")

    async def register_factory(
        self,
        name: str,
        factory: AdapterFactory,
    ) -> None:
        """Register an adapter factory.

        Args:
            name: Factory name
            factory: Factory to register

        Raises:
            AdapterError: If registration fails
        """
        if name in self._factories:
            raise AdapterError(f"Factory {name} already registered")

        try:
            # Register factory
            self._factories[name] = factory
            logger.info(
                "Registered adapter factory",
                extra={"name": name, "adapter_type": factory.adapter_type.__name__},
            )

        except Exception as e:
            raise AdapterError(f"Failed to register factory {name}: {e}")

    async def get_adapter(self, name: str) -> Optional[Adapter]:
        """Get an adapter by name.

        Args:
            name: Adapter name

        Returns:
            Adapter if found, None otherwise
        """
        return self._adapters.get(name)

    async def create_adapter(
        self,
        factory_name: str,
        config: AdapterConfig,
    ) -> Adapter:
        """Create an adapter using a factory.

        Args:
            factory_name: Factory name
            config: Adapter configuration

        Returns:
            Created adapter

        Raises:
            AdapterError: If creation fails
        """
        factory = self._factories.get(factory_name)
        if not factory:
            raise AdapterError(f"Factory {factory_name} not found")

        try:
            # Validate config
            await factory.validate_config(config)

            # Create adapter
            adapter = await factory.create(config)

            # Register adapter
            await self.register_adapter(adapter)

            return adapter

        except Exception as e:
            raise AdapterError(
                f"Failed to create adapter {config.name} using factory {factory_name}: {e}"
            )
