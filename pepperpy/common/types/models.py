"""Model types for Pepperpy."""

from typing import Any, Dict, List, Optional, Protocol, TypeVar, Union, runtime_checkable
from .base import Cloneable, Serializable, Validatable, ContextManageable, Disposable

# Type variables for model types
T = TypeVar("T")
M = TypeVar("M")

# Protocol for objects that can be used as models
@runtime_checkable
class Model(ContextManageable, Disposable, Protocol):
    """Protocol for objects that can be used as models."""
    
    @property
    def name(self) -> str:
        """Return model name."""
        ...
        
    @property
    def version(self) -> str:
        """Return model version."""
        ...
        
    @property
    def provider(self) -> str:
        """Return model provider."""
        ...
        
    @property
    def metadata(self) -> Dict[str, Any]:
        """Return model metadata."""
        ...

# Protocol for objects that can generate text
@runtime_checkable
class TextGenerator(Model, Protocol):
    """Protocol for objects that can generate text."""
    
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
        **kwargs: Any
    ) -> str:
        """Generate text from prompt."""
        ...

# Protocol for objects that can generate embeddings
@runtime_checkable
class EmbeddingGenerator(Model, Protocol):
    """Protocol for objects that can generate embeddings."""
    
    async def embed(
        self,
        text: Union[str, List[str]],
        **kwargs: Any
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings from text."""
        ...
        
    @property
    def embedding_dimension(self) -> int:
        """Return embedding dimension."""
        ...

# Protocol for objects that can be fine-tuned
@runtime_checkable
class Trainable(Model, Protocol):
    """Protocol for objects that can be fine-tuned."""
    
    async def train(
        self,
        training_data: Any,
        validation_data: Optional[Any] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Train model on data."""
        ...
        
    async def evaluate(
        self,
        test_data: Any,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Evaluate model on test data."""
        ...

# Protocol for objects that can be used as tokenizers
@runtime_checkable
class Tokenizer(Protocol):
    """Protocol for objects that can be used as tokenizers."""
    
    def encode(
        self,
        text: str,
        **kwargs: Any
    ) -> List[int]:
        """Encode text to token IDs."""
        ...
        
    def decode(
        self,
        token_ids: List[int],
        **kwargs: Any
    ) -> str:
        """Decode token IDs to text."""
        ...
        
    @property
    def vocabulary_size(self) -> int:
        """Return vocabulary size."""
        ...

# Protocol for objects that can be used as model configurations
@runtime_checkable
class ModelConfig(Protocol):
    """Protocol for objects that can be used as model configurations."""
    
    @property
    def model_type(self) -> str:
        """Return model type."""
        ...
        
    @property
    def model_name(self) -> str:
        """Return model name."""
        ...
        
    @property
    def provider(self) -> str:
        """Return model provider."""
        ...
        
    @property
    def parameters(self) -> Dict[str, Any]:
        """Return model parameters."""
        ... 