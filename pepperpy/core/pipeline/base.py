"""Base data pipeline components for stream and batch processing."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar, AsyncIterator
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging

from pepperpy.core.errors import ValidationError, ProcessingError
from pepperpy.core.lifecycle import Lifecycle
from pepperpy.core.metrics import MetricsCollector

T = TypeVar("T")  # Input type
U = TypeVar("U")  # Output type

@dataclass
class DataItem(Generic[T]):
    """Container for data items in the pipeline."""
    id: str
    data: T
    metadata: Dict[str, Any]
    timestamp: datetime
    source: str
    schema_version: str

@dataclass
class ProcessingResult(Generic[U]):
    """Result of data processing."""
    id: str
    data: U
    metadata: Dict[str, Any]
    timestamp: datetime
    processing_time: float
    status: str
    errors: List[str]

class DataValidator(ABC, Generic[T]):
    """Base class for data validators."""

    @abstractmethod
    async def validate(self, item: DataItem[T]) -> List[str]:
        """Validate a data item.
        
        Args:
            item: Data item to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        pass

class DataTransformer(ABC, Generic[T, U]):
    """Base class for data transformers."""

    @abstractmethod
    async def transform(self, item: DataItem[T]) -> U:
        """Transform a data item.
        
        Args:
            item: Data item to transform
            
        Returns:
            Transformed data
            
        Raises:
            ProcessingError: If transformation fails
        """
        pass

class DataProcessor(Lifecycle, Generic[T, U]):
    """Base class for data processors.
    
    This class provides core functionality for processing data items:
    - Data validation
    - Transformation
    - Error handling
    - Metrics collection
    """

    def __init__(
        self,
        name: str,
        validator: Optional[DataValidator[T]] = None,
        transformer: Optional[DataTransformer[T, U]] = None,
        metrics: Optional[MetricsCollector] = None,
        batch_size: int = 100,
        processing_timeout: float = 30.0
    ) -> None:
        """Initialize the data processor.
        
        Args:
            name: Processor name
            validator: Optional data validator
            transformer: Optional data transformer
            metrics: Optional metrics collector
            batch_size: Batch processing size
            processing_timeout: Processing timeout in seconds
        """
        super().__init__()
        self.name = name
        self._validator = validator
        self._transformer = transformer
        self._metrics = metrics or MetricsCollector()
        self._batch_size = batch_size
        self._processing_timeout = processing_timeout
        self._logger = logging.getLogger(f"processor.{name}")
        
        # Initialize metrics
        self._processed_items = self._metrics.counter(
            "processor_items_total",
            labels={"processor": name}
        )
        self._processing_errors = self._metrics.counter(
            "processor_errors_total",
            labels={"processor": name}
        )
        self._processing_time = self._metrics.histogram(
            "processor_time_seconds",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            labels={"processor": name}
        )
        self._batch_size_metric = self._metrics.gauge(
            "processor_batch_size",
            labels={"processor": name}
        )

    async def process_item(self, item: DataItem[T]) -> ProcessingResult[U]:
        """Process a single data item.
        
        Args:
            item: Data item to process
            
        Returns:
            Processing result
            
        Raises:
            ValidationError: If validation fails
            ProcessingError: If processing fails
        """
        start_time = datetime.now()
        errors: List[str] = []
        
        try:
            # Validate data
            if self._validator:
                validation_errors = await self._validator.validate(item)
                if validation_errors:
                    errors.extend(validation_errors)
                    raise ValidationError("\n".join(validation_errors))
            
            # Transform data
            if self._transformer:
                result = await self._transformer.transform(item)
            else:
                result = item.data  # type: ignore
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self._processing_time.observe(processing_time)
            self._processed_items.inc()
            
            return ProcessingResult(
                id=item.id,
                data=result,
                metadata=item.metadata,
                timestamp=datetime.now(),
                processing_time=processing_time,
                status="success",
                errors=errors
            )
            
        except Exception as e:
            self._processing_errors.inc()
            processing_time = (datetime.now() - start_time).total_seconds()
            errors.append(str(e))
            
            return ProcessingResult(
                id=item.id,
                data=item.data,  # type: ignore
                metadata=item.metadata,
                timestamp=datetime.now(),
                processing_time=processing_time,
                status="error",
                errors=errors
            )

    async def process_batch(
        self,
        items: List[DataItem[T]]
    ) -> List[ProcessingResult[U]]:
        """Process a batch of data items.
        
        Args:
            items: Data items to process
            
        Returns:
            List of processing results
        """
        self._batch_size_metric.set(len(items))
        
        tasks = [
            asyncio.create_task(self.process_item(item))
            for item in items
        ]
        
        try:
            results = await asyncio.gather(*tasks)
            return list(results)
        except Exception as e:
            self._logger.error(f"Batch processing failed: {e}", exc_info=True)
            self._processing_errors.inc()
            raise ProcessingError(f"Batch processing failed: {e}")

    async def process_stream(
        self,
        stream: AsyncIterator[DataItem[T]]
    ) -> AsyncIterator[ProcessingResult[U]]:
        """Process a stream of data items.
        
        Args:
            stream: Input data stream
            
        Yields:
            Processing results
        """
        batch: List[DataItem[T]] = []
        
        try:
            async for item in stream:
                batch.append(item)
                
                if len(batch) >= self._batch_size:
                    results = await self.process_batch(batch)
                    for result in results:
                        yield result
                    batch = []
            
            # Process remaining items
            if batch:
                results = await self.process_batch(batch)
                for result in results:
                    yield result
                    
        except Exception as e:
            self._logger.error(f"Stream processing failed: {e}", exc_info=True)
            self._processing_errors.inc()
            raise ProcessingError(f"Stream processing failed: {e}")

    async def _initialize(self) -> None:
        """Initialize the processor."""
        self._logger.info(f"Initialized processor: {self.name}")

    async def _cleanup(self) -> None:
        """Clean up the processor."""
        self._logger.info(f"Cleaned up processor: {self.name}")

