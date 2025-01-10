"""Autogen team example."""

import asyncio

from pepperpy_ai.teams import TeamConfig
from pepperpy_ai.teams.providers.autogen import AutogenTeamProvider


async def main() -> None:
    """Run example."""
    # Create team provider
    config = TeamConfig(
        name="autogen-team",
        provider="autogen",  # Specify the provider type
        members=["planner", "executor"],
        settings={  # Use settings instead of roles
            "roles": {
                "planner": "Plans and breaks down tasks",
                "executor": "Executes planned tasks",
            }
        },
    )
    provider = AutogenTeamProvider(config)
    await provider.initialize()

    try:
        # Execute task
        result = await provider.execute_task(
            "Design and implement a REST API for a todo list application"
        )
        print(f"Result: {result.content}")

        # Get team info
        members = await provider.get_team_members()
        roles = await provider.get_team_roles()
        print(f"Team members: {members}")
        print(f"Team roles: {roles}")

    finally:
        await provider.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
