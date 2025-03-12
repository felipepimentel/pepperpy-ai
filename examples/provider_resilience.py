#!/usr/bin/env python
"""
Example demonstrating the provider telemetry and resilience systems.

This example shows how to:
1. Use the telemetry system to monitor provider operations
2. Apply circuit breakers to prevent cascading failures
3. Implement fallback mechanisms for provider operations
4. Combine these patterns for robust provider interactions

Requirements:
    - Python 3.9+
    - PepperPy library
    - API keys for providers (OpenAI, Anthropic, etc.)

Usage:
    1. Set up environment variables in a .env file:
       OPENAI_API_KEY=your_key_here
       ANTHROPIC_API_KEY=your_key_here

    2. Run the example:
       python provider_resilience.py
"""

import logging
import os
import random
import time
from datetime import timedelta
from typing import Any, Dict

from pepperpy.core.resilience import (
    CircuitBreakerConfig,
    CircuitBreakerError,
    ProviderFallbackError,
    get_circuit_breaker,
    get_fallback,
    with_circuit_breaker,
    with_fallback,
)
from pepperpy.core.telemetry import (
    EventLevel,
    MetricType,
    get_provider_telemetry,
    report_event,
    report_metric,
)


def load_env():
    """Load environment variables from .env file."""
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value
        print("Loaded environment variables from .env file")
    else:
        print("No .env file found")


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def check_api_keys(keys):
    """Check if required API keys are set."""
    missing = [key for key in keys if not os.environ.get(key)]
    if missing:
        print(f"Warning: Missing API keys: {', '.join(missing)}")
        print("Some examples may not work without these keys")
    else:
        print(f"All required API keys are set: {', '.join(keys)}")


