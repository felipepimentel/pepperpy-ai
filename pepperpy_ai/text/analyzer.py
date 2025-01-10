"""Text analyzer implementation."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from .processor import BaseProcessor

ConfigT = TypeVar("ConfigT")


class BaseAnalyzer(BaseProcessor[ConfigT], ABC):
    """Base text analyzer implementation."""

    @abstractmethod
    async def analyze(self, text: str, **kwargs: Any) -> dict[str, Any]:
        """Analyze text.

        Args:
            text: Text to analyze
            **kwargs: Additional arguments

        Returns:
            Analysis results

        Raises:
            ProcessingError: If analysis fails
            ValidationError: If validation fails
            RuntimeError: If analyzer not initialized
        """
        pass

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """Get analyzer statistics.

        Returns:
            Analyzer statistics

        Raises:
            RuntimeError: If analyzer not initialized
        """
        pass
