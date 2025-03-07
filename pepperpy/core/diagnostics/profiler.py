"""Profiler for measuring performance of PepperPy components and pipelines."""

import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ProfilerEvent:
    """Event recorded by the profiler."""

    name: str
    event_type: str
    timestamp: float
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[int] = None
    id: Optional[int] = None
    children: List["ProfilerEvent"] = field(default_factory=list)


class Profiler:
    """Profiler for measuring performance of PepperPy components and pipelines.

    This class provides tools for measuring execution time, memory usage,
    and other performance metrics for components and pipelines.
    """

    def __init__(self) -> None:
        """Initialize the profiler."""
        self.events: List[ProfilerEvent] = []
        self.current_event_id = 0
        self.active_events: Dict[int, ProfilerEvent] = {}
        self.start_time = 0.0
        self.end_time = 0.0
        self.total_duration = 0.0
        self.metadata: Dict[str, Any] = {}

    def profile(
        self,
        component: Any,
        inputs: Dict[str, Any],
        max_depth: int = 10,
        include_memory: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Profile the execution of a component or pipeline.

        Args:
            component: The component or pipeline to profile
            inputs: The inputs to the component
            max_depth: Maximum depth of nested components to profile
            include_memory: Whether to include memory usage metrics
            **kwargs: Additional parameters for profiling

        Returns:
            Profiling results
        """
        self.start_time = time.time()
        self.metadata = {
            "component_type": type(component).__name__,
            "input_keys": list(inputs.keys()),
            **kwargs,
        }

        # Start the root event
        root_event_id = self._start_event(
            "execute",
            "component",
            {"component_type": type(component).__name__},
        )

        # Execute the component with profiling
        result = None
        error = None
        try:
            # Check if the component has a special profile method
            if hasattr(component, "profile"):
                result = component.profile(inputs, profiler=self)
            else:
                # Use the standard execute method with our event hooks
                result = self._profile_execution(component, inputs, max_depth)
        except Exception as e:
            error = e
            self._record_event(
                "error",
                "error",
                {"error_type": type(e).__name__, "error_message": str(e)},
            )
            traceback.print_exc()

        # End the root event
        self._end_event(root_event_id)

        # Record the overall execution
        self.end_time = time.time()
        self.total_duration = self.end_time - self.start_time

        # Build the results
        results = {
            "success": error is None,
            "total_duration": self.total_duration,
            "events": self.events,
            "metadata": self.metadata,
        }

        if error:
            results["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
            }
        else:
            results["output_keys"] = (
                list(result.keys()) if isinstance(result, dict) else ["result"]
            )

        return results

    def start_event(
        self,
        name: str,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Start a profiling event.

        Args:
            name: Name of the event
            event_type: Type of the event
            metadata: Additional metadata for the event

        Returns:
            ID of the started event
        """
        return self._start_event(name, event_type, metadata or {})

    def end_event(self, event_id: int) -> None:
        """End a profiling event.

        Args:
            event_id: ID of the event to end
        """
        self._end_event(event_id)

    def record_event(
        self,
        name: str,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        duration: Optional[float] = None,
    ) -> None:
        """Record a profiling event.

        Args:
            name: Name of the event
            event_type: Type of the event
            metadata: Additional metadata for the event
            duration: Optional duration of the event
        """
        self._record_event(name, event_type, metadata or {}, duration)

    def get_events(
        self,
        event_type: Optional[str] = None,
        min_duration: Optional[float] = None,
    ) -> List[ProfilerEvent]:
        """Get profiling events.

        Args:
            event_type: Optional event type filter
            min_duration: Optional minimum duration filter

        Returns:
            List of events matching the filters
        """
        filtered_events = self.events

        if event_type:
            filtered_events = [
                event for event in filtered_events if event.event_type == event_type
            ]

        if min_duration:
            filtered_events = [
                event
                for event in filtered_events
                if event.duration and event.duration >= min_duration
            ]

        return filtered_events

    def get_event_tree(self) -> List[ProfilerEvent]:
        """Get the event tree.

        Returns:
            List of root events with their children
        """
        # Find root events (events with no parent)
        root_events = [event for event in self.events if event.parent_id is None]

        # Build the tree
        for event in root_events:
            self._build_event_tree(event)

        return root_events

    def summary(self, format: str = "text") -> str:
        """Get a summary of the profiling results.

        Args:
            format: Output format (text, markdown, json)

        Returns:
            Summary of profiling results in the requested format
        """
        if format == "markdown":
            return self._markdown_summary()
        elif format == "json":
            import json

            return json.dumps(
                {
                    "total_duration": self.total_duration,
                    "events": [self._event_to_dict(event) for event in self.events],
                    "metadata": self.metadata,
                },
                indent=2,
            )
        else:
            return self._text_summary()

    def _profile_execution(
        self,
        component: Any,
        inputs: Dict[str, Any],
        max_depth: int,
        current_depth: int = 0,
    ) -> Any:
        """Profile the execution of a component.

        Args:
            component: The component to profile
            inputs: The inputs to the component
            max_depth: Maximum depth of nested components to profile
            current_depth: Current depth of profiling

        Returns:
            The result of the component execution
        """
        # If we've reached the maximum depth, execute without further profiling
        if current_depth >= max_depth:
            return component.execute(inputs)

        # Check if the component has subcomponents
        subcomponents = getattr(component, "components", [])

        # If the component has no subcomponents, execute it directly
        if not subcomponents:
            return component.execute(inputs)

        # If the component has subcomponents, wrap their execute methods
        original_methods = {}
        try:
            # Wrap the execute methods of subcomponents
            for subcomponent in subcomponents:
                original_methods[id(subcomponent)] = subcomponent.execute
                subcomponent.execute = self._create_profiled_execute(
                    subcomponent,
                    original_methods[id(subcomponent)],
                    current_depth + 1,
                    max_depth,
                )

            # Execute the component
            return component.execute(inputs)
        finally:
            # Restore the original execute methods
            for subcomponent in subcomponents:
                if id(subcomponent) in original_methods:
                    subcomponent.execute = original_methods[id(subcomponent)]

    def _create_profiled_execute(
        self,
        component: Any,
        original_execute: Callable,
        depth: int,
        max_depth: int,
    ) -> Callable:
        """Create a profiled execute method for a component.

        Args:
            component: The component
            original_execute: The original execute method
            depth: Current depth of profiling
            max_depth: Maximum depth of profiling

        Returns:
            A wrapped execute method with profiling
        """
        profiler = self

        def profiled_execute(inputs: Dict[str, Any]) -> Any:
            # Start the event
            event_id = profiler._start_event(
                "execute",
                "component",
                {
                    "component_type": type(component).__name__,
                    "depth": depth,
                },
            )

            # Execute the component
            try:
                if depth < max_depth:
                    result = profiler._profile_execution(
                        component,
                        inputs,
                        max_depth,
                        depth,
                    )
                else:
                    result = original_execute(inputs)
                return result
            finally:
                # End the event
                profiler._end_event(event_id)

        return profiled_execute

    def _start_event(
        self,
        name: str,
        event_type: str,
        metadata: Dict[str, Any],
    ) -> int:
        """Start a profiling event.

        Args:
            name: Name of the event
            event_type: Type of the event
            metadata: Additional metadata for the event

        Returns:
            ID of the started event
        """
        # Generate a new event ID
        event_id = self.current_event_id
        self.current_event_id += 1

        # Create the event
        event = ProfilerEvent(
            name=name,
            event_type=event_type,
            timestamp=time.time(),
            metadata=metadata,
            id=event_id,
        )

        # Add the event to the active events
        self.active_events[event_id] = event

        return event_id

    def _end_event(self, event_id: int) -> None:
        """End a profiling event.

        Args:
            event_id: ID of the event to end
        """
        if event_id not in self.active_events:
            return

        # Get the event
        event = self.active_events[event_id]

        # Calculate the duration
        event.duration = time.time() - event.timestamp

        # Add the event to the events list
        self.events.append(event)

        # Remove the event from active events
        del self.active_events[event_id]

    def _record_event(
        self,
        name: str,
        event_type: str,
        metadata: Dict[str, Any],
        duration: Optional[float] = None,
    ) -> None:
        """Record a profiling event.

        Args:
            name: Name of the event
            event_type: Type of the event
            metadata: Additional metadata for the event
            duration: Optional duration of the event
        """
        # Generate a new event ID
        event_id = self.current_event_id
        self.current_event_id += 1

        # Create the event
        event = ProfilerEvent(
            name=name,
            event_type=event_type,
            timestamp=time.time(),
            duration=duration,
            metadata=metadata,
            id=event_id,
        )

        # Add the event to the events list
        self.events.append(event)

    def _build_event_tree(self, event: ProfilerEvent) -> None:
        """Build the event tree for an event.

        Args:
            event: The event to build the tree for
        """
        # Find child events
        children = [e for e in self.events if e.parent_id == event.id]

        # Add children to the event
        event.children = children

        # Recursively build the tree for children
        for child in children:
            self._build_event_tree(child)

    def _event_to_dict(self, event: ProfilerEvent) -> Dict[str, Any]:
        """Convert an event to a dictionary.

        Args:
            event: The event to convert

        Returns:
            Dictionary representation of the event
        """
        return {
            "id": event.id,
            "name": event.name,
            "event_type": event.event_type,
            "timestamp": event.timestamp,
            "duration": event.duration,
            "metadata": event.metadata,
            "parent_id": event.parent_id,
            "children": [self._event_to_dict(child) for child in event.children],
        }

    def _text_summary(self) -> str:
        """Generate a text summary of the profiling results.

        Returns:
            Text summary
        """
        summary = "Profiling Summary\n"
        summary += "================\n\n"

        # Add total duration
        summary += f"Total Duration: {self.total_duration:.4f} seconds\n\n"

        # Add event counts by type
        event_types: Dict[str, int] = {}
        for event in self.events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

        summary += "Event Counts:\n"
        for event_type, count in event_types.items():
            summary += f"- {event_type}: {count}\n"
        summary += "\n"

        # Add slowest events
        events_with_duration = [
            event for event in self.events if event.duration is not None
        ]
        events_with_duration.sort(key=lambda e: e.duration or 0, reverse=True)

        summary += "Slowest Events:\n"
        for i, event in enumerate(events_with_duration[:5]):
            summary += f"{i + 1}. {event.name} ({event.event_type}): "
            summary += f"{event.duration:.4f} seconds\n"

        return summary

    def _markdown_summary(self) -> str:
        """Generate a markdown summary of the profiling results.

        Returns:
            Markdown summary
        """
        summary = "# Profiling Summary\n\n"

        # Add total duration
        summary += f"**Total Duration:** {self.total_duration:.4f} seconds\n\n"

        # Add event counts by type
        event_types: Dict[str, int] = {}
        for event in self.events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

        summary += "## Event Counts\n\n"
        for event_type, count in event_types.items():
            summary += f"- **{event_type}:** {count}\n"
        summary += "\n"

        # Add slowest events
        events_with_duration = [
            event for event in self.events if event.duration is not None
        ]
        events_with_duration.sort(key=lambda e: e.duration or 0, reverse=True)

        summary += "## Slowest Events\n\n"
        for i, event in enumerate(events_with_duration[:5]):
            summary += f"{i + 1}. **{event.name}** ({event.event_type}): "
            summary += f"{event.duration:.4f} seconds\n"

        return summary
