"""Hybrid orchestrator for combining multiple reasoning frameworks."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, ClassVar, cast

from pepperpy.agents.base.base_agent import BaseAgent
from pepperpy.agents.chain_of_thought import ChainOfThoughtAgent
from pepperpy.agents.react import ReActAgent
from pepperpy.agents.tree_of_thoughts import TreeOfThoughtsAgent
from pepperpy.agents.types import AgentConfig, AgentResponse


@dataclass
class FrameworkError(Exception):
    """Error in framework processing."""

    framework: str
    error: str


class HybridOrchestrator(BaseAgent):
    """Orchestrates multiple reasoning frameworks.

    This agent combines different reasoning approaches:
    1. Analyzes the task to choose best framework
    2. Delegates to appropriate framework
    3. Combines results if needed
    4. Handles fallbacks
    """

    # Cast each agent class to type[BaseAgent] to satisfy the type checker
    FRAMEWORKS: ClassVar[dict[str, type[BaseAgent]]] = {
        "react": cast(type[BaseAgent], ReActAgent),
        "chain_of_thought": cast(type[BaseAgent], ChainOfThoughtAgent),
        "tree_of_thoughts": cast(type[BaseAgent], TreeOfThoughtsAgent),
    }

    def __init__(self, config: AgentConfig) -> None:
        """Initialize the hybrid orchestrator.

        Args:
            config: Agent configuration
        """
        super().__init__(config)
        self.agents: dict[str, BaseAgent] = {}

    async def initialize(self) -> None:
        """Initialize agent resources."""
        # Initialize all frameworks
        for name, framework in self.FRAMEWORKS.items():
            self.agents[name] = framework(self.config)
            await self.agents[name].initialize()

    async def process(
        self, input_data: dict[str, Any], context: dict[str, Any] | None = None
    ) -> AgentResponse:
        """Process input using best framework.

        Args:
            input_data: Input data to process
            context: Optional context information

        Returns:
            Agent's response with metadata
        """
        context = context or {}

        try:
            # Choose best framework
            framework = await self._choose_framework(input_data, context)
            if framework not in self.agents:
                raise FrameworkError(
                    framework=framework, error=f"Framework {framework} not initialized"
                )

            # Process with chosen framework
            agent = self.agents[framework]
            response = await agent.process(input_data, context)

            # Add framework info to metadata
            if response.metadata is None:
                response.metadata = {}
            response.metadata["framework_used"] = framework
            return response

        except Exception as e:
            # Try fallback if primary fails
            try:
                return await self._handle_fallback(input_data, context, str(e))
            except Exception as fallback_e:
                return AgentResponse(
                    text="Error processing request",
                    metadata={
                        "primary_error": str(e),
                        "fallback_error": str(fallback_e),
                    },
                )

    async def process_stream(
        self, input_data: dict[str, Any], context: dict[str, Any] | None = None
    ) -> AsyncIterator[str]:
        """Process input and stream responses.

        Args:
            input_data: Input data to process
            context: Optional context information

        Returns:
            Async iterator of response chunks
        """
        context = context or {}

        try:
            # Choose best framework
            framework = await self._choose_framework(input_data, context)
            if framework not in self.agents:
                raise FrameworkError(
                    framework=framework, error=f"Framework {framework} not initialized"
                )

            yield f"Using {framework} framework\n"

            # Stream from chosen framework
            agent = self.agents[framework]
            async for chunk in agent.process_stream(input_data, context):
                yield chunk

        except Exception as e:
            yield f"Error: {e!s}\n"
            yield "Attempting fallback...\n"

            # Try fallback if primary fails
            try:
                fallback_response = await self._handle_fallback(
                    input_data, context, str(e)
                )
                yield f"Fallback response: {fallback_response.text}"
            except Exception as fallback_e:
                yield f"Fallback also failed: {fallback_e!s}"

    async def cleanup(self) -> None:
        """Clean up resources."""
        for agent in self.agents.values():
            await agent.cleanup()

    async def _choose_framework(
        self, input_data: dict[str, Any], context: dict[str, Any]
    ) -> str:
        """Choose best framework for the task.

        Args:
            input_data: Input data to process
            context: Current context

        Returns:
            Name of chosen framework

        Raises:
            Exception: If selection fails
        """
        message = input_data.get("message", "").lower()

        # Simple heuristic-based selection
        if any(word in message for word in ["step", "explain", "how to"]):
            return "chain_of_thought"
        elif any(word in message for word in ["explore", "consider", "compare"]):
            return "tree_of_thoughts"
        else:
            return "react"  # Default framework

    async def _handle_fallback(
        self, input_data: dict[str, Any], context: dict[str, Any], error: str
    ) -> AgentResponse:
        """Handle failure with fallback strategy.

        Args:
            input_data: Input data to process
            context: Current context
            error: Original error message

        Returns:
            Fallback response

        Raises:
            Exception: If fallback fails
        """
        # Try simpler framework as fallback
        fallback_framework = "chain_of_thought"

        # Get current framework from error if possible
        if isinstance(error, FrameworkError):
            if error.framework == "chain_of_thought":
                fallback_framework = "react"

        if fallback_framework not in self.agents:
            raise FrameworkError(
                framework=fallback_framework,
                error=f"Fallback framework {fallback_framework} not initialized",
            )

        fallback_agent = self.agents[fallback_framework]
        response = await fallback_agent.process(input_data, context)

        # Add fallback info to metadata
        if response.metadata is None:
            response.metadata = {}
        response.metadata.update(
            {
                "is_fallback": True,
                "original_error": error,
                "fallback_framework": fallback_framework,
            }
        )

        return response
