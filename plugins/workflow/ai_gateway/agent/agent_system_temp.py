"""Simplified agent system example."""

import asyncio
import logging
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class AgentContext:
    """Simple agent context."""

    def __init__(self, session_id=None):
        self.session_id = session_id or str(uuid.uuid4())
        self.data = {}


class Task:
    """Simple task definition."""

    def __init__(self, objective, parameters=None):
        self.objective = objective
        self.parameters = parameters or {}
        self.result = None
        self.status = "pending"
        self.error = None

    def complete(self, result):
        """Mark task as complete."""
        self.result = result
        self.status = "completed"

    def fail(self, error):
        """Mark task as failed."""
        self.error = str(error)
        self.status = "failed"


class BaseAgent:
    """Base agent implementation."""

    def __init__(self, agent_id, agent_type, name="Generic Agent"):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.name = name

    async def execute(self, task, context):
        """Execute a task."""
        try:
            # Mock implementation
            task.complete({
                "response": {
                    "content": f"Response from {self.name} to: {task.objective}"
                }
            })
            return True
        except Exception as e:
            task.fail(e)
            return False


class AgentRegistry:
    """Simple agent registry."""

    def __init__(self):
        self.agents = {}

    async def create_agent(self, agent_id, agent_type, config=None):
        """Create an agent."""
        config = config or {}
        agent = BaseAgent(agent_id, agent_type, config.get("name", agent_type))
        self.agents[agent_id] = agent
        logger.info(f"Created agent: {agent_id} ({agent_type})")
        return agent

    async def get_agent(self, agent_id):
        """Get an agent by ID."""
        return self.agents.get(agent_id)


async def run_examples():
    """Run simplified examples."""
    # Create registry
    registry = AgentRegistry()

    # Create an agent
    assistant = await registry.create_agent(
        "assistant-1", "assistant", {"name": "Test Assistant"}
    )

    # Create session and context
    session_id = "test-session"
    context = AgentContext(session_id)

    # Create and execute a task
    task = Task(
        objective="Answer a test question",
        parameters={"query": "What is this test about?"},
    )

    # Execute task
    logger.info(f"Executing task: {task.objective}")
    await assistant.execute(task, context)

    # Check result
    if task.status == "completed" and task.result:
        logger.info(f"Task completed: {task.result}")
    else:
        logger.error(f"Task failed: {task.error}")


async def main():
    """Run the example."""
    try:
        await run_examples()
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
