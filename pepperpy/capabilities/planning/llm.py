"""Language model-based planning implementation.

This module provides a planning implementation that uses a language model
to create and manage plans. All input and state types must be JSON-serializable
for compatibility with the language model interface.
"""

import json
import uuid
from typing import Any, TypeVar, cast

from pydantic import BaseModel, Field, validator

from pepperpy.common.errors import PlanningError
from pepperpy.core.types import Message, MessageType
from pepperpy.monitoring.tracing import tracer
from pepperpy.providers.base import BaseProvider

from .base import (
    BasePlanning,
    ExecutionResult,
    Plan,
    PlanStep,
)

# Type variables with constraints
T = TypeVar("T", dict, str)  # Input/State type - must be dict or str
A = TypeVar("A")  # Action type


class LLMConfig(BaseModel):
    """Language model configuration.

    Environment Variables:
        PEPPERPY_LLM_PROVIDER: Provider to use (default: openai)
        PEPPERPY_LLM_MODEL: Model to use (default: gpt-4)
        PEPPERPY_LLM_TEMPERATURE: Sampling temperature (default: 0.7)
        PEPPERPY_LLM_MAX_TOKENS: Maximum tokens to generate (default: 1000)

    Validation:
        - provider must be a registered provider
        - model must be available for the selected provider
        - temperature must be between 0 and 1
        - max_tokens must be positive
    """

    provider: str = Field(
        description="Provider to use for language model",
    )
    model: str = Field(
        description="Model to use for planning",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Temperature for model sampling",
    )
    max_tokens: int = Field(
        default=1000,
        gt=0,
        description="Maximum tokens to generate",
    )
    stop_sequences: list[str] | None = Field(
        default=None,
        description="Optional sequences to stop generation",
    )

    @validator("provider")
    def validate_provider(self, v: str) -> str:
        """Validate that the provider is registered."""
        if v not in ["openai", "anthropic", "local"]:
            raise ValueError(f"Provider {v} is not registered")
        return v

    @validator("model")
    def validate_model(self, v: str, values: dict[str, Any]) -> str:
        """Validate that the model is available for the provider."""
        provider = values.get("provider")
        if not provider:
            return v

        valid_models = {
            "openai": ["gpt-4", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-opus", "claude-3-sonnet"],
            "local": ["llama-2", "mistral-7b"],
        }

        if v not in valid_models.get(provider, []):
            raise ValueError(f"Model {v} not available for provider {provider}")
        return v


class LLMPlanning(BasePlanning[T, T, A]):
    """Language model-based planning implementation.

    This implementation requires that all type parameters (T, S, A) are
    JSON-serializable, as they need to be converted to strings for the
    language model interface.

    Type Parameters:
        T: Input data type - must be JSON-serializable
        S: State type - must be JSON-serializable
        A: Action type - must be JSON-serializable

    Example:
        >>> config = LLMConfig(
        ...     provider="openai",
        ...     model="gpt-4",
        ...     temperature=0.7
        ... )
        >>> provider = OpenAIProvider(api_key="...")
        >>> planner = LLMPlanning(config, provider)
        >>> plan = await planner.plan(
        ...     input_data={"goal": "Make coffee"},
        ...     state={"coffee_maker": "ready"}
        ... )
        >>> assert len(plan.steps) > 0
    """

    def __init__(
        self,
        config: LLMConfig,
        provider: BaseProvider,
    ):
        """Initialize the planning implementation.

        Args:
            config: Language model configuration
            provider: Provider instance for language model

        Raises:
            ValueError: If config is invalid
            TypeError: If provider is not compatible with config
        """
        if not isinstance(config, LLMConfig):
            raise TypeError("Config must be an instance of LLMConfig")
        if not isinstance(provider, BaseProvider):
            raise TypeError("Provider must be an instance of BaseProvider")
        if provider.name != config.provider:
            msg = (
                f"Provider {provider.name} does not match "
                f"config provider {config.provider}"
            )
            raise ValueError(msg)

        self.config = config
        self.provider = provider

    def _validate_json_serializable(self, data: Any, name: str) -> None:
        """Validate that data is JSON-serializable.

        Args:
            data: Data to validate
            name: Name of the data for error messages

        Raises:
            TypeError: If data is not JSON-serializable
        """
        try:
            json.dumps(data)
        except (TypeError, ValueError) as e:
            raise TypeError(f"{name} must be JSON-serializable: {e}") from e

    def _serialize_data(self, data: T | A, name: str = "data") -> str:
        r"""Serialize data to JSON string.

        Args:
            data: Data to serialize (must be JSON-serializable)
            name: Name of the data for error messages

        Returns:
            JSON string representation

        Raises:
            PlanningError: If data cannot be serialized

        Example:
            >>> planner = LLMPlanning(config, provider)
            >>> json_str = planner._serialize_data({"key": "value"})
            >>> assert json_str == '{\n  "key": "value"\n}'
        """
        try:
            # First validate JSON serializability
            self._validate_json_serializable(data, name)

            # Then serialize with proper formatting
            return data if isinstance(data, str) else json.dumps(data, indent=2)
        except TypeError as e:
            raise PlanningError(f"Failed to serialize {name}: {e}") from e

    def _validate_step_dependencies(
        self, step: PlanStep[A], all_steps: list[PlanStep[A]]
    ) -> None:
        """Validate step dependencies.

        Args:
            step: Step to validate
            all_steps: All steps in the plan

        Raises:
            PlanningError: If dependencies are invalid
        """
        step_ids = {str(s.id) for s in all_steps}
        for dep in step.dependencies:
            if str(dep) not in step_ids:
                raise PlanningError(f"Step {step.id} has invalid dependency: {dep}")

    def _make_prompt(
        self,
        input_data: T,
        state: T,
        failed_plan: Plan[A] | None = None,
        plans_to_merge: list[Plan[A]] | None = None,
    ) -> str:
        """Create a prompt for the language model.

        Args:
            input_data: Input data to plan from
            state: Current state
            failed_plan: Failed plan to replan from, if any
            plans_to_merge: Plans to merge, if any

        Returns:
            Generated prompt
        """
        # Convert input data and state to strings if needed
        input_str = str(input_data)
        state_str = str(state)

        # Build prompt based on available data
        prompt_parts = [
            f"Input: {input_str}",
            f"State: {state_str}",
        ]

        if failed_plan:
            prompt_parts.append(f"Failed Plan: {failed_plan!s}")
        elif plans_to_merge:
            prompt_parts.append("Plans to Merge:")
            for i, plan in enumerate(plans_to_merge):
                prompt_parts.append(f"Plan {i + 1}: {plan!s}")

        return "\n".join(prompt_parts)

    def _parse_steps(self, steps_json: list[dict[str, Any]]) -> list[PlanStep[A]]:
        """Parse steps from JSON response."""
        with tracer.start_as_current_span("parse_steps") as span:
            try:
                steps = []
                for i, step_data in enumerate(steps_json):
                    try:
                        step_id = step_data.get("id")
                        if not step_id:
                            raise ValueError(f"Step {i} missing id")
                        try:
                            step_id = uuid.UUID(step_id)
                        except ValueError as e:
                            raise ValueError(
                                f"Invalid UUID format for step {i} id: {e}"
                            ) from e

                        # Validate dependencies format
                        deps = step_data.get("dependencies", [])
                        if not isinstance(deps, list):
                            raise ValueError(
                                f"Dependencies for step {i} must be a list"
                            )

                        # Validate metadata
                        metadata = step_data.get("metadata", {})
                        if not isinstance(metadata, dict):
                            raise ValueError(
                                f"Metadata for step {i} must be a dictionary"
                            )

                        # Cast action to A type since we know it's valid from model
                        # This is safe because A must be JSON-serializable
                        step = PlanStep[A](
                            id=step_id,
                            action=cast(A, step_data["action"]),
                            dependencies=[uuid.UUID(d) for d in deps],
                            metadata=metadata,
                        )
                        steps.append(step)

                    except KeyError as e:
                        raise ValueError(f"Step {i} missing required field: {e}") from e

                return steps

            except Exception as e:
                span.record_exception(e)
                raise PlanningError(f"Failed to parse plan steps: {e}") from e

    async def plan(self, input_data: T, state: T) -> Plan[A]:
        """Create a plan from input data and current state.

        Args:
            input_data: Input data to plan from
            state: Current state to plan for

        Returns:
            Generated plan

        Raises:
            PlanningError: If planning fails
            TypeError: If state or input_data are invalid types
        """
        with tracer.start_as_current_span("plan") as span:
            try:
                # Generate plan using language model
                prompt = self._make_prompt(input_data, state)
                response = await self.provider.generate(
                    messages=[
                        Message(
                            type=MessageType.QUERY,
                            sender="planner",
                            receiver=None,
                            content={"prompt": prompt},
                        )
                    ],
                    model=self.config.model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    stop_sequences=self.config.stop_sequences,
                )

                # Parse response
                try:
                    result = response.content
                except json.JSONDecodeError as e:
                    raise PlanningError(f"Invalid JSON response: {e}") from e

                # Extract and validate steps
                steps = self._parse_steps(result["steps"])

                return Plan[A](steps=steps)

            except Exception as e:
                span.record_exception(e)
                span.set_attribute(
                    "error",
                    {
                        "type": type(e).__name__,
                        "message": str(e),
                    },
                )
                if isinstance(e, TypeError | ValueError | PlanningError):
                    raise
                raise PlanningError(f"Planning failed: {e}") from e

    async def validate(self, plan: Plan[A], state: T) -> bool:
        """Validate a plan against the current state.

        Args:
            plan: Plan to validate
            state: Current state

        Returns:
            True if plan is valid, False otherwise

        Raises:
            PlanningError: If validation fails
        """
        with tracer.start_as_current_span("validate") as span:
            try:
                # Generate validation prompt
                prompt = self._make_prompt(
                    input_data=state,  # Use state as input data
                    state=state,
                    failed_plan=plan,
                )

                # Get response from language model
                response = await self.provider.generate(
                    messages=[
                        Message(
                            type=MessageType.QUERY,
                            sender="planner",
                            receiver=None,
                            content={"prompt": prompt},
                        )
                    ],
                    model=self.config.model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    stop_sequences=self.config.stop_sequences,
                )

                # Parse response
                try:
                    result = response.content
                    return bool(result.get("valid", False))
                except KeyError as e:
                    raise PlanningError(f"Invalid validation response: {e}") from e

            except Exception as e:
                span.record_exception(e)
                span.set_attribute(
                    "error",
                    {
                        "type": type(e).__name__,
                        "message": str(e),
                    },
                )
                raise PlanningError(f"Validation failed: {e}") from e

    async def execute(self, plan: Plan[A], state: T) -> ExecutionResult[A]:
        """Execute a plan.

        Args:
            plan: Plan to execute
            state: Current state

        Returns:
            ExecutionResult containing:
                success: Whether execution succeeded
                completed_steps: Steps completed before failure/completion
                failed_step: Step that failed, if any
                error: Error that occurred, if any
        """
        with tracer.start_as_current_span("execute") as span:
            try:
                completed_steps: list[PlanStep[A]] = []
                for step in plan.steps:
                    try:
                        # Execute step
                        prompt = self._make_prompt(
                            input_data=state,  # Use state as input data
                            state=state,
                        )
                        response = await self.provider.generate(
                            messages=[
                                Message(
                                    type=MessageType.QUERY,
                                    sender="planner",
                                    receiver=None,
                                    content={"prompt": prompt},
                                )
                            ],
                            model=self.config.model,
                            temperature=self.config.temperature,
                            max_tokens=self.config.max_tokens,
                            stop_sequences=self.config.stop_sequences,
                        )

                        # Parse response
                        try:
                            result_json = response.content
                        except KeyError as e:
                            raise PlanningError(f"Invalid JSON response: {e}") from e

                        # Extract success status
                        if not result_json.get("success", False):
                            return ExecutionResult[A](
                                success=False,
                                completed_steps=completed_steps,
                                failed_step=step,
                                error=PlanningError(
                                    f"Step {step.id} failed: {result_json.get('error')}"
                                ),
                            )

                        completed_steps.append(step)

                    except Exception as e:
                        return ExecutionResult[A](
                            success=False,
                            completed_steps=completed_steps,
                            failed_step=step,
                            error=PlanningError(f"Step {step.id} failed: {e}"),
                        )

                return ExecutionResult[A](
                    success=True,
                    completed_steps=completed_steps,
                    failed_step=None,
                    error=None,
                )

            except Exception as e:
                span.record_exception(e)
                span.set_attribute(
                    "error",
                    {
                        "type": type(e).__name__,
                        "message": str(e),
                    },
                )
                raise PlanningError(f"Execution failed: {e}") from e

    async def optimize(self, plan: Plan[A], state: T) -> Plan[A]:
        """Optimize a plan for better performance.

        Args:
            plan: Plan to optimize
            state: Current state

        Returns:
            Optimized plan

        Raises:
            PlanningError: If optimization fails
        """
        with tracer.start_as_current_span("optimize") as span:
            try:
                # Generate optimization prompt
                prompt = self._make_prompt(
                    input_data=state,
                    state=state,
                    failed_plan=None,
                )

                # Get response from language model
                response = await self.provider.generate(
                    messages=[
                        Message(
                            type=MessageType.QUERY,
                            sender="planner",
                            receiver=None,
                            content={"prompt": prompt},
                        )
                    ],
                    model=self.config.model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    stop_sequences=self.config.stop_sequences,
                )

                # Parse response
                try:
                    result = response.content
                except json.JSONDecodeError as e:
                    raise PlanningError(f"Invalid JSON response: {e}") from e

                # Extract and validate steps
                steps = self._parse_steps(result["steps"])

                return Plan[A](steps=steps)

            except Exception as e:
                span.record_exception(e)
                span.set_attribute(
                    "error",
                    {
                        "type": type(e).__name__,
                        "message": str(e),
                    },
                )
                raise PlanningError(f"Optimization failed: {e}") from e

    async def merge(self, plans: list[Plan[A]], state: T) -> Plan[A]:
        """Merge multiple plans into a single plan.

        Args:
            plans: Plans to merge
            state: Current state

        Returns:
            Merged plan

        Raises:
            PlanningError: If merging fails
        """
        with tracer.start_as_current_span("merge") as span:
            try:
                # Generate merge prompt
                prompt = self._make_prompt(
                    input_data=state,  # Use state as input data
                    state=state,
                    plans_to_merge=plans,
                )

                # Get response from language model
                response = await self.provider.generate(
                    messages=[
                        Message(
                            type=MessageType.QUERY,
                            sender="planner",
                            receiver=None,
                            content={"prompt": prompt},
                        )
                    ],
                    model=self.config.model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    stop_sequences=self.config.stop_sequences,
                )

                # Parse response
                try:
                    result = response.content
                except json.JSONDecodeError as e:
                    raise PlanningError(f"Invalid JSON response: {e}") from e

                # Extract and validate steps
                steps = self._parse_steps(result["steps"])

                return Plan[A](steps=steps)

            except Exception as e:
                span.record_exception(e)
                span.set_attribute(
                    "error",
                    {
                        "type": type(e).__name__,
                        "message": str(e),
                    },
                )
                raise PlanningError(f"Merging failed: {e}") from e

    async def replan(self, plan: Plan[A], state: T) -> Plan[A]:
        """Create a new plan based on a failed plan.

        Args:
            plan: Plan that failed
            state: Current state

        Returns:
            New plan

        Raises:
            PlanningError: If replanning fails or state conversion fails
            TypeError: If state cannot be safely converted to input type
        """
        with tracer.start_as_current_span("replan") as span:
            try:
                # Generate new plan using state as input data
                return await self.plan(state, state)

            except Exception as e:
                span.record_exception(e)
                span.set_attribute(
                    "error",
                    {
                        "type": type(e).__name__,
                        "message": str(e),
                    },
                )
                if isinstance(e, TypeError | ValueError | PlanningError):
                    raise
                raise PlanningError(f"Replanning failed: {e}") from e
