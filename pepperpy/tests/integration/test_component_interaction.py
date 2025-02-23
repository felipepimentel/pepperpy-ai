"""Integration tests for component interactions.

This module contains integration tests that verify components
can interact with each other correctly.
"""

import asyncio
from typing import Any, AsyncGenerator, Dict

import pytest

from pepperpy.tests.base import TestContext
from pepperpy.tests.conftest import TestComponent


class ProducerComponent(TestComponent):
    """Producer component implementation."""

    async def produce(self, data: Dict[str, Any]) -> None:
        """Produce data.

        Args:
            data: Data to produce
        """
        self._operations.inc()
        try:
            # Simulate work
            await asyncio.sleep(0.1)
            self._state.update(data)
            self._duration.observe(0.1)
        except Exception:
            self._errors.inc()
            raise


class ConsumerComponent(TestComponent):
    """Consumer component implementation."""

    async def consume(self, producer: ProducerComponent) -> Dict[str, Any]:
        """Consume data from producer.

        Args:
            producer: Producer component

        Returns:
            Dict[str, Any]: Consumed data
        """
        self._operations.inc()
        try:
            # Simulate work
            await asyncio.sleep(0.1)
            data = producer.get_state()
            self._state.update(data)
            self._duration.observe(0.1)
            return data
        except Exception:
            self._errors.inc()
            raise


@pytest.fixture
async def producer_component() -> AsyncGenerator[ProducerComponent, None]:
    """Fixture that provides a producer component.

    Yields:
        ProducerComponent: Producer component
    """
    producer = ProducerComponent()
    await producer._initialize()
    yield producer
    await producer._cleanup()


@pytest.fixture
async def consumer_component() -> AsyncGenerator[ConsumerComponent, None]:
    """Fixture that provides a consumer component.

    Yields:
        ConsumerComponent: Consumer component
    """
    consumer = ConsumerComponent()
    await consumer._initialize()
    yield consumer
    await consumer._cleanup()


@pytest.mark.asyncio
async def test_producer_consumer_interaction(
    producer_component: ProducerComponent,
    consumer_component: ConsumerComponent,
    test_context: TestContext,
) -> None:
    """Test producer-consumer interaction.

    This test verifies that the producer and consumer components
    can interact correctly.

    Args:
        producer_component: Producer component fixture
        consumer_component: Consumer component fixture
        test_context: Test context fixture
    """
    # Produce data
    test_data = {"key": "value", "number": 42}
    await producer_component.produce(test_data)

    # Verify producer state and metrics
    assert producer_component.get_state() == test_data
    assert producer_component._operations.get_value() == 1
    assert producer_component._errors.get_value() == 0
    assert producer_component._duration.get_value()["count"] == 1

    # Consume data
    consumed_data = await consumer_component.consume(producer_component)

    # Verify consumer state and metrics
    assert consumed_data == test_data
    assert consumer_component.get_state() == test_data
    assert consumer_component._operations.get_value() == 1
    assert consumer_component._errors.get_value() == 0
    assert consumer_component._duration.get_value()["count"] == 1


@pytest.mark.asyncio
async def test_producer_consumer_error_handling(
    producer_component: ProducerComponent,
    consumer_component: ConsumerComponent,
    test_context: TestContext,
) -> None:
    """Test producer-consumer error handling.

    This test verifies that the producer and consumer components
    handle errors correctly.

    Args:
        producer_component: Producer component fixture
        consumer_component: Consumer component fixture
        test_context: Test context fixture
    """

    # Override producer's produce method to raise an error
    async def produce_with_error(data: Dict[str, Any]) -> None:
        producer_component._operations.inc()
        raise ValueError("Producer error")

    producer_component.produce = produce_with_error  # type: ignore

    # Produce should raise error
    with pytest.raises(ValueError, match="Producer error"):
        await producer_component.produce({"key": "value"})

    # Verify producer metrics
    assert producer_component._operations.get_value() == 1
    assert producer_component._errors.get_value() == 1

    # Override consumer's consume method to raise an error
    async def consume_with_error(producer: ProducerComponent) -> Dict[str, Any]:
        consumer_component._operations.inc()
        raise ValueError("Consumer error")

    consumer_component.consume = consume_with_error  # type: ignore

    # Consume should raise error
    with pytest.raises(ValueError, match="Consumer error"):
        await consumer_component.consume(producer_component)

    # Verify consumer metrics
    assert consumer_component._operations.get_value() == 1
    assert consumer_component._errors.get_value() == 1
