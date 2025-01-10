# Network Layer

PepperPy AI provides a robust network layer for handling API communications and data transfer.

## Overview

The network layer provides:
- HTTP client management
- Request handling
- Response processing
- Rate limiting
- Error handling

## Core Components

### HTTP Client

The main network client interface:

```python
from pepperpy_ai.network import HTTPClient
from pepperpy_ai.config import Config

async def client_example():
    config = Config()
    client = HTTPClient(config)
    
    # Make request
    response = await client.request(
        method="POST",
        url="https://api.example.com/v1/chat",
        json={"message": "Hello"}
    )
```

### Request Management

Handle different types of requests:

```python
from pepperpy_ai.network import RequestManager

async def request_example():
    manager = RequestManager(
        base_url="https://api.example.com",
        timeout=30,
        retries=3
    )
    
    # GET request
    data = await manager.get("/endpoint")
    
    # POST request with JSON
    result = await manager.post(
        "/endpoint",
        json={"key": "value"}
    )
    
    # Stream response
    async for chunk in manager.stream("/stream"):
        print(chunk)
```

## Configuration

Configure network behavior:

```python
from pepperpy_ai.network.config import NetworkConfig

config = NetworkConfig(
    timeout=30,
    max_retries=3,
    backoff_factor=1.5,
    rate_limit=100
)
```

## Advanced Features

### Rate Limiting

```python
from pepperpy_ai.network import RateLimiter

async def rate_limit_example():
    limiter = RateLimiter(
        requests_per_minute=60,
        burst_size=10
    )
    
    async with limiter:
        response = await client.request(...)
```

### Error Handling

```python
from pepperpy_ai.network import NetworkError, RetryHandler

async def error_handling_example():
    retry_handler = RetryHandler(
        max_retries=3,
        retry_codes=[500, 502, 503]
    )
    
    try:
        async with retry_handler:
            response = await client.request(...)
    except NetworkError as e:
        print(f"Network error: {e}")
```

### Request Middleware

```python
from pepperpy_ai.network import RequestMiddleware

async def middleware_example():
    middleware = RequestMiddleware()
    
    @middleware.before_request
    async def add_headers(request):
        request.headers["User-Agent"] = "PepperPy/1.0"
    
    @middleware.after_response
    async def process_response(response):
        if response.status == 429:
            await handle_rate_limit(response)
```

## Best Practices

1. **Request Management**
   - Use appropriate timeouts
   - Implement retries
   - Handle rate limits

2. **Error Handling**
   - Handle network errors
   - Implement backoff strategies
   - Log failures appropriately

3. **Performance**
   - Use connection pooling
   - Enable keepalive
   - Batch requests when possible

4. **Security**
   - Validate SSL certificates
   - Secure API keys
   - Sanitize request data

## Environment Variables

Configure network settings:

```bash
PEPPERPY_NETWORK_TIMEOUT=30
PEPPERPY_NETWORK_MAX_RETRIES=3
PEPPERPY_NETWORK_RATE_LIMIT=100
PEPPERPY_NETWORK_VERIFY_SSL=true
```

## Examples

### API Client

```python
from pepperpy_ai.network import APIClient

async def api_example():
    client = APIClient(
        base_url="https://api.example.com",
        api_key="your-api-key"
    )
    
    # Make authenticated request
    response = await client.get(
        "/endpoint",
        headers={"Custom-Header": "value"}
    )
    
    print("Status:", response.status)
    print("Data:", response.json())
```

### Streaming Client

```python
from pepperpy_ai.network import StreamingClient

async def streaming_example():
    client = StreamingClient()
    
    # Stream large response
    async for chunk in client.stream(
        "https://api.example.com/stream",
        chunk_size=1024
    ):
        process_chunk(chunk)
```

### WebSocket Client

```python
from pepperpy_ai.network import WebSocketClient

async def websocket_example():
    client = WebSocketClient(
        url="wss://api.example.com/ws"
    )
    
    async with client as ws:
        await ws.send({"type": "subscribe"})
        
        async for message in ws:
            print("Received:", message)
``` 