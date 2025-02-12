"""Example of using Pepperpy's quick start functionality."""

from pepperpy import Pepperpy


def main():
    """Run the example."""
    # Start interactive setup
    pepper = Pepperpy.quick_start()

    # Show usage examples
    print("\nUsage Examples:")
    print("""
    # Simple questions
    async with pepper as p:
        result = await p.ask("What is AI?")
        print(result)
    
    # Research topics
    async with pepper as p:
        result = await p.research("Impact of AI in Healthcare")
        print(result.tldr)  # Short summary
        print(result.full)  # Full report
        
    # Use teams
    async with pepper as p:
        team = await p.hub.team("research-team")
        async with team.run("Analyze AI trends") as session:
            print(session.current_step)
    """)


if __name__ == "__main__":
    main()
