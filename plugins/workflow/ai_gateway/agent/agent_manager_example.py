"""Agent manager example.

This module demonstrates how to use the agent manager for persistent agent
management across sessions.
"""

import asyncio
import logging
import sys
import tempfile

from .base import AgentCapability, Task, TaskStatus
from .manager import AgentManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def create_and_use_manager() -> None:
    """Create and use an agent manager."""
    # Create a temporary directory for agent storage
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Using temporary storage directory: {temp_dir}")

        # Create agent manager
        manager = AgentManager(
            storage_dir=temp_dir,
            memory_type="hierarchical",
            auto_save=True,
            save_interval=5,  # 5 seconds for demo
        )

        # Initialize manager
        await manager.initialize()

        try:
            # Create some agents
            await create_example_agents(manager)

            # Create a session
            session_id = "example-session"
            context = await manager.create_session(session_id)

            # Execute tasks with different agents
            await run_agent_tasks(manager, session_id)

            # Show persistence by simulating restart
            await demonstrate_persistence(temp_dir)

        finally:
            # Shut down manager
            await manager.shutdown()


async def create_example_agents(manager: AgentManager) -> dict[str, str]:
    """Create example agents.

    Args:
        manager: Agent manager

    Returns:
        Dictionary of agent IDs
    """
    agent_ids = {}

    # Create assistant agent
    assistant = await manager.create_agent(
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
        logger.info(f"Created assistant agent: {assistant.agent_id}")

    # Create RAG agent
    rag_agent = await manager.create_agent(
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
        logger.info(f"Created RAG agent: {rag_agent.agent_id}")

    # Create tool agent
    tool_agent = await manager.create_agent(
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
            ],
        },
    )
    if tool_agent:
        agent_ids["tool"] = tool_agent.agent_id
        logger.info(f"Created tool agent: {tool_agent.agent_id}")

    # Show available agent types
    agent_types = await manager.get_agent_types()
    logger.info(f"Available agent types: {agent_types}")

    return agent_ids


async def run_agent_tasks(manager: AgentManager, session_id: str) -> None:
    """Run tasks with different agents.

    Args:
        manager: Agent manager
        session_id: Session ID
    """
    # Run task with assistant agent
    task1 = Task(
        objective="Answer a question",
        parameters={
            "messages": [
                {"role": "user", "content": "What is artificial intelligence?"},
            ]
        },
    )

    logger.info("Running task with assistant agent")
    result1 = await manager.process_task(task1, session_id, "assistant-1")

    if result1.status == TaskStatus.COMPLETED and result1.result:
        logger.info(f"Task completed: {result1.objective}")
        if isinstance(result1.result, dict):
            content = result1.result.get("response", {}).get("content", "No content")
            logger.info(f"Response: {content[:100]}...")
    else:
        logger.error(f"Task failed: {result1.error}")

    # Run task with RAG agent
    task2 = Task(
        objective="Research topic",
        parameters={
            "query": "What are transformer neural networks?",
            "max_documents": 3,
        },
        required_capabilities=[AgentCapability.RAG],
    )

    logger.info("Running task with RAG agent")
    result2 = await manager.process_task(task2, session_id)

    if result2.status == TaskStatus.COMPLETED and result2.result:
        logger.info(f"Task completed: {result2.objective}")
        logger.info(f"Agent used: {result2.agent_id}")
    else:
        logger.error(f"Task failed: {result2.error}")

    # Update agent configuration
    logger.info("Updating assistant agent configuration")
    await manager.update_agent_config(
        "assistant-1",
        {
            "system_prompt": "You are a friendly and helpful AI assistant.",
            "max_history_length": 20,
        },
    )

    # Get agent configuration
    assistant_config = await manager.get_agent_config("assistant-1")
    if assistant_config:
        logger.info(f"Updated assistant config: {assistant_config}")


async def demonstrate_persistence(storage_dir: str) -> None:
    """Demonstrate agent persistence across manager restarts.

    Args:
        storage_dir: Storage directory
    """
    logger.info("\n=== Simulating manager restart ===\n")

    # Create new manager instance with same storage
    new_manager = AgentManager(
        storage_dir=storage_dir,
        auto_save=False,  # Disable auto-save for demo
    )

    # Initialize manager (will load agents from storage)
    await new_manager.initialize()

    try:
        # Get available agents
        agent_ids = await new_manager.registry.get_agent_ids()
        logger.info(f"Loaded agents after restart: {agent_ids}")

        # Get agent details
        for agent_id in agent_ids:
            agent = await new_manager.get_agent(agent_id)
            if agent:
                logger.info(f"Agent {agent_id}: {agent.name}")

        # Create new session
        new_session = "new-session"
        await new_manager.create_session(new_session)

        # Run task with existing agent
        if "assistant-1" in agent_ids:
            task = Task(
                objective="Verify persistence",
                parameters={
                    "messages": [
                        {"role": "user", "content": "Tell me about persistence."},
                    ]
                },
            )

            logger.info("Running task with persisted agent")
            result = await new_manager.process_task(task, new_session, "assistant-1")

            if result.status == TaskStatus.COMPLETED and result.result:
                logger.info("Task completed with persisted agent")
    finally:
        # Shut down manager
        await new_manager.shutdown()


async def main() -> None:
    """Main function."""
    try:
        await create_and_use_manager()
    except Exception as e:
        logger.exception(f"Error in example: {e!s}")


if __name__ == "__main__":
    asyncio.run(main())
