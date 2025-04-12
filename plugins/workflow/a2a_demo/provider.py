"""
A2A Demo Workflow provider module that demonstrates Agent-to-Agent communication
capabilities with PepperPy. This module sets up multiple agents and demonstrates
various interaction patterns.
"""

import json
import enum
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple, TypedDict, cast

from pepperpy.a2a.simulation import SimulationEnvironment, SimulatedAgent
from pepperpy.a2a.simulation import echo_response_handler, delayed_response_handler, stateful_response_handler
from pepperpy.a2a.types import AgentCard, AgentTask, MessageContent
from pepperpy.core.plugin import ProviderPlugin
from pepperpy.core.logging import get_logger
from pepperpy.workflow import BaseWorkflowProvider


class DemoMode(enum.Enum):
    """Demo mode options for the A2A workflow."""
    BASIC = "basic"
    MULTI_AGENT = "multi_agent"
    CONVERSATION_CHAIN = "conversation_chain"
    STATEFUL = "stateful"


class A2ADemoWorkflow(BaseWorkflowProvider, ProviderPlugin):
    """
    A workflow provider that demonstrates A2A (Agent-to-Agent) communication capabilities.
    
    This workflow sets up a simulation environment with multiple agents and demonstrates
    various interaction patterns including basic message passing, multi-agent conversations,
    conversation chains, and stateful interactions.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the A2A Demo Workflow provider.

        Args:
            config: Configuration for the workflow.
        """
        self.config = config
        self._logger = get_logger(__name__)
        self._sim_env = None
        self._agents = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the workflow resources."""
        if self._initialized:
            return

        try:
            # Create the simulation environment
            self._sim_env = SimulationEnvironment()
            
            # Register default agents
            self._agents["assistant"] = await self._sim_env.register_agent(
                SimulatedAgent(
                    AgentCard(
                        agent_id="assistant",
                        name="Assistant Agent",
                        description="A helpful AI assistant",
                        capabilities=["text-generation"]
                    )
                ),
                echo_response_handler
            )
            
            self._agents["knowledge"] = await self._sim_env.register_agent(
                SimulatedAgent(
                    AgentCard(
                        agent_id="knowledge",
                        name="Knowledge Agent",
                        description="An agent specialized in retrieving knowledge",
                        capabilities=["knowledge-retrieval"]
                    )
                ),
                delayed_response_handler
            )
            
            self._agents["memory"] = await self._sim_env.register_agent(
                SimulatedAgent(
                    AgentCard(
                        agent_id="memory",
                        name="Memory Agent",
                        description="An agent that maintains conversation context",
                        capabilities=["context-management"]
                    )
                ),
                stateful_response_handler
            )
            
            self._initialized = True
            self._logger.info("A2A Demo Workflow initialized successfully")
        except Exception as e:
            self._logger.error(f"Failed to initialize A2A Demo Workflow: {e}")
            raise

    async def cleanup(self) -> None:
        """Clean up any resources used by the provider."""
        if self._sim_env:
            await self._sim_env.cleanup()
        self._initialized = False
        self._agents = {}
        self._logger.info("A2A Demo Workflow resources cleaned up")

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the A2A demo workflow.

        Args:
            input_data: Input data for the workflow.

        Returns:
            A dictionary containing the results of the demo.
        """
        if not self._initialized:
            await self.initialize()

        # Get demo mode from config, defaulting to basic
        demo_mode_str = self.config.get("demo_mode", "basic")
        try:
            demo_mode = DemoMode(demo_mode_str)
        except ValueError:
            self._logger.warning(f"Invalid demo mode: {demo_mode_str}, using BASIC")
            demo_mode = DemoMode.BASIC

        # Get user message from input data, or use default
        user_message = input_data.get("message", "Hello, can you help me?")
        
        # Run the appropriate demo based on mode
        results = {}
        if demo_mode == DemoMode.BASIC:
            results = await self._run_basic_demo(user_message)
        elif demo_mode == DemoMode.MULTI_AGENT:
            results = await self._run_multi_agent_demo(user_message)
        elif demo_mode == DemoMode.CONVERSATION_CHAIN:
            results = await self._run_conversation_chain_demo(user_message)
        elif demo_mode == DemoMode.STATEFUL:
            results = await self._run_stateful_demo(user_message)
        
        return {
            "demo_mode": demo_mode_str,
            "user_message": user_message,
            "results": results
        }

    async def _run_basic_demo(self, message: str) -> Dict[str, Any]:
        """Run a basic demo with a single agent.

        Args:
            message: The message to send to the agent.

        Returns:
            Results of the basic demo.
        """
        self._logger.info("Running basic A2A demo")
        
        agent = self._agents["assistant"]
        
        # Create a simple task
        task = AgentTask(
            task_id="simple_task",
            instruction="Respond to the user message",
            input_data={"message": message}
        )
        
        # Send message to the agent
        response = await self._sim_env.send_message(
            "user",
            agent.agent_id,
            MessageContent(text=message),
            task
        )
        
        return {
            "agent": agent.agent_card.to_dict(),
            "task": task.to_dict(),
            "response": response.to_dict() if response else None
        }

    async def _run_multi_agent_demo(self, message: str) -> Dict[str, Any]:
        """Run a demo with multiple agents.

        Args:
            message: The message to send to the agents.

        Returns:
            Results of the multi-agent demo.
        """
        self._logger.info("Running multi-agent A2A demo")
        
        results = []
        
        # Send the same message to all agents
        for agent_id, agent in self._agents.items():
            task = AgentTask(
                task_id=f"{agent_id}_task",
                instruction=f"Process the following message as {agent_id}",
                input_data={"message": message}
            )
            
            response = await self._sim_env.send_message(
                "user",
                agent.agent_id,
                MessageContent(text=message),
                task
            )
            
            results.append({
                "agent": agent.agent_card.to_dict(),
                "task": task.to_dict(),
                "response": response.to_dict() if response else None
            })
        
        return {"interactions": results}

    async def _run_conversation_chain_demo(self, message: str) -> Dict[str, Any]:
        """Run a demo with a chain of conversations between agents.

        Args:
            message: The initial message to start the chain.

        Returns:
            Results of the conversation chain demo.
        """
        self._logger.info("Running conversation chain A2A demo")
        
        # Define the chain of agents to pass the message through
        chain = ["assistant", "knowledge", "memory"]
        results = []
        
        current_message = message
        
        # Pass the message through the chain
        for i, agent_id in enumerate(chain):
            agent = self._agents[agent_id]
            
            task = AgentTask(
                task_id=f"chain_step_{i}",
                instruction=f"Process this message and enhance it with your capabilities",
                input_data={"message": current_message}
            )
            
            # Send message to the current agent in the chain
            sender = "user" if i == 0 else chain[i-1]
            response = await self._sim_env.send_message(
                sender,
                agent.agent_id,
                MessageContent(text=current_message),
                task
            )
            
            # Update the message for the next agent
            if response and response.content.text:
                current_message = response.content.text
            
            results.append({
                "step": i + 1,
                "agent": agent.agent_card.to_dict(),
                "task": task.to_dict(),
                "input": current_message,
                "output": response.content.text if response else None
            })
        
        return {"chain": results, "final_result": current_message}

    async def _run_stateful_demo(self, message: str) -> Dict[str, Any]:
        """Run a demo that demonstrates stateful interactions.

        Args:
            message: The message to send to the memory agent.

        Returns:
            Results of the stateful demo.
        """
        self._logger.info("Running stateful A2A demo")
        
        memory_agent = self._agents["memory"]
        results = []
        
        # Series of messages to demonstrate conversation memory
        messages = [
            message,
            "What was my previous message?",
            "Can you remember all our conversation so far?"
        ]
        
        for i, msg in enumerate(messages):
            task = AgentTask(
                task_id=f"memory_task_{i}",
                instruction="Process this message while maintaining conversation context",
                input_data={"message": msg}
            )
            
            response = await self._sim_env.send_message(
                "user",
                memory_agent.agent_id,
                MessageContent(text=msg),
                task
            )
            
            results.append({
                "message_number": i + 1,
                "user_message": msg,
                "agent_response": response.content.text if response else None
            })
            
            # Add a short delay to simulate realistic conversation timing
            await asyncio.sleep(0.5)
        
        return {"interactions": results} 