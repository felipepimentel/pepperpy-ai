---
type: "guidelines"
scope: "Pepperpy Project"
version: "1.0"
created-at: "2024-03-19"
---

# Dependency Management Guidelines

## Overview

This document outlines the guidelines and best practices for managing dependencies in the Pepperpy project. Following these guidelines ensures maintainable, scalable, and performant code.

## Core Principles

1. **Dependency Inversion**
   - Depend on abstractions, not implementations
   - Use interfaces defined in `pepperpy.interfaces`
   - Implement new functionality behind appropriate interfaces

2. **Dependency Injection**
   - Use constructor injection for required dependencies
   - Use setter injection for optional dependencies
   - Configure dependencies through the factory system

3. **Lifecycle Management**
   - Register components with the lifecycle manager
   - Specify clear dependency relationships
   - Allow parallel initialization where possible

## Project Structure

### Interface Layer
- Located in `pepperpy.interfaces`
- Defines core abstractions and protocols
- No implementation details or concrete classes

### Provider Layer
- Implements provider interfaces
- Self-contained implementations
- Minimal cross-provider dependencies

### Agent Layer
- Uses dependency injection for providers
- Configurable through capabilities
- Clear separation of concerns

## Best Practices

1. **Interface Design**
   ```python
   from typing import Protocol
   
   class MyInterface(Protocol):
       async def operation(self) -> None:
           """Define clear method signatures."""
           raise NotImplementedError
   ```

2. **Implementation**
   ```python
   from ...interfaces import MyInterface
   
   class MyImplementation(MyInterface):
       def __init__(self, config: Dict[str, Any]):
           self.config = config
   
       async def operation(self) -> None:
           # Implementation here
           pass
   ```

3. **Dependency Injection**
   ```python
   class MyComponent:
       def __init__(
           self,
           required: RequiredDependency,
           optional: Optional[OptionalDependency] = None
       ):
           self.required = required
           self.optional = optional
   ```

4. **Factory Usage**
   ```python
   factory = (
       AgentFactory()
       .with_llm(llm_provider)
       .with_vector_store(vector_store)
       .with_embeddings(embeddings)
   )
   agent = await factory.create("agent_type", capabilities, config)
   ```

## Common Patterns

### Provider Registration
```python
@BaseLLMProvider.register("my_provider")
class MyProvider(BaseLLMProvider):
    """Register providers using the decorator pattern."""
```

### Lifecycle Management
```python
lifecycle = ComponentLifecycleManager()
lifecycle.register("component", instance, dependencies=["dep1", "dep2"])
await lifecycle.initialize()  # Parallel initialization
```

### Capability Configuration
```python
capabilities = {
    "vector_store": {
        "enabled": True,
        "config": {...}
    },
    "embeddings": {
        "enabled": True,
        "config": {...}
    }
}
```

## Anti-patterns to Avoid

1. **Direct Imports of Implementations**
   ```python
   # Bad
   from ...providers.llm.specific import SpecificProvider
   
   # Good
   from ...interfaces import LLMProvider
   ```

2. **Hidden Dependencies**
   ```python
   # Bad
   class MyComponent:
       def __init__(self):
           self.hidden = SomeImplementation()
   
   # Good
   class MyComponent:
       def __init__(self, dependency: SomeInterface):
           self.dependency = dependency
   ```

3. **Circular Dependencies**
   ```python
   # Bad
   class A:
       def __init__(self, b: 'B'): pass
   
   class B:
       def __init__(self, a: 'A'): pass
   
   # Good: Use interfaces and composition
   ```

## Testing

1. **Interface Testing**
   - Test against interface definitions
   - Use protocol validation
   - Create mock implementations

2. **Dependency Injection Testing**
   ```python
   def test_component():
       mock_dep = MockDependency()
       component = MyComponent(mock_dep)
       assert component.dependency is mock_dep
   ```

3. **Lifecycle Testing**
   ```python
   async def test_lifecycle():
       lifecycle = ComponentLifecycleManager()
       mock_component = MockComponent()
       lifecycle.register("test", mock_component)
       await lifecycle.initialize()
       assert mock_component.is_initialized
   ```

## Migration Guide

1. **Identify Dependencies**
   - Review import statements
   - Document component relationships
   - Create dependency graph

2. **Create Interfaces**
   - Extract interface definitions
   - Move to `interfaces` module
   - Update implementations

3. **Implement Injection**
   - Convert to constructor injection
   - Update factory methods
   - Add lifecycle management

4. **Update Tests**
   - Convert to interface-based testing
   - Add dependency injection tests
   - Verify lifecycle management

## Performance Considerations

1. **Initialization**
   - Use parallel initialization
   - Minimize startup dependencies
   - Cache expensive operations

2. **Runtime**
   - Lazy load optional components
   - Use dependency proxies
   - Implement proper cleanup

3. **Memory**
   - Clear references in cleanup
   - Use weak references
   - Implement proper resource management 