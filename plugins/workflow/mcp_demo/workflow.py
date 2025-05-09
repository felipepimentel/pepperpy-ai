"""MCP Demo Workflow.

This module provides a workflow that demonstrates the complete integration of MCP server and client.
"""

import os
import uuid
from typing import Any

from openai import AsyncOpenAI

from pepperpy.core.logging import get_logger
from pepperpy.mcp.client.providers.http import HTTPClientProvider
from pepperpy.mcp.protocol import (
    MCPOperationType,
    MCPRequest,
    MCPResponse,
    MCPStatusCode,
)
from pepperpy.mcp.server.providers.http import HTTPServerProvider
from pepperpy.plugin.base import PepperpyPlugin
from pepperpy.workflow import WorkflowProvider

# Use absolute import for agent_orchestration
from plugins.workflow.mcp_demo.agent_orchestration import AgentOrchestrator


class SimpleLLMAdapter:
    """Simple adapter for LLM providers."""

    def __init__(
        self, provider_type: str, model: str, api_key: str | None = None
    ) -> None:
        """Initialize the LLM adapter.

        Args:
            provider_type: Provider type (only openai supported for now)
            model: Model ID to use
            api_key: API key (if required)
        """
        self.provider_type = provider_type
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.client: Any = None
        self.initialized = False
        self.logger = get_logger("llm.adapter")

    async def initialize(self) -> None:
        """Initialize the client."""
        if self.initialized:
            return

        if self.provider_type == "openai":
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.logger.info(f"Initialized OpenAI client with model {self.model}")
        else:
            raise ValueError(f"Unsupported provider type: {self.provider_type}")

        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.client and hasattr(self.client, "close"):
            await self.client.close()
        self.client = None
        self.initialized = False

    async def chat(self, messages: list[dict[str, str]]) -> str:
        """Generate a chat response.

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            Generated response text
        """
        if not self.initialized:
            await self.initialize()

        if self.provider_type == "openai":
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
            )
            return response.choices[0].message.content or ""
        else:
            raise ValueError(f"Unsupported provider type: {self.provider_type}")


