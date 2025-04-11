"""Agent orchestration for AI Gateway.

This module provides functionality for orchestrating multi-agent workflows,
managing conversations, and coordinating complex tasks.
"""

import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from .base import AgentCapability, Task, TaskPriority, TaskStatus
from .manager import AgentManager

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Status of a workflow."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class WorkflowStep:
    """Step in a workflow."""

    def __init__(
        self,
        step_id: str,
        name: str,
        description: str,
        objective: str,
        parameters: dict[str, Any],
        capabilities: list[AgentCapability] = None,
        agent_id: str | None = None,
        depends_on: list[str] = None,
        required_outputs: list[str] = None,
        provided_outputs: list[str] = None,
    ):
        """Initialize workflow step.

        Args:
            step_id: Step ID
            name: Step name
            description: Step description
            objective: Task objective
            parameters: Task parameters
            capabilities: Required agent capabilities
            agent_id: Specific agent ID to use (optional)
            depends_on: IDs of steps that must complete before this one
            required_outputs: Outputs required from previous steps
            provided_outputs: Outputs provided by this step
        """
        self.step_id = step_id
        self.name = name
        self.description = description
        self.objective = objective
        self.parameters = parameters
        self.capabilities = capabilities or []
        self.agent_id = agent_id
        self.depends_on = depends_on or []
        self.required_outputs = required_outputs or []
        self.provided_outputs = provided_outputs or []

        # Runtime attributes
        self.task_id: str | None = None
        self.status = TaskStatus.PENDING
        self.result: dict[str, Any] | None = None
        self.error: str | None = None
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "step_id": self.step_id,
            "name": self.name,
            "description": self.description,
            "objective": self.objective,
            "parameters": self.parameters,
            "capabilities": [cap.value for cap in self.capabilities],
            "agent_id": self.agent_id,
            "depends_on": self.depends_on,
            "required_outputs": self.required_outputs,
            "provided_outputs": self.provided_outputs,
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowStep":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            WorkflowStep
        """
        step = cls(
            step_id=data["step_id"],
            name=data["name"],
            description=data["description"],
            objective=data["objective"],
            parameters=data["parameters"],
            capabilities=[AgentCapability(cap) for cap in data.get("capabilities", [])],
            agent_id=data.get("agent_id"),
            depends_on=data.get("depends_on", []),
            required_outputs=data.get("required_outputs", []),
            provided_outputs=data.get("provided_outputs", []),
        )

        step.task_id = data.get("task_id")
        step.status = TaskStatus(data.get("status", "pending"))
        step.result = data.get("result")
        step.error = data.get("error")

        if data.get("started_at"):
            step.started_at = datetime.fromisoformat(data["started_at"])

        if data.get("completed_at"):
            step.completed_at = datetime.fromisoformat(data["completed_at"])

        return step


class WorkflowDefinition:
    """Definition of a workflow."""

    def __init__(
        self,
        workflow_id: str,
        name: str,
        description: str,
        version: str,
        steps: list[WorkflowStep],
        parameters_schema: dict[str, Any] = None,
        output_schema: dict[str, Any] = None,
    ):
        """Initialize workflow definition.

        Args:
            workflow_id: Workflow ID
            name: Workflow name
            description: Workflow description
            version: Workflow version
            steps: Workflow steps
            parameters_schema: JSON Schema for parameters
            output_schema: JSON Schema for output
        """
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.version = version
        self.steps = steps
        self.parameters_schema = parameters_schema or {}
        self.output_schema = output_schema or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "steps": [step.to_dict() for step in self.steps],
            "parameters_schema": self.parameters_schema,
            "output_schema": self.output_schema,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowDefinition":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            WorkflowDefinition
        """
        return cls(
            workflow_id=data["workflow_id"],
            name=data["name"],
            description=data["description"],
            version=data["version"],
            steps=[WorkflowStep.from_dict(step_data) for step_data in data["steps"]],
            parameters_schema=data.get("parameters_schema", {}),
            output_schema=data.get("output_schema", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "WorkflowDefinition":
        """Create from JSON string.

        Args:
            json_str: JSON string

        Returns:
            WorkflowDefinition
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def to_json(self) -> str:
        """Convert to JSON string.

        Returns:
            JSON string
        """
        return json.dumps(self.to_dict())


class WorkflowInstance:
    """Instance of a workflow."""

    def __init__(
        self,
        instance_id: str,
        definition: WorkflowDefinition,
        parameters: dict[str, Any],
        context: dict[str, Any] = None,
    ):
        """Initialize workflow instance.

        Args:
            instance_id: Instance ID
            definition: Workflow definition
            parameters: Workflow parameters
            context: Additional context
        """
        self.instance_id = instance_id
        self.definition = definition
        self.parameters = parameters
        self.context = context or {}

        # Runtime attributes
        self.status = WorkflowStatus.CREATED
        self.steps = {
            step.step_id: WorkflowStep.from_dict(step.to_dict())
            for step in definition.steps
        }
        self.output: dict[str, Any] = {}
        self.step_outputs: dict[str, dict[str, Any]] = {}
        self.error: str | None = None
        self.created_at = datetime.now()
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "instance_id": self.instance_id,
            "definition": self.definition.to_dict(),
            "parameters": self.parameters,
            "context": self.context,
            "status": self.status.value,
            "steps": {step_id: step.to_dict() for step_id, step in self.steps.items()},
            "output": self.output,
            "step_outputs": self.step_outputs,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
        }


class WorkflowOrchestrator:
    """Orchestrator for agent workflows."""

    def __init__(
        self,
        agent_manager: AgentManager,
        context: dict[str, Any] | None = None,
    ):
        """Initialize workflow orchestrator.

        Args:
            agent_manager: Agent manager
            context: Shared context
        """
        self.agent_manager = agent_manager
        self.context = context or {}

        self.workflows: dict[str, WorkflowDefinition] = {}
        self.instances: dict[str, WorkflowInstance] = {}

        # Event handlers
        self.agent_manager.register_event_handler(
            "task_completed", self._on_task_completed
        )
        self.agent_manager.register_event_handler("task_failed", self._on_task_failed)

    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """Register a workflow.

        Args:
            workflow: Workflow definition
        """
        self.workflows[workflow.workflow_id] = workflow
        logger.info(f"Registered workflow: {workflow.name} ({workflow.workflow_id})")

    def unregister_workflow(self, workflow_id: str) -> bool:
        """Unregister a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            True if workflow was unregistered, False if not found
        """
        if workflow_id not in self.workflows:
            return False

        workflow = self.workflows.pop(workflow_id)
        logger.info(f"Unregistered workflow: {workflow.name} ({workflow.workflow_id})")
        return True

    def list_workflows(self) -> list[dict[str, Any]]:
        """List registered workflows.

        Returns:
            List of workflow details
        """
        return [workflow.to_dict() for workflow in self.workflows.values()]

    def get_workflow(self, workflow_id: str) -> WorkflowDefinition | None:
        """Get a workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow if found, None otherwise
        """
        return self.workflows.get(workflow_id)

    async def create_instance(
        self,
        workflow_id: str,
        parameters: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> str:
        """Create a workflow instance.

        Args:
            workflow_id: Workflow ID
            parameters: Workflow parameters
            context: Additional context

        Returns:
            Instance ID

        Raises:
            ValueError: If workflow not found
        """
        # Get workflow
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        # Create instance
        instance_id = str(uuid.uuid4())
        instance = WorkflowInstance(
            instance_id=instance_id,
            definition=workflow,
            parameters=parameters,
            context=context or {},
        )

        # Store instance
        self.instances[instance_id] = instance

        logger.info(f"Created workflow instance: {instance_id} ({workflow.name})")
        return instance_id

    def get_instance(self, instance_id: str) -> WorkflowInstance | None:
        """Get a workflow instance by ID.

        Args:
            instance_id: Instance ID

        Returns:
            Instance if found, None otherwise
        """
        return self.instances.get(instance_id)

    def list_instances(
        self,
        status: WorkflowStatus | list[WorkflowStatus] | None = None,
        workflow_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List workflow instances.

        Args:
            status: Filter by status
            workflow_id: Filter by workflow ID
            limit: Maximum number of instances to return

        Returns:
            List of instance details
        """
        instances = []

        # Convert single status to list
        if status and not isinstance(status, list):
            status = [status]

        for instance in self.instances.values():
            # Apply filters
            if status and instance.status not in status:
                continue

            if workflow_id and instance.definition.workflow_id != workflow_id:
                continue

            instances.append(instance.to_dict())

            if len(instances) >= limit:
                break

        return instances

    async def start_instance(self, instance_id: str) -> None:
        """Start a workflow instance.

        Args:
            instance_id: Instance ID

        Raises:
            ValueError: If instance not found or cannot be started
        """
        # Get instance
        instance = self.get_instance(instance_id)
        if not instance:
            raise ValueError(f"Instance not found: {instance_id}")

        # Check status
        if instance.status != WorkflowStatus.CREATED:
            raise ValueError(
                f"Instance cannot be started (status: {instance.status.value})"
            )

        # Update status
        instance.status = WorkflowStatus.RUNNING
        instance.started_at = datetime.now()

        logger.info(f"Starting workflow instance: {instance_id}")

        # Start initial steps
        await self._schedule_ready_steps(instance)

    async def cancel_instance(self, instance_id: str) -> None:
        """Cancel a workflow instance.

        Args:
            instance_id: Instance ID

        Raises:
            ValueError: If instance not found
        """
        # Get instance
        instance = self.get_instance(instance_id)
        if not instance:
            raise ValueError(f"Instance not found: {instance_id}")

        # Only cancel if running
        if instance.status == WorkflowStatus.RUNNING:
            # Update status
            instance.status = WorkflowStatus.CANCELLED

            logger.info(f"Cancelled workflow instance: {instance_id}")

    async def _schedule_ready_steps(self, instance: WorkflowInstance) -> None:
        """Schedule ready steps in a workflow instance.

        Args:
            instance: Workflow instance
        """
        # Find ready steps
        ready_steps: list[WorkflowStep] = []

        for step in instance.steps.values():
            # Skip if already done or in progress
            if step.status != TaskStatus.PENDING:
                continue

            # Check dependencies
            deps_satisfied = True
            for dep_id in step.depends_on:
                if dep_id not in instance.steps:
                    logger.warning(
                        f"Step {step.step_id} depends on unknown step {dep_id}"
                    )
                    deps_satisfied = False
                    break

                dep_step = instance.steps[dep_id]
                if dep_step.status != TaskStatus.COMPLETED:
                    deps_satisfied = False
                    break

            if deps_satisfied:
                ready_steps.append(step)

        # Schedule each ready step
        for step in ready_steps:
            await self._schedule_step(instance, step)

    async def _schedule_step(
        self, instance: WorkflowInstance, step: WorkflowStep
    ) -> None:
        """Schedule a workflow step.

        Args:
            instance: Workflow instance
            step: Workflow step
        """
        # Check if workflow is still running
        if instance.status != WorkflowStatus.RUNNING:
            return

        # Prepare parameters
        parameters = step.parameters.copy()

        # Add workflow parameters
        parameters.update({
            "workflow_id": instance.definition.workflow_id,
            "workflow_name": instance.definition.name,
            "workflow_instance_id": instance.instance_id,
            "workflow_parameters": instance.parameters,
            "step_id": step.step_id,
            "step_name": step.name,
        })

        # Add outputs from required steps
        for req_output in step.required_outputs:
            if "." in req_output:
                # Format: step_id.output_key
                parts = req_output.split(".", 1)
                src_step_id, output_key = parts

                if src_step_id not in instance.step_outputs:
                    logger.warning(
                        f"Required output from step {src_step_id} not available"
                    )
                    continue

                if output_key not in instance.step_outputs[src_step_id]:
                    logger.warning(
                        f"Output key {output_key} not available from step {src_step_id}"
                    )
                    continue

                parameters[req_output] = instance.step_outputs[src_step_id][output_key]
            else:
                # Just the output key, look in all completed steps
                for src_step_id, outputs in instance.step_outputs.items():
                    if req_output in outputs:
                        parameters[req_output] = outputs[req_output]
                        break

        # Submit task
        task_id = await self.agent_manager.submit_task(
            objective=step.objective,
            parameters=parameters,
            priority=TaskPriority.MEDIUM,
            required_capabilities=step.capabilities,
            agent_id=step.agent_id,
        )

        # Update step
        step.task_id = task_id
        step.status = TaskStatus.ASSIGNED
        step.started_at = datetime.now()

        logger.info(
            f"Scheduled step {step.name} ({step.step_id}) "
            f"in workflow instance {instance.instance_id}"
        )

    async def _on_task_completed(self, event_type: str, data: dict[str, Any]) -> None:
        """Handle task completed event.

        Args:
            event_type: Event type
            data: Event data
        """
        task = data.get("task")
        if not task:
            return

        # Check if this is a workflow step
        workflow_instance_id = task.parameters.get("workflow_instance_id")
        if not workflow_instance_id:
            return

        step_id = task.parameters.get("step_id")
        if not step_id:
            return

        # Get instance
        instance = self.get_instance(workflow_instance_id)
        if not instance:
            logger.warning(
                f"Task {task.id} completed for unknown workflow instance: "
                f"{workflow_instance_id}"
            )
            return

        # Get step
        if step_id not in instance.steps:
            logger.warning(
                f"Task {task.id} completed for unknown step {step_id} "
                f"in workflow instance {workflow_instance_id}"
            )
            return

        step = instance.steps[step_id]

        # Update step
        step.status = TaskStatus.COMPLETED
        step.completed_at = datetime.now()
        step.result = task.result

        logger.info(
            f"Step {step.name} ({step.step_id}) completed "
            f"in workflow instance {instance.instance_id}"
        )

        # Store step output
        instance.step_outputs[step_id] = task.result or {}

        # Check if workflow is complete
        all_completed = True
        for s in instance.steps.values():
            if s.status != TaskStatus.COMPLETED:
                all_completed = False
                break

        if all_completed:
            # All steps completed
            instance.status = WorkflowStatus.COMPLETED
            instance.completed_at = datetime.now()

            # Collect output
            instance.output = {
                step_id: outputs for step_id, outputs in instance.step_outputs.items()
            }

            logger.info(f"Workflow instance {instance.instance_id} completed")
        else:
            # Schedule next steps
            await self._schedule_ready_steps(instance)

    async def _on_task_failed(self, event_type: str, data: dict[str, Any]) -> None:
        """Handle task failed event.

        Args:
            event_type: Event type
            data: Event data
        """
        task = data.get("task")
        if not task:
            return

        # Check if this is a workflow step
        workflow_instance_id = task.parameters.get("workflow_instance_id")
        if not workflow_instance_id:
            return

        step_id = task.parameters.get("step_id")
        if not step_id:
            return

        # Get instance
        instance = self.get_instance(workflow_instance_id)
        if not instance:
            logger.warning(
                f"Task {task.id} failed for unknown workflow instance: "
                f"{workflow_instance_id}"
            )
            return

        # Get step
        if step_id not in instance.steps:
            logger.warning(
                f"Task {task.id} failed for unknown step {step_id} "
                f"in workflow instance {workflow_instance_id}"
            )
            return

        step = instance.steps[step_id]

        # Update step
        step.status = TaskStatus.FAILED
        step.error = task.error

        # Update instance
        instance.status = WorkflowStatus.FAILED
        instance.error = f"Step {step.name} ({step.step_id}) failed: {task.error}"

        logger.error(
            f"Step {step.name} ({step.step_id}) failed "
            f"in workflow instance {instance.instance_id}: {task.error}"
        )


class ConversationManager:
    """Manager for agent conversations."""

    def __init__(
        self,
        agent_manager: AgentManager,
        context: dict[str, Any] | None = None,
    ):
        """Initialize conversation manager.

        Args:
            agent_manager: Agent manager
            context: Shared context
        """
        self.agent_manager = agent_manager
        self.context = context or {}

        self.conversations: dict[str, dict[str, Any]] = {}

    async def create_conversation(
        self,
        conversation_type: str,
        parameters: dict[str, Any] = None,
    ) -> str:
        """Create a new conversation.

        Args:
            conversation_type: Type of conversation
            parameters: Conversation parameters

        Returns:
            Conversation ID
        """
        # Create conversation
        conversation_id = str(uuid.uuid4())

        conversation = {
            "id": conversation_id,
            "type": conversation_type,
            "parameters": parameters or {},
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "metadata": {},
            "agents": [],
        }

        # Store conversation
        self.conversations[conversation_id] = conversation

        logger.info(f"Created conversation: {conversation_id} ({conversation_type})")
        return conversation_id

    def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        """Get a conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation if found, None otherwise
        """
        return self.conversations.get(conversation_id)

    async def add_message(
        self,
        conversation_id: str,
        message: dict[str, Any],
    ) -> None:
        """Add a message to a conversation.

        Args:
            conversation_id: Conversation ID
            message: Message to add

        Raises:
            ValueError: If conversation not found
        """
        # Get conversation
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation not found: {conversation_id}")

        # Add timestamp if missing
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()

        # Add message
        conversation["messages"].append(message)

        logger.debug(
            f"Added message to conversation {conversation_id}: "
            f"{message.get('sender', 'Unknown')}: {message.get('content', '')[:50]}..."
        )

    async def process_conversation(
        self,
        conversation_id: str,
        agent_id: str,
    ) -> dict[str, Any]:
        """Process a conversation with an agent.

        Args:
            conversation_id: Conversation ID
            agent_id: Agent ID

        Returns:
            Agent response

        Raises:
            ValueError: If conversation or agent not found
        """
        # Get conversation
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation not found: {conversation_id}")

        # Get agent
        agent = self.agent_manager.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        # Create task
        task = Task(
            objective="Process conversation",
            parameters={
                "conversation_id": conversation_id,
                "conversation": conversation,
            },
            priority=TaskPriority.HIGH,
        )

        # Execute task
        result = await agent.execute(task, self.agent_manager.agent_context)

        # Record agent in conversation if not already present
        if agent_id not in conversation["agents"]:
            conversation["agents"].append(agent_id)

        # Add response to conversation
        if "response" in result:
            await self.add_message(
                conversation_id,
                {
                    "sender": agent.name,
                    "sender_id": agent_id,
                    "content": result["response"],
                    "type": "agent",
                },
            )

        return result
