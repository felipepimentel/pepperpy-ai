"""Public interfaces for PepperPy Streaming module.

This module provides a stable public interface for the streaming functionality.
It exposes the core streaming abstractions and implementations that are
considered part of the public API.
"""

from pepperpy.streaming.core import (
    BufferedStreamConsumer,
    CallbackStreamConsumer,
    FilterStreamProcessor,
    JsonStreamProcessor,
    LoggingStreamConsumer,
    MapStreamProcessor,
    StreamChunk,
    StreamConsumer,
    StreamEvent,
    StreamHandler,
    StreamProcessor,
    StreamProducer,
    TextStreamProcessor,
    collect_stream,
    create_stream_from_generator,
    create_stream_from_list,
)

# Re-export everything
__all__ = [
    # Classes
    "BufferedStreamConsumer",
    "CallbackStreamConsumer",
    "FilterStreamProcessor",
    "JsonStreamProcessor",
    "LoggingStreamConsumer",
    "MapStreamProcessor",
    "StreamChunk",
    "StreamConsumer",
    "StreamEvent",
    "StreamHandler",
    "StreamProcessor",
    "StreamProducer",
    "TextStreamProcessor",
    # Functions
    "collect_stream",
    "create_stream_from_generator",
    "create_stream_from_list",
]
