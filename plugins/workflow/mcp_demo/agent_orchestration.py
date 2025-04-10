"""Agent Orchestration for MCP.

This module provides an agent orchestration layer that coordinates multiple agents
and manages tools for them to use within the MCP framework.
"""

import asyncio
import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pepperpy.core.logging import get_logger


# Define a compatible ClientProvider interface as a Protocol
@runtime_checkable
class ClientProvider(Protocol):
    """Protocol for any MCP client provider."""

    initialized: bool

    async def initialize(self) -> None:
        """Initialize the client."""
        ...

    async def cleanup(self) -> None:
        """Clean up resources."""
        ...

    async def connect(self, server_url: str) -> None:
        """Connect to the server."""
        ...

    async def disconnect(self) -> None:
        """Disconnect from the server."""
        ...

    async def request(self, request: Any) -> Any:
        """Execute a request."""
        ...


# Use local protocol definitions if available, otherwise use pepperpy ones
try:
    from pepperpy.mcp.protocol import (
        MCPOperationType,
        MCPRequest,
        MCPStatusCode,
    )
except ImportError:
    # Fall back to local stubs
    from .protocol import (
        MCPOperationType,
        MCPRequest,
        MCPStatusCode,
    )


# Helper functions to create compatible requests
def create_request(
    request_id: str,
    model_id: str,
    operation_type: str,
    inputs: dict[str, Any],
    parameters: dict[str, Any] | None = None,
) -> MCPRequest:
    """Create a compatible MCPRequest that handles enum compatibility issues.

    Args:
        request_id: Unique request ID
        model_id: Model ID to use
        operation_type: Operation type as string ('chat', 'completion', etc.)
        inputs: Request inputs
        parameters: Optional request parameters

    Returns:
        MCPRequest instance
    """
    # Convert enum value to string if needed
    if hasattr(operation_type, "value"):
        operation_type = operation_type.value

    # Create request with properly typed operation
    return MCPRequest(
        request_id=request_id,
        model_id=model_id,
        operation=operation_type,  # Pass as string
        inputs=inputs,
        parameters=parameters or {},
    )


logger = get_logger("mcp.agent_orchestration")


class AgentState(str, Enum):
    """Agent execution state."""

    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentMemory:
    """Simple memory store for agents to retain information across executions."""

    # Short-term memory (current conversation)
    messages: list[dict[str, Any]] = field(default_factory=list)

    # Tool execution history
    tool_history: list[dict[str, Any]] = field(default_factory=list)

    # Key-value store for arbitrary data
    data: dict[str, Any] = field(default_factory=dict)

    # Function to retrieve embeddings for semantic memory (if available)
    _embedding_fn: Callable[[str], list[float]] | None = None

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": asyncio.get_event_loop().time(),
        })

    def add_tool_usage(
        self,
        tool_name: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        success: bool,
    ) -> None:
        """Record tool usage in history."""
        self.tool_history.append({
            "tool": tool_name,
            "inputs": inputs,
            "outputs": outputs,
            "success": success,
            "timestamp": asyncio.get_event_loop().time(),
        })

    def get_context(self, max_messages: int = 10) -> list[dict[str, Any]]:
        """Get formatted context for the agent."""
        # Return the most recent messages
        return self.messages[-max_messages:] if self.messages else []

    def get_relevant_tools(self, query: str) -> list[str]:
        """Get tools that might be relevant to the query."""
        # Simple implementation just returns all tools used recently
        # In a real implementation, this would use semantic search
        return list(set(item["tool"] for item in self.tool_history[-5:]))

    def store(self, key: str, value: Any) -> None:
        """Store a value in memory."""
        self.data[key] = value

    def retrieve(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from memory."""
        return self.data.get(key, default)

    def clear(self) -> None:
        """Clear all memory."""
        self.messages.clear()
        self.tool_history.clear()
        self.data.clear()


@dataclass
class Agent:
    """Agent that can execute tasks using tools."""

    name: str
    description: str
    tools: set[str] = field(default_factory=set)
    state: AgentState = AgentState.IDLE
    memory: AgentMemory = field(default_factory=AgentMemory)
    model_id: str = "gpt-3.5-turbo"

    def to_dict(self) -> dict[str, Any]:
        """Convert agent to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "tools": list(self.tools),
            "state": self.state.value,
            "model_id": self.model_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Agent":
        """Create agent from dictionary."""
        agent = cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            model_id=data.get("model_id", "gpt-3.5-turbo"),
        )

        # Set tools
        agent.tools = set(data.get("tools", []))

        # Set state if valid
        state_str = data.get("state")
        if state_str and isinstance(state_str, str):
            try:
                agent.state = AgentState(state_str)
            except ValueError:
                agent.state = AgentState.IDLE

        return agent


