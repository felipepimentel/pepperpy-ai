"""Agent system example.

This module demonstrates the usage of the agent system components.
"""

import asyncio
import logging

from .base import AgentContext, Task, TaskStatus
from .registry import AgentRegistry
from .specialized import (
    AssistantAgent,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def create_example_agents(registry: AgentRegistry) -> dict[str, str]:
    """Create example agents.

    Args:
        registry: Agent registry

    Returns:
        Dictionary mapping agent names to IDs
    """
    agent_ids = {}

    # Create assistant agent
    assistant = await registry.create_agent(
        "assistant-1",
        "assistant",
        {
            "name": "General Assistant",
            "model_id": "gpt-4",
            "description": "General-purpose AI assistant for answering questions",
            "system_prompt": "You are a helpful, harmless, and honest AI assistant.",
        },
    )
    if assistant:
        agent_ids["assistant"] = assistant.agent_id

    # Create RAG agent
    rag_agent = await registry.create_agent(
        "rag-1",
        "rag",
        {
            "name": "Knowledge Agent",
            "model_id": "gpt-4",
            "description": "Retrieval-augmented generation agent for answering questions with knowledge base",
            "vector_store_id": "chromadb",
            "max_documents": 5,
        },
    )
    if rag_agent:
        agent_ids["rag"] = rag_agent.agent_id

    # Create tool agent
    tool_agent = await registry.create_agent(
        "tool-1",
        "tool",
        {
            "name": "Tool Agent",
            "model_id": "gpt-4",
            "description": "Agent that can use external tools",
            "available_tools": [
                {
                    "name": "calculator",
                    "description": "Perform mathematical calculations",
                    "parameters": {
                        "operation": {
                            "type": "string",
                            "enum": ["add", "subtract", "multiply", "divide"],
                            "description": "The operation to perform",
                        },
                        "a": {
                            "type": "number",
                            "description": "First operand",
                        },
                        "b": {
                            "type": "number",
                            "description": "Second operand",
                        },
                    },
                },
                {
                    "name": "weather",
                    "description": "Get weather information for a location",
                    "parameters": {
                        "location": {
                            "type": "string",
                            "description": "The location to get weather for",
                        },
                    },
                },
            ],
        },
    )
    if tool_agent:
        agent_ids["tool"] = tool_agent.agent_id

    # Create planning agent
    planning_agent = await registry.create_agent(
        "planner-1",
        "planning",
        {
            "name": "Planner",
            "model_id": "gpt-4",
            "description": "Planning agent for complex tasks",
        },
    )
    if planning_agent:
        agent_ids["planning"] = planning_agent.agent_id

    # Create orchestrator
    orchestrator = await registry.create_agent(
        "orchestrator-1",
        "orchestrator",
        {
            "name": "Orchestrator",
            "description": "Coordinates multi-agent workflows",
        },
    )
    if orchestrator:
        agent_ids["orchestrator"] = orchestrator.agent_id

    return agent_ids


async def assistant_example(registry: AgentRegistry, session_id: str) -> None:
    """Run assistant agent example.

    Args:
        registry: Agent registry
        session_id: Session ID
    """
    logger.info("Running assistant agent example")

    # Get assistant agent
    assistant = await registry.get_agent("assistant-1")
    if not assistant:
        logger.error("Assistant agent not found")
        return

    # Create context
    context = AgentContext(session_id=session_id)

    # Get system prompt from the assistant if it's an AssistantAgent
    system_prompt = "You are a helpful assistant."
    if isinstance(assistant, AssistantAgent):
        system_prompt = assistant.system_prompt

    # Create task
    task = Task(
        objective="Answer a question",
        parameters={
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "What is artificial intelligence?"},
            ]
        },
    )

    # Process task
    logger.info("Sending question to assistant")
    await assistant.execute(task, context)

    # Check result
    if task.status == TaskStatus.COMPLETED and task.result:
        response = task.result.get("response", {})
        content = response.get("content", "No content returned")
        logger.info(f"Assistant response: {content}")
    else:
        logger.error(f"Task failed: {task.error}")


async def rag_example(registry: AgentRegistry, session_id: str) -> None:
    """Run RAG agent example.

    Args:
        registry: Agent registry
        session_id: Session ID
    """
    logger.info("Running RAG agent example")

    # Get RAG agent
    rag_agent = await registry.get_agent("rag-1")
    if not rag_agent:
        logger.error("RAG agent not found")
        return

    # Create context
    context = AgentContext(session_id=session_id)

    # Create task
    task = Task(
        objective="Answer a question using knowledge base",
        parameters={
            "query": "What are the key components of a transformer architecture?",
            "max_documents": 3,
        },
    )

    # Process task
    logger.info("Sending question to RAG agent")
    await rag_agent.execute(task, context)

    # Check result
    if task.status == TaskStatus.COMPLETED and task.result:
        response = task.result.get("response", {})
        content = response.get("content", "No content returned")
        logger.info(f"RAG agent response: {content}")

        # Show retrieved documents
        documents = task.result.get("documents", [])
        logger.info(f"Retrieved {len(documents)} documents")
        for i, doc in enumerate(documents):
            logger.info(
                f"Document {i + 1}: {doc.get('id')} (score: {doc.get('score')})"
            )
    else:
        logger.error(f"Task failed: {task.error}")


