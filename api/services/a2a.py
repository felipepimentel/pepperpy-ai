"""
A2A Simulation Service

Service for simulating Agent-to-Agent communication using the PepperPy framework.
"""

import logging
import time
import uuid
from typing import Any

from api.services.base import BaseService
from pepperpy import PepperPy
from pepperpy.agent.base import Message

logger = logging.getLogger("api.services.a2a")


class A2ASimulationService(BaseService):
    """Service for Agent-to-Agent communication simulation."""

    def __init__(self) -> None:
        """Initialize the service."""
        super().__init__()
        self.active_simulations: dict[str, dict[str, Any]] = {}
        self.start_time = time.time()
        self.version = "0.1.0"
        self._pepperpy: PepperPy | None = None

    async def initialize(self) -> None:
        """Initialize service resources."""
        if self._initialized:
            return
        await self._initialize_resources()
        self._initialized = True

    async def cleanup(self) -> None:
        """Clean up service resources."""
        if not self._initialized:
            return
        await self._cleanup_resources()
        self._initialized = False

    async def _initialize_resources(self) -> None:
        """Initialize service resources."""
        try:
            # Create PepperPy instance with communication abstraction
            self._pepperpy = PepperPy().with_communication("a2a")
            self.logger.info("A2A simulation service initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize A2A service: {e}")
            raise

    async def _cleanup_resources(self) -> None:
        """Clean up service resources."""
        # Clean up active simulations
        self.active_simulations.clear()

        # Clean up PepperPy instance if it exists
        if self._pepperpy:
            # No need to call cleanup directly as it will be handled by context manager
            self._pepperpy = None

        self.logger.info("A2A simulation service cleaned up")

    async def reset(self) -> None:
        """Reset the service."""
        await self.cleanup()
        await self.initialize()
        self.logger.info("A2A simulation service reset complete")

    async def get_status(self) -> dict[str, Any]:
        """Get service status."""
        return {
            "status": "available" if self._initialized else "unavailable",
            "active_simulations": len(self.active_simulations),
            "uptime_seconds": time.time() - self.start_time,
            "version": self.version,
        }

    async def run_simulation(
        self,
        agent1_prompt: str,
        agent2_prompt: str,
        initial_message: str,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Run an Agent-to-Agent simulation.

        Args:
            agent1_prompt: The system prompt for the first agent
            agent2_prompt: The system prompt for the second agent
            initial_message: The message to start the conversation with
            config: Optional configuration parameters

        Returns:
            Simulation results including conversation history
        """
        if not self._initialized:
            await self.initialize()

        if not self._pepperpy:
            raise ValueError("PepperPy instance not initialized")

        # Generate a unique ID for this simulation
        simulation_id = str(uuid.uuid4())

        # Extract configuration parameters
        config_dict = config or {}
        max_turns = config_dict.get("max_turns", 5)
        timeout_seconds = config_dict.get("timeout_seconds", 60)
        enable_reflection = config_dict.get("enable_reflection", False)
        response_format = config_dict.get("response_format", None)

        # Create communication configuration
        comm_config = {
            "agent1": {
                "system_prompt": agent1_prompt,
                "enable_reflection": enable_reflection,
            },
            "agent2": {
                "system_prompt": agent2_prompt,
                "enable_reflection": enable_reflection,
            },
            "max_turns": max_turns,
            "response_format": response_format,
        }

        # Track this simulation
        self.active_simulations[simulation_id] = {
            "start_time": time.time(),
            "config": comm_config,
            "status": "running",
        }

        try:
            # Use the communication abstraction to run the simulation
            start_time = time.time()

            # Create the initial message
            messages = [Message(role="user", content=initial_message)]

            # Prepare input data for execute_communication
            input_data = {
                "task": "simulate_conversation",
                "messages": [msg.to_dict() for msg in messages],
                "config": comm_config,
                "timeout": timeout_seconds,
            }

            # Run the communication simulation using PepperPy's execute_communication method
            result = await self._pepperpy.execute_communication(input_data)

            # Calculate runtime
            runtime = time.time() - start_time

            # Format the response
            simulation_result = {
                "simulation_id": simulation_id,
                "conversation": result.get("conversation", []),
                "completed": result.get("completed", False),
                "turns_executed": result.get("turns", 0),
                "runtime_seconds": runtime,
                "terminated_reason": result.get("termination_reason"),
            }

            # Update simulation status
            self.active_simulations[simulation_id]["status"] = "completed"
            self.active_simulations[simulation_id]["result"] = simulation_result

            return simulation_result

        except TimeoutError:
            self.logger.warning(
                f"Simulation {simulation_id} timed out after {timeout_seconds}s"
            )

            # Update simulation status
            self.active_simulations[simulation_id]["status"] = "timeout"

            return {
                "simulation_id": simulation_id,
                "conversation": [],
                "completed": False,
                "turns_executed": 0,
                "runtime_seconds": time.time() - start_time,
                "terminated_reason": "timeout",
            }

        except Exception as e:
            self.logger.error(f"Error in A2A simulation {simulation_id}: {e}")

            # Update simulation status
            self.active_simulations[simulation_id]["status"] = "error"
            self.active_simulations[simulation_id]["error"] = str(e)

            raise

        finally:
            # Clean up for this simulation if needed
            pass


# Singleton instance
a2a_service = A2ASimulationService()
