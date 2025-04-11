"""Coordinator agent implementation for AI Research Assistant."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set

from .base_agent import AgentContext, AgentStatus, BaseAgent, Task


class CoordinatorAgent(BaseAgent):
    """Coordinator agent for the AI Research Assistant.

    This agent is responsible for:
    1. Planning the overall research workflow
    2. Delegating tasks to specialized agents
    3. Monitoring progress and handling errors
    4. Assembling the final results
    """

    def __init__(
        self,
        agent_id: str = "coordinator",
        name: str = "Research Coordinator",
        description: str = "Manages the research workflow and coordinates specialized agents",
    ) -> None:
        """Initialize the coordinator agent.

        Args:
            agent_id: Unique identifier
            name: Display name
            description: Agent description
        """
        capabilities = {
            "planning",
            "delegation",
            "workflow_management",
            "error_handling",
            "result_assembly",
        }
        super().__init__(agent_id, name, description, capabilities)
        self.available_agents: Dict[str, BaseAgent] = {}
        self.task_queue: List[Task] = []
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.failed_tasks: Dict[str, Task] = {}

    async def _initialize_resources(self) -> None:
        """Initialize resources for the coordinator."""
        self.logger.info("Initializing coordinator agent resources")
        # No specific resources to initialize

    async def _cleanup_resources(self) -> None:
        """Clean up coordinator resources."""
        self.logger.info("Cleaning up coordinator agent resources")
        # Clean up registered agents
        for agent_id, agent in self.available_agents.items():
            if agent.initialized:
                self.logger.info(f"Cleaning up agent: {agent_id}")
                await agent.cleanup()

    async def register_agent(self, agent: BaseAgent) -> None:
        """Register a specialized agent with the coordinator.

        Args:
            agent: Agent to register
        """
        self.available_agents[agent.agent_id] = agent
        self.logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")

    async def _execute_task(self, task: Task, context: AgentContext) -> Dict[str, Any]:
        """Execute coordinator task.

        Args:
            task: Task to execute
            context: Execution context

        Returns:
            Task result
        """
        # Handle different task types
        if task.type == "research":
            return await self._handle_research_task(task, context)
        elif task.type == "status":
            return self._get_research_status()
        else:
            raise ValueError(f"Unknown task type: {task.type}")

    async def _handle_research_task(
        self, task: Task, context: AgentContext
    ) -> Dict[str, Any]:
        """Handle a research task.

        Args:
            task: Research task
            context: Execution context

        Returns:
            Research results
        """
        topic = task.input_data.get("topic", "")
        if not topic:
            raise ValueError("Research topic is required")

        self.logger.info(f"Starting research on topic: {topic}")

        # Create a research plan
        research_plan = await self._create_research_plan(topic, context)
        context.share("research_plan", research_plan)

        # Create and execute subtasks based on the plan
        try:
            # 1. Research phase
            research_task = await self._create_subtask(
                parent_task=task,
                task_type="find_information",
                description=f"Find information about: {topic}",
                input_data={"topic": topic, "research_plan": research_plan},
                agent_id="research",
                context=context,
            )

            # 2. Analysis phase
            if research_task.result and "sources" in research_task.result:
                analysis_task = await self._create_subtask(
                    parent_task=task,
                    task_type="analyze_content",
                    description=f"Analyze information about: {topic}",
                    input_data={
                        "topic": topic,
                        "sources": research_task.result["sources"],
                        "research_plan": research_plan,
                    },
                    agent_id="analysis",
                    context=context,
                )
            else:
                raise ValueError("Research task did not return any sources")

            # 3. Writing phase
            writing_task = await self._create_subtask(
                parent_task=task,
                task_type="write_report",
                description=f"Write a report about: {topic}",
                input_data={
                    "topic": topic,
                    "research_plan": research_plan,
                    "analysis": analysis_task.result.get("analysis", {}) if analysis_task.result else {},
                    "key_points": analysis_task.result.get("key_points", []) if analysis_task.result else [],
                },
                agent_id="writing",
                context=context,
            )

            # 4. Review phase
            review_task = await self._create_subtask(
                parent_task=task,
                task_type="review_report",
                description=f"Review the report on: {topic}",
                input_data={
                    "topic": topic,
                    "research_plan": research_plan,
                    "report": writing_task.result.get("report", "") if writing_task.result else "",
                },
                agent_id="critic",
                context=context,
            )

            # 5. Finalize report based on review
            final_report = await self._finalize_report(
                writing_task.result or {},
                review_task.result or {},
                context,
            )

            # Return the final research results
            return {
                "topic": topic,
                "research_plan": research_plan,
                "sources": research_task.result.get("sources", []) if research_task.result else [],
                "key_points": analysis_task.result.get("key_points", []) if analysis_task.result else [],
                "report": final_report,
                "feedback": review_task.result.get("feedback", {}) if review_task.result else {},
            }

        except Exception as e:
            self.logger.error(f"Error in research workflow: {e}")
            # Attempt to salvage partial results
            return self._collect_partial_results(topic, task, context)

    async def _create_research_plan(
        self, topic: str, context: AgentContext
    ) -> Dict[str, Any]:
        """Create a research plan for a topic.

        Args:
            topic: Research topic
            context: Execution context

        Returns:
            Research plan
        """
        # In a real implementation, this would use LLM to create a plan
        # For this showcase, we'll use a simple template
        return {
            "topic": topic,
            "objectives": [
                "Understand the main concepts and background",
                "Identify key developments and current state",
                "Analyze impact and significance",
                "Explore future directions and possibilities",
            ],
            "focus_areas": [
                f"Definitions and scope of {topic}",
                f"History and evolution of {topic}",
                f"Current applications of {topic}",
                f"Future trends in {topic}",
            ],
            "research_approach": "Comprehensive overview with balanced analysis",
        }

    async def _create_subtask(
        self,
        parent_task: Task,
        task_type: str,
        description: str,
        input_data: Dict[str, Any],
        agent_id: str,
        context: AgentContext,
    ) -> Task:
        """Create and execute a subtask.

        Args:
            parent_task: Parent task
            task_type: Subtask type
            description: Subtask description
            input_data: Input data for subtask
            agent_id: Target agent ID
            context: Execution context

        Returns:
            Completed subtask

        Raises:
            ValueError: If agent not found
            Exception: If subtask execution fails
        """
        # Create subtask
        subtask = Task(
            type=task_type,
            description=description,
            input_data=input_data,
            parent_task_id=parent_task.id,
        )

        # Add to parent's subtasks
        parent_task.subtasks.append(subtask.id)

        # Find the appropriate agent
        agent = self.available_agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        # Execute the subtask
        self.logger.info(f"Delegating {task_type} task to {agent.name}")
        executed_task = await agent.execute(subtask, context)

        # Store the result
        if executed_task.status == AgentStatus.COMPLETED:
            self.completed_tasks[executed_task.id] = executed_task
            self.logger.info(f"Subtask {task_type} completed successfully")
        else:
            self.failed_tasks[executed_task.id] = executed_task
            self.logger.error(f"Subtask {task_type} failed: {executed_task.error}")
            raise Exception(f"Subtask {task_type} failed: {executed_task.error}")

        return executed_task

    async def _finalize_report(
        self,
        writing_result: Dict[str, Any],
        review_result: Dict[str, Any],
        context: AgentContext,
    ) -> str:
        """Finalize the report based on review feedback.

        Args:
            writing_result: Original writing result
            review_result: Review result
            context: Execution context

        Returns:
            Finalized report
        """
        # Get original report and feedback
        original_report = writing_result.get("report", "")
        feedback = review_result.get("feedback", {})
        suggestions = review_result.get("suggestions", [])

        # In a real implementation, this would send the report and feedback to the writing agent
        # For this showcase, we'll simulate the process

        # Simply append feedback for demonstration
        improved_report = original_report

        if suggestions:
            improved_report += "\n\n## Improvements Based on Review\n\n"
            for suggestion in suggestions:
                improved_report += f"- {suggestion}\n"

        return improved_report

    def _get_research_status(self) -> Dict[str, Any]:
        """Get the current status of all research tasks.

        Returns:
            Research status summary
        """
        return {
            "total_tasks": len(self.task_queue)
            + len(self.running_tasks)
            + len(self.completed_tasks)
            + len(self.failed_tasks),
            "queued": len(self.task_queue),
            "running": len(self.running_tasks),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks),
            "completed_tasks": [
                task.to_dict() for task in self.completed_tasks.values()
            ],
            "failed_tasks": [task.to_dict() for task in self.failed_tasks.values()],
        }

    def _collect_partial_results(
        self, topic: str, task: Task, context: AgentContext
    ) -> Dict[str, Any]:
        """Collect partial results in case of workflow error.

        Args:
            topic: Research topic
            task: Main task
            context: Execution context

        Returns:
            Partial results
        """
        # Collect whatever results we have
        result = {
            "topic": topic,
            "status": "partial",
            "error": "Research workflow was interrupted",
            "research_plan": context.get_shared("research_plan", {}),
            "sources": [],
            "key_points": [],
            "report": "Report generation failed due to errors in the research process.",
        }

        # Collect results from completed subtasks
        for subtask_id in task.subtasks:
            if subtask_id in self.completed_tasks:
                subtask = self.completed_tasks[subtask_id]
                if subtask.result:
                    if subtask.type == "find_information" and "sources" in subtask.result:
                        result["sources"] = subtask.result["sources"]
                    elif (
                        subtask.type == "analyze_content" and "key_points" in subtask.result
                    ):
                        result["key_points"] = subtask.result["key_points"]
                    elif subtask.type == "write_report" and "report" in subtask.result:
                        result["report"] = subtask.result["report"]

        return result
