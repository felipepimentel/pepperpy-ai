"""NLTK-based text processor for RAG."""

import logging
from typing import Any, Dict, List, Optional

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import PorterStemmer, WordNetLemmatizer

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


class NLTKProcessor(TextProcessor, ProviderPlugin):
    """NLTK-based text processor implementation."""
    
    # Configuration attributes
    language: str = "english"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    stemming: bool = False
    lemmatization: bool = True
    
    def __init__(self, **kwargs: Any) -> None:
        """Initialize processor."""
        super().__init__(**kwargs)
        self.stemmer = None
        self.lemmatizer = None
        self.initialized = False
        
        # Required NLTK resources
        self.required_resources = [
            'punkt',           # For sentence tokenization
            'wordnet',         # For lemmatization
            'averaged_perceptron_tagger'  # For POS tagging
        ]
        
        # Get configuration from config.yaml if available
        config_manager = ConfigManager()
        config = config_manager.get_plugin_config("rag.processor.nltk")
        
        if config:
            self.language = config.get("language", self.language)
            self.chunk_size = config.get("chunk_size", self.chunk_size)
            self.chunk_overlap = config.get("chunk_overlap", self.chunk_overlap)
            self.stemming = config.get("stemming", self.stemming)
            self.lemmatization = config.get("lemmatization", self.lemmatization)
        
        # Override with explicit parameters if provided
        self.language = kwargs.get("language", self.language)
        self.chunk_size = kwargs.get("chunk_size", self.chunk_size)
        self.chunk_overlap = kwargs.get("chunk_overlap", self.chunk_overlap)
        self.stemming = kwargs.get("stemming", self.stemming)
        self.lemmatization = kwargs.get("lemmatization", self.lemmatization)
    
    async def initialize(self) -> None:
        """Initialize NLTK resources."""
        if self.initialized:
            return
            
        try:
            # Download required NLTK resources if needed
            for resource in self.required_resources:
                try:
                    nltk.data.find(f'tokenizers/{resource}')
                except LookupError:
                    nltk.download(resource, quiet=True)
            
            # Initialize stemmer and lemmatizer
            if self.stemming:
                self.stemmer = PorterStemmer()
            
            if self.lemmatization:
                self.lemmatizer = WordNetLemmatizer()
            
            self.initialized = True
            self.logger.debug(f"Initialized NLTK processor with language {self.language}")
        except Exception as e:
            self.logger.error(f"Failed to initialize NLTK processor: {e}")
            raise DomainError(f"Failed to initialize NLTK processor: {e}") from e
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return
            
        self.stemmer = None
        self.lemmatizer = None
        self.initialized = False
        self.logger.debug("Cleaned up NLTK processor")

    async def process(
        self, text: str, options: Optional[ProcessingOptions] = None
    ) -> ProcessedText:
        """Process text using NLTK.

        Args:
            text: Text to process
            options: Processing options

        Returns:
            Processed text result
            
        Raises:
            TextProcessingError: If processing fails
        """
        if not self.initialized:
            await self.initialize()

        try:
            # Tokenize text into sentences and words
            sentences = sent_tokenize(text, language=self.language)
            tokens = word_tokenize(text, language=self.language)
            
            # Apply stemming or lemmatization if configured
            processed_tokens = tokens
            if self.stemming and self.stemmer:
                processed_tokens = [self.stemmer.stem(token) for token in tokens]
            elif self.lemmatization and self.lemmatizer:
                processed_tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
            
            return ProcessedText(
                text=text,
                tokens=tokens,
                sentences=sentences,
                metadata={
                    "language": self.language,
                    "provider": "nltk",
                    "processed_tokens": processed_tokens if processed_tokens != tokens else None
                },
            )
        except Exception as e:
            raise TextProcessingError(f"NLTK processing failed: {e}")

    async def process_batch(
        self, texts: List[str], options: Optional[ProcessingOptions] = None
    ) -> List[ProcessedText]:
        """Process multiple texts using NLTK.

        Args:
            texts: Texts to process
            options: Processing options

        Returns:
            List of processed text results
            
        Raises:
            TextProcessingError: If processing fails
        """
        if not self.initialized:
            await self.initialize()

        try:
            return [await self.process(text, options) for text in texts]
        except Exception as e:
            raise TextProcessingError(f"NLTK batch processing failed: {e}")

    @property
    def name(self) -> str:
        """Get the processor name."""
        return "nltk"

    @property
    def capabilities(self) -> Dict[str, Any]:
        """Get the processor capabilities."""
        return {
            "tokenization": True,
            "sentence_splitting": True,
            "stemming": self.stemming,
            "lemmatization": self.lemmatization,
            "batch_processing": True,
            "languages": [self.language],
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
                
                # Convert ProcessedText to dict for response
                response_dict = {
                    "text": processed.text,
                    "tokens": processed.tokens,
                    "sentences": processed.sentences,
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
            self.logger.error(f"Error executing task: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks using NLTK.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        # Tokenize text into sentences
        sentences = sent_tokenize(text, language=self.language)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size
            if current_length + len(sentence) > self.chunk_size and current_chunk:
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
            
            current_chunk.append(sentence)
            current_length += len(sentence)
        
        # Add final chunk if any sentences remain
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(chunk_text)
        
        return chunks 