"""Workflow executor for running Pepperpy workflows.

This module provides functionality to execute workflows with caching and metrics tracking,
ensuring efficient and monitored workflow execution.
"""

import uuid
from typing import Any, Dict, Optional

import structlog
from pydantic import BaseModel, ValidationError

from pepperpy.core.errors import ConfigurationError, ExecutionError
from pepperpy.hub.cache import WorkflowCache
from pepperpy.hub.registry import WorkflowRegistry
from pepperpy.monitoring.metrics import MetricsContext, MetricsTracker

log = structlog.get_logger("pepperpy.hub.executor")


class ExecutionConfig(BaseModel):
    """Configuration for workflow execution."""

    use_cache: bool = True
    cache_ttl: Optional[int] = None
    collect_metrics: bool = True
    execution_timeout: Optional[int] = None
    max_retries: int = 0
    retry_delay: int = 0


class WorkflowExecutor:
    """Executor for running Pepperpy workflows."""

    def __init__(
        self,
        registry: WorkflowRegistry,
        cache: Optional[WorkflowCache] = None,
        metrics: Optional[MetricsTracker] = None,
    ):
        """Initialize the workflow executor.

        Args:
        ----
            registry: Registry for accessing workflows
            cache: Optional cache for workflow results
            metrics: Optional metrics tracker

        """
        self.registry = registry
        self.cache = cache or WorkflowCache()
        self.metrics = metrics or MetricsTracker()

    async def execute(
        self,
        workflow_name: str,
        workflow_version: str,
        inputs: Dict[str, Any],
        config: Optional[ExecutionConfig] = None,
    ) -> Dict[str, Any]:
        """Execute a workflow.

        Args:
        ----
            workflow_name: Name of the workflow to execute
            workflow_version: Version of the workflow
            inputs: Input parameters for the workflow
            config: Optional execution configuration

        Returns:
        -------
            Workflow execution results

        Raises:
        ------
            ConfigurationError: If workflow configuration is invalid
            ExecutionError: If workflow execution fails

        """
        config = config or ExecutionConfig()
        execution_id = str(uuid.uuid4())

        # Try to get cached results
        if config.use_cache:
            try:
                cached_result = await self.cache.get(
                    workflow_name, workflow_version, inputs
                )
                if cached_result:
                    log.info(
                        "Using cached results",
                        workflow=workflow_name,
                        version=workflow_version,
                        execution_id=execution_id,
                    )
                    return cached_result
            except Exception as e:
                log.warning(
                    "Failed to get cached results",
                    workflow=workflow_name,
                    version=workflow_version,
                    execution_id=execution_id,
                    error=str(e),
                )

        # Get workflow configuration
        try:
            workflow = await self.registry.get_workflow(workflow_name, workflow_version)
        except Exception as e:
            raise ConfigurationError(f"Failed to get workflow configuration: {e}")

        # Validate inputs
        try:
            self._validate_inputs(workflow["content"]["input_schema"], inputs)
        except ValidationError as e:
            raise ConfigurationError(f"Invalid workflow inputs: {e}")

        # Execute workflow with metrics tracking
        async with MetricsContext(
            self.metrics,
            workflow_name=workflow_name,
            workflow_version=workflow_version,
            execution_id=execution_id,
        ) as metrics_ctx:
            try:
                result = await self._execute_workflow(
                    workflow, inputs, metrics_ctx, config
                )
            except Exception as e:
                log.error(
                    "Workflow execution failed",
                    workflow=workflow_name,
                    version=workflow_version,
                    execution_id=execution_id,
                    error=str(e),
                )
                raise ExecutionError(f"Workflow execution failed: {e}")

        # Validate output
        try:
            self._validate_output(workflow["content"]["output_schema"], result)
        except ValidationError as e:
            raise ExecutionError(f"Invalid workflow output: {e}")

        # Cache results
        if config.use_cache:
            try:
                await self.cache.set(
                    workflow_name,
                    workflow_version,
                    inputs,
                    result,
                    ttl=config.cache_ttl,
                )
            except Exception as e:
                log.warning(
                    "Failed to cache results",
                    workflow=workflow_name,
                    version=workflow_version,
                    execution_id=execution_id,
                    error=str(e),
                )

        return result

    async def _execute_workflow(
        self,
        workflow: Dict[str, Any],
        inputs: Dict[str, Any],
        metrics_ctx: MetricsContext,
        config: ExecutionConfig,
    ) -> Dict[str, Any]:
        """Execute a workflow's steps.

        Args:
        ----
            workflow: Workflow configuration
            inputs: Input parameters
            metrics_ctx: Metrics context
            config: Execution configuration

        Returns:
        -------
            Workflow execution results

        Raises:
        ------
            ExecutionError: If step execution fails

        """
        context = {
            "inputs": inputs,
            "results": {},
            "metadata": {},
        }

        for step in workflow["content"]["steps"]:
            step_name = step["name"]
            agent_name = step["agent"]
            action = step["action"]

            # Execute step with metrics tracking
            async with MetricsContext(
                self.metrics,
                step_name=step_name,
                agent_name=agent_name,
                action=action,
            ) as step_ctx:
                try:
                    # Get agent
                    agent = await self.registry.get_agent(agent_name)

                    # Prepare step inputs
                    step_inputs = self._prepare_step_inputs(step["inputs"], context)

                    # Execute step
                    step_result = await agent.execute(
                        action, step_inputs, config.execution_timeout
                    )

                    # Track token usage
                    if "token_usage" in step_result:
                        step_ctx.set_token_usage(step_result["token_usage"])

                    # Update context with step outputs
                    self._update_context(context, step["outputs"], step_result)

                except Exception as e:
                    log.error(
                        "Step execution failed",
                        step=step_name,
                        agent=agent_name,
                        action=action,
                        error=str(e),
                    )
                    raise ExecutionError(f"Step '{step_name}' execution failed: {e}")

        return context["results"]

    def _validate_inputs(self, schema: Dict[str, Any], inputs: Dict[str, Any]) -> None:
        """Validate workflow inputs against schema.

        Args:
        ----
            schema: Input schema
            inputs: Input parameters to validate

        Raises:
        ------
            ValidationError: If inputs are invalid

        """
        # TODO: Implement JSON Schema validation
        pass

    def _validate_output(self, schema: Dict[str, Any], output: Dict[str, Any]) -> None:
        """Validate workflow output against schema.

        Args:
        ----
            schema: Output schema
            output: Output to validate

        Raises:
        ------
            ValidationError: If output is invalid

        """
        # TODO: Implement JSON Schema validation
        pass

    def _prepare_step_inputs(
        self, input_mapping: Dict[str, str], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare inputs for a workflow step.

        Args:
        ----
            input_mapping: Mapping of step inputs to context values
            context: Current workflow context

        Returns:
        -------
            Prepared step inputs

        """
        # TODO: Implement template rendering for input mapping
        return {}

    def _update_context(
        self,
        context: Dict[str, Any],
        output_mapping: Dict[str, str],
        step_result: Dict[str, Any],
    ) -> None:
        """Update workflow context with step outputs.

        Args:
        ----
            context: Current workflow context
            output_mapping: Mapping of step outputs to context values
            step_result: Step execution results

        """
        # TODO: Implement template rendering for output mapping
        pass
