# PepperPy Core Module

This module provides the core functionality for the PepperPy framework. It defines the fundamental abstractions, interfaces, and utilities that are used throughout the framework.

## Overview

The Core module is the foundation of the PepperPy framework. It provides common functionality that is used by all other modules, such as error handling, logging, configuration, and utility functions.

## Core Components

- **Errors**: Common error types used throughout the framework
- **Types**: Common type definitions and aliases
- **Interfaces**: Core interfaces and protocols
- **Utilities**: Common utility functions

## Module Structure

- `core.py`: Core functionality and error types
- `common/`: Common types and utilities
  - `types.py`: Common type definitions and aliases
  - `utils.py`: Common utility functions
- `interfaces.py`: Core interfaces and protocols
- `public.py`: Public API for the module

## Usage Example

```python
from pepperpy.core import get_logger, PepperPyError, JSON, Resource, ResourceType

# Create a logger
logger = get_logger("my_module")
logger.info("Hello, world!")

# Use utility functions
from pepperpy.core import generate_id, hash_string, load_json, save_json

resource_id = generate_id()
hashed_password = hash_string("password123")
data = load_json("config.json")
save_json(data, "config_backup.json")

# Use error types
try:
    # Do something
    pass
except Exception as e:
    raise PepperPyError("Something went wrong") from e

# Use resource types
metadata = Metadata(id=generate_id(), name="My Resource")
resource = Resource(
    type=ResourceType.FILE,
    metadata=metadata,
    content="Hello, world!",
    uri="file:///path/to/file.txt",
)

# Use interfaces
from pepperpy.core import Configurable, Initializable, Cleanable

class MyComponent(Configurable, Initializable, Cleanable):
    def configure(self, **kwargs):
        # Configure the component
        return self
    
    async def initialize(self):
        # Initialize the component
        pass
    
    async def cleanup(self):
        # Clean up resources
        pass
```

## Error Handling

The Core module provides a hierarchy of error types that can be used throughout the framework:

- `PepperPyError`: Base class for all PepperPy exceptions
  - `ConfigurationError`: Raised when there is an error in the configuration
  - `ValidationError`: Raised when validation fails
  - `ResourceNotFoundError`: Raised when a resource is not found
  - `AuthenticationError`: Raised when authentication fails
  - `AuthorizationError`: Raised when authorization fails
  - `TimeoutError`: Raised when an operation times out
  - `RateLimitError`: Raised when a rate limit is exceeded
  - `ServiceUnavailableError`: Raised when a service is unavailable

## Interfaces

The Core module provides a set of interfaces and protocols that can be used to define common behavior:

- `Configurable`: Protocol for objects that can be configured
- `Initializable`: Protocol for objects that can be initialized
- `Cleanable`: Protocol for objects that can be cleaned up
- `Serializable`: Protocol for objects that can be serialized
- `Provider`: Base class for all providers
- `ResourceProvider`: Base class for resource providers
- `Processor`: Base class for processors
- `Transformer`: Base class for transformers
- `Analyzer`: Base class for analyzers
- `Generator`: Base class for generators
- `Validator`: Base class for validators 