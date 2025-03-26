"""Text processing workflow recipe."""

from typing import List, Optional, cast

from pepperpy.rag.pipeline.processors import (
    NLTKProcessor,
    ProcessedText,
    ProcessingOptions,
    SpacyProcessor,
    TextProcessor,
    TransformersProcessor,
)
from pepperpy.workflow.base import PipelineContext, PipelineStage


class TextProcessingStage(PipelineStage[str, ProcessedText]):
    """Pipeline stage for text processing."""

    def __init__(
        self,
        processor: str = "spacy",
        model: Optional[str] = None,
        device: str = "cpu",
        batch_size: int = 32,
    ) -> None:
        """Initialize the text processing stage.

        Args:
            processor: Processor to use ("spacy", "nltk", or "transformers")
            model: Model to use (processor-specific)
            device: Device to run on ("cpu" or "cuda")
            batch_size: Batch size for processing
        """
        super().__init__(
            name="text_processing", description="Process text using NLP tools"
        )
        self._processor_type = processor
        self._model = model
        self._device = device
        self._batch_size = batch_size
        self._processor: Optional[TextProcessor] = None

    async def initialize(self) -> None:
        """Initialize the processor."""
        if self._processor_type == "spacy":
            self._processor = SpacyProcessor(
                model=self._model if self._model is not None else "en_core_web_sm"
            )
        elif self._processor_type == "nltk":
            self._processor = NLTKProcessor()
        elif self._processor_type == "transformers":
            self._processor = TransformersProcessor(
                model_name=self._model
                if self._model is not None
                else "dbmdz/bert-large-cased-finetuned-conll03-english",
                device=self._device,
                batch_size=self._batch_size,
            )
        else:
            raise ValueError(f"Unknown processor type: {self._processor_type}")

        await self._processor.initialize()

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._processor:
            await self._processor.cleanup()

    async def process(self, text: str, context: PipelineContext) -> ProcessedText:
        """Process text using the selected processor.

        Args:
            text: Text to process
            context: Pipeline context

        Returns:
            Processed text result
        """
        if not self._processor:
            await self.initialize()

        # After initialize(), self._processor is guaranteed to be set
        processor = cast(TextProcessor, self._processor)

        options = ProcessingOptions(
            model=self._model if self._model is not None else "default",
            additional_options=context.get("processing_options", {}),
        )

        result = await processor.process(text, options)

        # Store processor info in context
        context.set_metadata("processor_type", self._processor_type)
        context.set_metadata("processor_model", self._model)

        return result


class BatchTextProcessingStage(PipelineStage[List[str], List[ProcessedText]]):
    """Pipeline stage for batch text processing."""

    def __init__(
        self,
        processor: str = "spacy",
        model: Optional[str] = None,
        device: str = "cpu",
        batch_size: int = 32,
    ) -> None:
        """Initialize the batch text processing stage.

        Args:
            processor: Processor to use ("spacy", "nltk", or "transformers")
            model: Model to use (processor-specific)
            device: Device to run on ("cpu" or "cuda")
            batch_size: Batch size for processing
        """
        super().__init__(
            name="batch_text_processing",
            description="Process multiple texts using NLP tools",
        )
        self._processor_type = processor
        self._model = model
        self._device = device
        self._batch_size = batch_size
        self._processor: Optional[TextProcessor] = None

    async def initialize(self) -> None:
        """Initialize the processor."""
        if self._processor_type == "spacy":
            self._processor = SpacyProcessor(
                model=self._model if self._model is not None else "en_core_web_sm",
                batch_size=self._batch_size,
            )
        elif self._processor_type == "nltk":
            self._processor = NLTKProcessor()
        elif self._processor_type == "transformers":
            self._processor = TransformersProcessor(
                model_name=self._model
                if self._model is not None
                else "dbmdz/bert-large-cased-finetuned-conll03-english",
                device=self._device,
                batch_size=self._batch_size,
            )
        else:
            raise ValueError(f"Unknown processor type: {self._processor_type}")

        await self._processor.initialize()

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._processor:
            await self._processor.cleanup()

    async def process(
        self, texts: List[str], context: PipelineContext
    ) -> List[ProcessedText]:
        """Process multiple texts using the selected processor.

        Args:
            texts: Texts to process
            context: Pipeline context

        Returns:
            List of processed text results
        """
        if not self._processor:
            await self.initialize()

        # After initialize(), self._processor is guaranteed to be set
        processor = cast(TextProcessor, self._processor)

        options = ProcessingOptions(
            model=self._model if self._model is not None else "default",
            additional_options=context.get("processing_options", {}),
        )

        results = await processor.process_batch(texts, options)

        # Store processor info and stats in context
        context.set_metadata("processor_type", self._processor_type)
        context.set_metadata("processor_model", self._model)
        context.set_metadata("batch_size", self._batch_size)
        context.set_metadata("num_processed", len(texts))

        return results
