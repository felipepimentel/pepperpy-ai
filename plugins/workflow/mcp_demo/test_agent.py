#!/usr/bin/env python3
"""Test script for agent orchestration.

This script runs a simple test of the agent orchestration functionality.
"""

import asyncio
import json
import os
import sys
from typing import Any

# Add the current directory to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Import directly
from workflow import MCPDemoWorkflow


async def run_agent_test(task: str) -> dict[str, Any]:
    """Run a test of the agent orchestration.

    Args:
        task: Task description

    Returns:
        Test results
    """
    print(f"Testing agent orchestration with task: {task}")

    # Create workflow
    workflow = MCPDemoWorkflow(
        config={
            "host": "0.0.0.0",
            "port": 8000,
            "demo_duration": 30,
        }
    )

    # Initialize workflow
    print("Initializing workflow...")
    await workflow.initialize()

    try:
        # Create input data
        input_data = {
            "workflow_type": "agent",
            "task": task,
        }

        # Execute workflow
        print("Executing agent workflow...")
        result = await workflow.execute(input_data)
        return result
    finally:
        # Clean up
        print("Cleaning up workflow...")
        await workflow.cleanup()


async def main() -> None:
    """Run the test."""
    # Get task from command line arguments
    task = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Create a brief summary of AI trends for 2025"
    )

    # Run the test
    result = await run_agent_test(task)

    # Print result
    print("\nAgent test results:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
