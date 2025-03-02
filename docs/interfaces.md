# Public Interfaces in PepperPy

## Overview

PepperPy provides a set of well-defined public interfaces that serve as the contract between the framework and its users. These interfaces define the capabilities and behaviors that users can rely on when building applications with PepperPy.

## Interface Design Principles

1. **Stability**: Public interfaces are designed to be stable across minor versions
2. **Consistency**: Interfaces follow consistent naming and design patterns
3. **Simplicity**: Interfaces are designed to be simple and intuitive to use
4. **Extensibility**: Interfaces are designed to be extensible for future needs
5. **Type Safety**: Interfaces use type hints to ensure type safety

## Core Interfaces

### LLM Interfaces

The LLM interfaces define the contract for language model providers:

```python
# pepperpy/llm/public.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Iterator

class LLMProvider(ABC):
    """Interface for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt."""
        pass

class StreamingLLMProvider(LLMProvider):
    """Interface for streaming LLM providers."""
    
    @abstractmethod
    def generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Generate text from a prompt as a stream."""
        pass
```

### Storage Interfaces

The Storage interfaces define the contract for storage providers:

```python
# pepperpy/storage/public.py
from abc import ABC, abstractmethod
from typing import Any, BinaryIO, List, Optional, Union

class StorageProvider(ABC):
    """Interface for storage providers."""
    
    @abstractmethod
    def save(self, data: Union[str, bytes, BinaryIO], path: str) -> str:
        """Save data to storage."""
        pass
        
    @abstractmethod
    def load(self, path: str) -> Union[str, bytes]:
        """Load data from storage."""
        pass
```

### Cloud Interfaces

The Cloud interfaces define the contract for cloud service providers:

```python
# pepperpy/cloud/public.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class CloudProvider(ABC):
    """Interface for cloud service providers."""
    
    @abstractmethod
    def invoke_function(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a cloud function."""
        pass
```

## Domain-Specific Interfaces

### Embedding Interfaces

```python
# pepperpy/embedding/public.py
from abc import ABC, abstractmethod
from typing import List, Union

class EmbeddingProvider(ABC):
    """Interface for embedding providers."""
    
    @abstractmethod
    def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text."""
        pass
```

### RAG Interfaces

```python
# pepperpy/rag/public.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class RAGProvider(ABC):
    """Interface for RAG (Retrieval Augmented Generation) providers."""
    
    @abstractmethod
    def retrieve(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query."""
        pass
        
    @abstractmethod
    def generate(self, query: str, documents: List[Dict[str, Any]], **kwargs) -> str:
        """Generate a response based on retrieved documents."""
        pass
```

### Agent Interfaces

```python
# pepperpy/agents/public.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class Agent(ABC):
    """Interface for agents."""
    
    @abstractmethod
    def run(self, task: str, **kwargs) -> Dict[str, Any]:
        """Run the agent on a task."""
        pass
```

## Capability Interfaces

Capability interfaces define additional capabilities that providers can implement:

```python
# pepperpy/capabilities/public.py
from abc import ABC, abstractmethod
from typing import Iterator

class StreamingCapable(ABC):
    """Interface for components with streaming capability."""
    
    @abstractmethod
    def stream(self, *args, **kwargs) -> Iterator[Any]:
        """Stream results."""
        pass
```

## Interface Versioning

Interfaces follow semantic versioning:

- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible functionality additions
- **PATCH**: Backwards-compatible bug fixes

## Interface Deprecation

When an interface is deprecated:

1. It is marked with a deprecation warning
2. A replacement interface is provided
3. The deprecated interface continues to work for at least one major version
4. Documentation is updated to guide users to the new interface

Example:

```python
import warnings

def deprecated(message):
    """Decorator to mark a function as deprecated."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator

class OldInterface(ABC):
    """Deprecated interface."""
    
    @deprecated("OldInterface is deprecated. Use NewInterface instead.")
    @abstractmethod
    def old_method(self):
        pass
```

## Interface Extension

Users can extend interfaces to add custom functionality:

```python
from pepperpy.llm import LLMProvider

class CustomLLMProvider(LLMProvider):
    """Custom LLM provider with additional functionality."""
    
    def generate(self, prompt: str, **kwargs) -> str:
        # Implementation...
        pass
        
    def custom_method(self):
        """Custom method not defined in the interface."""
        # Implementation...
        pass
```

## Interface Composition

Interfaces can be composed to create more complex interfaces:

```python
from pepperpy.llm import LLMProvider
from pepperpy.capabilities import StreamingCapable

class AdvancedLLMProvider(LLMProvider, StreamingCapable):
    """Advanced LLM provider with streaming capability."""
    
    def generate(self, prompt: str, **kwargs) -> str:
        # Implementation...
        pass
        
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        # Implementation...
        yield from chunks
```

## Interface Best Practices

1. **Use Type Hints**: Always use type hints to ensure type safety
2. **Document Methods**: Document all methods with clear docstrings
3. **Keep It Simple**: Keep interfaces simple and focused on a single responsibility
4. **Be Consistent**: Follow consistent naming and design patterns
5. **Provide Examples**: Include examples of how to use the interface
6. **Test Implementations**: Test all implementations of the interface

## Conclusion

Public interfaces are the foundation of the PepperPy framework. They provide a stable contract between the framework and its users, enabling users to build applications with confidence that they will continue to work across framework versions. 