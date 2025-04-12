# PepperPy Agent Topologies

PepperPy provides a comprehensive framework for implementing and using various agent topologies - patterns for organizing and coordinating multiple AI agents to work together effectively.

## Available Topologies

PepperPy supports the following topology patterns:

### 1. Orchestrator Topology

A centrally controlled agent system where a main orchestrator agent coordinates the execution of specialized worker agents.

**Key Features:**
- Central control through orchestrator
- Task delegation to specialized agents
- Aggregation of agent results
- Structured workflow management

**Use Cases:**
- Complex multi-step tasks
- When specialized agents need coordination
- When a clear task breakdown is needed
- For managed deliberation processes

### 2. Mesh Topology

A decentralized network where agents can communicate directly with each other without a central coordinator.

**Key Features:**
- Peer-to-peer communication
- No central point of failure
- Flexible communication patterns
- Adaptive routing between agents

**Use Cases:**
- Collaborative problem-solving
- Self-organizing systems
- Resilient multi-agent networks
- When agents need direct coordination

### 3. Event Topology

A loosely coupled system where agents communicate through events and topics using a publish-subscribe pattern.

**Key Features:**
- Decoupled agent dependencies
- Topic-based message routing
- Asynchronous communication
- Event-driven workflows

**Use Cases:**
- When agents need to react to events
- For system monitoring and alerting
- When agents have varying availability
- For complex event processing

### 4. Hierarchy Topology

A tree-structured organization where agents are arranged in a management hierarchy with different levels of abstraction.

**Key Features:**
- Multi-level organization
- Delegation from higher to lower levels
- Aggregation of results up the hierarchy
- Abstraction at different levels

**Use Cases:**
- Complex tasks requiring decomposition
- When task management needs hierarchy
- For multi-level planning and execution
- When different abstraction levels are needed

### 5. Chain Topology

A sequential processing pipeline where tasks flow through agents in a predefined order, with each agent performing a specific transformation.

**Key Features:**
- Sequential processing stages
- Clear input/output contracts
- One-way or bidirectional flow
- Progressive refinement of outputs

**Use Cases:**
- Step-by-step processing
- When output of one agent feeds into another
- For gradual refinement of content
- Multi-stage reasoning processes

### 6. Teamwork Topology

A collaborative approach where agents work as a team, sharing insights and building consensus through deliberation and voting.

**Key Features:**
- Collaborative decision-making
- Consensus building mechanisms
- Role-based team structure
- Deliberation and voting protocols

**Use Cases:**
- When diverse perspectives are needed
- For balanced decision-making
- When consensus is required
- For complex evaluations requiring debate

### 7. Master Control Program (MCP) Topology

A centralized control system inspired by classic computing architecture that manages resources, schedules tasks, and coordinates agent processes.

**Key Features:**
- Centralized task scheduling and prioritization
- Resource allocation and management
- Fault tolerance and error recovery
- Parallel subtask execution

**Use Cases:**
- Complex multi-stage processing with varied resources
- Systems requiring fault tolerance and recovery
- When resource optimization is critical
- For complex workflows with dynamic priorities

### 8. Observer Topology

A monitoring and oversight system where observer agents can monitor, analyze, and potentially intervene in the actions of other agents.

**Key Features:**
- Real-time monitoring of agent activities
- Intervention capabilities (prevention, modification)
- Event logging and analysis
- Subscription-based observation relationships

**Use Cases:**
- Implementing AI oversight mechanisms
- Ethical and safety monitoring
- Performance and quality evaluation
- Regulatory compliance and audit trails
- Creating agent oversight hierarchies

### 9. Federation Topology

A multi-domain system that enables collaboration between separate agent systems across organizational boundaries while maintaining separation of concerns.

**Key Features:**
- Multi-domain architecture with organizational boundaries
- Controlled cross-domain communication with policies
- Authentication and security for cross-domain requests
- Federation-level coordination and governance

**Use Cases:**
- Cross-organization collaboration
- Multi-tenant agent systems
- Regulatory compliance scenarios
- Enterprise-scale agent ecosystems
- When strong domain separation is required

## Using Topologies

### Configuration

Each topology can be configured with topology-specific options:

```python
from pepperpy import PepperPy

# Create the PepperPy instance
pepperpy = (
    PepperPy()
    .with_llm("openai", model="gpt-4")
    .with_topology(
        "orchestrator",  # Choose topology type
        # Topology-specific configuration
        max_iterations=3,
        # Agent configurations
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
```

### Execution

Execute the topology with input data:

```python
async with pepperpy:
    result = await pepperpy.execute_topology({
        "task": "Research and write an article about AI topologies."
    })
    
print(result)
```

## Observer Topology Example

Here's an example of using the Observer topology for ethical oversight:

