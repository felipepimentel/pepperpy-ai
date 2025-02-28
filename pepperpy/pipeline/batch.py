"""Batch processing implementation for data pipelines."""

import asyncio
import logging
from datetime import datetime
from typing import Generic, TypeVar

from pepperpy.core.errors import ProcessingError
from pepperpy.common.lifecycle import Lifecycle
from pepperpy.common.metrics import MetricsCollector
from pepperpy.common.pipeline.base import (
    DataItem,
    DataProcessor,
    ProcessingResult,
)

T = TypeVar("T")  # Input type
U = TypeVar("U")  # Output type


class BatchProcessor(Lifecycle, Generic[T, U]):
    """Batch processor for optimized data processing.

    Features:
    - Parallel processing
    - Memory optimization
    - Error handling
    - Performance monitoring
    - Resource management
    """

    def __init__(
        self,
        name: str,
        processor: DataProcessor[T, U],
        max_batch_size: int = 1000,
        parallel_batches: int = 4,
        metrics: MetricsCollector | None = None,
    ) -> None:
        """Initialize the batch processor.

        Args:
            name: Processor name
            processor: Data processor instance
            max_batch_size: Maximum items per batch
            parallel_batches: Number of parallel batches
            metrics: Optional metrics collector
        """
        super().__init__()
        self.name = name
        self._processor = processor
        self._max_batch_size = max_batch_size
        self._parallel_batches = parallel_batches
        self._metrics = metrics
        self._semaphore = asyncio.Semaphore(parallel_batches)
        self._logger = logging.getLogger(__name__)

        # Initialize metrics
        if metrics:
            self._processed_batches = metrics.counter(
                f"{name}_processed_batches", {"processor": name}
            )
            self._processed_items = metrics.counter(
                f"{name}_processed_items", {"processor": name}
            )
            self._processing_errors = metrics.counter(
                f"{name}_processing_errors", {"processor": name}
            )
            self._processing_time = metrics.histogram(
                f"{name}_processing_time",
                [0.1, 0.5, 1.0, 2.0, 5.0],
                {"processor": name},
            )
            self._batch_size = metrics.histogram(
                f"{name}_batch_size", [10, 50, 100, 500, 1000], {"processor": name}
            )

    async def _initialize(self) -> None:
        """Initialize the batch processor.

        This starts the processor and initializes resources.
        """
        self._logger.info(f"Initializing batch processor: {self.name}")
        await self._processor.initialize()

    async def _cleanup(self) -> None:
        """Clean up processor resources."""
        self._logger.info(f"Cleaning up batch processor: {self.name}")
        await self._processor.stop()

    async def process_batch(
        self, items: list[DataItem[T]]
    ) -> list[ProcessingResult[U]]:
        """Process a batch of items.

        Args:
            items: List of items to process

        Returns:
            List of processing results

        Raises:
            ProcessingError: If processing fails
            StateError: If processor is not running
        """
        if not self.is_running():
            raise ProcessingError("Processor is not running")

        if not items:
            return []

        try:
            # Split into optimal batches
            batches = self._split_batch(items)

            # Process batches in parallel
            async with self._semaphore:
                start_time = datetime.now()

                # Create tasks for each batch
                tasks = [self._processor.process_batch(batch) for batch in batches]

                # Wait for all batches
                results = []
                for batch_results in await asyncio.gather(*tasks):
                    results.extend(batch_results)

                # Update metrics
                if self._metrics:
                    processing_time = (datetime.now() - start_time).total_seconds()
                    self._processed_batches.inc(len(batches))
                    self._processed_items.inc(len(results))
                    self._processing_time.observe(processing_time)
                    self._batch_size.observe(len(items))

                return results

        except Exception as e:
            self._logger.error(f"Error processing batch: {e}", exc_info=True)
            if self._metrics:
                self._processing_errors.inc()
            raise ProcessingError(f"Failed to process batch: {e}")

    def _split_batch(self, items: list[DataItem[T]]) -> list[list[DataItem[T]]]:
        """Split items into optimal batch sizes.

        Args:
            items: Items to split

        Returns:
            List of batches
        """
        if len(items) <= self._max_batch_size:
            return [items]

        batches = []
        for i in range(0, len(items), self._max_batch_size):
            batch = items[i : i + self._max_batch_size]
            batches.append(batch)

        return batches

    async def get_metrics(self) -> dict[str, float]:
        """Get processor metrics.

        Returns:
            Dictionary of metric values
        """
        if not self._metrics:
            return {}

        return {
            "processed_batches": self._processed_batches.value,
            "processed_items": self._processed_items.value,
            "processing_errors": self._processing_errors.value,
            "avg_processing_time": (
                self._processing_time.sum / self._processing_time.count
                if self._processing_time.count > 0
                else 0.0
            ),
            "avg_batch_size": (
                self._batch_size.sum / self._batch_size.count
                if self._batch_size.count > 0
                else 0.0
            ),
        }
