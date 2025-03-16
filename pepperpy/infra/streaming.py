"""Streaming infrastructure for PepperPy.

This module provides streaming capabilities for PepperPy, including:
- Stream handler interfaces
- Stream transformers
- Stream processors
- Utility functions for working with streams

Example:
    ```python
    from pepperpy.infra.streaming import Stream, TextStreamHandler

    # Create a simple text stream handler
    handler = TextStreamHandler()

    # Process a stream
    async with Stream() as stream:
        async for chunk in stream:
            processed = handler.process(chunk)
            yield processed
    ```
"""

import json
from abc import abstractmethod
from enum import Enum
from typing import (
    Any,
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Protocol,
    TypeVar,
    Union,
)

from pepperpy.core.errors import PepperPyError

# Type definitions
T = TypeVar("T")
U = TypeVar("U")
ChunkType = TypeVar("ChunkType")
ResultType = TypeVar("ResultType")


class StreamingError(PepperPyError):
    """Base error for streaming-related issues."""

    pass


class StreamClosedError(StreamingError):
    """Error raised when attempting to use a closed stream."""

    pass


class StreamTimeoutError(StreamingError):
    """Error raised when a stream operation times out."""

    pass


class StreamProcessingError(StreamingError):
    """Error raised when processing a stream fails."""

    pass


class StreamType(Enum):
    """Types of streams supported by PepperPy."""

    TEXT = "text"
    JSON = "json"
    BINARY = "binary"
    MIXED = "mixed"


class StreamMetadata(Dict[str, Any]):
    """Metadata associated with a stream."""

    pass


class StreamChunk(Generic[ChunkType]):
    """A chunk of data in a stream."""

    def __init__(
        self,
        data: ChunkType,
        metadata: Optional[StreamMetadata] = None,
        is_last: bool = False,
    ) -> None:
        """Initialize a new stream chunk.

        Args:
            data: The chunk data
            metadata: Optional metadata associated with the chunk
            is_last: Whether this is the last chunk in the stream
        """
        self.data = data
        self.metadata = metadata or {}
        self.is_last = is_last

    def __repr__(self) -> str:
        """Get a string representation of the chunk.

        Returns:
            String representation
        """
        return f"StreamChunk(data={self.data!r}, is_last={self.is_last}, metadata={self.metadata})"


class StreamHandler(Protocol, Generic[ChunkType, ResultType]):
    """Protocol for stream handlers."""

    def process(self, chunk: StreamChunk[ChunkType]) -> ResultType:
        """Process a chunk of data.

        Args:
            chunk: The chunk to process

        Returns:
            The processed result
        """
        ...

    async def process_async(self, chunk: StreamChunk[ChunkType]) -> ResultType:
        """Process a chunk of data asynchronously.

        Args:
            chunk: The chunk to process

        Returns:
            The processed result
        """
        ...