class ToolRegistry:
    """Registry for tools that agents can use."""

    def __init__(self) -> None:
        """Initialize the tool registry."""
        self.tools: dict[str, dict[str, Any]] = {}
        self.logger = get_logger("mcp.agent_orchestration.tool_registry")

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        required_permissions: list[str] | None = None,
    ) -> None:
        """Register a tool that agents can use.

        Args:
            name: Tool name
            description: Tool description
            parameters: Tool parameters schema
            required_permissions: Required permissions to use the tool
        """
        self.tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "required_permissions": required_permissions or [],
        }
        self.logger.info(f"Registered tool: {name}")

    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool.

        Args:
            name: Tool name

        Returns:
            True if the tool was unregistered, False if it wasn't registered
        """
        if name in self.tools:
            del self.tools[name]
            self.logger.info(f"Unregistered tool: {name}")
            return True
        return False

    def get_tool(self, name: str) -> dict[str, Any] | None:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool definition or None if not found
        """
        return self.tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        """List all registered tools.

        Returns:
            List of tool definitions
        """
        return list(self.tools.values())

    def get_tools_for_agent(self, agent: Agent) -> list[dict[str, Any]]:
        """Get tools that an agent is allowed to use.

        Args:
            agent: Agent to get tools for

        Returns:
            List of tool definitions the agent can use
        """
        return [self.tools[tool] for tool in agent.tools if tool in self.tools]


