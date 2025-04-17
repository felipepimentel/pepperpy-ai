"""Text processing workflow provider implementation."""

from typing import Any, cast

from pepperpy.plugin.provider import BasePluginProvider
from pepperpy.rag.pipeline.processors import (
    NLTKProcessor,
    ProcessedText,
    ProcessingOptions,
    SpacyProcessor,
    TextProcessor,
    TransformersProcessor,
)
from pepperpy.workflow.base import PipelineContext, PipelineStage, WorkflowProvider


class TextProcessingStage(PipelineStage[str, ProcessedText]):
    """Pipeline stage for text processing."""

    def __init__(
        self,
        processor: str = "spacy",
        model: str | None = None,
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
        self._processor: TextProcessor | None = None

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

        if self._processor:
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


class BatchTextProcessingStage(PipelineStage[list[str], list[ProcessedText]]):
    """Pipeline stage for batch text processing."""

    def __init__(
        self,
        processor: str = "spacy",
        model: str | None = None,
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
        self._processor: TextProcessor | None = None

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

        if self._processor:
            await self._processor.initialize()

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._processor:
            await self._processor.cleanup()

    async def process(
        self, texts: list[str], context: PipelineContext
    ) -> list[ProcessedText]:
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


class TextProcessingProvider(WorkflowProvider, BasePluginProvider):
    """Text processing workflow provider implementation.

    This provider implements NLP processing functionality including:
    - Text normalization
    - Named entity extraction
    - Keyword extraction
    - Text summarization
    """

    async def initialize(self) -> None:
        """Initialize the workflow provider.

        This method is called when the provider is first used.
        """
        # Initialize from parent first
        await super().initialize()

        if self.initialized:
            return

        # Initialize configuration
        self._processor = self.config.get("processor", "spacy")
        self._model = self.config.get("model")
        self._device = self.config.get("device", "cpu")
        self._batch_size = int(self.config.get("batch_size", 32))

        # These are lazily initialized
        self._single_processor = None
        self._batch_processor = None

        self.logger.debug(
            f"Initialized text processing provider with processor={self._processor}, "
            f"model={self._model}, device={self._device}, batch_size={self._batch_size}"
        )

    async def cleanup(self) -> None:
        """Clean up resources used by the provider."""
        try:
            # Cleanup processor resources if they were initialized
            if hasattr(self, "_single_processor") and self._single_processor:
                await self._single_processor.cleanup()

            if hasattr(self, "_batch_processor") and self._batch_processor:
                await self._batch_processor.cleanup()

            self.logger.debug("Cleaned up text processing provider resources")
        except Exception as e:
            self.logger.error(f"Error during text processing provider cleanup: {e}")

        # Always call parent cleanup last
        await super().cleanup()

    async def process_text(self, text: str, **options: Any) -> ProcessedText:
        """Process a single text.

        Args:
            text: Text to process
            **options: Additional processing options

        Returns:
            Processed text result
        """
        if not hasattr(self, "_single_processor") or not self._single_processor:
            self._single_processor = TextProcessingStage(
                processor=self._processor,
                model=self._model,
                device=self._device,
                batch_size=self._batch_size,
            )
            await self._single_processor.initialize()

        context = PipelineContext()
        # Add options to context
        for key, value in options.items():
            context.set(key, value)

        return await self._single_processor.process(text, context)

    async def process_batch(
        self, texts: list[str], **options: Any
    ) -> list[ProcessedText]:
        """Process multiple texts.

        Args:
            texts: Texts to process
            **options: Additional processing options

        Returns:
            List of processed text results
        """
        if not hasattr(self, "_batch_processor") or not self._batch_processor:
            self._batch_processor = BatchTextProcessingStage(
                processor=self._processor,
                model=self._model,
                device=self._device,
                batch_size=self._batch_size,
            )
            await self._batch_processor.initialize()

        context = PipelineContext()
        # Add options to context
        for key, value in options.items():
            context.set(key, value)

        return await self._batch_processor.process(texts, context)

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the workflow with the given input.

        Args:
            input_data: Input data with the following structure:
                {
                    "task": str,  # Task to execute (process_text, process_batch)
                    "text": str or List[str],  # Text to process
                    "options": Dict[str, Any]  # Processing options
                }

        Returns:
            Dictionary with processed results
        """
        # Handle initialization if not already done
        if not self.initialized:
            await self.initialize()

        # Get task type from input
        task_type = input_data.get("task", "process_text")
        options = input_data.get("options", {})
        text_input = input_data.get("text")

        try:
            if not text_input:
                return {"status": "error", "message": "Input must contain 'text' field"}

            if task_type == "process_text":
                # Handle single text processing
                if not isinstance(text_input, str):
                    return {
                        "status": "error",
                        "message": "'text' must be a string for process_text task",
                    }

                result = await self.process_text(text_input, **options)
                return {
                    "status": "success",
                    "result": result.model_dump()
                    if hasattr(result, "model_dump")
                    else dict(result),
                }

            elif task_type == "process_batch":
                # Handle batch text processing
                if not isinstance(text_input, list):
                    return {
                        "status": "error",
                        "message": "'text' must be a list of strings for process_batch task",
                    }

                results = await self.process_batch(text_input, **options)
                return {
                    "status": "success",
                    "results": [
                        r.model_dump() if hasattr(r, "model_dump") else dict(r)
                        for r in results
                    ],
                }

            else:
                return {"status": "error", "message": f"Unknown task: {task_type}"}

        except Exception as e:
            self.logger.error(f"Error executing task '{task_type}': {e}")
            return {"status": "error", "message": str(e)}
