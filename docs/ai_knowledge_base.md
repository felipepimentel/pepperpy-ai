# Pepperpy AI Knowledge Base

## Project Overview

Pepperpy is a sophisticated Python library designed for building AI-powered research assistants. The project provides a flexible and powerful framework for creating, managing, and deploying AI agents with a focus on research capabilities.

## Core Architecture

### System Components

1. **Core System (`pepperpy/core/`)**
   - Base abstractions and foundational classes
   - Event management system
   - Error handling framework
   - Configuration management
   - Type system enforcement

2. **Agent System (`pepperpy/agents/`)**
   ```python
   class BaseAgent:
       """Base class for all agents"""
       async def process(self, input: str) -> str:
           pass

   class ResearchAgent(BaseAgent):
       """Specialized agent for research tasks"""
       async def research(self, topic: str) -> ResearchResult:
           pass
   ```

3. **Provider System (`pepperpy/providers/`)**
   - Standardized interfaces for AI services
   - Provider registration and discovery
   - Resource lifecycle management
   - Error handling and recovery

4. **Hub System (`pepperpy/hub/`)**
   - Asset management (prompts, agents, workflows)
   - Hot-reloading capability
   - Version control integration
   - Asset distribution

### Key Subsystems

1. **Capabilities (`pepperpy/capabilities/`)**
   ```python
   from enum import Enum
   
   class ErrorType(Enum):
       LEARNING = "learning"
       PLANNING = "planning"
   
   class CapabilityError(Exception):
       def __init__(self, type: ErrorType, message: str):
           self.type = type
           self.message = message
   ```

2. **Memory Management (`pepperpy/memory/`)**
   - Conversation history tracking
   - State persistence
   - Context management
   - Cache optimization

3. **Search System (`pepperpy/search/`)**
   - Vector-based search
   - Semantic matching
   - Result ranking
   - Query optimization

## Technical Standards

### Code Style
- Python 3.12+ compatibility
- Type hints required
- Google-style docstrings
- Black code formatting
- Ruff linting rules

### Error Handling
```python
try:
    # Implementation
    result = await process_data()
except Exception as e:
    raise CapabilityError(ErrorType.PROCESSING, str(e))
```

### Type System
```python
from typing import TypeVar, Generic, Protocol

T = TypeVar('T')

class DataProvider(Protocol, Generic[T]):
    async def get(self) -> T: ...
    async def put(self, data: T) -> None: ...
```

## Provider Integration

### Supported Providers
1. **LLM Providers**
   - OpenAI
   - Google AI
   - Anthropic
   - Custom providers

2. **Vector Stores**
   - FAISS
   - Qdrant
   - Custom implementations

3. **Embedding Providers**
   - SentenceTransformers
   - OpenAI Embeddings
   - Custom models

### Provider Configuration
```python
provider_config = {
    "type": "openai",
    "parameters": {
        "model": "gpt-4",
        "temperature": 0.7
    },
    "metadata": {
        "version": "1.0",
        "capabilities": ["chat", "completion"]
    }
}
```

## Agent System

### Agent Types
1. **Research Agent**
   - Topic analysis
   - Source gathering
   - Information synthesis
   - Citation management

2. **Chat Agent**
   - Conversation management
   - Context tracking
   - Response generation
   - Memory utilization

3. **RAG Agent**
   - Document retrieval
   - Context augmentation
   - Knowledge integration
   - Source verification

### Agent Configuration
```python
agent_config = {
    "name": "research_assistant",
    "description": "AI-powered research assistant",
    "providers": {
        "llm": provider_config,
        "vector_store": provider_config,
        "embedding": provider_config
    },
    "capabilities": ["research", "chat", "rag"],
    "parameters": {
        "max_context": 4096,
        "response_format": "markdown"
    }
}
```

## Best Practices

### Development Guidelines
1. **Code Organization**
   - Modular architecture
   - Clear separation of concerns
   - Interface-based design
   - Comprehensive testing

2. **Error Management**
   - Specific error types
   - Contextual error messages
   - Clean error recovery
   - Proper resource cleanup

3. **Performance Optimization**
   - Async operations
   - Resource pooling
   - Cache utilization
   - Memory management

### Security Considerations
1. **API Security**
   - Key management
   - Rate limiting
   - Request validation
   - Response sanitization

2. **Data Protection**
   - Encryption at rest
   - Secure transmission
   - Access control
   - Audit logging

## Usage Patterns