class Pipeline(Lifecycle, Generic[T, U]):
    """Data processing pipeline.
    
    This class manages a sequence of data processors and handles:
    - Data flow control
    - Error handling
    - Metrics aggregation
    - Resource management
    """

    def __init__(
        self,
        name: str,
        processors: List[DataProcessor],
        metrics: Optional[MetricsCollector] = None
    ) -> None:
        """Initialize the pipeline.
        
        Args:
            name: Pipeline name
            processors: List of data processors
            metrics: Optional metrics collector
        """
        super().__init__()
        self.name = name
        self._processors = processors
        self._metrics = metrics or MetricsCollector()
        self._logger = logging.getLogger(f"pipeline.{name}")
        
        # Initialize metrics
        self._pipeline_throughput = self._metrics.counter(
            "pipeline_items_total",
            labels={"pipeline": name}
        )
        self._pipeline_errors = self._metrics.counter(
            "pipeline_errors_total",
            labels={"pipeline": name}
        )
        self._pipeline_time = self._metrics.histogram(
            "pipeline_time_seconds",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            labels={"pipeline": name}
        )

    async def process(
        self,
        item: DataItem[T]
    ) -> ProcessingResult[U]:
        """Process a data item through the pipeline.
        
        Args:
            item: Input data item
            
        Returns:
            Final processing result
            
        Raises:
            ProcessingError: If processing fails
        """
        start_time = datetime.now()
        current_item = item
        
        try:
            for processor in self._processors:
                result = await processor.process_item(current_item)
                if result.status == "error":
                    self._pipeline_errors.inc()
                    return result  # type: ignore
                current_item = DataItem(  # type: ignore
                    id=result.id,
                    data=result.data,
                    metadata=result.metadata,
                    timestamp=result.timestamp,
                    source=processor.name,
                    schema_version=item.schema_version
                )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self._pipeline_time.observe(processing_time)
            self._pipeline_throughput.inc()
            
            return ProcessingResult(  # type: ignore
                id=current_item.id,
                data=current_item.data,
                metadata=current_item.metadata,
                timestamp=datetime.now(),
                processing_time=processing_time,
                status="success",
                errors=[]
            )
            
        except Exception as e:
            self._pipeline_errors.inc()
            self._logger.error(f"Pipeline processing failed: {e}", exc_info=True)
            raise ProcessingError(f"Pipeline processing failed: {e}")

    async def process_batch(
        self,
        items: List[DataItem[T]]
    ) -> List[ProcessingResult[U]]:
        """Process a batch of items through the pipeline.
        
        Args:
            items: Input data items
            
        Returns:
            List of processing results
        """
        tasks = [
            asyncio.create_task(self.process(item))
            for item in items
        ]
        
        try:
            results = await asyncio.gather(*tasks)
            return list(results)
        except Exception as e:
            self._logger.error(f"Pipeline batch processing failed: {e}", exc_info=True)
            raise ProcessingError(f"Pipeline batch processing failed: {e}")

    async def process_stream(
        self,
        stream: AsyncIterator[DataItem[T]]
    ) -> AsyncIterator[ProcessingResult[U]]:
        """Process a stream of items through the pipeline.
        
        Args:
            stream: Input data stream
            
        Yields:
            Processing results
        """
        try:
            async for item in stream:
                result = await self.process(item)
                yield result
                
        except Exception as e:
            self._logger.error(f"Pipeline stream processing failed: {e}", exc_info=True)
            raise ProcessingError(f"Pipeline stream processing failed: {e}")

    async def _initialize(self) -> None:
        """Initialize the pipeline.
        
        This method initializes all processors in the pipeline.
        """
        for processor in self._processors:
            await processor.initialize()
        self._logger.info(f"Initialized pipeline: {self.name}")

    async def _cleanup(self) -> None:
        """Clean up the pipeline.
        
        This method cleans up all processors in the pipeline.
        """
        for processor in self._processors:
            await processor.stop()
        self._logger.info(f"Cleaned up pipeline: {self.name}")