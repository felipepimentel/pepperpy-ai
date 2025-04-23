"""
MCP Demo Workflow Provider.

This module provides a workflow for demonstrating Model Context Protocol (MCP)
capabilities with PepperPy. It sets up MCP server and client communication
and demonstrates various interaction patterns.
"""

import asyncio
import json
import uuid
from enum import Enum
from typing import Any, dict, list, Optional, cast

from pepperpy.plugin import ProviderPlugin
from pepperpy.workflow import WorkflowProvider
from pepperpy.core.logging import get_logger
from pepperpy.communication import (
    CommunicationProtocol,
    create_provider,
    Message,
    TextPart,
)
from pepperpy.llm import create_provider as create_llm_provider
from pepperpy.workflow.base import WorkflowError

logger = logger.getLogger(__name__)

logger = get_logger(__name__)


class DemoMode(class DemoMode(str, Enum):
    """Demo modes for the MCP workflow."""):
    """
    Workflow demomode provider.
    
    This provider implements demomode functionality for the PepperPy workflow framework.
    """
    
    BASIC = "basic"
    SERVER_CLIENT = "server_client"
    TOOLS = "tools"
    AGENT_ORCHESTRATION = "agent_orchestration"


class MCPDemoWorkflow(WorkflowProvider, ProviderPlugin):
    """MCP demo workflow provider.
    
    This workflow demonstrates MCP capabilities by:
    1. Starting an MCP server
    2. Registering tools and handlers
    3. Executing client requests
    4. Demonstrating agent orchestration
    """
    
    def __init__(self) -> None:

    
    """Initialize the MCP demo workflow.

    
    """
        self._initialized = False
        self._config: dict[str, Any] = {}
        self._server_provider: Optional[Any] = None
        self._client_provider: Optional[Any] = None
        self._llm_provider: Optional[Any] = None
        self._server_task: Optional[asyncio.Task] = None
    
    @property
    def initialized(self) -> bool:

    """Return whether the provider is initialized.


    Returns:

        Return description

    """
        return self._initialized
    
    async def initialize(self) -> None:
 """Initialize the provider.

        This method is called automatically when the provider is first used.
        It sets up resources needed by the provider.
 """
        if self._initialized:
            return
        
        try:
            # Extract configuration
            provider_type = self._config.get("provider_type", "default")
            host = self._config.get("host", "localhost")
            port = self._config.get("port", 8080)
            
            # Get the MCP server provider using correct protocol abstraction
            self._server_provider = await create_provider(
                protocol=CommunicationProtocol.MCP,
                provider_type=f"server_{provider_type}",
                host=host,
                port=port
            )
            
            # Get the MCP client provider using correct protocol abstraction
            self._client_provider = await create_provider(
                protocol=CommunicationProtocol.MCP,
                provider_type=provider_type,
                host=host,
                port=port
            )
            
            # Initialize the LLM provider if needed
            llm_config = self._config.get("llm_config", {})
            if llm_config:
                provider_type = llm_config.get("provider", "openai")
                model = llm_config.get("model", "gpt-4")
                self._llm_provider = create_llm_provider(provider_type=provider_type)
                await self._llm_provider.initialize()
            
            # Register tools for the MCP server
            await self._register_default_tools()
            
            # Start the server in the background
            self._server_task = asyncio.create_task(self._run_server())
            
            self._initialized = True
            logger.info("MCP Demo workflow initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MCP Demo workflow: {e}")
            raise
    
    async def cleanup(self) -> None:
 """Clean up provider resources.

        This method is called automatically when the context manager exits.
        It releases any resources acquired during initialization.
 """
        if not self._initialized:
            return
        
        try:
            # Stop the server task
            if self._server_task and not self._server_task.done():
                self._server_task.cancel()
                try:
                    await self._server_task
                except asyncio.CancelledError:
                    pass
            
            # Clean up the MCP providers
            if self._server_provider and hasattr(self._server_provider, "cleanup"):
                await self._server_provider.cleanup()
            
            if self._client_provider and hasattr(self._client_provider, "cleanup"):
                await self._client_provider.cleanup()
            
            # Clean up the LLM provider
            if self._llm_provider:
                await self._llm_provider.cleanup()
            
            self._initialized = False
            logger.info("MCP Demo workflow cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up MCP Demo workflow: {e}")
            raise
    
    async def get_config(self) -> dict[str, Any]:
 """Return the current configuration.

 Returns:
     Return description
 """
        return self._config
    
    def has_config(self) -> bool:

    
    """Return whether the provider has a configuration.


    
    Returns:

    
        Return description

    
    """
        return bool(self._config)
    
    async def update_config(self, config: dict[str, Any]) -> None:
 """Update the configuration.

 Args:
     config: Parameter description
     Any]: Parameter description
 """
        self._config = config
    
    async def __aenter__(self) -> "MCPDemoWorkflow":
 """Enter context manager.

 Returns:
     Return description
 """
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
 """Exit context manager.

 Args:
     exc_type: Parameter description
     exc_val: Parameter description
     exc_tb: Parameter description
 """
        await self.cleanup()
    
    async def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        """Execute the MCP demo workflow.
        
        Args:
            data: Input data containing the demo parameters:
                - mode: Demo mode to run (basic, server_client, tools, agent_orchestration)
                - prompt: Prompt to use for the demo
        
        Returns:
            Results of the demo execution
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._client_provider:
            raise RuntimeError("MCP provider not initialized")
        
        try:
            # Extract input parameters
            mode = data.get("mode", self._config.get("demo_mode", DemoMode.BASIC))
            prompt = data.get("prompt", "Hello, world!")
            
            # Select the appropriate demo mode
            if mode == DemoMode.BASIC:
                return await self._run_basic_demo(prompt)
            elif mode == DemoMode.SERVER_CLIENT:
                return await self._run_server_client_demo(prompt)
            elif mode == DemoMode.TOOLS:
                return await self._run_tools_demo(data)
            elif mode == DemoMode.AGENT_ORCHESTRATION:
                return await self._run_agent_orchestration_demo(data)
            else:
                raise WorkflowError(f"Unknown demo mode: {mode)"
                }
        except Exception as e:
            logger.error(f"Error executing MCP Demo workflow: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _register_default_tools(self) -> None:
 """Register default tools for the MCP server.
 """
        if not self._server_provider:
            return
        
        # Register the chat handler
        await self._server_provider.register_operation(
            "chat",
            self._handle_chat
        )
        
        # Register the calculate tool
        await self._server_provider.register_operation(
            "calculate",
            self._handle_calculate
        )
        
        # Register the weather tool
        await self._server_provider.register_operation(
            "weather",
            self._handle_weather
        )
        
        # Register the translate tool
        await self._server_provider.register_operation(
            "translate",
            self._handle_translate
        )
        
        logger.info("Registered default MCP tools")
    
    async def _run_server(self) -> None:
 """Run the MCP server in the background.
 """
        if not self._server_provider:
            return
        
        try:
            # Start the server
            await self._server_provider.start_server()
        except Exception as e:
            logger.error(f"Error running MCP server: {e}")
            raise
    
    async def _handle_chat(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle chat requests.
        
        Args:
            request: Chat request data
        
        Returns:
            Chat response
        """
        if not self._llm_provider:
            raise WorkflowError("LLM provider not initialized"
            )
        
        try:
            # Extract the message from the request
            prompt = request.get("prompt", "")
            if not prompt:
                raise WorkflowError("No prompt provided"
                )
            
            # Send to the LLM
            messages = [
                Message(
                    role=MessageRole.USER,
                    content=prompt
                )
            ]
            
            response = await self._llm_provider.generate(messages=messages)
            
            return {
                "status": "success",
                "response": response,
                "operation": "chat"
            }
        except Exception as e:
            logger.error(f"Error handling chat request: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _handle_calculate(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle calculate requests.
        
        Args:
            request: Calculate request data
        
        Returns:
            Calculation result
        """
        try:
            # Extract the expression from the request
            expression = request.get("expression", "")
            if not expression:
                raise WorkflowError("No expression provided"
                )
            
            # Evaluate the expression (safely)
            # This is just for demo purposes - would use a safer method in production
            result = eval(expression)
            
            return {
                "status": "success",
                "result": result,
                "operation": "calculate"
            }
        except Exception as e:
            logger.error(f"Error handling calculate request: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _handle_weather(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle weather requests.
        
        Args:
            request: Weather request data
        
        Returns:
            Weather information
        """
        try:
            # Extract the location from the request
            location = request.get("location", "")
            if not location:
                raise WorkflowError("No location provided"
                )
            
            # Simulate weather data (would use a real API in production)
            weather_data = {
                "location": location,
                "temperature": 72,
                "condition": "sunny",
                "humidity": 45,
                "wind_speed": 10
            }
            
            return {
                "status": "success",
                "weather": weather_data,
                "operation": "weather"
            }
        except Exception as e:
            logger.error(f"Error handling weather request: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _handle_translate(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle translate requests.
        
        Args:
            request: Translate request data
        
        Returns:
            Translation result
        """
        if not self._llm_provider:
            raise WorkflowError("LLM provider not initialized"
            )
        
        try:
            # Extract the text and target language from the request
            text = request.get("text", "")
            target_language = request.get("target_language", "")
            
            if not text:
                raise WorkflowError("No text provided"
                )
            
            if not target_language:
                raise WorkflowError("No target language provided"
                )
            
            # Use the LLM for translation
            messages = [
                Message(
                    role=MessageRole.SYSTEM,
                    content=f"You are a translator. Translate the text to {target_language}."
                ),
                Message(
                    role=MessageRole.USER,
                    content=text
                )
            ]
            
            translation = await self._llm_provider.generate(messages=messages)
            
            return {
                "status": "success",
                "original": text,
                "translation": translation,
                "target_language": target_language,
                "operation": "translate"
            }
        except Exception as e:
            logger.error(f"Error handling translate request: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _run_basic_demo(self, prompt: str) -> dict[str, Any]:
        """Run a basic MCP demo.
        
        Args:
            prompt: Prompt to send
        
        Returns:
            Demo results
        """
        if not self._client_provider:
            raise RuntimeError("MCP client provider not initialized")
        
        # Send a chat request
        from plugins.communication.mcp.adapter import MCPRequest, MCPOperationType
        
        request = MCPRequest(
            request_id=str(uuid.uuid4()),
            operation=MCPOperationType.CHAT,
            data={"prompt": prompt}
        )
        
        response = await self._client_provider.send_request(request)
        
        return {
            "prompt": prompt,
            "response": response.data.get("response", "No response"),
            "status": response.status,
            "demo_mode": DemoMode.BASIC
        }
    
    async def _run_server_client_demo(self, prompt: str) -> dict[str, Any]:
        """Run a server-client MCP demo with multiple requests.
        
        Args:
            prompt: Initial prompt
        
        Returns:
            Demo results
        """
        if not self._client_provider:
            raise RuntimeError("MCP client provider not initialized")
        
        # Import necessary types
        from plugins.communication.mcp.adapter import MCPRequest, MCPOperationType
        
        # Send a chat request
        chat_request = MCPRequest(
            request_id=str(uuid.uuid4()),
            operation=MCPOperationType.CHAT,
            data={"prompt": prompt}
        )
        
        chat_response = await self._client_provider.send_request(chat_request)
        
        # Send a calculate request
        calc_request = MCPRequest(
            request_id=str(uuid.uuid4()),
            operation=MCPOperationType.CUSTOM,
            operation_name="calculate",
            data={"expression": "2 + 2"}
        )
        
        calc_response = await self._client_provider.send_request(calc_request)
        
        # Send a weather request
        weather_request = MCPRequest(
            request_id=str(uuid.uuid4()),
            operation=MCPOperationType.CUSTOM,
            operation_name="weather",
            data={"location": "New York"}
        )
        
        weather_response = await self._client_provider.send_request(weather_request)
        
        return {
            "interactions": [
                {
                    "type": "chat",
                    "prompt": prompt,
                    "response": chat_response.data.get("response", "No response"),
                    "status": chat_response.status
                },
                {
                    "type": "calculate",
                    "expression": "2 + 2",
                    "result": calc_response.data.get("result", "No result"),
                    "status": calc_response.status
                },
                {
                    "type": "weather",
                    "location": "New York",
                    "weather": weather_response.data.get("weather", "No weather data"),
                    "status": weather_response.status
                }
            ],
            "status": "success",
            "demo_mode": DemoMode.SERVER_CLIENT
        }
    
    async def _run_tools_demo(self, data: dict[str, Any]) -> dict[str, Any]:
        """Run a tools MCP demo.
        
        Args:
            data: Input data containing tool requests
        
        Returns:
            Demo results
        """
        if not self._client_provider:
            raise RuntimeError("MCP client provider not initialized")
        
        # Import necessary types
        from plugins.communication.mcp.adapter import MCPRequest, MCPOperationType
        
        # Process tool requests
        results = []
        
        # Chat tool
        if "chat" in data:
            chat_request = MCPRequest(
                request_id=str(uuid.uuid4()),
                operation=MCPOperationType.CHAT,
                data={"prompt": data["chat"]}
            )
            
            chat_response = await self._client_provider.send_request(chat_request)
            
            results.append({
                "tool": "chat",
                "prompt": data["chat"],
                "response": chat_response.data.get("response", "No response"),
                "status": chat_response.status
            })
        
        # Calculate tool
        if "calculate" in data:
            calc_request = MCPRequest(
                request_id=str(uuid.uuid4()),
                operation=MCPOperationType.CUSTOM,
                operation_name="calculate",
                data={"expression": data["calculate"]}
            )
            
            calc_response = await self._client_provider.send_request(calc_request)
            
            results.append({
                "tool": "calculate",
                "expression": data["calculate"],
                "result": calc_response.data.get("result", "No result"),
                "status": calc_response.status
            })
        
        # Weather tool
        if "weather" in data:
            weather_request = MCPRequest(
                request_id=str(uuid.uuid4()),
                operation=MCPOperationType.CUSTOM,
                operation_name="weather",
                data={"location": data["weather"]}
            )
            
            weather_response = await self._client_provider.send_request(weather_request)
            
            results.append({
                "tool": "weather",
                "location": data["weather"],
                "weather": weather_response.data.get("weather", "No weather data"),
                "status": weather_response.status
            })
        
        # Translate tool
        if "translate" in data and "target_language" in data:
            translate_request = MCPRequest(
                request_id=str(uuid.uuid4()),
                operation=MCPOperationType.CUSTOM,
                operation_name="translate",
                data={
                    "text": data["translate"],
                    "target_language": data["target_language"]
                }
            )
            
            translate_response = await self._client_provider.send_request(translate_request)
            
            results.append({
                "tool": "translate",
                "text": data["translate"],
                "target_language": data["target_language"],
                "translation": translate_response.data.get("translation", "No translation"),
                "status": translate_response.status
            })
        
        return {
            "results": results,
            "status": "success",
            "demo_mode": DemoMode.TOOLS
        }
    
    async def _run_agent_orchestration_demo(self, data: dict[str, Any]) -> dict[str, Any]:
        """Run an agent orchestration MCP demo.
        
        Args:
            data: Input data containing the task
        
        Returns:
            Demo results
        """
        if not self._client_provider or not self._llm_provider:
            raise RuntimeError("MCP client provider or LLM provider not initialized")
        
        # Import necessary types
        from plugins.communication.mcp.adapter import MCPRequest, MCPOperationType
        
        # Extract the task from the input data
        task = data.get("task", "Create a plan for a weekend trip to New York")
        
        # Define agent roles
        planner_role = "You are the Planner Agent. Your job is to analyze tasks and break them down into steps."
        executor_role = "You are the Executor Agent. Your job is to perform the steps provided by the Planner."
        critic_role = "You are the Critic Agent. Your job is to evaluate the output and suggest improvements."
        
        # Step 1: Planner analyzes the task
        planner_prompt = f"Task: {task}\n\nBreak this task down into 3-5 clear steps."
        
        planner_request = MCPRequest(
            request_id=str(uuid.uuid4()),
            operation=MCPOperationType.CHAT,
            data={"prompt": planner_prompt, "system_message": planner_role}
        )
        
        planner_response = await self._client_provider.send_request(planner_request)
        plan = planner_response.data.get("response", "No plan generated")
        
        # Step 2: Executor follows the plan
        executor_prompt = f"Task: {task}\n\nPlan from Planner:\n{plan}\n\nExecute this plan step by step."
        
        executor_request = MCPRequest(
            request_id=str(uuid.uuid4()),
            operation=MCPOperationType.CHAT,
            data={"prompt": executor_prompt, "system_message": executor_role}
        )
        
        executor_response = await self._client_provider.send_request(executor_request)
        execution_result = executor_response.data.get("response", "No execution result")
        
        # Step 3: Critic reviews the result
        critic_prompt = f"Task: {task}\n\nExecution result:\n{execution_result}\n\nEvaluate this result and suggest improvements."
        
        critic_request = MCPRequest(
            request_id=str(uuid.uuid4()),
            operation=MCPOperationType.CHAT,
            data={"prompt": critic_prompt, "system_message": critic_role}
        )
        
        critic_response = await self._client_provider.send_request(critic_request)
        critique = critic_response.data.get("response", "No critique generated")
        
        # Step 4: Final improvement based on critique
        final_prompt = f"Task: {task}\n\nExecution result:\n{execution_result}\n\nCritique:\n{critique}\n\nCreate an improved final version incorporating the critique."
        
        final_request = MCPRequest(
            request_id=str(uuid.uuid4()),
            operation=MCPOperationType.CHAT,
            data={"prompt": final_prompt}
        )
        
        final_response = await self._client_provider.send_request(final_request)
        final_result = final_response.data.get("response", "No final result")
        
        return {
            "task": task,
            "workflow": [
                {"agent": "Planner", "role": "Task Analysis", "output": plan},
                {"agent": "Executor", "role": "Execution", "output": execution_result},
                {"agent": "Critic", "role": "Evaluation", "output": critique},
                {"agent": "System", "role": "Final Improvement", "output": final_result}
            ],
            "final_result": final_result,
            "status": "success",
            "demo_mode": DemoMode.AGENT_ORCHESTRATION
        } 