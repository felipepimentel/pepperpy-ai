"""Semantic extraction for document processing.

This module provides functionality for extracting semantic entities,
relationships, and concepts from document text.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from pepperpy.core.base import PepperpyError

logger = logging.getLogger(__name__)

# Try to import NLP libraries
try:
    import spacy
    from spacy.language import Language
    from spacy.tokens import Doc, Span

    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

    # Define classe de substituição para anotação de tipo
    class Doc:
        """Placeholder for spaCy Doc class when not available."""

        pass

    class Span:
        """Placeholder for spaCy Span class when not available."""

        pass


try:
    from transformers import pipeline

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class SemanticExtractionError(PepperpyError):
    """Error raised during semantic extraction operations."""

    pass


class Entity:
    """Representation of an extracted entity."""

    def __init__(
        self,
        text: str,
        label: str,
        start_char: int,
        end_char: int,
        score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize entity.

        Args:
            text: Text of the entity
            label: Entity type/label
            start_char: Start character position in the source text
            end_char: End character position in the source text
            score: Confidence score (0-1)
            metadata: Additional entity information
        """
        self.text = text
        self.label = label
        self.start_char = start_char
        self.end_char = end_char
        self.score = score
        self.metadata = metadata or {}

    def __str__(self) -> str:
        """String representation of the entity."""
        if self.score is not None:
            return f"{self.text} ({self.label}, {self.score:.2f})"
        return f"{self.text} ({self.label})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        result = {
            "text": self.text,
            "label": self.label,
            "start": self.start_char,
            "end": self.end_char,
        }
        if self.score is not None:
            result["score"] = self.score
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class Relationship:
    """Representation of a relationship between entities."""

    def __init__(
        self,
        source: Entity,
        target: Entity,
        relation_type: str,
        score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize relationship.

        Args:
            source: Source entity
            target: Target entity
            relation_type: Type of relationship
            score: Confidence score (0-1)
            metadata: Additional relationship information
        """
        self.source = source
        self.target = target
        self.relation_type = relation_type
        self.score = score
        self.metadata = metadata or {}

    def __str__(self) -> str:
        """String representation of the relationship."""
        if self.score is not None:
            return f"{self.source.text} --{self.relation_type}--> {self.target.text} ({self.score:.2f})"
        return f"{self.source.text} --{self.relation_type}--> {self.target.text}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to dictionary."""
        result = {
            "source": self.source.to_dict(),
            "target": self.target.to_dict(),
            "relation": self.relation_type,
        }
        if self.score is not None:
            result["score"] = self.score
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class SemanticExtractionResult:
    """Result of semantic extraction."""

    def __init__(
        self,
        text: str,
        entities: Optional[List[Entity]] = None,
        relationships: Optional[List[Relationship]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize extraction result.

        Args:
            text: Source text
            entities: Extracted entities
            relationships: Extracted relationships
            metadata: Additional metadata
        """
        self.text = text
        self.entities = entities or []
        self.relationships = relationships or []
        self.metadata = metadata or {}

    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the result."""
        self.entities.append(entity)

    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship to the result."""
        self.relationships.append(relationship)

    def get_entities_by_label(self, label: str) -> List[Entity]:
        """Get entities by label.

        Args:
            label: Entity label to filter by

        Returns:
            List of entities with matching label
        """
        return [e for e in self.entities if e.label == label]

    def get_relationships_by_type(self, relation_type: str) -> List[Relationship]:
        """Get relationships by type.

        Args:
            relation_type: Relationship type to filter by

        Returns:
            List of relationships with matching type
        """
        return [r for r in self.relationships if r.relation_type == relation_type]

    def merge(self, other: "SemanticExtractionResult") -> None:
        """Merge another extraction result into this one.

        Args:
            other: Another extraction result
        """
        self.entities.extend(other.entities)
        self.relationships.extend(other.relationships)

        # Update metadata by merging dictionaries
        for key, value in other.metadata.items():
            if (
                key in self.metadata
                and isinstance(self.metadata[key], dict)
                and isinstance(value, dict)
            ):
                self.metadata[key].update(value)
            else:
                self.metadata[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert extraction result to dictionary."""
        return {
            "entities": [e.to_dict() for e in self.entities],
            "relationships": [r.to_dict() for r in self.relationships],
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        """String representation of the extraction result."""
        parts = [
            f"Entities: {len(self.entities)}",
            f"Relationships: {len(self.relationships)}",
        ]
        if self.entities:
            parts.append("Entities:")
            for entity in self.entities[:10]:  # Limit to 10 entities for readability
                parts.append(f"  {entity}")
            if len(self.entities) > 10:
                parts.append(f"  ... and {len(self.entities) - 10} more")

        if self.relationships:
            parts.append("Relationships:")
            for rel in self.relationships[
                :10
            ]:  # Limit to 10 relationships for readability
                parts.append(f"  {rel}")
            if len(self.relationships) > 10:
                parts.append(f"  ... and {len(self.relationships) - 10} more")

        return "\n".join(parts)


class SemanticExtractor:
    """Extractor for semantic entities and relationships.

    This class provides functionality for extracting semantic information
    from document text using various NLP backends.
    """

    # Supported extraction backends
    SUPPORTED_BACKENDS = {
        "spacy": SPACY_AVAILABLE,
        "transformers": TRANSFORMERS_AVAILABLE,
    }

    # Default entity types to extract (for backends that need this info)
    DEFAULT_ENTITY_TYPES = {
        "PERSON",
        "ORG",
        "GPE",
        "LOC",
        "DATE",
        "TIME",
        "MONEY",
        "PERCENT",
        "FACILITY",
        "PRODUCT",
        "EVENT",
        "LAW",
        "WORK_OF_ART",
        "LANGUAGE",
    }

    def __init__(
        self,
        backend: str = "spacy",
        model_name: Optional[str] = None,
        entity_types: Optional[Set[str]] = None,
        extract_relationships: bool = False,
        chunk_size: int = 100000,  # 100K characters
        **kwargs: Any,
    ) -> None:
        """Initialize semantic extractor.

        Args:
            backend: NLP backend to use ('spacy' or 'transformers')
            model_name: Model name/path
            entity_types: Set of entity types to extract
            extract_relationships: Whether to extract relationships
            chunk_size: Maximum chunk size for processing
            **kwargs: Additional backend-specific parameters
        """
        # Check if backend is supported
        if backend not in self.SUPPORTED_BACKENDS:
            raise SemanticExtractionError(f"Unsupported extraction backend: {backend}")

        if not self.SUPPORTED_BACKENDS[backend]:
            raise SemanticExtractionError(
                f"Extraction backend {backend} is not available"
            )

        self.backend = backend
        self.model_name = model_name
        self.entity_types = entity_types or self.DEFAULT_ENTITY_TYPES
        self.extract_relationships = extract_relationships
        self.chunk_size = chunk_size
        self.config = kwargs

        # Initialize backend
        self._initialize_backend()

    def _initialize_backend(self) -> None:
        """Initialize NLP backend."""
        if self.backend == "spacy":
            self._initialize_spacy()
        elif self.backend == "transformers":
            self._initialize_transformers()

    def _initialize_spacy(self) -> None:
        """Initialize spaCy backend."""
        if not SPACY_AVAILABLE:
            raise SemanticExtractionError("spaCy is not available")

        # Set default model if not provided
        if not self.model_name:
            self.model_name = "en_core_web_sm"

        try:
            # Load spaCy model
            self.nlp = spacy.load(self.model_name)

            # Configure pipeline components
            if "neuralcoref" in self.config and self.config["neuralcoref"]:
                # Add neural coreference resolution if available
                try:
                    import neuralcoref

                    neuralcoref.add_to_pipe(self.nlp)
                    logger.debug("Added neuralcoref to spaCy pipeline")
                except ImportError:
                    logger.warning("neuralcoref requested but not available. Skipping.")

            # Add custom components if needed
            if self.extract_relationships and not self.nlp.has_pipe(
                "merge_noun_chunks"
            ):
                # Add noun chunks merging for better relationship extraction
                self.nlp.add_pipe("merge_noun_chunks")

            # Set processing options
            self.nlp.max_length = self.config.get("max_length", 1000000)
        except OSError as e:
            raise SemanticExtractionError(f"Error loading spaCy model: {e}")

    def _initialize_transformers(self) -> None:
        """Initialize Transformers backend."""
        if not TRANSFORMERS_AVAILABLE:
            raise SemanticExtractionError("Transformers is not available")

        # Set default model if not provided
        if not self.model_name:
            self.model_name = "dslim/bert-base-NER"

        try:
            # Initialize NER pipeline
            self.ner_pipeline = pipeline(
                "ner",
                model=self.model_name,
                aggregation_strategy=self.config.get("aggregation_strategy", "simple"),
            )

            # Initialize relationship extraction pipeline if requested
            if self.extract_relationships:
                self.rel_model_name = self.config.get(
                    "rel_model_name", "Jean-Baptiste/roberta-large-ner-english"
                )
                self.rel_pipeline = pipeline(
                    "text-classification",
                    model=self.rel_model_name,
                )
        except Exception as e:
            raise SemanticExtractionError(
                f"Error initializing transformers pipeline: {e}"
            )

    def process_text(self, text: str, **kwargs: Any) -> SemanticExtractionResult:
        """Process text to extract semantic information.

        Args:
            text: Text to process
            **kwargs: Additional backend-specific parameters

        Returns:
            Semantic extraction result

        Raises:
            SemanticExtractionError: If extraction fails
        """
        if not text:
            return SemanticExtractionResult(text="")

        try:
            # Process in smaller chunks if text is very large
            if len(text) > self.chunk_size:
                return self._process_text_in_chunks(text, **kwargs)

            # Use appropriate backend for processing
            if self.backend == "spacy":
                return self._process_with_spacy(text, **kwargs)
            elif self.backend == "transformers":
                return self._process_with_transformers(text, **kwargs)
            else:
                raise SemanticExtractionError(f"Unsupported backend: {self.backend}")
        except Exception as e:
            raise SemanticExtractionError(f"Error processing text: {e}")

    def _process_text_in_chunks(
        self, text: str, **kwargs: Any
    ) -> SemanticExtractionResult:
        """Process large text in chunks.

        Args:
            text: Text to process
            **kwargs: Additional backend-specific parameters

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
            if self.backend == "spacy":
                result = self._process_with_spacy(chunk, char_offset=offset, **kwargs)
            elif self.backend == "transformers":
                result = self._process_with_transformers(
                    chunk, char_offset=offset, **kwargs
                )
            else:
                raise SemanticExtractionError(f"Unsupported backend: {self.backend}")

            # Merge results
            combined_result.merge(result)

        return combined_result

    def _process_with_spacy(
        self, text: str, char_offset: int = 0, **kwargs: Any
    ) -> SemanticExtractionResult:
        """Process text using spaCy.

        Args:
            text: Text to process
            char_offset: Character offset for entity positions
            **kwargs: Additional spaCy-specific parameters

        Returns:
            Semantic extraction result
        """
        # Process text with spaCy
        doc = self.nlp(text)

        # Initialize result
        result = SemanticExtractionResult(text=text)

        # Extract entities
        for ent in doc.ents:
            # Check if entity type is in requested types
            if not self.entity_types or ent.label_ in self.entity_types:
                # Create entity with correct character positions
                entity = Entity(
                    text=ent.text,
                    label=ent.label_,
                    start_char=ent.start_char + char_offset,
                    end_char=ent.end_char + char_offset,
                )

                # Add entity metadata from spaCy
                entity.metadata["spacy_pos"] = ent.root.pos_
                entity.metadata["spacy_dep"] = ent.root.dep_

                result.add_entity(entity)

        # Extract relationships if requested
        if self.extract_relationships:
            self._extract_relationships_spacy(doc, result, char_offset)

        return result

    def _extract_relationships_spacy(
        self, doc: Doc, result: SemanticExtractionResult, char_offset: int = 0
    ) -> None:
        """Extract relationships using spaCy dependency parsing.

        Args:
            doc: spaCy Doc object
            result: Semantic extraction result to update
            char_offset: Character offset for entity positions
        """
        # Entity lookup by position
        entity_by_span: Dict[Tuple[int, int], Entity] = {
            (e.start_char - char_offset, e.end_char - char_offset): e
            for e in result.entities
        }

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

    def _process_with_transformers(
        self, text: str, char_offset: int = 0, **kwargs: Any
    ) -> SemanticExtractionResult:
        """Process text using transformers.

        Args:
            text: Text to process
            char_offset: Character offset for entity positions
            **kwargs: Additional transformers-specific parameters

        Returns:
            Semantic extraction result
        """
        # Initialize result
        result = SemanticExtractionResult(text=text)

        # Extract entities
        entities = self.ner_pipeline(text)

        for entity in entities:
            # Create Entity object
            ent = Entity(
                text=entity["word"],
                label=entity["entity_group"],
                start_char=entity["start"] + char_offset,
                end_char=entity["end"] + char_offset,
                score=entity["score"],
            )
            result.add_entity(ent)

        # Extract relationships (not yet implemented for transformers backend)
        # Would require a specific relationship extraction model

        return result

    def extract_entities(self, text: str, **kwargs: Any) -> List[Entity]:
        """Extract entities from text.

        Args:
            text: Text to process
            **kwargs: Additional backend-specific parameters

        Returns:
            List of extracted entities

        Raises:
            SemanticExtractionError: If extraction fails
        """
        result = self.process_text(text, **kwargs)
        return result.entities

    def extract_relationships(self, text: str, **kwargs: Any) -> List[Relationship]:
        """Extract relationships from text.

        Args:
            text: Text to process
            **kwargs: Additional backend-specific parameters

        Returns:
            List of extracted relationships

        Raises:
            SemanticExtractionError: If extraction fails
        """
        if not self.extract_relationships:
            logger.warning(
                "Relationship extraction was not enabled during initialization"
            )
            self.extract_relationships = True

        result = self.process_text(text, **kwargs)
        return result.relationships


# Global semantic extractor instance
_semantic_extractor: Optional[SemanticExtractor] = None


def get_semantic_extractor(
    backend: str = "spacy",
    model_name: Optional[str] = None,
    entity_types: Optional[Set[str]] = None,
    extract_relationships: bool = False,
    **kwargs: Any,
) -> SemanticExtractor:
    """Get semantic extractor instance.

    Args:
        backend: NLP backend to use ('spacy' or 'transformers')
        model_name: Model name/path
        entity_types: Set of entity types to extract
        extract_relationships: Whether to extract relationships
        **kwargs: Additional backend-specific parameters

    Returns:
        Semantic extractor instance
    """
    global _semantic_extractor

    # Create new instance if one doesn't exist or if configuration changed
    if (
        _semantic_extractor is None
        or _semantic_extractor.backend != backend
        or _semantic_extractor.model_name != model_name
        or _semantic_extractor.extract_relationships != extract_relationships
    ):
        _semantic_extractor = SemanticExtractor(
            backend=backend,
            model_name=model_name,
            entity_types=entity_types,
            extract_relationships=extract_relationships,
            **kwargs,
        )

    return _semantic_extractor
