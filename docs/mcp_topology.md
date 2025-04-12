# MCP (Master Control Program) Topology

The Master Control Program (MCP) topology is a powerful centralized control system for coordinating multiple AI agents with sophisticated resource management and task scheduling capabilities.

## Key Features

### 1. Priority-Based Task Scheduling

MCP provides a priority queue system that allows tasks to be scheduled and executed based on their importance:

- **Priority Levels**: Configure up to 10 priority levels (1-10)
- **Multiple Scheduling Algorithms**:
  - `priority`: Tasks are sorted by priority level (highest first)
  - `fifo`: Tasks are processed in first-in, first-out order
  - `round_robin`: Tasks are distributed evenly across agents

### 2. Dynamic Resource Allocation

MCP implements an intelligent resource allocation system for optimizing agent utilization:

- **Resource Weighting**: Assign weights to agents based on their capabilities or importance
- **Allocation Strategies**:
  - `balanced`: Even distribution of tasks across agents
  - `priority`: High-priority tasks get assigned to high-capability agents
  - `weighted`: Uses agent weights to determine assignment probabilities

### 3. Fault Tolerance and Error Recovery

MCP includes sophisticated error handling to gracefully recover from task failures:

- **Partial Result Synthesis**: If some subtasks succeed but others fail, MCP synthesizes results from completed subtasks
- **Automatic Retry**: Failed tasks can be retried with simplified parameters
- **Intelligent Error Handling**: Different error types trigger different recovery strategies

### 4. Performance Monitoring

MCP tracks detailed performance metrics to help optimize and analyze your agent system:

- **Execution Metrics**: Track success rates, processing times, and task throughput
- **Resource Utilization**: Monitor agent workloads and resource distribution
- **Optimization Feedback**: Use metrics to improve resource allocation

## Configuration Options

Here's a complete configuration reference for the MCP topology:

```python
pepperpy = (
    PepperPy()
    .with_llm("openai", model="gpt-4")
    .with_topology(
        "mcp",
        # Core MCP configuration
        priority_levels=5,                  # Number of priority levels (1-10)
        scheduling_algorithm="priority",    # Task scheduling algorithm
        fault_tolerance=True,               # Enable fault tolerance mechanisms
        resource_allocation="balanced",     # Resource allocation strategy
        
        # Plugin-specific configuration
        task_queue_limit=100,               # Maximum number of tasks in queue
        performance_metrics=True,           # Enable detailed performance metrics
        
        # Agent configurations
        agents={
            "agent_id": {
                "agent_type": "assistant",
                "system_prompt": "Agent prompt...",
                "resource_weight": 2.0      # Agent's resource allocation weight
            },
            # Additional agents...
        }
    )
)
```

## Usage Patterns

### Basic Usage

```python
from pepperpy import PepperPy

# Create PepperPy instance with MCP topology
pepperpy = (
    PepperPy()
    .with_llm("openai", model="gpt-4")
    .with_topology(
        "mcp",
        priority_levels=5,
        scheduling_algorithm="priority",
        agents={
            "researcher": {
                "agent_type": "assistant",
                "system_prompt": "You are a research specialist."
            },
            "writer": {
                "agent_type": "assistant",
                "system_prompt": "You are a content writer."
            }
        }
    )
)

async with pepperpy:
    # Execute a single task with priority
    result = await pepperpy.execute_topology({
        "task": "Research and summarize recent AI advances",
        "priority": 5  # High priority
    })
    
    print(result)
```

### Managing Multiple Tasks

```python
async with pepperpy:
    # Initialize the MCP
    await pepperpy.topology.initialize()
    
    # Add tasks with different priorities
    high_priority_id = await pepperpy.topology.add_task(
        "Critical task with highest priority", 
        priority=9
    )
    
    medium_priority_id = await pepperpy.topology.add_task(
        "Medium priority task", 
        priority=5
    )
    
    low_priority_id = await pepperpy.topology.add_task(
        "Low priority background task", 
        priority=2
    )
    
    # Process all tasks in priority order
    results = await pepperpy.topology._process_task_queue()
    
    # Check results
    print(f"High priority result: {results[high_priority_id]}")
```

### Dynamic Resource Management

