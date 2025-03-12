"""Parallel processing capabilities for CPU-bound tasks.

This module provides utilities for parallel processing of CPU-bound tasks,
including process pools, thread pools, and task distribution strategies.
"""

import asyncio
import concurrent.futures
import os
from dataclasses import dataclass
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    List,
    Optional,
    TypeVar,
)

from pepperpy.core.decorators import profile
from pepperpy.errors import PepperpyError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variables
T = TypeVar("T")  # Input type
R = TypeVar("R")  # Result type


class ProcessingStrategy(Enum):
    """Enum representing different parallel processing strategies."""

    PROCESS_POOL = auto()  # Use process pool for CPU-bound tasks
    THREAD_POOL = auto()  # Use thread pool for I/O-bound tasks
    ADAPTIVE = auto()  # Adaptively choose between process and thread pool
    CUSTOM = auto()  # Custom processing strategy


@dataclass
class ParallelConfig:
    """Configuration for parallel processing.

    This class defines the configuration for parallel processing, including
    the processing strategy, number of workers, and chunk size.
    """

    # The strategy to use for parallel processing
    strategy: ProcessingStrategy = ProcessingStrategy.PROCESS_POOL
    # The number of worker processes/threads (None = CPU count)
    workers: Optional[int] = None
    # The size of chunks for data distribution
    chunk_size: int = 1000
    # The maximum number of items to process
    max_items: Optional[int] = None
    # Whether to preserve order of results
    preserve_order: bool = True
    # Custom processing function (for CUSTOM strategy)
    custom_processor: Optional[Callable[[List[T]], List[R]]] = None


