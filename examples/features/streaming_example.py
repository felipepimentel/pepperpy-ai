#!/usr/bin/env python3
"""
Example demonstrating the PepperPy Streaming module.
"""

import asyncio
import json
import time
import uuid
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional


class StreamingEventType(str, Enum):
    """Types of streaming events."""

    START = "start"
    TOKEN = "token"
    END = "end"
    ERROR = "error"
    METADATA = "metadata"


class StreamingEvent:
    """Represents a streaming event."""

    def __init__(
        self,
        event_type: StreamingEventType,
        data: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a streaming event."""
        self.id = str(uuid.uuid4())
        self.event_type = event_type
        self.data = data
        self.metadata = metadata or {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "data": self.data,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        """Convert the event to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamingEvent":
        """Create an event from a dictionary."""
        event_type = StreamingEventType(data["event_type"])
        event = cls(
            event_type=event_type,
            data=data.get("data"),
            metadata=data.get("metadata", {}),
        )
        event.id = data.get("id", str(uuid.uuid4()))
        event.timestamp = data.get("timestamp", time.time())
        return event


class StreamingSource:
    """Base class for streaming sources."""

    def __init__(self, name: str) -> None:
        """Initialize a streaming source."""
        self.name = name
        self.id = str(uuid.uuid4())

    async def stream(self) -> AsyncGenerator[StreamingEvent, None]:
        """Stream events from the source."""
        raise NotImplementedError("Subclasses must implement this method")


class TextStreamingSource(StreamingSource):
    """Streams text content token by token."""

    def __init__(
        self,
        name: str,
        text: str,
        token_delay: float = 0.1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a text streaming source."""
        super().__init__(name)
        self.text = text
        self.token_delay = token_delay
        self.metadata = metadata or {}

    async def stream(self) -> AsyncGenerator[StreamingEvent, None]:
        """Stream the text token by token."""
        # Send start event
        yield StreamingEvent(
            event_type=StreamingEventType.START,
            metadata={"source": self.name, **self.metadata},
        )

        # Stream tokens (simple word-based tokenization for demonstration)
        tokens = self.text.split()
        for token in tokens:
            await asyncio.sleep(self.token_delay)
            yield StreamingEvent(
                event_type=StreamingEventType.TOKEN,
                data=token + " ",
                metadata={"source": self.name},
            )

        # Send end event
        yield StreamingEvent(
            event_type=StreamingEventType.END,
            metadata={"source": self.name, "token_count": len(tokens)},
        )


class StreamingProcessor:
    """Processes streaming events."""

    def __init__(
        self,
        name: str,
        transform_fn: Optional[Callable[[StreamingEvent], StreamingEvent]] = None,
    ) -> None:
        """Initialize a streaming processor."""
        self.name = name
        self.id = str(uuid.uuid4())
        self.transform_fn = transform_fn

    async def process(
        self,
        event_stream: AsyncGenerator[StreamingEvent, None],
    ) -> AsyncGenerator[StreamingEvent, None]:
        """Process events from the stream."""
        async for event in event_stream:
            if self.transform_fn:
                event = self.transform_fn(event)

            # Add processor metadata
            if event.metadata is None:
                event.metadata = {}
            event.metadata["processor"] = self.name

            yield event


class StreamingConsumer:
    """Consumes streaming events."""

    def __init__(self, name: str) -> None:
        """Initialize a streaming consumer."""
        self.name = name
        self.id = str(uuid.uuid4())
        self.events: List[StreamingEvent] = []

    async def consume(
        self,
        event_stream: AsyncGenerator[StreamingEvent, None],
    ) -> None:
        """Consume events from the stream."""
        async for event in event_stream:
            self.events.append(event)
            await self.handle_event(event)

    async def handle_event(self, event: StreamingEvent) -> None:
        """Handle a streaming event."""
        raise NotImplementedError("Subclasses must implement this method")


class ConsoleStreamingConsumer(StreamingConsumer):
    """Consumes streaming events and prints them to the console."""

    def __init__(
        self,
        name: str,
        show_metadata: bool = False,
        show_event_type: bool = False,
    ) -> None:
        """Initialize a console streaming consumer."""
        super().__init__(name)
        self.show_metadata = show_metadata
        self.show_event_type = show_event_type
        self.buffer = ""

    async def handle_event(self, event: StreamingEvent) -> None:
        """Handle a streaming event by printing to the console."""
        if event.event_type == StreamingEventType.START:
            if self.show_event_type:
                print(f"[{self.name}] Stream started")

        elif event.event_type == StreamingEventType.TOKEN:
            if isinstance(event.data, str):
                self.buffer += event.data
                print(event.data, end="", flush=True)

        elif event.event_type == StreamingEventType.END:
            if self.show_event_type:
                print(f"\n[{self.name}] Stream ended")
            else:
                print()  # Just add a newline

            if self.show_metadata:
                print(f"Metadata: {event.metadata}")

        elif event.event_type == StreamingEventType.ERROR:
            print(f"\n[{self.name}] Error: {event.data}")

        elif event.event_type == StreamingEventType.METADATA:
            if self.show_metadata:
                print(f"[{self.name}] Metadata: {event.metadata}")


class StreamingPipeline:
    """Connects streaming sources, processors, and consumers."""

    def __init__(self, name: str) -> None:
        """Initialize a streaming pipeline."""
        self.name = name
        self.id = str(uuid.uuid4())
        self.sources: List[StreamingSource] = []
        self.processors: List[StreamingProcessor] = []
        self.consumers: List[StreamingConsumer] = []

    def add_source(self, source: StreamingSource) -> None:
        """Add a source to the pipeline."""
        self.sources.append(source)

    def add_processor(self, processor: StreamingProcessor) -> None:
        """Add a processor to the pipeline."""
        self.processors.append(processor)

    def add_consumer(self, consumer: StreamingConsumer) -> None:
        """Add a consumer to the pipeline."""
        self.consumers.append(consumer)

    async def run(self) -> None:
        """Run the pipeline."""
        tasks = []

        for source in self.sources:
            # For each source and consumer combination, create a separate task
            for consumer in self.consumers:
                # Create a new stream for each consumer
                stream = source.stream()

                # Apply processors in sequence
                for processor in self.processors:
                    stream = processor.process(stream)

                # Create a task for the consumer
                task = asyncio.create_task(consumer.consume(stream))
                tasks.append(task)

        # Wait for all tasks to complete
        if tasks:
            await asyncio.gather(*tasks)


# Example transformers for the streaming processor
def uppercase_transformer(event: StreamingEvent) -> StreamingEvent:
    """Transform token data to uppercase."""
    if event.event_type == StreamingEventType.TOKEN and isinstance(event.data, str):
        event.data = event.data.upper()
    return event


def reverse_transformer(event: StreamingEvent) -> StreamingEvent:
    """Reverse token data."""
    if event.event_type == StreamingEventType.TOKEN and isinstance(event.data, str):
        # Reverse the characters in the token, but keep the space at the end
        if event.data.endswith(" "):
            event.data = event.data[:-1][::-1] + " "
        else:
            event.data = event.data[::-1]
    return event


async def main() -> None:
    """Run the streaming example."""
    print("PepperPy Streaming Example")
    print("=========================")

    # Create a simple streaming pipeline
    pipeline = StreamingPipeline("example-pipeline")

    # Add a text streaming source
    source = TextStreamingSource(
        name="text-source",
        text="This is an example of streaming text from the PepperPy framework. "
        "It demonstrates how to create a streaming pipeline with sources, "
        "processors, and consumers.",
        token_delay=0.1,  # 100ms delay between tokens
    )
    pipeline.add_source(source)

    # Add a consumer that prints to the console
    consumer = ConsoleStreamingConsumer(
        name="console-consumer",
        show_metadata=False,
        show_event_type=False,
    )
    pipeline.add_consumer(consumer)

    # Run the pipeline
    print("\nStreaming original text:")
    await pipeline.run()

    # Create a pipeline with an uppercase transformer
    uppercase_pipeline = StreamingPipeline("uppercase-pipeline")
    uppercase_pipeline.add_source(source)

    # Add a processor that transforms text to uppercase
    processor = StreamingProcessor(
        name="uppercase-processor",
        transform_fn=uppercase_transformer,
    )
    uppercase_pipeline.add_processor(processor)

    # Add a consumer
    uppercase_consumer = ConsoleStreamingConsumer(
        name="uppercase-consumer",
        show_metadata=False,
        show_event_type=False,
    )
    uppercase_pipeline.add_consumer(uppercase_consumer)

    # Run the uppercase pipeline
    print("\nStreaming uppercase text:")
    await uppercase_pipeline.run()

    # Create a pipeline with a reverse transformer
    reverse_pipeline = StreamingPipeline("reverse-pipeline")
    reverse_pipeline.add_source(source)

    # Add a processor that reverses text
    reverse_processor = StreamingProcessor(
        name="reverse-processor",
        transform_fn=reverse_transformer,
    )
    reverse_pipeline.add_processor(reverse_processor)

    # Add a consumer
    reverse_consumer = ConsoleStreamingConsumer(
        name="reverse-consumer",
        show_metadata=False,
        show_event_type=False,
    )
    reverse_pipeline.add_consumer(reverse_consumer)

    # Run the reverse pipeline
    print("\nStreaming reversed text:")
    await reverse_pipeline.run()


if __name__ == "__main__":
    asyncio.run(main())