class Stream(Generic[ChunkType]):
    """A stream of data."""

    def __init__(
        self,
        source: Optional[Union[Iterable[ChunkType], AsyncIterable[ChunkType]]] = None,
        stream_type: StreamType = StreamType.TEXT,
        metadata: Optional[StreamMetadata] = None,
    ) -> None:
        """Initialize a new stream.

        Args:
            source: The source of the stream data
            stream_type: The type of the stream
            metadata: Optional metadata associated with the stream
        """
        self.source = source
        self.stream_type = stream_type
        self.metadata = metadata or {}
        self.closed = False
        self._buffer: List[StreamChunk[ChunkType]] = []

    def __aiter__(self) -> "Stream[ChunkType]":
        """Get an async iterator for the stream.

        Returns:
            The stream itself
        """
        return self

    async def __anext__(self) -> StreamChunk[ChunkType]:
        """Get the next chunk in the stream.

        Returns:
            The next chunk

        Raises:
            StopAsyncIteration: If there are no more chunks
            StreamClosedError: If the stream is closed
        """
        if self.closed:
            raise StreamClosedError("Cannot iterate on a closed stream")

        # Check if there's a buffered chunk
        if self._buffer:
            return self._buffer.pop(0)

        # If we have a source, get the next chunk from it
        if self.source is not None:
            if isinstance(self.source, AsyncIterable):
                try:
                    async_iter = self.source.__aiter__()
                    data = await async_iter.__anext__()
                    return StreamChunk(data)
                except StopAsyncIteration:
                    self.closed = True
                    raise
            else:
                try:
                    data = next(iter(self.source))
                    return StreamChunk(data)
                except StopIteration:
                    self.closed = True
                    raise StopAsyncIteration

        # If we have no source and no buffer, we're done
        self.closed = True
        raise StopAsyncIteration

    def append(self, chunk: ChunkType, is_last: bool = False) -> None:
        """Append a chunk to the stream.

        Args:
            chunk: The chunk to append
            is_last: Whether this is the last chunk

        Raises:
            StreamClosedError: If the stream is closed
        """
        if self.closed:
            raise StreamClosedError("Cannot append to a closed stream")

        self._buffer.append(StreamChunk(chunk, is_last=is_last))

    def close(self) -> None:
        """Close the stream."""
        self.closed = True

    async def collect(self) -> List[ChunkType]:
        """Collect all chunks from the stream.

        Returns:
            List of all chunks

        Raises:
            StreamClosedError: If the stream is closed
        """
        if self.closed:
            raise StreamClosedError("Cannot collect from a closed stream")

        result: List[ChunkType] = []
        async for chunk in self:
            result.append(chunk.data)
        return result

    async def process_with(
        self, handler: StreamHandler[ChunkType, ResultType]
    ) -> AsyncGenerator[ResultType, None]:
        """Process the stream with a handler.

        Args:
            handler: The handler to use

        Yields:
            Processed results

        Raises:
            StreamClosedError: If the stream is closed
            StreamProcessingError: If processing fails
        """
        if self.closed:
            raise StreamClosedError("Cannot process a closed stream")

        try:
            async for chunk in self:
                try:
                    result = await handler.process_async(chunk)
                    yield result
                except Exception as e:
                    raise StreamProcessingError(f"Error processing chunk: {e}")
        except Exception as e:
            if not isinstance(e, StreamProcessingError):
                raise StreamProcessingError(f"Error iterating stream: {e}")
            raise

    async def __aenter__(self) -> "Stream[ChunkType]":
        """Enter the stream context.

        Returns:
            The stream itself
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the stream context.

        Args:
            exc_type: Exception type, if any
            exc_val: Exception value, if any
            exc_tb: Exception traceback, if any
        """
        self.close()


class TextStreamHandler(StreamHandler[str, str]):
    """Handler for text streams."""

    def process(self, chunk: StreamChunk[str]) -> str:
        """Process a text chunk.

        Args:
            chunk: The chunk to process

        Returns:
            The processed text
        """
        return chunk.data

    async def process_async(self, chunk: StreamChunk[str]) -> str:
        """Process a text chunk asynchronously.

        Args:
            chunk: The chunk to process

        Returns:
            The processed text
        """
        return self.process(chunk)


class JsonStreamHandler(StreamHandler[str, Dict[str, Any]]):
    """Handler for JSON streams."""

    def process(self, chunk: StreamChunk[str]) -> Dict[str, Any]:
        """Process a JSON chunk.

        Args:
            chunk: The chunk to process

        Returns:
            The parsed JSON data

        Raises:
            StreamProcessingError: If the chunk is not valid JSON
        """
        try:
            return json.loads(chunk.data)
        except json.JSONDecodeError as e:
            raise StreamProcessingError(f"Invalid JSON: {e}")

    async def process_async(self, chunk: StreamChunk[str]) -> Dict[str, Any]:
        """Process a JSON chunk asynchronously.

        Args:
            chunk: The chunk to process

        Returns:
            The parsed JSON data
        """
        return self.process(chunk)


class StreamTransformer(Generic[ChunkType, ResultType]):
    """Base class for stream transformers."""

    @abstractmethod
    def transform(self, chunk: StreamChunk[ChunkType]) -> StreamChunk[ResultType]:
        """Transform a chunk.

        Args:
            chunk: The chunk to transform

        Returns:
            The transformed chunk
        """
        pass

    async def transform_async(
        self, chunk: StreamChunk[ChunkType]
    ) -> StreamChunk[ResultType]:
        """Transform a chunk asynchronously.

        Args:
            chunk: The chunk to transform

        Returns:
            The transformed chunk
        """
        return self.transform(chunk)

    async def transform_stream(
        self, stream: Stream[ChunkType]
    ) -> AsyncGenerator[StreamChunk[ResultType], None]:
        """Transform a stream.

        Args:
            stream: The stream to transform

        Yields:
            Transformed chunks
        """
        async for chunk in stream:
            yield await self.transform_async(chunk)


class StreamProcessor(Generic[ChunkType]):
    """Base class for stream processors."""

    def __init__(self) -> None:
        """Initialize a new stream processor."""
        self.handlers: List[StreamHandler[ChunkType, Any]] = []

    def add_handler(self, handler: StreamHandler[ChunkType, Any]) -> None:
        """Add a handler to the processor.

        Args:
            handler: The handler to add
        """
        self.handlers.append(handler)

    async def process(self, stream: Stream[ChunkType]) -> None:
        """Process a stream.

        Args:
            stream: The stream to process

        Raises:
            StreamProcessingError: If processing fails
        """
        try:
            async for chunk in stream:
                for handler in self.handlers:
                    await handler.process_async(chunk)
        except Exception as e:
            raise StreamProcessingError(f"Error processing stream: {e}")


