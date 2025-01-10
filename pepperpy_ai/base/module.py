"""Base module implementation."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ..config.base import BaseConfig

ConfigT = TypeVar("ConfigT", bound=BaseConfig)


class BaseModule(Generic[ConfigT], ABC):
    """Base module implementation."""

    def __init__(self, config: ConfigT) -> None:
        """Initialize module."""
        self.config = config
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if module is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize module."""
        if not self._initialized:
            await self._setup()
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup module resources."""
        if self._initialized:
            await self._teardown()
            self._initialized = False

    @abstractmethod
    async def _setup(self) -> None:
        """Setup module resources."""
        pass

    @abstractmethod
    async def _teardown(self) -> None:
        """Teardown module resources."""
        pass
