"""Simplified agent demo for MCP workflow testing."""

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


# Simple Protocol for client providers
@runtime_checkable
class ClientProvider(Protocol):
    """Protocol for any MCP client provider."""

    initialized: bool

    async def initialize(self) -> None:
        """Initialize the client."""
        ...

    async def request(self, request: Any) -> Any:
        """Execute a request."""
        ...


# Simplified client implementation
class SimulatedClient:
    """Simulated client for local testing."""

    def __init__(self) -> None:
        """Initialize the client."""
        self.initialized = False
        print("Simulated client initialized")

    async def initialize(self) -> None:
        """Initialize the client."""
        self.initialized = True

    async def request(self, request: Any) -> Any:
        """Execute a request."""
        # Just echo the request with a mock response
        return {
            "status": "success",
            "result": f"Processed: {request.get('operation', 'unknown')}",
            "content": f"This is a simulated response for: {json.dumps(request, default=str)}",
        }


# Simple Agent implementation
@dataclass
class Agent:
    """Agent that can execute tasks using tools."""

    agent_id: str
    name: str
    description: str
    systemPrompt: str = ""
    tools: set[str] = field(default_factory=set)

    def to_dict(self) -> dict[str, Any]:
        """Convert agent to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "systemPrompt": self.systemPrompt,
            "tools": list(self.tools),
        }


# Event for memory storage
@dataclass
class Event:
    """Memory event."""

    agent_name: str
    content: str
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time())


# Memory for the orchestrator
@dataclass
class Memory:
    """Simple memory store."""

    events: list[Event] = field(default_factory=list)

    def add_event(self, agent_name: str, content: str) -> None:
        """Add an event to memory."""
        self.events.append(Event(agent_name=agent_name, content=content))


# Agent Orchestrator
class AgentOrchestrator:
    """Orchestrates multiple agents to complete tasks."""

    def __init__(self, client: Any = None) -> None:
        """Initialize the agent orchestrator.

        Args:
            client: MCP client provider
        """
        self.client = client
        self.agents = {}
        self.initialized = False

    def register_agent(self, agent: Agent) -> None:
        """Register an agent.

        Args:
            agent: The agent to register
        """
        self.agents[agent.agent_id] = agent
        print(f"Registered agent: {agent.name} ({agent.agent_id})")

    async def execute_agent(
        self, agent_id: str, operation: str, input_text: str
    ) -> str:
        """Execute an agent operation.

        Args:
            agent_id: The agent ID
            operation: The operation to perform
            input_text: The input text

        Returns:
            Operation result
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return f"Agent not found: {agent_id}"

        # Create a request
        request = {
            "agent_id": agent_id,
            "operation": operation,
            "input": input_text,
            "system_prompt": agent.systemPrompt,
        }

        # Execute the request
        if self.client:
            response = await self.client.request(request)
            return response.get("content", "No content returned")
        else:
            return f"Simulated response from {agent.name}: Processed {operation} on: {input_text}"

    async def run_workflow(self, workflow: list[dict[str, Any]]) -> Memory:
        """Run a workflow of agent operations.

        Args:
            workflow: List of workflow steps

        Returns:
            Memory with workflow results
        """
        memory = Memory()

        for step in workflow:
            # Use safe defaults for any missing values
            agent_id = step.get("agent_id", "")
            if not agent_id:
                print("⚠️ Skipping step with missing agent_id")
                continue

            operation = step.get("operation", "")
            if not operation:
                print(f"⚠️ Skipping step for {agent_id} with missing operation")
                continue

            input_text = step.get("input", "")

            print(f"\n➡️ Executing {operation} with {agent_id}")
            result = await self.execute_agent(agent_id, operation, input_text)

            # Get the agent or create a placeholder if not found
            agent = self.agents.get(agent_id)
            if agent:
                agent_name = agent.name
            else:
                agent_name = f"Unknown-{agent_id}"

            memory.add_event(agent_name, result)
            print(f"✅ {agent_name} completed {operation}")

        return memory


async def run_agent_demo(
    task: str = "Research top 5 AI trends for healthcare in 2025",
) -> None:
    """Run the agent demo with a simulated client.

    Args:
        task: The task description to give to the agent
    """
    # Create a simulated client
    client = SimulatedClient()
    await client.initialize()

    # Create the agent orchestrator - no model_id parameter
    orchestrator = AgentOrchestrator(client=client)

    # Define our agents
    planner = Agent(
        agent_id="planner",
        name="Planner",
        description="Creates plans for complex tasks",
        systemPrompt="You are a specialized planner that breaks down complex tasks into actionable steps.",
    )

    researcher = Agent(
        agent_id="researcher",
        name="Researcher",
        description="Conducts research on topics",
        systemPrompt="You are a specialized researcher that gathers information on specific topics.",
    )

    reviewer = Agent(
        agent_id="reviewer",
        name="Reviewer",
        description="Reviews and critiques work",
        systemPrompt="You are a specialized reviewer that provides constructive feedback on completed work.",
    )

    # Register agents
    orchestrator.register_agent(planner)
    orchestrator.register_agent(researcher)
    orchestrator.register_agent(reviewer)

    # Run the workflow
    print(f"\n📋 Starting agent workflow for task: {task}\n")
    memory = await orchestrator.run_workflow(
        workflow=[
            {"agent_id": "planner", "operation": "analyze_task", "input": task},
            {"agent_id": "researcher", "operation": "research", "input": task},
            {
                "agent_id": "reviewer",
                "operation": "review",
                "input": "Review the research results",
            },
        ]
    )

    # Print the results
    print("\n🎉 Agent workflow complete! Results:\n")
    for event in memory.events:
        print(f"📌 {event.agent_name} ({event.timestamp}):")
        print(f"   {event.content}\n")


async def main() -> None:
    """Run the agent demo."""
    import argparse

    parser = argparse.ArgumentParser(description="Run the Agent Orchestration Demo")
    parser.add_argument(
        "--task",
        type=str,
        default="Research top 5 AI trends for healthcare in 2025",
        help="The task to run the agent demo with",
    )

    args = parser.parse_args()
    await run_agent_demo(task=args.task)


if __name__ == "__main__":
    asyncio.run(main())
