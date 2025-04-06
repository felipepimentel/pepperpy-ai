"""spaCy-based semantic processor implementation."""

import logging
from typing import Any, cast

import spacy
from spacy.language import Language
from spacy.tokens import Doc

from pepperpy.content.base import (
    Entity,
    Relationship,
    SemanticExtractionResult,
    SemanticProcessorProvider,
)
from pepperpy.core.base import PepperpyError
from pepperpy.plugin import ProviderPlugin

logger = logging.getLogger(__name__)


class SpacySemanticProcessor(SemanticProcessorProvider, ProviderPlugin):
    """Semantic processor using spaCy."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize processor.

        Args:
            **kwargs: Configuration options
        """
        super().__init__(**kwargs)
        self.model_name: str = kwargs.get("model_name", "en_core_web_sm")
        self._extract_relationships: bool = kwargs.get("extract_relationships", False)
        self.chunk_size: int = kwargs.get("chunk_size", 100000)
        self.neuralcoref: bool = kwargs.get("neuralcoref", False)
        self.nlp: Language | None = None
        self.initialized: bool = False

    async def initialize(self) -> None:
        """Initialize the processor."""
        if self.initialized:
            return

        try:
            # Load spaCy model
            self.nlp = spacy.load(self.model_name)
            nlp = cast(Language, self.nlp)  # Help type checker

            # Configure pipeline components
            if self.neuralcoref:
                # Add neural coreference resolution if available
                try:
                    import neuralcoref

                    neuralcoref.add_to_pipe(nlp)
                    logger.debug("Added neuralcoref to spaCy pipeline")
                except ImportError:
                    logger.warning("neuralcoref requested but not available. Skipping.")

            # Add custom components if needed
            if self._extract_relationships and not nlp.has_pipe("merge_noun_chunks"):
                # Add noun chunks merging for better relationship extraction
                nlp.add_pipe("merge_noun_chunks")

            # Set processing options
            nlp.max_length = self.chunk_size
            self.initialized = True
            logger.debug(f"Initialized spaCy processor with model {self.model_name}")

        except Exception as e:
            raise PepperpyError(f"Error initializing spaCy processor: {e}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.nlp = None
        self.initialized = False

    async def process_text(self, text: str, **kwargs: Any) -> SemanticExtractionResult:
        """Process text to extract semantic information.

        Args:
            text: Text to process
            **kwargs: Additional processor-specific parameters

        Returns:
            Semantic extraction result
        """
        if not self.initialized or not self.nlp:
            await self.initialize()

        if not self.nlp:  # Double check after initialization
            raise PepperpyError("Failed to initialize spaCy processor")

        try:
            # Process text with spaCy
            doc = self.nlp(text)

            # Initialize result
            result = SemanticExtractionResult(text=text)

            # Extract entities
            for ent in doc.ents:
                entity = Entity(
                    text=ent.text,
                    label=ent.label_,
                    start_char=ent.start_char,
                    end_char=ent.end_char,
                    metadata={"pos": ent.root.pos_, "dep": ent.root.dep_},
                )
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

    async def _extract_relationships_impl(
        self, doc: Doc, result: SemanticExtractionResult
    ) -> None:
        """Extract relationships from spaCy doc.

        Args:
            doc: spaCy Doc object
            result: Result to update with relationships
        """
        # Entity lookup by position
        entity_by_span = {(e.start_char, e.end_char): e for e in result.entities}

        # Extract subject-verb-object structures
        for token in doc:
            if token.dep_ == "ROOT" and token.pos_ == "VERB":
                # Found a verb
                subjects = [
                    child
                    for child in token.children
                    if child.dep_ in ("nsubj", "nsubjpass")
                ]
                objects = [
                    child
                    for child in token.children
                    if child.dep_ in ("dobj", "pobj", "attr")
                ]

                for subj in subjects:
                    # Find entity for subject
                    subj_entity = None
                    for span in doc.ents:
                        if subj in span or span.root == subj:
                            key = (span.start_char, span.end_char)
                            if key in entity_by_span:
                                subj_entity = entity_by_span[key]
                                break

                    if subj_entity is None:
                        continue

                    for obj in objects:
                        # Find entity for object
                        obj_entity = None
                        for span in doc.ents:
                            if obj in span or span.root == obj:
                                key = (span.start_char, span.end_char)
                                if key in entity_by_span:
                                    obj_entity = entity_by_span[key]
                                    break

                        if obj_entity is not None:
                            # Create relationship
                            rel = Relationship(
                                source=subj_entity,
                                target=obj_entity,
                                relation_type=token.lemma_,
                                metadata={"dep": token.dep_, "pos": token.pos_},
                            )
                            result.add_relationship(rel)
