# Federation Topology

The Federation topology implements a pattern that enables multiple agent systems to collaborate across organizational boundaries while maintaining separation of concerns. It provides a structured way to manage cross-domain communication with security, authentication, and policy enforcement.

## Key Features

### 1. Multi-Domain Architecture

The Federation topology organizes agents into separate domains (organizational units):

- **Domain Independence**: Each domain operates with its own policies and configurations
- **Domain-Specific Topologies**: Domains can use different internal topologies (Orchestrator, MCP, Observer, etc.)
- **Organizational Boundaries**: Clear separation between different agent systems
- **Domain-Level Privacy**: Information sharing is explicitly controlled

### 2. Cross-Domain Communication

Secure and controlled communication between domains:

- **Federation Policies**: Fine-grained control over which domains can communicate
- **Authentication**: Secure token-based authentication for cross-domain requests
- **Task-Based Permissions**: Policies can allow or deny specific types of tasks
- **Broadcast Capabilities**: Send tasks to multiple domains simultaneously

### 3. Federated Governance

Central coordination with distributed execution:

- **Federation-Level Agents**: Agents that operate at the federation level to coordinate across domains
- **Shared Resources**: Resources that can be accessed by multiple domains
- **Centralized Monitoring**: Track cross-domain interactions and federation status
- **Dynamic Domain Management**: Add or remove domains at runtime

### 4. Multi-Organization Integration

Bridge between different agent ecosystems:

- **Organizational Isolation**: Maintain separation between different organizations
- **Selective Sharing**: Control what information crosses organizational boundaries
- **Regulatory Compliance**: Implement governance and oversight requirements
- **Cross-Organizational Workflows**: Enable complex workflows across organizational boundaries

## Configuration Options

Here's a complete configuration reference for the Federation topology:

```python
pepperpy = (
    PepperPy()
    .with_llm("openai", model="gpt-4")
    .with_topology(
        "federation",
        # Define domains (organizational boundaries)
        domains={
            "domain1": {
                "topology_type": "orchestrator",  # Each domain's internal topology
                "topology_config": {
                    # Domain-specific topology configuration
                    "max_iterations": 3,
                },
                "description": "Domain description",
                "features": ["feature1", "feature2"],
                "agents": {
                    # Agents configuration for this domain
                    "agent1": {
                        "agent_type": "assistant",
                        "system_prompt": "Agent system prompt"
                    }
                }
            },
            "domain2": {
                # Another domain configuration
            }
        },
        # Federation-level agents (not tied to any specific domain)
        agents={
            "federation_agent": {
                "agent_type": "assistant",
                "system_prompt": "Federation-level agent system prompt"
            }
        },
        # Define cross-domain communication policies
        federation_policies={
            "default": {"allow": False},  # Default policy is to deny
            "domain_policies": {
                # Allow domain1 to communicate with domain2 for specific tasks
                ("domain1", "domain2"): {
                    "allow": True,
                    "allowed_tasks": ["task_type1", "task_type2"]
                },
                # Allow domain2 to communicate with all domains
                ("domain2", "*"): {
                    "allow": True
                },
                # Allow federation-level agents to communicate with all domains
                ("federation", "*"): {
                    "allow": True
                }
            }
        },
        # Resources shared across domains
        shared_resources=["resource1", "resource2"],
        # Require authentication for cross-domain calls
        authentication_required=True
    )
)
```

## Usage Patterns

### Basic Domain Execution

Execute a task within a specific domain:

```python
# Execute a task in a specific domain
result = await pepperpy.execute_topology({
    "task": "Perform domain-specific task",
    "domain": "domain1",
    "target_agent": "agent1"  # Optional: specify which agent to use
})
```

### Cross-Domain Communication

Execute a task that requires communication between domains:

```python
# Get authentication token for the source domain
auth_result = await pepperpy.execute_topology({
    "task": "Get authentication token",
    "task_type": "get_auth_token",
    "domain": "domain1"
})

auth_token = auth_result.get("auth_token")

# Execute a cross-domain (federated) task
federated_result = await pepperpy.execute_topology({
    "task": "Perform cross-domain task",
    "source_domain": "domain1",
    "target_domain": "domain2",
    "auth_token": auth_token,
    "task_type": "allowed_task_type"  # Must be allowed in federation policy
})
```

### Federation-Level Operations

Use federation-level agents and operations:

```python
# Get federation status
federation_status = await pepperpy.execute_topology({
    "task": "Get federation status",
    "task_type": "get_federation_status"
})

# Use a federation-level agent
coordinator_result = await pepperpy.execute_topology({
    "task": "Coordinate activities across domains",
    "agent_id": "federation_agent"
})

# Broadcast a task to multiple domains
broadcast_result = await pepperpy.execute_topology({
    "task": "Update all domains with this information",
    "broadcast_to_domains": ["domain1", "domain2", "domain3"]
})
```

### Domain Information and Management

Get information about domains or manage domains at runtime:

```python
# Get information about a domain
domain_info = await pepperpy.execute_topology({
    "task": "Get domain information",
    "task_type": "get_domain_info",
    "domain": "domain1"
})

# With direct access to topology for advanced operations
await pepperpy.topology.add_domain("new_domain", {
    "topology_type": "orchestrator",
    "agents": {
        "new_agent": {
            "agent_type": "assistant",
            "system_prompt": "New agent system prompt"
        }
    }
})

# Add a new federation policy
await pepperpy.topology.add_federation_policy(
    "domain1", "new_domain", 
    {"allow": True, "allowed_tasks": ["task_type1"]}
)
```

## Example Use Case: Multi-Organization Collaboration

This example demonstrates how three organizations can collaborate on a healthcare AI project:

