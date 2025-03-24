"""Component implementations for PepperPy workflows.

This module provides the core component abstractions and registry for workflow
management, allowing for dynamic component creation and configuration.

Example:
    >>> from pepperpy.workflow.components import ComponentRegistry, Component
    >>> registry = ComponentRegistry()
    >>> registry.register(
    ...     name="text_processor",
    ...     component_type=ComponentType.PROCESSOR,
    ...     config={"max_length": 100}
    ... )
    >>> component = registry.create("text_processor")
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from pepperpy.core import PepperpyError
from pepperpy.workflow.base import ComponentType, WorkflowComponent


class ComponentError(PepperpyError):
    """Base exception for component-related errors.

    Example:
        >>> try:
        ...     registry.get("unknown_component")
        ... except ComponentError as e:
        ...     print(f"Component error: {e}")
    """

    pass


@dataclass
class ComponentConfig:
    """Configuration for a workflow component.

    Args:
        type: Component type
        config: Component configuration
        metadata: Optional component metadata

    Example:
        >>> config = ComponentConfig(
        ...     type=ComponentType.PROCESSOR,
        ...     config={"max_length": 100},
        ...     metadata={"version": "1.0"}
        ... )
    """

    type: ComponentType
    config: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class Component(WorkflowComponent):
    """Base implementation of a workflow component.

    Example:
        >>> component = Component(
        ...     name="text_processor",
        ...     type=ComponentType.PROCESSOR,
        ...     config={"max_length": 100}
        ... )
    """

    def __init__(
        self,
        name: str,
        type: ComponentType,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a component.

        Args:
            name: Component name
            type: Component type
            config: Optional component configuration
            metadata: Optional component metadata
        """
        super().__init__(
            id=f"{name}_{type.value}",
            name=name,
            type=type,
            config=config or {},
            metadata=metadata,
        )


