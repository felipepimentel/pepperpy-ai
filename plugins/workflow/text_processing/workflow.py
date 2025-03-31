"""Text processing workflow recipe plugin."""

from typing import Any, Dict, List, Optional, cast

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


class TextProcessingWorkflow(WorkflowProvider):
    """Text processing workflow provider."""

    def __init__(self, **config: Any) -> None:
        """Initialize the text processing workflow.

        Args:
            **config: Configuration options
                - processor: Processor to use ("spacy", "nltk", or "transformers")
                - model: Model to use (processor-specific)
                - device: Device to run on ("cpu" or "cuda")
                - batch_size: Batch size for processing
        """
        super().__init__()
        self._config = config
        self._processor = config.get("processor", "spacy")
        self._model = config.get("model")
        self._device = config.get("device", "cpu")
        self._batch_size = config.get("batch_size", 32)
        self._single_processor = None
        self._batch_processor = None

    async def initialize(self) -> None:
        """Initialize the workflow."""
        # Lazy initialization - will initialize processors when needed
        pass

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._single_processor:
            await self._single_processor.cleanup()

        if self._batch_processor:
            await self._batch_processor.cleanup()

    async def process_text(self, text: str, **options: Any) -> ProcessedText:
        """Process a single text.

        Args:
            text: Text to process
            **options: Additional processing options

        Returns:
            Processed text result
        """
        if not self._single_processor:
            self._single_processor = TextProcessingStage(
                processor=self._processor,
                model=self._model,
                device=self._device,
                batch_size=self._batch_size,
            )
            await self._single_processor.initialize()

        context = PipelineContext()
        # Adicionar opções ao contexto
        for key, value in options.items():
            context.set(key, value)

        return await self._single_processor.process(text, context)

    async def process_batch(
        self, texts: List[str], **options: Any
    ) -> List[ProcessedText]:
        """Process multiple texts.

        Args:
            texts: Texts to process
            **options: Additional processing options

        Returns:
            List of processed text results
        """
        if not self._batch_processor:
            self._batch_processor = BatchTextProcessingStage(
                processor=self._processor,
                model=self._model,
                device=self._device,
                batch_size=self._batch_size,
            )
            await self._batch_processor.initialize()

        context = PipelineContext()
        # Adicionar opções ao contexto
        for key, value in options.items():
            context.set(key, value)

        return await self._batch_processor.process(texts, context)

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow with the given input.

        Args:
            input_data: Input data with the following structure:
                {
                    "text": str or List[str],  # Text to process
                    "options": Dict[str, Any]  # Processing options
                }

        Returns:
            Dictionary with processed results
        """
        options = input_data.get("options", {})
        text_input = input_data.get("text")

        if text_input is None:
            raise ValueError("Input must contain 'text' field")

        if isinstance(text_input, str):
            result = await self.process_text(text_input, **options)
            return {"result": result}
        elif isinstance(text_input, list):
            results = await self.process_batch(text_input, **options)
            return {"results": results}
        else:
            raise ValueError("'text' must be a string or list of strings")
