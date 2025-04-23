"""Transformers-based semantic processor implementation."""

import logging
import re
from typing import list, Any

from transformers import Pipeline, pipeline

from pepperpy.content.base import (
    Entity,
    Relationship,
    SemanticExtractionResult,
    SemanticProcessorProvider,
)
from pepperpy.core.base import PepperpyError
from pepperpy.content.base import ContentError
from pepperpy.content import ContentProvider
from pepperpy.content.base import ContentError

logger = logging.getLogger(__name__)

logger = logger.getLogger(__name__)


class TransformersSemanticProcessor(class TransformersSemanticProcessor(SemanticProcessorProvider):
    """Semantic processor using Hugging Face Transformers."""):
    """
    Content transformerssemanticprocessor provider.
    
    This provider implements transformerssemanticprocessor functionality for the PepperPy content framework.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize processor.

        Args:
            **kwargs: Configuration options
        """
        super().__init__(**kwargs)
        self.model_name: str = kwargs.get("model_name", "dslim/bert-base-NER")
        self.rel_model_name: str = kwargs.get(
            "rel_model_name", "Jean-Baptiste/roberta-large-ner-english"
        )
        self._extract_relationships: bool = kwargs.get("extract_relationships", False)
        self.chunk_size: int = kwargs.get("chunk_size", 100000)
        self.aggregation_strategy: str = kwargs.get("aggregation_strategy", "simple")
        self.ner_pipeline: Pipeline | None = None
        self.rel_pipeline: Pipeline | None = None
        self.initialized: bool = False

    async def initialize(self) -> None:
 """Initialize the provider.

        This method is called automatically when the provider is first used.
        It sets up resources needed by the provider.
 """
        if self.initialized:
            return

        try:
            # Initialize NER pipeline
            self.ner_pipeline = pipeline(
                "ner",
                model=self.model_name,
                aggregation_strategy=self.aggregation_strategy,
            )

            # Initialize relationship extraction pipeline if requested
            if self._extract_relationships:
                self.rel_pipeline = pipeline(
                    "text-classification",
                    model=self.rel_model_name,
                )

            self.initialized = True
            logger.debug(
                f"Initialized transformers processor with model {self.model_name}"
            )

        except Exception as e:
            raise PepperpyError(f"Error initializing transformers processor: {e}")

    async def cleanup(self) -> None:
 """Clean up provider resources.

        This method is called automatically when the context manager exits.
        It releases any resources acquired during initialization.
 """
        self.ner_pipeline = None
        self.rel_pipeline = None
        self.initialized = False

    async def process_text(self, text: str, **kwargs: Any) -> SemanticExtractionResult:
        """Process text to extract semantic information.

        Args:
            text: Text to process
            **kwargs: Additional processor-specific parameters

        Returns:
            Semantic extraction result
        """
        if not self.initialized or not self.ner_pipeline:
            await self.initialize()

        if not self.ner_pipeline:  # Double check after initialization
            raise PepperpyError("Failed to initialize transformers processor")

        try:
            # Process in chunks if text is very large
            if len(text) > self.chunk_size:
                return await self._process_text_in_chunks(text, **kwargs)

            # Initialize result
            result = SemanticExtractionResult(text=text)

            # Extract entities
            entities = self.ner_pipeline(text)
            for entity in entities:
                ent = Entity(
                    text=entity["word"],
                    label=entity["entity_group"],
                    start_char=entity["start"],
                    end_char=entity["end"],
                    score=entity["score"],
                )
                result.add_entity(ent)

            # Extract relationships if requested
            if self._extract_relationships and self.rel_pipeline:
                await self._extract_relationships_impl(text, result)

            return result

        except Exception as e:
            raise PepperpyError(f"Error processing text: {e}")

    async def extract_entities(self, text: str, **kwargs: Any) -> list[Entity]:
        """Extract entities from text.

        Args:
            text: Text to process
            **kwargs: Additional processor-specific parameters

        Returns:
            list of extracted entities
        """
        result = await self.process_text(text, **kwargs)
        return result.entities

    async def extract_relationships(
        self, text: str, **kwargs: Any
    ) -> list[Relationship]:
        """Extract relationships from text.

        Args:
            text: Text to process
            **kwargs: Additional processor-specific parameters

        Returns:
            list of extracted relationships
        """
        if not self._extract_relationships:
            logger.warning(
                "Relationship extraction was not enabled during initialization"
            )
            self._extract_relationships = True
            await self.initialize()  # Reinitialize with relationships enabled

        result = await self.process_text(text, **kwargs)
        return result.relationships

    async def _process_text_in_chunks(
        self, text: str, **kwargs: Any
    ) -> SemanticExtractionResult:
        """Process large text in chunks.

        Args:
            text: Text to process
            **kwargs: Additional processor-specific parameters

        Returns:
            Combined semantic extraction result
        """
        # Split text into chunks at sentence boundaries when possible
        chunks = []
        current_chunk = ""

        # Simple sentence splitting (not perfect but works for most cases)
        sentences = re.split(r"(?<=[.!?])\s+", text)

        for sentence in sentences:
            if len(current_chunk) + len(sentence) < self.chunk_size:
                current_chunk += sentence + " "
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + " "

        # Add the last chunk if it's not empty
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # Process each chunk
        combined_result = SemanticExtractionResult(text=text)

        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk {i + 1}/{len(chunks)} ({len(chunk)} chars)")

            # Add chunk offset for correct character positions
            offset = text.find(chunk)

            # Process the chunk
            result = await self.process_text(chunk, **kwargs)

            # Adjust entity positions
            for entity in result.entities:
                entity.start_char += offset
                entity.end_char += offset

            # Merge results
            combined_result.entities.extend(result.entities)
            combined_result.relationships.extend(result.relationships)

        return combined_result

    async def _extract_relationships_impl(
        self, text: str, result: SemanticExtractionResult
    ) -> None:
        """Extract relationships between entities.

        Args:
            text: Input text
            result: Result to update with relationships
        """
        if not self.rel_pipeline:
            return

        # Get all pairs of entities
        entities = result.entities
        for i, source in enumerate(entities):
            for target in entities[i + 1 :]:
                # Get the text between entities
                start = min(source.end_char, target.end_char)
                end = max(source.start_char, target.start_char)
                between_text = text[start:end]

                # Classify the relationship
                rel_result = self.rel_pipeline(between_text)
                if rel_result:
                    rel = rel_result[0]  # Get the most likely relationship
                    relationship = Relationship(
                        source=source,
                        target=target,
                        relation_type=rel["label"],
                        score=rel["score"],
                    )
                    result.add_relationship(relationship)
