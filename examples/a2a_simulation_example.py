#!/usr/bin/env python3
"""
A2A Simulation Example.

This script demonstrates the use of the A2A simulation environment
for testing multi-agent interactions.
"""

import asyncio

from pepperpy.a2a import (
    StatefulResponseHandler,
    Task,
    create_simulation,
    create_text_message,
    delayed_response_handler,
    simple_echo_handler,
)
from pepperpy.a2a.base import Message, TextPart


def print_task(task: Task) -> None:
    """Print a task in a readable format.

    Args:
        task: Task to print
    """
    print(f"\nTask ID: {task.task_id}")
    print(f"State: {task.state.value}")
    print("Messages:")

    for i, msg in enumerate(task.messages):
        # Extract text from message
        text_parts = [part.text for part in msg.parts if isinstance(part, TextPart)]
        text = " ".join(text_parts)

        # Print message
        print(f"  [{i}] {msg.role}: {text}")

    print("")


async def simple_conversation() -> None:
    """Demonstrate a simple conversation between two agents."""
    print("\n=== Simple Conversation Example ===\n")

    # Create simulation environment
    sim = await create_simulation()

    # Register agents
    alice_id, alice_card = sim.register_agent(
        name="Alice",
        description="A helpful assistant",
        response_handler=simple_echo_handler,
    )

    bob_id, bob_card = sim.register_agent(
        name="Bob",
        description="A customer service agent",
        response_handler=delayed_response_handler,
    )

    # Create initial messages
    alice_message = create_text_message(
        "user", "Hello, Bob! I need help with my order."
    )
    bob_message = create_text_message("user", "Hello, Alice! Can you process a return?")

    # Send messages
    alice_task = await sim.send_message(bob_id, alice_message)
    bob_task = await sim.send_message(alice_id, bob_message)

    # Print results
    print("Alice sent a message to Bob:")
    print_task(alice_task)

    print("Bob sent a message to Alice:")
    print_task(bob_task)


async def stateful_conversation() -> None:
    """Demonstrate a conversation with a stateful agent."""
    print("\n=== Stateful Conversation Example ===\n")

    # Create simulation environment
    sim = await create_simulation()

    # Register agent with stateful handler
    agent_id, _ = sim.register_agent(
        name="Stateful Agent",
        description="An agent that remembers conversation history",
        response_handler=StatefulResponseHandler(),
    )

    # Send a sequence of messages
    messages = [
        "Hello, agent!",
        "How are you today?",
        "Can you remember what I asked before?",
    ]

    task_id = None
    for msg_text in messages:
        message = create_text_message("user", msg_text)
        task = await sim.send_message(agent_id, message, task_id)
        task_id = task.task_id

    # Print final conversation
    print("Conversation with stateful agent:")
    print_task(task)


async def multi_agent_conversation() -> None:
    """Demonstrate a conversation between multiple agents."""
    print("\n=== Multi-Agent Conversation Example ===\n")

    # Create simulation environment
    sim = await create_simulation()

    # Register agents with different behaviors
    agents = []

    # Create a specialized response handler for the coordinator
    async def coordinator_handler(message: Message) -> Message:
        text_parts = [part.text for part in message.parts if isinstance(part, TextPart)]
        text = " ".join(text_parts)

        response = (
            f"As the coordinator, I've received: '{text}'. "
            f"I'll delegate this task to our specialized agents."
        )

        return create_text_message("agent", response)

    # Register agents
    coordinator_id, _ = sim.register_agent(
        name="Coordinator",
        description="Coordinates tasks between agents",
        response_handler=coordinator_handler,
    )

    for i in range(3):
        agent_id, _ = sim.register_agent(
            name=f"Agent-{i + 1}",
            description=f"Specialized agent #{i + 1}",
            response_handler=simple_echo_handler,
        )
        agents.append(agent_id)

    # Simulate a user request to the coordinator
    user_request = create_text_message(
        "user", "I need help analyzing this dataset and generating a report."
    )

    # Coordinator processes the request
    coord_task = await sim.send_message(coordinator_id, user_request)
    print("User request to coordinator:")
    print_task(coord_task)

    # Coordinator delegates to agents
    for i, agent_id in enumerate(agents):
        # Extract response from coordinator
        coord_response = coord_task.messages[-1]
        text_parts = [
            part.text for part in coord_response.parts if isinstance(part, TextPart)
        ]
        coord_text = " ".join(text_parts)

        # Create delegation message
        delegation = create_text_message(
            "user",
            f"[From Coordinator] {coord_text} Please handle subtask #{i + 1}.",
        )

        # Send to agent
        agent_task = await sim.send_message(agent_id, delegation)
        print(f"\nCoordinator delegated to Agent-{i + 1}:")
        print_task(agent_task)


async def main() -> None:
    """Run the simulation examples."""
    # Run examples
    await simple_conversation()
    await stateful_conversation()
    await multi_agent_conversation()


if __name__ == "__main__":
    asyncio.run(main())
