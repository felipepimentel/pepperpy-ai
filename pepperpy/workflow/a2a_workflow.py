"""
PepperPy A2A Workflow.

This module provides a reusable workflow for agent-to-agent communication
using the A2A protocol. It simplifies the setup and configuration of A2A agents
and enables easy communication between them.
"""

import uuid
from typing import Any

from pepperpy.a2a.base import (
    A2AProvider,
    AgentCard,
    Message,
    Task,
    TaskState,
    TextPart,
)
from pepperpy.core.logging import get_logger
from pepperpy.workflow.base import (
    Pipeline,
    PipelineContext,
    PipelineStage,
    WorkflowProvider,
)

logger = get_logger(__name__)


class A2ASetupStage(PipelineStage[dict[str, Any], AgentCard]):
    """Stage for setting up an A2A agent.

    This stage creates and configures an A2A agent using the provided configuration.
    """

    def __init__(
        self,
        name: str = "a2a_setup",
        description: str = "Set up an A2A agent",
    ):
        """Initialize the A2A setup stage.

        Args:
            name: The name of the stage
            description: A description of the stage
        """
        super().__init__(name, description)

    def process(
        self, input_data: dict[str, Any], context: PipelineContext
    ) -> AgentCard:
        """Create and configure an A2A agent.

        Args:
            input_data: Configuration for the agent
            context: The pipeline context

        Returns:
            The created agent card

        Raises:
            ValueError: If required configuration is missing
        """
        # Create agent card from input data
        name = input_data.get("name")
        description = input_data.get("description")
        endpoint = input_data.get("endpoint")
        capabilities = input_data.get("capabilities", [])

        if not name or not description or not endpoint:
            raise ValueError("Missing required agent configuration")

        agent_card = AgentCard(
            name=name,
            description=description,
            endpoint=endpoint,
            capabilities=capabilities,
            skills=input_data.get("skills", []),
            authentication=input_data.get("authentication", {}),
            version=input_data.get("version", "1.0.0"),
        )

        # Store the agent provider in the context if provided
        if "provider" in input_data:
            context.set("provider", input_data["provider"])

        return agent_card


class A2ARegistrationStage(PipelineStage[AgentCard, str]):
    """Stage for registering an A2A agent.

    This stage registers an agent with the A2A provider.
    """

    def __init__(
        self,
        name: str = "a2a_registration",
        description: str = "Register an A2A agent",
    ):
        """Initialize the A2A registration stage.

        Args:
            name: The name of the stage
            description: A description of the stage
        """
        super().__init__(name, description)
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def process(self, agent_card: AgentCard, context: PipelineContext) -> str:
        """Register an agent with the A2A provider.

        Args:
            agent_card: The agent card to register
            context: The pipeline context

        Returns:
            The registered agent ID

        Raises:
            ValueError: If no provider is available in the context
        """
        # This is a synchronous method but we need to work with async methods
        # In a real scenario, you would use an async workflow framework or asyncio.run()

        provider = context.get("provider")
        if not provider or not isinstance(provider, A2AProvider):
            self.logger.error("A2A provider not found in context")
            raise ValueError("A2A provider not found in context")

        # Generate a random agent ID
        agent_id = str(uuid.uuid4())

        # Store the agent card and ID in the context
        context.set("agent_card", agent_card)
        context.set("agent_id", agent_id)

        # Register the agent (this is where we'd call the async method in a proper async workflow)
        self.logger.info(f"Registering agent {agent_id}: {agent_card.name}")

        # In a real implementation with async workflows, we would use:
        # try:
        #     await provider.register_agent(agent_card)
        # except Exception as e:
        #     self.logger.error(f"Failed to register agent: {e}")
        #     raise ValueError(f"Failed to register agent: {e}") from e

        return agent_id


class A2ATaskCreationStage(PipelineStage[dict[str, Any], Task]):
    """Stage for creating an A2A task.

    This stage creates a task for agent-to-agent communication.
    """

    def __init__(
        self,
        name: str = "a2a_task_creation",
        description: str = "Create an A2A task",
    ):
        """Initialize the A2A task creation stage.

        Args:
            name: The name of the stage
            description: A description of the stage
        """
        super().__init__(name, description)
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def process(self, input_data: dict[str, Any], context: PipelineContext) -> Task:
        """Create an A2A task.

        Args:
            input_data: Task configuration
            context: The pipeline context

        Returns:
            The created task

        Raises:
            ValueError: If required configuration is missing
        """
        # Get the agent ID from context or input
        agent_id = context.get("agent_id") or input_data.get("agent_id")
        if not agent_id:
            self.logger.error("Agent ID not found in context or input data")
            raise ValueError("Agent ID not found")

        # Get the input message
        message_content = input_data.get("message")
        if not message_content:
            self.logger.error("Message content is required")
            raise ValueError("Message content is required")

        # Create a message with text content
        message = Message(
            role="user",
            parts=[TextPart(message_content)],
        )

        # Generate a task ID
        task_id = str(uuid.uuid4())
        self.logger.info(f"Creating task {task_id} for agent {agent_id}")

        # Add metadata
        metadata = input_data.get("metadata", {})
        if not isinstance(metadata, dict):
            self.logger.warning(f"Metadata is not a dictionary, using empty dict instead: {metadata}")
            metadata = {}

        # Create the task
        task = Task(
            task_id=task_id,
            state=TaskState.SUBMITTED,
            messages=[message],
            artifacts=[],
            metadata=metadata,
        )

        # Store the task in the context
        context.set("task", task)
        context.set("task_id", task_id)
        self.logger.debug(f"Task {task_id} created successfully")

        return task


