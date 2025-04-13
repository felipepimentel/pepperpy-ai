"""
Agent-to-Agent Simulation Module.

This module provides functionality to simulate interactions between
multiple agents within PepperPy.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional, Callable, Awaitable, Tuple

class SimulatedAgent:
    """A simulated agent that can receive and respond to messages."""
    
    def __init__(
        self, 
        agent_id: str,
        name: str,
        response_handler: Callable[[str, Dict[str, Any]], Awaitable[str]]
    ):
        """
        Initialize a simulated agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            response_handler: Async function that generates responses
        """
        self.agent_id = agent_id
        self.name = name
        self.response_handler = response_handler
        self.state: Dict[str, Any] = {}
        self.message_history: List[Dict[str, Any]] = []
    
    async def receive_message(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Process an incoming message and generate a response.

    Args:
            message: The incoming message text
            metadata: Optional metadata about the message
            
        Returns:
            The agent's response
        """
        if metadata is None:
            metadata = {}
        
        # Record the message in history
        self.message_history.append({
            "role": "incoming",
            "content": message,
            "metadata": metadata
        })
        
        # Generate a response using the handler
        context = {
            "agent_id": self.agent_id,
            "name": self.name,
            "state": self.state,
            "history": self.message_history,
        }
        
        response = await self.response_handler(message, context)
        
        # Record the response in history
        self.message_history.append({
            "role": "outgoing",
            "content": response,
            "metadata": {}
        })
        
        return response

class SimulationEnvironment:
    """Environment for simulating agent-to-agent interactions."""
    
    def __init__(self):
        """Initialize the simulation environment."""
        self.agents: Dict[str, SimulatedAgent] = {}
    
    def register_agent(
        self,
        name: str,
        response_handler: Callable[[str, Dict[str, Any]], Awaitable[str]],
        agent_id: Optional[str] = None
    ) -> str:
        """
        Register an agent in the simulation.
        
        Args:
            name: Human-readable name for the agent
            response_handler: Function that generates responses
            agent_id: Optional agent ID (generated if not provided)
            
        Returns:
            The agent's ID
        """
        if agent_id is None:
            agent_id = str(uuid.uuid4())
        
        agent = SimulatedAgent(agent_id, name, response_handler)
        self.agents[agent_id] = agent
        
        return agent_id
    
    async def send_message(
        self,
        from_agent_id: str,
        to_agent_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Send a message from one agent to another.
        
        Args:
            from_agent_id: ID of the sending agent
            to_agent_id: ID of the receiving agent
            message: The message to send
            metadata: Optional metadata about the message
            
        Returns:
            The receiving agent's response
        """
        if metadata is None:
            metadata = {}
        
        if from_agent_id not in self.agents:
            raise ValueError(f"Agent with ID {from_agent_id} not found")
        
        if to_agent_id not in self.agents:
            raise ValueError(f"Agent with ID {to_agent_id} not found")
        
        metadata["from_agent_id"] = from_agent_id
        metadata["from_agent_name"] = self.agents[from_agent_id].name
        
        response = await self.agents[to_agent_id].receive_message(message, metadata)
        return response

# Sample response handlers for different agent behaviors

async def echo_response_handler(message: str, context: Dict[str, Any]) -> str:
    """Simple handler that echoes the received message."""
    return f"Echo: {message}"

async def delayed_response_handler(message: str, context: Dict[str, Any]) -> str:
    """Handler that introduces a delay before responding."""
    await asyncio.sleep(1)  # Simulate processing time
    return f"After thinking about '{message}', I respond with: This is a delayed response."

async def stateful_response_handler(message: str, context: Dict[str, Any]) -> str:
    """Handler that maintains state between messages."""
    state = context["state"]
    
    # Initialize conversation state if it doesn't exist
    if "topic" not in state:
        state["topic"] = None
        state["message_count"] = 0
    
    # Update state
    state["message_count"] += 1
    
    if state["topic"] is None and "topic" in message.lower():
        # Extract topic from the message
        state["topic"] = message.split("topic", 1)[1].strip()
        return f"I'll remember our topic is about {state['topic']}. What would you like to know?"
    
    if state["topic"] is not None:
        return f"Regarding {state['topic']}, this is response #{state['message_count']}. You said: {message}"
    
    return f"Message received ({state['message_count']}): {message}"

async def execute_simulation(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the A2A simulation workflow.
    
    Args:
        inputs: The workflow inputs
        
    Returns:
        The workflow result
    """
    scenario = inputs.get('scenario', 'simple_conversation')
    agent_count = int(inputs.get('agent_count', 2))
    initial_message = inputs.get('initial_message', 'Hello, agents!')

    # Create simulation environment
    sim = SimulationEnvironment()
    
    # Register agents based on scenario
    agent_ids = []
    if scenario == 'simple_conversation':
        agent_ids.append(sim.register_agent("Echo Agent", echo_response_handler))
        agent_ids.append(sim.register_agent("Delayed Agent", delayed_response_handler))
    elif scenario == 'stateful_interaction':
        agent_ids.append(sim.register_agent("Memory Agent 1", stateful_response_handler))
        agent_ids.append(sim.register_agent("Memory Agent 2", stateful_response_handler))
    elif scenario == 'multi_agent_collaboration':
        for i in range(agent_count):
            if i % 3 == 0:
                agent_ids.append(sim.register_agent(f"Echo Agent {i+1}", echo_response_handler))
            elif i % 3 == 1:
                agent_ids.append(sim.register_agent(f"Delayed Agent {i+1}", delayed_response_handler))
            else:
                agent_ids.append(sim.register_agent(f"Memory Agent {i+1}", stateful_response_handler))
    
    # Run the simulation
    conversation = []
    
    # Initial message from user to first agent
    from_id = "user"
    from_name = "User"
    to_id = agent_ids[0]
    to_name = sim.agents[to_id].name
    message = initial_message
    
    conversation.append({
        "from": {"id": from_id, "name": from_name},
        "to": {"id": to_id, "name": to_name},
        "message": message,
        "timestamp": 0
    })
    
    # Simulate conversation between agents
    current_timestamp = 1
    max_exchanges = 10  # Limit the number of exchanges to prevent infinite loops
    
    for i in range(max_exchanges):
        # Current agent responds and sends to next agent
        current_agent_id = agent_ids[i % len(agent_ids)]
        next_agent_id = agent_ids[(i + 1) % len(agent_ids)]
        
        response = await sim.send_message(
            from_agent_id=from_id if i == 0 else current_agent_id,
            to_agent_id=current_agent_id,
            message=message
        )
        
        conversation.append({
            "from": {"id": current_agent_id, "name": sim.agents[current_agent_id].name},
            "to": {"id": next_agent_id, "name": sim.agents[next_agent_id].name},
            "message": response,
            "timestamp": current_timestamp
        })
        
        message = response
        from_id = current_agent_id
        current_timestamp += 1
        
        # For simple conversation, limit to fewer exchanges
        if scenario == 'simple_conversation' and i >= 3:
            break
    
    # Prepare agent information for the result
    agents_info = []
    for agent_id in agent_ids:
        agent = sim.agents[agent_id]
        agents_info.append({
            "id": agent.agent_id,
            "name": agent.name,
            "message_count": len(agent.message_history) // 2,  # Each exchange is 2 messages in history
            "state": agent.state
        })
    
    return {
        "scenario": scenario,
        "agent_count": len(agent_ids),
        "conversation": conversation,
        "agents": agents_info
    }