```python
async with pepperpy:
    # Get current resource allocation
    stats = await pepperpy.topology.get_system_stats()
    print(f"Initial resources: {stats['resource_allocation']}")
    
    # Adjust resources for specific tasks
    await pepperpy.topology.adjust_resources("specialist_agent", 3.0)  # Increase
    await pepperpy.topology.adjust_resources("general_agent", 1.0)     # Decrease
    
    # Run a task with the adjusted resources
    result = await pepperpy.execute_topology({
        "task": "Perform specialized analysis",
        "priority": 5
    })
    
    # Reset and optimize resources based on usage patterns
    await pepperpy.topology.optimize_resources()
```

### Performance Monitoring

```python
async with pepperpy:
    # Execute several tasks
    for i in range(5):
        await pepperpy.execute_topology({
            "task": f"Task {i}",
            "priority": i+1
        })
    
    # Get performance metrics
    status = await pepperpy.topology.get_status()
    
    # Print metrics
    metrics = status.get("metrics", {})
    print(f"Tasks processed: {metrics.get('tasks_processed', 0)}")
    print(f"Average processing time: {metrics.get('avg_processing_time', 0):.2f}s")
    
    # Reset metrics for a new batch
    previous = await pepperpy.topology.reset_metrics()
```

## Advanced Features

### Task Metadata

You can include metadata with tasks to assist with processing and tracking:

```python
metadata = {
    "category": "research",
    "deadline": "2023-12-15",
    "importance": "critical",
    "requestor": "engineering_team",
    "context": {
        "related_projects": ["project_a", "project_b"],
        "background_info": "Previous research indicated..."
    }
}

task_id = await pepperpy.topology.add_task(
    "Research quantum computing advances", 
    priority=8,
    metadata=metadata
)
```

### Custom Process Handling

In some cases, you might want to implement custom handling for specific process types:

```python
# Subclassing to add custom process handling
class CustomMCPTopology(MCPTopology):
    async def _create_subtasks(self, process):
        # Custom subtask creation logic
        category = process["metadata"].get("category")
        
        if category == "research":
            # Research-specific subtask breakdown
            return await self._create_research_subtasks(process)
        else:
            # Default implementation
            return await super()._create_subtasks(process)
            
    async def _create_research_subtasks(self, process):
        # Specialized research subtask creation
        # ...implementation...
```

## Benefits and Use Cases

### When to Use MCP Topology

The MCP topology is ideal for:

1. **Complex Multi-Stage Processing**
   - When tasks require breaking down into subtasks
   - For workflows with multiple processing stages

2. **Priority-Sensitive Workloads**
   - When some tasks are more important than others
   - For real-time or time-sensitive applications

3. **Resource-Intensive Operations**
   - When you need efficient allocation of computational resources
   - For balancing load across multiple agents

4. **Fault-Critical Systems**
   - When task failure is not an option
   - For systems requiring graceful degradation

5. **Performance-Optimized Applications**
   - When you need data on system performance
   - For optimizing agent utilization over time

### Real-World Applications

- **Enterprise Task Processing**: Manage and prioritize business tasks across departments
- **Research Systems**: Coordinate multiple research agents with different specializations
- **Content Generation Pipelines**: Manage complex content creation workflows
- **Data Analysis Systems**: Allocate and coordinate data processing tasks
- **Decision Support Systems**: Provide fault-tolerant decision making for critical systems

## Limitations and Considerations

- **Centralized Control**: As a centralized system, MCP can become a bottleneck with extremely high volumes
- **Configuration Complexity**: More configuration options mean more tuning required
- **Resource Overhead**: Advanced features like performance monitoring add some overhead

## Comparison with Other Topologies

| Feature | MCP | Orchestrator | Mesh | Hierarchy |
|---------|-----|-------------|------|-----------|
| Task Prioritization | ✅ Advanced | ✅ Basic | ❌ | ✅ Basic |
| Resource Management | ✅ Dynamic | ❌ | ❌ | ✅ Basic |
| Fault Tolerance | ✅ Advanced | ❌ | ✅ Basic | ❌ |
| Performance Metrics | ✅ Detailed | ❌ | ❌ | ❌ |
| Centralized Control | ✅ | ✅ | ❌ | ✅ |
| Load Distribution | ✅ Dynamic | ❌ | ✅ Static | ✅ Static |

## Examples

See the [examples/mcp_topology_example.py](../examples/mcp_topology_example.py) and [examples/priority_task_processing.py](../examples/priority_task_processing.py) files for complete working examples. 