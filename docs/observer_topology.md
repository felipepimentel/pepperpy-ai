# Observer Topology

The Observer topology is a powerful pattern that implements monitoring, oversight, and intervention capabilities for agent systems. It allows designated observer agents to monitor the activities of other agents, analyze their outputs, and intervene when necessary.

## Key Features

### 1. Agent Monitoring

Observer agents can monitor one or more target agents:

- **Subscription Model**: Define which observers watch which agents
- **Broadcast Mode**: Optionally broadcast all events to all observers
- **Dynamic Relationships**: Add or remove observer relationships at runtime

### 2. Intervention Capabilities

Observers can intervene in agent activities in several ways:

- **Prevention**: Block execution of tasks that violate guidelines
- **Modification**: Alter results to improve quality or maintain standards
- **Analysis**: Provide feedback or insights without modifying output

### 3. Event Logging and Analysis

The topology maintains a detailed record of agent activities:

- **Event History**: Complete log of all agent interactions
- **Observation Records**: Track what was observed and by whom
- **Intervention Tracking**: Record all interventions and their effects

### 4. Customizable Oversight Models

Implement different oversight approaches based on your needs:

- **Ethics Oversight**: Monitor for ethical issues and prevent harmful outputs
- **Quality Assurance**: Review and improve agent outputs for quality
- **Fact Checking**: Verify factual accuracy of agent statements
- **Multi-Level Oversight**: Combine multiple observers with different specializations

## Configuration Options

Here's a complete configuration reference for the Observer topology:

```python
pepperpy = (
    PepperPy()
    .with_llm("openai", model="gpt-4")
    .with_topology(
        "observer",
        # Core Observer configuration
        subscriptions={                      # Map of observer_id -> [observable_ids]
            "observer1": ["agent1", "agent2"],
            "observer2": ["agent3", "*"]     # "*" means observe all events
        },
        broadcast_events=False,              # Whether to broadcast all events to all observers
        log_all_events=True,                 # Whether to log all events for debugging
        allow_interventions=True,            # Whether observers can intervene
        
        # Agent configurations
        agents={
            "agent1": {
                "agent_type": "assistant",
                "system_prompt": "You are a worker agent..."
            },
            "observer1": {
                "agent_type": "assistant",
                "system_prompt": "You are an observer agent..."
            },
            # Additional agents...
        }
    )
)
```

## Usage Patterns

### Basic Monitoring

The simplest use case is monitoring agents without intervention:

```python
from pepperpy import PepperPy

# Create PepperPy instance with Observer topology
pepperpy = (
    PepperPy()
    .with_llm("openai", model="gpt-4")
    .with_topology(
        "observer",
        subscriptions={
            "logger_agent": ["worker_agent"]  # Logger observes worker
        },
        broadcast_events=False,
        allow_interventions=False,            # No interventions
        agents={
            "worker_agent": {
                "agent_type": "assistant", 
                "system_prompt": "You are a worker AI that answers user questions."
            },
            "logger_agent": {
                "agent_type": "assistant",
                "system_prompt": "You are a logging AI that records and analyzes other agents' activities."
            }
        }
    )
)

async with pepperpy:
    # Execute with the worker agent
    result = await pepperpy.execute_topology({
        "task": "Explain how solar panels work.",
        "target_agent": "worker_agent"
    })
    
    # The logger agent will automatically receive a notification
    # about this execution but won't intervene
    
    # Get all recorded events
    events = await pepperpy.topology.get_events()
    print(f"Recorded {len(events)} events")
```

### Ethical Oversight

Implement ethical oversight to prevent harmful outputs:

```python
pepperpy = (
    PepperPy()
    .with_llm("openai", model="gpt-4")
    .with_topology(
        "observer",
        subscriptions={
            "ethics_agent": ["content_agent"]
        },
        allow_interventions=True,  # Enable interventions
        agents={
            "content_agent": {
                "agent_type": "assistant",
                "system_prompt": "You are a content creation AI."
            },
            "ethics_agent": {
                "agent_type": "assistant",
                "system_prompt": """You are an ethics oversight AI. Your role is to monitor other agents and intervene when necessary.

INTERVENTION GUIDELINES:
1. If a request involves harmful content, respond with: PREVENT: Request involves potentially harmful content.
2. If a request is about weapons or illegal activities, respond with: PREVENT: Request violates ethical guidelines.
3. If a request seems controversial but not harmful, respond with: ALLOW: Request is acceptable.
4. If a response should be modified, respond with: MODIFY: [your improved version]"""
            }
        }
    )
)

async with pepperpy:
    # Test with a potentially problematic request
    result = await pepperpy.execute_topology({
        "task": "Explain how to hack into someone's email account",
        "target_agent": "content_agent"
    })
    
    # The ethics agent should intervene and prevent execution
    if "interventions" in result:
        print(f"Ethical intervention occurred: {result['interventions']}")
```

### Multiple Specialized Observers

Implement a system with multiple observers for different aspects:

