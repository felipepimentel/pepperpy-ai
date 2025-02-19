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
from rich.table import Table

from pepperpy import Pepperpy

console = Console()


def validate_api_key(api_key: str) -> bool:
    """Validate API key format."""
    return bool(api_key and len(api_key) > 10)


def validate_model_settings(temperature: float, max_tokens: int) -> bool:
    """Validate model settings."""
    return 0.0 <= temperature <= 1.0 and 1 <= max_tokens <= 32000


async def setup_wizard() -> Pepperpy:
    """Run the interactive setup wizard.

    This wizard helps users configure Pepperpy by:
    1. Checking for existing configuration
    2. Guiding through API key setup
    3. Setting up basic preferences
    4. Initializing the Hub
    5. Testing the configuration

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
    config_dir = Path.home() / ".pepper_hub"
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
        while True:
            api_key = Prompt.ask("Enter your API key")
            if validate_api_key(api_key):
                break
            console.print("[red]Invalid API key format. Please try again.[/]")

    # Select model
    console.print("\n[yellow]Model Selection[/]")
    models = {
        "gpt-4": "openai/gpt-4 (Most capable)",
        "gpt-3.5": "openai/gpt-3.5-turbo (Fast & efficient)",
        "claude-3": "anthropic/claude-3-opus (Research focused)",
        "claude-3-sonnet": "anthropic/claude-3-sonnet (Balanced)",
    }

    # Show model options
    table = Table(title="Available Models")
    table.add_column("Key", style="cyan")
    table.add_column("Model", style="green")
    table.add_column("Description", style="yellow")

    for key, value in models.items():
        name, desc = value.split(" (", 1)
        table.add_row(key, name, f"({desc}")

    console.print(table)

    model_key = Prompt.ask(
        "Choose your preferred model", choices=list(models.keys()), default="gpt-4"
    )
    model = models[model_key].split(" (")[0]

    # Configure preferences
    console.print("\n[yellow]Advanced Settings[/]")
    if Confirm.ask("Would you like to configure advanced settings?", default=False):
        temperature = float(
            Prompt.ask(
                "Temperature (0.0-1.0)",
                default="0.7",
                show_default=True,
            )
        )
        max_tokens = int(
            Prompt.ask(
                "Maximum tokens per response",
                default="2048",
                show_default=True,
            )
        )

        # Validate settings
        if not validate_model_settings(temperature, max_tokens):
            console.print("[red]Invalid settings. Using defaults.[/]")
            temperature = 0.7
            max_tokens = 2048
    else:
        temperature = 0.7
        max_tokens = 2048

    # Initialize Hub
    console.print("\n[yellow]Hub Setup[/]")
    if Confirm.ask("Would you like to initialize the Pepper Hub?", default=True):
        hub_dir = Path.home() / ".pepper_hub"
        hub_dir.mkdir(parents=True, exist_ok=True)

        # Create standard directories
        for subdir in ["agents", "prompts", "workflows", "plugins"]:
            (hub_dir / subdir).mkdir(exist_ok=True)

        console.print("[green]✓ Hub initialized successfully[/]")

    # Save configuration
    with open(config_file, "w") as f:
        f.write(f"PEPPERPY_API_KEY={api_key}\n")
        f.write(f"PEPPERPY_MODEL={model}\n")
        f.write(f"PEPPERPY_TEMPERATURE={temperature}\n")
        f.write(f"PEPPERPY_MAX_TOKENS={max_tokens}\n")

    # Create client
    pepper = await Pepperpy.create(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
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
            "- [blue]pepper.chat('Start chatting')[/]\n\n"
            "For more examples and documentation:\n"
            "- Run [bold]pepperpy doctor[/] to check your setup\n"
            "- Visit [link]https://github.com/pepperpy/pepperpy[/link]"
        )
    )

    return pepper


def save_config(api_key: str, model: str) -> None:
    """Save configuration to .env file.

    Args:
        api_key: The API key to save
        model: The model name to save

    """
    env_path = Path.home() / ".pepper_hub" / ".env"
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