class ParallelProcessor(Generic[T, R]):
    """Processor for parallel execution of CPU-bound tasks.

    This class provides methods for executing tasks in parallel using
    either process pools or thread pools, with support for chunking
    and adaptive strategy selection.
    """

    def __init__(self, config: Optional[ParallelConfig] = None):
        """Initialize the parallel processor.

        Args:
            config: The parallel processing configuration
        """
        self.config = config or ParallelConfig()
        self.workers = self.config.workers or os.cpu_count() or 1

    @profile(level="debug")
    async def process_items(
        self, items: Iterable[T], processor: Callable[[T], R]
    ) -> List[R]:
        """Process items in parallel.

        Args:
            items: The items to process
            processor: The function to process each item

        Returns:
            The processed results

        Raises:
            PepperpyError: If processing fails
        """
        try:
            # Convert items to a list and apply max_items limit
            items_list = list(items)
            if self.config.max_items is not None:
                items_list = items_list[: self.config.max_items]

            if not items_list:
                return []

            # Create chunks for processing
            chunks = self._create_chunks(items_list)

            # Process chunks based on strategy
            if self.config.strategy == ProcessingStrategy.PROCESS_POOL:
                results = await self._process_with_process_pool(chunks, processor)
            elif self.config.strategy == ProcessingStrategy.THREAD_POOL:
                results = await self._process_with_thread_pool(chunks, processor)
            elif self.config.strategy == ProcessingStrategy.ADAPTIVE:
                results = await self._process_adaptive(chunks, processor)
            elif self.config.strategy == ProcessingStrategy.CUSTOM:
                results = await self._process_custom(chunks)
            else:
                # Default to process pool
                results = await self._process_with_process_pool(chunks, processor)

            # Flatten results while preserving order if needed
            return self._flatten_results(results)

        except Exception as e:
            raise PepperpyError(f"Error in parallel processing: {e}")

    def _create_chunks(self, items: List[T]) -> List[List[T]]:
        """Create chunks of items for parallel processing.

        Args:
            items: The items to chunk

        Returns:
            The chunked items
        """
        chunk_size = min(self.config.chunk_size, len(items))
        return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]

    async def _process_with_process_pool(
        self, chunks: List[List[T]], processor: Callable[[T], R]
    ) -> List[List[R]]:
        """Process chunks using a process pool.

        Args:
            chunks: The chunks to process
            processor: The function to process each item

        Returns:
            The processed results
        """
        loop = asyncio.get_event_loop()

        def process_chunk(chunk: List[T]) -> List[R]:
            return [processor(item) for item in chunk]

        with concurrent.futures.ProcessPoolExecutor(
            max_workers=self.workers
        ) as executor:
            # Submit all chunks to the process pool
            futures = [
                loop.run_in_executor(executor, process_chunk, chunk) for chunk in chunks
            ]
            # Wait for all futures to complete
            results = await asyncio.gather(*futures)

        return results

    async def _process_with_thread_pool(
        self, chunks: List[List[T]], processor: Callable[[T], R]
    ) -> List[List[R]]:
        """Process chunks using a thread pool.

        Args:
            chunks: The chunks to process
            processor: The function to process each item

        Returns:
            The processed results
        """
        loop = asyncio.get_event_loop()

        def process_chunk(chunk: List[T]) -> List[R]:
            return [processor(item) for item in chunk]

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.workers
        ) as executor:
            # Submit all chunks to the thread pool
            futures = [
                loop.run_in_executor(executor, process_chunk, chunk) for chunk in chunks
            ]
            # Wait for all futures to complete
            results = await asyncio.gather(*futures)

        return results

    async def _process_adaptive(
        self, chunks: List[List[T]], processor: Callable[[T], R]
    ) -> List[List[R]]:
        """Process chunks using an adaptive strategy.

        This method attempts to determine the best processing strategy
        based on the characteristics of the workload.

        Args:
            chunks: The chunks to process
            processor: The function to process each item

        Returns:
            The processed results
        """
        # Try processing a small sample to determine CPU vs I/O bound
        sample_chunk = chunks[0][: min(len(chunks[0]), 10)]

        import time

        import psutil

        # Measure CPU time vs wall time for the sample
        start_cpu = psutil.Process().cpu_times()
        start_time = time.time()

        _ = [processor(item) for item in sample_chunk]

        end_time = time.time()
        end_cpu = psutil.Process().cpu_times()

        wall_time = end_time - start_time
        cpu_time = (end_cpu.user + end_cpu.system) - (start_cpu.user + start_cpu.system)

        # If CPU time is close to wall time, it's CPU bound
        if cpu_time / wall_time > 0.7:
            logger.debug("Workload appears CPU-bound, using process pool")
            return await self._process_with_process_pool(chunks, processor)
        else:
            logger.debug("Workload appears I/O-bound, using thread pool")
            return await self._process_with_thread_pool(chunks, processor)

    async def _process_custom(self, chunks: List[List[T]]) -> List[List[R]]:
        """Process chunks using a custom processor.

        Args:
            chunks: The chunks to process

        Returns:
            The processed results

        Raises:
            PepperpyError: If no custom processor is configured
        """
        if not self.config.custom_processor:
            raise PepperpyError("No custom processor configured")

        loop = asyncio.get_event_loop()
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=self.workers
        ) as executor:
            # Submit all chunks to the process pool
            futures = [
                loop.run_in_executor(executor, self.config.custom_processor, chunk)
                for chunk in chunks
            ]
            # Wait for all futures to complete
            results = await asyncio.gather(*futures)

        return results

    def _flatten_results(self, chunked_results: List[List[R]]) -> List[R]:
        """Flatten chunked results into a single list.

        Args:
            chunked_results: The results in chunks

        Returns:
            The flattened results
        """
        if self.config.preserve_order:
            return [item for chunk in chunked_results for item in chunk]
        else:
            # When order doesn't matter, we can use a faster approach
            flattened = []
            for chunk in chunked_results:
                flattened.extend(chunk)
            return flattened


def create_parallel_processor(
    strategy: ProcessingStrategy = ProcessingStrategy.PROCESS_POOL,
    workers: Optional[int] = None,
    chunk_size: int = 1000,
    max_items: Optional[int] = None,
    preserve_order: bool = True,
    custom_processor: Optional[Callable[[List[Any]], List[Any]]] = None,
) -> ParallelProcessor:
    """Create a parallel processor with the specified configuration.

    Args:
        strategy: The processing strategy to use
        workers: The number of worker processes/threads
        chunk_size: The size of chunks for data distribution
        max_items: The maximum number of items to process
        preserve_order: Whether to preserve order of results
        custom_processor: Custom processing function

    Returns:
        A configured parallel processor
    """
    config = ParallelConfig(
        strategy=strategy,
        workers=workers,
        chunk_size=chunk_size,
        max_items=max_items,
        preserve_order=preserve_order,
        custom_processor=custom_processor,
    )
    return ParallelProcessor(config)
