"""Text processing workflow provider implementation."""

from typing import Dict, List, Any, cast
import logging

from pepperpy.workflow import WorkflowProvider
from pepperpy.plugin import ProviderPlugin
from pepperpy.rag.processor import (
    ProcessedText,
    ProcessingOptions,
    TextProcessor,
    TextProcessingError,
)
from pepperpy.rag.processors import (
    NLTKProcessor,
    SpacyProcessor,
    TransformersProcessor,
)
from pepperpy.workflow.base import PipelineContext, PipelineStage, WorkflowProvider
from pepperpy.workflow.base import WorkflowError

logger = logging.getLogger(__name__)


class TextProcessingError(WorkflowError):
    """Error during text processing workflow."""
    
    def __init__(self, message: str, cause: Exception | None = None) -> None:
        """Initialize error with message and optional cause.
        
        Args:
            message: Error description
            cause: Original exception that caused this error
        """
        super().__init__(message)
        self.__cause__ = cause


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
        """Initialize the provider.

        This method is called automatically when the provider is first used.
        It sets up resources needed by the provider.
        
        Raises:
            TextProcessingError: If initialization fails
        """
        try:
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
                raise TextProcessingError(f"Unknown processor type: {self._processor_type}")

            if self._processor:
                try:
                    await self._processor.initialize()
                    logger.debug(
                        f"Initialized {self._processor_type} processor with model={self._model}"
                    )
                except Exception as e:
                    raise TextProcessingError(
                        f"Failed to initialize {self._processor_type} processor: {e}",
                        cause=e
                    )
        except Exception as e:
            if not isinstance(e, TextProcessingError):
                raise TextProcessingError(f"Initialization failed: {e}", cause=e) from e
            raise

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method is called automatically when the context manager exits.
        It releases any resources acquired during initialization.
        """
        if self._processor:
            try:
                await self._processor.cleanup()
                logger.debug(f"Cleaned up {self._processor_type} processor")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            finally:
                self._processor = None

    async def process(self, text: str, context: PipelineContext) -> ProcessedText:
        """Process text using the selected processor.

        Args:
            text: Text to process
            context: Pipeline context

        Returns:
            Processed text result
            
        Raises:
            TextProcessingError: If processing fails
        """
        if not self._processor:
            await self.initialize()

        # After initialize(), self._processor is guaranteed to be set
        processor = cast(TextProcessor, self._processor)

        try:
            options = ProcessingOptions(
                model=self._model if self._model is not None else "default",
                additional_options=context.get("processing_options", {}),
            )

            result = await processor.process(text, options)

            # Store processor info in context
            context.set_metadata("processor_type", self._processor_type)
            context.set_metadata("processor_model", self._model)
            context.set_metadata("text_length", len(text))

            logger.debug(
                f"Processed text with {self._processor_type} "
                f"(length={len(text)}, model={self._model})"
            )

            return result
        except Exception as e:
            raise TextProcessingError(
                f"Text processing failed with {self._processor_type}: {e}",
                cause=e
            ) from e


class BatchTextProcessingStage(PipelineStage[List[str], List[ProcessedText]]):
    """Pipeline stage for batch text processing.
    
    This stage processes multiple texts in batches using the specified NLP processor.
    It includes comprehensive error handling and logging of processing operations.
    """

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
            
        Raises:
            ValueError: If batch_size is less than 1
        """
        if batch_size < 1:
            raise ValueError("batch_size must be at least 1")
            
        super().__init__(
            name="batch_text_processing",
            description="Process multiple texts using NLP tools"
        )
        self._processor_type = processor
        self._model = model
        self._device = device
        self._batch_size = batch_size
        self._processor: TextProcessor | None = None
        
        logger.debug(
            f"Created BatchTextProcessingStage with processor={processor}, "
            f"model={model}, device={device}, batch_size={batch_size}"
        )

    async def initialize(self) -> None:
        """Initialize the provider.

        This method is called automatically when the provider is first used.
        It sets up the text processor based on the specified type and configuration.
        
        Raises:
            TextProcessingError: If initialization fails or processor type is unknown
        """
        try:
            logger.info(
                f"Initializing {self._processor_type} processor "
                f"(model={self._model}, device={self._device})"
            )
            
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
                raise TextProcessingError(f"Unknown processor type: {self._processor_type}")

            if self._processor:
                try:
                    await self._processor.initialize()
                    logger.info(
                        f"Successfully initialized {self._processor_type} processor "
                        f"with model={self._model}"
                    )
                except Exception as e:
                    raise TextProcessingError(
                        f"Failed to initialize {self._processor_type} processor: {e}",
                        cause=e
                    )
        except Exception as e:
            if not isinstance(e, TextProcessingError):
                raise TextProcessingError(f"Initialization failed: {e}", cause=e) from e
            raise

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method is called automatically when the context manager exits.
        It releases any resources acquired during initialization.
        """
        if self._processor:
            try:
                await self._processor.cleanup()
                logger.info(f"Successfully cleaned up {self._processor_type} processor")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            finally:
                self._processor = None

    async def process(
        self, texts: List[str], context: PipelineContext
    ) -> List[ProcessedText]:
        """Process multiple texts using the selected processor.

        Args:
            texts: List of texts to process
            context: Pipeline context

        Returns:
            List of processed text results
            
        Raises:
            TextProcessingError: If processing fails
            ValueError: If texts list is empty
        """
        if not texts:
            raise ValueError("texts list cannot be empty")
            
        if not self._processor:
            await self.initialize()

        # After initialize(), self._processor is guaranteed to be set
        processor = cast(TextProcessor, self._processor)

        try:
            logger.info(
                f"Processing {len(texts)} texts with {self._processor_type} "
                f"(batch_size={self._batch_size})"
            )
            
            options = ProcessingOptions(
                model=self._model if self._model is not None else "default",
                additional_options=context.get("processing_options", {}),
            )

            # Process texts in batches
            results: List[ProcessedText] = []
            total_chars = sum(len(text) for text in texts)
            
            for i in range(0, len(texts), self._batch_size):
                batch = texts[i:i + self._batch_size]
                try:
                    batch_results = await processor.process_batch(batch, options)
                    results.extend(batch_results)
                    
                    logger.debug(
                        f"Processed batch {i//self._batch_size + 1} "
                        f"({len(batch)} texts)"
                    )
                except Exception as e:
                    raise TextProcessingError(
                        f"Failed to process batch {i//self._batch_size + 1}: {e}",
                        cause=e
                    ) from e

            # Store processing metadata in context
            context.set_metadata("processor_type", self._processor_type)
            context.set_metadata("processor_model", self._model)
            context.set_metadata("total_texts", len(texts))
            context.set_metadata("total_chars", total_chars)
            context.set_metadata("avg_text_length", total_chars / len(texts))
            context.set_metadata("num_batches", (len(texts) + self._batch_size - 1) // self._batch_size)

            logger.info(
                f"Successfully processed {len(texts)} texts "
                f"(total_chars={total_chars}, avg_length={total_chars/len(texts):.1f})"
            )

            return results
        except Exception as e:
            if not isinstance(e, (TextProcessingError, ValueError)):
                raise TextProcessingError(
                    f"Batch processing failed with {self._processor_type}: {e}",
                    cause=e
                ) from e
            raise


class TextProcessingProvider(WorkflowProvider, ProviderPlugin):
    """Text processing workflow provider implementation.

    This provider implements NLP processing functionality including:
    - Text normalization
    - Named entity extraction
    - Keyword extraction
    - Text summarization
    """

    async def initialize(self) -> None:
        """Initialize the provider.

        This method is called automatically when the provider is first used.
        It sets up resources needed by the provider.
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
        
        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method is called automatically when the context manager exits.
        It releases any resources acquired during initialization.
        """
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
            list of processed text results
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
                    "text": str or list[str],  # Text to process
                    "options": dict[str, Any]  # Processing options
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
                raise WorkflowError("Input must contain 'text' field")

            if task_type == "process_text":
                # Handle single text processing
                if not isinstance(text_input, str):
                    raise WorkflowError("'text' must be a string for process_text task",
                    )

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
                    raise WorkflowError("'text' must be a list of strings for process_batch task",
                    )

                results = await self.process_batch(text_input, **options)
                return {
                    "status": "success",
                    "results": [
                        r.model_dump() if hasattr(r, "model_dump") else dict(r)
                        for r in results
                    ],
                }

            else:
                raise WorkflowError(f"Unknown task: {task_type}")

        except Exception as e:
            self.logger.error(f"Error executing task '{task_type}': {e}")
            return {"status": "error", "message": str(e)}
