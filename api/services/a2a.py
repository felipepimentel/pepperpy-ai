"""
A2A Simulation Service

This module implements a service for running Agent-to-Agent simulations
using the PepperPy A2A protocol communication adapter.
"""

import logging
import time
import uuid
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from pepperpy import Agent, AgentConfig
from pepperpy.communication import (
    CommunicationProvider,
    create_provider as create_communication_provider
)
from pepperpy.utils.version import get_version

# Configure service logger
logger = logging.getLogger("api.services.a2a")

class A2ASimulationService:
    """
    Service for running Agent-to-Agent simulations using the PepperPy framework.
    Maintains simulation state and provides methods for running and monitoring simulations.
    """
    
    def __init__(self):
        """Initialize the A2A simulation service."""
        self.active_simulations: Dict[str, Dict[str, Any]] = {}
        self.start_time = time.time()
        self.initialized = False
        self.version = get_version()
        self._provider: Optional[CommunicationProvider] = None
        logger.info("A2A Simulation Service created")
    
    async def initialize(self):
        """Initialize simulation service resources."""
        if self.initialized:
            logger.warning("A2A service already initialized")
            return
        
        try:
            # Initialize any required resources
            # For example, we might pre-initialize the A2A adapter
            self._provider = await create_communication_provider("a2a")
            
            self.initialized = True
            logger.info("A2A simulation service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize A2A simulation service: {str(e)}")
            raise
    
    async def run_simulation(
        self,
        agent1_prompt: str,
        agent2_prompt: str,
        initial_message: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run an A2A simulation between two agents with the given prompts.
        
        Args:
            agent1_prompt: System prompt for the first agent
            agent2_prompt: System prompt for the second agent
            initial_message: Message to start the conversation
            config: Optional configuration parameters
            
        Returns:
            A dictionary containing simulation results
        """
        if not self.initialized:
            await self.initialize()
        
        # Generate a unique ID for this simulation
        simulation_id = str(uuid.uuid4())
        
        # Set default config values if not provided
        if config is None:
            config = {}
        
        max_turns = config.get("max_turns", 5)
        timeout_seconds = config.get("timeout_seconds", 60)
        enable_reflection = config.get("enable_reflection", False)
        response_format = config.get("response_format", None)
        
        # Track simulation start time
        start_time = time.time()
        
        try:
            # Configure agents
            agent1_config = AgentConfig(
                system_prompt=agent1_prompt,
                enable_reflection=enable_reflection
            )
            
            agent2_config = AgentConfig(
                system_prompt=agent2_prompt,
                enable_reflection=enable_reflection
            )
            
            # Create agents
            agent1 = Agent(config=agent1_config)
            agent2 = Agent(config=agent2_config)
            
            # Initialize the simulation environment
            await self._provider.initialize({
                "agent1": agent1,
                "agent2": agent2,
                "simulation_mode": True
            })
            
            # Setup tracking for the conversation
            conversation = []
            terminated_reason = None
            
            # Add the initial message to the conversation
            conversation.append({
                "role": "system",
                "content": initial_message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Execute the turns
            current_agent = "agent1"  # Start with agent 1
            turns_executed = 0
            
            # Register this as an active simulation
            self.active_simulations[simulation_id] = {
                "start_time": start_time,
                "agent1_prompt": agent1_prompt,
                "agent2_prompt": agent2_prompt,
                "config": config,
                "adapter": self._provider,
                "status": "running"
            }
            
            # Execute simulation turns
            while turns_executed < max_turns:
                # Check if we've exceeded the timeout
                if time.time() - start_time > timeout_seconds:
                    terminated_reason = "timeout"
                    break
                
                try:
                    # Get the sending and receiving agents
                    sender = "agent1" if current_agent == "agent1" else "agent2"
                    receiver = "agent2" if current_agent == "agent1" else "agent1"
                    
                    # Get the last message to respond to
                    last_message = initial_message if turns_executed == 0 else conversation[-1]["content"]
                    
                    # Send message and get response
                    message_data = {
                        "content": last_message,
                        "format": response_format
                    }
                    
                    # Have the current agent respond
                    response = await self._provider.send_message(
                        sender=sender,
                        receiver=receiver,
                        message=message_data
                    )
                    
                    # Record the message in the conversation
                    conversation.append({
                        "role": current_agent,
                        "content": response["content"],
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Switch agents
                    current_agent = "agent2" if current_agent == "agent1" else "agent1"
                    turns_executed += 1
                    
                except Exception as e:
                    logger.error(f"Error in simulation turn: {str(e)}")
                    terminated_reason = f"error: {str(e)}"
                    break
            
            # If we completed all turns without error
            if terminated_reason is None:
                terminated_reason = "completed"
            
            # Calculate runtime
            runtime_seconds = time.time() - start_time
            
            # Prepare result
            result = {
                "simulation_id": simulation_id,
                "conversation": conversation,
                "completed": terminated_reason == "completed",
                "turns_executed": turns_executed,
                "runtime_seconds": runtime_seconds,
                "terminated_reason": terminated_reason
            }
            
            # Update simulation status
            self.active_simulations[simulation_id]["status"] = "completed"
            
            # Clean up resources (in background)
            asyncio.create_task(self._cleanup_simulation(simulation_id))
            
            return result
            
        except Exception as e:
            logger.error(f"Simulation failed: {str(e)}")
            
            # Update simulation status
            if simulation_id in self.active_simulations:
                self.active_simulations[simulation_id]["status"] = "failed"
                asyncio.create_task(self._cleanup_simulation(simulation_id))
            
            raise
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the A2A simulation service.
        
        Returns:
            A dictionary containing service metrics and status
        """
        return {
            "status": "running" if self.initialized else "initializing",
            "active_simulations": len(self.active_simulations),
            "uptime_seconds": time.time() - self.start_time,
            "version": self.version
        }
    
    async def reset(self):
        """
        Reset the service, cleaning up all simulations and reinitializing resources.
        """
        logger.info("Resetting A2A simulation service")
        
        # Clean up all active simulations
        for simulation_id in list(self.active_simulations.keys()):
            await self._cleanup_simulation(simulation_id)
        
        # Reset service state
        self.initialized = False
        
        # Reinitialize
        await self.initialize()
        
        logger.info("A2A simulation service reset completed")
    
    async def cleanup(self):
        """
        Clean up resources when the service is shutting down.
        """
        logger.info("Cleaning up A2A simulation service")
        
        # Clean up all active simulations
        for simulation_id in list(self.active_simulations.keys()):
            await self._cleanup_simulation(simulation_id)
        
        self.initialized = False
        logger.info("A2A simulation service cleanup completed")
    
    async def _cleanup_simulation(self, simulation_id: str):
        """
        Clean up resources for a specific simulation.
        
        Args:
            simulation_id: The ID of the simulation to clean up
        """
        if simulation_id not in self.active_simulations:
            logger.warning(f"Cannot clean up non-existent simulation: {simulation_id}")
            return
        
        try:
            # Get the simulation data
            simulation = self.active_simulations[simulation_id]
            
            # Clean up the adapter
            if "adapter" in simulation:
                await simulation["adapter"].cleanup()
            
            # Remove from active simulations
            del self.active_simulations[simulation_id]
            
            logger.info(f"Simulation {simulation_id} cleaned up successfully")
        except Exception as e:
            logger.error(f"Error cleaning up simulation {simulation_id}: {str(e)}")


# Create a singleton instance
a2a_service = A2ASimulationService() 