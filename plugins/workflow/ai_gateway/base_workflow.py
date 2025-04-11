"""Base workflow components for AI Gateway."""

import asyncio
import time
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from pepperpy.core.types import ModelProvider

from .metrics import MetricsCollector
from .retry import RetryConfig, with_retry
from .validation import ValidationResult, WorkflowValidator
from .workflow_state import WorkflowState, WorkflowStateManager

T = TypeVar("T")


@dataclass
class WorkflowResult(Generic[T]):
    """Workflow execution result with type safety."""

    is_success: bool
    data: T | None = None
    error_message: str | None = None
    validation_result: ValidationResult | None = None

    @classmethod
    def error(
        cls, message: str, validation: ValidationResult | None = None
    ) -> "WorkflowResult[T]":
        """Create error result."""
        return cls(
            is_success=False, error_message=message, validation_result=validation
        )

    @classmethod
    def success(
        cls, data: T, validation: ValidationResult | None = None
    ) -> "WorkflowResult[T]":
        """Create success result."""
        return cls(is_success=True, data=data, validation_result=validation)

    def and_then(self, f: callable) -> "WorkflowResult[Any]":
        """Chain operations, executing only if previous was successful."""
        if not self.is_success:
            return self
        try:
            return f(self.data)
        except Exception as e:
            return WorkflowResult.error(str(e))


