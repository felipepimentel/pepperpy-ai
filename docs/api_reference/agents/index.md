# AI Agents Reference

PepperPy AI provides a rich set of specialized AI agents for different tasks and purposes.

## Available Agents

### Development Agents
- [Development Agent](./development.md) - Specialized in code development tasks
- [Architect Agent](./architect.md) - Handles system architecture and design
- [Quality Agent](./quality.md) - Focuses on code quality and best practices
- [Review Agent](./review.md) - Performs code reviews and provides feedback

### Research Agents
- [Research Agent](./research.md) - Conducts research and analysis
- [Analysis Agent](./analysis.md) - Performs detailed analysis of codebases
- [Researcher Agent](./researcher.md) - Advanced research capabilities

### Management Agents
- [Project Manager Agent](./project_manager.md) - Handles project management tasks
- [Team Agent](./team.md) - Manages team interactions and coordination
- [Management Agent](./management.md) - General management capabilities

### QA Agents
- [QA Agent](./qa.md) - Quality assurance and testing
- [Reviewer Agent](./reviewer.md) - Code and documentation review

### Specialized Agents
- [Specialized Agent](./specialized.md) - Custom specialized tasks

## Agent Factory

The `AgentFactory` provides a centralized way to create and manage agents:

```python
from pepperpy_ai.agents import AgentFactory
from pepperpy_ai.config import Config

config = Config()
factory = AgentFactory(config)

# Create a development agent
dev_agent = factory.create_agent("development")

# Create a research agent
research_agent = factory.create_agent("research")
```

## Base Agent Interface

All agents implement the base agent interface:

```python
class BaseAgent(Protocol):
    """Base agent protocol."""
    
    @property
    def config(self) -> Config:
        """Get agent configuration."""
        ...
        
    async def process(self, input: str) -> str:
        """Process input and return response."""
        ...
        
    async def stream(self, input: str) -> AsyncGenerator[str, None]:
        """Stream responses."""
        ...
```

## Agent Configuration

Agents can be configured through the config system:

```python
from pepperpy_ai.config import Config

config = Config(
    agent_type="development",
    temperature=0.7,
    max_tokens=1000
)
```

## Agent Types

The following agent types are available:

- `development` - Code development
- `architect` - System architecture
- `quality` - Code quality
- `review` - Code review
- `research` - Research tasks
- `analysis` - Code analysis
- `project_manager` - Project management
- `team` - Team management
- `qa` - Quality assurance
- `specialized` - Custom tasks

## Best Practices

1. **Agent Selection**
   - Choose the most appropriate agent for your task
   - Consider using multiple agents for complex tasks
   - Use the factory pattern for agent creation

2. **Configuration**
   - Configure agents with appropriate parameters
   - Use environment variables for sensitive data
   - Validate configuration values

3. **Error Handling**
   - Handle agent-specific exceptions
   - Implement proper logging
   - Use fallback mechanisms

4. **Performance**
   - Use streaming for long responses
   - Implement caching when appropriate
   - Monitor agent performance

## Examples

### Development Agent

```python
from pepperpy_ai.agents import AgentFactory
from pepperpy_ai.config import Config

async def development_example():
    config = Config()
    factory = AgentFactory(config)
    agent = factory.create_agent("development")
    
    response = await agent.process("Implement a Python function to sort a list")
    print(response)
```

### Research Agent

```python
async def research_example():
    config = Config()
    factory = AgentFactory(config)
    agent = factory.create_agent("research")
    
    response = await agent.process("Research best practices for API design")
    print(response)
```

### Team Agent

```python
async def team_example():
    config = Config()
    factory = AgentFactory(config)
    agent = factory.create_agent("team")
    
    response = await agent.process("Coordinate code review process")
    print(response)
``` 