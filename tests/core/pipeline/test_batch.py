"""Tests for batch processing implementation."""

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
from pepperpy.core.pipeline.batch import BatchProcessor

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
async def batch_processor(processor, metrics):
    """Fixture for batch processor."""
    proc = BatchProcessor(
        name="test-batch",
        processor=processor,
        max_batch_size=10,
        parallel_batches=2,
        metrics=metrics
    )
    await proc.initialize()
    yield proc
    await proc.stop()

@pytest.mark.asyncio
async def test_batch_processor_init(batch_processor):
    """Test batch processor initialization."""
    assert batch_processor.name == "test-batch"
    assert batch_processor.is_running()

@pytest.mark.asyncio
async def test_batch_processing(batch_processor):
    """Test batch processing functionality."""
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
        for i in range(25)
    ]
    
    # Process batch
    results = await batch_processor.process_batch(items)
    
    # Verify results
    assert len(results) == 25
    assert all(r.status == "success" for r in results)
    assert all(r.data.value == i * 2 for i, r in enumerate(results))
    
    # Check metrics
    metrics = await batch_processor.get_metrics()
    assert metrics["processed_items"] == 25
    assert metrics["processed_batches"] == 3  # 25 items split into 3 batches
    assert metrics["processing_errors"] == 0

@pytest.mark.asyncio
async def test_batch_processor_empty_batch(batch_processor):
    """Test processing empty batch."""
    results = await batch_processor.process_batch([])
    assert len(results) == 0

@pytest.mark.asyncio
async def test_batch_processor_error_handling(batch_processor):
    """Test error handling in batch processor."""
    # Create invalid items
    items = [
        DataItem(
            id="invalid",
            data=None,  # This will cause an error
            metadata={},
            timestamp=datetime.now(),
            source="test",
            schema_version="1.0"
        )
    ]
    
    # Process invalid batch
    with pytest.raises(ProcessingError):
        await batch_processor.process_batch(items)
    
    # Check metrics
    metrics = await batch_processor.get_metrics()
    assert metrics["processing_errors"] > 0

@pytest.mark.asyncio
async def test_batch_splitting(batch_processor):
    """Test batch splitting functionality."""
    # Create large batch
    items = [
        DataItem(
            id=f"test-{i}",
            data=TestData(i),
            metadata={},
            timestamp=datetime.now(),
            source="test",
            schema_version="1.0"
        )
        for i in range(25)
    ]
    
    # Split batch
    batches = batch_processor._split_batch(items)
    
    # Verify splitting
    assert len(batches) == 3  # 25 items split into 3 batches
    assert len(batches[0]) == 10  # First batch
    assert len(batches[1]) == 10  # Second batch
    assert len(batches[2]) == 5   # Last batch 