class ComponentRegistry:
    """Registry for workflow components.

    The registry maintains a collection of available components and
    their configurations, allowing for dynamic component creation
    and management.

    Example:
        >>> registry = ComponentRegistry()
        >>> registry.register(
        ...     name="text_processor",
        ...     component_type=ComponentType.PROCESSOR,
        ...     config={"max_length": 100}
        ... )
        >>> component = registry.create("text_processor")
    """

    def __init__(self) -> None:
        """Initialize the component registry."""
        self._components: Dict[str, ComponentConfig] = {}

    def register(
        self,
        name: str,
        component_type: ComponentType,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a new component configuration.

        Args:
            name: Component name
            component_type: Component type
            config: Optional component configuration
            metadata: Optional component metadata

        Raises:
            ComponentError: If component already exists

        Example:
            >>> registry.register(
            ...     name="text_processor",
            ...     component_type=ComponentType.PROCESSOR,
            ...     config={"max_length": 100}
            ... )
        """
        if name in self._components:
            raise ComponentError(f"Component {name} already registered")

        self._components[name] = ComponentConfig(
            type=component_type,
            config=config or {},
            metadata=metadata,
        )

    @staticmethod
    def rss(url: str, **kwargs: Any) -> Source:
        """Create an RSS feed source component.

        Args:
            url: RSS feed URL
            **kwargs: Additional configuration options

        Returns:
            RSS source component
        """
        return Source(
            id=str(uuid.uuid4()),
            name=f"rss_source_{str(uuid.uuid4())[:8]}",
            config={"url": url, **kwargs},
        )

    @staticmethod
    def api(url: str, method: str = "GET", **kwargs: Any) -> Source:
        """Create an API source component.

        Args:
            url: API endpoint URL
            method: HTTP method (default: GET)
            **kwargs: Additional configuration options

        Returns:
            API source component
        """
        return Source(
            id=str(uuid.uuid4()),
            name=f"api_source_{str(uuid.uuid4())[:8]}",
            config={"url": url, "method": method, **kwargs},
        )


class Processors:
    """Collection of processor components."""

    @staticmethod
    def summarize(max_length: int = 100, **kwargs: Any) -> Processor:
        """Create a text summarization processor.

        Args:
            max_length: Maximum summary length
            **kwargs: Additional configuration options

        Returns:
            Summarization processor
        """
        return Processor(
            id=str(uuid.uuid4()),
            name=f"summarizer_{str(uuid.uuid4())[:8]}",
            config={"max_length": max_length, **kwargs},
        )

    @staticmethod
    def translate(
        target_language: str,
        source_language: Optional[str] = None,
        **kwargs: Any,
    ) -> Processor:
        """Create a translation processor.

        Args:
            target_language: Target language code
            source_language: Optional source language code
            **kwargs: Additional configuration options

        Returns:
            Translation processor
        """
        return Processor(
            id=str(uuid.uuid4()),
            name=f"translator_{str(uuid.uuid4())[:8]}",
            config={
                "target_language": target_language,
                "source_language": source_language,
                **kwargs,
            },
        )

    @staticmethod
    def extract_keywords(
        max_keywords: int = 5,
        min_length: int = 3,
        **kwargs: Any,
    ) -> Processor:
        """Create a keyword extraction processor.

        Args:
            max_keywords: Maximum number of keywords
            min_length: Minimum keyword length
            **kwargs: Additional configuration options

        Returns:
            Keyword extraction processor
        """
        return Processor(
            id=str(uuid.uuid4()),
            name=f"keyword_extractor_{str(uuid.uuid4())[:8]}",
            config={
                "max_keywords": max_keywords,
                "min_length": min_length,
                **kwargs,
            },
        )

    @staticmethod
    def sentiment_analysis(**kwargs: Any) -> Processor:
        """Create a sentiment analysis processor.

        Args:
            **kwargs: Configuration options

        Returns:
            Sentiment analysis processor
        """
        return Processor(
            id=str(uuid.uuid4()),
            name=f"sentiment_analyzer_{str(uuid.uuid4())[:8]}",
            config=kwargs,
        )

    @staticmethod
    def ner(
        entity_types: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Processor:
        """Create a named entity recognition processor.

        Args:
            entity_types: Optional list of entity types to extract
            **kwargs: Additional configuration options

        Returns:
            NER processor
        """
        return Processor(
            id=str(uuid.uuid4()),
            name=f"ner_{str(uuid.uuid4())[:8]}",
            config={"entity_types": entity_types, **kwargs},
        )


class Outputs:
    """Collection of output components."""

    @staticmethod
    def file(
        path: Union[str, Path],
        mode: str = "w",
        encoding: str = "utf-8",
        **kwargs: Any,
    ) -> Output:
        """Create a file output component.

        Args:
            path: File path
            mode: File open mode (default: w)
            encoding: File encoding (default: utf-8)
            **kwargs: Additional configuration options

        Returns:
            File output component
        """
        return Output(
            id=str(uuid.uuid4()),
            name=f"file_output_{str(uuid.uuid4())[:8]}",
            config={
                "path": str(path),
                "mode": mode,
                "encoding": encoding,
                **kwargs,
            },
        )

    @staticmethod
    def api(
        url: str,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Output:
        """Create an API output component.

        Args:
            url: API endpoint URL
            method: HTTP method (default: POST)
            headers: Optional request headers
            **kwargs: Additional configuration options

        Returns:
            API output component
        """
        return Output(
            id=str(uuid.uuid4()),
            name=f"api_output_{str(uuid.uuid4())[:8]}",
            config={
                "url": url,
                "method": method,
                "headers": headers,
                **kwargs,
            },
        )

    @staticmethod
    def database(
        connection_string: str,
        table: str,
        **kwargs: Any,
    ) -> Output:
        """Create a database output component.

        Args:
            connection_string: Database connection string
            table: Target table name
            **kwargs: Additional configuration options

        Returns:
            Database output component
        """
        return Output(
            id=str(uuid.uuid4()),
            name=f"db_output_{str(uuid.uuid4())[:8]}",
            config={
                "connection_string": connection_string,
                "table": table,
                **kwargs,
            },
        )

    @staticmethod
    def podcast(
        path: Union[str, Path],
        voice: str = "en-US",
        **kwargs: Any,
    ) -> Output:
        """Create a podcast output component.

        Args:
            path: Output file path
            voice: Voice identifier (default: en-US)
            **kwargs: Additional configuration options

        Returns:
            Podcast output component
        """
        return Output(
            id=str(uuid.uuid4()),
            name=f"podcast_output_{str(uuid.uuid4())[:8]}",
            config={
                "path": str(path),
                "voice": voice,
                **kwargs,
            },
        )


class Agents:
    """Collection of AI agent components."""

    @staticmethod
    def chat(
        system_prompt: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> Agent:
        """Create a chat agent component.

        Args:
            system_prompt: System prompt for the agent
            model: Model identifier (default: gpt-4)
            temperature: Sampling temperature (default: 0.7)
            **kwargs: Additional configuration options

        Returns:
            Chat agent component
        """
        return Agent(
            id=str(uuid.uuid4()),
            name=f"chat_agent_{str(uuid.uuid4())[:8]}",
            config={
                "system_prompt": system_prompt,
                "model": model,
                "temperature": temperature,
                **kwargs,
            },
        )

    @staticmethod
    def task(
        task_description: str,
        tools: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Agent:
        """Create a task agent component.

        Args:
            task_description: Description of the task
            tools: Optional list of tool names
            **kwargs: Additional configuration options

        Returns:
            Task agent component
        """
        return Agent(
            id=str(uuid.uuid4()),
            name=f"task_agent_{str(uuid.uuid4())[:8]}",
            config={
                "task_description": task_description,
                "tools": tools,
                **kwargs,
            },
        )

    @staticmethod
    def rag(
        collection_name: str,
        query_type: str = "similarity",
        **kwargs: Any,
    ) -> Agent:
        """Create a RAG agent component.

        Args:
            collection_name: Vector store collection name
            query_type: Query type (default: similarity)
            **kwargs: Additional configuration options

        Returns:
            RAG agent component
        """
        return Agent(
            id=str(uuid.uuid4()),
            name=f"rag_agent_{str(uuid.uuid4())[:8]}",
            config={
                "collection_name": collection_name,
                "query_type": query_type,
                **kwargs,
            },
        )
