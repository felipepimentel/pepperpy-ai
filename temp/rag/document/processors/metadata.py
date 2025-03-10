"""Metadata enrichment processor module.

This module provides functionality for enriching documents with additional metadata.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Pattern, Union

from transformers import pipeline

from pepperpy.errors import DocumentProcessError
from pepperpy.rag.document.processors.base import BaseDocumentProcessor
from pepperpy.rag.document.types import Document, DocumentChunk


class MetadataEnrichmentProcessor(BaseDocumentProcessor):
    """Metadata enrichment processor for adding metadata to documents.

    This processor can:
    - Extract entities (names, organizations, locations, etc.)
    - Extract dates and timestamps
    - Extract keywords and topics
    - Add custom metadata based on regex patterns
    - Compute text statistics (length, readability, etc.)
    """

    def __init__(
        self,
        extract_entities: bool = True,
        extract_dates: bool = True,
        extract_keywords: bool = True,
        custom_patterns: Optional[Dict[str, str]] = None,
        compute_stats: bool = True,
        ner_model: str = "dbmdz/bert-large-cased-finetuned-conll03-english",
        **kwargs: Any,
    ) -> None:
        """Initialize the metadata enrichment processor.

        Args:
            extract_entities: Whether to extract named entities.
            extract_dates: Whether to extract dates and timestamps.
            extract_keywords: Whether to extract keywords and topics.
            custom_patterns: Dict of {name: pattern} for custom regex extraction.
            compute_stats: Whether to compute text statistics.
            ner_model: HuggingFace model ID for named entity recognition.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.extract_entities = extract_entities
        self.extract_dates = extract_dates
        self.extract_keywords = extract_keywords
        self.compute_stats = compute_stats

        # Initialize NER pipeline if needed
        self.ner_pipeline = None
        if extract_entities:
            self.ner_pipeline = pipeline(
                "ner", model=ner_model, aggregation_strategy="simple"
            )

        # Compile custom regex patterns
        self.custom_patterns: Dict[str, Pattern] = {}
        if custom_patterns:
            for name, pattern in custom_patterns.items():
                self.custom_patterns[name] = re.compile(pattern)

        # Common date patterns
        self.date_patterns = [
            (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
            (r"\d{2}/\d{2}/\d{4}", "%m/%d/%Y"),
            (r"\d{2}-\d{2}-\d{4}", "%d-%m-%Y"),
            (r"\d{4}/\d{2}/\d{2}", "%Y/%m/%d"),
        ]

    def _extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract named entities from text using NER.

        Args:
            text: The text to extract entities from.

        Returns:
            A dictionary mapping entity types to lists of entities.
        """
        if not self.ner_pipeline:
            return {}

        try:
            # Run NER pipeline
            entities = self.ner_pipeline(text)

            # Group entities by type
            grouped = {}
            for entity in entities:
                entity_type = entity.pop("entity_group")
                if entity_type not in grouped:
                    grouped[entity_type] = []
                grouped[entity_type].append(entity)

            return grouped

        except Exception as e:
            raise DocumentProcessError(f"Entity extraction failed: {str(e)}") from e

    def _extract_dates(self, text: str) -> List[datetime]:
        """Extract dates from text using regex patterns.

        Args:
            text: The text to extract dates from.

        Returns:
            A list of datetime objects.
        """
        dates = []
        for pattern, format_str in self.date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    date = datetime.strptime(match.group(), format_str)
                    dates.append(date)
                except ValueError:
                    continue
        return dates

    def _extract_custom_patterns(self, text: str) -> Dict[str, List[str]]:
        """Extract text matching custom regex patterns.

        Args:
            text: The text to extract patterns from.

        Returns:
            A dictionary mapping pattern names to lists of matches.
        """
        matches = {}
        for name, pattern in self.custom_patterns.items():
            matches[name] = pattern.findall(text)
        return matches

    def _compute_text_stats(self, text: str) -> Dict[str, Any]:
        """Compute various text statistics.

        Args:
            text: The text to analyze.

        Returns:
            A dictionary of text statistics.
        """
        # Split into words and sentences
        words = text.split()
        sentences = re.split(r"[.!?]+", text)

        # Basic statistics
        stats = {
            "char_count": len(text),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0,
            "avg_sentence_length": len(words) / len(sentences) if sentences else 0,
        }

        return stats

    async def process(
        self,
        documents: Union[Document, List[Document]],
        **kwargs: Any,
    ) -> Union[Document, List[Document]]:
        """Process one or more documents to enrich their metadata.

        Args:
            documents: A single document or list of documents to process.
            **kwargs: Additional keyword arguments for processing.

        Returns:
            The processed document(s) with enriched metadata.

        Raises:
            DocumentProcessError: If processing fails.
        """
        try:
            if isinstance(documents, Document):
                documents = [documents]

            processed_docs = []
            for doc in documents:
                # Process each chunk
                processed_chunks = []
                for chunk in doc.chunks:
                    # Initialize chunk metadata
                    chunk_metadata = chunk.metadata or {}

                    # Extract entities
                    if self.extract_entities:
                        entities = self._extract_entities(chunk.content)
                        if entities:
                            chunk_metadata["entities"] = entities

                    # Extract dates
                    if self.extract_dates:
                        dates = self._extract_dates(chunk.content)
                        if dates:
                            chunk_metadata["dates"] = [d.isoformat() for d in dates]

                    # Extract custom patterns
                    if self.custom_patterns:
                        matches = self._extract_custom_patterns(chunk.content)
                        if matches:
                            chunk_metadata["custom_matches"] = matches

                    # Compute text statistics
                    if self.compute_stats:
                        stats = self._compute_text_stats(chunk.content)
                        chunk_metadata["text_stats"] = stats

                    # Create processed chunk
                    processed_chunk = DocumentChunk(
                        content=chunk.content, metadata=chunk_metadata
                    )
                    processed_chunks.append(processed_chunk)

                # Create processed document
                processed_doc = Document(
                    chunks=processed_chunks,
                    metadata={
                        **(doc.metadata or {}),
                        "metadata_enriched": True,
                        "enrichment_timestamp": datetime.utcnow().isoformat(),
                    },
                )
                processed_docs.append(processed_doc)

            return processed_docs[0] if len(processed_docs) == 1 else processed_docs

        except Exception as e:
            raise DocumentProcessError(f"Metadata enrichment failed: {str(e)}") from e
