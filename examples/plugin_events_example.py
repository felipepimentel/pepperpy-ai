"""Example demonstrating event-based communication between plugins.

This example shows how to use events to enable loose coupling between plugins
and facilitate communication between them.
"""

import asyncio
from enum import Enum

from pepperpy.plugins import (
    EventContext,
    EventPriority,
    PepperpyPlugin,
)


# Define custom event types for this example
class ExampleEventType(Enum):
    """Custom event types for the example."""

    DATA_CREATED = "example.data.created"
    DATA_UPDATED = "example.data.updated"
    DATA_DELETED = "example.data.deleted"
    CALCULATION_STARTED = "example.calculation.started"
    CALCULATION_COMPLETED = "example.calculation.completed"
    CALCULATION_FAILED = "example.calculation.failed"


# Data source plugin that publishes events
class DataSourcePlugin(PepperpyPlugin):
    """A plugin that manages data and publishes events when data changes."""

    __metadata__ = {
        "name": "data_source",
        "version": "1.0.0",
        "description": "Data source plugin",
        "author": "PepperPy Team",
        "provider_type": "data",  # Provider type is required
    }

    def __init__(self, config=None):
        """Initialize plugin."""
        super().__init__(config)
        self.data = {}

    def initialize(self) -> None:
        """Initialize plugin."""
        super().initialize()
        # Register data as a resource
        self.register_resource(
            resource_key="data",
            resource=self.data,
            resource_type="memory",
            metadata={"description": "Shared data resource"},
        )
        print(f"✅ Initialized {self.__metadata__['name']}")

    async def async_cleanup(self) -> None:
        """Clean up plugin."""
        await super().async_cleanup()
        print(f"🧹 Cleaned up {self.__metadata__['name']}")

    async def create_data(self, key: str, value: any) -> None:
        """Create a new data item and publish an event.

        Args:
            key: Data key
            value: Data value
        """
        # Create data
        self.data[key] = value

        # Publish event
        context = await self.publish(
            ExampleEventType.DATA_CREATED,
            {"key": key, "value": value},
            {"operation": "create"},
        )

        print(f"📢 Published {ExampleEventType.DATA_CREATED.value} event for key={key}")
        return context

    async def update_data(self, key: str, value: any) -> None:
        """Update a data item and publish an event.

        Args:
            key: Data key
            value: New data value
        """
        if key not in self.data:
            raise KeyError(f"Key {key} not found")

        # Store old value for event data
        old_value = self.data[key]

        # Update data
        self.data[key] = value

        # Publish event
        context = await self.publish(
            ExampleEventType.DATA_UPDATED,
            {"key": key, "old_value": old_value, "new_value": value},
            {"operation": "update"},
        )

        print(f"📢 Published {ExampleEventType.DATA_UPDATED.value} event for key={key}")
        return context

    async def delete_data(self, key: str) -> None:
        """Delete a data item and publish an event.

        Args:
            key: Data key
        """
        if key not in self.data:
            raise KeyError(f"Key {key} not found")

        # Store value for event data
        value = self.data[key]

        # Delete data
        del self.data[key]

        # Publish event
        context = await self.publish(
            ExampleEventType.DATA_DELETED,
            {"key": key, "value": value},
            {"operation": "delete"},
        )

        print(f"📢 Published {ExampleEventType.DATA_DELETED.value} event for key={key}")
        return context


# Calculator plugin that reacts to data events
class CalculatorPlugin(PepperpyPlugin):
    """A plugin that performs calculations based on data changes."""

    __metadata__ = {
        "name": "calculator",
        "version": "1.0.0",
        "description": "Calculator plugin",
        "author": "PepperPy Team",
        "provider_type": "calculator",  # Provider type is required
    }

    def __init__(self, config=None):
        """Initialize plugin."""
        super().__init__(config)
        self.calculations = []

    def initialize(self) -> None:
        """Initialize plugin."""
        super().initialize()
        # Register calculations as a resource
        self.register_resource(
            resource_key="calculations",
            resource=self.calculations,
            resource_type="memory",
            metadata={"description": "Calculation history"},
        )
        print(f"✅ Initialized {self.__metadata__['name']}")

    async def async_cleanup(self) -> None:
        """Clean up plugin."""
        await super().async_cleanup()
        print(f"🧹 Cleaned up {self.__metadata__['name']}")

    # Event handler using the decorator approach with high priority
    @PepperpyPlugin.event_handler(ExampleEventType.DATA_CREATED, EventPriority.HIGH)
    async def handle_data_created(
        self, event_type: str, context: EventContext, data: dict
    ) -> None:
        """Handle data created events."""
        key = data.get("key")
        value = data.get("value")

        if key is not None and isinstance(value, (int, float)):
            # Start a calculation
            await self.perform_calculation(key, value)

    # Event handler using the decorator approach with normal priority
    @PepperpyPlugin.event_handler(ExampleEventType.DATA_UPDATED)
    async def handle_data_updated(
        self, event_type: str, context: EventContext, data: dict
    ) -> None:
        """Handle data updated events."""
        key = data.get("key")
        new_value = data.get("new_value")

        if key is not None and isinstance(new_value, (int, float)):
            # Start a calculation
            await self.perform_calculation(key, new_value)

    async def perform_calculation(self, key: str, value: any) -> None:
        """Perform a calculation on a value and publish events.

        Args:
            key: Data key
            value: Value to calculate on
        """
        # Publish calculation started event
        await self.publish(
            ExampleEventType.CALCULATION_STARTED, {"key": key, "value": value}
        )

        print(f"🧮 Starting calculation for key={key}, value={value}")

        try:
            # Simulate some processing time
            await asyncio.sleep(0.5)

            # Perform calculations
            square = value * value
            cube = value * value * value

            # Store calculation
            calculation = {
                "key": key,
                "value": value,
                "square": square,
                "cube": cube,
                "status": "completed",
            }
            self.calculations.append(calculation)

            # Publish calculation completed event
            await self.publish(
                ExampleEventType.CALCULATION_COMPLETED,
                {"key": key, "value": value, "square": square, "cube": cube},
            )

            print(
                f"✅ Calculation completed for key={key}: square={square}, cube={cube}"
            )

        except Exception as e:
            # Publish calculation failed event
            await self.publish(
                ExampleEventType.CALCULATION_FAILED,
                {"key": key, "value": value, "error": str(e)},
            )

            print(f"❌ Calculation failed for key={key}: {e}")

            # Store failed calculation
            self.calculations.append(
                {"key": key, "value": value, "status": "failed", "error": str(e)}
            )