### Basic Implementation
```python
from pepperpy import Pepperpy

async def main():
    # Initialize with defaults
    pepper = await Pepperpy.create()
    
    # Simple question
    result = await pepper.ask("What is AI?")
    print(result)
    
    # Research task
    research = await pepper.research("Impact of AI")
    print(research.summary)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Advanced Implementation
```python
async def advanced_research():
    config = {
        "name": "advanced_researcher",
        "providers": {
            "llm": {"type": "openai", "model": "gpt-4"},
            "vector_store": {"type": "faiss"},
            "embedding": {"type": "sentence_transformers"}
        },
        "capabilities": ["research", "rag"]
    }
    
    pepper = await Pepperpy.create(config)
    result = await pepper.research(
        topic="AI Ethics",
        depth="academic",
        sources=["papers", "journals"],
        max_results=10
    )
    
    return result.full_report
```

## System Requirements

### Technical Requirements
- Python 3.12+
- Poetry for dependency management
- Async/await support
- Modern AI provider APIs

### Dependencies
```toml
[tool.poetry.dependencies]
python = ">=3.12,<4.0"
openai = "^1.61.1"
pydantic = "^2.10.6"
structlog = "^25.1.0"
asyncpg = "^0.30.0"
redis = "^5.2.1"
```

## Testing Guidelines

### Test Categories
1. **Unit Tests**
   - Component isolation
   - Mock dependencies
   - Edge cases
   - Error scenarios

2. **Integration Tests**
   - Provider integration
   - System workflows
   - End-to-end scenarios
   - Performance metrics

3. **Type Tests**
   - Static type checking
   - Generic validation
   - Protocol compliance
   - Type safety

### Test Implementation
```python
import pytest
from pepperpy import Pepperpy

@pytest.mark.asyncio
async def test_research_capability():
    pepper = await Pepperpy.create()
    result = await pepper.research("Test Topic")
    assert result.summary is not None
    assert len(result.sources) > 0
```

## Monitoring and Observability

### Logging System
```python
from pepperpy.monitoring import logger

class StructuredLogger:
    """Structured logger with context."""
    def __init__(self):
        self._logger = logger
        self._context = {}
    
    def bind(self, **context):
        """Create new logger with bound context."""
        new_logger = StructuredLogger()
        new_logger._context = {**self._context, **context}
        return new_logger

# Usage example
logger = StructuredLogger()
logger.info("Operation started", 
    operation_id=123,
    user="admin"
)
```

### Metrics System
```python
from pepperpy.monitoring.metrics import Metrics

class MetricsCollector:
    def __init__(self):
        self.metrics = {
            "queries": {"total": 0, "errors": 0},
            "latency": {"sum": 0, "count": 0},
            "tokens": {"used": 0, "cost": 0.0}
        }
    
    async def record_operation(self, operation_type: str, duration_ms: float):
        """Record operation metrics."""
        self.metrics["queries"]["total"] += 1
        self.metrics["latency"]["sum"] += duration_ms
        self.metrics["latency"]["count"] += 1
```

### Tracing System
```python
from pepperpy.monitoring.tracing import TracingManager

class Tracer:
    def __init__(self):
        self._enabled = True
        self._current_span = None
    
    @contextmanager
    def start_span(self, name: str, **attributes):
        """Start a new trace span."""
        span = {"name": name, "attributes": attributes}
        old_span = self._current_span
        self._current_span = span
        try:
            yield span
        finally:
            self._current_span = old_span
```

## Event System

### Event Types
```python
from enum import Enum

class EventType(str, Enum):
    # System events
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    
    # Provider events
    PROVIDER_REGISTERED = "provider_registered"
    PROVIDER_ERROR = "provider_error"
    
    # Agent events
    AGENT_CREATED = "agent_created"
    AGENT_ERROR = "agent_error"
    
    # Task events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
```

### Event Bus
```python
class EventBus:
    def __init__(self):
        self._handlers = {}
        self._filters = {}
        self._queue = asyncio.Queue()
        self._running = False
    
    async def publish(self, event: Event):
        """Publish event to all subscribers."""
        await self._queue.put(event)
    
    async def subscribe(self, event_type: EventType, handler: EventHandler):
        """Subscribe to events."""
        if event_type not in self._handlers:
            self._handlers[event_type] = set()
        self._handlers[event_type].add(handler)
```

## Lifecycle Management

### Component States
```python
class ComponentState(Enum):
    UNREGISTERED = auto()
    REGISTERED = auto()
    INITIALIZING = auto()
    INITIALIZED = auto()
    RUNNING = auto()
    STOPPED = auto()
    ERROR = auto()
