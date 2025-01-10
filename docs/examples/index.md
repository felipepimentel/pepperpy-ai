# Examples

This section provides practical examples of using PepperPy AI in various scenarios.

## Basic Examples

### Simple Chat Interaction

```python
from pepperpy_ai.client import PepperPyAI
from pepperpy_ai.config import Config

async def chat_example():
    config = Config(provider="openai")
    client = PepperPyAI(config)
    
    response = await client.chat("Tell me about Python programming.")
    print(response)
```

### Text Completion

```python
from pepperpy_ai.client import PepperPyAI
from pepperpy_ai.config import Config

async def completion_example():
    config = Config(provider="anthropic")
    client = PepperPyAI(config)
    
    response = await client.complete("Python is a")
    print(response)
```

## Advanced Use Cases

### Custom Agent Configuration

```python
from pepperpy_ai.client import PepperPyAI
from pepperpy_ai.config import Config
from pepperpy_ai.agents import ChatAgent

async def custom_agent_example():
    config = Config()
    agent = ChatAgent(
        temperature=0.7,
        max_tokens=100
    )
    client = PepperPyAI(config, agent=agent)
    
    response = await client.chat("Explain quantum computing.")
    print(response)
```

### Using Caching

```python
from pepperpy_ai.client import PepperPyAI
from pepperpy_ai.config import Config
from pepperpy_ai.cache import Cache

async def cached_example():
    config = Config(cache_enabled=True)
    client = PepperPyAI(config)
    
    # First call will hit the API
    response1 = await client.chat("What is AI?")
    
    # Second call will use cached result
    response2 = await client.chat("What is AI?")
```

## Integration Examples

### Web Application Integration

```python
from fastapi import FastAPI
from pepperpy_ai.client import PepperPyAI
from pepperpy_ai.config import Config

app = FastAPI()
config = Config()
ai_client = PepperPyAI(config)

@app.post("/chat")
async def chat_endpoint(message: str):
    response = await ai_client.chat(message)
    return {"response": response}
```

### Error Handling

```python
from pepperpy_ai.client import PepperPyAI
from pepperpy_ai.config import Config
from pepperpy_ai.exceptions import PepperPyError

async def error_handling_example():
    config = Config()
    client = PepperPyAI(config)
    
    try:
        response = await client.chat("Your message here")
    except PepperPyError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

## Best Practices

### Environment Variables

```bash
# .env file
PEPPERPY_PROVIDER=openai
PEPPERPY_API_KEY=your-api-key
PEPPERPY_CACHE_ENABLED=true
```

```python
from pepperpy_ai.client import PepperPyAI
from pepperpy_ai.config import Config
from dotenv import load_dotenv

load_dotenv()
config = Config()  # Will load from environment variables
client = PepperPyAI(config)
```

### Async Context Manager

```python
from pepperpy_ai.client import PepperPyAI
from pepperpy_ai.config import Config

async def context_manager_example():
    config = Config()
    async with PepperPyAI(config) as client:
        response = await client.chat("Hello!")
        print(response)
```

For more detailed API documentation, see the [API Reference](../api_reference/index.md) section. 