# Logger plugin that logs all events
class LoggerPlugin(PepperpyPlugin):
    """A plugin that logs all events in the system."""

    __metadata__ = {
        "name": "logger",
        "version": "1.0.0",
        "description": "Event logger plugin",
        "author": "PepperPy Team",
        "provider_type": "logger",  # Provider type is required
    }

    def __init__(self, config=None):
        """Initialize plugin."""
        super().__init__(config)
        self.log_entries = []

    def initialize(self) -> None:
        """Initialize plugin."""
        super().initialize()
        # Register log entries as a resource
        self.register_resource(
            resource_key="log_entries",
            resource=self.log_entries,
            resource_type="memory",
            metadata={"description": "Event log entries"},
        )

        # Subscribe to all example events with lowest priority
        # This shows the manual subscription approach (vs. decorator)
        for event_type in ExampleEventType:
            self.subscribe(
                event_type,
                self.log_event,
                EventPriority.LOWEST,
                # Call even if event is canceled
                call_if_canceled=True,
            )

        print(f"✅ Initialized {self.__metadata__['name']}")

    async def async_cleanup(self) -> None:
        """Clean up plugin."""
        # Implicitly unsubscribe from all events via base class cleanup
        await super().async_cleanup()
        print(f"🧹 Cleaned up {self.__metadata__['name']}")

    async def log_event(
        self, event_type: str, context: EventContext, data: dict
    ) -> None:
        """Log an event.

        Args:
            event_type: Event type
            context: Event context
            data: Event data
        """
        # Create log entry
        log_entry = {
            "timestamp": context.timestamp,
            "event_id": context.event_id,
            "event_type": event_type,
            "source": context.source,
            "data": data,
            "context_data": context.data,
            "canceled": context.canceled,
        }

        # Add to log entries
        self.log_entries.append(log_entry)

        print(f"📝 Logged event: {event_type} from {context.source}")

    def get_log_entries(self) -> list:
        """Get all log entries.

        Returns:
            List of log entries
        """
        return self.log_entries

    def get_log_entries_by_type(self, event_type: Enum) -> list:
        """Get log entries for a specific event type.

        Args:
            event_type: Event type to filter by

        Returns:
            Filtered list of log entries
        """
        event_type_str = (
            event_type.value if isinstance(event_type, Enum) else event_type
        )
        return [
            entry for entry in self.log_entries if entry["event_type"] == event_type_str
        ]


async def main():
    """Run the example."""
    print("🚀 Starting plugin events example")

    # Create plugins
    data_source = DataSourcePlugin()
    calculator = CalculatorPlugin()
    logger = LoggerPlugin()

    # Initialize plugins
    data_source.initialize()
    calculator.initialize()
    logger.initialize()

    # Perform some data operations
    print("\n📊 Creating and updating data:")

    # Create data - will trigger calculator
    await data_source.create_data("x", 5)
    await data_source.create_data("y", 10)

    # Create non-numeric data - won't trigger calculator
    await data_source.create_data("name", "PepperPy")

    # Update data - will trigger calculator
    await data_source.update_data("x", 7)

    # Delete data
    await data_source.delete_data("name")

    # Wait for async operations to complete
    await asyncio.sleep(1)

    # Display calculation results
    calculations = calculator.get_resource("calculations")
    print("\n🧮 Calculation results:")
    for calc in calculations:
        status = calc["status"]
        if status == "completed":
            print(
                f"  Key: {calc['key']}, Value: {calc['value']}, Square: {calc['square']}, Cube: {calc['cube']}"
            )
        else:
            print(f"  Key: {calc['key']}, Value: {calc['value']}, Status: {status}")

    # Display log statistics
    log_entries = logger.get_resource("log_entries")
    print("\n📝 Event log statistics:")

    # Count events by type
    event_counts = {}
    for entry in log_entries:
        event_type = entry["event_type"]
        event_counts[event_type] = event_counts.get(event_type, 0) + 1

    for event_type, count in event_counts.items():
        print(f"  {event_type}: {count} events")

    # Clean up plugins
    print("\n🧹 Cleaning up...")
    await logger.async_cleanup()
    await calculator.async_cleanup()
    await data_source.async_cleanup()

    print("\n✅ Done!")


if __name__ == "__main__":
    asyncio.run(main())
