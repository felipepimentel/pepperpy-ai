"""Batching strategies for bulk operations.

This module provides utilities for batching operations to improve performance
and resource utilization when working with large datasets or making multiple
API calls.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import (
    Awaitable,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Tuple,
    TypeVar,
    cast,
)

from pepperpy.core.decorators import profile
from pepperpy.core.errors import PepperPyError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variables
T = TypeVar("T")  # Input item type
R = TypeVar("R")  # Result type
K = TypeVar("K")  # Key type


class BatchingStrategy(Enum):
    """Enum representing different batching strategies."""

    FIXED_SIZE = auto()  # Fixed batch size
    ADAPTIVE = auto()  # Adaptive batch size based on processing time
    TIME_WINDOW = auto()  # Batch items within a time window
    SIZE_BASED = auto()  # Batch items based on total size
    PRIORITY = auto()  # Batch items based on priority
    CUSTOM = auto()  # Custom batching strategy


@dataclass
class BatchConfig:
    """Configuration for batching operations.

    This class defines the configuration for batching operations, including
    batch size, timeout, and retry settings.
    """

    # The strategy to use for batching
    strategy: BatchingStrategy = BatchingStrategy.FIXED_SIZE
    # The maximum number of items in a batch
    max_batch_size: int = 100
    # The minimum number of items in a batch
    min_batch_size: int = 1
    # The maximum time to wait for a batch to fill up (in seconds)
    batch_timeout: float = 1.0
    # The maximum number of retries for a batch
    max_retries: int = 3
    # The delay between retries (in seconds)
    retry_delay: float = 1.0
    # Whether to use exponential backoff for retries
    exponential_backoff: bool = True
    # The maximum delay between retries (in seconds)
    max_retry_delay: float = 30.0
    # The maximum total size of a batch (for SIZE_BASED strategy)
    max_batch_total_size: Optional[int] = None
    # The function to calculate the size of an item (for SIZE_BASED strategy)
    size_calculator: Optional[Callable[[T], int]] = None
    # The target processing time per batch (for ADAPTIVE strategy)
    target_processing_time: float = 0.5
    # The function to get the priority of an item (for PRIORITY strategy)
    priority_calculator: Optional[Callable[[T], int]] = None
    # Custom batching function (for CUSTOM strategy)
    custom_batcher: Optional[Callable[[List[T], "BatchConfig"], List[List[T]]]] = None


class BatchProcessor(Generic[T, R], ABC):
    """Base class for batch processors.

    This class provides the foundation for implementing batch processors
    that can process items in batches for improved performance.
    """

    def __init__(self, config: Optional[BatchConfig] = None):
        """Initialize the batch processor.

        Args:
            config: The batch configuration
        """
        self.config = config or BatchConfig()
        self._processing_times: List[float] = []
        self._batch_sizes: List[int] = []
        self._current_batch_size = self.config.min_batch_size

    @abstractmethod
    async def process_batch(self, batch: List[T]) -> List[R]:
        """Process a batch of items.

        Args:
            batch: The batch of items to process

        Returns:
            The processed results
        """
        pass

    async def process_items(self, items: Iterable[T]) -> List[R]:
        """Process items in batches.

        Args:
            items: The items to process

        Returns:
            The processed results

        Raises:
            PepperPyError: If processing fails
        """
        try:
            # Convert items to a list if it's not already
            items_list = list(items)
            if not items_list:
                return []

            # Create batches based on the strategy
            batches = self._create_batches(items_list)
            results: List[R] = []

            # Process each batch
            for batch in batches:
                batch_results = await self._process_batch_with_retry(batch)
                results.extend(batch_results)

            return results

        except Exception as e:
            raise PepperPyError(f"Error processing items in batches: {e}")

    @profile(level="debug")
    async def _process_batch_with_retry(self, batch: List[T]) -> List[R]:
        """Process a batch with retry logic.

        Args:
            batch: The batch to process

        Returns:
            The processed results

        Raises:
            PepperPyError: If processing fails after all retries
        """
        retries = 0
        last_error = None

        while retries <= self.config.max_retries:
            try:
                # Process the batch and measure the time
                start_time = time.time()
                results = await self.process_batch(batch)
                processing_time = time.time() - start_time

                # Update processing statistics
                self._update_statistics(len(batch), processing_time)

                return results

            except Exception as e:
                retries += 1
                last_error = e
                logger.warning(
                    f"Batch processing failed (attempt {retries}/{self.config.max_retries + 1}): {e}"
                )

                if retries <= self.config.max_retries:
                    # Calculate retry delay
                    delay = self._calculate_retry_delay(retries)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    # All retries exhausted
                    raise PepperPyError(
                        f"Batch processing failed after {retries} attempts: {last_error}"
                    ) from last_error

        # This should never be reached, but just in case
        raise PepperPyError("Unexpected error in batch processing retry logic")

    def _calculate_retry_delay(self, retry_count: int) -> float:
        """Calculate the delay before the next retry.

        Args:
            retry_count: The current retry count

        Returns:
            The delay before the next retry
        """
        if self.config.exponential_backoff:
            # Use exponential backoff
            delay = self.config.retry_delay * (2 ** (retry_count - 1))
            # Add jitter to avoid thundering herd problem
            delay = delay * (0.5 + 0.5 * (hash(str(time.time())) % 1000) / 1000)
            # Cap at max retry delay
            return cast(float, min(delay, self.config.max_retry_delay))
        else:
            # Use fixed delay
            return cast(float, self.config.retry_delay)

    def _update_statistics(self, batch_size: int, processing_time: float) -> None:
        """Update processing statistics.

        Args:
            batch_size: The size of the processed batch
            processing_time: The time taken to process the batch
        """
        self._processing_times.append(processing_time)
        self._batch_sizes.append(batch_size)

        # Keep only the last 10 processing times
        if len(self._processing_times) > 10:
            self._processing_times.pop(0)
            self._batch_sizes.pop(0)

        # Update batch size for adaptive strategy
        if self.config.strategy == BatchingStrategy.ADAPTIVE:
            self._update_adaptive_batch_size()

    def _update_adaptive_batch_size(self) -> None:
        """Update the batch size for adaptive strategy."""
        if not self._processing_times:
            return

        # Calculate average processing time per item
        total_items = sum(self._batch_sizes)
        total_time = sum(self._processing_times)
        if total_items == 0 or total_time == 0:
            return

        avg_time_per_item = total_time / total_items

        # Calculate new batch size based on target processing time
        target_batch_size = int(self.config.target_processing_time / avg_time_per_item)

        # Ensure batch size is within limits
        target_batch_size = max(self.config.min_batch_size, target_batch_size)
        target_batch_size = min(self.config.max_batch_size, target_batch_size)

        # Gradually adjust batch size to avoid oscillation
        adjustment_factor = 0.2
        self._current_batch_size = int(
            self._current_batch_size * (1 - adjustment_factor)
            + target_batch_size * adjustment_factor
        )
        self._current_batch_size = max(
            self.config.min_batch_size, self._current_batch_size
        )
        self._current_batch_size = min(
            self.config.max_batch_size, self._current_batch_size
        )

        logger.debug(
            f"Adaptive batch size updated: {self._current_batch_size} "
            f"(avg time per item: {avg_time_per_item:.6f}s, "
            f"target time: {self.config.target_processing_time:.2f}s)"
        )

    def _create_batches(self, items: List[T]) -> List[List[T]]:
        """Create batches based on the configured strategy.

        Args:
            items: The items to batch

        Returns:
            The created batches
        """
        if not items:
            return []

        if self.config.strategy == BatchingStrategy.FIXED_SIZE:
            return self._create_fixed_size_batches(items)
        elif self.config.strategy == BatchingStrategy.ADAPTIVE:
            return self._create_adaptive_batches(items)
        elif self.config.strategy == BatchingStrategy.TIME_WINDOW:
            return self._create_time_window_batches(items)
        elif self.config.strategy == BatchingStrategy.SIZE_BASED:
            return self._create_size_based_batches(items)
        elif self.config.strategy == BatchingStrategy.PRIORITY:
            return self._create_priority_batches(items)
        elif self.config.strategy == BatchingStrategy.CUSTOM:
            return self._create_custom_batches(items)
        else:
            # Default to fixed size
            return self._create_fixed_size_batches(items)

    def _create_fixed_size_batches(self, items: List[T]) -> List[List[T]]:
        """Create fixed-size batches.

        Args:
            items: The items to batch

        Returns:
            The created batches
        """
        batch_size = self.config.max_batch_size
        return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]

    def _create_adaptive_batches(self, items: List[T]) -> List[List[T]]:
        """Create batches with adaptive size.

        Args:
            items: The items to batch

        Returns:
            The created batches
        """
        batch_size = self._current_batch_size
        return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]

    def _create_time_window_batches(self, items: List[T]) -> List[List[T]]:
        """Create batches based on time windows.

        This is a simplified implementation that just uses fixed-size batches,
        as true time-window batching requires a different processing model.

        Args:
            items: The items to batch

        Returns:
            The created batches
        """
        # For simplicity, we just use fixed-size batches
        # In a real implementation, this would use a different processing model
        return self._create_fixed_size_batches(items)

    def _create_size_based_batches(self, items: List[T]) -> List[List[T]]:
        """Create batches based on total size.

        Args:
            items: The items to batch

        Returns:
            The created batches
        """
        if not self.config.size_calculator or not self.config.max_batch_total_size:
            # Fall back to fixed size if size calculator or max size is not provided
            return self._create_fixed_size_batches(items)

        batches: List[List[T]] = []
        current_batch: List[T] = []
        current_size = 0

        for item in items:
            item_size = self.config.size_calculator(item)
            if (
                current_batch
                and current_size + item_size > self.config.max_batch_total_size
                or len(current_batch) >= self.config.max_batch_size
            ):
                # Current batch is full, start a new one
                batches.append(current_batch)
                current_batch = [item]
                current_size = item_size
            else:
                # Add to current batch
                current_batch.append(item)
                current_size += item_size

        # Add the last batch if it's not empty
        if current_batch:
            batches.append(current_batch)

        return batches

    def _create_priority_batches(self, items: List[T]) -> List[List[T]]:
        """Create batches based on priority.

        Args:
            items: The items to batch

        Returns:
            The created batches
        """
        if not self.config.priority_calculator:
            # Fall back to fixed size if priority calculator is not provided
            return self._create_fixed_size_batches(items)

        # Sort items by priority (higher priority first)
        sorted_items = sorted(items, key=self.config.priority_calculator, reverse=True)

        # Create fixed-size batches from the sorted items
        return self._create_fixed_size_batches(sorted_items)

    def _create_custom_batches(self, items: List[T]) -> List[List[T]]:
        """Create batches using a custom batching function.

        Args:
            items: The items to batch

        Returns:
            The created batches
        """
        if not self.config.custom_batcher:
            # Fall back to fixed size if custom batcher is not provided
            return self._create_fixed_size_batches(items)

        return self.config.custom_batcher(items, self.config)


class KeyedBatchProcessor(BatchProcessor[Tuple[K, T], Tuple[K, R]]):
    """Batch processor that preserves keys.

    This class extends BatchProcessor to handle items with associated keys,
    preserving the mapping between keys and results.
    """

    @abstractmethod
    async def process_keyed_batch(self, batch: Dict[K, T]) -> Dict[K, R]:
        """Process a batch of keyed items.

        Args:
            batch: The batch of keyed items to process

        Returns:
            The processed results with keys
        """
        pass

    async def process_batch(self, batch: List[Tuple[K, T]]) -> List[Tuple[K, R]]:
        """Process a batch of key-value tuples.

        Args:
            batch: The batch of key-value tuples to process

        Returns:
            The processed results as key-value tuples
        """
        # Convert list of tuples to dictionary
        batch_dict = {key: value for key, value in batch}

        # Process the batch
        results_dict = await self.process_keyed_batch(batch_dict)

        # Convert back to list of tuples
        return [(key, results_dict[key]) for key in batch_dict.keys()]

    async def process_dict(self, items: Dict[K, T]) -> Dict[K, R]:
        """Process a dictionary of items.

        Args:
            items: The dictionary of items to process

        Returns:
            The processed results as a dictionary
        """
        # Convert dictionary to list of tuples
        items_list = [(key, value) for key, value in items.items()]

        # Process the items
        results_list = await self.process_items(items_list)

        # Convert back to dictionary
        return {key: value for key, value in results_list}


def create_batches(
    items: List[T], batch_size: int, min_batch_size: Optional[int] = None
) -> List[List[T]]:
    """Create batches of items with a fixed size.

    Args:
        items: The items to batch
        batch_size: The maximum size of each batch
        min_batch_size: The minimum size of the last batch (if None, no minimum)

    Returns:
        The created batches
    """
    if not items:
        return []

    batches = [items[i : i + batch_size] for i in range(0, len(items), batch_size)]

    # Ensure the last batch meets the minimum size
    if min_batch_size is not None and batches and len(batches[-1]) < min_batch_size:
        # If we have only one batch and it's smaller than min_batch_size, keep it
        if len(batches) == 1:
            return batches

        # Otherwise, distribute the last batch to previous batches
        last_batch = batches.pop()
        while last_batch and batches:
            batches[-1].append(last_batch.pop(0))
            if not last_batch:
                break
            # Rotate batches to distribute evenly
            batches = [batches[-1]] + batches[:-1]

        # If there are still items left, create a new batch
        if last_batch:
            batches.append(last_batch)

    return batches


async def process_in_batches(
    items: List[T],
    processor: Callable[[List[T]], Awaitable[R]],
    batch_size: int = 100,
    concurrency: int = 1,
) -> List[R]:
    """Process items in batches.

    Args:
        items: The items to process
        processor: The function to process each batch
        batch_size: The maximum batch size
        concurrency: The maximum number of concurrent batch processing tasks

    Returns:
        The processed results
    """
    if not items:
        return []

    # Create batches
    batches = create_batches(items, batch_size)
    results: List[R] = []

    if concurrency <= 1:
        # Process batches sequentially
        for batch in batches:
            result = cast(R, await processor(batch))
            results.append(result)
    else:
        # Process batches concurrently with limited concurrency
        semaphore = asyncio.Semaphore(concurrency)

        async def process_batch(batch: List[T]) -> R:
            async with semaphore:
                return cast(R, await processor(batch))

        # Create tasks for all batches
        tasks = [process_batch(batch) for batch in batches]
        results = await asyncio.gather(*tasks)

    return results


async def process_keyed_items_in_batches(
    items: Dict[K, T],
    processor: Callable[[Dict[K, T]], Awaitable[Dict[K, R]]],
    batch_size: int = 100,
    concurrency: int = 1,
) -> Dict[K, R]:
    """Process keyed items in batches.

    Args:
        items: The keyed items to process
        processor: The function to process each batch
        batch_size: The maximum batch size
        concurrency: The maximum number of concurrent batch processing tasks

    Returns:
        The processed results
    """
    if not items:
        return {}

    # Create batches of keys
    key_batches = create_batches(list(items.keys()), batch_size)
    results: Dict[K, R] = {}

    if concurrency <= 1:
        # Process batches sequentially
        for key_batch in key_batches:
            batch_items = {key: items[key] for key in key_batch}
            batch_results = cast(Dict[K, R], await processor(batch_items))
            results.update(batch_results)
    else:
        # Process batches concurrently with limited concurrency
        semaphore = asyncio.Semaphore(concurrency)

        async def process_batch(key_batch: List[K]) -> Dict[K, R]:
            async with semaphore:
                batch_items = {key: items[key] for key in key_batch}
                return cast(Dict[K, R], await processor(batch_items))

        # Create tasks for all batches
        tasks = [process_batch(key_batch) for key_batch in key_batches]
        batch_results_list = await asyncio.gather(*tasks)

        # Combine results
        for batch_results in batch_results_list:
            results.update(batch_results)

    return results
