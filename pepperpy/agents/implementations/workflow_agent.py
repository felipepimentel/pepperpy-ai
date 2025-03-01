"""Workflow agent module for the Pepperpy framework.

This module provides the workflow agent implementation that can execute workflow steps.
It defines the workflow agent class, configuration, and step execution capabilities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from pepperpy.agents.base import AgentConfig, BaseAgent
from pepperpy.core.errors import AgentError
from pepperpy.workflows.base import WorkflowStep
from pepperpy.workflows.core.cache import WorkflowCache
from pepperpy.workflows.core.manager import WorkflowManager


@dataclass
class WorkflowAgentConfig(AgentConfig):
    """Workflow agent configuration."""

    step_types: List[str] = field(default_factory=list)
    max_concurrent_steps: int = 1
    step_timeout: float = 3600.0
    step_retry: Dict[str, Any] = field(default_factory=dict)
    use_cache: bool = True
    cache_ttl: int = 3600  # 1 hour in seconds


class WorkflowAgent(BaseAgent):
    """Workflow agent that can execute workflow steps.

    This agent type is designed for executing steps within a workflow,
    handling step-specific logic and maintaining step state.
    """

    def __init__(
        self,
        config: Optional[WorkflowAgentConfig] = None,
        workflow_manager: Optional[WorkflowManager] = None,
    ) -> None:
        """Initialize workflow agent.

        Args:
            config: Optional workflow agent configuration
            workflow_manager: Optional workflow manager instance
        """
        super().__init__(config or WorkflowAgentConfig(name=self.__class__.__name__))
        self._active_steps: Dict[str, Any] = {}
        self._workflow_manager = workflow_manager
        self._step_cache: Optional[WorkflowCache] = None

    @property
    def step_types(self) -> List[str]:
        """Get supported step types."""
        if isinstance(self.config, WorkflowAgentConfig):
            return self.config.step_types
        return []

    async def _initialize(self) -> None:
        """Initialize workflow agent."""
        # Validate step types
        if not self.step_types:
            raise AgentError("No step types configured")

        # Initialize step cache if enabled
        if isinstance(self.config, WorkflowAgentConfig) and self.config.use_cache:
            self._step_cache = WorkflowCache(
                namespace=f"{self.config.name}_steps", default_ttl=self.config.cache_ttl
            )

        # Initialize step metrics
        for step_type in self.step_types:
            await self._metrics_manager.create_counter(
                name=f"{self.config.name}_step_{step_type}_total",
                description=f"Total number of {step_type} steps executed",
                labels={"status": "success"},
            )
            await self._metrics_manager.create_histogram(
                name=f"{self.config.name}_step_{step_type}_seconds",
                description=f"Execution time in seconds for {step_type} steps",
                labels={"status": "success"},
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            )

    async def _execute(self, step: WorkflowStep, **kwargs: Any) -> Any:
        """Execute a workflow step.

        Args:
            step: Step to execute
            **kwargs: Step parameters

        Returns:
            Step result

        Raises:
            AgentError: If step execution fails
        """
        if step.action not in self.step_types:
            raise AgentError(f"Unsupported step type: {step.action}")

        if isinstance(self.config, WorkflowAgentConfig):
            if len(self._active_steps) >= self.config.max_concurrent_steps:
                raise AgentError("Maximum concurrent steps reached")

        # Check cache first if enabled
        if self._step_cache:
            cached_result = await self._step_cache.get_step_result(step, kwargs)
            if cached_result is not None:
                self._logger.info(f"Cache hit for step {step.name}")
                return cached_result

        start_time = datetime.now()
        try:
            # Track active step
            self._active_steps[step.name] = {
                "start_time": start_time,
                "action": step.action,
                "parameters": kwargs,
            }

            # Execute step based on type
            result = None
            if step.action == "data_transformation":
                result = await self._transform_data(step, **kwargs)
            elif step.action == "model_inference":
                result = await self._run_inference(step, **kwargs)
            elif step.action == "api_call":
                result = await self._call_api(step, **kwargs)
            else:
                raise AgentError(f"Step type not implemented: {step.action}")

            # Cache result if enabled
            if self._step_cache:
                await self._step_cache.set_step_result(step, kwargs, result)

            # Update metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            await self._metrics_manager.increment_counter(
                f"{self.config.name}_step_{step.action}_total",
                labels={"status": "success"},
            )
            await self._metrics_manager.observe_histogram(
                f"{self.config.name}_step_{step.action}_seconds",
                execution_time,
                labels={"status": "success"},
            )

            return result

        except Exception as e:
            # Update metrics for failed step
            await self._metrics_manager.increment_counter(
                f"{self.config.name}_step_{step.action}_total",
                labels={"status": "error"},
            )
            raise AgentError(f"Failed to execute step {step.name}: {e}") from e
        finally:
            # Remove from active steps
            self._active_steps.pop(step.name, None)

    async def _transform_data(self, step: WorkflowStep, **kwargs: Any) -> Any:
        """Transform data according to step configuration.

        Args:
            step: Step configuration
            **kwargs: Transformation parameters

        Returns:
            Transformed data
        """
        # TODO: Implement data transformation
        return kwargs.get("data")

    async def _run_inference(self, step: WorkflowStep, **kwargs: Any) -> Any:
        """Run model inference according to step configuration.

        Args:
            step: Step configuration
            **kwargs: Inference parameters

        Returns:
            Inference results
        """
        # TODO: Implement model inference
        return {"predictions": []}

    async def _call_api(self, step: WorkflowStep, **kwargs: Any) -> Any:
        """Make API call according to step configuration.

        Args:
            step: Step configuration
            **kwargs: API parameters

        Returns:
            API response
        """
        # TODO: Implement API call
        return {"status": "success"}

    async def _cleanup(self) -> None:
        """Clean up workflow agent."""
        # Cancel any active steps
        for step in self._active_steps.values():
            try:
                await step.cancel()
            except Exception:
                pass
        self._active_steps.clear()

        # Clean up cache
        if self._step_cache:
            await self._step_cache.clear()
            self._step_cache = None
