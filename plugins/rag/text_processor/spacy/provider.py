"""SpaCy text processor implementation."""

import logging
from typing import Any

import spacy
from spacy.language import Language

from pepperpy.plugin.provider import BasePluginProvider
from pepperpy.rag.processor import (
    ProcessedText,
    ProcessingOptions,
    TextProcessingError,
    TextProcessor,
)

logger = logging.getLogger(__name__)


class SpacyProcessor(TextProcessor, BasePluginProvider):
    """Text processor using SpaCy."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        model_name: str = "en_core_web_sm",
        disable: list[str] | None = None,
    ) -> None:
        """Initialize the SpaCy processor.

        Args:
            config: Configuration dictionary
            model_name: Name of the SpaCy model to use
            disable: Pipeline components to disable
        """
        super().__init__()
        config = config or {}
        self._model_name = config.get("model_name", model_name)
        self._disable = config.get("disable", disable) or []
        self._nlp: Language | None = None
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize SpaCy resources."""
        if self.initialized:
            return

        try:
            logger.info(f"Loading SpaCy model: {self._model_name}")
            self._nlp = spacy.load(self._model_name, disable=self._disable)
            self.initialized = True
        except Exception as e:
            raise TextProcessingError(f"Failed to load SpaCy model: {e}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        # No explicit cleanup needed for SpaCy
        self._nlp = None
        self.initialized = False

    async def process(
        self, text: str, options: ProcessingOptions | None = None
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
            await self.initialize()
            if not self._nlp:
                raise TextProcessingError("SpaCy model not initialized")

        try:
            # Process the text with SpaCy
            doc = self._nlp(text)

            # Extract tokens
            tokens = [token.text for token in doc]

            # Extract entities
            entities = [
                {
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                }
                for ent in doc.ents
            ]

            # Build metadata
            metadata = {
                "lemmas": [token.lemma_ for token in doc],
                "pos_tags": [token.pos_ for token in doc],
                "dependencies": [token.dep_ for token in doc],
                "sentences": [sent.text for sent in doc.sents],
            }

            return ProcessedText(
                text=text,
                tokens=tokens,
                entities=entities,
                metadata=metadata,
            )
        except Exception as e:
            raise TextProcessingError(f"SpaCy processing failed: {e}")

    async def process_batch(
        self, texts: list[str], options: ProcessingOptions | None = None
    ) -> list[ProcessedText]:
        """Process multiple texts using SpaCy.

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
            raise TextProcessingError(f"SpaCy batch processing failed: {e}")

    @property
    def name(self) -> str:
        """Get the processor name."""
        return "spacy"

    @property
    def capabilities(self) -> dict[str, Any]:
        """Get the processor capabilities."""
        return {
            "tokenization": True,
            "sentence_tokenization": True,
            "lemmatization": True,
            "pos_tagging": True,
            "dependency_parsing": True,
            "entity_recognition": True,
            "batch_processing": True,
            "languages": ["en"],  # Depends on the model loaded
            "model": self._model_name,
        }

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a task based on input data.

        Args:
            input_data: Input data containing task and parameters

        Returns:
            Task execution result
        """
        task_type = input_data.get("task")

        if not task_type:
            return {"status": "error", "error": "No task specified"}

        try:
            if not self.initialized:
                await self.initialize()

            if task_type == "process":
                text = input_data.get("text")
                if not text:
                    return {"status": "error", "error": "No text provided"}

                options_dict = input_data.get("options", {})
                options = ProcessingOptions(
                    model=options_dict.get("model", "default"),
                    disable=options_dict.get("disable", []),
                    additional_options=options_dict.get("additional_options", {}),
                )

                result = await self.process(text, options)

                return {
                    "status": "success",
                    "text": result.text,
                    "tokens": result.tokens,
                    "entities": result.entities,
                    "metadata": result.metadata,
                }

            elif task_type == "process_batch":
                texts = input_data.get("texts", [])
                if not texts:
                    return {"status": "error", "error": "No texts provided"}

                options_dict = input_data.get("options", {})
                options = ProcessingOptions(
                    model=options_dict.get("model", "default"),
                    disable=options_dict.get("disable", []),
                    additional_options=options_dict.get("additional_options", {}),
                )

                results = await self.process_batch(texts, options)

                return {
                    "status": "success",
                    "results": [
                        {
                            "text": r.text,
                            "tokens": r.tokens,
                            "entities": r.entities,
                            "metadata": r.metadata,
                        }
                        for r in results
                    ],
                }

            else:
                return {"status": "error", "error": f"Unknown task type: {task_type}"}

        except Exception as e:
            logger.error(f"Error executing task '{task_type}': {e}")
            return {"status": "error", "error": str(e)}
