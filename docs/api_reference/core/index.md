# Core Functionality

PepperPy AI's core module provides fundamental functionality and base classes used throughout the system.

## Overview

The core module provides:
- Base classes
- Core interfaces
- Common utilities
- Exception handling
- Type definitions

## Core Components

### Base Classes

The fundamental building blocks:

```python
from pepperpy.core import BaseComponent
from pepperpy.config import Config

class CustomComponent(BaseComponent):
    """Custom component implementation."""
    
    def __init__(self, config: Config):
        super().__init__(config)
        self.initialize()
    
    async def process(self, input: str) -> str:
        """Process input data."""
        return await self._process_implementation(input)
```

### Core Interfaces

Standard interfaces for components:

```python
from pepperpy.core import ProcessorInterface, AsyncProcessor
from typing import Protocol

class CustomProcessor(ProcessorInterface):
    """Custom processor implementation."""
    
    async def process(self, input: str) -> str:
        """Process input data."""
        ...
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        ...
```

## Core Features

### Initialization

```python
from pepperpy.core import Initializable

class CustomService(Initializable):
    """Custom service with initialization."""
    
    async def initialize(self) -> None:
        """Initialize service."""
        await self.setup_resources()
        await self.validate_config()
    
    async def cleanup(self) -> None:
        """Cleanup service."""
        await self.release_resources()
```

### Error Handling

```python
from pepperpy.core.exceptions import CoreError

class CustomError(CoreError):
    """Custom error type."""
    
    def __init__(self, message: str, code: int = None):
        super().__init__(message)
        self.code = code

# Using error handling
try:
    result = await process_data()
except CustomError as e:
    handle_error(e)
```

### Type Definitions

```python
from pepperpy.core.types import (
    ProcessResult,
    ComponentConfig,
    ProcessorType
)

# Type definitions
ProcessResult = dict[str, Any]
ComponentConfig = dict[str, Union[str, int, float, bool]]
ProcessorType = Literal["text", "chat", "embedding"]
```

## Best Practices

1. **Component Design**
   - Inherit from base classes
   - Implement required interfaces
   - Follow async patterns

2. **Error Handling**
   - Use custom exceptions
   - Provide error context
   - Handle cleanup properly

3. **Type Safety**
   - Use type hints
   - Define clear interfaces
   - Validate input types

4. **Resource Management**
   - Proper initialization
   - Clean resource cleanup
   - Handle async context

## Examples

### Custom Component

```python
from pepperpy.core import BaseComponent
from pepperpy.config import Config

class DataProcessor(BaseComponent):
    """Custom data processor."""
    
    def __init__(self, config: Config):
        super().__init__(config)
        self.validate_config()
    
    async def process(self, data: dict) -> dict:
        """Process input data."""
        try:
            result = await self._process_data(data)
            return self._format_result(result)
        except Exception as e:
            raise CoreError(f"Processing failed: {e}")
```

### Async Context Manager

```python
from pepperpy.core import AsyncContextManager

class ResourceManager(AsyncContextManager):
    """Resource manager with context support."""
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        await self.cleanup()
```

### Type-Safe Processing

```python
from pepperpy.core import ProcessorInterface
from typing import TypeVar, Generic

T = TypeVar("T")
R = TypeVar("R")

class GenericProcessor(ProcessorInterface, Generic[T, R]):
    """Generic processor with type safety."""
    
    async def process(self, input: T) -> R:
        """Process input of type T to output of type R."""
        result = await self._process_implementation(input)
        return self._validate_result(result)
```

### Error Chain

```python
from pepperpy.core.exceptions import (
    CoreError,
    ValidationError,
    ProcessingError
)

async def process_with_error_chain():
    try:
        data = await validate_input()
    except ValidationError as e:
        raise CoreError("Input validation failed") from e
    
    try:
        result = await process_data(data)
    except ProcessingError as e:
        raise CoreError("Processing failed") from e
    
    return result
``` 