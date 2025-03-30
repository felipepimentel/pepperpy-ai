"""Example showing plugin management with UV."""

import asyncio
import os
from pathlib import Path

from loguru import logger

from pepperpy import PepperPy, install_plugin_dependencies, plugin_manager


async def install_plugins() -> None:
    """Install plugin dependencies using UV."""
    # Get the plugins directory
    current_dir = Path(__file__).parent
    plugins_dir = current_dir.parent / "plugins"

    print("Available plugins:")
    for plugin_dir in plugins_dir.iterdir():
        if plugin_dir.is_dir():
            print(f"  - {plugin_dir.name}")

    # Install all plugins
    print("\nInstalling all plugin dependencies...")
    results = plugin_manager.install_all_plugins()
    for plugin_name, success in results.items():
        status = "✓ Successfully installed" if success else "✗ Failed to install"
        print(f"  {status}: {plugin_name}")

    # Install a specific plugin
    print("\nInstalling a specific plugin (llm_openai)...")
    success = install_plugin_dependencies("llm_openai")
    status = "✓ Successfully installed" if success else "✗ Failed to install"
    print(f"  {status}: llm_openai")


async def use_plugin() -> None:
    """Use an installed plugin."""
    print("\nUsing the OpenAI plugin:")
    try:
        async with PepperPy().with_llm(
            provider_type="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-3.5-turbo",
        ) as pepper:
            # Generate text using the plugin
            result = await pepper.chat.with_user(
                "What's the capital of France?"
            ).generate()
            print(f"\nResponse: {result.content}")
    except Exception as e:
        logger.error(f"Error using plugin: {e}")


async def main() -> None:
    """Run the example."""
    try:
        await install_plugins()
        await use_plugin()
    except Exception as e:
        logger.error(f"Example failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
