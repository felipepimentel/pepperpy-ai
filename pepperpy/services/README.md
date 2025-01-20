# Services Module

This module provides service interfaces and implementations for Pepperpy's REST and WebSocket APIs.

## Overview

The services module contains:
- Base service protocols (`RESTService`, `WebSocketService`)
- Data service implementations
- Learning service implementations

## Structure

```
services/
├── base.py        # Base service protocols and error types
├── data.py        # Data service implementations
├── learning.py    # Learning service implementations
└── __init__.py    # Module exports
```

## Usage

### REST Services

```python
from pepperpy.services import DataRESTService, LearningRESTService

# Initialize services
data_service = DataRESTService(data_manager)
learning_service = LearningRESTService(learning_manager)

# Handle requests
result = await data_service.handle_request(
    method="POST",
    path="/ingest",
    data={"content": "..."},
    headers={"Content-Type": "application/json"}
)
```

### WebSocket Services

```python
from pepperpy.services import DataWebSocketService, LearningWebSocketService

# Initialize services
data_service = DataWebSocketService(data_manager)
learning_service = LearningWebSocketService(learning_manager)

# Handle messages
result = await data_service.handle_message(
    message={"action": "ingest", "data": {"content": "..."}},
    context={"session_id": "..."}
)
```

## Error Handling

All services use the `ServiceError` class for error handling:

```python
from pepperpy.services import ServiceError

try:
    result = await service.handle_request(...)
except ServiceError as e:
    logger.error(f"Service error: {e}")
``` 