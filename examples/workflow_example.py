"""Example demonstrating the workflow functionality of Pepperpy.

This example shows how to:
1. Initialize Pepperpy with minimal configuration
2. Load and run workflows
3. Monitor workflow progress
4. Handle workflow results
"""

import asyncio
from pathlib import Path

from pepperpy import Pepperpy


async def run_research_workflow():
    """Run a research workflow that coordinates multiple agents."""
    pepper = await Pepperpy.create()

    # Load workflow from hub
    workflow = await pepper.hub.workflow("research/comprehensive")

    # Run workflow with progress monitoring
    result = await workflow.run(
        "Impact of AI in Healthcare", max_sources=5, style="academic"
    )

    # Print findings
    print("\nKey Findings:")
    for finding in result.findings:
        print(f"- {finding}")


async def run_custom_workflow():
    """Create and run a custom workflow."""
    pepper = await Pepperpy.create()

    # Create workflow configuration
    config_path = Path.home() / ".pepperpy/hub/teams/research-team.yaml"

    # Create and initialize team
    team = await pepper.hub.team("research-team")

    # Run team workflow
    result = await team.run("Research AI Impact")

    # Print results
    print(f"\nReport Summary: {result.summary}")


async def main():
    # Run workflow examples
    await run_research_workflow()
    await run_custom_workflow()


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