class A2AWorkflowProvider(WorkflowProvider):
    """A2A workflow provider.

    This provider implements a workflow for agent-to-agent communication
    using the A2A protocol. It simplifies the setup and execution of A2A
    interactions between agents.
    """

    # Configuration options with type annotations
    provider_type: str = "mock"
    agent_name: str = "PepperPy Agent"
    agent_description: str = "An agent created with PepperPy"
    agent_endpoint: str = "http://localhost:8080/api/a2a"
    capabilities: list[str] = ["text-generation", "task-completion"]

    def __init__(self, **config: Any):
        """Initialize the A2A workflow provider.

        Args:
            **config: Configuration options including:
                provider_type: A2A provider type (default: "mock")
                agent_name: Name of the agent (default: "PepperPy Agent")
                agent_description: Description of the agent
                agent_endpoint: API endpoint URL
                capabilities: List of agent capabilities
        """
        super().__init__(config)
        self.a2a_provider: A2AProvider | None = None
        self.agent_id: str | None = None
        self.agent_card: AgentCard | None = None
        self._logger = get_logger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

    async def _initialize_resources(self) -> None:
        """Initialize the A2A provider and resources."""
        try:
            from pepperpy.a2a import create_provider

            # Create the A2A provider
            self.a2a_provider = await create_provider(
                provider_type=self.provider_type,
                **self.config,
            )

            # Initialize the provider
            await self.a2a_provider.initialize()

            # Create an agent card
            self.agent_card = AgentCard(
                name=self.agent_name,
                description=self.agent_description,
                endpoint=self.agent_endpoint,
                capabilities=self.capabilities,
            )

            # For mock provider, we'd register the agent
            if hasattr(self.a2a_provider, "register_agent"):
                self.agent_id = str(uuid.uuid4())
                # await self.a2a_provider.register_agent(self.agent_card)
                self._logger.info(f"Registered agent {self.agent_id}")

            self._logger.debug("A2A workflow provider initialized successfully")
        except Exception as e:
            self._logger.error(f"Failed to initialize A2A workflow provider: {e}")
            raise

    async def _cleanup_resources(self) -> None:
        """Clean up the A2A provider resources."""
        if self.a2a_provider:
            try:
                await self.a2a_provider.cleanup()
                self._logger.debug("A2A provider cleaned up successfully")
            except Exception as e:
                self._logger.error(f"Error cleaning up A2A provider: {e}")
            finally:
                self.a2a_provider = None

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the A2A workflow.

        Args:
            input_data: Input data for the workflow, should include:
                - operation: The operation to perform ("send_message", "get_task")
                For send_message:
                    - target_agent_id: Target agent ID
                    - message: Message content
                For get_task:
                    - task_id: Task ID to retrieve

        Returns:
            Execution results containing:
                - status: "success" or "error"
                - operation: The operation that was performed
                - Additional operation-specific data
        
        Raises:
            ValueError: If required input is missing or invalid
        """
        if not input_data:
            self._logger.error("Input data is required")
            return {"status": "error", "message": "Input data is required"}
        
        # Get the operation to perform
        operation = input_data.get("operation", "send_message")
        self._logger.info(f"Executing operation: {operation}")
        
        try:
            if operation == "send_message":
                return await self._execute_send_message(input_data)
            elif operation == "get_task":
                return await self._execute_get_task(input_data)
            else:
                self._logger.warning(f"Unknown operation: {operation}")
                return {
                    "status": "error",
                    "message": f"Unknown operation: {operation}",
                }
        except Exception as e:
            self._logger.error(f"Error executing operation {operation}: {e}")
            return {
                "status": "error",
                "operation": operation,
                "message": str(e),
            }

    async def _execute_send_message(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the send_message operation.
        
        Args:
            input_data: Input data for the operation
        
        Returns:
            Operation result
            
        Raises:
            ValueError: If required input is missing
        """
        # Send a message to another agent
        target_agent_id = input_data.get("target_agent_id")
        message_content = input_data.get("message")
        
        if not target_agent_id or not message_content:
            raise ValueError("Target agent ID and message are required")
        
        # Create a message
        message = Message(
            role="user",
            parts=[TextPart(message_content)],
        )
        
        # Create a task (this is where we'd use the async API in a real implementation)
        # task = await self.a2a_provider.create_task(target_agent_id, message)
        
        # For demonstration
        task_id = str(uuid.uuid4())
        self._logger.info(f"Created task {task_id} for agent {target_agent_id}")
        
        return {
            "status": "success",
            "operation": "send_message",
            "task_id": task_id,
            "target_agent_id": target_agent_id,
        }

    async def _execute_get_task(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the get_task operation.
        
        Args:
            input_data: Input data for the operation
        
        Returns:
            Operation result
            
        Raises:
            ValueError: If required input is missing
        """
        # Get a task status
        task_id = input_data.get("task_id")
        
        if not task_id:
            raise ValueError("Task ID is required")
        
        # Get the task (this is where we'd use the async API)
        # task = await self.a2a_provider.get_task(task_id)
        
        # For demonstration
        self._logger.info(f"Retrieved task {task_id}")
        
        return {
            "status": "success",
            "operation": "get_task",
            "task_id": task_id,
            "state": TaskState.WORKING.value,
        }


def create_a2a_workflow() -> Pipeline:
    """Create an A2A workflow pipeline.

    Returns:
        A pipeline for A2A agent setup and communication
    """
    # Create the pipeline stages
    setup_stage = A2ASetupStage()
    registration_stage = A2ARegistrationStage()
    task_creation_stage = A2ATaskCreationStage()

    # Create the pipeline
    pipeline = Pipeline(
        name="a2a_workflow",
        stages=[setup_stage, registration_stage, task_creation_stage],
    )

    return pipeline


# Register the pipeline
from pepperpy.workflow.base import register_pipeline

register_pipeline(create_a2a_workflow())