class MCPDemoWorkflow(WorkflowProvider, PepperpyPlugin):
    """Workflow provider that demonstrates MCP server and client integration."""

    # Explicitly define plugin attributes
    plugin_type = "workflow"
    provider_name = "mcp_demo"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize MCP demo workflow."""
        super().__init__(config=config or {})
        self.logger = get_logger("workflow.mcp_demo")
        self.server: HTTPServerProvider | None = None
        self.client: HTTPClientProvider | None = None
        self.llm_provider = None
        self.orchestrator: AgentOrchestrator | None = None
        self.initialized = False
        self.demo_duration = 60
        self.host = "0.0.0.0"
        self.port = 8000
        self.provider_type = "http"
        self.llm_provider_type = "openai"
        self.llm_model = "gpt-3.5-turbo"
        self.tool_registry = {}

    async def _initialize_resources(self) -> None:
        """Initialize the workflow resources.

        This method is called by the parent initialize() method.
        """
        config = self.config
        self.logger.info("Initializing MCP demo workflow")

        # Configure connection parameters
        self.host = config.get("host", self.host)
        self.port = config.get("port", self.port)
        self.provider_type = config.get("provider_type", self.provider_type)
        self.llm_provider_type = config.get("llm_provider", self.llm_provider_type)
        self.llm_model = config.get("llm_model", self.llm_model)
        self.demo_duration = config.get("demo_duration", self.demo_duration)

        # Initialize server (don't start it yet)
        self.server = HTTPServerProvider(host=self.host, port=self.port)
        await self.server.initialize()

        # Initialize LLM provider
        self.llm_provider = SimpleLLMAdapter(
            provider_type=self.llm_provider_type,
            model=self.llm_model,
            api_key=config.get("openai_api_key"),
        )
        await self.llm_provider.initialize()

        # Register tools with the server
        await self._register_server_tools()

        # Initialize client (don't connect yet)
        self.client = HTTPClientProvider(url=f"http://{self.host}:{self.port}")
        await self.client.initialize()

        # Initialize agent orchestrator
        # Use type ignore to handle the client type incompatibility
        from typing import Any, cast

        self.orchestrator = AgentOrchestrator(client=cast(Any, self.client))
        await self.orchestrator.initialize()

    async def _cleanup_resources(self) -> None:
        """Clean up resources used by the workflow.

        This method is called by the parent cleanup() method.
        """
        self.logger.info("Cleaning up MCP demo workflow")

        if self.orchestrator:
            await self.orchestrator.cleanup()
            self.orchestrator = None

        if self.server:
            await self.server.cleanup()
            self.server = None

        if self.client:
            await self.client.cleanup()
            self.client = None

        if self.llm_provider:
            await self.llm_provider.cleanup()
            self.llm_provider = None

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the workflow.

        Args:
            input_data: Input data for the workflow

        Returns:
            Workflow execution results

        Raises:
            WorkflowError: If execution fails
        """
        if not self.initialized:
            raise ValueError("Workflow not initialized")

        if not self.server or not self.client:
            raise ValueError("Server or client not initialized")

        # Get workflow type from input
        workflow_type = input_data.get("workflow_type", "default")

        try:
            # Ensure server is not already running
            if hasattr(self.server, "running") and self.server.running:
                self.logger.warning("Server is already running, stopping it first")
                await self.server.stop()

            # Start the server and wait a moment for it to be ready
            self.logger.info("Starting MCP server...")
            await self.server.start()

            # Small delay to ensure server is ready
            import asyncio

            await asyncio.sleep(2)

            # Connect client to server
            self.logger.info("Connecting client to server...")
            await self.client.connect(f"http://{self.host}:{self.port}")

            # Execute the requested workflow type
            if workflow_type == "agent":
                return await self._run_agent_workflow(input_data)
            else:
                # Run the default client operations
                self.logger.info("Running demo client operations...")
                return await self._run_demo_client()

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            import traceback

            self.logger.error(traceback.format_exc())
            return {"status": "error", "message": str(e)}
        finally:
            # Stop the server
            if self.server and hasattr(self.server, "running") and self.server.running:
                self.logger.info("Stopping MCP server...")
                await self.server.stop()

    async def _run_agent_workflow(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Run an agent-based workflow.

        Args:
            input_data: Input data for the workflow, should contain 'task' and optionally 'workflow'

        Returns:
            Agent workflow execution results
        """
        if not self.orchestrator:
            return {"status": "error", "message": "Agent orchestrator not initialized"}

        task = input_data.get("task")
        if not task:
            return {"status": "error", "message": "No task provided for agent workflow"}

        # Get optional workflow sequence
        workflow = input_data.get("workflow")

        # Execute the workflow
        self.logger.info(f"Executing agent workflow for task: {task}")
        result = await self.orchestrator.execute_workflow(task, workflow)

        return {
            "status": "success" if result.get("status") == "success" else "error",
            "workflow_type": "agent",
            "agents_used": workflow or ["planner", "executor", "critic"],
            "result": result,
        }

    async def _register_server_tools(self) -> None:
        """Register custom tools with the server."""
        if not self.server:
            return

        # Register the LLM provider for chat
        await self.server.register_model(
            model_id=self.llm_model, model=self.llm_provider
        )

        # Register custom tool handlers
        await self.server.register_handler(
            "calculate", self._tool_calculate, is_stream=False
        )
        await self.server.register_handler(
            "get_weather", self._tool_weather, is_stream=False
        )
        await self.server.register_handler(
            "translate", self._tool_translate, is_stream=False
        )

    async def _handle_chat_request(self, request: MCPRequest) -> MCPResponse:
        """Handle a chat request using the LLM provider.

        Args:
            request: The chat request.

        Returns:
            The chat response.
        """
        if not self.llm_provider:
            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.ERROR,
                error="LLM provider not initialized",
            )

        try:
            messages = request.inputs.get("messages", [])
            result = await self.llm_provider.chat(messages)
            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.SUCCESS,
                outputs={"content": result},
            )
        except Exception as e:
            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.ERROR,
                error=str(e),
            )

    async def _tool_calculate(self, request: MCPRequest) -> MCPResponse:
        """Handle calculate tool requests.

        Args:
            request: The MCP request.

        Returns:
            The MCP response.
        """
        try:
            messages = request.inputs.get("messages", [])
            if not messages:
                return MCPResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    status=MCPStatusCode.ERROR,
                    error="No messages provided",
                )

            content = messages[-1].get("content", "")
            if not content.startswith("calculate:"):
                return MCPResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    status=MCPStatusCode.ERROR,
                    error="Invalid calculate request format",
                )

            expression = content.replace("calculate:", "").strip()
            result = eval(
                expression
            )  # Note: In production, use a safer evaluation method

            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.SUCCESS,
                outputs={"result": str(result)},
            )
        except Exception as e:
            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.ERROR,
                error=str(e),
            )

    async def _tool_weather(self, request: MCPRequest) -> MCPResponse:
        """Handle weather tool requests.

        Args:
            request: The MCP request.

        Returns:
            The MCP response.
        """
        try:
            messages = request.inputs.get("messages", [])
            if not messages:
                return MCPResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    status=MCPStatusCode.ERROR,
                    error="No messages provided",
                )

            content = messages[-1].get("content", "")
            if not content.startswith("get_weather:"):
                return MCPResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    status=MCPStatusCode.ERROR,
                    error="Invalid weather request format",
                )

            location = content.replace("get_weather:", "").strip()
            # Mock weather data - replace with actual API call
            weather = {"location": location, "temperature": 20, "condition": "sunny"}

            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.SUCCESS,
                outputs={"weather": weather},
            )
        except Exception as e:
            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.ERROR,
                error=str(e),
            )

    async def _tool_translate(self, request: MCPRequest) -> MCPResponse:
        """Handle translate tool requests.

        Args:
            request: The MCP request.

        Returns:
            The MCP response.
        """
        try:
            messages = request.inputs.get("messages", [])
            if not messages:
                return MCPResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    status=MCPStatusCode.ERROR,
                    error="No messages provided",
                )

            content = messages[-1].get("content", "")
            if not content.startswith("translate:"):
                return MCPResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    status=MCPStatusCode.ERROR,
                    error="Invalid translate request format",
                )

            # Parse "translate: text to target_lang"
            parts = content.replace("translate:", "").strip().split(" to ")
            if len(parts) != 2:
                return MCPResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    status=MCPStatusCode.ERROR,
                    error="Invalid translate format. Use: translate: text to target_lang",
                )

            text, target_lang = parts
            # Mock translation - replace with actual API call
            translated_text = f"[{target_lang}] {text}"

            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.SUCCESS,
                outputs={"translated_text": translated_text},
            )
        except Exception as e:
            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.ERROR,
                error=str(e),
            )

    async def _run_demo_client(self) -> dict[str, Any]:
        """Run demo client operations.

        Returns:
            Results from demo operations.
        """
        if not self.client:
            return {"status": "error", "message": "Client not initialized"}

        results = {}
        try:
            # Test chat
            chat_request = MCPRequest(
                request_id=str(uuid.uuid4()),
                model_id=self.llm_model,
                operation=MCPOperationType.CHAT,
                inputs={
                    "messages": [{"role": "user", "content": "Hello! How are you?"}]
                },
            )
            chat_response = await self.client.request(chat_request)
            results["chat"] = {
                "status": chat_response.status,
                "content": chat_response.outputs.get("content", ""),
            }

            # Test calculate tool
            calc_request = MCPRequest(
                request_id=str(uuid.uuid4()),
                model_id="calculator",
                operation=MCPOperationType.CHAT,
                inputs={"messages": [{"role": "user", "content": "calculate: 2 + 2"}]},
            )
            calc_response = await self.client.request(calc_request)
            results["calculate"] = {
                "status": calc_response.status,
                "result": calc_response.outputs.get("result", ""),
            }

            # Test weather tool
            weather_request = MCPRequest(
                request_id=str(uuid.uuid4()),
                model_id="weather",
                operation=MCPOperationType.CHAT,
                inputs={
                    "messages": [{"role": "user", "content": "get_weather: London"}]
                },
            )
            weather_response = await self.client.request(weather_request)
            results["weather"] = {
                "status": weather_response.status,
                "weather": weather_response.outputs.get("weather", {}),
            }

            # Test translate tool
            translate_request = MCPRequest(
                request_id=str(uuid.uuid4()),
                model_id="translator",
                operation=MCPOperationType.CHAT,
                inputs={
                    "messages": [
                        {"role": "user", "content": "translate: Hello world to es"}
                    ]
                },
            )
            translate_response = await self.client.request(translate_request)
            results["translate"] = {
                "status": translate_response.status,
                "translated_text": translate_response.outputs.get(
                    "translated_text", ""
                ),
            }

            return results
        except Exception as e:
            self.logger.error(f"Error running demo client operations: {e}")
            return {"status": "error", "message": str(e)}
