"""Memory optimization strategies for RAG."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Union

from pepperpy.core.errors import PepperPyError
from pepperpy.rag.base import Document, Query, RetrievalResult


class MemoryOptimizationError(PepperPyError):
    """Base class for memory optimization errors."""

    pass


class BaseMemoryOptimizer(ABC):
    """Base class for memory optimization strategies."""

    @abstractmethod
    async def optimize(
        self,
        query: Query,
        documents: List[Document],
        **kwargs: Any,
    ) -> RetrievalResult:
        """Optimize memory usage for a query and documents.

        Args:
            query: The query to optimize for.
            documents: The documents to optimize.
            **kwargs: Additional optimizer-specific arguments.

        Returns:
            A RetrievalResult containing the optimized documents.

        Raises:
            MemoryOptimizationError: If there is an error optimizing memory.
        """
        pass
