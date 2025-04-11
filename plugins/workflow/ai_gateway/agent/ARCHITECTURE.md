# Agent System Architecture

This document provides an overview of the Agent System architecture, including core components, interfaces, and extension patterns.

## System Overview

The Agent System is a modular framework for creating, managing, and orchestrating AI agents with different capabilities. The architecture follows these key principles:

1. **Modular Design**: Each component has a single responsibility
2. **Interface-Driven**: Components interact through well-defined interfaces
3. **Extensible**: Easy to extend with new agent types and capabilities
4. **Async-First**: All operations are asynchronous for scalability

## Core Components

### 1. BaseAgent

The `BaseAgent` abstract class provides the foundation for all agent implementations. It defines:

- Common properties (ID, name, capabilities)
- Lifecycle methods (initialize, shutdown)
- Abstract execution method that must be implemented by subclasses

```python
class BaseAgent(ABC):
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        role: AgentRole,
        capabilities: list[AgentCapability],
        config: dict[str, Any],
    ):
        # Initialize agent properties
        
    @abstractmethod
    async def execute(self, task: Task, context: AgentContext) -> Any:
        """Execute a task."""
        pass
```

### 2. AgentContext

The `AgentContext` class provides a shared context for agents, including:

- Session-specific data storage
- Shared memory for cross-agent communication
- History tracking
- Tool registration and access

```python
@dataclass
class AgentContext:
    session_id: str
    user_id: str | None = None
    # Other properties...
    
    async def get(self, key: str) -> Any | None:
        """Get a value from context."""
        
    async def set(self, key: str, value: Any) -> None:
        """Set a value in context."""
```

### 3. Task

The `Task` class represents a unit of work for an agent to execute:

- Task metadata (ID, objective, status)
- Input parameters
- Result storage
- Timing information

```python
@dataclass
class Task:
    id: str
    objective: str
    parameters: dict[str, Any]
    status: TaskStatus
    # Other properties...
```

### 4. AgentRegistry

The `AgentRegistry` class provides a central registry for managing agent instances:

- Agent creation and initialization
- Agent retrieval by ID or capability
- Agent lifecycle management
- Agent type registration

```python
class AgentRegistry:
    def __init__(self):
        """Initialize the agent registry."""
        self.agents: dict[str, BaseAgent] = {}
        self.agent_types: dict[str, type[BaseAgent]] = {...}
        
    async def create_agent(
        self, agent_id: str, agent_type: str, config: dict[str, Any]
    ) -> BaseAgent | None:
        """Create a new agent."""
        
    async def get_agent(self, agent_id: str) -> BaseAgent | None:
        """Get an agent by ID."""
```

### 5. Memory System

The memory system provides different storage mechanisms for agent state:

- `BaseMemory`: Abstract memory interface
- `SimpleMemory`: Basic in-memory storage
- `LRUMemory`: Memory with least recently used eviction
- `ConversationMemory`: For storing conversation history
- `HierarchicalMemory`: Multi-tier memory with different retention policies

```python
class BaseMemory(ABC):
    @abstractmethod
    async def add(self, key: Key, value: Value) -> None:
        """Add an item to memory."""
        
    @abstractmethod
    async def get(self, key: Key) -> Optional[Value]:
        """Retrieve an item from memory."""
```

## Specialized Agent Types

The system includes several specialized agent types for different use cases:

### 1. AssistantAgent

General-purpose conversational agent for answering questions and chat interactions.

```python
class AssistantAgent(BaseAgent):
    def __init__(
        self,
        id: str,
        name: str,
        model_id: str,
        description: str = "",
        system_prompt: str = "You are a helpful assistant.",
        max_history_length: int = 10,
    ):
        # Initialize assistant-specific properties
```

### 2. RAGAgent

Retrieval-augmented generation agent for knowledge-based tasks.

```python
class RAGAgent(BaseAgent):
    def __init__(
        self,
        id: str,
        name: str,
        model_id: str,
        vector_store_id: str,
        description: str = "",
        max_documents: int = 5,
    ):
        # Initialize RAG-specific properties
```

