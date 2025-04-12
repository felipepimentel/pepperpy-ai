"""
MCP (Master Control Program) Topology.

Implements a centralized control system with distributed processing capabilities,
similar to the concept from classic computing systems.
"""

from typing import Any

from pepperpy.agent.base import BaseAgentProvider
from pepperpy.core.logging import get_logger

from .base import AgentTopologyProvider, TopologyError

logger = get_logger(__name__)


class MCPTopology(AgentTopologyProvider):
    """Master Control Program (MCP) topology implementation.

    This topology implements a central control system that manages resources,
    schedules tasks, and coordinates agent processes in a computing-inspired model.

    The MCP maintains:
    - A task queue for pending operations
    - Resource allocation for agents
    - Priority-based scheduling
    - Execution monitoring and fault tolerance

    MCP topologies are suitable for:
    - Complex multi-stage processing
    - Resource-intensive agent operations
    - Systems requiring fault tolerance
    - Scenarios needing dynamic resource allocation

    Configuration:
        priority_levels: Number of priority levels (1-10)
        scheduling_algorithm: Algorithm for task scheduling (fifo, priority, round_robin)
        fault_tolerance: Enable fault tolerance mechanisms
        resource_allocation: Algorithm for agent resource allocation
        agents: Dict of agent configurations by ID
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize MCP topology.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)

        # MCP configuration
        self.priority_levels = self.config.get("priority_levels", 5)
        self.scheduling_algorithm = self.config.get("scheduling_algorithm", "priority")
        self.fault_tolerance = self.config.get("fault_tolerance", True)
        self.resource_allocation = self.config.get("resource_allocation", "balanced")

        # Internal state
        self.task_queue: list[dict[str, Any]] = []
        self.active_processes: dict[str, dict[str, Any]] = {}
        self.resource_map: dict[str, float] = {}  # Agent ID to resource allocation
        self.system_state = "idle"  # idle, processing, error

    async def initialize(self) -> None:
        """Initialize MCP topology resources."""
        if self.initialized:
            return

        try:
            # Initialize configured agents
            for agent_id, agent_config in self.agent_configs.items():
                from pepperpy.agent import create_agent

                agent = create_agent(**agent_config)
                await self.add_agent(agent_id, agent)

                # Assign initial resources
                self.resource_map[agent_id] = agent_config.get("resource_weight", 1.0)

            self.initialized = True
            logger.info(f"Initialized MCP topology with {len(self.agents)} agents")
        except Exception as e:
            logger.error(f"Failed to initialize MCP topology: {e}")
            await self.cleanup()
            raise TopologyError(f"Initialization failed: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        # Cancel any active processes
        for process_id, process in self.active_processes.items():
            logger.info(f"Terminating process {process_id}")
            # Optionally do process-specific cleanup here

        self.active_processes = {}
        self.task_queue = []

        await super().cleanup()

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the MCP topology with input data.

        Args:
            input_data: Input containing task details

        Returns:
            Execution results
        """
        if not self.initialized:
            await self.initialize()

        # Prepare main task
        task = input_data.get("task", "")
        if not task:
            raise TopologyError("No task provided in input data")

        task_id = input_data.get("task_id", f"task_{len(self.task_queue)}")
        priority = input_data.get("priority", 3)  # Default medium priority

        # Create process for main task
        process = self._create_process(task_id, task, priority, input_data)

        # Add to task queue
        self.task_queue.append(process)

        # Process the task queue
        self.system_state = "processing"
        processing_result = await self._process_task_queue()

        # Return result for the submitted task
        if task_id in processing_result:
            return processing_result[task_id]
        else:
            return {
                "status": "error",
                "message": "Task execution failed or was not completed",
                "system_state": self.system_state,
            }

    def _create_process(
        self, process_id: str, task: str, priority: int, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a process descriptor.

        Args:
            process_id: Unique process identifier
            task: Task description
            priority: Process priority (1-10)
            metadata: Additional process metadata

        Returns:
            Process descriptor
        """
        return {
            "id": process_id,
            "task": task,
            "priority": max(
                1, min(priority, self.priority_levels)
            ),  # Clamp to valid range
            "status": "pending",
            "created_at": self._get_timestamp(),
            "metadata": metadata,
            "subtasks": [],
            "result": None,
            "error": None,
        }

    def _get_timestamp(self) -> float:
        """Get current timestamp.

        Returns:
            Current timestamp
        """
        import time

        return time.time()

    async def _process_task_queue(self) -> dict[str, dict[str, Any]]:
        """Process the task queue based on scheduling algorithm.

        Returns:
            Results for all processed tasks
        """
        results: dict[str, dict[str, Any]] = {}

        # Sort task queue based on scheduling algorithm
        if self.scheduling_algorithm == "priority":
            self.task_queue.sort(key=lambda x: (-x["priority"], x["created_at"]))
        elif self.scheduling_algorithm == "fifo":
            self.task_queue.sort(key=lambda x: x["created_at"])
        # Other algorithms could be implemented here

        # Process each task
        pending_tasks = list(self.task_queue)
        self.task_queue = []  # Clear queue as we process

        for process in pending_tasks:
            process_id = process["id"]
            logger.info(
                f"Processing task {process_id} with priority {process['priority']}"
            )

            try:
                # Mark process as active
                process["status"] = "running"
                self.active_processes[process_id] = process

                # Break down task into subtasks
                subtasks = await self._create_subtasks(process)
                process["subtasks"] = subtasks

                # Allocate agents to subtasks based on resource allocation strategy
                allocations = self._allocate_agents(subtasks)

                # Execute subtasks on allocated agents
                subtask_results = await self._execute_subtasks(subtasks, allocations)

                # Synthesize results
                final_result = await self._synthesize_results(process, subtask_results)

                # Store process result
                process["result"] = final_result
                process["status"] = "completed"
                results[process_id] = {
                    "status": "success",
                    "result": final_result,
                    "process": {
                        "id": process_id,
                        "priority": process["priority"],
                        "subtasks_count": len(subtasks),
                    },
                }
            except Exception as e:
                logger.error(f"Error processing task {process_id}: {e}")
                process["status"] = "error"
                process["error"] = str(e)

                # Implement fault tolerance if enabled
                if self.fault_tolerance:
                    retry_result = await self._handle_fault(process, e)
                    if retry_result["status"] == "success":
                        results[process_id] = retry_result
                        continue

                results[process_id] = {
                    "status": "error",
                    "error": str(e),
                    "process_id": process_id,
                }
            finally:
                # Remove from active processes
                if process_id in self.active_processes:
                    del self.active_processes[process_id]

        self.system_state = "idle"
        return results

    async def _create_subtasks(self, process: dict[str, Any]) -> list[dict[str, Any]]:
        """Break down a process into subtasks.

        Args:
            process: Process descriptor

        Returns:
            List of subtask descriptors
        """
        task = process["task"]
        metadata = process["metadata"]

        # Simple task breakdown - in a real system, this would use an agent to intelligently
        # break down the task based on its complexity and available agents

        # For simplicity, we'll create one subtask per agent
        subtasks = []
        for i, agent_id in enumerate(self.agents.keys()):
            subtask_id = f"{process['id']}_subtask_{i}"

            # Create agent-specific prompt
            prompt = (
                f"You are part of a Master Control Program system processing task: {task}\n\n"
                f"You are agent {agent_id} and have been assigned subtask {i + 1}.\n"
                f"Process the following task according to your capabilities:\n\n"
                f"{task}"
            )

            subtasks.append({
                "id": subtask_id,
                "parent_id": process["id"],
                "prompt": prompt,
                "status": "pending",
                "agent_id": None,  # Will be assigned during allocation
                "created_at": self._get_timestamp(),
                "priority": process["priority"],
                "result": None,
                "error": None,
            })

        return subtasks

    def _allocate_agents(self, subtasks: list[dict[str, Any]]) -> dict[str, str]:
        """Allocate agents to subtasks based on resource allocation strategy.

        Args:
            subtasks: List of subtask descriptors

        Returns:
            Dictionary mapping subtask IDs to agent IDs
        """
        allocations: dict[str, str] = {}

        if self.resource_allocation == "balanced":
            # Simple round-robin allocation
            agent_ids = list(self.agents.keys())
            for i, subtask in enumerate(subtasks):
                agent_idx = i % len(agent_ids)
                agent_id = agent_ids[agent_idx]
                allocations[subtask["id"]] = agent_id
                subtask["agent_id"] = agent_id
        elif self.resource_allocation == "priority":
            # Allocate based on agent capabilities (simplified)
            # In a real system, this would be more sophisticated
            agent_capabilities = {
                agent_id: self.resource_map.get(agent_id, 1.0)
                for agent_id in self.agents.keys()
            }

            # Sort agents by capability score
            sorted_agents = sorted(
                agent_capabilities.items(), key=lambda x: x[1], reverse=True
            )

            # Sort subtasks by priority
            sorted_subtasks = sorted(
                subtasks, key=lambda x: x["priority"], reverse=True
            )

            # Assign highest priority subtasks to most capable agents
            for i, subtask in enumerate(sorted_subtasks):
                agent_idx = i % len(sorted_agents)
                agent_id = sorted_agents[agent_idx][0]
                allocations[subtask["id"]] = agent_id
                subtask["agent_id"] = agent_id

        return allocations

    async def _execute_subtasks(
        self, subtasks: list[dict[str, Any]], allocations: dict[str, str]
    ) -> dict[str, Any]:
        """Execute subtasks on allocated agents.

        Args:
            subtasks: List of subtask descriptors
            allocations: Dictionary mapping subtask IDs to agent IDs

        Returns:
            Subtask execution results
        """
        results: dict[str, Any] = {}

        # Execute subtasks in parallel for efficiency
        import asyncio

        tasks = []

        for subtask in subtasks:
            subtask_id = subtask["id"]
            agent_id = subtask["agent_id"]

            if not agent_id or agent_id not in self.agents:
                logger.warning(f"No valid agent allocated for subtask {subtask_id}")
                results[subtask_id] = {
                    "status": "error",
                    "error": "No valid agent allocation",
                }
                continue

            # Create task for execution
            task = asyncio.create_task(
                self._execute_single_subtask(subtask, self.agents[agent_id])
            )
            tasks.append((subtask_id, task))

        # Wait for all tasks to complete
        for subtask_id, task in tasks:
            try:
                result = await task
                results[subtask_id] = {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Error executing subtask {subtask_id}: {e}")
                results[subtask_id] = {"status": "error", "error": str(e)}

        return results

    async def _execute_single_subtask(
        self, subtask: dict[str, Any], agent: BaseAgentProvider
    ) -> Any:
        """Execute a single subtask with the assigned agent.

        Args:
            subtask: Subtask descriptor
            agent: Agent provider

        Returns:
            Execution result

        Raises:
            Exception: If execution fails
        """
        subtask["status"] = "running"

        try:
            # Execute with agent
            prompt = subtask["prompt"]
            result = await agent.process_message(prompt)

            subtask["status"] = "completed"
            subtask["result"] = result
            return result
        except Exception as e:
            subtask["status"] = "error"
            subtask["error"] = str(e)
            raise

    async def _synthesize_results(
        self, process: dict[str, Any], subtask_results: dict[str, Any]
    ) -> Any:
        """Synthesize final result from subtask results.

        Args:
            process: Process descriptor
            subtask_results: Results from subtasks

        Returns:
            Synthesized result
        """
        # Collect successful results
        successful_results = [
            subtask_results[subtask["id"]]["result"]
            for subtask in process["subtasks"]
            if subtask["id"] in subtask_results
            and subtask_results[subtask["id"]]["status"] == "success"
        ]

        if not successful_results:
            raise TopologyError("No successful subtask results to synthesize")

        # If only one result, return it directly
        if len(successful_results) == 1:
            return successful_results[0]

        # For multiple results, we need to combine them
        # In a real system, this would likely use another agent to synthesize the results
        combined_result = "\n\n".join([
            f"Result {i + 1}:\n{result}" for i, result in enumerate(successful_results)
        ])

        return {
            "combined_results": combined_result,
            "result_count": len(successful_results),
            "total_subtasks": len(process["subtasks"]),
        }

    async def _handle_fault(
        self, process: dict[str, Any], error: Exception
    ) -> dict[str, Any]:
        """Handle fault tolerance for failed processes.

        Args:
            process: Failed process descriptor
            error: Exception that caused the failure

        Returns:
            Result of fault handling
        """
        logger.info(f"Applying fault tolerance for process {process['id']}")

        # Check if any subtasks successfully completed
        completed_subtasks = [
            subtask
            for subtask in process.get("subtasks", [])
            if subtask["status"] == "completed"
        ]

        # If we have some successful subtasks, try to synthesize from those
        if completed_subtasks:
            logger.info(
                f"Attempting to synthesize from {len(completed_subtasks)} completed subtasks"
            )

            # Build a partial result dict
            partial_results = {}
            for subtask in completed_subtasks:
                partial_results[subtask["id"]] = {
                    "status": "success",
                    "result": subtask["result"],
                }

            try:
                # Synthesize from partial results
                partial_synthesis = await self._synthesize_results(
                    process, partial_results
                )

                return {
                    "status": "success",
                    "result": {
                        "partial_result": True,
                        "synthesis": partial_synthesis,
                        "completed_subtasks": len(completed_subtasks),
                        "total_subtasks": len(process.get("subtasks", [])),
                        "original_error": str(error),
                    },
                    "process_id": process["id"],
                }
            except Exception as e:
                logger.error(f"Error during partial synthesis: {e}")
                # Fall through to retry logic

        # Simple retry mechanism - attempt once with reduced complexity
        logger.info(f"Retrying process {process['id']} with simplified task")

        try:
            # Create a simplified version of the task
            simplified_task = f"Simplified version of: {process['task']}"

            # Get a high-capability agent for the retry
            retry_agent_id = None
            max_capability = 0.0

            for agent_id, capability in self.resource_map.items():
                if capability > max_capability:
                    max_capability = capability
                    retry_agent_id = agent_id

            if not retry_agent_id or retry_agent_id not in self.agents:
                return {
                    "status": "error",
                    "message": "No suitable agent found for retry",
                    "original_error": str(error),
                    "process_id": process["id"],
                }

            # Execute with retry agent
            retry_agent = self.agents[retry_agent_id]
            retry_prompt = (
                f"The following task encountered an error and needs a simplified solution:\n\n"
                f"ORIGINAL TASK: {process['task']}\n\n"
                f"ERROR: {error}\n\n"
                f"Please provide a simplified but effective solution for this task."
            )

            retry_result = await retry_agent.process_message(retry_prompt)

            return {
                "status": "success",
                "result": {
                    "retry": True,
                    "simplified_result": retry_result,
                    "retry_agent": retry_agent_id,
                    "original_error": str(error),
                },
                "process_id": process["id"],
            }

        except Exception as retry_error:
            logger.error(
                f"Retry also failed for process {process['id']}: {retry_error}"
            )

            return {
                "status": "error",
                "message": f"Both original attempt and retry failed: {retry_error}",
                "original_error": str(error),
                "retry_error": str(retry_error),
                "process_id": process["id"],
            }

    async def add_task(
        self, task: str, priority: int = 3, metadata: dict[str, Any] | None = None
    ) -> str:
        """Add a new task to the MCP queue.

        Args:
            task: Task description
            priority: Task priority (1-10)
            metadata: Additional task metadata

        Returns:
            Task ID
        """
        task_id = f"task_{len(self.task_queue) + len(self.active_processes)}"
        process = self._create_process(task_id, task, priority, metadata or {})

        self.task_queue.append(process)
        logger.info(f"Added task {task_id} to queue with priority {priority}")

        return task_id

    async def get_system_stats(self) -> dict[str, Any]:
        """Get current system statistics.

        Returns:
            System statistics
        """
        return {
            "state": self.system_state,
            "pending_tasks": len(self.task_queue),
            "active_processes": len(self.active_processes),
            "agent_count": len(self.agents),
            "resource_allocation": self.resource_map,
            "scheduling_algorithm": self.scheduling_algorithm,
            "fault_tolerance": self.fault_tolerance,
        }

    async def adjust_resources(self, agent_id: str, allocation: float) -> None:
        """Adjust resource allocation for an agent.

        Args:
            agent_id: Agent ID
            allocation: New resource allocation weight

        Raises:
            TopologyError: If agent not found
        """
        if agent_id not in self.agents:
            raise TopologyError(f"Agent {agent_id} not found")

        self.resource_map[agent_id] = max(0.1, min(10.0, allocation))
        logger.info(f"Adjusted resource allocation for {agent_id} to {allocation}")