def main():
    """Run the provider resilience example."""
    # Load environment variables and set up logging
    load_env()
    setup_logging()

    # Check for required API keys
    check_api_keys(["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "COHERE_API_KEY"])

    # Demonstrate telemetry
    demonstrate_telemetry()

    # Demonstrate circuit breaker
    demonstrate_circuit_breaker()

    # Demonstrate fallback
    demonstrate_fallback()

    # Demonstrate combined patterns
    demonstrate_combined_patterns()


def demonstrate_telemetry():
    """Demonstrate how to use the telemetry system."""
    print("\n=== Telemetry System ===")

    # Get telemetry for a provider
    openai_telemetry = get_provider_telemetry("openai")

    # Report metrics
    print("Reporting metrics...")
    openai_telemetry.count("requests", 1)
    openai_telemetry.gauge("queue_depth", 5)
    openai_telemetry.histogram("response_time", 0.25)

    # Report events
    print("Reporting events...")
    openai_telemetry.info(
        "api_request",
        "API request started",
        {"endpoint": "/v1/chat/completions", "model": "gpt-4"},
    )
    openai_telemetry.warning(
        "rate_limit",
        "Approaching rate limit",
        {"limit": 100, "current": 80, "remaining": 20},
    )

    # Use timer
    print("Using timer...")
    with openai_telemetry.time("operation_duration"):
        # Simulate some work
        time.sleep(0.5)
        print("Operation completed")

    # Report global metrics and events
    print("Reporting global metrics and events...")
    report_metric(
        "global_requests",
        10,
        MetricType.COUNTER,
        {"service": "api", "endpoint": "/v1/chat/completions"},
    )
    report_event(
        "system_status",
        EventLevel.INFO,
        "System is healthy",
        {"uptime": 3600, "memory_usage": 512},
    )


class SimulatedProvider:
    """Simulated provider for demonstration purposes."""

    def __init__(self, provider_id: str, failure_rate: float = 0.0):
        """Initialize the simulated provider.

        Args:
            provider_id: The ID of the provider.
            failure_rate: The probability of a request failing (0.0 to 1.0).
        """
        self.provider_id = provider_id
        self.failure_rate = failure_rate
        self.telemetry = get_provider_telemetry(provider_id)

    def make_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a simulated request to the provider.

        Args:
            request_data: The request data.

        Returns:
            The response data.

        Raises:
            Exception: If the request fails.
        """
        self.telemetry.info(
            "request_started",
            f"Request to {self.provider_id} started",
            {"request": request_data},
        )

        # Simulate request latency
        latency = 0.1 + random.random() * 0.3
        time.sleep(latency)

        # Simulate request failure
        if random.random() < self.failure_rate:
            self.telemetry.error(
                "request_failed",
                f"Request to {self.provider_id} failed",
                {"request": request_data, "latency": latency},
            )
            raise Exception(f"Simulated failure from {self.provider_id}")

        # Simulate successful response
        response = {
            "provider": self.provider_id,
            "request": request_data,
            "latency": latency,
            "timestamp": time.time(),
        }

        self.telemetry.info(
            "request_succeeded",
            f"Request to {self.provider_id} succeeded",
            {"request": request_data, "latency": latency},
        )
        self.telemetry.histogram("request_latency", latency)

        return response


def demonstrate_circuit_breaker():
    """Demonstrate how to use the circuit breaker pattern."""
    print("\n=== Circuit Breaker Pattern ===")

    # Create a simulated provider with a high failure rate
    provider = SimulatedProvider("openai", failure_rate=0.7)

    # Create a circuit breaker with a custom configuration
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=timedelta(seconds=5),
        success_threshold=2,
        max_retries=2,
    )
    breaker = get_circuit_breaker(provider.provider_id, config)

    # Make requests with circuit breaker protection
    for i in range(10):
        try:
            print(f"Request {i + 1}...")
            response = breaker.execute(
                provider.make_request, {"query": f"Request {i + 1}"}
            )
            print(f"  Success: {response}")
        except CircuitBreakerError as e:
            print(f"  Circuit breaker error: {e}")
        except Exception as e:
            print(f"  Unexpected error: {e}")

        # Add a small delay between requests
        time.sleep(0.5)

    # Demonstrate using the circuit breaker as a decorator
    print("\nUsing circuit breaker as a decorator...")

    @with_circuit_breaker("anthropic", config)
    def make_anthropic_request(request_data):
        """Make a request to the Anthropic provider."""
        provider = SimulatedProvider("anthropic", failure_rate=0.5)
        return provider.make_request(request_data)

    # Make requests using the decorated function
    for i in range(5):
        try:
            print(f"Decorated request {i + 1}...")
            response = make_anthropic_request({"query": f"Decorated request {i + 1}"})
            print(f"  Success: {response}")
        except CircuitBreakerError as e:
            print(f"  Circuit breaker error: {e}")
        except Exception as e:
            print(f"  Unexpected error: {e}")

        # Add a small delay between requests
        time.sleep(0.5)


def demonstrate_fallback():
    """Demonstrate how to use the fallback pattern."""
    print("\n=== Fallback Pattern ===")

    # Create simulated providers with different failure rates
    primary_provider = SimulatedProvider("openai", failure_rate=0.8)
    fallback1_provider = SimulatedProvider("anthropic", failure_rate=0.4)
    fallback2_provider = SimulatedProvider("cohere", failure_rate=0.2)

    # Create a fallback mechanism
    fallback = get_fallback(
        primary_provider.provider_id,
        [fallback1_provider.provider_id, fallback2_provider.provider_id],
    )

    # Define a function that takes a provider ID and makes a request
    def make_request_with_provider(provider_id, request_data=None):
        """Make a request using the specified provider."""
        if provider_id == "openai":
            return primary_provider.make_request(request_data or {})
        elif provider_id == "anthropic":
            return fallback1_provider.make_request(request_data or {})
        elif provider_id == "cohere":
            return fallback2_provider.make_request(request_data or {})
        else:
            raise ValueError(f"Unknown provider: {provider_id}")

    # Make requests with fallback protection
    for i in range(5):
        try:
            print(f"Request {i + 1} with fallback...")
            response = fallback.execute(
                lambda provider_id: make_request_with_provider(
                    provider_id, {"query": f"Fallback request {i + 1}"}
                )
            )
            print(f"  Success with provider: {response['provider']}")
        except ProviderFallbackError as e:
            print(f"  All providers failed: {e}")
        except Exception as e:
            print(f"  Unexpected error: {e}")

        # Add a small delay between requests
        time.sleep(0.5)

    # Demonstrate using the fallback as a decorator
    print("\nUsing fallback as a decorator...")

    @with_fallback("openai", ["anthropic", "cohere"])
    def make_request_with_fallback(provider_id):
        """Make a request with fallback support."""
        return make_request_with_provider(
            provider_id, {"query": "Decorated fallback request"}
        )

    # Make requests using the decorated function
    for i in range(3):
        try:
            print(f"Decorated fallback request {i + 1}...")
            response = make_request_with_fallback()
            print(f"  Success with provider: {response['provider']}")
        except ProviderFallbackError as e:
            print(f"  All providers failed: {e}")
        except Exception as e:
            print(f"  Unexpected error: {e}")

        # Add a small delay between requests
        time.sleep(0.5)


def demonstrate_combined_patterns():
    """Demonstrate how to combine telemetry, circuit breakers, and fallbacks."""
    print("\n=== Combined Patterns ===")

    # Create a more realistic example that combines all patterns
    # This simulates a text generation service that uses multiple providers

    class TextGenerationService:
        """Text generation service that uses multiple providers with resilience patterns."""

        def __init__(self):
            """Initialize the text generation service."""
            # Create circuit breaker configuration
            self.circuit_config = CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=timedelta(seconds=10),
                max_retries=2,
            )

            # Create simulated providers
            self.providers = {
                "openai": SimulatedProvider("openai", failure_rate=0.6),
                "anthropic": SimulatedProvider("anthropic", failure_rate=0.3),
                "cohere": SimulatedProvider("cohere", failure_rate=0.1),
            }

            # Create fallback mechanism
            self.fallback = get_fallback(
                "openai", ["anthropic", "cohere"], self.circuit_config
            )

            # Create telemetry
            self.telemetry = get_provider_telemetry("text_generation_service")

        def generate_text(self, prompt: str) -> Dict[str, Any]:
            """Generate text using the available providers.

            Args:
                prompt: The prompt to generate text from.

            Returns:
                The generated text and metadata.

            Raises:
                Exception: If all providers fail.
            """
            self.telemetry.info(
                "generate_text_started",
                "Text generation started",
                {"prompt": prompt},
            )

            start_time = time.time()

            try:
                # Use the fallback mechanism to try multiple providers
                response = self.fallback.execute(
                    lambda provider_id: self._generate_with_provider(
                        provider_id, prompt
                    ),
                    lambda: self._fallback_generation(prompt),
                )

                # Record success metrics
                duration = time.time() - start_time
                self.telemetry.histogram("generation_time", duration)
                self.telemetry.count("successful_generations", 1)
                self.telemetry.info(
                    "generate_text_succeeded",
                    "Text generation succeeded",
                    {
                        "prompt": prompt,
                        "provider": response["provider"],
                        "duration": duration,
                    },
                )

                return response

            except Exception as e:
                # Record failure metrics
                duration = time.time() - start_time
                self.telemetry.count("failed_generations", 1)
                self.telemetry.error(
                    "generate_text_failed",
                    "Text generation failed",
                    {"prompt": prompt, "error": str(e), "duration": duration},
                )
                raise

        def _generate_with_provider(
            self, provider_id: str, prompt: str
        ) -> Dict[str, Any]:
            """Generate text with a specific provider.

            Args:
                provider_id: The ID of the provider to use.
                prompt: The prompt to generate text from.

            Returns:
                The generated text and metadata.

            Raises:
                Exception: If the provider fails.
            """
            provider = self.providers.get(provider_id)
            if not provider:
                raise ValueError(f"Unknown provider: {provider_id}")

            # Get the circuit breaker for this provider
            breaker = get_circuit_breaker(provider_id, self.circuit_config)

            # Use the circuit breaker to make the request
            return breaker.execute(
                provider.make_request, {"prompt": prompt, "max_tokens": 100}
            )

        def _fallback_generation(self, prompt: str) -> Dict[str, Any]:
            """Generate a fallback response when all providers fail.

            Args:
                prompt: The prompt that failed to generate text.

            Returns:
                A fallback response.
            """
            self.telemetry.warning(
                "using_fallback_generation",
                "Using fallback generation",
                {"prompt": prompt},
            )

            # In a real system, this might use a cached response or a simple rule-based generator
            return {
                "provider": "fallback",
                "text": "I'm sorry, I'm unable to generate a response at the moment.",
                "prompt": prompt,
                "is_fallback": True,
                "timestamp": time.time(),
            }

    # Create the text generation service
    service = TextGenerationService()

    # Generate text with the service
    for i in range(10):
        prompt = (
            f"Explain the concept of resilience in distributed systems, part {i + 1}."
        )
        print(f"\nGenerating text for prompt {i + 1}...")

        try:
            response = service.generate_text(prompt)
            print(f"  Generated with provider: {response['provider']}")
            if response.get("is_fallback"):
                print(f"  Fallback response: {response['text']}")
        except Exception as e:
            print(f"  Failed to generate text: {e}")

        # Add a small delay between requests
        time.sleep(0.5)


if __name__ == "__main__":
    main()