class BaseWorkflow:
    """Enhanced workflow base with state management, retries and metrics."""

    def __init__(
        self,
        workflow_id: str | None = None,
        retry_config: RetryConfig | None = None,
        state_path: str = "/tmp/workflow_states",
        metrics_path: str = "/tmp/workflow_metrics",
        llm_provider: str = "mock",
        llm_model: str | None = None,
        use_rag: bool = False,
        use_vision: bool = False,
        tools: list[str] | None = None,
        validate_steps: bool = True,
        **kwargs: Any,
    ):
        # Initialize workflow components
        self.workflow_id = workflow_id or str(uuid.uuid4())
        self.retry_config = retry_config or RetryConfig()
        self.state_manager = WorkflowStateManager(state_path)
        self.metrics = MetricsCollector(metrics_path)
        self._state: WorkflowState | None = None
        self.validator = WorkflowValidator() if validate_steps else None

        # Initialize AI components
        builder = ModelProvider.create().with_llm(
            llm_provider, model=llm_model or "default"
        )
        if use_rag:
            builder = builder.with_rag("chroma")
        if use_vision:
            builder = builder.with_vision()
        if tools:
            builder = builder.with_tools(tools)

        self._provider_builder = builder
        self._provider: ModelProvider | None = None
        self.config = kwargs

    async def __aenter__(self) -> "BaseWorkflow":
        """Initialize workflow resources."""
        self._state = await self.state_manager.create_state(self.workflow_id)
        await self.metrics.load_metrics()
        self._provider = await self._provider_builder.build()
        return self

    async def __aexit__(self, *_: Any) -> None:
        """Clean up workflow resources."""
        if self._provider:
            await self._provider.cleanup()

    def _check_initialized(self) -> ModelProvider:
        """Check if workflow is initialized and return provider."""
        if not self._provider:
            raise RuntimeError("Workflow not initialized")
        return self._provider

    def _validate_step(
        self, step: dict[str, Any], path: str = ""
    ) -> ValidationResult | None:
        """Validate a single step if validation is enabled."""
        if self.validator:
            self.validator.validate_step(step, path)
            return self.validator._get_result()
        return None

    @with_retry()
    async def execute_step(self, step: dict[str, Any]) -> Any:
        """Execute single workflow step with retries."""
        # Validate step
        validation = self._validate_step(step)
        if validation and not validation.is_valid:
            raise ValueError(
                f"Invalid step configuration: {validation.errors[0].message}"
            )

        provider = self._check_initialized()
        step_type = step["type"]
        start_time = time.time()
        error = None

        try:
            # Execute step based on type
            if step_type == "rag":
                result = await self._execute_rag(step)
            elif step_type == "tool":
                result = await self._execute_tool(step)
            elif step_type == "chat":
                result = await self._execute_chat(step)
            else:
                raise ValueError(f"Unknown step type: {step_type}")

            # Record success
            duration = time.time() - start_time
            await self.metrics.record_operation(step_type, duration, True)

            # Update state
            if self._state:
                await self._state.update_step(step_type, result)

            return result

        except Exception as e:
            error = e
            # Record failure
            duration = time.time() - start_time
            await self.metrics.record_operation(step_type, duration, False, error)

            # Update state
            if self._state:
                await self._state.record_error(step_type, error)

            raise

    async def execute_chain(
        self, steps: Sequence[dict[str, Any]]
    ) -> WorkflowResult[list[dict[str, Any]]]:
        """Execute chain of steps with state tracking."""
        # Validate chain
        validation = None
        if self.validator:
            validation = self.validator.validate_chain(list(steps))
            if not validation.is_valid:
                return WorkflowResult.error(
                    f"Invalid chain configuration: {validation.errors[0].message}",
                    validation,
                )

        results: list[dict[str, Any]] = []

        for step in steps:
            try:
                result = await self.execute_step(step)
                results.append({
                    "type": step["type"],
                    "result": result,
                    "success": True,
                })
            except Exception as e:
                results.append({
                    "type": step["type"],
                    "error": str(e),
                    "success": False,
                })
                # Don't break chain on error unless specified
                if step.get("break_on_error", False):
                    break

        return WorkflowResult.success(results, validation)

    async def execute_parallel(
        self, operations: list[dict[str, Any]]
    ) -> WorkflowResult[list[dict[str, Any]]]:
        """Execute multiple operations in parallel."""
        # Validate parallel operations
        validation = None
        if self.validator:
            validation = self.validator.validate_parallel(operations)
            if not validation.is_valid:
                return WorkflowResult.error(
                    f"Invalid parallel configuration: {validation.errors[0].message}",
                    validation,
                )

        try:
            results = []
            tasks = []

            for op in operations:
                op_type = op["type"]
                if op_type == "chat":
                    task = self.execute_chat(op["messages"], op.get("model"))
                elif op_type == "rag":
                    task = self.execute_rag(op["query"], op.get("context_path"))
                elif op_type == "vision":
                    task = self.execute_vision(op["prompt"], op["image_path"])
                elif op_type == "tool":
                    task = self.execute_tool(op["tool_name"], op["inputs"])
                else:
                    raise ValueError(f"Unknown operation type: {op_type}")
                tasks.append(task)

            results = await asyncio.gather(*tasks)
            return WorkflowResult.success(
                [
                    {"type": op["type"], "result": result.data}
                    for op, result in zip(operations, results, strict=False)
                ],
                validation,
            )
        except Exception as e:
            return WorkflowResult.error(str(e), validation)

    async def get_state(self) -> dict[str, Any] | None:
        """Get current workflow state."""
        if self._state:
            return self._state.to_dict()
        return None

    async def get_metrics(self) -> dict[str, dict[str, Any]]:
        """Get workflow metrics."""
        return await self.metrics.get_all_metrics()

    # Implementation of step execution methods
    async def _execute_rag(self, step: dict[str, Any]) -> Any:
        """Execute RAG step."""
        provider = self._check_initialized()
        return await provider.rag.query(
            query=step["query"], context_path=step.get("context_path")
        )

    async def _execute_tool(self, step: dict[str, Any]) -> Any:
        """Execute tool step."""
        provider = self._check_initialized()
        tool = provider.get_tool(step["name"])
        return await tool.execute(step["inputs"])

    async def _execute_chat(self, step: dict[str, Any]) -> Any:
        """Execute chat step."""
        provider = self._check_initialized()
        return await provider.llm.chat(messages=step["messages"])

    async def execute_chat(
        self, messages: list[dict[str, str]], model: str | None = None
    ) -> WorkflowResult[dict[str, Any]]:
        """Execute a chat workflow."""
        try:
            provider = self._check_initialized()
            llm = provider.llm
            if model:
                llm = llm.with_model(model)
            response = await llm.chat(messages)
            return WorkflowResult.success(response)
        except Exception as e:
            return WorkflowResult.error(str(e))

    async def execute_rag(
        self,
        query: str,
        context_path: str | None = None,
        context_text: str | None = None,
    ) -> WorkflowResult[dict[str, Any]]:
        """Execute a RAG workflow."""
        try:
            provider = self._check_initialized()
            if context_path:
                await provider.rag.load_document(context_path)
            if context_text:
                await provider.rag.add_text(context_text)

            response = await provider.rag.query(query)
            return WorkflowResult.success(response)
        except Exception as e:
            return WorkflowResult.error(str(e))

    async def execute_vision(
        self, prompt: str, image_path: str
    ) -> WorkflowResult[dict[str, Any]]:
        """Execute a vision workflow."""
        try:
            provider = self._check_initialized()
            response = await provider.vision.analyze(prompt, image_path)
            return WorkflowResult.success(response)
        except Exception as e:
            return WorkflowResult.error(str(e))

    async def execute_tool(
        self, tool_name: str, inputs: dict[str, Any]
    ) -> WorkflowResult[dict[str, Any]]:
        """Execute a tool workflow."""
        try:
            provider = self._check_initialized()
            response = await provider.tools[tool_name].execute(inputs)
            return WorkflowResult.success(response)
        except Exception as e:
            return WorkflowResult.error(str(e))