# Utility functions


async def combine_streams(
    streams: List[Stream[T]], interleave: bool = True
) -> Stream[T]:
    """Combine multiple streams into a single stream.

    Args:
        streams: The streams to combine
        interleave: Whether to interleave chunks from different streams

    Returns:
        A combined stream
    """
    result = Stream[T]()

    if interleave:
        # Interleave chunks from all streams
        pending = list(streams)
        while pending:
            for stream in pending[:]:
                try:
                    # Get the next chunk from the stream
                    chunk = await stream.__anext__()
                    result.append(chunk.data, is_last=chunk.is_last)
                    if stream.closed:
                        pending.remove(stream)
                except StopAsyncIteration:
                    pending.remove(stream)
    else:
        # Process streams sequentially
        for stream in streams:
            async for chunk in stream:
                result.append(chunk.data, is_last=chunk.is_last)

    return result


async def stream_to_string(stream: Stream[str]) -> str:
    """Convert a text stream to a string.

    Args:
        stream: The stream to convert

    Returns:
        The concatenated string
    """
    chunks = await stream.collect()
    return "".join(chunks)


async def create_text_stream(text: str, chunk_size: int = 100) -> Stream[str]:
    """Create a stream from a string.

    Args:
        text: The text to stream
        chunk_size: The size of each chunk

    Returns:
        A stream of text chunks
    """
    stream = Stream[str]()

    for i in range(0, len(text), chunk_size):
        chunk = text[i : i + chunk_size]
        is_last = i + chunk_size >= len(text)
        stream.append(chunk, is_last=is_last)

    return stream


async def merge_streams(
    streams: List[Stream[T]], merger: Callable[[List[T]], U]
) -> Stream[U]:
    """Merge multiple streams using a merger function.

    Args:
        streams: The streams to merge
        merger: Function to merge chunks from different streams

    Returns:
        A merged stream
    """
    result = Stream[U]()

    # Keep track of the latest chunk from each stream
    latest_chunks: List[Optional[T]] = [None] * len(streams)

    # Process all streams until they're all closed
    while not all(stream.closed for stream in streams):
        # Get the latest chunk from each stream
        for i, stream in enumerate(streams):
            if not stream.closed:
                try:
                    # Get the next chunk from the stream
                    chunk = await stream.__anext__()
                    latest_chunks[i] = chunk.data
                except StopAsyncIteration:
                    pass

        # Filter out None values
        valid_chunks = [c for c in latest_chunks if c is not None]

        # Apply merger function
        if valid_chunks:
            merged = merger(valid_chunks)
            is_last = all(stream.closed for stream in streams)
            result.append(merged, is_last=is_last)

    return result


class AsyncIteratorWrapper(AsyncIterator[T]):
    """Wrapper for an async iterator that provides additional functionality."""

    def __init__(self, iterator: AsyncIterator[T]):
        """Initialize a new async iterator wrapper.

        Args:
            iterator: The async iterator to wrap
        """
        self.iterator = iterator
        self._buffer: List[T] = []
        self._state = StreamState.READY
        self._consumed = False

    def __aiter__(self) -> "AsyncIteratorWrapper[T]":
        """Get an async iterator for this wrapper.

        Returns:
            This wrapper as an async iterator
        """
        return self

    async def __anext__(self) -> T:
        """Get the next item from the iterator.

        Returns:
            The next item from the iterator

        Raises:
            StopAsyncIteration: If there are no more items
        """
        if self._state == StreamState.CLOSED:
            raise StopAsyncIteration

        if self._buffer:
            return self._buffer.pop(0)

        try:
            self._state = StreamState.STREAMING
            item = await self.iterator.__anext__()
            return item
        except StopAsyncIteration:
            self._state = StreamState.COMPLETED
            raise
        except Exception as e:
            self._state = StreamState.ERROR
            raise StreamError(f"Error iterating: {e}") from e


# Export all public APIs
__all__ = [
    # Error classes
    "StreamingError",
    "StreamClosedError",
    "StreamTimeoutError",
    "StreamProcessingError",
    # Enums
    "StreamType",
    # Classes
    "StreamMetadata",
    "StreamChunk",
    "StreamHandler",
    "Stream",
    "TextStreamHandler",
    "JsonStreamHandler",
    "StreamTransformer",
    "StreamProcessor",
    # Utility functions
    "combine_streams",
    "stream_to_string",
    "create_text_stream",
    "merge_streams",
]
