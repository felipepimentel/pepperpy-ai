# PepperPy Applications Module

This module provides high-level application templates for various AI tasks, simplifying the development of AI applications.

## Overview

PepperPy applications follow a common architecture and provide consistent interfaces for different types of data and content processing. Each application type is specialized for a specific domain, but they all share a common base class and interface.

## Application Types

- **BaseApp**: Base class for all PepperPy applications
- **TextApp**: Application for text processing (summarization, translation, etc.)
- **DataApp**: Application for structured data processing (analysis, transformation, etc.)
- **ContentApp**: Application for content generation (articles, blog posts, etc.)
- **MediaApp**: Application for media processing (images, audio, video)
- **RAGApp**: Application for Retrieval Augmented Generation
- **AssistantApp**: Application for AI assistants

## Module Structure

- `core.py`: Core functionality and base classes
- `public.py`: Public API for the module
- `text.py`: Text processing application
- `data.py`: Data processing application
- `content.py`: Content generation application
- `media.py`: Media processing application
- `rag.py`: RAG application
- `assistant.py`: Assistant application

## Usage Example

```python
from pepperpy.apps import TextApp

# Create a text processing application
app = TextApp("my_text_app")

# Configure the application
app.configure(
    operations=["summarize", "translate"],
    target_language="pt-br",
    max_length=200
)

# Process text
result = await app.process("Text to process")

# Access the result
print(result.text)
```

## Creating Custom Applications

You can create custom applications by extending the `BaseApp` class:

```python
from pepperpy.apps import BaseApp

class MyCustomApp(BaseApp):
    """Custom application for specific tasks."""
    
    async def process(self, input_data):
        """Process input data."""
        # Custom processing logic
        return result
``` 