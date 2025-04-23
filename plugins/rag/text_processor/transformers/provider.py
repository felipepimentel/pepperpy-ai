"""Transformers text processor implementation."""

import logging
from typing import dict, list, Any

from pepperpy.rag import RAGProvider
from pepperpy.plugin import ProviderPlugin
from pepperpy.rag.processor import (
from pepperpy.rag.base import RagError
from pepperpy.rag.base import RagError

logger = logging.getLogger(__name__)
    ProcessedText,
    ProcessingOptions,
    TextProcessingError,
    TextProcessor,
)

logger = logger.getLogger(__name__)


class TransformersProcessor(class TransformersProcessor(TextProcessor, ProviderPlugin):
    """Text processor using Hugging Face Transformers."""):
    """
    Rag transformersprocessor provider.
    
    This provider implements transformersprocessor functionality for the PepperPy rag framework.
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        model_name: str = "distilbert-base-uncased",
        tokenizer_name: str | None = None,
        device: str = "cpu",
    ) -> None:
        """Initialize the Transformers processor.

        Args:
            config: Configuration dictionary
            model_name: Name of the model to use
            tokenizer_name: Name of the tokenizer (uses model_name if None)
            device: Device to run the model on (cpu, cuda, etc.)
        """
        super().__init__()
        config = config or {}
        self._model_name = config.get("model_name", model_name)
        self._tokenizer_name = (
            config.get("tokenizer_name", tokenizer_name) or self._model_name
        )
        self._device = config.get("device", device)
        self._model = None
        self._tokenizer = None
        self._pipeline = None
        self.initialized = False

    async def initialize(self) -> None:
 """Initialize the provider.

        This method is called automatically when the provider is first used.
        It sets up resources needed by the provider.
 """
        if self.initialized:
            return
            
        try:
            # Import here to avoid dependency issues if transformers is not installed
            from transformers import AutoModel, AutoTokenizer, pipeline

            logger.info(f"Loading Transformers model: {self._model_name}")

            # Load tokenizer and model
            self._tokenizer = AutoTokenizer.from_pretrained(self._tokenizer_name)
            self._model = AutoModel.from_pretrained(self._model_name).to(self._device)

            # Initialize NER pipeline if available
            try:
                self._pipeline = pipeline(
                    "ner",
                    model=self._model_name,
                    tokenizer=self._tokenizer,
                    device=self._device if self._device != "cpu" else -1,
                )
            except Exception as e:
                logger.warning(f"NER pipeline not available: {e}")
                self._pipeline = None
                
            self.initialized = True

        except Exception as e:
            raise TextProcessingError(f"Failed to load Transformers model: {e}")

    async def cleanup(self) -> None:
 """Clean up provider resources.

        This method is called automatically when the context manager exits.
        It releases any resources acquired during initialization.
 """
        self._model = None
        self._tokenizer = None
        self._pipeline = None
        self.initialized = False

    async def process(
        self, text: str, options: ProcessingOptions | None = None
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
        if not self._tokenizer or not self._model:
            await self.initialize()
            if not self._tokenizer or not self._model:
                raise TextProcessingError("Transformers model not initialized")

        try:
            # Import torch here to avoid dependency issues
            import torch

            # Tokenize text
            inputs = self._tokenizer(
                text, return_tensors="pt", padding=True, truncation=True
            )
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            # Get model outputs
            with torch.no_grad():
                outputs = self._model(**inputs)

            # Extract embeddings
            embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy().tolist()

            # Get tokens
            tokens = self._tokenizer.convert_ids_to_tokens(
                inputs["input_ids"][0].cpu().numpy()
            )

            # Get entities if pipeline is available
            entities = []
            if self._pipeline:
                try:
                    ner_results = self._pipeline(text)
                    for entity in ner_results:
                        entities.append({
                            "text": entity["word"],
                            "label": entity["entity"],
                            "score": entity["score"],
                            "start": entity.get("start", 0),
                            "end": entity.get("end", 0),
                        })
                except Exception as e:
                    logger.warning(f"Entity extraction failed: {e}")

            return ProcessedText(
                text=text,
                tokens=tokens,
                entities=entities,
                metadata={
                    "embeddings": embeddings,
                    "model_name": self._model_name,
                },
            )
        except Exception as e:
            raise TextProcessingError(f"Transformers processing failed: {e}")

    async def process_batch(
        self, texts: list[str], options: ProcessingOptions | None = None
    ) -> list[ProcessedText]:
        """Process multiple texts using Transformers.

        Args:
            texts: Texts to process
            options: Processing options

        Returns:
            list of processed text results

        Raises:
            TextProcessingError: If processing fails
        """
        try:
            return [await self.process(text, options) for text in texts]
        except Exception as e:
            raise TextProcessingError(f"Transformers batch processing failed: {e}")

    @property
    def name(self) -> str:

    """Get the processor name.


    Returns:

        Return description

    """
        return "transformers"

    @property
    def capabilities(self) -> dict[str, Any]:

    """Get the processor capabilities.


    Returns:

        Return description

    """
        return {
            "tokenization": True,
            "embeddings": True,
            "entity_recognition": self._pipeline is not None,
            "batch_processing": True,
            "model_name": self._model_name,
            "device": self._device,
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
            raise RagError("No task specified")
            
        try:
            if not self.initialized:
                await self.initialize()
                
            if task_type == "process":
                text = input_data.get("text")
                if not text:
                    raise RagError("No text provided")
                    
                options_dict = input_data.get("options", {})
                options = ProcessingOptions(
                    model=options_dict.get("model", "default"),
                    disable=options_dict.get("disable", []),
                    additional_options=options_dict.get("additional_options", {})
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
                    raise RagError("No texts provided")
                    
                options_dict = input_data.get("options", {})
                options = ProcessingOptions(
                    model=options_dict.get("model", "default"),
                    disable=options_dict.get("disable", []),
                    additional_options=options_dict.get("additional_options", {})
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
                raise RagError(f"Unknown task type: {task_type)"}
                
        except Exception as e:
            logger.error(f"Error executing task '{task_type}': {e}")
            return {"status": "error", "message": str(e)} 