```python
pepperpy = (
    PepperPy()
    .with_llm("openai", model="gpt-4")
    .with_topology(
        "observer",
        subscriptions={
            "fact_checker": ["primary_agent"],
            "ethics_reviewer": ["primary_agent"],
            "quality_controller": ["primary_agent"]
        },
        allow_interventions=True,
        agents={
            "primary_agent": {
                "agent_type": "assistant",
                "system_prompt": "You are a general-purpose AI assistant."
            },
            "fact_checker": {
                "agent_type": "assistant",
                "system_prompt": "You verify factual accuracy of other agents' responses."
            },
            "ethics_reviewer": {
                "agent_type": "assistant",
                "system_prompt": "You ensure responses follow ethical guidelines."
            },
            "quality_controller": {
                "agent_type": "assistant",
                "system_prompt": "You improve the quality and clarity of responses."
            }
        }
    )
)
```

### Dynamically Managing Observers

Add or remove observers at runtime:

```python
async with pepperpy:
    # Start with no observers
    
    # Add a quality checker for this specific task
    await pepperpy.topology.add_observer("quality_agent", "worker_agent")
    
    # Execute with monitoring
    result = await pepperpy.execute_topology({
        "task": "Summarize the benefits of renewable energy.",
        "target_agent": "worker_agent"
    })
    
    # Remove the observer when no longer needed
    await pepperpy.topology.remove_observer("quality_agent", "worker_agent")
    
    # Get observers for an agent
    observers = await pepperpy.topology.get_observers("worker_agent")
    print(f"Current observers: {observers}")
```

## Observer Intervention Process

When observers are configured to allow interventions, they follow this process:

1. **Pre-Execution Check**: Before the target agent executes a task, the topology sends an intervention request to all observers
2. **Intervention Decision**: Observers decide whether to allow, prevent, or modify the task
3. **Response Handling**:
   - If any observer chooses to prevent, execution is blocked
   - If observers suggest modifications, these are applied to the result
   - If all observers allow, execution proceeds normally
4. **Post-Execution Notification**: Observers are notified of the execution results for analysis

The intervention mechanism is controlled by the `allow_interventions` configuration parameter and is disabled by default.

## Advanced Features

### Event Filtering and Analysis

Query events with filtering capabilities:

```python
# Get events for a specific agent
agent_events = await pepperpy.topology.get_events(agent_id="worker_agent")

# Get events of a specific type
execution_events = await pepperpy.topology.get_events(event_type="execution")
```

### Custom Event Handlers

Register custom handlers for specific event types:

```python
async def handle_error_event(event):
    """Handle error events specially."""
    logger.error(f"Agent {event['agent_id']} encountered an error: {event.get('error')}")

# Register the handler
await pepperpy.topology.register_event_handler(
    agent_id="monitor_agent",
    event_type="error",
    handler=handle_error_event
)
```

## Benefits and Use Cases

### AI Oversight and Governance

Build responsible AI systems with built-in oversight:

- **Safety Monitoring**: Detect and prevent harmful outputs
- **Ethical Compliance**: Ensure agents follow ethical guidelines
- **Bias Detection**: Monitor and correct for biases in agent responses
- **Regulatory Compliance**: Implement and document governance procedures

### Quality Management

Improve output quality through observation and intervention:

- **Content Review**: Review and improve content generation
- **Fact Verification**: Verify factual accuracy of statements
- **Style Consistency**: Maintain consistent style and tone
- **Technical Validation**: Check technical correctness of outputs

### Monitoring and Analytics

Gather insights about agent performance:

- **Performance Monitoring**: Track agent performance metrics
- **User Interaction Analysis**: Analyze patterns in agent usage
- **Failure Detection**: Identify recurring error patterns
- **Continuous Improvement**: Gather data for system refinement

## Example Use Cases

1. **Content Moderation System**:
   - Content creation agents generate responses
   - Ethics observers monitor for harmful content
   - Safety observers prevent violations of guidelines

2. **AI Research Assistant**:
   - Research agents gather information
   - Fact-checking observers verify accuracy
   - Quality observers improve presentation
   - Cross-reference observers identify contradictions

3. **Automated Support System**:
   - Support agents handle customer queries
   - Quality observers improve clarity and empathy
   - Knowledge observers verify technical accuracy
   - Escalation observers identify complex cases for human review

## Limitations and Considerations

- **Performance Impact**: Each observer adds processing overhead
- **Complexity Management**: Multiple observers require careful coordination
- **Intervention Conflicts**: Potential conflicts between different observers
- **System Transparency**: Need for clear logs of interventions for accountability

## Comparison with Other Topologies

| Feature | Observer | Orchestrator | MCP | Mesh |
|---------|----------|-------------|-----|------|
| Primary Purpose | Monitoring and intervention | Task coordination | Resource management | Agent collaboration |
| Control Model | Oversight | Central control | Centralized scheduling | Decentralized |
| Key Strength | Safety and quality | Workflow management | Task prioritization | Adaptability |
| Overhead | Medium-High | Medium | High | Low |
| Best For | Oversight, governance | Structured processes | Complex scheduling | Peer collaboration |

## Examples

See the [examples/observer_oversight_example.py](../examples/observer_oversight_example.py) file for complete working examples of different observer patterns. 