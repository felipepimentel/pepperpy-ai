#!/usr/bin/env python3
"""
PepperPy AI Mesh Runner

This script runs the complete PepperPy AI Mesh solution,
providing a unified gateway to multiple AI models and tools with orchestration.
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
from typing import Any

# Core imports
# Local imports
from plugins.workflow.ai_gateway.create_tool import create_tool
from plugins.workflow.ai_gateway.gateway import (
    create_auth_provider,
    create_model_provider,
    create_routing_provider,
)

# Add the project root to sys.path if needed
if os.path.exists(os.path.join(os.path.dirname(__file__), "..", "..", "..")):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


# Test client function
async def test_ai_mesh(host: str, port: int, debug: bool = False) -> None:
    """Run AI Mesh with a test request.

    Args:
        host: Host address
        port: Port number
        debug: Enable debug mode
    """
    # Make sure we use the correct port
    port = port or 8081

    # Start the server in background
    gateway_task = asyncio.create_task(run_ai_mesh(None, host, port, debug, test=True))

    # Wait for server to start - longer timeout to allow initialization
    await asyncio.sleep(5)

    # Run test requests
    await _run_test_requests(host, port)

    # Cancel the server task
    gateway_task.cancel()
    try:
        await gateway_task
    except asyncio.CancelledError:
        pass


async def _run_test_requests(host: str, port: int, api_key: str = "test-key-1") -> None:
    """Run test requests against the AI Mesh.

    Args:
        host: Gateway host
        port: Gateway port
        api_key: API key for authentication
    """
    # Make sure to use the configured port
    port = port or 8081

    async with aiohttp.ClientSession() as session:
        # Test chat with default model
        await test_chat(session, host, port, api_key)

        # Test calculator tool
        await test_calculator(session, host, port, api_key)


async def test_chat(
    session, host: str, port: int, api_key: str, model: str | None = None
) -> None:
    """Test chat with a model.

    Args:
        session: aiohttp session
        host: Gateway host
        port: Gateway port
        api_key: API key for authentication
        model: Model ID (optional)
    """
    print(f"\n\nTesting chat with {model or 'default'} model")

    endpoint = f"http://{host}:{port}/api/llm"
    if model:
        endpoint = f"http://{host}:{port}/api/{model}"

    data = {
        "operation": "chat",
        "messages": [{"role": "user", "content": "What is the capital of France?"}],
    }

    try:
        async with session.post(
            endpoint, json=data, headers={"X-API-Key": api_key}
        ) as response:
            print(f"Response status: {response.status}")
            result = await response.json()
            print(f"Response data: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Error during test: {e}")


async def test_calculator(session, host: str, port: int, api_key: str) -> None:
    """Test calculator tool.

    Args:
        session: aiohttp session
        host: Gateway host
        port: Gateway port
        api_key: API key for authentication
    """
    print("\n\nTesting calculator tool")

    endpoint = f"http://{host}:{port}/api/calculator"

    data = {"expression": "(35 * 2) / 7 + 4"}

    try:
        async with session.post(
            endpoint, json=data, headers={"X-API-Key": api_key}
        ) as response:
            print(f"Response status: {response.status}")
            result = await response.json()
            print(f"Response data: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Error during test: {e}")


# AI Mesh runner
async def run_ai_mesh(config_path=None, host=None, port=None, debug=False, test=False):
    """Run the AI Mesh solution.

    Args:
        config_path: Path to configuration file
        host: Host to bind the server
        port: Port to bind the server
        debug: Enable debug mode
        test: Run tests
    """
    logger = logging.getLogger("ai_mesh")
    logger.info("Starting AI Mesh...")

    # Initialize resources that should only be initialized once
    resources = {}
    resource_errors = []

    try:
        # Load configuration
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                config = yaml.safe_load(f)
        else:
            config = {}

        # Get global configuration
        global_config = config.get("global", {})

        # Get models configuration
        models_config = config.get("models", {})
        if not models_config:
            logger.warning("No models configured")

        # Get routing configuration
        routing_config = config.get("routing", {})
        if not routing_config:
            logger.warning("No routing configured")

        # Override host and port if provided
        # Ensure host is never None
        host = host or routing_config.get("host") or "0.0.0.0"
        port = port or routing_config.get("port", 8081)

        # Log selected host and port
        logger.info(f"Using host: {host}, port: {port}")

        # Get multiport configuration - enables multiple service endpoints
        multiport_config = config.get("multiport", {})
        services = multiport_config.get("services", [])

        # Configure advanced features
        feature_flags = _configure_feature_flags(config)

        # Create necessary providers
        providers = await _create_providers(config, logger)
        resources.update(providers)

        # Extract providers from resources
        auth_provider = resources.get("auth_provider")
        model_providers = resources.get("model_providers", {})
        tools = resources.get("tools", {})

        if not model_providers:
            logger.warning(
                "No model providers created. Check your configuration for LLM providers."
            )
            logger.warning(
                "Continuing without model providers - only tools will be available."
            )
            # Continue anyway to allow tool-only operation

        # Create routing provider with necessary dependencies
        routing_provider = await _create_routing_provider(
            routing_config, auth_provider, model_providers, tools, logger
        )

        if routing_provider:
            resources["routing_provider"] = routing_provider
            # Add routing provider to config for test access
            config["routing_provider"] = routing_provider

            logger.info(
                f"Routing provider created: {routing_provider.__class__.__name__}"
            )
        else:
            logger.error("Failed to create routing provider")
            logger.error("Cannot start the gateway without a routing provider")
            return 1

        # Configure resource cleanup on shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(
                    _cleanup_resources(
                        [
                            r
                            for r in resources.values()
                            if hasattr(r, "cleanup") and callable(r.cleanup)
                        ]
                    )
                ),
            )

        # Report any resource initialization errors
        if resource_errors:
            logger.warning(f"Resource initialization errors: {len(resource_errors)}")
            for error in resource_errors:
                logger.warning(f" - {error}")

        # If running in test mode, just run tests
        if test:
            await _run_service_tests(host, port, config, logger)
            await _cleanup_resources(
                [
                    r
                    for r in resources.values()
                    if hasattr(r, "cleanup") and callable(r.cleanup)
                ]
            )
            return 0

        # Start services in multiport mode if configured
        if services and multiport_config.get("enabled", False):
            await _start_multiport_services(
                services, routing_provider, host, port, config, logger
            )
        else:
            # Start single service - first configure the host and port
            logger.info(f"AI Mesh starting on {host}:{port}")
            await routing_provider.configure(host, port)
            await routing_provider.start()
            logger.info(f"AI Mesh running on {host}:{port}")

        # Keep server running
        while True:
            await asyncio.sleep(3600)

    except asyncio.CancelledError:
        logger.info("AI Mesh shutdown requested")
    except Exception as e:
        logger.error(f"Error running AI Mesh: {e}")
        if debug:
            logger.exception("Detailed error:")
        return 1
    finally:
        # Clean up resources
        await _cleanup_resources(
            [
                r
                for r in resources.values()
                if hasattr(r, "cleanup") and callable(r.cleanup)
            ]
        )

    return 0


def _configure_feature_flags(config: dict) -> dict:
    """Configure feature flags from configuration.

    Args:
        config: Configuration dictionary

    Returns:
        Dictionary of feature flags
    """
    return {
        "rag_enabled": config.get("rag", {}).get("enabled", False),
        "function_calling_enabled": config.get("function_calling", {}).get(
            "enabled", True
        ),
        "federation_enabled": config.get("federation", {}).get("enabled", False),
        "guardrails_enabled": config.get("guardrails", {}).get("enabled", False),
        "fine_tuning_enabled": config.get("fine_tuning", {}).get("enabled", False),
        "cost_optimization_enabled": config.get("cost_optimization", {}).get(
            "enabled", True
        ),
        "caching_enabled": config.get("caching", {}).get("enabled", True),
        "multimodal_enabled": config.get("multimodal", {}).get("enabled", False),
        "plugin_marketplace_enabled": config.get("plugin_marketplace", {}).get(
            "enabled", False
        ),
        "compliance_enabled": config.get("compliance", {}).get("enabled", False),
    }


async def _create_providers(config: dict, logger: logging.Logger) -> dict:
    """Create necessary providers from configuration.

    Args:
        config: Configuration dictionary
        logger: Logger instance

    Returns:
        Dictionary of created providers
    """
    resources = {}
    resource_errors = []

    # Create auth provider
    try:
        auth_config = config.get("auth", {})
        try:
            auth_provider = await create_auth_provider(
                auth_config.get("provider", "basic"), **auth_config
            )
            if auth_provider:
                logger.info(
                    f"Auth provider created: {auth_provider.__class__.__name__}"
                )
                resources["auth_provider"] = auth_provider
            else:
                logger.warning(
                    "No auth provider created - provider factory returned None"
                )
        except Exception as auth_error:
            logger.warning(
                f"Error creating auth provider via plugin system: {auth_error}"
            )
            logger.warning(
                "Running without authentication - this is NOT recommended for production"
            )
            auth_provider = None
    except Exception as e:
        logger.error(f"Error creating auth provider: {e}")
        resource_errors.append(f"Auth provider creation error: {e}")

    # Create model providers
    model_providers = {}
    models_config = config.get("models", {})
    for model_name, model_config in models_config.items():
        try:
            provider_type = model_config.get("provider")
            try:
                model_provider = await create_model_provider(
                    provider_type, **model_config
                )
                if model_provider:
                    logger.info(
                        f"Model provider created: {model_name} - {model_provider.__class__.__name__}"
                    )
                    model_providers[model_name] = model_provider
                else:
                    logger.warning(
                        f"No model provider created for {model_name} - provider factory returned None"
                    )
            except Exception as model_error:
                logger.warning(
                    f"Error creating model provider {model_name} via plugin system: {model_error}"
                )
                logger.warning(f"Skipping model {model_name}")
        except Exception as e:
            logger.error(f"Error creating model provider {model_name}: {e}")
            resource_errors.append(f"Model provider {model_name} creation error: {e}")

    resources["model_providers"] = model_providers

    # Create tools
    tools = {}
    tools_config = config.get("tools", {})
    for tool_name, tool_config in tools_config.items():
        try:
            # Ensure the tool_name is set in the config
            if "id" not in tool_config:
                tool_config["id"] = tool_name

            try:
                # Try to load tool via plugin system
                tool = await create_tool(tool_config)
                if tool:
                    logger.info(
                        f"Tool created: {tool_name} - {tool.__class__.__name__}"
                    )
                    tools[tool_name] = tool
                else:
                    logger.warning(
                        f"No tool provider created for {tool_name} - plugin system returned None"
                    )
            except Exception as plugin_error:
                # Log plugin error
                logger.warning(
                    f"Error loading tool {tool_name} via plugin system: {plugin_error}"
                )

                # Skip this tool for now
                logger.warning(f"Skipping tool {tool_name} for now")

        except Exception as e:
            logger.error(f"Error creating tool {tool_name}: {e}")
            resource_errors.append(f"Tool {tool_name} creation error: {e}")

    resources["tools"] = tools
    resources["resource_errors"] = resource_errors

    return resources


async def _create_routing_provider(
    routing_config: dict,
    auth_provider,
    model_providers: dict,
    tools: dict,
    logger: logging.Logger,
) -> Any:
    """Create routing provider.

    Args:
        routing_config: Routing configuration
        auth_provider: Auth provider instance
        model_providers: Dictionary of model providers
        tools: Dictionary of tools
        logger: Logger instance

    Returns:
        Routing provider instance or None if failed
    """
    provider_types = [routing_config.get("provider", "basic"), "basic", "simple"]

    # Try each provider type in order
    for provider_type in provider_types:
        try:
            logger.info(
                f"Attempting to create routing provider with type: {provider_type}"
            )

            # Create the routing provider - await the coroutine to get the actual provider
            routing_provider = await create_routing_provider(provider_type)

            if routing_provider:
                # Add auth provider
                if auth_provider:
                    await routing_provider.set_auth_provider(auth_provider)

                # Register model backends
                for name, provider in model_providers.items():
                    await routing_provider.register_backend(name, provider)
                    logger.info(f"Registered model backend: {name}")

                # Register tool backends
                for name, tool in tools.items():
                    await routing_provider.register_backend(name, tool)
                    logger.info(f"Registered tool backend: {name}")

                logger.info(
                    f"Successfully created routing provider with type: {provider_type}"
                )
                return routing_provider

            logger.warning(f"No routing provider created for type: {provider_type}")

        except Exception as e:
            logger.warning(
                f"Error creating routing provider with type {provider_type}: {e}"
            )
            # Continue to try the next provider type

    # If we reach here, all provider types failed
    logger.error("Failed to create routing provider with any of the available types")
    return None


async def _start_multiport_services(
    services: list,
    routing_provider,
    default_host: str,
    default_port: int,
    config: dict,
    logger: logging.Logger,
) -> None:
    """Start services in multiport mode.

    Args:
        services: List of service configurations
        routing_provider: Routing provider instance
        default_host: Default host if not specified in service
        default_port: Default port if not specified in service
        config: Global configuration
        logger: Logger instance
    """
    # Create tasks for each service
    service_tasks = []

    for service in services:
        name = service.get("name", "unnamed")
        host = service.get("host", default_host)
        port = service.get("port", default_port)
        service_type = service.get("type", "api")

        logger.info(f"Starting service {name} ({service_type}) on {host}:{port}")

        # Configure service-specific settings based on type
        service_config = service.get("config", {})

        # Create a copy of the routing provider for this service
        # This would typically clone the provider and apply service-specific config
        # For now, we're using the same provider instance

        task = asyncio.create_task(
            routing_provider.start(host, port, service_config), name=f"service-{name}"
        )
        service_tasks.append(task)

        logger.info(f"Service {name} started on {host}:{port}")

    # Wait for all services to complete (they shouldn't unless errored)
    if service_tasks:
        done, pending = await asyncio.wait(
            service_tasks, return_when=asyncio.FIRST_COMPLETED
        )

        # If any task completes, it's an error
        for task in done:
            try:
                await task
            except Exception as e:
                service_name = task.get_name()
                logger.error(f"Service {service_name} failed: {e}")


async def _cleanup_resources(resources_to_cleanup: list):
    """Cleanup resources upon shutdown.

    Args:
        resources_to_cleanup: List of resources to cleanup
    """
    for resource in resources_to_cleanup:
        if hasattr(resource, "cleanup") and callable(resource.cleanup):
            await resource.cleanup()


async def _run_service_tests(
    host: str, port: int, config: dict, logger: logging.Logger
) -> None:
    """Run tests for the service.

    Args:
        host: Service host
        port: Service port
        config: Configuration dictionary
        logger: Logger instance
    """
    logger.info("Running service tests...")
    try:
        # Get test configuration
        test_config = config.get("test", {})
        api_key = test_config.get("api_key", "test-key-1")

        # Just run the tests without starting server to avoid API incompatibility
        async with aiohttp.ClientSession() as session:
            # Test chat with default model
            logger.info("Testing chat endpoint (may fail if server not running)...")
            await test_chat(session, host, port, api_key)

            # Test calculator tool
            logger.info(
                "Testing calculator endpoint (may fail if server not running)..."
            )
            await test_calculator(session, host, port, api_key)

        logger.info("Service tests completed")
    except Exception as e:
        logger.error(f"Error running service tests: {e}")


def main() -> int:
    """Command-line entry point.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Run an AI Mesh server")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8081, help="Port to listen on (default: 8081)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--test", action="store_true", help="Run a test request after startup"
    )

    args = parser.parse_args()

    try:
        if args.test:
            asyncio.run(test_ai_mesh(args.host, args.port, args.debug))
            return 0
        else:
            asyncio.run(run_ai_mesh(args.config, args.host, args.port, args.debug))
            return 0
    except KeyboardInterrupt:
        print("Gateway stopped by user")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
