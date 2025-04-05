"""NLTK text processor implementation."""

import logging
from typing import Any

import nltk
from nltk.chunk import ne_chunk
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag
from nltk.tokenize import sent_tokenize, word_tokenize

from plugins.rag.base import (
    ProcessedText,
    ProcessingOptions,
    TextProcessingError,
    TextProcessor,
)

logger = logging.getLogger(__name__)


class NLTKProcessor(TextProcessor):
    """Text processor using NLTK."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        download_resources: bool = True,
        resources: list[str] | None = None,
    ) -> None:
        """Initialize the NLTK processor.

        Args:
            config: Configuration dictionary
            download_resources: Whether to download required NLTK resources
            resources: List of specific resources to download
        """
        config = config or {}
        self._download_resources = config.get("download_resources", download_resources)
        self._resources = config.get("resources", resources) or [
            "punkt",
            "averaged_perceptron_tagger",
            "maxent_ne_chunker",
            "words",
            "wordnet",
        ]
        self._lemmatizer = WordNetLemmatizer()

    async def initialize(self) -> None:
        """Initialize NLTK resources."""
        if self._download_resources:
            try:
                logger.info("Downloading NLTK resources")
                for resource in self._resources:
                    nltk.download(resource, quiet=True)
            except Exception as e:
                raise TextProcessingError(f"Failed to download NLTK resources: {e}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass  # No cleanup needed for NLTK

    def _extract_entities(self, text: str) -> list[dict[str, Any]]:
        """Extract named entities from text.

        Args:
            text: Input text

        Returns:
            List of named entities with their types
        """
        tokens = word_tokenize(text)
        pos_tags = pos_tag(tokens)
        tree = ne_chunk(pos_tags)

        entities = []
        for subtree in tree:
            if hasattr(subtree, "label"):
                entity_text = " ".join([token for token, pos in subtree.leaves()])
                start = text.find(entity_text)
                if start >= 0:
                    entities.append({
                        "text": entity_text,
                        "label": subtree.label(),
                        "start": start,
                        "end": start + len(entity_text),
                    })

        return entities

    async def process(
        self, text: str, options: ProcessingOptions | None = None
    ) -> ProcessedText:
        """Process text using NLTK.

        Args:
            text: Text to process
            options: Processing options

        Returns:
            Processed text result

        Raises:
            TextProcessingError: If processing fails
        """
        try:
            # Tokenization
            tokens = word_tokenize(text)

            # POS tagging
            pos_tags = pos_tag(tokens)

            # Lemmatization
            lemmas = [self._lemmatizer.lemmatize(token) for token in tokens]

            # Named Entity Recognition
            entities = self._extract_entities(text)

            # Sentence tokenization
            sentences = sent_tokenize(text)

            return ProcessedText(
                text=text,
                tokens=tokens,
                entities=entities,
                metadata={
                    "lemmas": lemmas,
                    "pos_tags": [tag for _, tag in pos_tags],
                    "sentences": sentences,
                },
            )
        except Exception as e:
            raise TextProcessingError(f"NLTK processing failed: {e}")

    async def process_batch(
        self, texts: list[str], options: ProcessingOptions | None = None
    ) -> list[ProcessedText]:
        """Process multiple texts using NLTK.

        Args:
            texts: Texts to process
            options: Processing options

        Returns:
            List of processed text results

        Raises:
            TextProcessingError: If processing fails
        """
        try:
            return [await self.process(text, options) for text in texts]
        except Exception as e:
            raise TextProcessingError(f"NLTK batch processing failed: {e}")

    @property
    def name(self) -> str:
        """Get the processor name."""
        return "nltk"

    @property
    def capabilities(self) -> dict[str, Any]:
        """Get the processor capabilities."""
        return {
            "tokenization": True,
            "sentence_tokenization": True,
            "lemmatization": True,
            "pos_tagging": True,
            "entity_recognition": True,
            "batch_processing": True,
            "languages": ["en"],
            "resources": self._resources,
        }