async def tool_example(registry: AgentRegistry, session_id: str) -> None:
    """Run tool agent example.

    Args:
        registry: Agent registry
        session_id: Session ID
    """
    logger.info("Running tool agent example")

    # Get tool agent
    tool_agent = await registry.get_agent("tool-1")
    if not tool_agent:
        logger.error("Tool agent not found")
        return

    # Create context
    context = AgentContext(session_id=session_id)

    # Create task
    task = Task(
        objective="Use calculator tool",
        parameters={
            "messages": [
                {"role": "user", "content": "Calculate 24 * 7"},
            ]
        },
    )

    # Process task
    logger.info("Sending calculation request to tool agent")
    await tool_agent.execute(task, context)

    # Check result
    if task.status == TaskStatus.COMPLETED and task.result:
        response = task.result.get("response", {})
        content = response.get("content", "No content returned")
        logger.info(f"Tool agent response: {content}")

        # Show tool calls
        tool_calls = task.result.get("tool_calls", [])
        logger.info(f"Made {len(tool_calls)} tool calls")
        for i, call in enumerate(tool_calls):
            logger.info(
                f"Tool call {i + 1}: {call.get('name')} - Args: {call.get('arguments')}"
            )
            logger.info(f"Result: {call.get('result')}")
    else:
        logger.error(f"Task failed: {task.error}")


async def planning_example(registry: AgentRegistry, session_id: str) -> None:
    """Run planning agent example.

    Args:
        registry: Agent registry
        session_id: Session ID
    """
    logger.info("Running planning agent example")

    # Get planning agent
    planning_agent = await registry.get_agent("planner-1")
    if not planning_agent:
        logger.error("Planning agent not found")
        return

    # Create context
    context = AgentContext(session_id=session_id)

    # Create task
    task = Task(
        objective="Create a plan for a research project",
        parameters={
            "project_topic": "Renewable energy adoption barriers",
            "timeframe": "3 months",
            "resources": ["2 researchers", "limited budget"],
        },
    )

    # Process task
    logger.info("Sending planning request to planning agent")
    await planning_agent.execute(task, context)

    # Check result
    if task.status == TaskStatus.COMPLETED and task.result:
        plan = task.result.get("plan", [])
        logger.info(f"Planning agent created a plan with {len(plan)} steps")
        for i, step in enumerate(plan):
            logger.info(
                f"Step {step.get('step')}: {step.get('action')} - Status: {step.get('status')}"
            )

        conclusion = task.result.get("conclusion", "")
        logger.info(f"Conclusion: {conclusion}")
    else:
        logger.error(f"Task failed: {task.error}")


async def orchestrator_example(registry: AgentRegistry, session_id: str) -> None:
    """Run orchestrator example.

    Args:
        registry: Agent registry
        session_id: Session ID
    """
    logger.info("Running orchestrator example")

    # Get orchestrator
    orchestrator = await registry.get_agent("orchestrator-1")
    if not orchestrator:
        logger.error("Orchestrator not found")
        return

    # Create context
    context = AgentContext(session_id=session_id)

    # Add agents to context for orchestrator to use
    for agent_id in ["assistant-1", "rag-1", "tool-1"]:
        agent = await registry.get_agent(agent_id)
        if agent:
            await context.set(f"agent:{agent_id}", agent)

    # Create task
    task = Task(
        objective="Execute multi-agent workflow",
        parameters={
            "workflow_name": "research_and_summarize",
            "query": "Explain the impact of climate change on agriculture",
            "max_results": 3,
        },
    )

    # Process task
    logger.info("Sending workflow request to orchestrator")
    await orchestrator.execute(task, context)

    # Check result
    if task.status == TaskStatus.COMPLETED and task.result:
        workflow_result = task.result.get("status", "")
        logger.info(f"Workflow execution status: {workflow_result}")

        contributions = task.result.get("agent_contributions", [])
        logger.info(f"Agents involved: {len(contributions)}")
        for contribution in contributions:
            logger.info(
                f"Agent {contribution.get('agent_id')}: {contribution.get('result')}"
            )

        conclusion = task.result.get("conclusion", "")
        logger.info(f"Conclusion: {conclusion}")
    else:
        logger.error(f"Task failed: {task.error}")


async def run_examples() -> None:
    """Run all examples."""
    # Create registry
    registry = AgentRegistry()

    try:
        # Initialize registry
        await registry.initialize({})

        # Create example agents
        session_id = "example-session"
        agent_ids = await create_example_agents(registry)
        logger.info(f"Created agents: {agent_ids}")

        # Run examples
        await assistant_example(registry, session_id)
        await rag_example(registry, session_id)
        await tool_example(registry, session_id)
        await planning_example(registry, session_id)
        await orchestrator_example(registry, session_id)

    finally:
        # Clean up
        await registry.shutdown()


async def main() -> None:
    """Main function."""
    try:
        await run_examples()
    except Exception as e:
        logger.exception(f"Error during example execution: {e!s}")


if __name__ == "__main__":
    asyncio.run(main())
