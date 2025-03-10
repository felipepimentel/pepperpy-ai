"""Core functionality for streaming in PepperPy.

This module provides the core functionality for streaming in PepperPy,
including stream handlers, processors, and consumers.
"""

import json
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    TypeVar,
    Union,
    cast,
)

from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for stream data types
T = TypeVar("T")
U = TypeVar("U")
R = TypeVar("R")  # For return types in stream functions


class StreamEvent(str, Enum):
    """Types of stream events."""

    START = "start"
    DATA = "data"
    END = "end"
    ERROR = "error"


class StreamChunk(Generic[T]):
    """A chunk of data in a stream.

    A stream chunk represents a piece of data in a stream, along with metadata
    about the chunk.
    """

    def __init__(
        self,
        data: T,
        event: StreamEvent = StreamEvent.DATA,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ):
        """Initialize a stream chunk.

        Args:
            data: The data in the chunk
            event: The event type of the chunk
            metadata: Additional metadata for the chunk
            timestamp: The timestamp of the chunk (defaults to current time)
        """
        self.data = data
        self.event = event
        self.metadata = metadata or {}
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the stream chunk to a dictionary.

        Returns:
            The stream chunk as a dictionary
        """
        return {
            "data": self.data,
            "event": self.event.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamChunk[Any]":
        """Create a stream chunk from a dictionary.

        Args:
            data: The dictionary to create the stream chunk from

        Returns:
            The created stream chunk
        """
        return cls(
            data=data["data"],
            event=StreamEvent(data["event"]),
            metadata=data["metadata"],
            timestamp=data["timestamp"],
        )

    @classmethod
    def start(cls, metadata: Optional[Dict[str, Any]] = None) -> "StreamChunk[Any]":
        """Create a start event chunk.

        Args:
            metadata: Additional metadata for the chunk

        Returns:
            The created stream chunk
        """
        # Using cast to satisfy the type checker
        return cast(
            StreamChunk[Any],
            cls(
                data=None,  # type: ignore
                event=StreamEvent.START,
                metadata=metadata,
            ),
        )

    @classmethod
    def end(cls, metadata: Optional[Dict[str, Any]] = None) -> "StreamChunk[Any]":
        """Create an end event chunk.

        Args:
            metadata: Additional metadata for the chunk

        Returns:
            The created stream chunk
        """
        # Using cast to satisfy the type checker
        return cast(
            StreamChunk[Any],
            cls(
                data=None,  # type: ignore
                event=StreamEvent.END,
                metadata=metadata,
            ),
        )

    @classmethod
    def error(
        cls, error: Union[str, Exception], metadata: Optional[Dict[str, Any]] = None
    ) -> "StreamChunk[str]":
        """Create an error event chunk.

        Args:
            error: The error message or exception
            metadata: Additional metadata for the chunk

        Returns:
            The created stream chunk
        """
        error_message = str(error)
        metadata = metadata or {}

        if isinstance(error, Exception):
            metadata["exception_type"] = type(error).__name__

        # Using cast to satisfy the type checker
        return cast(
            StreamChunk[str],
            cls(
                data=error_message,  # type: ignore
                event=StreamEvent.ERROR,
                metadata=metadata,
            ),
        )


class StreamProcessor(Generic[T, U], ABC):
    """Base class for stream processors.

    A stream processor transforms chunks from one type to another.
    """

    @abstractmethod
    async def process(self, chunk: StreamChunk[T]) -> StreamChunk[U]:
        """Process a stream chunk.

        Args:
            chunk: The chunk to process

        Returns:
            The processed chunk
        """
        pass

    async def process_stream(
        self, stream: AsyncGenerator[StreamChunk[T], None]
    ) -> AsyncGenerator[StreamChunk[U], None]:
        """Process a stream of chunks.

        Args:
            stream: The stream to process

        Yields:
            The processed chunks
        """
        async for chunk in stream:
            yield await self.process(chunk)


class StreamConsumer(Generic[T], ABC):
    """Base class for stream consumers.

    A stream consumer consumes chunks from a stream.
    """

    @abstractmethod
    async def consume(self, chunk: StreamChunk[T]) -> None:
        """Consume a stream chunk.

        Args:
            chunk: The chunk to consume
        """
        pass

    async def consume_stream(
        self, stream: AsyncGenerator[StreamChunk[T], None]
    ) -> None:
        """Consume a stream of chunks.

        Args:
            stream: The stream to consume
        """
        async for chunk in stream:
            await self.consume(chunk)


class StreamProducer(Generic[T], ABC):
    """Base class for stream producers.

    A stream producer generates chunks for a stream.
    """

    @abstractmethod
    async def produce(self) -> AsyncGenerator[StreamChunk[T], None]:
        """Produce a stream of chunks.

        Yields:
            The produced chunks
        """
        pass


class StreamHandler(Generic[T]):
    """Handler for streams.

    A stream handler manages the flow of chunks in a stream, including
    processing, consuming, and producing.
    """

    def __init__(self):
        """Initialize a stream handler."""
        self.processors: List[StreamProcessor] = []
        self.consumers: List[StreamConsumer] = []

    def add_processor(self, processor: StreamProcessor) -> "StreamHandler[T]":
        """Add a processor to the handler.

        Args:
            processor: The processor to add

        Returns:
            The stream handler
        """
        self.processors.append(processor)
        return self

    def add_consumer(self, consumer: StreamConsumer) -> "StreamHandler[T]":
        """Add a consumer to the handler.

        Args:
            consumer: The consumer to add

        Returns:
            The stream handler
        """
        self.consumers.append(consumer)
        return self

    async def handle(
        self, stream: AsyncGenerator[StreamChunk[T], None]
    ) -> AsyncGenerator[StreamChunk[Any], None]:
        """Handle a stream.

        Args:
            stream: The stream to handle

        Yields:
            The handled chunks
        """
        # Process the stream through each processor
        processed_stream = stream
        for processor in self.processors:
            processed_stream = processor.process_stream(processed_stream)

        # Consume the stream with each consumer
        async def consume_all():
            async for chunk in processed_stream:
                for consumer in self.consumers:
                    await consumer.consume(chunk)
                yield chunk

        return consume_all()


class CallbackStreamConsumer(StreamConsumer[T]):
    """Stream consumer that calls a callback function for each chunk.

    This consumer is useful for integrating with callback-based APIs.
    """

    def __init__(self, callback: Callable[[StreamChunk[T]], None]):
        """Initialize a callback stream consumer.

        Args:
            callback: The callback function to call for each chunk
        """
        self.callback = callback

    async def consume(self, chunk: StreamChunk[T]) -> None:
        """Consume a stream chunk.

        Args:
            chunk: The chunk to consume
        """
        self.callback(chunk)


class LoggingStreamConsumer(StreamConsumer[T]):
    """Stream consumer that logs each chunk.

    This consumer is useful for debugging and monitoring streams.
    """

    def __init__(self, logger_name: Optional[str] = None, level: str = "info"):
        """Initialize a logging stream consumer.

        Args:
            logger_name: The name of the logger to use, or None to use the module logger
            level: The log level to use
        """
        self.logger = get_logger(logger_name) if logger_name else logger
        self.level = level.lower()

    async def consume(self, chunk: StreamChunk[T]) -> None:
        """Consume a stream chunk.

        Args:
            chunk: The chunk to consume
        """
        message = f"Stream chunk: {chunk.event.value}"

        if chunk.event == StreamEvent.DATA:
            message += f", data: {chunk.data}"
        elif chunk.event == StreamEvent.ERROR:
            message += f", error: {chunk.data}"

        if self.level == "debug":
            self.logger.debug(message)
        elif self.level == "info":
            self.logger.info(message)
        elif self.level == "warning":
            self.logger.warning(message)
        elif self.level == "error":
            self.logger.error(message)
        elif self.level == "critical":
            self.logger.critical(message)


class BufferedStreamConsumer(StreamConsumer[T]):
    """Stream consumer that buffers chunks.

    This consumer is useful for collecting all chunks in a stream.
    """

    def __init__(self):
        """Initialize a buffered stream consumer."""
        self.buffer: List[StreamChunk[T]] = []

    async def consume(self, chunk: StreamChunk[T]) -> None:
        """Consume a stream chunk.

        Args:
            chunk: The chunk to consume
        """
        self.buffer.append(chunk)

    def get_buffer(self) -> List[StreamChunk[T]]:
        """Get the buffer.

        Returns:
            The buffer
        """
        return self.buffer

    def clear_buffer(self) -> None:
        """Clear the buffer."""
        self.buffer.clear()


class JsonStreamProcessor(StreamProcessor[Dict[str, Any], str]):
    """Stream processor that converts dictionary chunks to JSON strings.

    This processor is useful for serializing chunks for transmission.
    """

    async def process(self, chunk: StreamChunk[Dict[str, Any]]) -> StreamChunk[str]:
        """Process a stream chunk.

        Args:
            chunk: The chunk to process

        Returns:
            The processed chunk
        """
        if chunk.event == StreamEvent.DATA and chunk.data is not None:
            json_data = json.dumps(chunk.data)
            return StreamChunk(
                data=json_data,
                event=chunk.event,
                metadata=chunk.metadata,
                timestamp=chunk.timestamp,
            )

        # For non-data events or None data, create a chunk with None or JSON string
        data_str = None if chunk.data is None else json.dumps(chunk.data)
        return cast(
            StreamChunk[str],
            StreamChunk(
                data=data_str,  # type: ignore
                event=chunk.event,
                metadata=chunk.metadata,
                timestamp=chunk.timestamp,
            ),
        )


class TextStreamProcessor(StreamProcessor[Any, str]):
    """Stream processor that converts chunks to strings.

    This processor is useful for converting chunks to a human-readable format.
    """

    async def process(self, chunk: StreamChunk[Any]) -> StreamChunk[str]:
        """Process a stream chunk.

        Args:
            chunk: The chunk to process

        Returns:
            The processed chunk
        """
        if chunk.event == StreamEvent.DATA and chunk.data is not None:
            text_data = str(chunk.data)
            return StreamChunk(
                data=text_data,
                event=chunk.event,
                metadata=chunk.metadata,
                timestamp=chunk.timestamp,
            )

        # For non-data events or None data, create a chunk with None or string
        data_str = None if chunk.data is None else str(chunk.data)
        return cast(
            StreamChunk[str],
            StreamChunk(
                data=data_str,  # type: ignore
                event=chunk.event,
                metadata=chunk.metadata,
                timestamp=chunk.timestamp,
            ),
        )


class FilterStreamProcessor(StreamProcessor[T, T]):
    """Stream processor that filters chunks based on a predicate.

    This processor is useful for filtering out unwanted chunks.
    """

    def __init__(self, predicate: Callable[[StreamChunk[T]], bool]):
        """Initialize a filter stream processor.

        Args:
            predicate: The predicate function to use for filtering
        """
        self.predicate = predicate

    async def process(self, chunk: StreamChunk[T]) -> StreamChunk[T]:
        """Process a stream chunk.

        Args:
            chunk: The chunk to process

        Returns:
            The processed chunk

        Raises:
            StopAsyncIteration: If the chunk is filtered out
        """
        if self.predicate(chunk):
            return chunk

        raise StopAsyncIteration


class MapStreamProcessor(StreamProcessor[T, U]):
    """Stream processor that maps chunks using a function.

    This processor is useful for transforming chunks.
    """

    def __init__(self, mapper: Callable[[T], U]):
        """Initialize a map stream processor.

        Args:
            mapper: The mapper function to use for transforming data
        """
        self.mapper = mapper

    async def process(self, chunk: StreamChunk[T]) -> StreamChunk[U]:
        """Process a stream chunk.

        Args:
            chunk: The chunk to process

        Returns:
            The processed chunk
        """
        if chunk.event == StreamEvent.DATA and chunk.data is not None:
            mapped_data = self.mapper(chunk.data)
            return StreamChunk(
                data=mapped_data,
                event=chunk.event,
                metadata=chunk.metadata,
                timestamp=chunk.timestamp,
            )

        # For non-data events or None data, create a chunk with None
        return cast(
            StreamChunk[U],
            StreamChunk(
                data=None,  # type: ignore
                event=chunk.event,
                metadata=chunk.metadata,
                timestamp=chunk.timestamp,
            ),
        )


async def create_stream_from_list(
    items: List[R],
) -> AsyncGenerator[StreamChunk[R], None]:
    """Create a stream from a list of items.

    Args:
        items: The items to create the stream from

    Yields:
        The stream chunks
    """
    # Start event
    yield cast(StreamChunk[R], StreamChunk.start())

    # Data events
    for item in items:
        yield StreamChunk(data=item)

    # End event
    yield cast(StreamChunk[R], StreamChunk.end())


async def create_stream_from_generator(
    generator: AsyncGenerator[R, None],
) -> AsyncGenerator[StreamChunk[R], None]:
    """Create a stream from an async generator.

    Args:
        generator: The generator to create the stream from

    Yields:
        The stream chunks
    """
    # Start event
    yield cast(StreamChunk[R], StreamChunk.start())

    try:
        # Data events
        async for item in generator:
            yield StreamChunk(data=item)

        # End event
        yield cast(StreamChunk[R], StreamChunk.end())
    except Exception as e:
        # Error event
        yield cast(StreamChunk[R], StreamChunk.error(e))
        # End event
        yield cast(StreamChunk[R], StreamChunk.end())


async def collect_stream(stream: AsyncGenerator[StreamChunk[R], None]) -> List[R]:
    """Collect all data items from a stream.

    Args:
        stream: The stream to collect from

    Returns:
        The collected data items
    """
    items = []

    async for chunk in stream:
        if chunk.event == StreamEvent.DATA and chunk.data is not None:
            items.append(chunk.data)

    return items