class AgentOrchestrator:
    """Orchestrates multiple agents to complete tasks."""

    def __init__(self, client: Any = None) -> None:
        """Initialize the agent orchestrator.

        Args:
            client: MCP client provider
        """
        self.client = client
        self.agents: dict[str, Agent] = {}
        self.tool_registry = ToolRegistry()
        self.logger = get_logger("mcp.agent_orchestration.orchestrator")
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the orchestrator."""
        if self.initialized:
            return

        # Verify client is initialized
        if self.client and not getattr(self.client, "initialized", False):
            await self.client.initialize()

        # Register default agents and tools
        self._register_default_agents()
        self._register_default_tools()

        self.initialized = True
        self.logger.info("Agent orchestrator initialized")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.agents.clear()
        self.initialized = False
        self.logger.info("Agent orchestrator cleaned up")

    def _register_default_agents(self) -> None:
        """Register default agents."""
        # Register a planner agent
        self.register_agent(
            name="planner",
            description="Decomposes complex tasks into smaller steps",
            tools={"analyze_task", "create_plan"},
            model_id="gpt-4",
        )

        # Register an executor agent
        self.register_agent(
            name="executor",
            description="Executes individual tasks using available tools",
            tools={"calculate", "get_weather", "translate", "search"},
            model_id="gpt-3.5-turbo",
        )

        # Register a critic agent
        self.register_agent(
            name="critic",
            description="Reviews outputs and suggests improvements",
            tools={"analyze_output", "suggest_improvements"},
            model_id="gpt-3.5-turbo",
        )

    def _register_default_tools(self) -> None:
        """Register default tools."""
        # Planning tools
        self.tool_registry.register_tool(
            name="analyze_task",
            description="Analyze a task to determine required steps and tools",
            parameters={
                "task_description": {
                    "type": "string",
                    "description": "Description of the task to analyze",
                }
            },
        )

        self.tool_registry.register_tool(
            name="create_plan",
            description="Create a step-by-step plan to complete a task",
            parameters={
                "task_description": {
                    "type": "string",
                    "description": "Description of the task to plan",
                },
                "available_tools": {
                    "type": "array",
                    "description": "List of available tools to use in the plan",
                },
            },
        )

        # Review tools
        self.tool_registry.register_tool(
            name="analyze_output",
            description="Analyze agent output for correctness and completeness",
            parameters={
                "output": {"type": "string", "description": "Output to analyze"},
                "task_description": {
                    "type": "string",
                    "description": "Original task description",
                },
            },
        )

        self.tool_registry.register_tool(
            name="suggest_improvements",
            description="Suggest improvements to agent output",
            parameters={
                "output": {"type": "string", "description": "Output to improve"},
                "analysis": {"type": "string", "description": "Analysis of the output"},
            },
        )

    def register_agent(
        self,
        name: str,
        description: str,
        tools: set[str] | None = None,
        model_id: str = "gpt-3.5-turbo",
    ) -> Agent:
        """Register a new agent.

        Args:
            name: Agent name
            description: Agent description
            tools: Set of tool names the agent can use
            model_id: Model ID to use for the agent

        Returns:
            The registered agent
        """
        agent = Agent(
            name=name, description=description, tools=tools or set(), model_id=model_id
        )
        self.agents[name] = agent
        self.logger.info(f"Registered agent: {name}")
        return agent

    def unregister_agent(self, name: str) -> bool:
        """Unregister an agent.

        Args:
            name: Agent name

        Returns:
            True if the agent was unregistered, False if it wasn't registered
        """
        if name in self.agents:
            del self.agents[name]
            self.logger.info(f"Unregistered agent: {name}")
            return True
        return False

    def get_agent(self, name: str) -> Agent | None:
        """Get an agent by name.

        Args:
            name: Agent name

        Returns:
            Agent or None if not found
        """
        return self.agents.get(name)

    def list_agents(self) -> list[dict[str, Any]]:
        """List all registered agents.

        Returns:
            List of agent definitions
        """
        return [agent.to_dict() for agent in self.agents.values()]

    async def execute_agent(
        self, agent_name: str, task: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute a task with a specific agent.

        Args:
            agent_name: Name of the agent to use
            task: Task description
            context: Additional context for the task

        Returns:
            Agent execution result

        Raises:
            ValueError: If the agent doesn't exist
        """
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent not found: {agent_name}")

        if not self.client:
            raise ValueError("MCP client not initialized")

        # Update agent state
        agent.state = AgentState.RUNNING

        try:
            # Add task to agent memory
            agent.memory.add_message(
                "system", f"You are {agent.name}. {agent.description}"
            )
            agent.memory.add_message("user", task)

            # Get available tools for this agent
            available_tools = self.tool_registry.get_tools_for_agent(agent)

            # Create tool descriptions for the model
            tool_descriptions = []
            for tool in available_tools:
                tool_descriptions.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": {
                            "type": "object",
                            "properties": tool["parameters"],
                            "required": list(tool["parameters"].keys()),
                        },
                    },
                })

            # Create the request
            request_id = str(uuid.uuid4())
            request = MCPRequest(
                request_id=request_id,
                model_id=agent.model_id,
                operation=MCPOperationType.CHAT,
                inputs={
                    "messages": agent.memory.get_context(),
                },
                parameters={
                    "tools": tool_descriptions,
                    "temperature": 0.7,
                },
            )

            # Send the request to the server
            response = await self.client.request(request)

            # Process the response
            if response.status == MCPStatusCode.SUCCESS:
                if "tool_calls" in response.outputs:
                    # Handle tool calls
                    tool_calls = response.outputs["tool_calls"]
                    results = await self._execute_tool_calls(agent, tool_calls)

                    # Add tool results to memory
                    for result in results:
                        agent.memory.add_message("function", json.dumps(result))

                    # Get final response after tool execution
                    final_response = await self._get_final_response(agent)
                    agent.memory.add_message("assistant", final_response)

                    result = {
                        "status": "success",
                        "agent": agent_name,
                        "response": final_response,
                        "tools_used": [r["name"] for r in results],
                    }
                else:
                    # Direct response
                    content = response.outputs.get("content", "")
                    agent.memory.add_message("assistant", content)

                    result = {
                        "status": "success",
                        "agent": agent_name,
                        "response": content,
                        "tools_used": [],
                    }
            else:
                # Handle error
                error_msg = response.error or "Unknown error"
                agent.memory.add_message("system", f"Error: {error_msg}")

                result = {"status": "error", "agent": agent_name, "error": error_msg}

                agent.state = AgentState.FAILED
                return result

            # Update agent state
            agent.state = AgentState.COMPLETED
            return result

        except Exception as e:
            self.logger.error(f"Error executing agent {agent_name}: {e}")
            agent.state = AgentState.FAILED
            return {"status": "error", "agent": agent_name, "error": str(e)}

    async def _execute_tool_calls(
        self, agent: Agent, tool_calls: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Execute tool calls for an agent.

        Args:
            agent: Agent executing the tools
            tool_calls: List of tool calls to execute

        Returns:
            List of tool results
        """
        results = []

        for call in tool_calls:
            tool_name = call.get("name", "")
            arguments = call.get("arguments", {})

            # Check if the agent has access to this tool
            if tool_name not in agent.tools:
                self.logger.warning(
                    f"Agent {agent.name} doesn't have access to tool {tool_name}"
                )
                results.append({
                    "name": tool_name,
                    "result": {"error": f"Access denied to tool {tool_name}"},
                    "success": False,
                })
                continue

            # Get the tool definition
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                self.logger.warning(f"Tool not found: {tool_name}")
                results.append({
                    "name": tool_name,
                    "result": {"error": f"Tool not found: {tool_name}"},
                    "success": False,
                })
                continue

            try:
                # Create an MCP request for the tool
                request_id = str(uuid.uuid4())
                request = MCPRequest(
                    request_id=request_id,
                    model_id=agent.model_id,
                    operation=MCPOperationType.CHAT,
                    inputs={
                        "messages": [
                            {
                                "role": "user",
                                "content": f"{tool_name}: {json.dumps(arguments)}",
                            }
                        ]
                    },
                )

                # Execute the tool
                if self.client is None:
                    raise ValueError("MCP client not initialized")
                response = await self.client.request(request)

                # Process the response
                if response.status == MCPStatusCode.SUCCESS:
                    result = response.outputs
                    success = True
                else:
                    result = {"error": response.error or "Unknown error"}
                    success = False

                # Record tool usage in memory
                agent.memory.add_tool_usage(tool_name, arguments, result, success)

                # Add to results
                results.append({
                    "name": tool_name,
                    "result": result,
                    "success": success,
                })

            except Exception as e:
                self.logger.error(f"Error executing tool {tool_name}: {e}")
                results.append({
                    "name": tool_name,
                    "result": {"error": str(e)},
                    "success": False,
                })

        return results

    async def _get_final_response(self, agent: Agent) -> str:
        """Get final response after tool execution.

        Args:
            agent: Agent to get response for

        Returns:
            Final response text
        """
        if not self.client:
            return "Error: MCP client not initialized"

        # Create the request
        request_id = str(uuid.uuid4())
        request = MCPRequest(
            request_id=request_id,
            model_id=agent.model_id,
            operation=MCPOperationType.CHAT,
            inputs={
                "messages": agent.memory.get_context(),
            },
        )

        # Send the request to the server
        response = await self.client.request(request)

        # Process the response
        if response.status == MCPStatusCode.SUCCESS:
            return response.outputs.get("content", "")
        else:
            return f"Error: {response.error or 'Unknown error'}"

    async def execute_workflow(
        self, task: str, workflow: list[str] | None = None
    ) -> dict[str, Any]:
        """Execute a multi-agent workflow for a task.

        Args:
            task: Task description
            workflow: List of agent names to execute in sequence

        Returns:
            Workflow execution result
        """
        if not workflow:
            # Default workflow: planner -> executor -> critic
            workflow = ["planner", "executor", "critic"]

        results = []
        task_context = {"original_task": task}
        current_task = task

        for i, agent_name in enumerate(workflow):
            # Execute the agent
            self.logger.info(f"Executing agent {agent_name} ({i + 1}/{len(workflow)})")
            result = await self.execute_agent(agent_name, current_task, task_context)
            results.append(result)

            # Update context and task for next agent
            if result["status"] == "success":
                if agent_name == "planner" and "response" in result:
                    task_context["plan"] = result["response"]
                    current_task = (
                        f"Execute this plan to complete the original task: "
                        f"{result['response']}\n\nOriginal task: {task}"
                    )
                elif agent_name == "executor" and "response" in result:
                    task_context["execution_result"] = result["response"]
                    current_task = (
                        f"Review this output and suggest improvements if needed: "
                        f"{result['response']}\n\nIt was produced for this task: {task}"
                    )
            else:
                # Handle error
                self.logger.error(
                    f"Workflow failed at agent {agent_name}: {result.get('error')}"
                )
                return {
                    "status": "error",
                    "error": f"Workflow failed at agent {agent_name}: {result.get('error')}",
                    "results": results,
                }

        return {
            "status": "success",
            "results": results,
            "final_output": results[-1].get("response", ""),
        }
