# PepperPy AI Gateway Agent System

The Agent System is a modular framework for creating, managing, and orchestrating AI agents with different capabilities. It provides a flexible architecture for building complex multi-agent systems.

## Features

- **Modular Agent Architecture**: Create and extend different types of agents with specific capabilities
- **Agent Registry**: Central registry for managing agent instances
- **Agent Manager**: Persistent storage and lifecycle management for agents
- **Context Management**: Share context and data between agents in sessions
- **Task-based Execution**: Structured task execution with parameters and results
- **Memory Management**: Different memory implementations for agent state
- **Tool Integration**: Enable agents to use tools and external services
- **Orchestration**: Coordinate workflows across multiple agents

## Core Components

### 1. BaseAgent

Abstract class providing common agent functionality:

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

### 2. AgentRegistry

Central registry for agent instances:

```python
class AgentRegistry:
    async def create_agent(
        self, agent_id: str, agent_type: str, config: dict[str, Any]
    ) -> BaseAgent | None:
        """Create a new agent."""
        
    async def get_agent(self, agent_id: str) -> BaseAgent | None:
        """Get an agent by ID."""
        
    async def register_agent_type(
        self, type_name: str, agent_class: type[BaseAgent]
    ) -> None:
        """Register a new agent type."""
```

### 3. AgentManager

Manager for agent lifecycle and persistence:

```python
class AgentManager:
    def __init__(
        self,
        storage_dir: Optional[str] = None,
        memory_type: str = "hierarchical",
        auto_save: bool = True,
        save_interval: int = 300,
    ):
        """Initialize the agent manager."""
        
    async def create_agent(
        self, agent_id: str, agent_type: str, config: Dict[str, Any]
    ) -> Optional[BaseAgent]:
        """Create a new agent."""
        
    async def create_session(
        self, session_id: str, user_id: Optional[str] = None
    ) -> AgentContext:
        """Create a new agent session."""
        
    async def process_task(
        self, task: Task, session_id: str, agent_id: Optional[str] = None
    ) -> Task:
        """Process a task with an agent."""
```

### 4. Memory System

Provides different storage mechanisms for agent state:

```python
class BaseMemory(ABC):
    @abstractmethod
    async def add(self, key: Key, value: Value) -> None:
        """Add an item to memory."""
        
    @abstractmethod
    async def get(self, key: Key) -> Optional[Value]:
        """Retrieve an item from memory."""
```

## Agent Types

The system provides several specialized agent types:

- **AssistantAgent**: General-purpose conversational agent
- **RAGAgent**: Retrieval-augmented generation for knowledge-based tasks
- **ToolAgent**: Tool-using agent that can execute functions
- **PlanningAgent**: Creates and executes plans for complex tasks
- **Orchestrator**: Coordinates multi-agent workflows

## Basic Usage

### Using the Agent Registry

```python
import asyncio
from plugins.workflow.ai_gateway.agent.registry import AgentRegistry
from plugins.workflow.ai_gateway.agent.base import AgentContext, Task

async def main():
    # Create and initialize the agent registry
    registry = AgentRegistry()
    await registry.initialize({})
    
    # Create an agent
    assistant = await registry.create_agent(
        "assistant-1",
        "assistant",
        {
            "name": "General Assistant",
            "model_id": "gpt-4",
            "system_prompt": "You are a helpful assistant."
        }
    )
    
    # Create context
    context = AgentContext(session_id="example-session")
    
    # Create and run a task
    task = Task(
        objective="Answer a question",
        parameters={
            "messages": [
                {"role": "user", "content": "What is AI?"}
            ]
        }
    )
    
    result = await assistant.execute(task, context)
    
    if task.status == "completed":
        print(f"Response: {task.result}")
    else:
        print(f"Task failed: {task.error}")
    
    # Clean up
    await registry.shutdown()
```

### Using the Agent Manager

```python
import asyncio
from plugins.workflow.ai_gateway.agent.manager import AgentManager
from plugins.workflow.ai_gateway.agent.base import Task

async def main():
    # Create and initialize the agent manager
    manager = AgentManager(storage_dir="~/.pepperpy/agents")
    await manager.initialize()
    
    try:
        # Create an agent
        assistant = await manager.create_agent(
            "assistant-1",
            "assistant",
            {
                "name": "General Assistant",
                "model_id": "gpt-4",
                "system_prompt": "You are a helpful assistant."
            }
        )
        
        # Create a session
        session_id = "user-session-123"
        context = await manager.create_session(session_id)
        
        # Create a task
        task = Task(
            objective="Answer a question",
            parameters={
                "messages": [
                    {"role": "user", "content": "What is AI?"}
                ]
            }
        )
        
        # Process the task
        result = await manager.process_task(task, session_id, "assistant-1")
        
        if result.status == "completed":
            print(f"Response: {result.result}")
        else:
            print(f"Task failed: {result.error}")
            
    finally:
        # Shut down the manager
        await manager.shutdown()
```

## Examples

See the example files for implementation demonstrations:

- `agent_system_example.py`: Example using the agent registry
- `agent_manager_example.py`: Example using the agent manager with persistence

## Memory Implementations

Choose from different memory implementations:

- **SimpleMemory**: Basic in-memory storage
- **LRUMemory**: Memory with least recently used eviction policy
- **ConversationMemory**: For storing conversation history
- **HierarchicalMemory**: Multi-layer memory with different retention policies

## Creating Custom Agents

Extend the `BaseAgent` class to create custom agent types:

```python
from plugins.workflow.ai_gateway.agent.base import BaseAgent, AgentRole, AgentCapability

class MyCustomAgent(BaseAgent):
    """Custom agent implementation."""
    
    def __init__(self, agent_id, name, description, ...):
        """Initialize custom agent."""
        role = AgentRole.SPECIALIST
        capabilities = [AgentCapability.CUSTOM_CAPABILITY]
        config = {"custom_param": custom_value}
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            role=role,
            capabilities=capabilities,
            config=config
        )
        
    async def execute(self, task, context):
        """Execute a task."""
        # Custom task execution logic
        return result
```

## Agent Registration

Register custom agent types with the registry:

```python
from plugins.workflow.ai_gateway.agent.registry import AgentRegistry
from my_agent_module import MyCustomAgent

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
    }
)
```

## Architecture

For detailed architecture information, see the [ARCHITECTURE.md](ARCHITECTURE.md) file. 