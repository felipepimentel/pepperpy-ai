"""Stanza-based semantic processor implementation."""

import logging
import os
import re
from typing import Any

import stanza
from stanza.models.common.doc import Document
from stanza.pipeline.core import Pipeline

from pepperpy.content.base import (
    Entity,
    Relationship,
    SemanticExtractionResult,
    SemanticProcessorProvider,
)
from pepperpy.core.base import PepperpyError

logger = logging.getLogger(__name__)


class StanzaSemanticProcessor(SemanticProcessorProvider):
    """Semantic processor using Stanza."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize processor.

        Args:
            **kwargs: Configuration options
        """
        super().__init__()
        self.language: str = kwargs.get("language", "en")
        self.processors: list[str] = kwargs.get(
            "processors", ["tokenize", "pos", "lemma", "ner", "depparse"]
        )
        self.entity_types: set[str] = set(
            kwargs.get(
                "entity_types",
                [
                    "PERSON",
                    "ORG",
                    "LOC",
                    "GPE",
                    "DATE",
                    "TIME",
                    "MONEY",
                    "PERCENT",
                ],
            )
        )
        self._extract_relationships: bool = kwargs.get("extract_relationships", False)
        self.chunk_size: int = kwargs.get("chunk_size", 100000)
        self.download_dir: str = os.path.expanduser(
            kwargs.get("download_dir", "~/.stanza_resources")
        )
        self.pipeline: Pipeline | None = None
        self.initialized: bool = False

    async def initialize(self) -> None:
        """Initialize the processor."""
        if self.initialized:
            return

        try:
            # Download required models
            stanza.download(
                self.language,
                dir=self.download_dir,
                processors=self.processors,
                logging_level="ERROR",
            )

            # Initialize pipeline
            self.pipeline = stanza.Pipeline(
                lang=self.language,
                dir=self.download_dir,
                processors=self.processors,
                logging_level="ERROR",
            )

            self.initialized = True
            logger.debug(f"Initialized Stanza processor for language {self.language}")

        except Exception as e:
            raise PepperpyError(f"Error initializing Stanza processor: {e}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.pipeline = None
        self.initialized = False

    async def process_text(self, text: str, **kwargs: Any) -> SemanticExtractionResult:
        """Process text to extract semantic information.

        Args:
            text: Text to process
            **kwargs: Additional processor-specific parameters

        Returns:
            Semantic extraction result
        """
        if not self.initialized or not self.pipeline:
            await self.initialize()

        if not self.pipeline:  # Double check after initialization
            raise PepperpyError("Failed to initialize Stanza processor")

        try:
            # Process in chunks if text is very large
            if len(text) > self.chunk_size:
                return await self._process_text_in_chunks(text, **kwargs)

            # Initialize result
            result = SemanticExtractionResult(text=text)

            # Process text with Stanza
            doc = self.pipeline(text)

            # Extract entities
            entities = await self._extract_entities_impl(doc, text)
            for entity in entities:
                result.add_entity(entity)

            # Extract relationships if requested
            if self._extract_relationships:
                await self._extract_relationships_impl(doc, result)

            return result

        except Exception as e:
            raise PepperpyError(f"Error processing text: {e}")

    async def extract_entities(self, text: str, **kwargs: Any) -> list[Entity]:
        """Extract entities from text.

        Args:
            text: Text to process
            **kwargs: Additional processor-specific parameters

        Returns:
            List of extracted entities
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
            List of extracted relationships
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
        # Split text into sentences using Stanza's tokenizer
        if not self.pipeline:
            raise PepperpyError("Pipeline not initialized")

        # Use a simple sentence splitter for chunking
        sentences = re.split(r"(?<=[.!?])\s+", text)

        # Group sentences into chunks
        chunks = []
        current_chunk = ""

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

    async def _extract_entities_impl(self, doc: Document, text: str) -> list[Entity]:
        """Extract entities from Stanza document.

        Args:
            doc: Stanza document
            text: Original text

        Returns:
            List of extracted entities
        """
        entities: list[Entity] = []

        for sent in doc.sentences:
            for ent in sent.ents:
                # Skip if entity type not in configured types
                if ent.type not in self.entity_types:
                    continue

                # Get entity text and position
                start_char = text.find(ent.text)
                if start_char == -1:
                    continue  # Skip if can't find exact position

                end_char = start_char + len(ent.text)

                # Create entity
                entity = Entity(
                    text=ent.text,
                    label=ent.type,
                    start_char=start_char,
                    end_char=end_char,
                    score=1.0,  # Stanza doesn't provide confidence scores
                )
                entities.append(entity)

        return entities

    async def _extract_relationships_impl(
        self, doc: Document, result: SemanticExtractionResult
    ) -> None:
        """Extract relationships from Stanza document.

        Uses dependency parsing to identify relationships between entities.

        Args:
            doc: Stanza document
            result: Result to update with relationships
        """
        # Create a mapping of token spans to entities
        entity_spans: dict[str, Entity] = {}
        for entity in result.entities:
            entity_spans[entity.text] = entity

        # Process each sentence
        for sent in doc.sentences:
            # Get dependency tree
            deps = sent.dependencies

            # Look for relationships between entities
            for dep in deps:
                gov_text = dep[0].text
                dep_text = dep[2].text
                rel_type = dep[1]

                # Check if both tokens are part of entities
                gov_entity = None
                dep_entity = None

                # Find entities containing these tokens
                for span, entity in entity_spans.items():
                    if gov_text in span:
                        gov_entity = entity
                    if dep_text in span:
                        dep_entity = entity

                # Create relationship if both tokens are part of entities
                if (
                    gov_entity
                    and dep_entity
                    and gov_entity != dep_entity
                    and rel_type != "punct"
                ):
                    relationship = Relationship(
                        source=gov_entity,
                        target=dep_entity,
                        relation_type=rel_type,
                        score=1.0,  # Simple implementation always uses 1.0
                    )
                    result.add_relationship(relationship)