```

### Lifecycle Manager
```python
class LifecycleManager:
    def __init__(self):
        self._components = {}
        self._states = {}
        self._dependencies = defaultdict(set)
    
    async def initialize(self, component_id: UUID) -> None:
        """Initialize a component."""
        try:
            component = self._components[component_id]
            await self._update_state(component_id, ComponentState.INITIALIZING)
            await component.initialize()
            await self._update_state(component_id, ComponentState.INITIALIZED)
        except Exception as e:
            await self._update_state(component_id, ComponentState.ERROR)
            raise LifecycleError(f"Initialization failed: {e}")
```

## Error Handling

### Error Categories
```python
class ErrorCategory(str, Enum):
    SYSTEM = "system"
    VALIDATION = "validation"
    RESOURCE = "resource"
    RUNTIME = "runtime"
    SECURITY = "security"
    NETWORK = "network"
    PLANNING = "planning"
    TOOLS = "tools"
    REASONING = "reasoning"
    LEARNING = "learning"
```

### Error Management
```python
class ErrorManager:
    def __init__(self):
        self._handlers = {}
        self._metrics = MetricsCollector()
    
    async def handle_error(self, error: Exception, context: dict):
        """Handle system errors with proper logging and metrics."""
        category = self._categorize_error(error)
        await self._metrics.increment_error(category)
        
        if category in self._handlers:
            await self._handlers[category](error, context)
        
        logger.error("Error occurred",
            error_type=type(error).__name__,
            error_msg=str(error),
            **context
        )
```

## Registry System

### Component Registry
```python
class Registry(Generic[T]):
    def __init__(self, name: str, event_bus: EventBus = None):
        self._name = name
        self._items = {}
        self._event_bus = event_bus
        self._lock = asyncio.Lock()
    
    async def register(self, component: T, metadata: dict) -> None:
        """Register a component with metadata."""
        async with self._lock:
            component_id = uuid4()
            self._items[component_id] = {
                "component": component,
                "metadata": metadata,
                "registered_at": datetime.now()
            }
            
            if self._event_bus:
                await self._event_bus.publish(Event(
                    type=EventType.COMPONENT_REGISTERED,
                    component_id=component_id,
                    metadata=metadata
                ))
```

## Best Practices

### Monitoring Best Practices
1. **Structured Logging**
   - Always use structured logging with context
   - Include relevant metadata
   - Use appropriate log levels
   - Add trace IDs for correlation

2. **Metrics Collection**
   - Define clear metric names
   - Use appropriate metric types
   - Add relevant labels
   - Set up proper aggregation

3. **Tracing Implementation**
   - Create meaningful spans
   - Add relevant attributes
   - Properly manage context
   - Handle nested spans

### Error Handling Best Practices
1. **Error Categories**
   - Properly categorize errors
   - Use specific error types
   - Include context information
   - Implement recovery strategies

2. **Error Recovery**
   - Implement retry mechanisms
   - Handle transient failures
   - Clean up resources
   - Maintain system state

### Component Management
1. **Lifecycle**
   - Proper initialization
   - Resource cleanup
   - State management
   - Dependency handling

2. **Registration**
   - Unique identification
   - Metadata management
   - Version control
   - Dependency tracking

## System Health

### Health Checks
```python
class HealthChecker:
    async def check_health(self) -> dict:
        """Perform system health check."""
        return {
            "status": "healthy",
            "components": {
                "database": await self._check_database(),
                "cache": await self._check_cache(),
                "providers": await self._check_providers()
            },
            "metrics": {
                "error_rate": await self._get_error_rate(),
                "response_time": await self._get_response_time()
            }
        }
```

### Performance Monitoring
```python
class PerformanceMonitor:
    async def collect_metrics(self) -> dict:
        """Collect system performance metrics."""
        return {
            "memory_usage": self._get_memory_usage(),
            "cpu_usage": self._get_cpu_usage(),
            "request_rate": self._get_request_rate(),
            "error_rate": self._get_error_rate(),
            "response_time": self._get_response_time()
        }
```

## Future Considerations

### Planned Features
1. **Enhanced Capabilities**
   - Multi-agent collaboration
   - Advanced reasoning
   - Custom provider support
   - Workflow automation

2. **System Improvements**
   - Performance optimization
   - Enhanced security
   - Better error handling
   - Extended provider support

3. **Developer Experience**
   - Improved documentation
   - More examples
   - Better debugging tools
   - Enhanced testing support 