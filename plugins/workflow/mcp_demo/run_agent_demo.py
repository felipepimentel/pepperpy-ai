#!/usr/bin/env python3
"""Agent Orchestration Demo Runner.

This script demonstrates the agent orchestration capabilities by simulating a workflow.
"""

import asyncio
import os
import sys
from typing import Any, Protocol

# Add the project root to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# Import or define ClientProvider Protocol
class ClientProvider(Protocol):
    """Protocol for MCP client providers."""

    async def initialize(self) -> None:
        """Initialize the client provider."""
        ...

    async def execute(self, request: Any) -> Any:
        """Execute a request through the client provider."""
        ...


# Import our agent orchestration components
from plugins.workflow.mcp_demo.agent_orchestration import AgentOrchestrator

# Import or define protocol types
try:
    from pepperpy.mcp.protocol import MCPResponse, MCPStatusCode
except ImportError:
    from plugins.workflow.mcp_demo.protocol import MCPResponse, MCPStatusCode


class SimulatedClient(ClientProvider):
    """Simulated MCP client for demo purposes."""

    def __init__(self) -> None:
        """Initialize the simulated client."""
        self.initialized = False
        self.tools = {}

    async def initialize(self) -> None:
        """Initialize the client."""
        self.initialized = True
        print("Simulated client initialized")

    async def execute(self, request: Any) -> Any:
        """Simulate executing a request."""
        request_id = request.request_id
        model_id = request.model_id
        operation = request.operation
        inputs = request.inputs

        # Simulate a response based on the inputs
        if "messages" in inputs:
            messages = inputs["messages"]
            last_message = messages[-1] if messages else {"content": ""}
            content = last_message.get("content", "")

            # Simulate different types of responses
            if "analyze_task" in content or "create_plan" in content:
                return MCPResponse(
                    request_id=request_id,
                    model_id=model_id,
                    status=MCPStatusCode.SUCCESS,
                    outputs={
                        "content": "Based on my analysis, this task can be broken down into 3 steps:\n"
                        "1. Research current AI trends in healthcare\n"
                        "2. Identify the most promising applications\n"
                        "3. Compile a list of the top 5 trends with brief descriptions"
                    },
                )
            elif "execute" in content or "research" in content:
                return MCPResponse(
                    request_id=request_id,
                    model_id=model_id,
                    status=MCPStatusCode.SUCCESS,
                    outputs={
                        "content": "Based on my research, here are the top 5 AI trends for healthcare in 2025:\n\n"
                        "1. AI-powered diagnostic imaging tools\n"
                        "2. Personalized medicine through genomic analysis\n"
                        "3. Remote patient monitoring with smart wearables\n"
                        "4. AI-assisted surgical robots\n"
                        "5. Predictive analytics for preventive care"
                    },
                )
            elif "review" in content or "suggest" in content:
                return MCPResponse(
                    request_id=request_id,
                    model_id=model_id,
                    status=MCPStatusCode.SUCCESS,
                    outputs={
                        "content": "The list is well-structured and covers important trends. To improve it, consider adding:\n\n"
                        "- Brief explanations for each trend\n"
                        "- Potential implementation challenges\n"
                        "- Expected timeframes for widespread adoption"
                    },
                )
            else:
                # Generic response
                return MCPResponse(
                    request_id=request_id,
                    model_id=model_id,
                    status=MCPStatusCode.SUCCESS,
                    outputs={
                        "content": f"I've processed your request about: {content[:50]}..."
                    },
                )

        # Fallback
        return MCPResponse(
            request_id=request_id,
            model_id=model_id,
            status=MCPStatusCode.SUCCESS,
            outputs={"content": "Task completed successfully."},
        )


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

    # Create the agent orchestrator
    orchestrator = AgentOrchestrator(
        client=client,
        model_id="gpt-3.5-turbo",
    )

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