```python
from pepperpy import PepperPy

# Create a PepperPy instance with Observer topology
pepperpy = (
    PepperPy()
    .with_llm("openai", model="gpt-4")
    .with_topology(
        "observer",
        # Observer configuration
        broadcast_events=False,
        allow_interventions=True,  # Enable interventions
        # Observer relationships
        subscriptions={
            "ethics_observer": ["content_agent"]
        },
        # Agent configurations
        agents={
            "content_agent": {
                "agent_type": "assistant",
                "system_prompt": "You are a content creation AI."
            },
            "ethics_observer": {
                "agent_type": "assistant",
                "system_prompt": "You are an ethics oversight AI. Intervene when necessary."
            }
        }
    )
)

async with pepperpy:
    # Execute with the target agent
    result = await pepperpy.execute_topology({
        "task": "Write a paragraph about renewable energy.",
        "target_agent": "content_agent"
    })
    
    # Check if there were any interventions
    if result.get("interventions"):
        print(f"Observer intervention occurred: {result['interventions']}")
    
    # Get event history
    events = await pepperpy.topology.get_events()
    print(f"Recorded {len(events)} events")
```

## MCP Topology Example

Here's an example of using the Master Control Program (MCP) topology for a complex task:

```python
from pepperpy import PepperPy

# Create a PepperPy instance with MCP topology
pepperpy = (
    PepperPy()
    .with_llm("openai", model="gpt-4")
    .with_topology(
        "mcp",
        # MCP configuration
        priority_levels=5,
        scheduling_algorithm="priority",
        fault_tolerance=True,
        resource_allocation="balanced",
        # Agent configurations
        agents={
            "researcher": {
                "agent_type": "assistant",
                "system_prompt": "You are a research specialist.",
                "resource_weight": 2.0  # Higher resource allocation
            },
            "writer": {
                "agent_type": "assistant",
                "system_prompt": "You are a content writer."
            },
            "editor": {
                "agent_type": "assistant",
                "system_prompt": "You are an editor who reviews and improves content."
            }
        }
    )
)

# Execute with priority
async with pepperpy:
    result = await pepperpy.execute_topology({
        "task": "Research, analyze, and write a comprehensive report on AI trends.",
        "priority": 5  # High priority task
    })
    
    # Get system stats
    stats = await pepperpy.topology.get_system_stats()
    print(f"System stats: {stats}")
```

## Custom Topology Implementation

You can create custom topologies by:

1. Creating a class that inherits from `AgentTopologyProvider`
2. Implementing the required methods (`initialize`, `cleanup`, `execute`)
3. Registering the topology

Example:

```python
from pepperpy.agent.topology.base import AgentTopologyProvider, register_topology_provider

class CustomTopology(AgentTopologyProvider):
    """Custom topology implementation."""
    
    async def initialize(self) -> None:
        """Initialize topology resources."""
        # Implementation
        
    async def cleanup(self) -> None:
        """Clean up resources."""
        # Implementation
        
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the topology."""
        # Implementation

# Register the topology
register_topology_provider("custom", CustomTopology)
```

You can also implement topologies as plugins using the plugin architecture.

## Federation Topology Example

Here's an example of using the Federation topology for multi-organization collaboration:

```python
from pepperpy import PepperPy

# Create a PepperPy instance with Federation topology
pepperpy = (
    PepperPy()
    .with_llm("openai", model="gpt-4")
    .with_topology(
        "federation",
        # Define domains (organizational boundaries)
        domains={
            "research_domain": {
                "topology_type": "orchestrator",  # Each domain uses its own internal topology
                "description": "Research organization",
                "agents": {
                    "researcher": {
                        "agent_type": "assistant",
                        "system_prompt": "You are a research specialist."
                    }
                }
            },
            "development_domain": {
                "topology_type": "mesh",  # Different internal topology
                "description": "Development organization",
                "agents": {
                    "developer": {
                        "agent_type": "assistant",
                        "system_prompt": "You are a developer."
                    }
                }
            }
        },
        # Federation-level coordination
        agents={
            "coordinator": {
                "agent_type": "assistant",
                "system_prompt": "You coordinate between research and development."
            }
        },
        # Cross-domain communication policies
        federation_policies={
            "default": {"allow": False},  # Default is to disallow cross-domain communication
            "domain_policies": {
                # Allow specific communication paths
                ("research_domain", "development_domain"): {"allow": True},
                ("federation", "*"): {"allow": True}  # Federation agents can talk to all domains
            }
        },
        authentication_required=True
    )
)

async with pepperpy:
    # Execute a task in a specific domain
    research_result = await pepperpy.execute_topology({
        "task": "Research the latest AI techniques",
        "domain": "research_domain"
    })
    
    # Execute a cross-domain task (with proper authentication)
    auth_result = await pepperpy.execute_topology({
        "task": "Get authentication token",
        "task_type": "get_auth_token",
        "domain": "research_domain"
    })
    
    federated_result = await pepperpy.execute_topology({
        "task": "Implement the new AI technique",
        "source_domain": "research_domain",
        "target_domain": "development_domain",
        "auth_token": auth_result["auth_token"]
    })
    
    # Use federation-level coordination
    coordination_result = await pepperpy.execute_topology({
        "task": "Coordinate research and development efforts",
        "agent_id": "coordinator"
    })
``` 