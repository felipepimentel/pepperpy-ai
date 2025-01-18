# Capabilities

Capabilities are reusable components that provide specific functionality to agents. They follow a common interface defined by the `Capability` protocol and can be easily extended.

## Available Capabilities

### ChatCapability

The `ChatCapability` handles conversational interactions using a configured provider.

```python
from pepperpy.capabilities import ChatCapability
from pepperpy import Provider

# Initialize with a provider
provider = Provider(...)
chat = ChatCapability("chat", provider)

# Initialize the capability
await chat.initialize()

# Execute chat task
response = await chat.execute(
    task="What is the weather like?",
    temperature=0.7,
    max_tokens=100
)

# Cleanup when done
await chat.cleanup()
```

## Creating Custom Capabilities

To create a custom capability:

1. Inherit from `BaseCapability`
2. Implement required methods:
   - `_setup()`: Initialize resources
   - `_teardown()`: Cleanup resources
   - `execute()`: Main capability logic

Example:

```python
from pepperpy.capabilities import BaseCapability

class CustomCapability(BaseCapability):
    async def _setup(self) -> None:
        # Initialize resources
        pass

    async def _teardown(self) -> None:
        # Cleanup resources
        pass

    async def execute(self, task: str, **kwargs: Any) -> Message:
        # Implement capability logic
        pass
``` 