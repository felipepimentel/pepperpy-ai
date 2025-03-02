"""Base classes for the generation components of the RAG system.

This module provides the base classes and interfaces for the generation components.
"""

from abc import abstractmethod
from typing import Dict, List, Optional

from pepperpy.core.logging import get_logger
from pepperpy.rag.base import RagComponent
from pepperpy.rag.types import RagComponentType, RagContext, RagResponse

logger = get_logger(__name__)


class Generator(RagComponent):
    """Base class for generation components."""

    component_type = RagComponentType.GENERATOR

    @abstractmethod
    async def generate(self, context: RagContext) -> RagResponse:
        """Generate a response from the given context.

        Args:
            context: The RAG context containing the query and search results

        Returns:
            The generated response
        """
        pass


class PromptGenerator(Generator):
    """Generator that uses prompt templates to generate responses."""

    def __init__(
        self, component_id: str, name: str, prompt_template: str, description: str = ""
    ):
        """Initialize the prompt generator.

        Args:
            component_id: Unique identifier for the component
            name: Human-readable name for the component
            prompt_template: The prompt template to use for generation
            description: Description of the component's functionality
        """
        super().__init__(component_id, name, description)
        self.prompt_template = prompt_template

    async def initialize(self) -> None:
        """Initialize the prompt generator."""
        logger.info(f"Initializing prompt generator: {self.name}")
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up the prompt generator."""
        logger.info(f"Cleaning up prompt generator: {self.name}")
        await super().cleanup()

    def format_prompt(self, context: RagContext) -> str:
        """Format the prompt template with the context.

        Args:
            context: The RAG context

        Returns:
            The formatted prompt
        """
        # This is a simple implementation that can be overridden by subclasses
        # to provide more sophisticated prompt formatting
        query = context.query.query

        # Format context from search results
        context_str = "\n\n".join(
            [
                f"[{i + 1}] {result.chunk.content}"
                for i, result in enumerate(context.results)
            ]
        )

        return self.prompt_template.format(query=query, context=context_str)


class ContextAwareGenerator(Generator):
    """Generator that is aware of the context and can use it to generate responses."""

    @abstractmethod
    async def generate_with_context(self, query: str, context_chunks: List[str]) -> str:
        """Generate a response using the query and context chunks.

        Args:
            query: The query string
            context_chunks: The context chunks to use for generation

        Returns:
            The generated response text
        """
        pass

    async def generate(self, context: RagContext) -> RagResponse:
        """Generate a response from the given context.

        Args:
            context: The RAG context containing the query and search results

        Returns:
            The generated response
        """
        query = context.query.query
        context_chunks = [result.chunk.content for result in context.results]

        response_text = await self.generate_with_context(query, context_chunks)

        return RagResponse(query=context.query, response=response_text, context=context)


class GenerationManager(RagComponent):
    """Manager for generation operations."""

    component_type = RagComponentType.GENERATION_MANAGER

    def __init__(self, component_id: str, name: str, description: str = ""):
        """Initialize the generation manager.

        Args:
            component_id: Unique identifier for the component
            name: Human-readable name for the component
            description: Description of the component's functionality
        """
        super().__init__(component_id, name, description)
        self.generators: Dict[str, Generator] = {}
        self.default_generator: Optional[str] = None

    def add_generator(self, generator: Generator, set_as_default: bool = False) -> None:
        """Add a generator to the manager.

        Args:
            generator: The generator to add
            set_as_default: Whether to set this generator as the default
        """
        self.generators[generator.component_id] = generator
        logger.debug(f"Added generator {generator.name} to manager {self.name}")

        if set_as_default or self.default_generator is None:
            self.default_generator = generator.component_id
            logger.debug(f"Set {generator.name} as default generator")

    def get_generator(self, generator_id: str) -> Optional[Generator]:
        """Get a generator by ID.

        Args:
            generator_id: The ID of the generator to get

        Returns:
            The generator if found, None otherwise
        """
        return self.generators.get(generator_id)

    async def initialize(self) -> None:
        """Initialize all generators."""
        logger.info(f"Initializing generation manager: {self.name}")
        for generator in self.generators.values():
            await generator.initialize()
        await super().initialize()

    async def cleanup(self) -> None:
        """Clean up all generators."""
        logger.info(f"Cleaning up generation manager: {self.name}")
        for generator in self.generators.values():
            await generator.cleanup()
        await super().cleanup()

    async def generate(
        self, context: RagContext, generator_id: Optional[str] = None
    ) -> RagResponse:
        """Generate a response using the specified generator or the default.

        Args:
            context: The RAG context
            generator_id: The ID of the generator to use, or None to use the default

        Returns:
            The generated response
        """
        if generator_id is None:
            if self.default_generator is None:
                raise ValueError("No default generator set")
            generator_id = self.default_generator

        generator = self.get_generator(generator_id)
        if generator is None:
            raise ValueError(f"Generator not found: {generator_id}")

        return await generator.generate(context)
