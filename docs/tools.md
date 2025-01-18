# Tools

Tools are reusable components that provide specific functionality to agents. They follow a common interface defined by the `Tool` protocol and can be easily extended.

## Available Tools

### EmbeddingsTool

The `EmbeddingsTool` generates vector embeddings from text input using a configured provider.

```python
from pepperpy.tools import EmbeddingsTool
from pepperpy import Provider

# Initialize with a provider
provider = Provider(...)
embeddings = EmbeddingsTool("embeddings", provider)

# Initialize the tool
await embeddings.initialize()

# Generate embeddings
vectors = await embeddings.execute(
    texts=["Hello world", "How are you?"],
    model="text-embedding-ada-002"
)

# Cleanup when done
await embeddings.cleanup()
```

## Creating Custom Tools

To create a custom tool:

1. Inherit from `BaseTool`
2. Implement required methods:
   - `_setup()`: Initialize resources
   - `_teardown()`: Cleanup resources
   - `execute()`: Main tool logic

Example:

```python
from pepperpy.tools import BaseTool

class CustomTool(BaseTool):
    async def _setup(self) -> None:
        # Initialize resources
        pass

    async def _teardown(self) -> None:
        # Cleanup resources
        pass

    async def execute(self, **kwargs: Any) -> Any:
        # Implement tool logic
        pass
``` 