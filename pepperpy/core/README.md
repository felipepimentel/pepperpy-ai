# PepperPy Core Module

The core module provides fundamental functionality for the PepperPy framework, including base classes, utilities, and the component metadata system.

## Component Metadata System

The component metadata system allows components to self-describe and be discovered by the Hub. This enables:

- **Component Discovery**: Automatically find and register components in modules
- **Component Registry**: Maintain a central registry of available components
- **Component Categorization**: Organize components by category and tags
- **Component Documentation**: Provide rich metadata about components

### Key Features

- **Decorator-based**: Simple `@component` decorator to add metadata to component classes
- **Categorization**: Components are organized by category (audio, image, text, etc.)
- **Tagging**: Components can be tagged for easier discovery
- **Registry**: Global registry for component lookup
- **Discovery**: Automatic discovery of components in modules

### Usage Example

```python
from pepperpy.core.base.common import BaseComponent
from pepperpy.core.metadata import ComponentCategory, component, register_component

@component(
    name="my_text_processor",
    description="A text processor that does something useful",
    category=ComponentCategory.TEXT,
    input=["text"],
    output=["text"],
    tags=["nlp", "processing"],
)
class MyTextProcessor(BaseComponent):
    def __init__(self, name="text_processor"):
        super().__init__(name=name)
        
    def process(self, text):
        # Process text
        return text

# Register the component
register_component(MyTextProcessor)
```

### Component Discovery

You can discover components in a module:

```python
from pepperpy.core.metadata import discover_components

# Discover components in the current module
components = discover_components(__name__)
```

### Component Lookup

You can look up components by name, category, or tag:

```python
from pepperpy.core.metadata import get_component, get_components_by_category, get_components_by_tag

# Get a component by name
text_processor = get_component("my_text_processor")

# Get components by category
text_components = get_components_by_category(ComponentCategory.TEXT)

# Get components by tag
nlp_components = get_components_by_tag("nlp")
```

### Component Metadata

You can access component metadata:

```python
from pepperpy.core.metadata import get_metadata

# Get metadata for a component
metadata = get_metadata(MyTextProcessor)
print(metadata.description)
print(metadata.category)
print(metadata.tags)

# Convert metadata to dictionary
metadata_dict = metadata.to_dict()
```

## Base Components

The core module also provides base classes for components:

- **BaseComponent**: The root class for all components
- **BaseProcessor**: Base class for processors
- **BaseModel**: Base class for models

## Utilities

The core module includes various utilities:

- **Configuration**: Utilities for component configuration
- **Logging**: Logging utilities
- **Error Handling**: Error handling utilities
- **Type Definitions**: Common type definitions

## Integration with Hub

The metadata system is designed to integrate with the PepperPy Hub, allowing:

- **Component Publishing**: Publish components to the Hub
- **Component Discovery**: Discover components from the Hub
- **Component Installation**: Install components from the Hub
- **Component Updates**: Update components from the Hub

## Examples

See the `examples` directory for more examples of using the core module. 