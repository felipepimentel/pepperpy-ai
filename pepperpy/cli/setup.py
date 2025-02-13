"""CLI setup wizard for Pepperpy.

This module provides an interactive setup wizard to help users
configure Pepperpy with a friendly step-by-step guide.
"""

import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from pepperpy import Pepperpy

console = Console()


async def setup_wizard() -> Pepperpy:
    """Run the interactive setup wizard.

    This wizard helps users configure Pepperpy by:
    1. Checking for existing configuration
    2. Guiding through API key setup
    3. Setting up basic preferences
    4. Testing the configuration

    Returns:
        A configured Pepperpy instance

    Example:
        >>> pepper = await Pepperpy.quick_start()  # Launches wizard
        >>> result = await pepper.ask("Hello!")

    """
    console.print(
        Panel.fit(
            "[bold blue]Welcome to Pepperpy Setup![/]\n\n"
            "This wizard will help you get started with Pepperpy "
            "by configuring the essential settings."
        )
    )

    # Check for existing config
    config_dir = Path.home() / ".pepperpy"
    config_file = config_dir / "config.env"

    if config_file.exists() and not Confirm.ask(
        "\nExisting configuration found. Would you like to reconfigure?"
    ):
        # Load existing config
        return await Pepperpy.create()

    # Ensure config directory exists
    config_dir.mkdir(parents=True, exist_ok=True)

    # Get API key
    api_key = os.getenv("PEPPERPY_API_KEY")
    if not api_key:
        console.print("\n[yellow]API Key Setup[/]")
        console.print(
            "You'll need an API key from OpenRouter. "
            "Visit https://openrouter.ai to get one."
        )
        api_key = Prompt.ask("Enter your API key")

    # Select model
    console.print("\n[yellow]Model Selection[/]")
    models = [
        "openai/gpt-4",
        "openai/gpt-3.5-turbo",
        "anthropic/claude-3-opus",
        "anthropic/claude-3-sonnet",
    ]
    model = Prompt.ask(
        "Choose your preferred model", choices=models, default="openai/gpt-4"
    )

    # Configure preferences
    console.print("\n[yellow]Preferences[/]")
    temperature = float(Prompt.ask("Temperature (0.0-1.0)", default="0.7"))
    max_tokens = int(Prompt.ask("Maximum tokens per response", default="2048"))

    # Save configuration
    with open(config_file, "w") as f:
        f.write(f"PEPPERPY_API_KEY={api_key}\n")
        f.write(f"PEPPERPY_MODEL={model}\n")
        f.write(f"PEPPERPY_TEMPERATURE={temperature}\n")
        f.write(f"PEPPERPY_MAX_TOKENS={max_tokens}\n")

    # Create client
    pepper = await Pepperpy.create(
        api_key=api_key, model=model, temperature=temperature, max_tokens=max_tokens
    )

    # Test configuration
    console.print("\n[yellow]Testing Configuration[/]")
    try:
        response = await pepper.ask("Hello! This is a test message.")
        console.print("[green]✓ Configuration test successful![/]")
    except Exception as e:
        console.print(f"[red]✗ Configuration test failed: {e}[/]")
        if Confirm.ask("Would you like to try again?"):
            return await setup_wizard()
        sys.exit(1)

    console.print(
        Panel.fit(
            "[bold green]Setup Complete![/]\n\n"
            "You can now use Pepperpy with the following methods:\n"
            "- [blue]pepper = await Pepperpy.create()[/]\n"
            "- [blue]result = await pepper.ask('Your question')[/]\n"
            "- [blue]pepper.chat('Start chatting')[/]"
        )
    )

    return pepper


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