### 3. ToolAgent

Agent that can use external tools and functions.

```python
class ToolAgent(BaseAgent):
    def __init__(
        self,
        id: str,
        name: str,
        model_id: str,
        description: str = "",
        available_tools: list[dict[str, Any]] | None = None,
    ):
        # Initialize tool-specific properties
```

### 4. PlanningAgent

Agent that can create and execute plans for complex tasks.

```python
class PlanningAgent(BaseAgent):
    def __init__(
        self,
        id: str,
        name: str,
        model_id: str,
        description: str = "",
    ):
        # Initialize planning-specific properties
```

### 5. Orchestrator

Agent that coordinates workflows across multiple agents.

```python
class Orchestrator(BaseAgent):
    def __init__(
        self,
        id: str,
        name: str,
        description: str = "",
    ):
        # Initialize orchestrator-specific properties
```

## Extension Patterns

### Creating a Custom Agent

To create a custom agent type, extend the `BaseAgent` class:

```python
class MyCustomAgent(BaseAgent):
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        custom_param: str,
    ):
        role = AgentRole.SPECIALIST
        capabilities = [AgentCapability.CUSTOM_CAPABILITY]
        config = {"custom_param": custom_param}
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            role=role,
            capabilities=capabilities,
            config=config,
        )
        
        self.custom_param = custom_param
        
    async def execute(self, task: Task, context: AgentContext) -> Any:
        """Execute a task."""
        # Custom implementation
        return result
```

### Registering a Custom Agent Type

Register your custom agent type with the registry:

```python
registry = AgentRegistry()
await registry.register_agent_type("custom", MyCustomAgent)

# Create an instance
custom_agent = await registry.create_agent(
    "custom-1",
    "custom",
    {
        "name": "My Custom Agent",
        "description": "Custom agent implementation",
        "custom_param": "value",
    },
)
```

### Creating a Custom Memory Implementation

Extend the `BaseMemory` class to create a custom memory implementation:

```python
class MyCustomMemory(BaseMemory):
    def __init__(self, max_size: int = 1000):
        super().__init__(max_size)
        # Initialize custom memory
        
    async def add(self, key: Key, value: Value) -> None:
        """Add an item to memory."""
        # Custom implementation
        
    async def get(self, key: Key) -> Optional[Value]:
        """Retrieve an item from memory."""
        # Custom implementation
```

## Workflow Patterns

### Single Agent Execution

Execute a task with a single agent:

```python
# Get an agent
agent = await registry.get_agent("agent-id")

# Create context
context = AgentContext(session_id="session-id")

# Create task
task = Task(
    objective="Task objective",
    parameters={"param": "value"},
)

# Execute task
await agent.execute(task, context)

# Check result
if task.status == TaskStatus.COMPLETED:
    result = task.result
```

### Multi-Agent Orchestration

Orchestrate multiple agents to solve a complex task:

```python
# Get orchestrator
orchestrator = await registry.get_agent("orchestrator-id")

# Create context with agents
context = AgentContext(session_id="session-id")

# Add agents to context
for agent_id in ["agent-1", "agent-2", "agent-3"]:
    agent = await registry.get_agent(agent_id)
    await context.set(f"agent:{agent_id}", agent)

# Create task
task = Task(
    objective="Execute multi-agent workflow",
    parameters={
        "workflow_name": "complex_workflow",
        "workflow_params": {...},
    },
)

# Execute workflow
await orchestrator.execute(task, context)
```

## Best Practices

1. **Agent Design**
   - Keep agents focused on a single capability
   - Use composition over inheritance for complex agents
   - Properly handle errors and task status updates

2. **Task Execution**
   - Design tasks with clear objectives and parameters
   - Include all necessary context in the task
   - Handle task status properly (PROCESSING, COMPLETED, FAILED)

3. **Context Management**
   - Use context for sharing state between agents
   - Don't store large data in context; use external storage
   - Clean up context when no longer needed

4. **Memory Management**
   - Choose the appropriate memory implementation for your needs
   - Be careful with memory size limits
   - Use hierarchical memory for complex agents 