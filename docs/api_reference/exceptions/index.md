# Error Handling

PepperPy AI provides a comprehensive error handling system with custom exceptions for different types of errors.

## Overview

The error handling system provides:
- Custom exception hierarchy
- Error context preservation
- Error recovery mechanisms
- Error reporting
- Error chaining

## Exception Hierarchy

### Base Exceptions

```python
from pepperpy_ai.exceptions import PepperpyError

class PepperpyError(Exception):
    """Base exception for all PepperPy errors."""
    
    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)
        self.cause = cause
```

### Specific Exceptions

```python
from pepperpy_ai.exceptions import (
    AIError,
    ConfigError,
    ProviderError,
    NetworkError,
    ValidationError
)

# AI operation errors
class AIError(PepperpyError):
    """AI operation error."""
    pass

# Configuration errors
class ConfigError(PepperpyError):
    """Configuration error."""
    pass

# Provider errors
class ProviderError(PepperpyError):
    """Provider error."""
    pass
```

## Error Handling Features

### Error Context

Preserve error context:

```python
from pepperpy_ai.exceptions import ErrorContext

class ErrorContext:
    """Error context information."""
    
    def __init__(self, operation: str, details: dict):
        self.operation = operation
        self.details = details
        self.timestamp = datetime.now()

# Using error context
try:
    result = await process_data()
except Exception as e:
    context = ErrorContext(
        operation="data_processing",
        details={"input": data, "stage": "processing"}
    )
    raise ProcessingError("Data processing failed", cause=e) from e
```

### Error Recovery

```python
from pepperpy_ai.exceptions import ErrorRecovery

class ErrorRecovery:
    """Error recovery mechanisms."""
    
    async def recover(self, error: PepperpyError) -> bool:
        """Attempt to recover from error."""
        if isinstance(error, NetworkError):
            return await self._handle_network_error(error)
        elif isinstance(error, ProviderError):
            return await self._handle_provider_error(error)
        return False
```

### Error Reporting

```python
from pepperpy_ai.exceptions import ErrorReporter

class ErrorReporter:
    """Error reporting system."""
    
    async def report(self, error: PepperpyError) -> None:
        """Report error to monitoring system."""
        await self._log_error(error)
        await self._notify_if_critical(error)
        await self._update_metrics(error)
```

## Best Practices

1. **Exception Handling**
   - Use specific exceptions
   - Preserve error context
   - Chain related errors

2. **Error Recovery**
   - Implement recovery strategies
   - Handle transient failures
   - Provide fallback options

3. **Error Reporting**
   - Log error details
   - Include context
   - Track error metrics

4. **Error Prevention**
   - Validate inputs
   - Check preconditions
   - Handle edge cases

## Examples

### Basic Error Handling

```python
from pepperpy_ai.exceptions import PepperpyError, AIError

async def process_with_error_handling():
    try:
        result = await process_data()
        return result
    except AIError as e:
        # Handle AI-specific errors
        logger.error(f"AI error: {e}")
        raise
    except PepperpyError as e:
        # Handle general errors
        logger.error(f"Processing error: {e}")
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error: {e}")
        raise PepperpyError("Unexpected error occurred", cause=e) from e
```

### Error Recovery Pattern

```python
from pepperpy_ai.exceptions import ErrorRecovery, RetryableError

async def retry_with_recovery():
    recovery = ErrorRecovery()
    retries = 3
    
    for attempt in range(retries):
        try:
            return await process_operation()
        except RetryableError as e:
            if await recovery.recover(e):
                continue
            if attempt == retries - 1:
                raise
```

### Error Context Chain

```python
from pepperpy_ai.exceptions import ErrorContextChain

async def process_with_context():
    context_chain = ErrorContextChain()
    
    try:
        with context_chain.add_context("validation"):
            data = await validate_input()
            
        with context_chain.add_context("processing"):
            result = await process_data(data)
            
        with context_chain.add_context("output"):
            return await format_output(result)
            
    except Exception as e:
        raise ProcessingError(
            f"Operation failed: {context_chain.current_operation}",
            context=context_chain.get_context(),
            cause=e
        ) from e
```

### Custom Error Types

```python
from pepperpy_ai.exceptions import PepperpyError

class ValidationError(PepperpyError):
    """Validation error with field information."""
    
    def __init__(self, message: str, field: str, value: Any):
        super().__init__(message)
        self.field = field
        self.value = value

class RateLimitError(PepperpyError):
    """Rate limit error with retry information."""
    
    def __init__(self, message: str, retry_after: int):
        super().__init__(message)
        self.retry_after = retry_after
``` 