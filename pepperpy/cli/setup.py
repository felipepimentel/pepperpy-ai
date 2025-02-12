"""CLI setup wizard for Pepperpy configuration."""

import os
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, Prompt

from pepperpy import Pepperpy

console = Console()


async def setup_wizard() -> Pepperpy:
    """Interactive setup wizard for Pepperpy.

    Returns:
        A configured Pepperpy instance

    Example:
        >>> pepper = await setup_wizard()
        >>> # Follow the interactive prompts...

    """
    console.print("\n[bold blue]Welcome to Pepperpy Setup![/bold blue]")
    console.print("Let's get you started with a basic configuration.\n")

    # Get API key
    api_key = os.getenv("PEPPERPY_API_KEY")
    if not api_key:
        console.print("[yellow]No API key found in environment.[/yellow]")
        api_key = Prompt.ask("Please enter your API key", password=True)

    # Choose model
    default_model = "openai/gpt-4"
    model = Prompt.ask(
        "Which model would you like to use?",
        default=default_model,
        choices=["openai/gpt-4", "openai/gpt-3.5-turbo", "anthropic/claude-3"],
    )

    # Save configuration?
    if Confirm.ask("Would you like to save this configuration?"):
        save_config(api_key, model)
        console.print("[green]Configuration saved![/green]")

    # Create instance
    instance = await Pepperpy.create(api_key=api_key, model=model)
    console.print(
        "\n[bold green]Setup complete! You're ready to start using Pepperpy.[/bold green]"
    )

    # Show example
    console.print("\nQuick example:")
    console.print("""
    [blue]async with pepper as p:
        result = await p.ask("What is AI?")
        print(result)[/blue]
    """)

    return instance


def save_config(api_key: str, model: str) -> None:
    """Save configuration to .env file.

    Args:
        api_key: The API key to save
        model: The model name to save

    """
    env_path = Path.home() / ".pepperpy" / ".env"
    env_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing config
    config = {}
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    config[key] = value

    # Update config
    config["PEPPERPY_API_KEY"] = api_key
    config["PEPPERPY_MODEL"] = model

    # Write config
    with open(env_path, "w") as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")


if __name__ == "__main__":
    import asyncio

    asyncio.run(setup_wizard())
