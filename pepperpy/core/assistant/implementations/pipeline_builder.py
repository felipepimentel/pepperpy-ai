"""Pipeline builder assistant implementation."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from pepperpy.core.assistant.base import BaseAssistant
from pepperpy.core.assistant.templates import get_template, list_templates
from pepperpy.pipeline.base import Pipeline


class PipelineBuilderAssistant(BaseAssistant[Pipeline]):
    """Assistant for building pipelines.

    This assistant helps users create and configure pipelines through
    interactive guidance, templates, and natural language descriptions.
    """

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the pipeline builder assistant.

        Args:
            name: Name of the assistant
            config: Configuration for the assistant
            **kwargs: Additional arguments for the base assistant
        """
        super().__init__(name=name, config=config, **kwargs)
        self.logger = logging.getLogger(f"{__name__}.{name}")

    async def initialize(self) -> None:
        """Initialize the pipeline builder assistant.

        This method is called before using the assistant.
        """
        self.logger.info(f"Initializing {self.name}")
        # Simulate initialization
        await asyncio.sleep(0.1)

    def create(self, description: str, **kwargs: Any) -> Pipeline:
        """Create a pipeline based on the description.

        This method supports several ways to create a pipeline:
        1. From a template name (e.g., "rag_basic")
        2. From a natural language description (e.g., "a pipeline for question answering")
        3. From a specific configuration (passed via kwargs)

        Args:
            description: Description of the pipeline to create
            **kwargs: Additional parameters for creation
                - template_category: Optional category to filter templates
                - components: Optional list of component configurations
                - connections: Optional list of component connections

        Returns:
            The created pipeline

        Examples:
            >>> assistant = PipelineBuilderAssistant("my_assistant")
            >>> # Create from template
            >>> pipeline = assistant.create("rag_basic")
            >>> # Create from description
            >>> pipeline = assistant.create("a pipeline for question answering")
        """
        self._trigger_callback("start", {"description": description})
        self._add_to_history("create", {"description": description})

        # Check if the description is a template name
        try:
            template = get_template(
                description,
                category=kwargs.get("template_category"),
                custom_path=self.config.get("custom_templates_path"),
            )
            return self._create_from_template(template)
        except ValueError:
            # Not a template name, continue with other methods
            pass

        # Check if components and connections are provided
        if "components" in kwargs and "connections" in kwargs:
            return self._create_from_config(
                kwargs["components"],
                kwargs["connections"],
            )

        # Create from natural language description
        return self._create_from_description(description)

    def modify(self, pipeline: Pipeline, description: str, **kwargs: Any) -> Pipeline:
        """Modify an existing pipeline based on the description.

        Args:
            pipeline: Pipeline to modify
            description: Description of the modifications
            **kwargs: Additional parameters for modification
                - add_components: Optional list of components to add
                - remove_components: Optional list of component names to remove
                - update_components: Optional dict of component updates
                - add_connections: Optional list of connections to add
                - remove_connections: Optional list of connection indices to remove

        Returns:
            The modified pipeline
        """
        self._trigger_callback("start", {"description": description})
        self._add_to_history("modify", {"description": description})

        # Create a copy of the pipeline to modify
        modified_pipeline = pipeline.copy()

        # Apply modifications based on kwargs
        if "add_components" in kwargs:
            for component in kwargs["add_components"]:
                modified_pipeline.add_component(component)

        if "remove_components" in kwargs:
            for component_name in kwargs["remove_components"]:
                modified_pipeline.remove_component(component_name)

        if "update_components" in kwargs:
            for component_name, updates in kwargs["update_components"].items():
                modified_pipeline.update_component(component_name, updates)

        if "add_connections" in kwargs:
            for connection in kwargs["add_connections"]:
                modified_pipeline.add_connection(connection)

        if "remove_connections" in kwargs:
            for connection_idx in kwargs["remove_connections"]:
                modified_pipeline.remove_connection(connection_idx)

        self._trigger_callback("complete", {"pipeline": modified_pipeline})
        return modified_pipeline

    def explain(self, pipeline: Pipeline, **kwargs: Any) -> str:
        """Explain a pipeline.

        Args:
            pipeline: Pipeline to explain
            **kwargs: Additional parameters for explanation
                - format: Output format (text, json, markdown)
                - include_components: Whether to include component details
                - include_connections: Whether to include connection details

        Returns:
            Explanation of the pipeline
        """
        self._trigger_callback("start", {"pipeline": pipeline})
        self._add_to_history("explain", {"pipeline_id": id(pipeline)})

        # Get the output format
        output_format = kwargs.get("format", "text")
        include_components = kwargs.get("include_components", True)
        include_connections = kwargs.get("include_connections", True)

        # Get pipeline information
        pipeline_info = {
            "name": pipeline.name,
            "description": getattr(pipeline, "description", ""),
            "components": getattr(pipeline, "components", [])
            if include_components
            else [],
            "connections": getattr(pipeline, "connections", [])
            if include_connections
            else [],
        }

        # Format the output
        if output_format == "json":
            explanation = json.dumps(pipeline_info, indent=2)
        elif output_format == "markdown":
            explanation = self._format_markdown(pipeline_info)
        else:
            explanation = self._format_text(pipeline_info)

        self._trigger_callback("complete", {"explanation": explanation})
        return explanation

    def _create_from_template(self, template: Dict[str, Any]) -> Pipeline:
        """Create a pipeline from a template.

        Args:
            template: Template configuration

        Returns:
            The created pipeline
        """
        # Extract components and connections from the template
        components = template.get("components", {})
        pipeline_config = template.get("pipeline", {})

        # Create the pipeline with default processors
        pipeline = Pipeline(
            template.get("metadata", {}).get("name", "Pipeline from template"),
            processors=[],
        )

        # Set the description
        pipeline.description = template.get("metadata", {}).get("description", "")

        # Add components
        for name, config in components.items():
            pipeline.add_component(name, config)

        # Add connections for each stage
        for stage_name, connections in pipeline_config.items():
            for connection in connections:
                pipeline.add_connection(connection)

        self._trigger_callback("complete", {"pipeline": pipeline})
        return pipeline

    def _create_from_config(
        self,
        components: List[Dict[str, Any]],
        connections: List[Dict[str, Any]],
    ) -> Pipeline:
        """Create a pipeline from a configuration.

        Args:
            components: List of component configurations
            connections: List of component connections

        Returns:
            The created pipeline
        """
        # Create the pipeline with default processors
        pipeline = Pipeline(
            "Pipeline from config",
            processors=[],
        )

        # Set the description
        pipeline.description = "Pipeline created from explicit configuration"

        # Add components
        for component in components:
            pipeline.add_component(component)

        # Add connections
        for connection in connections:
            pipeline.add_connection(connection)

        self._trigger_callback("complete", {"pipeline": pipeline})
        return pipeline

    def _create_from_description(self, description: str) -> Pipeline:
        """Create a pipeline from a natural language description.

        Args:
            description: Natural language description of the pipeline

        Returns:
            The created pipeline
        """
        # In a real implementation, this would use an LLM to generate a pipeline
        # configuration based on the description. For now, we'll use a simple
        # heuristic to select a template.

        # Get all templates
        templates = list_templates(
            custom_path=self.config.get("custom_templates_path"),
        )

        # Find a template that matches the description
        for template_meta in templates:
            if any(
                keyword in description.lower()
                for keyword in [
                    template_meta.get("name", "").lower(),
                    template_meta.get("category", "").lower(),
                ]
            ):
                template = get_template(
                    template_meta.get("name", ""),
                    custom_path=self.config.get("custom_templates_path"),
                )
                return self._create_from_template(template)

        # If no template matches, create a minimal pipeline with default processors
        pipeline = Pipeline(
            "Pipeline from description",
            processors=[],
        )

        # Set the description
        pipeline.description = description

        self._trigger_callback("complete", {"pipeline": pipeline})
        return pipeline

    def _format_markdown(self, pipeline_info: Dict[str, Any]) -> str:
        """Format pipeline information as markdown.

        Args:
            pipeline_info: Pipeline information

        Returns:
            Markdown-formatted explanation
        """
        markdown = f"# {pipeline_info['name']}\n\n"
        markdown += f"{pipeline_info['description']}\n\n"

        if pipeline_info.get("components"):
            markdown += "## Components\n\n"
            for component in pipeline_info["components"]:
                markdown += f"### {component['name']}\n\n"
                markdown += f"Type: {component.get('type', 'Unknown')}\n\n"
                if "config" in component:
                    markdown += "Configuration:\n```json\n"
                    markdown += json.dumps(component["config"], indent=2)
                    markdown += "\n```\n\n"

        if pipeline_info.get("connections"):
            markdown += "## Connections\n\n"
            for i, connection in enumerate(pipeline_info["connections"]):
                markdown += f"{i + 1}. {connection.get('source', '')} -> "
                markdown += f"{connection.get('target', '')}\n"

        return markdown

    def _format_text(self, pipeline_info: Dict[str, Any]) -> str:
        """Format pipeline information as plain text.

        Args:
            pipeline_info: Pipeline information

        Returns:
            Text-formatted explanation
        """
        text = f"Pipeline: {pipeline_info['name']}\n"
        text += f"Description: {pipeline_info['description']}\n\n"

        if pipeline_info.get("components"):
            text += "Components:\n"
            for component in pipeline_info["components"]:
                text += f"- {component['name']} "
                text += f"(Type: {component.get('type', 'Unknown')})\n"

        if pipeline_info.get("connections"):
            text += "\nConnections:\n"
            for i, connection in enumerate(pipeline_info["connections"]):
                text += f"{i + 1}. {connection.get('source', '')} -> "
                text += f"{connection.get('target', '')}\n"

        return text
