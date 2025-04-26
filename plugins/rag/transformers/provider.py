"""Transformers-based text processor for RAG."""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel

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


class TransformersProcessor(TextProcessor, ProviderPlugin):
    """Transformers-based text processor implementation."""
    
    # Configuration attributes
    model: str = "distilbert-base-uncased"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_length: int = 512
    device: str = "cpu"
    
    def __init__(self, **kwargs: Any) -> None:
        """Initialize processor."""
        super().__init__(**kwargs)
        self.tokenizer = None
        self.model_instance = None
        self._initialized = False
        
        # Get configuration from config.yaml if available
        config_manager = ConfigManager()
        config = config_manager.get_plugin_config("rag.processor.transformers")
        
        if config:
            self.model = config.get("model", self.model)
            self.chunk_size = config.get("chunk_size", self.chunk_size)
            self.chunk_overlap = config.get("chunk_overlap", self.chunk_overlap)
            self.max_length = config.get("max_length", self.max_length)
            self.device = config.get("device", self.device)
        
        # Override with explicit parameters if provided
        self.model = kwargs.get("model", self.model)
        self.chunk_size = kwargs.get("chunk_size", self.chunk_size)
        self.chunk_overlap = kwargs.get("chunk_overlap", self.chunk_overlap)
        self.max_length = kwargs.get("max_length", self.max_length)
        self.device = kwargs.get("device", self.device)
    
    @property
    def initialized(self) -> bool:
        """Check if the processor is initialized."""
        return self._initialized
    
    async def initialize(self) -> None:
        """Initialize Transformers resources."""
        if self._initialized:
            return
            
        try:
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model)
            self.model_instance = AutoModel.from_pretrained(self.model)
            
            # Set device
            device = torch.device(self.device)
            self.model_instance = self.model_instance.to(device)
            
            self._initialized = True
            logger.debug(f"Initialized Transformers processor with model {self.model} on {self.device}")
        except Exception as e:
            logger.error(f"Failed to initialize Transformers processor: {e}")
            raise DomainError(f"Failed to initialize Transformers processor: {e}") from e
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self._initialized:
            return
            
        # Clear CUDA cache if using GPU
        if self.device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        self.tokenizer = None
        self.model_instance = None
        self._initialized = False
        logger.debug("Cleaned up Transformers processor")

    async def process_text(
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
        if not self._initialized or not self.tokenizer or not self.model_instance:
            await self.initialize()

        try:
            # Chunk the text
            chunks = self._chunk_text(text)
            
            # Tokenize the chunks
            token_lists = [self.tokenizer.tokenize(chunk) for chunk in chunks]
            
            # Get embeddings for each chunk
            embeddings_list = []
            for chunk in chunks:
                embeddings = self._get_embeddings(chunk)
                embeddings_list.append(embeddings.cpu().numpy())
            
            return ProcessedText(
                chunks=chunks,
                tokens=token_lists,
                embeddings=embeddings_list,
                metadata={
                    "model": self.model,
                    "provider": "transformers",
                    "embedding_dim": embeddings_list[0].shape[-1] if embeddings_list else 0
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
        if not self._initialized or not self.tokenizer or not self.model_instance:
            await self.initialize()

        try:
            results = []
            for text in texts:
                # Process each text individually
                processed = await self.process_text(text, options)
                results.append(processed)
                
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
            "embedding_generation": True,
            "batch_processing": True,
            "max_sequence_length": self.max_length
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute text processing task.
        
        Args:
            input_data: Input data containing task and parameters
            
        Returns:
            Response dictionary with status and result/message
        """
        try:
            if not self._initialized:
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
                processed = await self.process_text(text, options)
                
                # Convert ProcessedText to dict for response
                response_dict = {
                    "chunks": processed.chunks,
                    "tokens": processed.tokens,
                    "embeddings": [emb.tolist() for emb in processed.embeddings] if input_data.get("full_embeddings") else None,
                    "embeddings_shape": [emb.shape for emb in processed.embeddings] if processed.embeddings else None,
                    "metadata": processed.metadata
                }
                
                return {
                    "status": "success",
                    "result": response_dict
                }
            else:
                return {
                    "status": "error",
                    "message": f"Unknown task: {task}"
                }
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
            
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        # Simple implementation of text chunking
        text = text.strip()
        
        # If text is shorter than chunk size, return it as a single chunk
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Find a good ending point
            end = min(start + self.chunk_size, len(text))
            
            # Try to end at a sentence or paragraph boundary
            if end < len(text):
                # Look for paragraph boundary
                paragraph_end = text.rfind("\n\n", start, end)
                if paragraph_end > start + int(self.chunk_size * 0.5):
                    end = paragraph_end + 2
                else:
                    # Look for sentence boundary
                    sentence_end = text.rfind(". ", start, end)
                    if sentence_end > start + int(self.chunk_size * 0.5):
                        end = sentence_end + 2
                    else:
                        # Look for space
                        space_end = text.rfind(" ", start, end)
                        if space_end > start + int(self.chunk_size * 0.5):
                            end = space_end + 1
            
            chunk = text[start:end].strip()
            chunks.append(chunk)
            
            # Overlap with the next chunk
            start = end - self.chunk_overlap
            if start < 0 or start >= len(text):
                break
        
        return chunks
    
    def _get_embeddings(self, text: str) -> torch.Tensor:
        """Generate embeddings for a text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embeddings tensor
        """
        # Tokenize the text
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            padding=True, 
            truncation=True, 
            max_length=self.max_length
        )
        
        # Move inputs to the correct device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate embeddings
        with torch.no_grad():
            outputs = self.model_instance(**inputs)
            
        # Use the last hidden state as embeddings (first token [CLS] for whole sequence)
        return outputs.last_hidden_state[:, 0, :]
    
    def _get_batch_embeddings(self, texts: List[str]) -> torch.Tensor:
        """Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Batch of embeddings tensors
        """
        # Tokenize the texts
        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.max_length
        )
        
        # Move inputs to the correct device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate embeddings
        with torch.no_grad():
            outputs = self.model_instance(**inputs)
            
        # Use the last hidden state as embeddings (first token [CLS] for whole sequence)
        return outputs.last_hidden_state[:, 0, :] 