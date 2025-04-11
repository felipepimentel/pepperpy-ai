"""Tool provider factory module."""

import importlib
import logging

from plugins.workflow.ai_gateway.gateway import GatewayComponent


async def create_tool(tool_config: dict) -> GatewayComponent | None:
    """Create a tool provider from configuration.

    Args:
        tool_config: Tool configuration

    Returns:
        Tool provider or None if creation failed
    """
    logger = logging.getLogger("ToolFactory")

    # Get tool provider details
    provider_type = tool_config.get("provider")
    tool_id = tool_config.get("id")

    if not provider_type or not tool_id:
        logger.error(f"Invalid tool configuration: {tool_config}")
        return None

    try:
        # Form the module path
        module_path = f"plugins.tool.{tool_id}.{provider_type}.provider"

        # Import the module
        module = importlib.import_module(module_path)

        # Find provider class (assuming it ends with 'Provider')
        provider_class = None
        for attr_name in dir(module):
            if attr_name.endswith("Provider") and not attr_name.startswith("_"):
                provider_class = getattr(module, attr_name)
                break

        if not provider_class:
            logger.error(f"No provider class found in {module_path}")
            return None

        # Create provider instance
        provider = provider_class(**tool_config)

        # Initialize the provider
        await provider.initialize()

        logger.info(f"Created and initialized tool provider: {tool_id}/{provider_type}")
        return provider
    except ImportError as e:
        logger.error(f"Failed to import tool provider {tool_id}/{provider_type}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error creating tool provider {tool_id}/{provider_type}: {e}")
        return None
