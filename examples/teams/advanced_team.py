"""Advanced team example."""

import asyncio

from pepperpy_ai.teams import TeamConfig
from pepperpy_ai.teams.providers.autogen import AutogenTeamProvider


async def main() -> None:
    """Run example."""
    # Create team provider
    config = TeamConfig(
        name="example-team",
        provider="autogen",  # Specify the provider type
        members=["developer", "reviewer"],
        settings={  # Use settings instead of roles
            "roles": {"developer": "Writes code", "reviewer": "Reviews code"}
        },
    )
    provider = AutogenTeamProvider(config)
    await provider.initialize()

    try:
        # Execute task
        result = await provider.execute_task(
            "Create a simple Python function to calculate factorial"
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
