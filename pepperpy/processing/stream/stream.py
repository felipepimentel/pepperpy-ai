"""Stream processing implementation for data pipelines."""

import asyncio
import logging
from datetime import datetime
from typing import Generic, TypeVar

from pepperpy.core.errors import ProcessingError
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.metrics import MetricsCollector
from pepperpy.core.pipeline.base import (
    DataItem,
    DataProcessor,
)

T = TypeVar("T")  # Input type
U = TypeVar("U")  # Output type


class StreamProcessor(Lifecycle, Generic[T, U]):
    """Stream processor for continuous data processing.

    Features:
    - Asynchronous stream processing
    - Backpressure handling
    - Error recovery
    - Performance monitoring
    - Batch optimization
    """

    def __init__(
        self,
        name: str,
        processor: DataProcessor[T, U],
        buffer_size: int = 1000,
        batch_size: int = 100,
        metrics: MetricsCollector | None = None,
    ) -> None:
        """Initialize the stream processor.

        Args:
            name: Processor name
            processor: Data processor instance
            buffer_size: Maximum items in buffer
            batch_size: Items to process in batch
            metrics: Optional metrics collector
        """
        super().__init__()
        self.name = name
        self._processor = processor
        self._buffer_size = buffer_size
        self._batch_size = batch_size
        self._metrics = metrics
        self._queue: asyncio.Queue[DataItem[T]] = asyncio.Queue(maxsize=buffer_size)
        self._logger = logging.getLogger(__name__)

        # Initialize metrics
        if metrics:
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
            self._queue_size = metrics.gauge(f"{name}_queue_size", {"processor": name})

    async def _initialize(self) -> None:
        """Initialize the stream processor.

        This starts the processor and creates processing tasks.
        """
        self._logger.info(f"Initializing stream processor: {self.name}")
        await self._processor.initialize()
        self._processing_task = asyncio.create_task(self._process_stream())

    async def _cleanup(self) -> None:
        """Clean up processor resources.

        This stops processing and cleans up resources.
        """
        self._logger.info(f"Cleaning up stream processor: {self.name}")
        if hasattr(self, "_processing_task"):
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

        await self._processor.stop()
        self._queue = asyncio.Queue(maxsize=self._buffer_size)

    async def process(self, item: DataItem[T]) -> None:
        """Add an item for processing.

        Args:
            item: Data item to process

        Raises:
            ProcessingError: If processing fails
            StateError: If processor is not running
        """
        if not self.is_running():
            raise ProcessingError("Processor is not running")

        try:
            await self._queue.put(item)
            if self._metrics:
                self._queue_size.set(self._queue.qsize())

        except Exception as e:
            self._logger.error(f"Error queueing item: {e}", exc_info=True)
            if self._metrics:
                self._processing_errors.inc()
            raise ProcessingError(f"Failed to queue item: {e}")

    async def _process_stream(self) -> None:
        """Background task for processing queued items."""
        batch: list[DataItem[T]] = []

        while True:
            try:
                # Get items for batch
                while len(batch) < self._batch_size:
                    try:
                        item = await asyncio.wait_for(self._queue.get(), timeout=0.1)
                        batch.append(item)
                    except TimeoutError:
                        break

                if not batch:
                    continue

                # Process batch
                start_time = datetime.now()
                results = await self._processor.process_batch(batch)
                processing_time = (datetime.now() - start_time).total_seconds()

                # Update metrics
                if self._metrics:
                    self._processed_items.inc(len(results))
                    self._processing_time.observe(processing_time)
                    self._queue_size.set(self._queue.qsize())

                # Clear batch
                batch = []

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error processing batch: {e}", exc_info=True)
                if self._metrics:
                    self._processing_errors.inc()
                batch = []  # Clear failed batch
                await asyncio.sleep(1)  # Brief pause before retry

    async def get_metrics(self) -> dict[str, float]:
        """Get processor metrics.

        Returns:
            Dictionary of metric values
        """
        if not self._metrics:
            return {}

        return {
            "processed_items": self._processed_items.value,
            "processing_errors": self._processing_errors.value,
            "queue_size": self._queue_size.value,
            "avg_processing_time": (
                self._processing_time.sum / self._processing_time.count
                if self._processing_time.count > 0
                else 0.0
            ),
        }
