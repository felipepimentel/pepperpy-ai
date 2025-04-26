"""SpaCy-based text processor for RAG."""

import logging
from typing import Any, Dict, List, Optional

import spacy

from pepperpy.rag.processor import (
    ProcessedText,
    ProcessingOptions,
    TextProcessor,
    TextProcessingError,
)
from pepperpy.plugin import ProviderPlugin
from pepperpy.core.errors import DomainError
from pepperpy.core.config import ConfigManager

logger = logging.getLogger(__name__)


class SpacyProcessor(TextProcessor, ProviderPlugin):
    """SpaCy-based text processor implementation."""
    
    # Configuration attributes
    model: str = "en_core_web_sm"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    def __init__(self, **kwargs: Any) -> None:
        """Initialize processor."""
        super().__init__(**kwargs)
        self.nlp = None
        
        # Get configuration from config.yaml if available
        config_manager = ConfigManager()
        config = config_manager.get_plugin_config("rag.processor.spacy")
        
        if config:
            self.model = config.get("model", self.model)
            self.chunk_size = config.get("chunk_size", self.chunk_size)
            self.chunk_overlap = config.get("chunk_overlap", self.chunk_overlap)
            
        # Override with explicit parameters if provided
        self.model = kwargs.get("model", self.model)
        self.chunk_size = kwargs.get("chunk_size", self.chunk_size)
        self.chunk_overlap = kwargs.get("chunk_overlap", self.chunk_overlap)
    
    async def initialize(self) -> None:
        """Initialize SpaCy resources."""
        if self.initialized:
            return
            
        try:
            # Load SpaCy model
            self.nlp = spacy.load(self.model)
            self.initialized = True
            self.logger.debug(f"Initialized SpaCy processor with model {self.model}")
        except Exception as e:
            self.logger.error(f"Failed to initialize SpaCy processor: {e}")
            raise DomainError(f"Failed to initialize SpaCy processor: {e}") from e
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return
            
        self.nlp = None
        self.initialized = False
        self.logger.debug("Cleaned up SpaCy processor")

    async def process(
        self, text: str, options: Optional[ProcessingOptions] = None
    ) -> ProcessedText:
        """Process text using spaCy.

        Args:
            text: Text to process
            options: Processing options

        Returns:
            Processed text result
            
        Raises:
            TextProcessingError: If processing fails
        """
        if not self.initialized or not self.nlp:
            await self.initialize()

        try:
            doc = self.nlp(text)
            return ProcessedText(
                text=text,
                tokens=[token.text for token in doc],
                entities=[
                    {
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char
                    }
                    for ent in doc.ents
                ],
                metadata={
                    "model": self.model,
                    "provider": "spacy",
                },
            )
        except Exception as e:
            raise TextProcessingError(f"spaCy processing failed: {e}")

    async def process_batch(
        self, texts: List[str], options: Optional[ProcessingOptions] = None
    ) -> List[ProcessedText]:
        """Process multiple texts using spaCy.

        Args:
            texts: Texts to process
            options: Processing options

        Returns:
            List of processed text results
            
        Raises:
            TextProcessingError: If processing fails
        """
        if not self.initialized or not self.nlp:
            await self.initialize()

        try:
            docs = list(self.nlp.pipe(texts))
            return [
                ProcessedText(
                    text=text,
                    tokens=[token.text for token in doc],
                    entities=[
                        {
                            "text": ent.text,
                            "label": ent.label_,
                            "start": ent.start_char,
                            "end": ent.end_char
                        }
                        for ent in doc.ents
                    ],
                    metadata={
                        "model": self.model,
                        "provider": "spacy",
                    },
                )
                for text, doc in zip(texts, docs)
            ]
        except Exception as e:
            raise TextProcessingError(f"spaCy batch processing failed: {e}")

    @property
    def name(self) -> str:
        """Get the processor name."""
        return "spacy"

    @property
    def capabilities(self) -> Dict[str, Any]:
        """Get the processor capabilities."""
        return {
            "tokenization": True,
            "entity_recognition": True,
            "batch_processing": True,
            "languages": ["en"],  # Add more based on model
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute text processing task.
        
        Args:
            input_data: Input data containing task and parameters
            
        Returns:
            Response dictionary with status and result/message
        """
        try:
            if not self.initialized:
                await self.initialize()
                
            task = input_data.get("task")
            
            if task == "chunk_text":
                text = input_data.get("text")
                if not text:
                    return {
                        "status": "error",
                        "message": "No text provided"
                    }
                    
                chunks = self._chunk_text(text)
                return {
                    "status": "success",
                    "result": {
                        "chunks": chunks
                    }
                }
            elif task == "process_text":
                text = input_data.get("text")
                if not text:
                    return {
                        "status": "error",
                        "message": "No text provided"
                    }
                
                options = ProcessingOptions(**(input_data.get("options") or {}))
                processed = await self.process(text, options)
                return {
                    "status": "success",
                    "result": processed.dict()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Unknown task: {task}"
                }
        except Exception as e:
            self.logger.error(f"Error executing task: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks using SpaCy.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        if not self.nlp:
            raise TextProcessingError("Processor not initialized")
            
        # Process text with SpaCy
        doc = self.nlp(text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sent in doc.sents:
            # If adding this sentence would exceed chunk size
            if current_length + len(sent.text) > self.chunk_size and current_chunk:
                # Join current chunk and add to chunks
                chunk_text = " ".join(current_chunk)
                chunks.append(chunk_text)
                
                # Start new chunk with overlap
                if self.chunk_overlap > 0:
                    # Take sentences from end of previous chunk for overlap
                    overlap_text = 0
                    overlap_sents = []
                    for prev_sent in reversed(current_chunk):
                        if overlap_text + len(prev_sent) > self.chunk_overlap:
                            break
                        overlap_text += len(prev_sent)
                        overlap_sents.insert(0, prev_sent)
                    
                    current_chunk = overlap_sents
                    current_length = overlap_text
                else:
                    current_chunk = []
                    current_length = 0
            
            current_chunk.append(sent.text)
            current_length += len(sent.text)
        
        # Add final chunk if any sentences remain
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(chunk_text)
        
        return chunks 