import asyncio
import logging
from typing import Any

from pepperpy.core.errors import ProviderError, ValidationError
from pepperpy.core.plugin import PluginWorkflow

logger = logging.getLogger(__name__)

# Agent types and their roles in the mesh
AGENT_TYPES = {
    "analytical": "Process and analyze data, extract insights",
    "decision": "Make decisions based on analytical outputs",
    "conversion": "Transform formats or translate between domains",
    "execution": "Perform concrete actions based on decisions",
}

# Message types for inter-agent communication
MESSAGE_TYPES = [
    "task_request",
    "task_result",
    "query",
    "response",
    "notification",
    "error",
    "status_update",
]


class AgenticMeshWorkflow(PluginWorkflow):
    """
    A workflow that orchestrates multiple AI agents in a composable mesh architecture.

    The Agentic Mesh enables multiple specialized AI agents to collaborate on complex tasks,
    with automatic routing, shared knowledge, and dynamic reconfiguration capabilities.
    """

    async def initialize(self) -> None:
        """Initialize the Agentic Mesh workflow components."""
        logger.info("Initializing Agentic Mesh workflow")

        self.workflow_name = self.config.get("workflow_name")
        if not self.workflow_name:
            self.workflow_name = "agentic_mesh"

        # Initialize logging
        log_level = self.config.get("log_level", "INFO")
        numeric_level = getattr(logging, log_level, logging.INFO)
        logger.setLevel(numeric_level)

        # Load components
        try:
            self.components = self.config.get("components", {})

            # Get agent registry provider
            agent_registry_id = self.components.get("agent_registry")
            if not agent_registry_id:
                raise ProviderError("Agent registry provider not specified")
            self.agent_registry = await self.get_provider(agent_registry_id)

            # Get knowledge provider
            knowledge_provider_id = self.components.get("knowledge_provider")
            if not knowledge_provider_id:
                raise ProviderError("Knowledge provider not specified")
            self.knowledge_provider = await self.get_provider(knowledge_provider_id)

            # Get communication provider
            comm_provider_id = self.components.get("communication_provider")
            if not comm_provider_id:
                raise ProviderError("Communication provider not specified")
            self.communication_provider = await self.get_provider(comm_provider_id)

            # Initialize agent instances
            self.agents = {}
            agent_configs = self.config.get("agents", [])
            for agent_config in agent_configs:
                await self._register_agent(agent_config)

            # Set up default routing
            self.routing_rules = self.config.get("default_routing", {})

            # Initialize execution state
            self.active_tasks = {}
            self.message_history = []

            logger.info(
                f"Agentic Mesh '{self.workflow_name}' initialized with {len(self.agents)} agents"
            )

        except Exception as e:
            logger.error(f"Failed to initialize Agentic Mesh workflow: {e!s}")
            raise ProviderError(f"Initialization failed: {e!s}")

    async def _register_agent(self, agent_config: dict[str, Any]) -> None:
        """Register an agent with the mesh."""
        agent_id = agent_config.get("agent_id")
        if not agent_id:
            raise ValidationError("Agent configuration missing agent_id")

        agent_type = agent_config.get("agent_type")
        if not agent_type or agent_type not in AGENT_TYPES:
            raise ValidationError(f"Invalid agent type: {agent_type}")

        provider_type = agent_config.get("provider_type")
        if not provider_type:
            raise ValidationError("Agent configuration missing provider_type")

        parameters = agent_config.get("parameters", {})

        try:
            # Get the agent provider
            agent_provider = await self.get_provider(provider_type)

            # Register with the agent registry
            await self.agent_registry.register_agent(
                agent_id=agent_id,
                agent_type=agent_type,
                provider=agent_provider,
                parameters=parameters,
            )

            # Store in local registry
            self.agents[agent_id] = {
                "id": agent_id,
                "type": agent_type,
                "provider_type": provider_type,
                "provider": agent_provider,
                "parameters": parameters,
                "status": "idle",
            }

            logger.info(f"Registered agent '{agent_id}' of type '{agent_type}'")

        except Exception as e:
            logger.error(f"Failed to register agent '{agent_id}': {e!s}")
            raise ProviderError(f"Agent registration failed: {e!s}")

    async def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        """Execute actions in the Agentic Mesh based on input data."""
        action = data.get("action")
        if not action:
            return {"status": "error", "error": "No action specified"}

        try:
            if action == "run_task":
                return await self._run_task(data)
            elif action == "broadcast_message":
                return await self._broadcast_message(data)
            elif action == "direct_message":
                return await self._direct_message(data)
            elif action == "status":
                return await self._get_status(data)
            elif action == "add_agent":
                return await self._add_agent(data)
            elif action == "remove_agent":
                return await self._remove_agent(data)
            else:
                return {"status": "error", "error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Error executing action '{action}': {e!s}")
            return {"status": "error", "error": str(e)}

    async def _run_task(self, data: dict[str, Any]) -> dict[str, Any]:
        """Run a task in the mesh, routing to appropriate agents."""
        task = data.get("task")
        if not task:
            return {"status": "error", "error": "No task specified"}

        parameters = data.get("parameters", {})
        target_agent = data.get("target_agent")

        # If target agent specified, send task directly
        if target_agent:
            if target_agent not in self.agents:
                return {"status": "error", "error": f"Agent '{target_agent}' not found"}

            agent_data = self.agents[target_agent]
            task_id = f"task_{len(self.active_tasks) + 1}"

            # Create task in registry
            self.active_tasks[task_id] = {
                "id": task_id,
                "task": task,
                "agent": target_agent,
                "status": "pending",
                "result": None,
            }

            # Execute task on agent
            try:
                agent_provider = agent_data["provider"]
                result = await agent_provider.execute({
                    "task": task,
                    "parameters": parameters,
                })

                self.active_tasks[task_id]["status"] = "completed"
                self.active_tasks[task_id]["result"] = result

                return {"status": "success", "result": result, "task_id": task_id}

            except Exception as e:
                self.active_tasks[task_id]["status"] = "failed"
                self.active_tasks[task_id]["error"] = str(e)

                return {
                    "status": "error",
                    "error": f"Task execution failed: {e!s}",
                    "task_id": task_id,
                }

        # Otherwise, use routing rules to find appropriate agent
        task_type = parameters.get("task_type", "general")
        if task_type in self.routing_rules:
            target_agent = self.routing_rules[task_type]
            return await self._run_task({
                "task": task,
                "parameters": parameters,
                "target_agent": target_agent,
            })

        # If no routing rule, try to find an analytical agent
        analytical_agents = [
            a for a in self.agents.values() if a["type"] == "analytical"
        ]
        if not analytical_agents:
            return {
                "status": "error",
                "error": "No analytical agent available for task routing",
            }

        # Use first available analytical agent
        target_agent = analytical_agents[0]["id"]
        return await self._run_task({
            "task": task,
            "parameters": parameters,
            "target_agent": target_agent,
        })

    async def _broadcast_message(self, data: dict[str, Any]) -> dict[str, Any]:
        """Broadcast a message to all agents in the mesh."""
        message = data.get("message")
        if not message:
            return {"status": "error", "error": "No message specified"}

        # Validate message format
        if not isinstance(message, dict):
            return {"status": "error", "error": "Message must be an object"}

        if "type" not in message or message["type"] not in MESSAGE_TYPES:
            return {
                "status": "error",
                "error": f"Invalid message type. Must be one of: {', '.join(MESSAGE_TYPES)}",
            }

        if "content" not in message:
            return {"status": "error", "error": "Message must have content"}

        # Add metadata
        message["timestamp"] = asyncio.get_event_loop().time()
        message["broadcast"] = True
        message["sender"] = "workflow"

        # Record in history
        self.message_history.append(message)

        # Broadcast via communication provider
        try:
            result = await self.communication_provider.broadcast(message)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": f"Broadcast failed: {e!s}"}

    async def _direct_message(self, data: dict[str, Any]) -> dict[str, Any]:
        """Send a direct message to a specific agent."""
        target_agent = data.get("target_agent")
        if not target_agent:
            return {"status": "error", "error": "No target agent specified"}

        if target_agent not in self.agents:
            return {"status": "error", "error": f"Agent '{target_agent}' not found"}

        message = data.get("message")
        if not message:
            return {"status": "error", "error": "No message specified"}

        # Validate message format
        if not isinstance(message, dict):
            return {"status": "error", "error": "Message must be an object"}

        if "type" not in message or message["type"] not in MESSAGE_TYPES:
            return {
                "status": "error",
                "error": f"Invalid message type. Must be one of: {', '.join(MESSAGE_TYPES)}",
            }

        if "content" not in message:
            return {"status": "error", "error": "Message must have content"}

        # Add metadata
        message["timestamp"] = asyncio.get_event_loop().time()
        message["broadcast"] = False
        message["sender"] = "workflow"
        message["recipient"] = target_agent

        # Record in history
        self.message_history.append(message)

        # Send via communication provider
        try:
            result = await self.communication_provider.send_message(
                recipient=target_agent, message=message
            )
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": f"Direct message failed: {e!s}"}

    async def _get_status(self, data: dict[str, Any]) -> dict[str, Any]:
        """Get the current status of the Agentic Mesh."""
        detailed = data.get("detailed", False)

        # Basic status
        status = {
            "workflow_name": self.workflow_name,
            "agent_count": len(self.agents),
            "active_tasks": len([
                t for t in self.active_tasks.values() if t["status"] == "pending"
            ]),
            "completed_tasks": len([
                t for t in self.active_tasks.values() if t["status"] == "completed"
            ]),
            "failed_tasks": len([
                t for t in self.active_tasks.values() if t["status"] == "failed"
            ]),
            "message_count": len(self.message_history),
        }

        # Detailed status if requested
        if detailed:
            status["agents"] = list(self.agents.values())
            status["tasks"] = list(self.active_tasks.values())
            status["recent_messages"] = (
                self.message_history[-10:] if self.message_history else []
            )

        return {"status": "success", "result": status}

    async def _add_agent(self, data: dict[str, Any]) -> dict[str, Any]:
        """Add a new agent to the mesh."""
        agent_config = data.get("parameters")
        if not agent_config:
            return {"status": "error", "error": "No agent configuration provided"}

        try:
            await self._register_agent(agent_config)
            return {
                "status": "success",
                "result": {
                    "agent_id": agent_config.get("agent_id"),
                    "message": "Agent successfully added to mesh",
                },
            }
        except Exception as e:
            return {"status": "error", "error": f"Failed to add agent: {e!s}"}

    async def _remove_agent(self, data: dict[str, Any]) -> dict[str, Any]:
        """Remove an agent from the mesh."""
        agent_id = data.get("target_agent")
        if not agent_id:
            return {"status": "error", "error": "No agent ID specified"}

        if agent_id not in self.agents:
            return {"status": "error", "error": f"Agent '{agent_id}' not found"}

        try:
            # Remove from agent registry
            await self.agent_registry.unregister_agent(agent_id)

            # Remove from local registry
            del self.agents[agent_id]

            logger.info(f"Removed agent '{agent_id}' from mesh")

            return {
                "status": "success",
                "result": {
                    "agent_id": agent_id,
                    "message": "Agent successfully removed from mesh",
                },
            }
        except Exception as e:
            return {"status": "error", "error": f"Failed to remove agent: {e!s}"}

    async def cleanup(self) -> None:
        """Clean up resources used by the Agentic Mesh workflow."""
        logger.info(f"Cleaning up Agentic Mesh workflow '{self.workflow_name}'")

        try:
            # Close all connections
            for agent_id, agent_data in self.agents.items():
                try:
                    # Tell agent registry to unregister the agent
                    await self.agent_registry.unregister_agent(agent_id)
                except Exception as e:
                    logger.warning(f"Error unregistering agent '{agent_id}': {e!s}")

            self.agents = {}
            self.active_tasks = {}
            self.message_history = []

            logger.info(f"Agentic Mesh workflow '{self.workflow_name}' cleaned up")

        except Exception as e:
            logger.error(f"Error during cleanup: {e!s}")
            raise ProviderError(f"Cleanup failed: {e!s}")
