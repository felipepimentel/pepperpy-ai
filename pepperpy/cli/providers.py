"""CLI commands for managing AI providers and models.

This module provides commands for managing different AI providers,
their configurations, and model settings.
"""

import json
from typing import Any, Dict, Optional

import click

from pepperpy.cli import CommandGroup, logger
from pepperpy.monitoring import metrics
from pepperpy.providers import get_provider, list_providers
from pepperpy.providers.base import ProviderConfig


class ProviderCommands(CommandGroup):
    """Provider-related CLI commands."""

    name = "provider"
    help = "Manage AI providers and models"

    @classmethod
    def get_command_group(cls) -> click.Group:
        """Get the provider command group."""

        @click.group(name=cls.name, help=cls.help)
        def provider():
            """Manage AI providers and models."""
            pass

        # Add all commands
        provider.add_command(cls.list)
        provider.add_command(cls.info)
        provider.add_command(cls.test)
        provider.add_command(cls.configure)
        provider.add_command(cls.models)
        provider.add_command(cls.stats)
        provider.add_command(cls.quota)

        return provider

    @staticmethod
    @click.command()
    @click.option("--detailed", "-d", is_flag=True, help="Show detailed information")
    def list(detailed: bool) -> None:
        """List available providers."""
        try:
            providers = list_providers()

            click.echo("\nAvailable Providers:")
            click.echo("=" * 80)

            for provider_name, provider_info in providers.items():
                if detailed:
                    click.echo(f"\n{provider_name}:")
                    click.echo(f"  Type: {provider_info['type']}")
                    click.echo(f"  Description: {provider_info['description']}")
                    click.echo(f"  Models: {', '.join(provider_info['models'])}")
                    click.echo(f"  Features: {', '.join(provider_info['features'])}")
                    click.echo("-" * 40)
                else:
                    click.echo(f"- {provider_name}")

        except Exception as e:
            logger.error(
                "Failed to list providers",
                error=str(e),
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("provider_name")
    def info(provider_name: str) -> None:
        """Show detailed information about a provider."""
        try:
            provider = get_provider(provider_name)
            info = provider.get_info()

            click.echo(f"\nProvider: {provider_name}")
            click.echo("=" * 80)
            click.echo(f"\nDescription: {info['description']}")
            click.echo("\nSupported Models:")
            for model in info["models"]:
                click.echo(f"  - {model['name']}")
                click.echo(f"    Context: {model['context_length']} tokens")
                click.echo(f"    Features: {', '.join(model['features'])}")

            click.echo("\nCapabilities:")
            for cap, details in info["capabilities"].items():
                click.echo(f"  - {cap}: {details}")

        except Exception as e:
            logger.error(
                "Failed to get provider info",
                error=str(e),
                provider=provider_name,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("provider_name")
    @click.option("--model", "-m", help="Specific model to test")
    def test(provider_name: str, model: Optional[str]) -> None:
        """Test provider connectivity and functionality."""
        try:
            provider = get_provider(provider_name)
            results = provider.run_tests(model=model)

            click.echo(f"\nTest Results for {provider_name}:")
            click.echo("=" * 80)

            for test in results:
                status = "✓" if test.passed else "✗"
                click.echo(f"\n{status} {test.name}")
                if not test.passed:
                    click.echo(f"  Error: {test.error}")
                if test.latency:
                    click.echo(f"  Latency: {test.latency:.2f}ms")

        except Exception as e:
            logger.error(
                "Provider test failed",
                error=str(e),
                provider=provider_name,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("provider_name")
    @click.option(
        "--config-file",
        "-f",
        type=click.Path(exists=True),
        help="Configuration file path",
    )
    @click.option("--api-key", envvar="PEPPERPY_API_KEY", help="API key")
    @click.option("--model", help="Default model")
    @click.option("--temperature", type=float, help="Default temperature")
    @click.option("--max-tokens", type=int, help="Default max tokens")
    def configure(
        provider_name: str,
        config_file: Optional[str],
        api_key: Optional[str],
        model: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
    ) -> None:
        """Configure a provider with API keys and defaults."""
        try:
            config: Dict[str, Any] = {}

            # Load from file if provided
            if config_file:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

            # Override with CLI options
            if api_key:
                config["api_key"] = api_key
            if model:
                config["model"] = model
            if temperature is not None:
                config["temperature"] = temperature
            if max_tokens is not None:
                config["max_tokens"] = max_tokens

            # Create provider config
            provider_config = ProviderConfig(provider_type=provider_name, **config)

            # Initialize and test provider
            provider = get_provider(provider_name, provider_config)
            provider.initialize()

            click.echo(f"Provider '{provider_name}' configured successfully")

        except Exception as e:
            logger.error(
                "Failed to configure provider",
                error=str(e),
                provider=provider_name,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("provider_name")
    def models(provider_name: str) -> None:
        """List available models for a provider."""
        try:
            provider = get_provider(provider_name)
            models = provider.list_models()

            click.echo(f"\nAvailable Models for {provider_name}:")
            click.echo("=" * 80)

            for model in models:
                click.echo(f"\n{model['name']}:")
                click.echo(f"  Context Length: {model['context_length']} tokens")
                click.echo(f"  Input Cost: ${model['input_cost']}/1K tokens")
                click.echo(f"  Output Cost: ${model['output_cost']}/1K tokens")
                click.echo(f"  Features: {', '.join(model['features'])}")
                click.echo("-" * 40)

        except Exception as e:
            logger.error(
                "Failed to list models",
                error=str(e),
                provider=provider_name,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("provider_name")
    @click.option(
        "--period", "-p", default="24h", help="Time period (e.g., 24h, 7d, 30d)"
    )
    def stats(provider_name: str, period: str) -> None:
        """Show usage statistics for a provider."""
        try:
            stats = metrics.get_provider_stats(provider_name, period)

            click.echo(f"\nUsage Statistics for {provider_name}:")
            click.echo("=" * 80)

            if "requests" in stats:
                click.echo("\nRequests:")
                click.echo(f"  Total: {stats['requests']['total']}")
                click.echo(f"  Success Rate: {stats['requests']['success_rate']:.2f}%")
                click.echo(
                    f"  Average Latency: {stats['requests']['avg_latency']:.2f}ms"
                )

            if "tokens" in stats:
                click.echo("\nToken Usage:")
                click.echo(f"  Input Tokens: {stats['tokens']['input']}")
                click.echo(f"  Output Tokens: {stats['tokens']['output']}")
                click.echo(f"  Total Cost: ${stats['tokens']['cost']:.2f}")

            if "models" in stats:
                click.echo("\nModel Usage:")
                for model, count in stats["models"].items():
                    click.echo(f"  {model}: {count} requests")

        except Exception as e:
            logger.error(
                "Failed to get provider stats",
                error=str(e),
                provider=provider_name,
            )
            click.echo(f"Error: {str(e)}")

    @staticmethod
    @click.command()
    @click.argument("provider_name")
    def quota(provider_name: str) -> None:
        """Show quota and rate limit information."""
        try:
            provider = get_provider(provider_name)
            quota = provider.get_quota_info()

            click.echo(f"\nQuota Information for {provider_name}:")
            click.echo("=" * 80)

            if "rate_limits" in quota:
                click.echo("\nRate Limits:")
                for limit in quota["rate_limits"]:
                    click.echo(f"  {limit['requests']} requests per {limit['period']}")

            if "usage" in quota:
                click.echo("\nUsage:")
                click.echo(f"  Used: {quota['usage']['used']}")
                click.echo(f"  Remaining: {quota['usage']['remaining']}")
                click.echo(f"  Reset: {quota['usage']['reset_time']}")

            if "tiers" in quota:
                click.echo("\nTier Information:")
                click.echo(f"  Current Tier: {quota['tiers']['current']}")
                click.echo(f"  Monthly Limit: {quota['tiers']['monthly_limit']}")

        except Exception as e:
            logger.error(
                "Failed to get quota info",
                error=str(e),
                provider=provider_name,
            )
            click.echo(f"Error: {str(e)}")


# Register the provider commands
from pepperpy.cli import CLIManager

CLIManager.register_group(ProviderCommands)
