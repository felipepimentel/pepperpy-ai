"""Learning types for Pepperpy."""

from typing import Any, Dict, List, Optional, Protocol, TypeVar, Union, runtime_checkable

# Type variables for learning types
T = TypeVar("T")
E = TypeVar("E")

# Protocol for objects that can be used as examples
@runtime_checkable
class Example(Protocol):
    """Protocol for objects that can be used as examples."""
    
    @property
    def input(self) -> str:
        """Return example input."""
        ...
        
    @property
    def output(self) -> str:
        """Return example output."""
        ...
        
    @property
    def metadata(self) -> Dict[str, Any]:
        """Return example metadata."""
        ...

# Protocol for objects that can manage examples
@runtime_checkable
class ExampleStore(Protocol[E]):
    """Protocol for objects that can manage examples."""
    
    async def add(self, example: E) -> None:
        """Add example to store."""
        ...
        
    async def get(self, example_id: str) -> Optional[E]:
        """Get example by ID."""
        ...
        
    async def find_similar(
        self,
        query: str,
        k: int = 5,
        threshold: float = 0.7
    ) -> List[E]:
        """Find similar examples."""
        ...

# Protocol for objects that can be used as models
@runtime_checkable
class Model(Protocol):
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