```python
pepperpy = (
    PepperPy()
    .with_llm("openai", model="gpt-4")
    .with_topology(
        "federation",
        # Define organization domains
        domains={
            "org_healthcare": {
                "topology_type": "orchestrator",
                "description": "Healthcare organization with medical expertise",
                "agents": {
                    "medical_expert": {
                        "agent_type": "assistant",
                        "system_prompt": "You are a medical expert..."
                    }
                }
            },
            "org_tech": {
                "topology_type": "orchestrator",
                "description": "Technology organization with AI expertise",
                "agents": {
                    "tech_expert": {
                        "agent_type": "assistant",
                        "system_prompt": "You are a technology expert..."
                    }
                }
            },
            "org_regulatory": {
                "topology_type": "observer",  # Using Observer topology for oversight
                "topology_config": {
                    "allow_interventions": True
                },
                "description": "Regulatory organization that ensures compliance",
                "agents": {
                    "compliance_officer": {
                        "agent_type": "assistant",
                        "system_prompt": "You are a compliance officer..."
                    }
                }
            }
        },
        # Federation-level coordination
        agents={
            "project_manager": {
                "agent_type": "assistant",
                "system_prompt": "You are a project manager coordinating work..."
            }
        },
        # Strict cross-domain policies
        federation_policies={
            "default": {"allow": False},
            "domain_policies": {
                # Define which organizations can communicate with each other
                ("org_healthcare", "org_tech"): {"allow": True, "allowed_tasks": ["request_analysis"]},
                ("org_tech", "org_healthcare"): {"allow": True, "allowed_tasks": ["provide_analysis"]},
                ("org_regulatory", "*"): {"allow": True},
                ("federation", "*"): {"allow": True}
            }
        },
        shared_resources=["project_requirements", "compliance_guidelines"],
        authentication_required=True
    )
)
```

With this configuration, the three organizations can collaborate while:
- Maintaining separation of concerns
- Following organizational policies
- Meeting regulatory requirements
- Controlling information flow between organizations

## Benefits and Use Cases

### Cross-Organization Collaboration

Enable collaboration while maintaining organizational boundaries:

- **Healthcare Partnerships**: Connect medical experts with technology providers
- **Supply Chain Integration**: Link manufacturer and supplier agent systems
- **Research Collaborations**: Enable multiple research institutions to share specific findings
- **Public-Private Partnerships**: Connect government and private sector agent systems

### Regulatory Compliance

Implement governance requirements for multi-domain systems:

- **Privacy Compliance**: Control data sharing across organizational boundaries
- **Regulatory Oversight**: Enable third-party audit and regulatory supervision
- **Security Boundaries**: Implement security zones with controlled access
- **Data Sovereignty**: Maintain data governance across organizational domains

### Scalable Agent Ecosystems

Build large-scale agent systems with clear organizational structure:

- **Departmental Boundaries**: Create separate domains for different business units
- **Vendor Integration**: Integrate third-party agent systems securely
- **Ecosystem Development**: Build extensible agent ecosystems with clear interfaces
- **Enterprise Architecture**: Implement domain-driven design in agent systems

### Multi-Tenant Systems

Create systems that can serve multiple clients or tenants:

- **SaaS Architectures**: Separate customer-specific agent domains
- **Client Isolation**: Maintain strict separation between customer data and agents
- **Managed Service Providers**: Provide domain-specific agent systems to multiple clients
- **White-Label Solutions**: Deploy similar agent topologies for different brands

## Limitations and Considerations

- **Performance Impact**: Cross-domain communication adds overhead
- **Complexity Management**: Federation adds administrative complexity
- **Authentication Overhead**: Token management requires additional processing
- **Policy Maintenance**: Federation policies must be maintained and updated

## Comparison with Other Topologies

| Feature | Federation | Orchestrator | MCP | Observer |
|---------|-----------|-------------|-----|----------|
| Primary Purpose | Multi-organization collaboration | Task coordination | Resource management | Monitoring and intervention |
| Organizational Boundaries | Strong | None | None | None |
| Authentication | Yes | No | No | No |
| Policy Enforcement | Yes | No | No | No |
| Complexity | High | Medium | High | Medium |
| Best For | Cross-organization workflows | Task delegation | Resource optimization | Oversight mechanisms |

## Advanced Features

### 1. Federation Queries

Track all cross-domain communication:

```python
# Get all federation queries
queries = await pepperpy.topology.get_queries()

# Get queries of a specific type
federated_tasks = await pepperpy.topology.get_queries("federated_task")
```

### 2. Dynamic Domain Topologies

Access domain-specific topologies for advanced operations:

```python
# Get the topology for a specific domain
domain_topology = await pepperpy.topology.get_domain_topology("domain1")

# Perform domain-specific operations
if hasattr(domain_topology, "get_system_stats"):  # For MCP topology
    stats = await domain_topology.get_system_stats()
```

### 3. Domain Agent Access

Access agents from specific domains:

```python
# Get an agent from a specific domain
domain_agent = await pepperpy.topology.get_domain_agent("domain1", "agent1")

# Use the agent directly if needed
result = await domain_agent.process_message("Perform specialized task")
```

## Integration with Other Topologies

The Federation topology can be integrated with other topologies to create sophisticated agent systems:

1. **Federation of MCP Domains**: Each domain uses MCP internally for resource management
2. **Observer-Enabled Federation**: Use Observer topology for regulatory domains
3. **Mesh Networks in Domains**: Use Mesh topology within domains for peer collaboration
4. **Hierarchical Domains**: Use Hierarchy topology within domains for multi-level organization

See [examples/federation_example.py](../examples/federation_example.py) for complete working examples of the Federation topology. 