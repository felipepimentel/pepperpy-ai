"""Tests for stream processing implementation."""

import asyncio
from datetime import datetime
import pytest
from typing import List

from pepperpy.core.errors import ProcessingError
from pepperpy.core.metrics import MetricsCollector
from pepperpy.core.pipeline.base import (
    DataItem,
    ProcessingResult,
    DataProcessor,
)
from pepperpy.core.pipeline.stream import StreamProcessor

# Test data types
class TestData:
    def __init__(self, value: int):
        self.value = value

class ProcessedData:
    def __init__(self, value: int):
        self.value = value * 2

# Test processor
class TestProcessor(DataProcessor[TestData, ProcessedData]):
    async def _initialize(self) -> None:
        pass

    async def _cleanup(self) -> None:
        pass

    async def process_item(self, item: DataItem[TestData]) -> ProcessingResult[ProcessedData]:
        return ProcessingResult(
            id=item.id,
            data=ProcessedData(item.data.value),
            metadata=item.metadata,
            timestamp=datetime.now(),
            processing_time=0.1,
            status="success",
            errors=[]
        )

    async def process_batch(
        self,
        items: List[DataItem[TestData]]
    ) -> List[ProcessingResult[ProcessedData]]:
        return [await self.process_item(item) for item in items]

@pytest.fixture
def metrics():
    """Fixture for metrics collector."""
    return MetricsCollector()

@pytest.fixture
def processor():
    """Fixture for test processor."""
    return TestProcessor("test-processor")

@pytest.fixture
async def stream_processor(processor, metrics):
    """Fixture for stream processor."""
    proc = StreamProcessor(
        name="test-stream",
        processor=processor,
        buffer_size=10,
        batch_size=2,
        metrics=metrics
    )
    await proc.initialize()
    yield proc
    await proc.stop()

@pytest.mark.asyncio
async def test_stream_processor_init(stream_processor):
    """Test stream processor initialization."""
    assert stream_processor.name == "test-stream"
    assert stream_processor.is_running()

@pytest.mark.asyncio
async def test_stream_processing(stream_processor):
    """Test stream processing functionality."""
    # Create test items
    items = [
        DataItem(
            id=f"test-{i}",
            data=TestData(i),
            metadata={},
            timestamp=datetime.now(),
            source="test",
            schema_version="1.0"
        )
        for i in range(5)
    ]
    
    # Process items
    for item in items:
        await stream_processor.process(item)
    
    # Wait for processing
    await asyncio.sleep(0.5)
    
    # Check metrics
    metrics = await stream_processor.get_metrics()
    assert metrics["processed_items"] == 5
    assert metrics["processing_errors"] == 0
    assert metrics["queue_size"] == 0

@pytest.mark.asyncio
async def test_stream_processor_error_handling(stream_processor):
    """Test error handling in stream processor."""
    # Create invalid item
    invalid_item = DataItem(
        id="invalid",
        data=None,  # This will cause an error
        metadata={},
        timestamp=datetime.now(),
        source="test",
        schema_version="1.0"
    )
    
    # Process invalid item
    with pytest.raises(ProcessingError):
        await stream_processor.process(invalid_item)
    
    # Check metrics
    metrics = await stream_processor.get_metrics()
    assert metrics["processing_errors"] > 0

@pytest.mark.asyncio
async def test_stream_processor_backpressure(stream_processor):
    """Test backpressure handling."""
    # Create more items than buffer size
    items = [
        DataItem(
            id=f"test-{i}",
            data=TestData(i),
            metadata={},
            timestamp=datetime.now(),
            source="test",
            schema_version="1.0"
        )
        for i in range(20)
    ]
    
    # Process items (should block when buffer is full)
    for item in items:
        await stream_processor.process(item)
    
    # Wait for processing
    await asyncio.sleep(1)
    
    # Check metrics
    metrics = await stream_processor.get_metrics()
    assert metrics["processed_items"] == 20
    assert metrics["queue_size"] == 0 