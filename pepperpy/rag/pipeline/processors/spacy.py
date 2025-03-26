"""SpaCy text processor implementation."""

import logging
from typing import Any, Dict, List, Optional

import spacy
from spacy.language import Language

from pepperpy.rag.pipeline.processors.base import (
    ProcessedText,
    ProcessingOptions,
    TextProcessingError,
    TextProcessor,
)

logger = logging.getLogger(__name__)


class SpacyProcessor(TextProcessor):
    """Text processor using SpaCy."""

    def __init__(
        self,
        model: str = "en_core_web_sm",
        batch_size: int = 1000,
        disable: Optional[List[str]] = None,
    ) -> None:
        """Initialize the SpaCy processor.

        Args:
            model: SpaCy model to use
            batch_size: Batch size for processing
            disable: Pipeline components to disable
        """
        self._model_name = model
        self._batch_size = batch_size
        self._disable = disable or []
        self._nlp: Optional[Language] = None

    async def initialize(self) -> None:
        """Initialize the SpaCy model."""
        try:
            logger.info(f"Loading SpaCy model: {self._model_name}")
            self._nlp = spacy.load(self._model_name, disable=self._disable)
        except Exception as e:
            raise TextProcessingError(f"Failed to load SpaCy model: {e}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._nlp = None

    async def process(
        self, text: str, options: Optional[ProcessingOptions] = None
    ) -> ProcessedText:
        """Process text using SpaCy.

        Args:
            text: Text to process
            options: Processing options

        Returns:
            Processed text result

        Raises:
            TextProcessingError: If processing fails
        """
        if not self._nlp:
            raise TextProcessingError("SpaCy model not initialized")

        try:
            doc = self._nlp(text)

            return ProcessedText(
                text=text,
                tokens=[token.text for token in doc],
                entities=[
                    {
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char,
                    }
                    for ent in doc.ents
                ],
                metadata={
                    "lemmas": [token.lemma_ for token in doc],
                    "pos_tags": [token.pos_ for token in doc],
                    "dep_tags": [token.dep_ for token in doc],
                },
            )
        except Exception as e:
            raise TextProcessingError(f"SpaCy processing failed: {e}")

    async def process_batch(
        self, texts: List[str], options: Optional[ProcessingOptions] = None
    ) -> List[ProcessedText]:
        """Process multiple texts using SpaCy.

        Args:
            texts: Texts to process
            options: Processing options

        Returns:
            List of processed text results

        Raises:
            TextProcessingError: If processing fails
        """
        if not self._nlp:
            raise TextProcessingError("SpaCy model not initialized")

        try:
            results = []
            for doc in self._nlp.pipe(texts, batch_size=self._batch_size):
                results.append(
                    ProcessedText(
                        text=doc.text,
                        tokens=[token.text for token in doc],
                        entities=[
                            {
                                "text": ent.text,
                                "label": ent.label_,
                                "start": ent.start_char,
                                "end": ent.end_char,
                            }
                            for ent in doc.ents
                        ],
                        metadata={
                            "lemmas": [token.lemma_ for token in doc],
                            "pos_tags": [token.pos_ for token in doc],
                            "dep_tags": [token.dep_ for token in doc],
                        },
                    )
                )
            return results
        except Exception as e:
            raise TextProcessingError(f"SpaCy batch processing failed: {e}")

    @property
    def name(self) -> str:
        """Get the processor name."""
        return "spacy"

    @property
    def capabilities(self) -> Dict[str, Any]:
        """Get the processor capabilities."""
        return {
            "tokenization": True,
            "lemmatization": True,
            "pos_tagging": True,
            "dependency_parsing": True,
            "entity_recognition": True,
            "batch_processing": True,
            "languages": ["en"],  # Depends on model
            "model": self._model_name,
        }
