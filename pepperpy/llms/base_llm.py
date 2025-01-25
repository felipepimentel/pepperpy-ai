"""Base LLM module."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.utils.errors import PepperpyError


class LLMError(PepperpyError):
    """LLM error."""
    pass


class BaseLLM(ABC):
    """Base LLM class.
    
    This class defines the interface for LLMs in Pepperpy.
    All LLMs should inherit from this class.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize LLM.
        
        Args:
            name: LLM name
            config: Optional configuration dictionary
        """
        self.name = name
        self._config = config or {}
        self._is_initialized = False
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        return self._config
    
    @property
    def is_initialized(self) -> bool:
        """Check if LLM is initialized."""
        return self._is_initialized
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize LLM.
        
        This method should be called before using the LLM.
        """
        self._is_initialized = True
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up LLM.
        
        This method should be called when the LLM is no longer needed.
        """
        self._is_initialized = False
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
        **kwargs: Any,
    ) -> str:
        """Generate text from prompt.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            stop: Stop sequence(s)
            **kwargs: Additional model-specific parameters
            
        Returns:
            Generated text
            
        Raises:
            LLMError: If generation fails
        """
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings for text.
        
        Args:
            text: Input text
            
        Returns:
            Text embeddings
            
        Raises:
            LLMError: If embedding fails
        """
        pass
    
    @abstractmethod
    async def tokenize(self, text: str) -> List[str]:
        """Tokenize text.
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
            
        Raises:
            LLMError: If tokenization fails
        """
        pass
    
    @abstractmethod
    async def detokenize(self, tokens: List[str]) -> str:
        """Convert tokens back to text.
        
        Args:
            tokens: Input tokens
            
        Returns:
            Detokenized text
            
        Raises:
            LLMError: If detokenization fails
        """
        pass 