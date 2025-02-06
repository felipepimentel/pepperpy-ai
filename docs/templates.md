# Template System Documentation

The Pepperpy template system provides a flexible and extensible way to generate various types of content, including documentation, configuration files, and code. This document describes the template system's architecture, features, and usage.

## Overview

The template system is built around the following core components:

- `Template`: Base class for all templates
- `TemplateContext`: Context data for template rendering
- `TemplateMetadata`: Metadata for template identification and versioning
- `TemplateError`: Error handling for template operations

## Template Types

### Documentation Templates

The documentation template system supports multiple formats:

- **Markdown**: Standard markdown format with GitHub-style features
- **reStructuredText**: Python's preferred documentation format
- **HTML**: Responsive HTML with modern styling
- **AsciiDoc**: Popular technical documentation format

Example usage:

```python
from pepperpy.core.templates.base import TemplateContext, TemplateMetadata
from pepperpy.core.templates.docs import DocFormat, DocsTemplate

# Create template metadata
metadata = TemplateMetadata(
    name="Project Documentation",
    description="Documentation template for Python projects",
    version="1.0.0",
)

# Create template context
context = TemplateContext(
    template_id=metadata.id,
    data={
        "title": "My Project",
        "description": "Project description",
        "overview": "Project overview",
        "installation": "pip install my-project",
        "usage": "from my_project import main",
    }
)

# Create and use template
template = DocsTemplate(
    metadata,
    format=DocFormat.MARKDOWN,
    style_guide={"wrap": "no", "number": True},
)

# Generate documentation
await template.load()
if await template.validate(context):
    content = await template.render(context)
    with open("README.md", "w") as f:
        f.write(content)
```

### Configuration Templates

Configuration templates help generate configuration files in various formats:

- JSON with schema validation
- YAML with type checking
- INI with section support
- Environment files

Example usage:

```python
from pepperpy.core.templates.config import ConfigTemplate, ConfigFormat

template = ConfigTemplate(
    metadata,
    format=ConfigFormat.YAML,
    schema="config_schema.yaml",
)

await template.load()
if await template.validate(context):
    config = await template.render(context)
    await template.save("config.yaml")
```

### Code Templates

Code templates assist in generating boilerplate code:

- Python modules and packages
- Test files
- CLI applications
- API endpoints

Example usage:

```python
from pepperpy.core.templates.code import CodeTemplate, CodeType

template = CodeTemplate(
    metadata,
    code_type=CodeType.PYTHON_MODULE,
    style_guide="google",
)

await template.load()
if await template.validate(context):
    code = await template.render(context)
    await template.save("module.py")
```

## Features

### Template Validation

All templates support validation to ensure:

- Required fields are present
- Data types are correct
- Format-specific rules are followed
- Custom validation rules are satisfied

### Style Guide Support

Templates can apply style guides during rendering:

- Markdown formatting (wrapping, numbering)
- Code style (PEP 8, Google style)
- HTML prettification
- Custom formatting rules

### Performance Optimizations

The template system includes several optimizations:

- Template caching
- Lazy loading
- Compiled template reuse
- LRU cache for compilation

### Error Handling

Comprehensive error handling with:

- Detailed error messages
- Template identification
- Stack traces
- Recovery suggestions

## Best Practices

1. **Template Organization**
   - Keep templates in a dedicated directory
   - Use clear naming conventions
   - Version templates appropriately
   - Document template requirements

2. **Context Management**
   - Validate context data early
   - Use type hints for context data
   - Keep context data immutable
   - Document context schema

3. **Error Handling**
   - Always validate before rendering
   - Handle template errors gracefully
   - Provide helpful error messages
   - Log template operations

4. **Performance**
   - Reuse template instances
   - Cache compiled templates
   - Use async operations
   - Profile template rendering

## Future Enhancements

1. **Template Discovery**
   - Dynamic template loading
   - Plugin system
   - Template registry
   - Version management

2. **Additional Formats**
   - PDF output
   - Slide presentations
   - API documentation
   - Interactive notebooks

3. **Enhanced Features**
   - Template inheritance
   - Partial templates
   - Template composition
   - Custom renderers

4. **Integration**
   - CI/CD pipelines
   - Documentation tools
   - Code generators
   - Build systems 