"""Transformers text processor implementation."""

import logging
from typing import Any, Dict, List, Optional

from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizer,
    pipeline,
)

from pepperpy.rag.pipeline.processors.base import (
    ProcessedText,
    ProcessingOptions,
    TextProcessingError,
    TextProcessor,
)

logger = logging.getLogger(__name__)


class TransformersProcessor(TextProcessor):
    """Text processor using Hugging Face Transformers."""

    def __init__(
        self,
        model_name: str = "dbmdz/bert-large-cased-finetuned-conll03-english",
        tokenizer_name: Optional[str] = None,
        device: str = "cpu",
        batch_size: int = 32,
    ) -> None:
        """Initialize the Transformers processor.

        Args:
            model_name: Name of the pre-trained model to use
            tokenizer_name: Name of the tokenizer (defaults to model_name)
            device: Device to run the model on ("cpu" or "cuda")
            batch_size: Batch size for processing
        """
        self._model_name = model_name
        self._tokenizer_name = tokenizer_name or model_name
        self._device = device
        self._batch_size = batch_size

        self._tokenizer: Optional[PreTrainedTokenizer] = None
        self._model: Optional[PreTrainedModel] = None
        self._ner_pipeline: Optional[Any] = None

    async def initialize(self) -> None:
        """Initialize the model and tokenizer."""
        try:
            logger.info(f"Loading Transformers model: {self._model_name}")

            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(self._tokenizer_name)

            # Load model
            self._model = AutoModelForTokenClassification.from_pretrained(
                self._model_name
            )

            # Move model to device
            self._model.to(self._device)

            # Create NER pipeline
            self._ner_pipeline = pipeline(
                "ner",
                model=self._model,
                tokenizer=self._tokenizer,
                device=-1 if self._device == "cpu" else 0,
                batch_size=self._batch_size,
                aggregation_strategy="simple",
            )

        except Exception as e:
            raise TextProcessingError(f"Failed to load Transformers model: {e}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._model = None
        self._tokenizer = None
        self._ner_pipeline = None

    def _process_entities(
        self, ner_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process NER results into standard format.

        Args:
            ner_results: Raw NER results from the pipeline

        Returns:
            Processed entity list
        """
        return [
            {
                "text": result["word"],
                "label": result["entity_group"],
                "start": result["start"],
                "end": result["end"],
                "score": result["score"],
            }
            for result in ner_results
        ]

    async def process(
        self, text: str, options: Optional[ProcessingOptions] = None
    ) -> ProcessedText:
        """Process text using Transformers.

        Args:
            text: Text to process
            options: Processing options

        Returns:
            Processed text result

        Raises:
            TextProcessingError: If processing fails
        """
        if not self._tokenizer or not self._ner_pipeline:
            raise TextProcessingError("Transformers model not initialized")

        try:
            # Tokenization
            tokens = self._tokenizer.tokenize(text)

            # Named Entity Recognition
            ner_results = self._ner_pipeline(text)
            entities = self._process_entities(ner_results)

            # Get token IDs and attention mask
            encoding = self._tokenizer(
                text, return_tensors="pt", padding=True, truncation=True
            )

            return ProcessedText(
                text=text,
                tokens=tokens,
                entities=entities,
                metadata={
                    "input_ids": encoding["input_ids"].tolist(),
                    "attention_mask": encoding["attention_mask"].tolist(),
                    "model_name": self._model_name,
                },
            )
        except Exception as e:
            raise TextProcessingError(f"Transformers processing failed: {e}")

    async def process_batch(
        self, texts: List[str], options: Optional[ProcessingOptions] = None
    ) -> List[ProcessedText]:
        """Process multiple texts using Transformers.

        Args:
            texts: Texts to process
            options: Processing options

        Returns:
            List of processed text results

        Raises:
            TextProcessingError: If processing fails
        """
        if not self._tokenizer or not self._ner_pipeline:
            raise TextProcessingError("Transformers model not initialized")

        try:
            results = []

            # Process in batches
            for i in range(0, len(texts), self._batch_size):
                batch = texts[i : i + self._batch_size]

                # Tokenization
                batch_tokens = [self._tokenizer.tokenize(text) for text in batch]

                # Named Entity Recognition
                batch_ner = self._ner_pipeline(batch)

                # Get token IDs and attention masks
                batch_encoding = self._tokenizer(
                    batch, return_tensors="pt", padding=True, truncation=True
                )

                # Create ProcessedText objects
                for text, tokens, ner_results, input_ids, attention_mask in zip(
                    batch,
                    batch_tokens,
                    batch_ner,
                    batch_encoding["input_ids"].tolist(),
                    batch_encoding["attention_mask"].tolist(),
                ):
                    results.append(
                        ProcessedText(
                            text=text,
                            tokens=tokens,
                            entities=self._process_entities(ner_results),
                            metadata={
                                "input_ids": input_ids,
                                "attention_mask": attention_mask,
                                "model_name": self._model_name,
                            },
                        )
                    )

            return results
        except Exception as e:
            raise TextProcessingError(f"Transformers batch processing failed: {e}")

    @property
    def name(self) -> str:
        """Get the processor name."""
        return "transformers"

    @property
    def capabilities(self) -> Dict[str, Any]:
        """Get the processor capabilities."""
        return {
            "tokenization": True,
            "entity_recognition": True,
            "batch_processing": True,
            "gpu_support": True,
            "model_name": self._model_name,
            "device": self._device,
            "batch_size": self._batch_size,
        }
