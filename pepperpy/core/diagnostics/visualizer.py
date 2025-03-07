"""Visualizer for PepperPy components and pipelines."""

from typing import Any, Dict, List, Union


class Visualizer:
    """Visualizer for PepperPy components and pipelines.

    This class provides tools for visualizing components, pipelines,
    and their execution flow as diagrams.
    """

    def __init__(self) -> None:
        """Initialize the visualizer."""
        self.node_styles: Dict[str, Dict[str, str]] = {
            "default": {
                "shape": "box",
                "style": "filled",
                "fillcolor": "#f5f5f5",
                "color": "#333333",
                "fontname": "Arial",
                "fontsize": "12",
            },
            "source": {
                "shape": "box",
                "style": "filled",
                "fillcolor": "#e6f3ff",
                "color": "#0066cc",
                "fontname": "Arial",
                "fontsize": "12",
            },
            "processor": {
                "shape": "box",
                "style": "filled",
                "fillcolor": "#fff2e6",
                "color": "#cc6600",
                "fontname": "Arial",
                "fontsize": "12",
            },
            "output": {
                "shape": "box",
                "style": "filled",
                "fillcolor": "#e6ffe6",
                "color": "#006600",
                "fontname": "Arial",
                "fontsize": "12",
            },
            "error": {
                "shape": "box",
                "style": "filled",
                "fillcolor": "#ffe6e6",
                "color": "#cc0000",
                "fontname": "Arial",
                "fontsize": "12",
            },
        }
        self.edge_styles: Dict[str, Dict[str, str]] = {
            "default": {
                "color": "#999999",
                "fontname": "Arial",
                "fontsize": "10",
                "fontcolor": "#666666",
            },
            "data": {
                "color": "#0066cc",
                "fontname": "Arial",
                "fontsize": "10",
                "fontcolor": "#0066cc",
            },
            "control": {
                "color": "#cc6600",
                "style": "dashed",
                "fontname": "Arial",
                "fontsize": "10",
                "fontcolor": "#cc6600",
            },
            "error": {
                "color": "#cc0000",
                "style": "dotted",
                "fontname": "Arial",
                "fontsize": "10",
                "fontcolor": "#cc0000",
            },
        }

    def visualize(
        self,
        component: Any,
        format: str = "svg",
        include_data: bool = True,
        include_config: bool = True,
        theme: str = "light",
        **kwargs: Any,
    ) -> Union[str, bytes]:
        """Visualize a component or pipeline.

        Args:
            component: The component or pipeline to visualize
            format: Output format (svg, png, dot)
            include_data: Whether to include data flow in the visualization
            include_config: Whether to include component configuration
            theme: Visualization theme (light, dark)
            **kwargs: Additional parameters for visualization

        Returns:
            The visualization in the requested format
        """
        # Set the theme
        self._set_theme(theme)

        # Generate the DOT source
        dot_source = self._generate_dot(
            component,
            include_data=include_data,
            include_config=include_config,
            **kwargs,
        )

        # If the format is dot, return the source
        if format.lower() == "dot":
            return dot_source

        # Otherwise, render the visualization
        return self._render_dot(dot_source, format)

    def visualize_execution(
        self,
        execution_data: Dict[str, Any],
        format: str = "svg",
        include_timing: bool = True,
        include_data: bool = False,
        theme: str = "light",
        **kwargs: Any,
    ) -> Union[str, bytes]:
        """Visualize the execution of a component or pipeline.

        Args:
            execution_data: Execution data from a profiler
            format: Output format (svg, png, dot)
            include_timing: Whether to include timing information
            include_data: Whether to include data flow
            theme: Visualization theme (light, dark)
            **kwargs: Additional parameters for visualization

        Returns:
            The visualization in the requested format
        """
        # Set the theme
        self._set_theme(theme)

        # Generate the DOT source
        dot_source = self._generate_execution_dot(
            execution_data,
            include_timing=include_timing,
            include_data=include_data,
            **kwargs,
        )

        # If the format is dot, return the source
        if format.lower() == "dot":
            return dot_source

        # Otherwise, render the visualization
        return self._render_dot(dot_source, format)

    def _set_theme(self, theme: str) -> None:
        """Set the visualization theme.

        Args:
            theme: Theme name (light, dark)
        """
        if theme.lower() == "dark":
            # Dark theme
            self.node_styles["default"]["fillcolor"] = "#2d2d2d"
            self.node_styles["default"]["color"] = "#cccccc"
            self.node_styles["default"]["fontcolor"] = "#ffffff"

            self.node_styles["source"]["fillcolor"] = "#1a3c5a"
            self.node_styles["source"]["color"] = "#4d94ff"
            self.node_styles["source"]["fontcolor"] = "#ffffff"

            self.node_styles["processor"]["fillcolor"] = "#5a3a1a"
            self.node_styles["processor"]["color"] = "#ff9933"
            self.node_styles["processor"]["fontcolor"] = "#ffffff"

            self.node_styles["output"]["fillcolor"] = "#1a5a1a"
            self.node_styles["output"]["color"] = "#33cc33"
            self.node_styles["output"]["fontcolor"] = "#ffffff"

            self.node_styles["error"]["fillcolor"] = "#5a1a1a"
            self.node_styles["error"]["color"] = "#ff3333"
            self.node_styles["error"]["fontcolor"] = "#ffffff"

            self.edge_styles["default"]["color"] = "#666666"
            self.edge_styles["default"]["fontcolor"] = "#999999"

            self.edge_styles["data"]["color"] = "#4d94ff"
            self.edge_styles["data"]["fontcolor"] = "#4d94ff"

            self.edge_styles["control"]["color"] = "#ff9933"
            self.edge_styles["control"]["fontcolor"] = "#ff9933"

            self.edge_styles["error"]["color"] = "#ff3333"
            self.edge_styles["error"]["fontcolor"] = "#ff3333"
        else:
            # Light theme (default)
            self.node_styles["default"]["fillcolor"] = "#f5f5f5"
            self.node_styles["default"]["color"] = "#333333"
            self.node_styles["default"]["fontcolor"] = "#000000"

            self.node_styles["source"]["fillcolor"] = "#e6f3ff"
            self.node_styles["source"]["color"] = "#0066cc"
            self.node_styles["source"]["fontcolor"] = "#000000"

            self.node_styles["processor"]["fillcolor"] = "#fff2e6"
            self.node_styles["processor"]["color"] = "#cc6600"
            self.node_styles["processor"]["fontcolor"] = "#000000"

            self.node_styles["output"]["fillcolor"] = "#e6ffe6"
            self.node_styles["output"]["color"] = "#006600"
            self.node_styles["output"]["fontcolor"] = "#000000"

            self.node_styles["error"]["fillcolor"] = "#ffe6e6"
            self.node_styles["error"]["color"] = "#cc0000"
            self.node_styles["error"]["fontcolor"] = "#000000"

            self.edge_styles["default"]["color"] = "#999999"
            self.edge_styles["default"]["fontcolor"] = "#666666"

            self.edge_styles["data"]["color"] = "#0066cc"
            self.edge_styles["data"]["fontcolor"] = "#0066cc"

            self.edge_styles["control"]["color"] = "#cc6600"
            self.edge_styles["control"]["fontcolor"] = "#cc6600"

            self.edge_styles["error"]["color"] = "#cc0000"
            self.edge_styles["error"]["fontcolor"] = "#cc0000"

    def _generate_dot(
        self,
        component: Any,
        include_data: bool = True,
        include_config: bool = True,
        **kwargs: Any,
    ) -> str:
        """Generate DOT source for a component or pipeline.

        Args:
            component: The component or pipeline to visualize
            include_data: Whether to include data flow
            include_config: Whether to include component configuration
            **kwargs: Additional parameters for visualization

        Returns:
            DOT source for the visualization
        """
        # Start the DOT source
        dot = [
            "digraph G {",
            "  rankdir=LR;",
            "  node [shape=box, style=filled, fontname=Arial];",
            "  edge [fontname=Arial];",
        ]

        # Check if the component is a pipeline
        if hasattr(component, "components") and hasattr(component, "connections"):
            # It's a pipeline, visualize it
            self._add_pipeline_to_dot(
                dot,
                component,
                include_data=include_data,
                include_config=include_config,
                **kwargs,
            )
        else:
            # It's a single component, visualize it
            self._add_component_to_dot(
                dot,
                component,
                "component",
                include_config=include_config,
                **kwargs,
            )

        # End the DOT source
        dot.append("}")

        return "\n".join(dot)

    def _generate_execution_dot(
        self,
        execution_data: Dict[str, Any],
        include_timing: bool = True,
        include_data: bool = False,
        **kwargs: Any,
    ) -> str:
        """Generate DOT source for execution visualization.

        Args:
            execution_data: Execution data from a profiler
            include_timing: Whether to include timing information
            include_data: Whether to include data flow
            **kwargs: Additional parameters for visualization

        Returns:
            DOT source for the visualization
        """
        # Start the DOT source
        dot = [
            "digraph G {",
            "  rankdir=LR;",
            "  node [shape=box, style=filled, fontname=Arial];",
            "  edge [fontname=Arial];",
        ]

        # Add execution events to the DOT source
        self._add_execution_to_dot(
            dot,
            execution_data,
            include_timing=include_timing,
            include_data=include_data,
            **kwargs,
        )

        # End the DOT source
        dot.append("}")

        return "\n".join(dot)

    def _add_pipeline_to_dot(
        self,
        dot: List[str],
        pipeline: Any,
        include_data: bool = True,
        include_config: bool = True,
        **kwargs: Any,
    ) -> None:
        """Add a pipeline to the DOT source.

        Args:
            dot: DOT source lines
            pipeline: The pipeline to visualize
            include_data: Whether to include data flow
            include_config: Whether to include component configuration
            **kwargs: Additional parameters for visualization
        """
        # Add the pipeline components
        for component in pipeline.components:
            component_type = component.get("type", "default")
            component_name = component.get("name", "unknown")

            # Determine the node style
            node_style = self.node_styles.get(
                component_type, self.node_styles["default"]
            )

            # Build the node attributes
            attrs = []
            for key, value in node_style.items():
                attrs.append(f'{key}="{value}"')

            # Add the component label
            label = component_name
            if include_config and "config" in component:
                config_str = self._format_config(component["config"])
                label += f"\\n{config_str}"

            attrs.append(f'label="{label}"')

            # Add the node to the DOT source
            dot.append(f'  "{component_name}" [{", ".join(attrs)}];')

        # Add the pipeline connections
        for connection in pipeline.connections:
            source = connection.get("source", "")
            target = connection.get("target", "")

            if not source or not target:
                continue

            # Determine the edge style
            edge_style = self.edge_styles.get("data", self.edge_styles["default"])

            # Build the edge attributes
            attrs = []
            for key, value in edge_style.items():
                attrs.append(f'{key}="{value}"')

            # Add the edge label
            label = ""
            if include_data and "data" in connection:
                label = self._format_data(connection["data"])
                attrs.append(f'label="{label}"')

            # Add the edge to the DOT source
            dot.append(f'  "{source}" -> "{target}" [{", ".join(attrs)}];')

    def _add_component_to_dot(
        self,
        dot: List[str],
        component: Any,
        component_id: str,
        include_config: bool = True,
        **kwargs: Any,
    ) -> None:
        """Add a component to the DOT source.

        Args:
            dot: DOT source lines
            component: The component to visualize
            component_id: ID for the component node
            include_config: Whether to include component configuration
            **kwargs: Additional parameters for visualization
        """
        # Determine the component type
        component_type = getattr(component, "type", "default")
        component_name = getattr(component, "name", type(component).__name__)

        # Determine the node style
        node_style = self.node_styles.get(component_type, self.node_styles["default"])

        # Build the node attributes
        attrs = []
        for key, value in node_style.items():
            attrs.append(f'{key}="{value}"')

        # Add the component label
        label = component_name
        if include_config and hasattr(component, "config"):
            config_str = self._format_config(component.config)
            label += f"\\n{config_str}"

        attrs.append(f'label="{label}"')

        # Add the node to the DOT source
        dot.append(f'  "{component_id}" [{", ".join(attrs)}];')

    def _add_execution_to_dot(
        self,
        dot: List[str],
        execution_data: Dict[str, Any],
        include_timing: bool = True,
        include_data: bool = False,
        **kwargs: Any,
    ) -> None:
        """Add execution events to the DOT source.

        Args:
            dot: DOT source lines
            execution_data: Execution data from a profiler
            include_timing: Whether to include timing information
            include_data: Whether to include data flow
            **kwargs: Additional parameters for visualization
        """
        # Add the execution events
        events = execution_data.get("events", [])

        # Create a map of event IDs to events
        event_map = {event.get("id"): event for event in events if "id" in event}

        # Add nodes for each event
        for event in events:
            event_id = event.get("id")
            if event_id is None:
                continue

            event_name = event.get("name", "unknown")
            event_type = event.get("event_type", "default")

            # Determine the node style
            node_style = self.node_styles.get(event_type, self.node_styles["default"])

            # Build the node attributes
            attrs = []
            for key, value in node_style.items():
                attrs.append(f'{key}="{value}"')

            # Add the event label
            label = event_name
            if include_timing and "duration" in event:
                duration = event.get("duration", 0)
                label += f"\\n{duration:.4f}s"

            attrs.append(f'label="{label}"')

            # Add the node to the DOT source
            dot.append(f'  "event_{event_id}" [{", ".join(attrs)}];')

        # Add edges for parent-child relationships
        for event in events:
            event_id = event.get("id")
            parent_id = event.get("parent_id")

            if event_id is None or parent_id is None:
                continue

            # Determine the edge style
            edge_style = self.edge_styles.get("control", self.edge_styles["default"])

            # Build the edge attributes
            attrs = []
            for key, value in edge_style.items():
                attrs.append(f'{key}="{value}"')

            # Add the edge to the DOT source
            dot.append(
                f'  "event_{parent_id}" -> "event_{event_id}" [{", ".join(attrs)}];'
            )

        # Add edges for data flow
        if include_data:
            # This would require additional information about data flow between events
            pass

    def _format_config(self, config: Dict[str, Any]) -> str:
        """Format component configuration for display.

        Args:
            config: Component configuration

        Returns:
            Formatted configuration string
        """
        # Format the configuration as a simple string
        parts = []
        for key, value in config.items():
            # Truncate long values
            value_str = str(value)
            if len(value_str) > 20:
                value_str = value_str[:17] + "..."

            parts.append(f"{key}: {value_str}")

        return "\\n".join(parts)

    def _format_data(self, data: Any) -> str:
        """Format data for display.

        Args:
            data: Data to format

        Returns:
            Formatted data string
        """
        # Format the data as a simple string
        if isinstance(data, dict):
            return ", ".join(data.keys())
        elif isinstance(data, list):
            return f"{len(data)} items"
        else:
            # Truncate long values
            value_str = str(data)
            if len(value_str) > 20:
                value_str = value_str[:17] + "..."

            return value_str

    def _render_dot(self, dot_source: str, format: str) -> Union[str, bytes]:
        """Render DOT source to the requested format.

        Args:
            dot_source: DOT source to render
            format: Output format (svg, png)

        Returns:
            Rendered visualization
        """
        # This would use a library like graphviz to render the DOT source
        # For now, we'll return a placeholder
        if format.lower() == "svg":
            return "<svg><!-- SVG visualization would be here --></svg>"
        elif format.lower() == "png":
            return b"PNG visualization would be here"
        else:
            return dot_source
